"""Wiki vocabulary index for wikilink canonicalisation (Task 4).

Walks ``wiki/entities/*.md`` and ``wiki/concepts/*.md`` once per process
to build an alias map ``{normalized_term: canonical_slug}``. Used by
Task 7's deterministic renderer to canonicalise wikilinks against the
existing 8500+ entity / 1500+ concept pages.

Performance budget (from docs/ingestion_prompt_overhaul_plan.md):
  * cold build: ≤ 5 s
  * find_canonical: O(1) dict lookup
  * top_k_candidates: ≤ 250 ms / paper

Caching: a module-level singleton index, rebuilt only when a file in
``wiki/entities/`` or ``wiki/concepts/`` is newer than the cached
``built_at`` timestamp. Stub redirects (< 200 bytes) are skipped. The
built index is also persisted to ``wiki/vocabulary_index.json`` so a new
process rehydrates it instead of re-reading every page; the disk copy is
validated with the same directory-signature + recursive-mtime checks.

This module has no third-party dependencies so it can be imported from
prompt builders and tests without dragging Vertex / genai into the graph.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

#: Project root inferred from this file's location. Override via the
#: ``wiki_root`` kwarg on ``get_index()`` or in tests.
_DEFAULT_WIKI_ROOT = Path(__file__).resolve().parent / "wiki"

#: Persisted alias index, so a fresh process (search CLI, MCP server, ingest
#: worker) does not have to re-read every entity/concept page. Invalidated by
#: the same directory-signature + recursive-mtime checks as the memory cache.
_CACHE_FILENAME = "vocabulary_index.json"
_CACHE_VERSION = 1

#: Pages smaller than this many bytes are treated as stub redirects and
#: skipped to avoid pulling in placeholder slugs.
_STUB_THRESHOLD_BYTES = 200

#: Maximum tokens to extract from source text in top_k_candidates. Keeps
#: candidate-extraction bounded for very long papers.
_MAX_SOURCE_TOKENS = 50_000


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VocabularyEntry:
    """One canonical entry in the wiki vocabulary."""

    slug: str        # filename without .md, e.g. "cas9"
    title: str       # Display text from the `# Title` line, e.g. "Cas9"
    kind: str        # "entity" or "concept"
    aliases: tuple[str, ...] = ()


@dataclass
class VocabularyIndex:
    """In-memory alias index. Built lazily by ``get_index()``."""

    entries: dict[str, VocabularyEntry] = field(default_factory=dict)
    #: lowercased term -> canonical slug. The hot path for find_canonical.
    alias_to_slug: dict[str, str] = field(default_factory=dict)
    built_at: float = 0.0
    wiki_root: Path = _DEFAULT_WIKI_ROOT

    def __len__(self) -> int:
        return len(self.entries)

    def find_canonical(self, term: str) -> str | None:
        """Return the canonical slug matching `term` (case-insensitive,
        whitespace-collapsed), or None if not found."""
        key = _normalise(term)
        if not key:
            return None
        return self.alias_to_slug.get(key)

    def top_k_candidates(self, text: str, k: int = 50) -> list[str]:
        """Return up to `k` canonical slugs whose alias appears in `text`.

        Sorted by frequency descending, then by slug for stable ordering.
        Implementation uses a single tokenisation pass + dict lookups,
        so it's O(len(text)) regardless of vocabulary size.
        """
        if not text or k <= 0 or not self.alias_to_slug:
            return []

        counts: dict[str, int] = {}
        # Pass 1: word-level tokens (lowercase, punctuation-stripped).
        tokens = _tokenise(text)
        for tok in tokens[:_MAX_SOURCE_TOKENS]:
            slug = self.alias_to_slug.get(tok)
            if slug is not None:
                counts[slug] = counts.get(slug, 0) + 1

        # Pass 2: bigrams + trigrams (covers multi-word entities like
        # "phenylpropanoid pathway" or "starch branching enzyme"). Capped
        # at the same token budget to bound runtime.
        capped = tokens[:_MAX_SOURCE_TOKENS]
        for n in (2, 3):
            for i in range(len(capped) - n + 1):
                gram = " ".join(capped[i : i + n])
                slug = self.alias_to_slug.get(gram)
                if slug is not None:
                    counts[slug] = counts.get(slug, 0) + 1

        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        return [slug for slug, _ in ranked[:k]]


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------

_index_lock = threading.Lock()
_cached_index: VocabularyIndex | None = None
_cached_directory_signature: tuple[int, int] | None = None
_last_full_validation = 0.0


def _normalise(term: str) -> str:
    """Lowercase + collapse whitespace + strip outer punctuation."""
    if not term:
        return ""
    s = term.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


_TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9./_-]*")


def _tokenise(text: str) -> list[str]:
    """Lightweight tokeniser: lowercase alphanumeric runs plus -._/ for
    things like ``Qphs.osu-3A`` or ``CRISPR/Cas9``. Trailing punctuation
    (``.``, ``-``, ``_``, ``/``) is stripped per token so ``TaPHS1.`` →
    ``taphs1`` matches the canonical slug.
    """
    out = []
    for m in _TOKEN_RE.finditer(text):
        tok = m.group(0).lower().rstrip("./_-")
        if tok:
            out.append(tok)
    return out


def _extract_title(md: str) -> str | None:
    """Pull the first ``# Heading`` line from the page body."""
    m = re.search(r"(?m)^#\s+(.+?)\s*$", md)
    return m.group(1).strip() if m else None


