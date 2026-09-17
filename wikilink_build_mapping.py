#!/usr/bin/env python3
"""Build stem-to-filepath mapping for the Antigravity research-wiki corpus."""

import json
import os
import sys
from pathlib import Path

# ── config ──────────────────────────────────────────────────────────────

BASE = Path(os.environ.get("ANTIGRAVITY_WIKI", str(Path.home().absolute() / "Desktop/antigravity/research-wiki")))

CITATION_GRAPH = BASE / "wiki" / "citation_network.json"

SCAN_DIRS = [
    BASE / "wiki" / "sources",
    BASE / "raw" / "papers",
    BASE / "entities",
    BASE / "concepts",
    BASE / "synthesis",
]

OUTPUT_MAP = BASE / "wiki" / "source_stem_map.json"
OUTPUT_UNRESOLVED = BASE / "wiki" / "unresolved_citations.json"

# Directories to skip during recursive scans (noise)
SKIP_DIR_NAMES = {".ds_store"}


# ── helpers ─────────────────────────────────────────────────────────────

def extract_stem_noext(filename: str) -> str:
    """Return filename without extension.

    Filenames are already in stem form (e.g. ``Zhang_2014_cloning_seed_dormancy.md``).
    We just strip the extension; no further transformation here since the
    caller will normalize case for comparison.
    """
    stem, _ = os.path.splitext(filename)
    return stem.strip()


def scan_for_md_files(base_dir: Path) -> list[tuple[str, str, str]]:
    """Recursively find every .md file under *base_dir*.

    Returns list of (stem, absolute_path_str, relative_dir) tuples.
    Skips dirs whose name is in SKIP_DIR_NAMES.
    """
    results: list[tuple[str, str, str]] = []
    if not base_dir.is_dir():
        return results

    for root, dirs, filenames in os.walk(str(base_dir)):
        # Prune noise directories in-place so os.walk doesn't recurse into them
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIR_NAMES]

        for fn in filenames:
            if not fn.lower().endswith(".md"):
                continue

            abs_path = os.path.join(root, fn)
            rel_dir = os.path.relpath(root, str(base_dir))
            stem = extract_stem_noext(fn)
            results.append((stem, abs_path, rel_dir))

    return results


# ── main logic ──────────────────────────────────────────────────────────

