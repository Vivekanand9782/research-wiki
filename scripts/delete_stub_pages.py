"""Delete *whole-stub* seed pages from wiki/entities/ and wiki/concepts/.

A "whole-stub" page is one whose **Summary** itself is a ``_Stub: ..._``
placeholder — i.e. the page was created from a snippet too thin to summarise
and carries no real content. These are safe to delete and (after the
significance-gate fix in pdf_extractor.py) will NOT be recreated on a
``--force`` re-run; pages whose subject is discussed substantively by some
paper will be regenerated properly from that paper.

CRITICAL: a page with a real **Summary** that merely *contains* legacy
``_Stub:`` finding blocks (e.g. a heavily-cited hub page like
``triticum-aestivum.md``) is NEVER deleted — only pages whose Summary itself
is a stub qualify.

Default mode is dry-run. ``--apply`` deletes; each deleted file is first
copied to ``.backup/delete_stubs_<ts>/<rel-path>`` so the action is
reversible.
"""
from __future__ import annotations

import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
DIRS = [WIKI / "entities", WIKI / "concepts"]

# The Summary section content, captured up to the next blank line / heading.
SUMMARY_RE = re.compile(r"\*\*Summary\*\*:\s*\n(.+?)\n", re.DOTALL)


def is_whole_stub(text: str) -> bool:
    """True iff the page's **Summary** body itself is a ``_Stub:`` placeholder."""
    m = SUMMARY_RE.search(text)
    if not m:
        return False
    return m.group(1).strip().startswith("_Stub:")


def find_stub_pages() -> list[Path]:
    out = []
    for d in DIRS:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            try:
                if is_whole_stub(p.read_text(encoding="utf-8")):
                    out.append(p)
            except OSError:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="actually delete (default: dry-run, list only)")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap number of pages acted on (0 = no cap)")
    args = ap.parse_args()

    pages = find_stub_pages()
    if args.limit:
        pages = pages[:args.limit]

    if not pages:
        print("No whole-stub pages found.")
        return 0

    if not args.apply:
        print(f"[dry-run] {len(pages)} whole-stub page(s) would be deleted "
              f"(backups to .backup/). Sample:")
        for p in pages[:20]:
            print(f"  - {p.relative_to(ROOT)}")
        if len(pages) > 20:
            print(f"  ... and {len(pages) - 20} more")
        print("\nRe-run with --apply to delete (each file is backed up first).")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = ROOT / ".backup" / f"delete_stubs_{ts}"
    deleted = 0
    for p in pages:
        dest = backup_root / p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(p, dest)
            p.unlink()
            deleted += 1
        except OSError as e:
            print(f"  ⚠️  failed on {p.relative_to(ROOT)}: {e}", file=sys.stderr)
    print(f"Deleted {deleted}/{len(pages)} whole-stub page(s). "
          f"Backups: {backup_root.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
