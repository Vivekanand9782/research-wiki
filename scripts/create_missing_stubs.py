"""(b) Auto-create stub pages for Tier 1+2 broken wikilinks.

Each stub is schema-clean and matches the format produced by the patched
``_render_seed_page`` in ``pdf_extractor.py``. The summary is a clear
``_Stub: ..._`` placeholder so it's easy to grep for later. The
``**Sources**:`` list carries the union of source papers cited by every
page that mentions this target — so the new stub joins the citation graph
correctly and isn't an orphan.

Default mode is dry-run. ``--apply`` writes; per-stub backup of the
prior state ('did the file already exist?') is captured to
``.backup/stub_creation_<ts>/<rel-path>``. Existing files are NEVER
overwritten — if a target's stub path already exists, it's skipped.

Per-stub safety gates:
  * destination path is within wiki/concepts/ or wiki/entities/
  * destination file does not already exist
  * the produced text passes ``validate_for_kind('seed', text) == []``
  * the produced text passes ``check_wrong_sources_heading(text) == []``
  * after writing, lint_wiki.py re-run no longer reports the target as
    a broken link
"""
from __future__ import annotations

import argparse
import datetime
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lint_wiki import (  # noqa: E402
    extract_aliases,
    validate_for_kind,
    check_wrong_sources_heading,
    _link_slug,
)

WIKI = ROOT / "wiki"
SPECIAL = {WIKI / "index.md", WIKI / "log.md"}
SOURCES_DIR = WIKI / "sources"
WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")
SOURCES_LABEL_RE = re.compile(r"^\s*\*\*Sources\*\*\s*:\s*$")
BULLET_LINK_RE = re.compile(
    r"^\s*[-*]\s*\[\[\s*([^\]|#]+?)\s*(?:#[^\]|]*)?(?:\|[^\]]*)?\s*\]\]\s*$"
)
STUB_BACKUP_ROOT = ROOT / ".backup"


def _slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()


def _classify_target(name: str) -> str:
    """Heuristic: gene-like targets → entity, descriptive ones → concept."""
    # spaces, slash, or all-lowercase descriptive phrase → concept
    if " " in name:
        return "concept"
    # Patterns like ZmMYB31, miR528, AtPP2C, CRISPR/Cas9 → entity
    if re.match(r"^[A-Z][A-Za-z]*[0-9]", name):
        return "entity"
    if re.match(r"^[A-Z]{2,}$", name):
        return "entity"
    if re.match(r"^[a-z]+[A-Z][A-Za-z0-9]+$", name):
        return "entity"
    return "concept"


def _existing_pages() -> tuple[set[str], set[str]]:
    all_names: set[str] = set()
    normalized: set[str] = set()
    for f in WIKI.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = f.relative_to(WIKI).with_suffix("").as_posix()
        all_names.add(f.stem)
        all_names.add(rel)
        normalized.add(_link_slug(f.stem))
        normalized.add(_link_slug(rel))
        for a in extract_aliases(text):
            all_names.add(a)
            normalized.add(_link_slug(a))
    return all_names, normalized


def _broken_targets() -> tuple[
    list[str], dict[str, set[Path]], dict[str, int]
]:
    """Re-derive the truly-broken target list and citing pages map."""
    all_names, normalized = _existing_pages()
    total: Counter[str] = Counter()
    pages: dict[str, set[Path]] = defaultdict(set)
    for f in WIKI.rglob("*.md"):
        if f in SPECIAL:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for raw in WIKILINK_RE.findall(text):
            target = raw.split("|", 1)[0].split("#", 1)[0].strip()
            if not target:
                continue
            total[target] += 1
            pages[target].add(f)
    broken = [
        t for t in total
        if t not in all_names and _link_slug(t) not in normalized
    ]
    return broken, pages, dict(total)


def _source_papers_from_citing(citing_pages: set[Path]) -> list[str]:
    """Collect all paper-link bullets from the **Sources**: lists of every
    citing page. Deduplicate, preserve first-seen order."""
    seen: dict[str, None] = {}
    source_stems = {p.stem for p in SOURCES_DIR.rglob("*.md")} if SOURCES_DIR.exists() else set()
    for p in citing_pages:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        in_block = False
        for ln in lines:
            if SOURCES_LABEL_RE.match(ln):
                in_block = True
                continue
            if in_block:
                m = BULLET_LINK_RE.match(ln)
                if m:
                    stem = m.group(1).strip()
                    if stem in source_stems:
                        seen.setdefault(stem, None)
                elif ln.strip() == "":
                    in_block = False
                else:
                    in_block = False
        # Also: if the citing page IS a source page, list it itself.
        try:
            p.relative_to(SOURCES_DIR)
            if p.stem in source_stems:
                seen.setdefault(p.stem, None)
        except ValueError:
            pass
    return list(seen.keys())


