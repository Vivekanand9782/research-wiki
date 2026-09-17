"""fix_related_sources.py — bulk-remove source-paper wikilinks from ``## Related pages``.

The wiki schema (see ``GEMINI.md``) says:

  * ``**Sources**:`` (top of page) — source-paper wikilinks live here.
  * ``## Related pages``           — only concept / entity wikilinks live here.

The seed-page generator has been mixing the two: source-paper wikilinks
(targets that live under ``wiki/sources/``) keep showing up under
``## Related pages``. This script walks every page outside ``wiki/sources/``
and strips those misplaced bullets.

It is conservative:
  * Only touches lines inside the ``## Related pages`` section.
  * Only touches lines that match a single-bullet wikilink pattern.
  * A wikilink target is considered a "source" iff its stem (text before
    ``|`` alias and before ``#`` anchor) matches the stem of a real ``.md``
    file under ``wiki/sources/``.
  * Defaults to **dry-run** — prints what it would change and writes nothing
    until you pass ``--apply``.

Usage::

    python3 fix_related_sources.py                # dry run, full report
    python3 fix_related_sources.py --apply        # actually write changes
    python3 fix_related_sources.py --pattern 'entities/*.md' --apply
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WIKI = Path(__file__).resolve().parent / "wiki"
SOURCES_DIR = WIKI / "sources"

# Heading that opens the section we edit. Matched case-insensitively, allowing
# trailing whitespace but nothing else (so we don't catch ``## Related pages
# (legacy)`` etc.).
SECTION_HEADING_RE = re.compile(r"^\s*##\s+Related\s+pages\s*$", re.IGNORECASE)
# Any other ``## `` heading closes the section.
NEXT_HEADING_RE = re.compile(r"^\s*##\s+\S")
# A bullet line containing exactly one wikilink, e.g.
#   - [[foo]]
#   - [[foo|alias]]
#   - [[foo#anchor]]
BULLET_LINK_RE = re.compile(
    r"^\s*[-*]\s*\[\[\s*([^\]|#]+?)\s*(?:#[^\]|]*)?(?:\|[^\]]*)?\s*\]\]\s*$"
)


def collect_source_stems() -> set[str]:
    """Return the stems of every markdown file under ``wiki/sources/``."""
    if not SOURCES_DIR.exists():
        return set()
    return {p.stem for p in SOURCES_DIR.rglob("*.md")}


def candidate_pages(pattern: str | None) -> list[Path]:
    """Pages eligible for the fix: under ``wiki/`` but not under ``wiki/sources/``."""
    if pattern:
        files = list(WIKI.glob(pattern))
    else:
        files = list(WIKI.rglob("*.md"))
    out = []
    for f in files:
        if not f.is_file():
            continue
        try:
            f.relative_to(SOURCES_DIR)
            continue  # skip anything inside sources/
        except ValueError:
            pass
        out.append(f)
    return out


def fix_text(text: str, source_stems: set[str]) -> tuple[str, list[str]]:
    """Return ``(new_text, removed_stems)``. Idempotent."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    removed: list[str] = []
    in_section = False

    for line in lines:
        if not in_section:
            out.append(line)
            if SECTION_HEADING_RE.match(line):
                in_section = True
            continue

        # We're inside ``## Related pages``.
        if NEXT_HEADING_RE.match(line):
            in_section = False
            out.append(line)
            continue

        m = BULLET_LINK_RE.match(line)
        if m:
            stem = m.group(1).strip()
            if stem in source_stems:
                removed.append(stem)
                continue  # drop the line entirely
        out.append(line)

    return "".join(out), removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", default=None,
                        help="Glob (relative to wiki/) to restrict the scan, "
                             "e.g. 'entities/*.md'")
    parser.add_argument("--apply", action="store_true",
                        help="Actually write changes. Default is dry-run.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-file output; only print the summary.")
    args = parser.parse_args(argv)

    if not WIKI.exists():
        print(f"ERROR: wiki directory not found: {WIKI}", file=sys.stderr)
        return 2

    source_stems = collect_source_stems()
    if not source_stems:
        print("ERROR: no markdown files under wiki/sources/ — nothing to compare against.",
              file=sys.stderr)
        return 1

    pages = candidate_pages(args.pattern)
    files_with_changes = 0
    total_removed = 0
    sample_changes: list[tuple[Path, list[str]]] = []

    for path in pages:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"  ! skipping {path}: {e}", file=sys.stderr)
            continue

        new_text, removed = fix_text(text, source_stems)
        if not removed:
            continue

        files_with_changes += 1
        total_removed += len(removed)

        if not args.quiet:
            rel = path.relative_to(WIKI).as_posix()
            print(f"  {rel}  ({len(removed)} link{'s' if len(removed) != 1 else ''})")
            for stem in removed:
                print(f"      - [[{stem}]]")
        else:
            sample_changes.append((path, removed))

        if args.apply:
            path.write_text(new_text, encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY RUN"
    print()
    print(f"[{mode}] scanned {len(pages)} pages "
          f"(source pool: {len(source_stems)} papers, "
          f"pattern: {args.pattern or 'all'})")
    print(f"[{mode}] {files_with_changes} file{'s' if files_with_changes != 1 else ''} "
          f"would change, {total_removed} bullet{'s' if total_removed != 1 else ''} removed.")
    if not args.apply and files_with_changes:
        print("Re-run with --apply to write changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
