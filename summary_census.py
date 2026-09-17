#!/usr/bin/env python3
"""
summary_census.py — richness census of wiki/sources pages.

Reports how many pages meet the deep-summary spec (>= adaptive word minimum
and >= 8 footnote definitions, or scaled equivalents) vs old-style thin pages.

Usage: python3 summary_census.py [--json census_report.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

RW = Path(__file__).resolve().parent
SOURCES = RW / "wiki" / "sources"
CUTOFF = 1755282600.0  # 2026-08-16 local approx; used only for reporting buckets

FN_DEF_RE = re.compile(r"(?m)^\[\^[\w-]+\]:")


def page_stats(path: Path) -> dict:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "words": len(txt.split()),
        "footnotes": len(FN_DEF_RE.findall(txt)),
        "sections": len(re.findall(r"(?m)^## ", txt)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write full report to this path")
    args = ap.parse_args()

    rich = old_thin = 0
    thin_pages = []
    total_words = 0
    n = 0
    for topic_dir in sorted(SOURCES.iterdir()):
        if not topic_dir.is_dir() or topic_dir.name.startswith("."):
            continue
        for md in sorted(topic_dir.glob("*.md")):
            try:
                st = page_stats(md)
            except Exception:
                continue
            n += 1
            total_words += st["words"]
            # Rich-spec heuristic: >= 2500 words and >= 6 footnotes and >= 12 sections
            if st["words"] >= 2500 and st["footnotes"] >= 6 and st["sections"] >= 12:
                rich += 1
            else:
                old_thin += 1
                thin_pages.append({
                    "path": str(md.relative_to(RW)),
                    **st,
                    "mtime": os.path.getmtime(md),
                })

    thin_pages.sort(key=lambda x: x["mtime"])
    print(f"total pages:        {n}")
    print(f"rich-spec pages:    {rich} ({100*rich/max(1,n):.1f}%)")
    print(f"old/thin pages:     {old_thin}")
    print(f"total words:        {total_words:,}")
    if thin_pages:
        oldest = thin_pages[0]
        newest_thin = thin_pages[-1]
        print(f"oldest thin page:   {oldest['path']}")
        print(f"newest thin page:   {newest_thin['path']}")

    if args.json:
        out = RW / args.json
        out.write_text(json.dumps({
            "total": n, "rich": rich, "old_thin": old_thin,
            "total_words": total_words, "thin_pages": thin_pages,
        }, indent=1), encoding="utf-8")
        print(f"report written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
