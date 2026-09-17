"""Versioned, quality-aware retrieval for the ResearchWiki corpus.

The persisted index covers compact wiki documents. Raw paper Markdown is linked
by source stem and searched/reranked at query time so evidence mode can recover
facts omitted by generated summaries without creating a second huge chunk index.
"""

from __future__ import annotations

from collections import Counter, OrderedDict, defaultdict
from dataclasses import asdict, dataclass, field
from functools import lru_cache
import copy
import hashlib
import json
import math
import os
import sqlite3
import time
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence


INDEX_VERSION = 4
INDEX_FILENAME = "search_index.json"
DOCS_FILENAME = "search_index_docs.json"
INDEXED_FOLDERS: tuple[tuple[str, str], ...] = (
    ("sources", "paper"),
    ("entities", "entity"),
    ("concepts", "concept"),
    ("synthesis", "synthesis"),
)
SEARCH_MODES = ("summary", "hybrid", "evidence")
DOC_TYPES = ("paper", "entity", "concept", "synthesis")
SUMMARY_QUERY_CACHE_SIZE = max(1, int(os.environ.get("WIKI_SEARCH_CACHE_SIZE", "32")))
PASSAGE_FEATURE_CACHE_SIZE = max(1, int(os.environ.get("WIKI_PASSAGE_CACHE_SIZE", "2048")))

# Phrase scoring runs a whitespace/dash-tolerant regex over the *full text* of
# every scored candidate. A phrase can only occur in a document that already
# contains every one of the phrase's word tokens, so a cheap necessary-condition
# check against the per-document term maps (already in memory) lets us skip the
# regex for the overwhelming majority of candidates with byte-for-byte identical
# scoring. Profiling on the 57k-document corpus showed this regex was ~33% of
# total retrieval time. Set WIKI_SEARCH_PHRASE_PREFILTER=0 to restore the
# unconditional regex (safety valve / equivalence testing).
PHRASE_PREFILTER_ENABLED = os.environ.get(
    "WIKI_SEARCH_PHRASE_PREFILTER", "1"
).strip().lower() not in {"0", "false", "no", "off"}

RAW_PASSAGE_INDEX_VERSION = 3
RAW_PASSAGE_INDEX_FILENAME = "raw_passage_index.sqlite3"
RAW_PASSAGE_CANDIDATE_LIMIT = max(
    200,
    int(os.environ.get("WIKI_RAW_PASSAGE_CANDIDATE_LIMIT", "2000")),
)

STOPWORDS = frozenset(
    {
        "a", "about", "all", "also", "an", "and", "answer", "are", "as",
        "associated", "at", "be", "been", "being", "between", "by", "can",
        "could", "did", "do", "does", "during", "each", "exhaustive", "for",
        "from", "function", "functions", "give", "has", "have", "having", "how",
        "in", "interaction", "interactions", "into", "is", "it", "its", "list",
        "may", "more", "most", "of", "on", "or", "our", "reported", "show",
        "than", "that", "the", "their", "there", "these", "they", "this",
        "those", "to", "using", "was", "were", "what", "when", "where",
        "which", "who", "will", "with", "within", "would", "you", "your",
    }
)

_DOMAIN_PHRASES = (
    "seed dormancy",
    "bud dormancy",
    "tuber dormancy",
    "pre-harvest sprouting",
    "pre harvest sprouting",
    "transcription factor",
    "transcription factors",
    "dna binding",
    "after-ripening",
    "after ripening",
    "bud break",
)

_DORMANCY_MARKERS = frozenset(
    {
        "dormancy", "dormant", "germination", "sprouting", "after-ripening",
        "afterripening", "endodormancy", "ecodormancy", "paradormancy",
    }
)
_TF_FAMILY_MARKERS = frozenset(
    {
        "transcription", "dna-binding", "myb", "bzip", "bhlh", "ap2", "erf",
        "nac", "wrky", "mads", "gata", "b3",
    }
)
_DORMANCY_CONTEXT_MARKERS: dict[str, frozenset[str]] = {
    "seed_dormancy": frozenset({"seed", "grain", "sprouting", "germination"}),
    # "buds" is listed explicitly: the stemmer leaves four-letter words alone,
    # so it never reduces the stored token "buds" to "bud".
    "bud_dormancy": frozenset(
        {"bud", "buds", "endodormancy", "ecodormancy", "paradormancy"}
    ),
    "tuber_dormancy": frozenset({"tuber", "potato"}),
}

_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9*./_-]*")
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_SPACE_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

STEM_CACHE_SIZE = max(1024, int(os.environ.get("WIKI_STEM_CACHE_SIZE", "500000")))


@lru_cache(maxsize=STEM_CACHE_SIZE)
def _stem_word(word: str) -> str:
    """Conservative suffix stemming; identifiers with digits/punctuation stay intact.

    Memoised because corpus tokens repeat heavily: an evidence query tokenises
    thousands of passages, and stemming was the single largest cost in that path.
    """
    if len(word) <= 4 or any(character.isdigit() for character in word):
        return word
    if any(character in word for character in "-./*"):
        return word
    if word.endswith("ing") and len(word) > 6:
        return word[:-3]
    if word.endswith("ed") and len(word) > 5:
        return word[:-2]
    if word.endswith("ies") and len(word) > 5:
        return word[:-3] + "y"
    if word.endswith("es") and not word.endswith("ees"):
        if len(word) > 4 and word[-3] in {"s", "x", "z", "h"}:
            return word[:-2]
        return word[:-1]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 4:
        return word[:-1]
    return word


def _token_set(markers: Iterable[str]) -> frozenset[str]:
    """Project a marker vocabulary into index-token space.

    Stored tokens are stemmed, so an unstemmed marker such as ``sprouting``
    can never match the token the indexer actually wrote (``sprout``).
    """
    return frozenset(_stem_word(marker) for marker in markers)


_DORMANCY_TOKENS = _token_set(_DORMANCY_MARKERS)
_TF_FAMILY_TOKENS = _token_set(_TF_FAMILY_MARKERS)
_DORMANCY_CONTEXT_TOKENS: dict[str, frozenset[str]] = {
    context: _token_set(markers)
    for context, markers in _DORMANCY_CONTEXT_MARKERS.items()
}

_DORMANCY_PHENOTYPE_PATTERN = r"(?:dormancy|dormant|after-ripening|after ripening)"
_SEED_PROCESS_PATTERN = rf"(?:{_DORMANCY_PHENOTYPE_PATTERN}|germination|sprouting)"
_BUD_STAGE_MARKERS = ("endodormancy", "ecodormancy", "paradormancy")
_PHS_MARKERS = ("pre-harvest sprouting", "pre harvest sprouting")


def _proximity_pattern(marker: str, phenotype: str, span: int) -> re.Pattern[str]:
    """Compile a bidirectional "marker near phenotype" sentence matcher."""
    return re.compile(
        rf"\b{marker}\b.{{0,{span}}}{phenotype}"
        rf"|{phenotype}.{{0,{span}}}\b{marker}\b"
    )


# Compiled once: these were previously rebuilt from f-strings for every
# sentence of every candidate passage.
_SEED_CONTEXT_RE = _proximity_pattern(r"seeds?", _SEED_PROCESS_PATTERN, 180)
_GRAIN_CONTEXT_RE = _proximity_pattern(r"grains?", _SEED_PROCESS_PATTERN, 180)
_BUD_CONTEXT_RE = _proximity_pattern(r"buds?", _DORMANCY_PHENOTYPE_PATTERN, 180)
# A bare "tuber sprouting" mention is often generic starch/storage physiology,
# so tuber evidence keeps the tighter span and the dormancy-only phenotype.
_TUBER_CONTEXT_RE = _proximity_pattern(
    r"(?:tubers?|potatoes?)", _DORMANCY_PHENOTYPE_PATTERN, 80
)

_PHRASE_GAP_PATTERN = r"[\s_]+"
_PHRASE_DASH_PATTERN = r"[\s_]*[-\u2013\u2014][\s_]*"


@lru_cache(maxsize=1024)
def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    """Compile a normalised phrase into a matcher for un-normalised text.

    Spaces tolerate wrapped whitespace and underscores, hyphens tolerate
    en/em dashes and surrounding whitespace — the same tolerances
    :func:`_normalize_phrase` provides, without rewriting the haystack.
    """
    pieces: list[str] = []
    for character in phrase:
        if character == " ":
            pieces.append(_PHRASE_GAP_PATTERN)
        elif character == "-":
            pieces.append(_PHRASE_DASH_PATTERN)
        else:
            pieces.append(re.escape(character))
    return re.compile("".join(pieces), re.IGNORECASE)


@dataclass
class SearchResult:
    """One ranked result. The original first five fields remain unchanged."""

    paper: str
    title: str
    snippet: str
    score: float
    matches: list[str]
    path: str = ""
    doc_type: str = ""
    section: str = ""
    source_path: str = ""
    line_start: int | None = None
    line_end: int | None = None
    evidence_quality: float = 0.0
    quality_flags: list[str] = field(default_factory=list)
    canonical_terms: list[str] = field(default_factory=list)
    canonical_key: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryPlan:
    query: str
    base_tokens: tuple[str, ...]
    term_weights: Mapping[str, float]
    phrases: tuple[str, ...]
    canonical_terms: tuple[str, ...]
    #: Tokenised form of each entry in ``phrases`` (aligned by index). Used by
    #: the phrase prefilter in ``_bm25_score``. Defaults to empty so callers
    #: that build a plan directly (e.g. ``_generate_snippet``) stay valid.
    phrase_tokens: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class Passage:
    text: str
    section: str
    line_start: int
    line_end: int


@dataclass(frozen=True)
class RankedPassage:
    passage: Passage
    score: float
    matches: tuple[str, ...]


