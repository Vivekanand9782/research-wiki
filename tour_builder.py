"""tour_builder.py — generate guided reading lists ("tours") from the wiki graph.

Inspired by Understand-Anything's ``tour-builder`` agent. For each high-degree
concept or entity, walks the wiki graph and emits an ordered list of source
papers to read, sorted by publication year (foundational → recent).

Inputs (in order of preference):
  1. ``wiki/.understand-anything/intermediate/scan-manifest.json``
     (the UA deterministic scan; produced by ``parse-knowledge-base.py``)
  2. Falls back to scanning ``wiki/`` directly if the manifest is missing.

Outputs:
  ``wiki/synthesis/tours/<concept-slug>.md``  — one tour per selected anchor.
  ``wiki/synthesis/tours/index.md``          — table of contents.

Usage::

    python3 tour_builder.py                       # build tours for top-N anchors
    python3 tour_builder.py --top 30              # change anchor budget
    python3 tour_builder.py --min-papers 5        # only build tours backed by ≥5 sources
    python3 tour_builder.py --dry-run             # list anchors but don't write
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

WIKI = Path(__file__).resolve().parent / "wiki"
MANIFEST = WIKI / ".understand-anything" / "intermediate" / "scan-manifest.json"
TOURS_DIR = WIKI / "synthesis" / "tours"
TOC_PATH = TOURS_DIR / "index.md"
WIKILINK_RE = re.compile(r"\[\[(.*?)\]\]")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "tour"


def _read_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    try:
        data = yaml.safe_load(text[3:end]) or {}
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _extract_year(fm: dict, filename: str) -> int | None:
    """Pull a year from frontmatter; fall back to ``Author_YYYY_`` filename pattern."""
    raw = fm.get("year")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        m = YEAR_RE.search(raw)
        if m:
            return int(m.group(0))
    m = YEAR_RE.search(filename)
    return int(m.group(0)) if m else None


def load_graph() -> tuple[dict[str, dict], list[tuple[str, str]]]:
    """Return (nodes_by_filepath, edges_as_pairs).

    Each node dict carries ``filePath``, ``name``, ``type`` (concept/entity/source/synthesis),
    ``year``, ``tags``, ``backlinks_count``.
    """
    nodes: dict[str, dict] = {}
    edges: list[tuple[str, str]] = []  # (source_filePath, target_filePath_or_name)

    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text())
        # Index articles
        for n in manifest.get("nodes", []):
            fp = n.get("filePath", "")
            if not fp:
                continue
            full = WIKI / fp
            fm = _read_frontmatter(full.read_text(encoding="utf-8", errors="replace")) if full.exists() else {}
            kind = "concept" if fp.startswith("concepts/") else \
                   "entity"  if fp.startswith("entities/") else \
                   "source"  if fp.startswith("sources/")  else \
                   "synthesis" if fp.startswith("synthesis/") else "other"
            nodes[fp] = {
                "filePath": fp,
                "name": n.get("name", Path(fp).stem),
                "type": kind,
                "year": _extract_year(fm, Path(fp).stem),
                "tags": fm.get("tags") or [],
                "wikilinks": n.get("knowledgeMeta", {}).get("wikilinks", []),
            }
        # Edges from related links (already resolved by UA when possible).
        # Edge targets carry the path without .md, so we map back to filePath keys.
        for e in manifest.get("edges", []):
            src = e.get("source", "")
            tgt = e.get("target", "")
            if src.startswith("article:") and tgt.startswith("article:"):
                src_fp = src[len("article:"):] + ".md"
                tgt_fp = tgt[len("article:"):] + ".md"
                edges.append((src_fp, tgt_fp))
        return nodes, edges

    # Fallback: walk wiki/ directly
    for f in WIKI.rglob("*.md"):
        if f.name in {"index.md", "log.md"}:
            continue
        rel = f.relative_to(WIKI).as_posix()
        text = f.read_text(encoding="utf-8", errors="replace")
        fm = _read_frontmatter(text)
        kind = "concept" if rel.startswith("concepts/") else \
               "entity"  if rel.startswith("entities/") else \
               "source"  if rel.startswith("sources/")  else \
               "synthesis" if rel.startswith("synthesis/") else "other"
        nodes[rel] = {
            "filePath": rel, "name": f.stem, "type": kind,
            "year": _extract_year(fm, f.stem),
            "tags": fm.get("tags") or [],
            "wikilinks": WIKILINK_RE.findall(text),
        }
    # Build a name → filePath lookup for fallback edge resolution
    name_to_fp = {Path(fp).stem: fp for fp in nodes}
    for fp, n in nodes.items():
        for link in n["wikilinks"]:
            target = link.split("|")[0].split("#")[0].strip()
            tgt_fp = name_to_fp.get(target)
            if tgt_fp:
                edges.append((fp, tgt_fp))
    return nodes, edges


def select_anchors(nodes: dict, edges: list, top: int, min_papers: int) -> list[tuple[str, dict, list[str]]]:
    """Pick concept/entity anchors with the most connected source pages.

    In this wiki, concept/entity pages list their evidence via outbound
    wikilinks ([[source-paper]]), so we look at *outbound* edges from each
    concept/entity and collect targets that resolve to source pages.

    Returns a list of (anchor_filePath, anchor_node, [source_filePaths]) tuples,
    sorted by source count descending.
    """
    outbound: dict[str, set[str]] = defaultdict(set)
    for src, tgt in edges:
        outbound[src].add(tgt)

    candidates: list[tuple[str, dict, list[str]]] = []
    for fp, n in nodes.items():
        if n["type"] not in {"concept", "entity"}:
            continue
        sources = [t for t in outbound.get(fp, set()) if nodes.get(t, {}).get("type") == "source"]
        if len(sources) < min_papers:
            continue
        candidates.append((fp, n, sources))

    candidates.sort(key=lambda x: -len(x[2]))
    return candidates[:top]


def build_tour(anchor_fp: str, anchor: dict, source_fps: list[str], nodes: dict) -> str:
    """Render an ordered Markdown reading list for one anchor."""
    items = []
    for sfp in source_fps:
        s = nodes.get(sfp)
        if not s:
            continue
        items.append({
            "filePath": sfp,
            "name": s["name"],
            "year": s["year"] or 9999,  # unknown years go last
            "stem": Path(sfp).stem,
        })
    # Order: by year ascending, then by name
    items.sort(key=lambda x: (x["year"], x["name"].lower()))
    today = datetime.date.today().isoformat()

    lines = [
        "---",
        "tags: [synthesis, tour, auto-generated]",
        "type: synthesis",
        f"date_created: {today}",
        f"date_updated: {today}",
        f"source_count: {len(items)}",
        "---",
        "",
        f"# Reading tour: {anchor['name']}",
        "",
        f"**Summary**: Auto-generated dependency-ordered reading list for "
        f"`[[{Path(anchor_fp).stem}]]`. Papers sorted by year (foundational → recent).",
        "",
        f"**Sources**: derived from {len(items)} source pages linking to this anchor.",
        "",
        f"**Last updated**: {today}",
        "",
        "---",
        "",
        "## Reading order",
        "",
    ]
    for i, item in enumerate(items, 1):
        year_str = str(item["year"]) if item["year"] != 9999 else "n.d."
        lines.append(f"{i}. **{year_str}** — [[{item['stem']}]] — {item['name']}")
    lines += [
        "",
        "## Related pages",
        "",
        f"- [[{Path(anchor_fp).stem}]]",
        "",
        "_Generated by `tour_builder.py`. Edits below this line are preserved on regeneration if you "
        "rename the file (the script never overwrites a tour whose first line is not the auto header)._",
    ]
    return "\n".join(lines) + "\n"


AUTO_MARKER = "tags: [synthesis, tour, auto-generated]"


def write_tours(anchors, nodes, dry_run: bool) -> tuple[int, int]:
    """Returns (written, skipped_manual)."""
    if not dry_run:
        TOURS_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    today_iso = datetime.date.today().isoformat()
    toc_frontmatter = (
        "---\n"
        "tags: [synthesis, tour, auto-generated]\n"
        "type: synthesis\n"
        f"date_created: {today_iso}\n"
        f"date_updated: {today_iso}\n"
        "---\n"
        "\n"
    )
    toc = ["# Tours\n", "_Auto-generated reading lists; one per anchor concept/entity._\n",
           "| Tour | Anchor | Sources |", "|---|---|---:|"]
    for anchor_fp, anchor, source_fps in anchors:
        slug = _slugify(anchor["name"])
        out = TOURS_DIR / f"{slug}.md"
        if out.exists():
            existing = out.read_text(encoding="utf-8", errors="replace")
            if AUTO_MARKER not in existing[:300]:
                skipped += 1
                print(f"  · skipping (manual edits) {out.relative_to(WIKI)}")
                continue
        if dry_run:
            print(f"  → would write {out.relative_to(WIKI)}  ({len(source_fps)} sources)")
        else:
            out.write_text(build_tour(anchor_fp, anchor, source_fps, nodes), encoding="utf-8")
        written += 1
        toc.append(f"| [[tours/{slug}]] | `{anchor_fp}` | {len(source_fps)} |")
    if not dry_run:
        TOC_PATH.write_text(toc_frontmatter + "\n".join(toc) + "\n", encoding="utf-8")
    return written, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=20,
                        help="Build tours for the top-N most-connected anchors (default 20)")
    parser.add_argument("--min-papers", type=int, default=3,
                        help="Skip anchors with fewer than this many connected source pages (default 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be written without modifying files")
    args = parser.parse_args(argv)

    if not WIKI.exists():
        print(f"ERROR: wiki directory not found: {WIKI}", file=sys.stderr)
        return 2

    print(f"Loading graph (manifest={MANIFEST.exists()})…")
    nodes, edges = load_graph()
    print(f"  {len(nodes)} nodes, {len(edges)} edges")

    anchors = select_anchors(nodes, edges, args.top, args.min_papers)
    print(f"\nSelected {len(anchors)} anchors:")
    for anchor_fp, anchor, source_fps in anchors[:10]:
        print(f"  · {len(source_fps):>3} sources  {anchor_fp}")
    if len(anchors) > 10:
        print(f"  …and {len(anchors) - 10} more")
    if not anchors:
        print("\nNo anchors met the threshold. Try lowering --min-papers.")
        return 1

    written, skipped = write_tours(anchors, nodes, args.dry_run)
    verb = "Would write" if args.dry_run else "Wrote"
    print(f"\n✓ {verb} {written} tour(s); skipped {skipped} (manual edits preserved)")
    if not args.dry_run:
        print(f"✓ TOC: {TOC_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
