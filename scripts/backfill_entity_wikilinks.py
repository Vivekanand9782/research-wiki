#!/usr/bin/env python3
"""Backfill missing [[wikilinks]] in existing wiki source pages.

Why this exists
---------------
The two-stage ingestion path returns ``entities[]`` as structured objects whose
``text`` is a plain display form. That schema's own description promises "the
renderer canonicalises against wiki_vocabulary", but
``renderer._canonicalise_wikilinks`` only ever *rewrote* existing ``[[...]]``
tokens -- it never created them. So ``## Important Entities`` rendered as plain
bullets, silently violating the prompt rule "Every entity in ## Important
Entities MUST be in [[double brackets]]" and orphaning those entities from the
wiki graph.

``renderer._linkify_entity_bullets`` fixes this for all future ingestion. This
script repairs the pages already on disk. It is deterministic and needs no LLM
call: the entity names are already present in the page text.

Usage (from research-wiki/)::

    python3 scripts/backfill_entity_wikilinks.py --dry-run
    python3 scripts/backfill_entity_wikilinks.py --apply
    python3 scripts/backfill_entity_wikilinks.py --apply --limit 20
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from renderer import _linkify_entity_bullets  # noqa: E402

WIKI_SOURCES = ROOT / "wiki" / "sources"
RAW_PAPERS = ROOT / "raw" / "papers"

H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:[#|][^\]]*)?\]\]")
#: ``- **Seed Dormancy**: Definition.`` -> ``- **[[Seed Dormancy]]**: Definition.``
#: The leading bullet is optional: some pages render concepts as bare
#: ``**Concept**: Definition`` lines (no ``-``), which still need linking.
CONCEPT_BULLET = re.compile(r"^(\s*(?:[-*]\s+)?\*\*)(?!\[\[)([^*\n]+?)(\*\*\s*:)", re.MULTILINE)

ENTITY_SECTION = "Important Entities"
CONCEPT_SECTION = "Key Concepts & Theory"


def section_span(text: str, name: str) -> tuple[int, int] | None:
    """Return the (start, end) offsets of a section's body, or None."""
    m = re.search(rf"^##\s+{re.escape(name)}\s*$", text, re.MULTILINE)
    if not m:
        return None
    rest = text[m.end():]
    nxt = H2.search(rest)
    return m.end(), m.end() + (nxt.start() if nxt else len(rest))


def entity_names_for(page: Path) -> set[str]:
    """Authoritative display names from the paper's Stage A sidecar, if present."""
    sidecar = RAW_PAPERS / f"{page.stem}.summary.json"
    if not sidecar.exists():
        hits = list(RAW_PAPERS.rglob(f"{page.stem}.summary.json"))
        if not hits:
            return set()
        sidecar = hits[0]
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {
        str((e or {}).get("text", "")).strip()
        for e in (payload.get("entities") or [])
        if isinstance(e, dict) and str((e or {}).get("text", "")).strip()
    }


def repair(text: str, known: set[str]) -> tuple[str, int, int]:
    """Return (new_text, entity_links_added, concept_links_added)."""
    n_ent = n_con = 0

    span = section_span(text, ENTITY_SECTION)
    if span:
        start, end = span
        body = text[start:end]
        if not WIKILINK.search(body):
            # renderer._linkify_entity_bullets now handles both the
            # one-entity-per-bullet and inline "**Category**: a, b, c" layouts.
            fixed, n_ent = _linkify_entity_bullets(body, known)
            if n_ent:
                text = text[:start] + fixed + text[end:]

    span = section_span(text, CONCEPT_SECTION)
    if span:
        start, end = span
        body = text[start:end]
        if not WIKILINK.search(body):
            fixed, n_con = CONCEPT_BULLET.subn(r"\1[[\2]]\3", body)
            if n_con:
                text = text[:start] + fixed + text[end:]

    return text, n_ent, n_con


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Report only; write nothing.")
    mode.add_argument("--apply", action="store_true", help="Write repairs to disk.")
    ap.add_argument("--limit", type=int, default=0, help="Repair at most N pages.")
    args = ap.parse_args(argv)

    pages = sorted(WIKI_SOURCES.rglob("*.md"))
    if not pages:
        print(f"No source pages under {WIKI_SOURCES}")
        return 1

    backup_dir = None
    if args.apply:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = ROOT / ".backup" / f"entity_wikilink_backfill_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)

    changed = ent_total = con_total = sidecar_used = 0
    for page in pages:
        if args.limit and changed >= args.limit:
            break
        original = page.read_text(encoding="utf-8", errors="replace")
        known = entity_names_for(page)
        updated, n_ent, n_con = repair(original, known)
        if updated == original:
            continue
        changed += 1
        ent_total += n_ent
        con_total += n_con
        if known:
            sidecar_used += 1
        if args.apply:
            shutil.copy2(page, backup_dir / page.name)
            page.write_text(updated, encoding="utf-8")
        else:
            print(f"  would fix (+{n_ent} entity, +{n_con} concept) {page.name[:80]}")

    verb = "repaired" if args.apply else "would repair"
    print(f"\n  pages scanned            : {len(pages)}")
    print(f"  pages {verb:<18}: {changed}")
    print(f"  entity wikilinks added   : {ent_total}")
    print(f"  concept wikilinks added  : {con_total}")
    print(f"  pages cross-checked against a Stage A sidecar: {sidecar_used}")
    if backup_dir:
        print(f"  backups                  : {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
