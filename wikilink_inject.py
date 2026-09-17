"""Inject [[wikilink]] citation references into wiki source files.

Reads the citation graph (citation_network.json), maps paper stems to
actual wiki/sources/*.md file paths, then annotates each paper with the
list of papers it cites and/or is cited by.  Idempotent, backs up files
before writing, and writes a JSON report.

Usage (from research-wiki/):
    python3 wikilink_inject.py
    python3 wikilink_inject.py --dry-run          # only show what would happen
    python3 wikilink_inject.py --limit 50           # process at most N files
"""
from __future__ import annotations

import argparse, json, os, re, shutil, sys, time
from datetime import datetime, timezone
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────
ROOT   = Path(os.environ.get("ANTIGRAVITY_ROOT", Path.home() / "Desktop" / "antigravity")).resolve()
WIKI   = ROOT / "research-wiki" / "wiki"
GRAPH  = WIKI / "citation_network.json"
BACKUP = ROOT / "research-wiki" / ".backup"

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:[#|][^\]]*)?\]\]")


# ── helpers ────────────────────────────────────────────────────────────
def _build_source_map() -> dict[str, Path]:
    """Map stem (filename without extension, stripped) → absolute path."""
    mapping: dict[str, Path] = {}
    sources = WIKI / "sources"
    if not sources.exists():
        print(f"[warn] {sources} does not exist")
        return mapping
    count = 0
    for md in sources.rglob("*.md"):
        stem = md.stem.strip()
        if not stem:
            continue
        # If two files share the same stem, prefer shallower path
        if stem not in mapping or len(md.parts) < len(mapping[stem].parts):
            mapping[stem] = md
        count += 1
    print(f"[src_map] scanned {count} .md files → {len(mapping)} unique stems")
    return mapping


def _existing_wikilinks(path: Path) -> set[str]:
    """Return the set of wikilink targets already present in a file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return set()
    return set(_WIKILINK_RE.findall(text))


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)


def _inject_wikilinks(path: Path, new_links: list[str]) -> None:
    """Append a citation block to *path*, backing up first."""
    BACKUP.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = BACKUP / f"{path.stem}_{ts}.bak"
    shutil.copy2(path, bak)

    text = path.read_text(encoding="utf-8", errors="replace")

    # Build the block
    block_lines = ["\n", "## Citation links"]
    for lnk in sorted(new_links):
        block_lines.append(f"[[{lnk}]]")
    block_lines.append("")  # trailing newline

    # Try to insert before the last heading-level content or just append
    text = text.rstrip() + "\n" + "\n".join(block_lines) + "\n"
    path.write_text(text, encoding="utf-8")


# ── main ───────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Inject citation wikilinks")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args(argv)

    if not GRAPH.exists():
        print(f"[err] graph not found: {GRAPH}")
        return 1

    graph = json.loads(GRAPH.read_text())
    papers = graph.get("papers", {})
    src_map = _build_source_map()

    total_checked = 0
    total_modified = 0
    total_injected = 0
    report: list[dict] = []
    start = time.time()

    for stem, data in papers.items():
        if args.limit and total_checked >= args.limit:
            break

        target_path = src_map.get(stem.strip())
        if target_path is None:
            # Some stems have leading spaces; try stripped version
            target_path = src_map.get(stem)
        if target_path is None:
            continue

        total_checked += 1
        existing = _existing_wikilinks(target_path)

        candidates: list[str] = []
        for edge in data.get("cites", []):
            t = edge["target"].strip()
            if t and t in src_map and t not in existing:
                candidates.append(t)
        for edge in data.get("cited_by", []):
            s = edge["source"].strip()
            if s and s in src_map and s not in existing:
                candidates.append(s)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique = [c for c in candidates if not (c in seen or seen.add(c))]

        if not unique:
            continue

        total_modified += 1
        total_injected += len(unique)
        report.append({
            "path": str(target_path),
            "stem": stem.strip(),
            "count": len(unique),
            "wikilinks": unique,
        })

        if args.dry_run:
            print(f"[dry-run] would add {len(unique)} links to {target_path.name}")
            continue

        _inject_wikilinks(target_path, unique)
        elapsed = time.time() - start
        if total_modified % 100 == 0:
            print(f"[progress] {total_modified} files modified, {int(elapsed)}s elapsed")

    # Write report
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_papers_in_graph": len(papers),
        "total_files_checked": total_checked,
        "total_files_modified": total_modified,
        "total_wikilinks_injected": total_injected,
        "details": report,
    }
    report_path = BACKUP / "injection_report.json"
    report_path.write_text(json.dumps(report_data, indent=2, default=str))

    elapsed = time.time() - start
    print(f"\n══ Injection complete ══")
    print(f"  Papers in graph : {len(papers)}")
    print(f"  Files checked   : {total_checked}")
    print(f"  Files modified  : {total_modified}")
    print(f"  Wikilinks added : {total_injected}")
    print(f"  Time            : {elapsed:.1f}s")
    print(f"  Report          : {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