_ALIASES_RE = re.compile(
    r"(?im)^aliases\s*:\s*\[(?P<list>[^\]]*)\]"
    r"|^aliases\s*:\s*\n(?P<block>(?:\s*-\s*.+\n)+)"
)


def _extract_aliases(md: str) -> list[str]:
    """Pull ``aliases: [a, b]`` or YAML-block aliases from frontmatter.

    Only the *first* aliases match in the file is used (frontmatter is
    expected to live at the top). Returns deduped, normalised entries.
    """
    m = _ALIASES_RE.search(md)
    if not m:
        return []
    raw = m.group("list") or m.group("block") or ""
    items = []
    if "," in raw and "\n" not in raw:
        items = [x.strip().strip('"\'') for x in raw.split(",")]
    else:
        for line in raw.splitlines():
            ln = line.strip()
            if ln.startswith("-"):
                items.append(ln.lstrip("-").strip().strip('"\''))
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        n = _normalise(it)
        if n and n not in seen:
            seen.add(n)
            out.append(it)  # preserve original casing for VocabularyEntry
    return out


def _slug_to_terms(slug: str) -> list[str]:
    """Generate aliases from a collision-safe relative-path slug."""
    basename = slug.rsplit("/", 1)[-1]
    terms = {
        slug,
        basename,
        basename.replace("-", " "),
        basename.replace("-", "/"),
    }
    return sorted(term for term in terms if term)


def _looks_like_stub(md: str, size: int) -> bool:
    """Conservatively identify empty/generated placeholders, not short facts."""
    if size < _STUB_THRESHOLD_BYTES:
        return True
    body = re.sub(r"\A---\s*\n.*?\n---\s*", "", md, count=1, flags=re.DOTALL)
    body = re.sub(r"(?m)^#{1,6}\s+.*$", "", body)
    body = re.sub(r"(?m)^\*\*(?:Sources|Last updated|Related pages)\*\*:?.*$", "", body)
    body = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", body)
    informative = re.sub(r"\s+", " ", body).strip()
    lowered = informative.lower()
    if len(informative) < 100:
        return True
    placeholders = (
        "no summary available",
        "summary not available",
        "content pending",
        "to be populated",
        "no information available",
    )
    if any(marker in lowered for marker in placeholders) and len(informative) < 500:
        return True
    return lowered.count("not reported in this paper") >= 6 and len(informative) < 1500