_REF_SECTION_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s*)?\**\s*(?:\d+[\.\s]+)?(references?|bibliography|literature\s+cited|works\s+cited|reference\s+list)\b",
    re.IGNORECASE,
)
_REF_SECTION_CLEAN_RE = re.compile(
    r"\b(references?|bibliography|literature\s+cited|works\s+cited|reference\s+list)\b",
    re.IGNORECASE,
)
_BIOLOGICAL_REF_RE = re.compile(
    r"\breference\s+(genome|sequence|transcriptome|assembly|gene|cultivar|strain|set|panel|line|standard|sample)\b",
    re.IGNORECASE,
)
_CITATION_LINE_RE = re.compile(
    r"^(?:\[\d+\]|\d+[\.\)]|\*|\-)\s+[A-Z][a-z]+(?:,\s*[A-Z]\.?|\s+[A-Z]\.|\s+et\s+al).*?\b(?:19|20)\d{2}\b|"
    r"\b(?:19|20)\d{2}\b.*?\b(?:doi|vol\.|pp\.|https?://|journal|front\.|nature|science)\b|"
    r"^[A-Z][a-z]+(?:,\s*[A-Z]\.?)+.*?\b(?:19|20)\d{2}\b",
    re.IGNORECASE,
)
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"'<>\]\)]+")


def _is_excluded_path(path: Path | str) -> bool:
    """Check if a path belongs to archived drafts/copies (.attic or .pre-agent)."""
    if not path:
        return False
    s = str(path)
    if ".attic" not in s and ".pre-agent" not in s:
        return False
    p = Path(path) if isinstance(path, str) else path
    parts = set(p.parts)
    if ".attic" in parts or any(part.startswith(".attic") for part in parts):
        return True
    posix = p.as_posix()
    if "/.attic/" in posix or posix.startswith(".attic/") or posix.endswith("/.attic") or ".attic" in posix.split("/"):
        return True
    name = p.name.lower()
    if name.endswith(".pre-agent.md") or ".pre-agent." in name or name.endswith(".pre-agent"):
        return True
    return False


def _is_reference_or_citation_passage(section: str, text: str) -> bool:
    """Determine if a passage is a bibliography/reference section or primarily a citation list."""
    s_lower = section.strip().lower()
    # 1. Section heading match
    if _REF_SECTION_HEADING_RE.search(s_lower):
        if not _BIOLOGICAL_REF_RE.search(s_lower):
            return True
    sec_clean = re.sub(r"^[#*_\s\d\.\-:]+", "", s_lower).strip()
    if _REF_SECTION_CLEAN_RE.search(sec_clean):
        if not _BIOLOGICAL_REF_RE.search(sec_clean):
            return True
    if re.fullmatch(r"^\**\s*reference\s*\**$", s_lower):
        return True

    # 2. Text check for bibliography / citation lists
    dois = _DOI_RE.findall(text)
    if len(dois) >= 2:
        return True

    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 10]
    if len(lines) >= 2:
        citation_lines = sum(1 for l in lines if _CITATION_LINE_RE.search(l))
        if citation_lines >= 2 and (citation_lines / len(lines)) >= 0.4:
            return True

    return False


def _extract_doi(text: str) -> str:
    """Extract and normalize DOI from markdown or metadata."""
    if not text:
        return ""
    m = _DOI_RE.search(text)
    if m:
        return m.group(0).lower().rstrip(".,;)]}\"'")
    return ""


def _canonical_doc_key(
    doc_id: str = "",
    title: str = "",
    text: str = "",
    source_path: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> str:
    """Generate a stable canonical key for document deduplication based on DOI, title, slug, or content hash."""
    # 1. Check DOI in metadata or content or source_path
    doi = ""
    if metadata:
        doi = str(metadata.get("doi", "") or "").strip().lower()
    if not doi and text:
        doi = _extract_doi(text)
    if not doi and source_path:
        doi = _extract_doi(source_path)
    if doi:
        return f"doi:{doi}"

    # 2. Check substantive normalized title
    doc_title = title or (str(metadata.get("title", "")) if metadata else "")
    if not doc_title and text:
        doc_title = _extract_title(text, "")
    if doc_title:
        norm_title = re.sub(r"[^a-z0-9]+", " ", doc_title.lower()).strip()
        if len(norm_title) >= 15 and len(norm_title.split()) >= 3:
            return f"title:{norm_title}"

    # 3. Check author + year + title slug from stem or path
    stem = Path(source_path or doc_id).stem.lower()
    stem_clean = re.sub(r"_[a-f0-9]{10}$", "", stem)
    m = re.match(r"^([a-z]+).*?(19\d\d|20\d\d)[_-](.+)$", stem_clean)
    if m:
        author = m.group(1)
        year = m.group(2)
        rest = m.group(3)
        slug_words = [w for w in re.split(r"[^a-z0-9]+", rest) if w and w not in STOPWORDS][:3]
        if slug_words:
            return f"slug:{author}_{year}_{'_'.join(slug_words)}"

    # 4. Hash fallback from substantive content
    if text:
        clean_text = re.sub(r"[^a-z0-9]+", "", text.lower()[:3000])
        if len(clean_text) >= 100:
            return f"hash:{hashlib.md5(clean_text.encode('utf-8')).hexdigest()}"

    # 5. Final fallback
    return f"stem:{stem}"


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _normalize_phrase(value: str) -> str:
    text = str(value or "").lower().replace("_", " ")
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s*-\s*", "-", text)
    return _SPACE_RE.sub(" ", text).strip()


def _parse_frontmatter(content: str) -> dict[str, Any]:
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}
    result: dict[str, Any] = {}
    for line in match.group("body").splitlines():
        if not line or line[:1].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            result[key] = [
                item.strip().strip("\"'")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        elif value.lower() in {"null", "none", "~"}:
            result[key] = None
        elif value.isdigit():
            result[key] = int(value)
        else:
            result[key] = value.strip("\"'")
    return result


def _extract_title(content: str, fallback: str) -> str:
    h1 = re.search(r"(?m)^#\s+(.+?)\s*$", content)
    if h1:
        return h1.group(1).strip()
    title_section = re.search(
        r"(?im)^##\s+Title\s*&\s*Metadata\s*$\n+(?P<title>[^\n#].+?)\s*$",
        content,
    )
    if title_section:
        return title_section.group("title").strip().strip("*_")
    return fallback


def _strip_markup_for_quality(content: str) -> str:
    text = _FRONTMATTER_RE.sub("", content, count=1)
    text = re.sub(r"(?m)^#{1,6}\s+.*$", "", text)
    text = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"(?m)^\*\*(?:Sources|Last updated|Related pages)\*\*:?.*$", "", text)
    text = re.sub(r"(?m)^---\s*$", "", text)
    return _SPACE_RE.sub(" ", text).strip()


def _is_stub(content: str, doc_type: str, file_size: int) -> bool:
    if file_size < 200:
        return True
    informative = _strip_markup_for_quality(content)
    lowered = informative.lower()
    placeholders = (
        "not reported in this paper",
        "no summary available",
        "summary not available",
        "content pending",
        "to be populated",
        "no information available",
    )
    if len(informative) < 100:
        return True
    if any(phrase in lowered for phrase in placeholders) and len(informative) < 500:
        return True
    if doc_type in {"entity", "concept"}:
        summary_match = re.search(
            r"(?is)\*\*Summary\*\*:\s*(.*?)(?:\n\s*\*\*Sources\*\*:|\n\s*##|\Z)",
            content,
        )
        if summary_match and len(_SPACE_RE.sub(" ", summary_match.group(1)).strip()) < 40:
            return True
    not_reported_count = lowered.count("not reported in this paper")
    return not_reported_count >= 6 and len(informative) < 1500


def _infer_source_kind(content: str, doc_type: str) -> str:
    if doc_type != "paper":
        return "generated_secondary"
    sample = _normalize_phrase(content[:12_000])
    review_markers = (
        "this review",
        "we review",
        "literature review",
        "systematic review",
        "meta-analysis",
        "comparative overview",
        "literature synthesis",
        "this editorial",
        "editorial article",
        "perspective article",
    )
    title_match = re.search(
        r"(?im)^##\s+Title\s*&\s*Metadata\s*$\n+(?P<title>[^\n#].+?)\s*$",
        content,
    )
    source_title = _normalize_phrase(title_match.group("title")) if title_match else ""
    if (
        any(marker in sample for marker in review_markers)
        or re.search(r"\b(review|editorial|perspective)\b", source_title)
    ):
        return "review"
    primary_markers = (
        "randomized complete",
        "we investigated",
        "this study reports",
        "experimental population",
        "association mapping",
        "linkage mapping",
        "field trial",
    )
    if any(marker in sample for marker in primary_markers):
        return "primary_research"
    return "unknown_source"


def _quality_metadata(
    content: str,
    doc_type: str,
    *,
    file_size: int,
    raw_path: str = "",
    raw_ambiguous: bool = False,
) -> tuple[bool, str, float, list[str]]:
    stub = _is_stub(content, doc_type, file_size)
    source_kind = _infer_source_kind(content, doc_type)
    flags: list[str] = []
    if stub:
        flags.append("stub_or_low_information")
    if doc_type == "paper":
        flags.append("compiled_source_summary")
        if raw_path:
            flags.append("raw_full_text_available")
        else:
            flags.append("raw_full_text_missing")
        flags.append(source_kind)
    else:
        flags.append("generated_secondary_page")
        flags.append(doc_type)
    if raw_ambiguous:
        flags.append("ambiguous_raw_source_link")

    if doc_type == "paper":
        quality = {
            "primary_research": 0.95,
            "review": 0.78,
            "unknown_source": 0.82,
        }[source_kind]
        if not raw_path:
            quality -= 0.12
    elif doc_type == "synthesis":
        quality = 0.48
    else:
        quality = 0.36
    if stub:
        quality = min(quality, 0.10)
    return stub, source_kind, max(0.0, round(quality, 3)), flags