def main() -> None:
    # ── Step 1: build lookup map ────────────────────────────────────────

    # key = lowercase stem → [{stem, path, dir}]
    map_raw: dict[str, list[dict]] = {}
    total_files_scanned = 0

    for scan_dir in SCAN_DIRS:
        entries = scan_for_md_files(scan_dir)
        if not entries:
            continue
        for stem, filepath, rel_dir in entries:
            lookup_key = stem.lower()
            entry = {"stem": stem, "path": filepath, "dir": rel_dir}
            map_raw.setdefault(lookup_key, []).append(entry)
            total_files_scanned += 1

    # Deduplicate within each key: keep only distinct paths
    map_deduped: dict[str, list[dict]] = {}
    for key, entries in map_raw.items():
        seen_paths: set[str] = set()
        unique = []
        for e in entries:
            if e["path"] not in seen_paths:
                seen_paths.add(e["path"])
                unique.append(e)
        if unique:
            map_deduped[key] = unique

    # Sort by count descending (most-ambiguous keys first)
    sorted_map = sorted(map_deduped.items(), key=lambda kv: -len(kv[1]))

    OUTPUT_MAP.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MAP, "w") as f:
        json.dump(dict(sorted_map), f, indent=2, ensure_ascii=False)
    print(f"[ok] Wrote {OUTPUT_MAP}")

    # ── Step 2: load citation graph & compute resolutions ───────────────

    if not CITATION_GRAPH.exists():
        print(f"[warn] Citation graph not found at {CITATION_GRAPH}", file=sys.stderr)
        # Produce empty outputs and exit
        json.dump({}, open(OUTPUT_UNRESOLVED, "w"), indent=2, ensure_ascii=False)
        print("[done]")
        return

    with open(CITATION_GRAPH) as f:
        graph = json.load(f)

    # Locate the papers dict inside the graph
    papers: dict | None = None
    for val in graph.values():
        if isinstance(val, dict) and len(val) > 0:
            first = next(iter(val.values()), None)
            if isinstance(first, dict):
                papers = val
                break
            elif isinstance(first, str):
                papers = val
                break

    if papers is None:
        print("[warn] Could not find papers dict in citation graph", file=sys.stderr)
        json.dump({}, open(OUTPUT_UNRESOLVED, "w"), indent=2, ensure_ascii=False)
        print("[done]")
        return

    # Collect ALL distinct citation target stems from cites + cited_by
    citation_targets: set[str] = set()
    for paper_id, info in papers.items():
        if isinstance(info, str):
            # Some graphs store the ID directly; still treat it as a target candidate
            citation_targets.add(paper_id.strip())
            continue
        if not isinstance(info, dict):
            continue
        for ref_key in ("cites", "cited_by"):
            refs = info.get(ref_key, [])
            if isinstance(refs, list):
                for ref in refs:
                    if isinstance(ref, str):
                        citation_targets.add(ref.strip())
                    elif isinstance(ref, dict) and "target" in ref:
                        citation_targets.add(str(ref["target"]).strip())

    # Determine which are resolved, ambiguous, or unresolved
    resolved_unique: list[str] = []
    resolved_ambiguous: list[str] = []
    unresolved: list[str] = []

    ambiguous_examples: dict[str, list[list[str]]] = {}

    for target in sorted(citation_targets):
        key = target.lower()
        matches = map_deduped.get(key, [])
        if len(matches) == 0:
            unresolved.append(target)
        elif len(matches) == 1:
            resolved_unique.append(target)
        else:
            resolved_ambiguous.append(target)
            ambiguous_examples[target] = [m["stem"] for m in matches]

    # ── Step 3: write unresolved citations report ───────────────────────

    unresolved_report = {
        "total_citation_targets": len(citation_targets),
        "resolved_unique": len(resolved_unique),
        "resolved_ambiguous": len(resolved_ambiguous),
        "unresolved": len(unresolved),
        "unresolved_stems": unresolved[:50],  # top-50 examples
        "all_unresolved_count": len(unresolved),
    }

    OUTPUT_UNRESOLVED.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_UNRESOLVED, "w") as f:
        json.dump(unresolved_report, f, indent=2, ensure_ascii=False)
    print(f"[ok] Wrote {OUTPUT_UNRESOLVED}")

    # ── Step 4: print statistics ────────────────────────────────────────

    total_matches = sum(len(v) for v in map_deduped.values())

    print()
    print("=" * 60)
    print("  STEM-TO-PATH MAPPING  –  STATISTICS")
    print("=" * 60)
    print(f"  Total .md files scanned:     {total_files_scanned}")
    print(f"  Unique stems in files:       {len(map_deduped)}")
    print(f"  Total unique citation targets:{len(citation_targets)}")
    print()
    print(f"  Resolved uniquely (1 match):  {len(resolved_unique)}")
    print(f"  Resolved ambiguously (>1):    {len(resolved_ambiguous)}")
    print(f"  Unresolved (0 matches):       {len(unresolved)}")
    print()

    if resolved_ambiguous:
        print("--- Ambiguous cases (first 10) ---")
        count = 0
        for stem in sorted(resolved_ambiguous)[:10]:
            matches = ambiguous_examples[stem]
            print(f"  \"{stem}\"")
            print(f"    matches ({len(matches)}):")
            for m in matches[:5]:
                # Show short version
                print(f"      – {m[:90]}...")
            count += 1
        if len(resolved_ambiguous) > 10:
            print(f"  ... and {len(resolved_ambiguous) - 10} more")
        print()

    if unresolved:
        print("--- Unresolved citations (first 20) ---")
        for u in unresolved[:20]:
            print(f"  – {u}")
        if len(unresolved) > 20:
            print(f"  ... and {len(unresolved) - 20} more")
        print()

    # Check whether any files were skipped because their scan dir didn't exist
    missed_dirs = [str(d) for d in SCAN_DIRS if not d.is_dir()]
    if missed_dirs:
        print(f"  NOTE: The following expected directories do not exist and were skipped:")
        for md in missed_dirs:
            print(f"    - {md}")
        print()

    # Any duplicate warnings?
    multi_match_keys = {k: v for k, v in map_deduped.items() if len(v) > 1}
    if multi_match_keys:
        print(f"  NOTE: {sum(len(v)-1 for v in multi_match_keys.values())} extra duplicate file entries"
              f" across {len(multi_match_keys)} stems have been collapsed to unique paths.")
        print()

    print("=" * 60)


if __name__ == "__main__":
    main()