def _scan_dir(wiki_dir: Path, kind: str) -> Iterable[VocabularyEntry]:
    """Yield non-stub entries recursively with collision-safe path slugs."""
    if not wiki_dir.is_dir():
        return
    for path in sorted(wiki_dir.rglob("*.md")):
        try:
            stat = path.stat()
            md = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _looks_like_stub(md, stat.st_size):
            continue
        slug = path.relative_to(wiki_dir).with_suffix("").as_posix()
        title = _extract_title(md) or path.stem
        aliases = _extract_aliases(md)
        yield VocabularyEntry(
            slug=slug,
            title=title,
            kind=kind,
            aliases=tuple(aliases),
        )


def _build_alias_to_slug(entries: dict[str, VocabularyEntry]) -> dict[str, str]:
    """Flatten entries into a ``{normalised_alias: slug}`` map.

    Earlier entries win on collision (entities scanned before concepts —
    entities tend to be more specific). On a within-pass tie we keep the
    shorter slug, on the assumption that shorter == canonical.
    """
    alias_to_slug: dict[str, str] = {}
    for slug, entry in entries.items():
        candidates: set[str] = set()
        for term in _slug_to_terms(slug):
            candidates.add(_normalise(term))
        candidates.add(_normalise(entry.title))
        for a in entry.aliases:
            candidates.add(_normalise(a))
        for key in candidates:
            if not key:
                continue
            existing = alias_to_slug.get(key)
            if existing is None:
                alias_to_slug[key] = slug
            elif len(slug) < len(existing):
                alias_to_slug[key] = slug
    return alias_to_slug


def _directory_signature(wiki_root: Path) -> tuple[int, int]:
    """Cheap signal for additions/deletions in the two flat vocabulary dirs."""
    signature = []
    for sub in ("entities", "concepts"):
        try:
            signature.append((wiki_root / sub).stat().st_mtime_ns)
        except OSError:
            signature.append(-1)
    return tuple(signature)  # type: ignore[return-value]


def _cache_path(wiki_root: Path) -> Path:
    """Location of the persisted alias index (sibling of ``search_index.json``)."""
    return wiki_root / _CACHE_FILENAME


def _load_disk_cache(wiki_root: Path,
                     directory_signature: tuple[int, int]) -> VocabularyIndex | None:
    """Rehydrate the alias index from disk, or None when absent/stale.

    Building from disk skips reading and stub-screening every entity/concept
    page, which is the whole cost of a cold vocabulary build.
    """
    try:
        with _cache_path(wiki_root).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return None
    if int(payload.get("version", 0)) != _CACHE_VERSION:
        return None
    if list(payload.get("directory_signature", ())) != list(directory_signature):
        return None
    built_at = float(payload.get("built_at", -1.0))
    if built_at <= 0.0:
        return None
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, dict):
        return None
    entries: dict[str, VocabularyEntry] = {}
    for slug, item in raw_entries.items():
        try:
            title, kind, aliases = item
        except (TypeError, ValueError):
            return None
        entries[slug] = VocabularyEntry(
            slug=slug,
            title=str(title),
            kind=str(kind),
            aliases=tuple(str(alias) for alias in aliases),
        )
    stored_alias = payload.get("alias_to_slug")
    if isinstance(stored_alias, dict):
        alias_to_slug = stored_alias
    else:
        alias_to_slug = _build_alias_to_slug(entries)
    return VocabularyIndex(
        entries=entries,
        alias_to_slug=alias_to_slug,
        built_at=built_at,
        wiki_root=wiki_root,
    )


def _store_disk_cache(index: VocabularyIndex,
                      directory_signature: tuple[int, int]) -> None:
    """Persist the alias index atomically; a read-only wiki simply skips it."""
    payload = {
        "version": _CACHE_VERSION,
        "built_at": index.built_at,
        "directory_signature": list(directory_signature),
        "alias_to_slug": index.alias_to_slug,
        "entries": {
            slug: [entry.title, entry.kind, list(entry.aliases)]
            for slug, entry in index.entries.items()
        },
    }
    path = _cache_path(index.wiki_root)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        os.replace(temporary, path)
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _max_mtime(wiki_root: Path) -> float:
    """Largest recursive file/directory mtime for cache invalidation."""
    latest = 0.0
    for sub in ("entities", "concepts"):
        directory = wiki_root / sub
        if not directory.is_dir():
            continue
        for path in (directory, *directory.rglob("*")):
            try:
                latest = max(latest, path.stat().st_mtime)
            except OSError:
                continue
    return latest