class FullTextSearch:
    """BM25 wiki retrieval plus query-time raw-paper passage ranking."""

    def __init__(self, wiki_folder: str = "wiki"):
        self.wiki_folder = Path(wiki_folder).expanduser().resolve()
        self.project_root = self.wiki_folder.parent
        self.raw_root = self.project_root / "raw" / "papers"
        self.index: dict[str, dict[str, int]] = {}
        self.documents: dict[str, str] = {}
        self.doc_metadata: dict[str, dict[str, Any]] = {}
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.average_doc_length: float = 0.0
        self.index_version: int = 0
        self.last_search_report: dict[str, Any] = {}
        self._raw_by_stem: dict[str, list[Path]] | None = None
        self._raw_path_to_docs: dict[str, list[str]] = {}
        self._document_marker_cache: dict[str, tuple[frozenset[str], bool, bool]] = {}
        self._passage_feature_cache: OrderedDict[str, tuple[Counter, str]] = OrderedDict()
        self._summary_query_cache: OrderedDict[tuple, tuple[list[dict], dict]] = OrderedDict()
        self._raw_index_path = self.project_root / "raw" / RAW_PASSAGE_INDEX_FILENAME
        self._raw_index_connection: sqlite3.Connection | None = None
        self._raw_index_signature: str | None = None
        self._last_index_validation_time: float = 0.0
        self._last_directory_signature: tuple | None = None
        self._last_raw_validation_time: float = 0.0
        self._cached_raw_paths: list[Path] = []
        self._raw_folder_signature: tuple | None = None

    def _wiki_folders_signature(self) -> tuple[tuple[str, int], ...]:
        sig = []
        for folder_name, _ in INDEXED_FOLDERS:
            p = self.wiki_folder / folder_name
            try:
                sig.append((folder_name, p.stat().st_mtime_ns))
            except OSError:
                sig.append((folder_name, -1))
        return tuple(sig)

    def _raw_folders_signature(self) -> tuple[int, ...]:
        sig = []
        if self.raw_root.is_dir():
            try:
                sig.append(self.raw_root.stat().st_mtime_ns)
                for sub in sorted(self.raw_root.iterdir()):
                    if sub.is_dir():
                        sig.append(sub.stat().st_mtime_ns)
            except OSError:
                pass
        return tuple(sig)

    def _reset_runtime_caches(self) -> None:
        """Invalidate derivatives whenever the persisted index changes."""
        self._document_marker_cache.clear()
        self._passage_feature_cache.clear()
        self._summary_query_cache.clear()

    # ------------------------------------------------------------------
    # Tokenisation and query planning
    # ------------------------------------------------------------------

    @staticmethod
    def _stem(word: str) -> str:
        """Conservative suffix stemming (memoised in :func:`_stem_word`)."""
        return _stem_word(word)

    def _tokenize(self, text: str) -> list[str]:
        normalized = str(text or "").lower().replace("_", " ")
        normalized = normalized.replace("–", "-").replace("—", "-")
        # findall avoids materialising a Match object per token; the pattern
        # has no groups, so each item is the whole match.
        return [
            _stem_word(word)
            for word in (
                raw.rstrip("./_-") for raw in _TOKEN_RE.findall(normalized)
            )
            if len(word) >= 2 and word not in STOPWORDS
        ]

    def _build_query_plan(self, query: str) -> QueryPlan:
        base_tokens = _ordered_unique(self._tokenize(query))
        term_weights: dict[str, float] = {token: 1.0 for token in base_tokens}
        normalized_query = _normalize_phrase(query)
        phrases: list[str] = [
            _normalize_phrase(match.group(1))
            for match in re.finditer(r'["“](.+?)["”]', query)
            if len(match.group(1).strip()) > 2
        ]
        phrases.extend(phrase for phrase in _DOMAIN_PHRASES if phrase in normalized_query)
        canonical_terms: list[str] = []

        try:
            from wiki_vocabulary import get_index

            vocabulary = get_index(self.wiki_folder)
            direct = vocabulary.find_canonical(query)
            candidates = vocabulary.top_k_candidates(query, k=25)
            if direct:
                candidates.insert(0, direct)
            for slug in _ordered_unique(candidates):
                canonical_terms.append(slug)
                entry = vocabulary.entries.get(slug)
                expansion_values = [slug, slug.replace("-", " ")]
                if entry is not None:
                    expansion_values.extend((entry.title, *entry.aliases))
                for expansion in expansion_values:
                    for token in self._tokenize(expansion):
                        term_weights[token] = max(term_weights.get(token, 0.0), 0.55)
                if entry is not None and len(self._tokenize(entry.title)) > 1:
                    phrases.append(_normalize_phrase(entry.title))
        except (ImportError, OSError, ValueError):
            # Search remains usable for isolated/temp wiki folders.
            pass

        final_phrases = _ordered_unique(phrase for phrase in phrases if phrase)
        return QueryPlan(
            query=query,
            base_tokens=base_tokens,
            term_weights=term_weights,
            phrases=final_phrases,
            canonical_terms=_ordered_unique(canonical_terms),
            phrase_tokens=tuple(
                tuple(self._tokenize(phrase)) for phrase in final_phrases
            ),
        )

    # ------------------------------------------------------------------
    # Index construction and persistence
    # ------------------------------------------------------------------

    def _discover_raw_papers(self) -> dict[str, list[Path]]:
        if self._raw_by_stem is not None:
            return self._raw_by_stem
        raw_by_stem: dict[str, list[Path]] = defaultdict(list)
        if self.raw_root.is_dir():
            for path in sorted(self.raw_root.rglob("*.md")):
                if _is_excluded_path(path):
                    continue
                raw_by_stem[path.stem.lower()].append(path)
        self._raw_by_stem = dict(raw_by_stem)
        return self._raw_by_stem

    @staticmethod
    def _fts_token(token: str) -> str:
        """Map a retrieval token to a safe, stable FTS5 token."""
        return re.sub(r"[^a-z0-9]+", "", str(token).lower())

    def _raw_manifest(self) -> tuple[str, list[Path]]:
        """Return a raw-paper fingerprint and the current Markdown paths."""
        digest = hashlib.sha256()
        paths: list[Path] = []
        if self.raw_root.is_dir():
            for path in sorted(self.raw_root.rglob("*.md")):
                if _is_excluded_path(path):
                    continue
                try:
                    stat = path.stat()
                    relative = path.relative_to(self.project_root).as_posix()
                except OSError:
                    continue
                digest.update(relative.encode("utf-8"))
                digest.update(b"\0")
                digest.update(str(stat.st_size).encode("ascii"))
                digest.update(b"\0")
                digest.update(str(stat.st_mtime_ns).encode("ascii"))
                digest.update(b"\n")
                paths.append(path)

        raw_by_stem: dict[str, list[Path]] = defaultdict(list)
        for path in paths:
            raw_by_stem[path.stem.lower()].append(path)
        self._raw_by_stem = dict(raw_by_stem)
        return digest.hexdigest(), paths

    def _close_raw_index(self) -> None:
        if self._raw_index_connection is not None:
            self._raw_index_connection.close()
        self._raw_index_connection = None
        self._raw_index_signature = None

    def _open_raw_index(self, read_only: bool = False) -> sqlite3.Connection:
        if read_only:
            uri = f"file:{self._raw_index_path.resolve().as_posix()}?mode=ro"
            connection = sqlite3.connect(uri, uri=True)
        else:
            connection = sqlite3.connect(str(self._raw_index_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000;")
        if not read_only:
            connection.execute("PRAGMA journal_mode = WAL;")
            connection.execute("PRAGMA synchronous = NORMAL;")
        return connection

    def _build_raw_passage_index(self, signature: str, raw_paths: Sequence[Path]) -> None:
        """Build a provenance-preserving FTS5 index atomically."""
        self._close_raw_index()
        self._raw_index_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._raw_index_path.with_name(
            f".{self._raw_index_path.name}.{os.getpid()}.tmp"
        )
        temporary.unlink(missing_ok=True)
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(str(temporary))
            connection.executescript(
                """
                PRAGMA journal_mode=MEMORY;
                PRAGMA synchronous=OFF;
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE raw_documents (
                    path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL
                );
                CREATE TABLE passages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    section TEXT NOT NULL,
                    line_start INTEGER NOT NULL,
                    line_end INTEGER NOT NULL,
                    text TEXT NOT NULL
                );
                CREATE INDEX idx_passages_path ON passages(path);
                CREATE VIRTUAL TABLE passage_fts USING fts5(
                    title,
                    section,
                    body,
                    content='',
                    contentless_delete=1
                );
                """
            )
            next_passage_id = 1
            for raw_path in raw_paths:
                if _is_excluded_path(raw_path):
                    continue
                try:
                    content = raw_path.read_text(encoding="utf-8", errors="replace")
                    stat = raw_path.stat()
                    relative = raw_path.relative_to(self.project_root).as_posix()
                except OSError:
                    continue
                title = _extract_title(content, raw_path.stem)
                connection.execute(
                    "INSERT INTO raw_documents(path, title, size, mtime_ns) VALUES (?, ?, ?, ?)",
                    (relative, title, stat.st_size, stat.st_mtime_ns),
                )
                title_tokens = " ".join(
                    safe
                    for safe in (
                        self._fts_token(token)
                        for token in self._tokenize(title)
                    )
                    if safe
                )
                rows = []
                fts_rows = []
                for passage in self._split_passages(content):
                    if _is_reference_or_citation_passage(passage.section, passage.text):
                        continue
                    body_tokens = " ".join(
                        safe
                        for safe in (
                            self._fts_token(token)
                            for token in self._tokenize(passage.text)
                        )
                        if safe
                    )
                    if not body_tokens:
                        continue
                    sec_tokens = " ".join(
                        safe
                        for safe in (
                            self._fts_token(token)
                            for token in self._tokenize(passage.section)
                        )
                        if safe
                    )
                    rows.append(
                        (
                            next_passage_id,
                            relative,
                            passage.section,
                            passage.line_start,
                            passage.line_end,
                            passage.text,
                        )
                    )
                    fts_rows.append((next_passage_id, title_tokens, sec_tokens, body_tokens))
                    next_passage_id += 1
                if rows:
                    connection.executemany(
                        """
                        INSERT INTO passages(
                            id, path, section, line_start, line_end, text
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        rows,
                    )
                    connection.executemany(
                        "INSERT INTO passage_fts(rowid, title, section, body) VALUES (?, ?, ?, ?)",
                        fts_rows,
                    )

            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                [
                    ("version", str(RAW_PASSAGE_INDEX_VERSION)),
                    ("signature", signature),
                ],
            )
            connection.commit()
            connection.execute("PRAGMA journal_mode=WAL;")
            connection.execute("PRAGMA synchronous=NORMAL;")
            connection.close()
            connection = None
            os.replace(temporary, self._raw_index_path)
        except Exception:
            if connection is not None:
                connection.rollback()
                connection.close()
            temporary.unlink(missing_ok=True)
            raise

        self._raw_index_connection = self._open_raw_index()
        self._raw_index_signature = signature

    def _sync_raw_passage_index(
        self, force_rebuild: bool = False
    ) -> tuple[sqlite3.Connection | None, list[Path]]:
        """Synchronize SQLite FTS5 passage index incrementally in <30ms."""
        signature, raw_paths = self._raw_manifest()
        if not raw_paths:
            self._close_raw_index()
            return None, []

        if not self._raw_index_path.exists() or force_rebuild:
            self._build_raw_passage_index(signature, raw_paths)
            return self._raw_index_connection, raw_paths

        if (
            self._raw_index_connection is not None
            and self._raw_index_signature == signature
        ):
            return self._raw_index_connection, raw_paths

        self._close_raw_index()
        conn = None
        try:
            conn = self._open_raw_index(read_only=False)
            cur = conn.cursor()
            meta_rows = cur.execute("SELECT key, value FROM metadata").fetchall()
            meta = {r["key"]: r["value"] for r in meta_rows}
            if meta.get("version") != str(RAW_PASSAGE_INDEX_VERSION):
                conn.close()
                conn = None
                self._build_raw_passage_index(signature, raw_paths)
                return self._raw_index_connection, raw_paths

            # If fast signature matches, no filesystem delta exists
            if meta.get("signature") == signature:
                self._raw_index_connection = conn
                self._raw_index_signature = signature
                return conn, raw_paths

            # Query indexed file metadata from SQLite
            db_rows = cur.execute(
                "SELECT path, size, mtime_ns FROM raw_documents"
            ).fetchall()
            db_map = {
                r["path"]: (int(r["size"]), int(r["mtime_ns"])) for r in db_rows
            }

            # Build current filesystem map
            fs_map = {}
            path_by_rel = {}
            for p in raw_paths:
                rel = p.relative_to(self.project_root).as_posix()
                try:
                    st = p.stat()
                    fs_map[rel] = (st.st_size, st.st_mtime_ns)
                    path_by_rel[rel] = p
                except OSError:
                    continue

            added_rels = set(fs_map) - set(db_map)
            deleted_rels = set(db_map) - set(fs_map)
            modified_rels = {
                rel
                for rel in (set(fs_map) & set(db_map))
                if fs_map[rel] != db_map[rel]
            }

            if not added_rels and not deleted_rels and not modified_rels:
                cur.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES ('signature', ?)",
                    (signature,),
                )
                conn.commit()
                self._raw_index_connection = conn
                self._raw_index_signature = signature
                return conn, raw_paths

            # Perform atomic incremental update
            cur.execute("BEGIN IMMEDIATE")
            stale_rels = deleted_rels | modified_rels
            for rel in stale_rels:
                cur.execute(
                    "DELETE FROM passage_fts WHERE rowid IN (SELECT id FROM passages WHERE path = ?)",
                    (rel,),
                )
                cur.execute("DELETE FROM passages WHERE path = ?", (rel,))
                cur.execute("DELETE FROM raw_documents WHERE path = ?", (rel,))

            reindex_rels = added_rels | modified_rels
            for rel in reindex_rels:
                path_obj = path_by_rel[rel]
                try:
                    content = path_obj.read_text(
                        encoding="utf-8", errors="replace"
                    )
                    size, mtime_ns = fs_map[rel]
                except OSError:
                    continue

                title = _extract_title(content, path_obj.stem)
                cur.execute(
                    "INSERT INTO raw_documents(path, title, size, mtime_ns) VALUES (?, ?, ?, ?)",
                    (rel, title, size, mtime_ns),
                )
                title_tokens = " ".join(
                    safe
                    for safe in (
                        self._fts_token(token)
                        for token in self._tokenize(title)
                    )
                    if safe
                )

                for passage in self._split_passages(content):
                    if _is_reference_or_citation_passage(
                        passage.section, passage.text
                    ):
                        continue
                    body_tokens = " ".join(
                        safe
                        for safe in (
                            self._fts_token(token)
                            for token in self._tokenize(passage.text)
                        )
                        if safe
                    )
                    if not body_tokens:
                        continue
                    sec_tokens = " ".join(
                        safe
                        for safe in (
                            self._fts_token(token)
                            for token in self._tokenize(passage.section)
                        )
                        if safe
                    )

                    cur.execute(
                        """
                        INSERT INTO passages(path, section, line_start, line_end, text)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            rel,
                            passage.section,
                            passage.line_start,
                            passage.line_end,
                            passage.text,
                        ),
                    )
                    pid = cur.lastrowid
                    cur.execute(
                        "INSERT INTO passage_fts(rowid, title, section, body) VALUES (?, ?, ?, ?)",
                        (pid, title_tokens, sec_tokens, body_tokens),
                    )

            cur.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES ('signature', ?)",
                (signature,),
            )
            conn.commit()
            self._raw_index_connection = conn
            self._raw_index_signature = signature
            return conn, raw_paths
        except Exception:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
                conn.close()
                conn = None
            self._close_raw_index()
            try:
                self._build_raw_passage_index(signature, raw_paths)
                return self._raw_index_connection, raw_paths
            except Exception:
                raise

    def _ensure_raw_passage_index(
        self,
    ) -> tuple[sqlite3.Connection | None, list[Path]]:
        return self._sync_raw_passage_index()

    def _query_raw_passages(
        self,
        plan: QueryPlan,
        top_k: int,
        exhaustive: bool,
    ) -> tuple[list[tuple[Path, Passage, str]], int] | None:
        """Return indexed passage candidates, or None to request legacy fallback."""
        try:
            connection, raw_paths = self._ensure_raw_passage_index()
            if connection is None:
                return [], 0
            terms = _ordered_unique(
                self._fts_token(term) for term in plan.term_weights
            )
            terms = tuple(term for term in terms if term)
            if not terms:
                return [], len(raw_paths)
            match_query = " OR ".join(f'"{term}"' for term in terms)
            sql = """
                SELECT p.path, p.section, p.line_start, p.line_end, p.text,
                       COALESCE(d.title, '') AS title
                FROM passage_fts
                JOIN passages AS p ON p.id = passage_fts.rowid
                LEFT JOIN raw_documents AS d ON d.path = p.path
                WHERE passage_fts MATCH ?
                ORDER BY bm25(passage_fts, 5.0, 3.0, 1.0)
            """
            parameters: list[Any] = [match_query]
            if not exhaustive:
                sql += " LIMIT ?"
                parameters.append(max(RAW_PASSAGE_CANDIDATE_LIMIT, top_k * 100))
            rows = connection.execute(sql, parameters).fetchall()
        except (OSError, sqlite3.Error):
            return None

        candidates = [
            (
                self.project_root / str(row["path"]),
                Passage(
                    text=str(row["text"]),
                    section=str(row["section"]),
                    line_start=int(row["line_start"]),
                    line_end=int(row["line_end"]),
                ),
                str(row["title"] or ""),
            )
            for row in rows
        ]
        return candidates, len(raw_paths)

    def _choose_raw_path(self, source_path: Path) -> tuple[str, bool]:
        candidates = self._discover_raw_papers().get(source_path.stem.lower(), [])
        if not candidates:
            return "", False
        if len(candidates) == 1:
            return candidates[0].relative_to(self.project_root).as_posix(), False
        source_parts = set(source_path.parts)
        ranked = sorted(
            candidates,
            key=lambda path: (-len(source_parts & set(path.parts)), path.as_posix()),
        )
        return ranked[0].relative_to(self.project_root).as_posix(), True

    def _document_id(self, file_path: Path) -> str:
        return file_path.relative_to(self.wiki_folder).with_suffix("").as_posix()

    def build_index(self):
        """Build and persist an INDEX_VERSION index from all wiki categories."""
        print("Building ResearchWiki search index...")
        self.index = {}
        self.documents = {}
        self.doc_metadata = {}
        self.vocab = {}
        self.idf = {}
        self.average_doc_length = 0.0
        self.index_version = INDEX_VERSION
        self.last_search_report = {}
        self._reset_runtime_caches()
        self._raw_path_to_docs = defaultdict(list)
        self._discover_raw_papers()

        for folder_name, doc_type in INDEXED_FOLDERS:
            directory = self.wiki_folder / folder_name
            if not directory.is_dir():
                continue
            for md_file in sorted(directory.rglob("*.md")):
                if _is_excluded_path(md_file):
                    continue
                self._index_file(md_file, doc_type)

        self._calculate_idf()
        self._rebuild_raw_path_links()
        print(f"  Indexed {len(self.documents)} collision-safe documents")
        self.save_index()
        try:
            self._ensure_raw_passage_index()
        except (OSError, sqlite3.Error) as exc:
            self._close_raw_index()
            print(f"Warning: raw passage index unavailable ({exc}); using scan fallback")

    def _index_file(self, file_path: Path, doc_type: str):
        """Index one wiki file under its relative-path document ID."""
        if _is_excluded_path(file_path):
            return
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            stat = file_path.stat()
        except OSError as exc:
            print(f"Error indexing {file_path}: {exc}")
            return

        doc_id = self._document_id(file_path)
        if _is_excluded_path(doc_id):
            return
        if doc_id in self.documents:
            raise ValueError(f"collision-safe document ID unexpectedly duplicated: {doc_id}")
        frontmatter = _parse_frontmatter(content)
        tags = frontmatter.get("tags") if isinstance(frontmatter.get("tags"), list) else []
        title = _extract_title(content, file_path.stem)
        raw_path = ""
        raw_ambiguous = False
        if doc_type == "paper":
            raw_path, raw_ambiguous = self._choose_raw_path(file_path)

        tokens = self._tokenize(content)
        terms = Counter(tokens)
        title_tokens = self._tokenize(f"{title} {file_path.stem}")
        tag_tokens = self._tokenize(" ".join(str(tag) for tag in tags))
        stub, source_kind, evidence_quality, quality_flags = _quality_metadata(
            content,
            doc_type,
            file_size=stat.st_size,
            raw_path=raw_path,
            raw_ambiguous=raw_ambiguous,
        )

        canonical_key = _canonical_doc_key(
            doc_id=doc_id,
            title=title,
            text=content,
            source_path=raw_path or file_path.as_posix(),
            metadata=frontmatter,
        )

        self.documents[doc_id] = content
        self.index[doc_id] = dict(terms)
        self.doc_metadata[doc_id] = {
            "title": title,
            "type": doc_type,
            "tags": tags,
            "date": frontmatter.get("date_updated") or frontmatter.get("date_created"),
            "path": file_path.relative_to(self.wiki_folder).as_posix(),
            "legacy_stem": file_path.stem,
            "length": len(tokens),
            "title_terms": dict(Counter(title_tokens)),
            "tag_terms": dict(Counter(tag_tokens)),
            "is_stub": stub,
            "source_kind": source_kind,
            "evidence_quality": evidence_quality,
            "quality_flags": quality_flags,
            "raw_path": raw_path,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "canonical_key": canonical_key,
        }
        if raw_path:
            self._raw_path_to_docs[raw_path].append(doc_id)
        for token in terms:
            if token not in self.vocab:
                self.vocab[token] = len(self.vocab)

    def _calculate_idf(self):
        document_count = len(self.documents)
        if not document_count:
            self.average_doc_length = 0.0
            return
        document_frequency: Counter[str] = Counter()
        for terms in self.index.values():
            document_frequency.update(terms.keys())
        self.idf = {
            term: math.log(
                1.0 + (document_count - frequency + 0.5) / (frequency + 0.5)
            )
            for term, frequency in document_frequency.items()
        }
        self.average_doc_length = sum(
            int(metadata.get("length", 0)) for metadata in self.doc_metadata.values()
        ) / document_count

    def _current_files(self) -> dict[str, Path]:
        current: dict[str, Path] = {}
        for folder_name, _ in INDEXED_FOLDERS:
            directory = self.wiki_folder / folder_name
            if not directory.is_dir():
                continue
            for path in directory.rglob("*.md"):
                if _is_excluded_path(path):
                    continue
                current[path.relative_to(self.wiki_folder).as_posix()] = path
        return current

    def _is_stale(self) -> bool:
        if self.index_version != INDEX_VERSION:
            return True
        if not (self.wiki_folder / DOCS_FILENAME).exists():
            return True
        changed, removed = self._changed_files()
        return bool(changed or removed)

    def _changed_files(self) -> tuple[dict[str, Path], set[str]]:
        """Split the corpus into pages needing re-indexing and vanished pages.

        Size and mtime come from the persisted metadata, so this makes the
        same comparison the whole-index staleness check made — it just reports
        *which* pages moved instead of only whether any did.
        """
        current = self._current_files()
        indexed_paths = {
            str(metadata.get("path", "")): metadata
            for metadata in self.doc_metadata.values()
        }
        changed: dict[str, Path] = {}
        for relative_path, path in current.items():
            metadata = indexed_paths.get(relative_path)
            if metadata is None:
                changed[relative_path] = path
                continue
            try:
                stat = path.stat()
            except OSError:
                changed[relative_path] = path
                continue
            if (
                int(metadata.get("size", -1)) != stat.st_size
                or int(metadata.get("mtime_ns", -1)) != stat.st_mtime_ns
            ):
                changed[relative_path] = path
        return changed, set(indexed_paths) - set(current)

    def _rebuild_raw_path_links(self) -> None:
        """Recompute the raw-path -> document-id map from current metadata."""
        links: dict[str, list[str]] = defaultdict(list)
        for doc_id, metadata in self.doc_metadata.items():
            raw_path = str(metadata.get("raw_path", "") or "")
            if raw_path:
                links[raw_path].append(doc_id)
        self._raw_path_to_docs = {
            raw_path: sorted(doc_ids) for raw_path, doc_ids in links.items()
        }

    def _apply_index_delta(
        self,
        changed: Mapping[str, Path],
        removed: Iterable[str],
    ) -> None:
        """Re-index only the pages that moved, then persist.

        Ingestion appends pages continuously, so rebuilding all 50k+ documents
        because a handful changed made every post-ingest query pay for the
        whole corpus.
        """
        removed_paths = set(removed)
        print(
            f"Search index delta: {len(changed)} changed, "
            f"{len(removed_paths)} removed; updating..."
        )
        stale_paths = removed_paths | set(changed)
        for doc_id, metadata in list(self.doc_metadata.items()):
            if str(metadata.get("path", "")) in stale_paths:
                del self.doc_metadata[doc_id]
                self.index.pop(doc_id, None)
                self.documents.pop(doc_id, None)

        # _index_file appends to this map, so it must accept unseen raw paths.
        self._raw_path_to_docs = defaultdict(list, self._raw_path_to_docs)
        doc_type_by_folder = dict(INDEXED_FOLDERS)
        for relative_path, path in sorted(changed.items()):
            doc_type = doc_type_by_folder.get(relative_path.split("/", 1)[0])
            if doc_type is not None:
                self._index_file(path, doc_type)

        self._calculate_idf()
        self._rebuild_raw_path_links()
        self._reset_runtime_caches()
        self.save_index()

    @staticmethod
    def _atomic_json_write(path: Path, payload: Any):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        os.replace(temporary, path)

    def save_index(self, path: str | None = None):
        path_obj = Path(path).expanduser().resolve() if path else self.wiki_folder / INDEX_FILENAME
        docs_path = path_obj.with_name(path_obj.stem + "_docs.json")
        index_data = {
            "version": INDEX_VERSION,
            "metadata": self.doc_metadata,
            "index": self.index,
            "idf": self.idf,
            "vocab": self.vocab,
            "average_doc_length": self.average_doc_length,
        }
        self._atomic_json_write(path_obj, index_data)
        self._atomic_json_write(docs_path, self.documents)

    def load_index(self, path: str | None = None):
        path_obj = Path(path).expanduser().resolve() if path else self.wiki_folder / INDEX_FILENAME
        docs_path = path_obj.with_name(path_obj.stem + "_docs.json")
        if not path_obj.exists() or not docs_path.exists():
            self.build_index()
            return

        now = time.monotonic()
        interval = max(0.0, float(os.environ.get("WIKI_SEARCH_VALIDATION_INTERVAL", "30.0")))
        current_sig = self._wiki_folders_signature()

        if (
            bool(self.index)
            and self._last_directory_signature == current_sig
            and (now - self._last_index_validation_time) < interval
        ):
            return

        try:
            with path_obj.open("r", encoding="utf-8") as handle:
                index_data = json.load(handle)
            if int(index_data.get("version", 0)) != INDEX_VERSION:
                print("Search index schema changed; rebuilding...")
                self.build_index()
                return
            with docs_path.open("r", encoding="utf-8") as handle:
                documents = json.load(handle)
            self.index_version = int(index_data["version"])
            self.doc_metadata = index_data.get("metadata", {})
            self.index = {
                doc_id: {term: int(frequency) for term, frequency in terms.items()}
                for doc_id, terms in index_data.get("index", {}).items()
            }
            self.idf = {
                term: float(value) for term, value in index_data.get("idf", {}).items()
            }
            self.vocab = index_data.get("vocab", {})
            self.average_doc_length = float(index_data.get("average_doc_length", 0.0))
            self.documents = documents
            self._rebuild_raw_path_links()
            self._reset_runtime_caches()
            self._last_directory_signature = current_sig
            self._last_index_validation_time = now
            changed, removed = self._changed_files()
            if changed or removed:
                self._apply_index_delta(changed, removed)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"Error loading search index ({exc}); rebuilding...")
            self.build_index()

    # ------------------------------------------------------------------
    # Ranking and passages
    # ------------------------------------------------------------------

    @staticmethod
    def _contexts_for_terms(terms: Iterable[str]) -> set[str]:
        term_set = set(terms)
        if not (_DORMANCY_TOKENS & term_set):
            return set()
        return {
            context
            for context, markers in _DORMANCY_CONTEXT_TOKENS.items()
            if markers & term_set
        }

    @staticmethod
    def _contexts_for_text(text: str, wanted: Iterable[str] | None = None) -> set[str]:
        """Identify explicit dormancy contexts within one evidence passage.

        Corpus-level token overlap is intentionally permissive, but a returned
        evidence passage needs a same-sentence phenotype relation. In
        particular, this rejects incidental terms such as ``clove bud oil`` or
        ``bud germination assay`` from a seasonal/tiller bud-dormancy search.
        """
        return FullTextSearch._contexts_for_normalized_text(
            _normalize_phrase(text), wanted
        )

    @staticmethod
    def _contexts_for_normalized_text(
        normalized: str,
        wanted: Iterable[str] | None = None,
    ) -> set[str]:
        """Context detection for text already passed through normalisation.

        Callers that hold a normalised copy (passage ranking) use this
        directly instead of normalising the same text a second time, and pass
        ``wanted`` so only the contexts the caller compares against are
        tested. Each context is first gated on whole-text substring
        conditions that any sentence-level match necessarily implies, which
        keeps the per-sentence proximity patterns off the majority of
        passages.
        """
        contexts: set[str] = set()
        targets = set(wanted) if wanted is not None else set(_DORMANCY_CONTEXT_MARKERS)
        phenotype = "dorman" in normalized or "ripening" in normalized
        seed_process = (
            phenotype or "germination" in normalized or "sprouting" in normalized
        )
        check_seed = "seed_dormancy" in targets and (
            (seed_process and ("seed" in normalized or "grain" in normalized))
            or "harvest sprouting" in normalized
        )
        check_bud = "bud_dormancy" in targets and (
            (phenotype and "bud" in normalized)
            or any(marker in normalized for marker in _BUD_STAGE_MARKERS)
        )
        check_tuber = (
            "tuber_dormancy" in targets
            and phenotype
            and ("tuber" in normalized or "potato" in normalized)
        )
        enabled = sum((check_seed, check_bud, check_tuber))
        if not enabled:
            return contexts

        for raw_sentence in _SENTENCE_SPLIT_RE.split(normalized):
            sentence = raw_sentence.strip()
            if not sentence:
                continue
            if check_seed and "seed_dormancy" not in contexts and (
                any(marker in sentence for marker in _PHS_MARKERS)
                or _SEED_CONTEXT_RE.search(sentence)
                or _GRAIN_CONTEXT_RE.search(sentence)
            ):
                contexts.add("seed_dormancy")
            if check_bud and "bud_dormancy" not in contexts and (
                any(marker in sentence for marker in _BUD_STAGE_MARKERS)
                or _BUD_CONTEXT_RE.search(sentence.replace("clove bud", ""))
            ):
                contexts.add("bud_dormancy")
            if (
                check_tuber
                and "tuber_dormancy" not in contexts
                and _TUBER_CONTEXT_RE.search(sentence)
            ):
                contexts.add("tuber_dormancy")
            if len(contexts) == enabled:
                break
        return contexts

    @staticmethod
    def _requested_dormancy_contexts(plan: QueryPlan) -> set[str]:
        """Return explicitly requested dormancy contexts from query tokens.

        A query naming one context (for example ``bud dormancy``) must not
        return a seed-dormancy passage simply because it shares generic terms.
        A multi-context query may legitimately return any named context.
        """
        query_terms = set(plan.base_tokens)
        if not (_DORMANCY_TOKENS & query_terms):
            return set()
        return {
            context
            for context, markers in _DORMANCY_CONTEXT_TOKENS.items()
            if markers & query_terms
        }

    @staticmethod
    def _contains_normalized_phrase(value: str, phrase: str) -> bool:
        """Test an already-normalised phrase against un-normalised text.

        Equivalent to matching against the normalised text, but the tolerance
        lives in one cached pattern instead of rewriting every candidate
        document for every phrase.
        """
        return _phrase_pattern(phrase).search(value) is not None

    def _document_markers(
        self, doc_id: str
    ) -> tuple[frozenset[str], bool, bool]:
        """Cache tiny dormancy/TF features instead of rebuilding huge term sets."""
        cached = self._document_marker_cache.get(doc_id)
        if cached is not None:
            return cached
        terms = self.index.get(doc_id, {})
        metadata = self.doc_metadata.get(doc_id, {})
        title_terms = metadata.get("title_terms", {})
        tag_terms = metadata.get("tag_terms", {})

        all_terms = set(terms)
        if title_terms:
            all_terms.update(title_terms)
        if tag_terms:
            all_terms.update(tag_terms)

        has_dormancy = bool(all_terms & _DORMANCY_TOKENS)
        contexts = frozenset(
            context
            for context, markers in _DORMANCY_CONTEXT_TOKENS.items()
            if has_dormancy and bool(all_terms & markers)
        )
        features = (contexts, has_dormancy, bool(all_terms & _TF_FAMILY_TOKENS))
        self._document_marker_cache[doc_id] = features
        return features

    def _bm25_score(self, doc_id: str, plan: QueryPlan) -> tuple[float, list[str]]:
        terms = self.index.get(doc_id, {})
        metadata = self.doc_metadata.get(doc_id, {})
        length = max(1, int(metadata.get("length", 0)))
        average = max(1.0, self.average_doc_length)
        k1 = 1.5
        b = 0.75
        length_norm = k1 * (1.0 - b + b * length / average)
        title_terms = metadata.get("title_terms", {})
        tag_terms = metadata.get("tag_terms", {})
        score = 0.0
        matched: list[str] = []
        default_idf = math.log(1.0 + max(1, len(self.documents)))

        for term, query_weight in plan.term_weights.items():
            frequency = int(terms.get(term, 0))
            if not frequency:
                continue
            idf = self.idf.get(term, default_idf)
            score += query_weight * idf * (
                frequency * (k1 + 1.0) / (frequency + length_norm)
            )
            score += query_weight * idf * 2.4 * min(2, int(title_terms.get(term, 0)))
            score += query_weight * idf * 1.5 * min(2, int(tag_terms.get(term, 0)))
            matched.append(term)

        if not matched:
            return 0.0, []

        title = str(metadata.get("title", ""))
        content = self.documents.get(doc_id, "")
        phrase_token_lists = (
            plan.phrase_tokens
            if len(plan.phrase_tokens) == len(plan.phrases)
            else ((),) * len(plan.phrases)
        )
        for phrase, phrase_tokens in zip(plan.phrases, phrase_token_lists):
            # Plan phrases are already normalised by _build_query_plan. A phrase
            # can only be present where every one of its word tokens is present,
            # so gate the tolerant full-text regex on the (already-available)
            # term maps. This skips the regex for candidates that cannot match
            # with identical scoring. Degenerate phrases (no indexable tokens)
            # and the disabled flag fall back to the unconditional regex.
            prefilter = PHRASE_PREFILTER_ENABLED and bool(phrase_tokens)
            title_possible = (
                all(token in title_terms for token in phrase_tokens)
                if prefilter
                else True
            )
            if title_possible and self._contains_normalized_phrase(title, phrase):
                score += 5.0
                continue
            content_possible = (
                all(token in terms for token in phrase_tokens)
                if prefilter
                else True
            )
            if content_possible and self._contains_normalized_phrase(content, phrase):
                score += 1.5

        dormancy_query = "dormancy" in plan.base_tokens
        document_contexts, has_dormancy_marker, has_tf_marker = (
            self._document_markers(doc_id)
        )
        required_contexts = self._requested_dormancy_contexts(plan)
        if required_contexts and not (required_contexts & document_contexts):
            # Preserve raw-only recall in evidence mode (which scans every raw
            # paper), but keep incompatible summaries out of bounded ranking.
            score *= 0.02
        if dormancy_query:
            if has_dormancy_marker:
                score += 6.0
            else:
                # A TF-only paper is not responsive to a dormancy-TF query.
                score *= 0.06

        strict_tf_query = {"transcription", "factor"} <= set(plan.base_tokens)
        if strict_tf_query and has_tf_marker and has_dormancy_marker:
            score += 10.0
        if document_contexts:
            score += 2.0 * len(document_contexts)

        quality = float(metadata.get("evidence_quality", 0.0))
        score *= 0.65 + quality
        if metadata.get("type") == "paper":
            score *= 1.18
        elif metadata.get("type") in {"entity", "concept"}:
            score *= 0.78
        if metadata.get("is_stub"):
            score *= 0.15
        return score, sorted(set(matched))

    def _split_passages(self, content: str, max_chars: int = 4_000) -> list[Passage]:
        lines = content.splitlines()
        if not lines:
            return []
        passages: list[Passage] = []
        current_section = "Document opening"
        chunk_lines: list[str] = []
        chunk_start = 1
        chunk_chars = 0

        def flush(end_line: int):
            nonlocal chunk_lines, chunk_chars
            text = "\n".join(chunk_lines).strip()
            if text:
                passages.append(
                    Passage(
                        text=text,
                        section=current_section,
                        line_start=chunk_start,
                        line_end=max(chunk_start, end_line),
                    )
                )
            chunk_lines = []
            chunk_chars = 0

        for line_number, line in enumerate(lines, start=1):
            heading = _HEADING_RE.match(line.strip())
            if heading:
                flush(line_number - 1)
                current_section = heading.group(2).strip()
                chunk_start = line_number
            if chunk_lines and chunk_chars + len(line) + 1 > max_chars:
                flush(line_number - 1)
                chunk_start = line_number
            elif not chunk_lines:
                chunk_start = line_number
            chunk_lines.append(line)
            chunk_chars += len(line) + 1
        flush(len(lines))
        return passages

    def _passage_features(self, text: str) -> tuple[Counter, str]:
        cached = self._passage_feature_cache.pop(text, None)
        if cached is not None:
            self._passage_feature_cache[text] = cached
            return cached
        features = (Counter(self._tokenize(text)), _normalize_phrase(text))
        self._passage_feature_cache[text] = features
        if len(self._passage_feature_cache) > PASSAGE_FEATURE_CACHE_SIZE:
            self._passage_feature_cache.popitem(last=False)
        return features

    def _rank_passage(self, passage: Passage, plan: QueryPlan) -> RankedPassage:
        frequencies, normalized = self._passage_features(passage.text)
        default_idf = math.log(1.0 + max(1, len(self.documents)))
        score = 0.0
        matches: list[str] = []
        for term, query_weight in plan.term_weights.items():
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            score += query_weight * self.idf.get(term, default_idf) * (1.0 + math.log(frequency))
            matches.append(term)
        for phrase in plan.phrases:
            if phrase in normalized:
                score += 4.0
        base_match_count = len(set(plan.base_tokens) & set(matches))
        if plan.base_tokens:
            score += 5.0 * base_match_count / len(plan.base_tokens)

        required_contexts = self._requested_dormancy_contexts(plan)
        passage_contexts = (
            self._contexts_for_normalized_text(normalized, required_contexts)
            if required_contexts
            else set()
        )
        if required_contexts and not (required_contexts & passage_contexts):
            return RankedPassage(
                passage=passage,
                score=0.0,
                matches=tuple(sorted(set(matches))),
            )
        dormancy_query = "dormancy" in plan.base_tokens
        strict_tf_query = {"transcription", "factor"} <= set(plan.base_tokens)
        passage_terms = set(frequencies) if dormancy_query or strict_tf_query else set()
        if dormancy_query:
            if _DORMANCY_TOKENS & passage_terms:
                score += 5.0
            else:
                score *= 0.08
        if strict_tf_query:
            if (_TF_FAMILY_TOKENS & passage_terms) and (_DORMANCY_TOKENS & passage_terms):
                score += 7.0

        section = passage.section.lower()
        if _is_reference_or_citation_passage(passage.section, passage.text):
            # A bibliography can help discover a paper, but it is not a source
            # passage supporting a biological claim.
            return RankedPassage(
                passage=passage,
                score=0.0,
                matches=tuple(sorted(set(matches))),
            )
        if "supplement" in section:
            score *= 0.45
        elif re.search(r"\b(results?|findings?|abstract|discussion|mechanistic|conclusions?)\b", section):
            score *= 1.12
        elif re.search(r"\b(materials?|methods?)\b", section):
            score *= 0.78

        # Mild density preference prevents long review sections from winning on
        # raw term count alone while retaining substantive passages.
        score /= 1.0 + max(0, len(passage.text) - 1_500) / 12_000
        return RankedPassage(passage=passage, score=score, matches=tuple(sorted(set(matches))))

    def _best_passage(self, content: str, plan: QueryPlan) -> RankedPassage | None:
        ranked = [self._rank_passage(passage, plan) for passage in self._split_passages(content)]
        ranked = [candidate for candidate in ranked if candidate.score > 0]
        if not ranked:
            return None
        return max(
            ranked,
            key=lambda candidate: (
                candidate.score,
                len(candidate.matches),
                -candidate.passage.line_start,
            ),
        )

    def _snippet_from_passage(self, passage: Passage, plan: QueryPlan, context_chars: int = 360) -> str:
        text = _SPACE_RE.sub(" ", passage.text).strip()
        normalized = text.lower()
        positions = [
            normalized.find(token.lower())
            for token in plan.base_tokens
            if normalized.find(token.lower()) >= 0
        ]
        best_position = min(positions) if positions else 0
        start = max(0, best_position - context_chars // 3)
        end = min(len(text), best_position + context_chars)
        snippet = text[start:end].strip()
        if start:
            snippet = "..." + snippet
        if end < len(text):
            snippet += "..."
        return snippet

    def _generate_snippet(
        self,
        content: str,
        query_tokens: Sequence[str],
        context_chars: int = 150,
    ) -> str:
        """Backward-compatible snippet helper used by older callers."""
        plan = QueryPlan(
            query=" ".join(query_tokens),
            base_tokens=_ordered_unique(query_tokens),
            term_weights={token: 1.0 for token in _ordered_unique(query_tokens)},
            phrases=(),
            canonical_terms=(),
        )
        best = self._best_passage(content, plan)
        if best is None:
            return _SPACE_RE.sub(" ", content[: context_chars * 2]).strip()
        return self._snippet_from_passage(best.passage, plan, context_chars * 2)

    def _source_content(self, metadata: Mapping[str, Any], mode: str) -> tuple[str, str]:
        wiki_path = str(metadata.get("path", "") or "")
        if mode in {"hybrid", "evidence"}:
            raw_path = str(metadata.get("raw_path", "") or "")
            if raw_path:
                absolute = self.project_root / raw_path
                try:
                    return absolute.read_text(encoding="utf-8", errors="replace"), raw_path
                except OSError:
                    pass
        doc_id = next(
            (
                key
                for key, value in self.doc_metadata.items()
                if value is metadata
            ),
            "",
        )
        return self.documents.get(doc_id, ""), wiki_path

    def _result_from_document(
        self,
        doc_id: str,
        first_stage_score: float,
        first_stage_matches: Sequence[str],
        plan: QueryPlan,
        mode: str,
    ) -> SearchResult | None:
        if _is_excluded_path(doc_id):
            return None
        metadata = self.doc_metadata.get(doc_id, {})
        content = self.documents.get(doc_id, "")
        source_path = str(metadata.get("path", "") or "")
        if _is_excluded_path(source_path):
            return None
        if mode == "hybrid" and metadata.get("type") == "paper" and metadata.get("raw_path"):
            raw_path = self.project_root / str(metadata["raw_path"])
            try:
                content = raw_path.read_text(encoding="utf-8", errors="replace")
                source_path = str(metadata["raw_path"])
            except OSError:
                pass
        best = self._best_passage(content, plan)
        if best is None:
            return None
        if _is_reference_or_citation_passage(best.passage.section, best.passage.text):
            return None
        quality = float(metadata.get("evidence_quality", 0.0))
        score = first_stage_score + best.score * (0.75 + quality)
        canonical_key = str(
            metadata.get("canonical_key")
            or _canonical_doc_key(
                doc_id=doc_id,
                title=str(metadata.get("title", doc_id)),
                text=content,
                source_path=source_path,
                metadata=metadata,
            )
        )
        return SearchResult(
            paper=doc_id,
            title=str(metadata.get("title", doc_id)),
            snippet=self._snippet_from_passage(best.passage, plan),
            score=score,
            matches=sorted(set(first_stage_matches) | set(best.matches)),
            path=str(metadata.get("path", "") or ""),
            doc_type=str(metadata.get("type", "") or ""),
            section=best.passage.section,
            source_path=source_path,
            line_start=best.passage.line_start,
            line_end=best.passage.line_end,
            evidence_quality=quality,
            quality_flags=list(metadata.get("quality_flags", [])),
            canonical_terms=list(plan.canonical_terms),
            canonical_key=canonical_key,
        )

    def _raw_result_from_passage(
        self,
        raw_path: Path,
        best: RankedPassage,
        plan: QueryPlan,
        *,
        raw_title: str = "",
    ) -> SearchResult | None:
        if _is_excluded_path(raw_path):
            return None
        if _is_reference_or_citation_passage(best.passage.section, best.passage.text):
            return None
        relative_raw = raw_path.relative_to(self.project_root).as_posix()
        linked_doc_ids = [
            d for d in self._raw_path_to_docs.get(relative_raw, [])
            if not _is_excluded_path(d)
        ]
        linked_doc_id = linked_doc_ids[0] if linked_doc_ids else ""
        metadata = self.doc_metadata.get(linked_doc_id, {})
        base_matches = set(plan.base_tokens) & set(best.matches)
        if not base_matches:
            return None
        synthetic_id = "raw/" + raw_path.relative_to(self.raw_root).with_suffix("").as_posix()
        doc_id = linked_doc_id or synthetic_id
        quality = float(metadata.get("evidence_quality", 0.88))
        flags = list(metadata.get("quality_flags", [])) or ["raw_full_text", "unlinked_raw_source"]
        if "raw_full_text_evidence" not in flags:
            flags.append("raw_full_text_evidence")
        title = str(metadata.get("title") or raw_title or raw_path.stem)
        canonical_key = str(
            metadata.get("canonical_key")
            or _canonical_doc_key(
                doc_id=doc_id,
                title=title,
                text=best.passage.text,
                source_path=relative_raw,
                metadata=metadata,
            )
        )
        return SearchResult(
            paper=doc_id,
            title=title,
            snippet=self._snippet_from_passage(best.passage, plan),
            score=best.score * (1.0 + quality),
            matches=list(best.matches),
            path=str(metadata.get("path", "") or ""),
            doc_type="paper",
            section=best.passage.section,
            source_path=relative_raw,
            line_start=best.passage.line_start,
            line_end=best.passage.line_end,
            evidence_quality=quality,
            quality_flags=flags,
            canonical_terms=list(plan.canonical_terms),
            canonical_key=canonical_key,
        )

    def _raw_result(
        self,
        raw_path: Path,
        plan: QueryPlan,
        *,
        doc_type: str | None,
        include_stubs: bool,
    ) -> SearchResult | None:
        if _is_excluded_path(raw_path):
            return None
        relative_raw = raw_path.relative_to(self.project_root).as_posix()
        linked_doc_ids = [
            d for d in self._raw_path_to_docs.get(relative_raw, [])
            if not _is_excluded_path(d)
        ]
        linked_doc_id = linked_doc_ids[0] if linked_doc_ids else ""
        metadata = self.doc_metadata.get(linked_doc_id, {})
        if doc_type and doc_type != "paper":
            return None
        if metadata.get("is_stub") and not include_stubs:
            # Raw evidence is still substantive even if its generated summary is
            # a stub; retain it and flag the summary rather than dropping it.
            pass
        try:
            content = raw_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        best = self._best_passage(content, plan)
        if best is None:
            return None
        if _is_reference_or_citation_passage(best.passage.section, best.passage.text):
            return None
        return self._raw_result_from_passage(
            raw_path,
            best,
            plan,
            raw_title=_extract_title(content, raw_path.stem),
        )

    # ------------------------------------------------------------------
    # Public search API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 10,
        doc_type: str | None = None,
        *,
        mode: str = "hybrid",
        include_stubs: bool = False,
        exhaustive: bool = False,
    ) -> list[SearchResult]:
        """Search wiki summaries and/or raw evidence.

        ``summary`` ranks compiled wiki pages; ``hybrid`` reranks strong wiki
        candidates against linked raw papers; ``evidence`` retrieves and ranks
        exact passages from the persistent raw-paper index, falling back to a
        full raw scan when the index is unavailable. With ``exhaustive=True``,
        all positive matches in the indexed corpus are returned instead of
        applying ``top_k``.
        """
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        mode = mode.lower().strip()
        if mode == "full_text":
            mode = "evidence"
        if mode not in SEARCH_MODES:
            raise ValueError(f"mode must be one of {SEARCH_MODES}")
        if doc_type == "source":
            doc_type = "paper"
        if doc_type is not None and doc_type not in DOC_TYPES:
            raise ValueError(f"doc_type must be one of {DOC_TYPES} or None")
        if not self.index:
            self.load_index()

        cache_key = (query, top_k, doc_type, mode, include_stubs, exhaustive)
        if mode == "summary":
            cached = self._summary_query_cache.pop(cache_key, None)
            if cached is not None:
                payloads, report = cached
                self._summary_query_cache[cache_key] = cached
                self.last_search_report = copy.deepcopy(report)
                self.last_search_report["cache_hit"] = True
                return [SearchResult(**copy.deepcopy(item)) for item in payloads]

        plan = self._build_query_plan(query)
        if not plan.base_tokens:
            self.last_search_report = {
                "query": query,
                "reason": "query contains no searchable tokens",
                "returned_results": 0,
            }
            return []

        eligible_ids = [
            doc_id
            for doc_id, metadata in self.doc_metadata.items()
            if (doc_type is None or metadata.get("type") == doc_type)
            and (include_stubs or not metadata.get("is_stub"))
            and not _is_excluded_path(doc_id)
            and not _is_excluded_path(metadata.get("path", ""))
        ]
        first_stage: list[tuple[str, float, list[str]]] = []
        if mode != "evidence":
            query_terms = tuple(plan.term_weights)
            candidate_ids = (
                doc_id for doc_id in eligible_ids
                if any(term in self.index.get(doc_id, {}) for term in query_terms)
            )
            for doc_id in candidate_ids:
                score, matches = self._bm25_score(doc_id, plan)
                if score > 0 and matches:
                    first_stage.append((doc_id, score, matches))
            first_stage.sort(key=lambda item: (-item[1], item[0]))

        passage_documents_evaluated = 0
        raw_documents_scanned = 0
        raw_indexed_documents = 0
        raw_passage_candidates = 0
        raw_index_used = False
        results: list[SearchResult] = []

        if mode == "evidence":
            if not doc_type or doc_type == "paper":
                indexed = self._query_raw_passages(plan, top_k, exhaustive)
            else:
                indexed = ([], 0)
            if indexed is not None:
                indexed_rows, raw_indexed_documents = indexed
                raw_index_used = True
                raw_passage_candidates = len(indexed_rows)
                best_by_raw_path: dict[str, tuple[RankedPassage, Path, str]] = {}
                for raw_path, passage, raw_title in indexed_rows:
                    if _is_excluded_path(raw_path):
                        continue
                    if _is_reference_or_citation_passage(passage.section, passage.text):
                        continue
                    best = self._rank_passage(passage, plan)
                    if best.score <= 0:
                        continue
                    relative = raw_path.relative_to(self.project_root).as_posix()
                    existing = best_by_raw_path.get(relative)
                    if existing is None or best.score > existing[0].score:
                        best_by_raw_path[relative] = (best, raw_path, raw_title)
                for best, raw_path, raw_title in best_by_raw_path.values():
                    result = self._raw_result_from_passage(
                        raw_path,
                        best,
                        plan,
                        raw_title=raw_title,
                    )
                    if result is not None:
                        passage_documents_evaluated += 1
                        results.append(result)
            else:
                raw_paths = [
                    path
                    for paths in self._discover_raw_papers().values()
                    for path in paths
                    if not _is_excluded_path(path)
                ]
                for raw_path in sorted(set(raw_paths)):
                    raw_documents_scanned += 1
                    result = self._raw_result(
                        raw_path,
                        plan,
                        doc_type=doc_type,
                        include_stubs=include_stubs,
                    )
                    if result is not None:
                        passage_documents_evaluated += 1
                        results.append(result)
        else:
            if exhaustive:
                candidate_rows = first_stage
            else:
                candidate_limit = max(top_k * (10 if mode == "hybrid" else 4), 80)
                candidate_rows = first_stage[:candidate_limit]
            for doc_id, score, matches in candidate_rows:
                result = self._result_from_document(doc_id, score, matches, plan, mode)
                if result is not None:
                    passage_documents_evaluated += 1
                    results.append(result)

            # Exhaustive hybrid mode also searches raw-only/summary-missed papers.
            if mode == "hybrid" and exhaustive:
                existing_sources = {result.source_path for result in results}
                raw_paths = [
                    path
                    for paths in self._discover_raw_papers().values()
                    for path in paths
                    if not _is_excluded_path(path)
                ]
                for raw_path in sorted(set(raw_paths)):
                    relative_raw = raw_path.relative_to(self.project_root).as_posix()
                    if relative_raw in existing_sources:
                        continue
                    raw_documents_scanned += 1
                    result = self._raw_result(
                        raw_path,
                        plan,
                        doc_type=doc_type,
                        include_stubs=include_stubs,
                    )
                    if result is not None:
                        results.append(result)
                        passage_documents_evaluated += 1

        # Keep one result per canonical document (deduplicating duplicate reviews/papers), preferring strongest score & quality.
        best_by_canonical: dict[str, SearchResult] = {}
        for result in results:
            if _is_excluded_path(result.path) or _is_excluded_path(result.source_path) or _is_excluded_path(result.paper):
                continue
            if _is_reference_or_citation_passage(result.section, result.snippet):
                continue
            canon_key = getattr(result, "canonical_key", "") or _canonical_doc_key(
                doc_id=result.paper,
                title=result.title,
                text=result.snippet,
                source_path=result.source_path or result.path,
            )
            existing = best_by_canonical.get(canon_key)
            if existing is None or (result.score, result.evidence_quality) > (existing.score, existing.evidence_quality):
                best_by_canonical[canon_key] = result
        results = sorted(
            best_by_canonical.values(),
            key=lambda result: (
                -result.score,
                -result.evidence_quality,
                result.title.lower(),
                result.paper,
            ),
        )
        positive_results = len(results)
        returned = results if exhaustive else results[:top_k]

        stub_eligible = sum(
            1 for metadata in self.doc_metadata.values() if metadata.get("is_stub")
        )

        first_stage_ids = {doc_id for doc_id, _, _ in first_stage}
        returned_contexts: dict[str, int] = {name: 0 for name in _DORMANCY_CONTEXT_MARKERS}
        for result in returned:
            # Evidence-mode output can come from raw text whose generated wiki
            # summary has a different context. Re-read the complete selected
            # source span so reporting is not distorted by a truncated snippet.
            passage_text = ""
            if (
                result.source_path
                and result.line_start is not None
                and result.line_end is not None
            ):
                source_root = (
                    self.project_root
                    if result.source_path.startswith("raw/")
                    else self.wiki_folder
                )
                try:
                    source_lines = (source_root / result.source_path).read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines()
                    passage_text = "\n".join(
                        source_lines[result.line_start - 1 : result.line_end]
                    )
                except OSError:
                    pass
            if not passage_text:
                passage_text = result.snippet
            for context in self._contexts_for_text(passage_text):
                returned_contexts[context] += 1
        requested_context_tokens = {
            "seed_dormancy": {"seed", "grain"},
            "bud_dormancy": {"bud", "buds", "endodormancy", "ecodormancy", "paradormancy"},
            "tuber_dormancy": {"tuber", "potato"},
        }
        eligible_context_counts: Counter[str] = Counter()
        for doc_id in eligible_ids:
            eligible_context_counts.update(self._document_markers(doc_id)[0])
        first_stage_context_counts: Counter[str] = Counter()
        for doc_id in first_stage_ids:
            first_stage_context_counts.update(self._document_markers(doc_id)[0])

        context_coverage = {}
        for context, request_tokens in requested_context_tokens.items():
            context_coverage[context] = {
                "requested": bool(request_tokens & set(plan.base_tokens)),
                "eligible_documents": eligible_context_counts[context],
                "first_stage_matches": first_stage_context_counts[context],
                "returned_results": returned_contexts[context],
                "coverage_gap": bool(request_tokens & set(plan.base_tokens))
                and returned_contexts[context] == 0,
            }

        self.last_search_report = {
            "index_version": INDEX_VERSION,
            "query": query,
            "mode": mode,
            "doc_type": doc_type,
            "include_stubs": include_stubs,
            "exhaustive": exhaustive,
            "top_k": None if exhaustive else top_k,
            "query_tokens": list(plan.base_tokens),
            "expanded_terms": sorted(set(plan.term_weights) - set(plan.base_tokens)),
            "canonical_terms": list(plan.canonical_terms),
            "dormancy_context_coverage": context_coverage,
            "indexed_documents": len(self.documents),
            "indexed_stubs": stub_eligible,
            "eligible_documents": len(eligible_ids),
            "first_stage_matches": len(first_stage),
            "first_stage_evaluated": (
                len(first_stage)
                if exhaustive or mode == "evidence"
                else min(len(first_stage), max(top_k * (10 if mode == "hybrid" else 4), 80))
            ),
            "raw_documents_scanned": raw_documents_scanned,
            "raw_index_used": raw_index_used,
            "raw_indexed_documents": raw_indexed_documents,
            "raw_passage_candidates": raw_passage_candidates,
            "passage_documents_evaluated": passage_documents_evaluated,
            "positive_results": positive_results,
            "returned_results": len(returned),
            "truncated": not exhaustive and positive_results > len(returned),
            "cache_hit": False,
            "coverage_scope": (
                "indexed raw passage candidates" if mode == "evidence" and raw_index_used else
                "all raw Markdown papers" if mode == "evidence" else
                "all positive first-stage matches plus raw-only papers" if exhaustive and mode == "hybrid" else
                "bounded first-stage candidates"
            ),
        }
        if mode == "summary":
            cached_value = (
                [result.as_dict() for result in returned],
                copy.deepcopy(self.last_search_report),
            )
            self._summary_query_cache[cache_key] = cached_value
            if len(self._summary_query_cache) > SUMMARY_QUERY_CACHE_SIZE:
                self._summary_query_cache.popitem(last=False)
        return returned

    def search_entities(self, query: str, **kwargs: Any) -> list[SearchResult]:
        return self.search(query, doc_type="entity", **kwargs)

    def search_papers(self, query: str, **kwargs: Any) -> list[SearchResult]:
        return self.search(query, doc_type="paper", **kwargs)


__all__ = [
    "DOC_TYPES",
    "INDEX_VERSION",
    "SEARCH_MODES",
    "FullTextSearch",
    "QueryPlan",
    "SearchResult",
]
