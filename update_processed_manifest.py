#!/usr/bin/env python3
"""Maintain a human-readable manifest of ingested papers.

Scans ``wiki/sources/**/*.md`` (the wiki output of the ingest pipeline) and
writes ``wiki/processed_papers.json`` — a flat, readable record keyed by paper
slug. Each entry captures where the PDF lives, where the wiki page landed, the
topic folder, when it was last updated, and how many source citations it has.

This manifest is the *readable* layer on top of ``pipeline_state.json`` (which
is a content-fingerprint cache that actually prevents re-ingestion). Together
they guarantee a paper is never processed twice:

  * ``pipeline_state.json`` (ingest step) → ingest_parallel.py skips the paper.
  * ``wiki/processed_papers.json`` → this file; for humans / other tools.

Re-run any time; it is idempotent (regenerates from current wiki output).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCES_DIR = BASE / "wiki" / "sources"
MANIFEST = BASE / "wiki" / "processed_papers.json"

_FRONT_KEY = re.compile(r"^(\w[\w-]*):\s*(.+)$")
_H2 = re.compile(r"^##\s+(.*?)\s*$")


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). Frontmatter is the --- block."""
    fm: dict = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end]
            body = text[end + 4:]
            for line in block.splitlines():
                m = _FRONT_KEY.match(line)
                if m:
                    fm[m.group(1)] = m.group(2).strip()
    return fm, body


def _count_sections(body: str) -> int:
    return sum(1 for line in body.splitlines() if _H2.match(line))


def build_manifest() -> dict:
    entries: dict[str, dict] = {}
    if not SOURCES_DIR.exists():
        return entries
    for md in sorted(SOURCES_DIR.rglob("*.md")):
        if md.parent == SOURCES_DIR:  # top-level stray (no topic folder)
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        fm, body = _parse_frontmatter(text)
        slug = md.stem
        topic = md.parent.name
        # Map the wiki source path back to the data/ PDF location.
        pdf_path = f"../data/{topic}/{slug}.pdf"
        entries[slug] = {
            "slug": slug,
            "topic": topic,
            "pdf": pdf_path,
            "wiki_page": f"wiki/sources/{topic}/{slug}.md",
            "model": fm.get("model", "unknown"),
            "type": fm.get("type", "source"),
            "year": fm.get("year"),
            "journal": fm.get("journal"),
            "doi": fm.get("doi"),
            "source_count": int(fm.get("source_count", 1) or 1),
            "sections": _count_sections(body),
            "bytes": len(text),
            "date_created": fm.get("date_created"),
            "date_updated": fm.get("date_updated"),
            "status": "processed",
        }
    return entries


def main() -> int:
    entries = build_manifest()
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_dir": "wiki/sources",
        "count": len(entries),
        "papers": entries,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {MANIFEST} with {len(entries)} processed paper(s).")
    # Per-topic summary
    by_topic: dict[str, int] = {}
    for e in entries.values():
        by_topic[e["topic"]] = by_topic.get(e["topic"], 0) + 1
    for t, n in sorted(by_topic.items()):
        print(f"  {t}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