def build_index(wiki_root: Path | None = None) -> VocabularyIndex:
    """Build the index from disk. Use ``get_index()`` for the cached form."""
    root = Path(wiki_root) if wiki_root else _DEFAULT_WIKI_ROOT
    entries: dict[str, VocabularyEntry] = {}
    # Entities scanned first so they take priority on alias collisions
    # (per the assumption in _build_alias_to_slug).
    for entry in _scan_dir(root / "entities", "entity"):
        entries[entry.slug] = entry
    for entry in _scan_dir(root / "concepts", "concept"):
        entries.setdefault(entry.slug, entry)
    alias_to_slug = _build_alias_to_slug(entries)
    return VocabularyIndex(
        entries=entries,
        alias_to_slug=alias_to_slug,
        built_at=_max_mtime(root),
        wiki_root=root,
    )


def get_index(wiki_root: Path | None = None, *, force_rebuild: bool = False) -> VocabularyIndex:
    """Return the cached vocabulary index, rebuilding on file changes.

    Directory mtimes detect additions/deletions immediately. Existing-file
    edits are checked with the full recursive scan at a short configurable
    interval, avoiding a 20k-file ``stat`` walk on every search request.
    """
    global _cached_index, _cached_directory_signature, _last_full_validation
    root = Path(wiki_root) if wiki_root else _DEFAULT_WIKI_ROOT

    with _index_lock:
        now = time.monotonic()
        directory_signature = _directory_signature(root)
        cache = _cached_index
        if not force_rebuild and cache is not None and cache.wiki_root == root:
            if directory_signature == _cached_directory_signature:
                # File *additions/deletions* are already caught immediately by
                # the directory signature above. The recursive _max_mtime walk
                # below only exists to catch *in-place edits* of existing pages,
                # and on the 50k+ entity/concept corpus it costs a ~750k-path
                # stat walk (~280ms) per call. Revalidating that on every search
                # dominated query latency, so the walk is throttled to a
                # configurable interval; the vocabulary is a soft alias-expansion
                # aid, so a bounded staleness window for edits is acceptable.
                interval = max(
                    0.0, float(os.environ.get("WIKI_VOCAB_VALIDATION_INTERVAL", "30.0"))
                )
                if now - _last_full_validation < interval:
                    return cache
                current_mtime = _max_mtime(root)
                _last_full_validation = now
                if current_mtime <= cache.built_at:
                    return cache
        new_index = None
        if not force_rebuild:
            new_index = _load_disk_cache(root, directory_signature)
        if new_index is None:
            new_index = build_index(root)
            _store_disk_cache(new_index, directory_signature)
        _cached_index = new_index
        _cached_directory_signature = directory_signature
        _last_full_validation = time.monotonic()
        return new_index


def reset_cache() -> None:
    """Drop the cached index and validation metadata (used by tests)."""
    global _cached_index, _cached_directory_signature, _last_full_validation
    with _index_lock:
        _cached_index = None
        _cached_directory_signature = None
        _last_full_validation = 0.0


# ---------------------------------------------------------------------------
# Public functional API
# ---------------------------------------------------------------------------

def find_canonical(term: str, *, wiki_root: Path | None = None) -> str | None:
    """Return the canonical slug for `term`, or None if no match."""
    return get_index(wiki_root).find_canonical(term)


def top_k_candidates(text: str, *, k: int = 50,
                     wiki_root: Path | None = None) -> list[str]:
    """Return up to `k` canonical slugs whose alias appears in `text`."""
    return get_index(wiki_root).top_k_candidates(text, k=k)


__all__ = [
    "VocabularyEntry",
    "VocabularyIndex",
    "build_index",
    "get_index",
    "reset_cache",
    "find_canonical",
    "top_k_candidates",
]