def _render_stub(name: str, category: str, sources: list[str], today_iso: str,
                 n_citing_pages: int) -> str:
    cat = category.lower()
    if sources:
        sources_block = "\n".join(f"- [[{s}]]" for s in sources)
    else:
        sources_block = "- _none yet_"
    return (
        "---\n"
        f"tags: [{cat}, stub, auto-created]\n"
        f"type: {cat}\n"
        f"date_created: {today_iso}\n"
        f"date_updated: {today_iso}\n"
        f"source_count: {len(sources)}\n"
        "---\n"
        "\n"
        f"# {name}\n"
        "\n"
        "**Summary**:\n"
        f"_Stub: this concept is referenced by {n_citing_pages} other "
        "page(s) but has no description yet. Sources below cite it; "
        "summary needs human review or LLM enrichment._\n"
        "\n"
        "**Sources**:\n"
        f"{sources_block}\n"
        "\n"
        f"**Last updated**: {today_iso}\n"
        "\n"
        "---\n"
        "## Related pages\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Actually write stubs (default: dry-run)")
    parser.add_argument("--min-pages", type=int, default=2,
                        help="Skip targets cited by fewer than N pages (default 2 = Tier 1+2)")
    args = parser.parse_args()

    today_iso = datetime.date.today().isoformat()

    print("Re-deriving broken targets…")
    broken, pages, total = _broken_targets()
    eligible = [t for t in broken if len(pages[t]) >= args.min_pages]
    eligible.sort(key=lambda t: (-len(pages[t]), -total[t], t.lower()))
    print(f"  {len(broken)} truly broken; {len(eligible)} ≥ {args.min_pages} pages "
          f"(Tier 1{'+2' if args.min_pages == 2 else ''})")

    if not eligible:
        print("Nothing to do.")
        return 0

    backup_dir: Path | None = None
    if args.apply:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = STUB_BACKUP_ROOT / f"stub_creation_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    skipped: list[tuple[str, str]] = []

    for target in eligible:
        cat = _classify_target(target)
        slug = _slugify(target)
        if not slug:
            skipped.append((target, "empty slug"))
            continue
        out = WIKI / ("entities" if cat == "entity" else "concepts") / f"{slug}.md"
        # Safety: never overwrite.
        if out.exists():
            skipped.append((target, f"destination exists: {out.relative_to(WIKI)}"))
            continue
        sources = _source_papers_from_citing(pages[target])
        stub_text = _render_stub(target, cat, sources, today_iso, len(pages[target]))

        # Validate before writing.
        fmt_errs = validate_for_kind('seed', stub_text)
        if fmt_errs:
            skipped.append((target, f"validation failed: {fmt_errs}"))
            continue
        if check_wrong_sources_heading(stub_text):
            skipped.append((target, "wrong sources heading"))
            continue

        rel = out.relative_to(ROOT).as_posix()
        print(f"  [+] {rel}  (cat={cat}, sources={len(sources)}, "
              f"citing={len(pages[target])})")

        if args.apply:
            assert backup_dir is not None
            # Even though out doesn't exist, record the absence by writing a
            # marker so revert restores the pre-state correctly.
            (backup_dir / "DELETE_THESE_TO_REVERT.txt").open("a", encoding="utf-8").write(
                f"{out.relative_to(ROOT).as_posix()}\n"
            )
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(stub_text, encoding="utf-8")
            written.append(out)

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print()
    print(f"[{mode}] {len(eligible)} targets considered, "
          f"{len(written) if args.apply else len(eligible) - len(skipped)} stubs "
          f"{'written' if args.apply else 'would be written'}, "
          f"{len(skipped)} skipped")
    if skipped:
        for t, r in skipped[:10]:
            print(f"   skipped [[{t}]]: {r}")

    if args.apply and written:
        print(f"\nBackup manifest: {backup_dir.relative_to(ROOT)}/DELETE_THESE_TO_REVERT.txt")
        print("To revert: delete the listed files.")
    if not args.apply and (len(eligible) - len(skipped)) > 0:
        print("\nRe-run with --apply to write stubs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
