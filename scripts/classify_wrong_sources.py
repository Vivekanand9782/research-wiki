"""Structural classifier for the 947 wrong-Sources-heading pages.

Builds a fingerprint for every affected file by extracting:
  - count and ordering of `**Sources**:` labels (top schema label)
  - count of `## Sources` headings (bug indicator) and where they appear
  - count of `### Sources` headings (could be matched by old buggy substring check)
  - count and location of `### Findings from [[...]]` blocks
  - count and location of `## Related pages` headings
  - presence of legitimate bullets under `## Related pages` (concept/entity wikilinks)
  - paper wikilinks under bottom `## Sources` block, deduped
  - any text under `## Sources` that ISN'T a bullet wikilink (data we'd lose if we naively delete)

Then groups every file into a bucket whose key is a tuple of structural facts.
Prints the bucket histogram and writes per-bucket sample paths to /tmp/.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Use absolute path relative to this script to ensure it works regardless of CWD
WIKI = Path(__file__).resolve().parent.parent / "wiki"
SOURCES_DIR = WIKI / "sources"

# Pre-compute the set of paper stems so we can label wikilink targets correctly.
SOURCE_STEMS: set[str] = {p.stem for p in SOURCES_DIR.rglob("*.md")} if SOURCES_DIR.exists() else set()

H2_RE = re.compile(r"^##\s+(.+?)\s*$")
H3_RE = re.compile(r"^###\s+(.+?)\s*$")
BULLET_LINK_RE = re.compile(
    r"^\s*[-*]\s*\[\[\s*([^\]|#]+?)\s*(?:#[^\]|]*)?(?:\|[^\]]*)?\s*\]\]\s*$"
)
SOURCES_LABEL_RE = re.compile(r"^\s*\*\*Sources\*\*\s*:\s*$")
FINDINGS_H3_RE = re.compile(r"^###\s+Findings\s+from\s+\[\[([^\]]+)\]\]", re.IGNORECASE)


def parse_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # Identify the index of every H2/H3 heading and the **Sources**: label.
    h2_indices: list[tuple[int, str]] = []  # (line_idx, heading_text)
    h3_indices: list[tuple[int, str]] = []
    sources_label_lines: list[int] = []
    for i, ln in enumerate(lines):
        m = H2_RE.match(ln)
        if m:
            h2_indices.append((i, m.group(1).strip()))
            continue
        m = H3_RE.match(ln)
        if m:
            h3_indices.append((i, m.group(1).strip()))
            continue
        if SOURCES_LABEL_RE.match(ln):
            sources_label_lines.append(i)

    h2_titles = [t for _, t in h2_indices]
    related_h2_idx = next((i for i, t in h2_indices if t.lower() == "related pages"), None)
    sources_h2_idx_list = [i for i, t in h2_indices if t.lower() == "sources"]
    findings_count = sum(1 for _, t in h3_indices if t.lower().startswith("findings from"))

    # Slice helper: take all lines that belong to a given heading until the next
    # H2 (or EOF). For our buggy structure this is fine; we don't try to model
    # nested H3 sections specially.
    def section_lines(heading_line_idx: int) -> list[str]:
        next_h2 = next(
            (j for j, _ in h2_indices if j > heading_line_idx),
            len(lines),
        )
        return lines[heading_line_idx + 1:next_h2]

    # Inspect ## Related pages content (excluding ### Findings sub-sections).
    related_legitimate_links: list[str] = []
    related_findings_under_it = 0
    if related_h2_idx is not None:
        block = section_lines(related_h2_idx)
        # Lines before the first ### Findings heading inside this block are
        # "legitimate" Related Pages content.
        first_finding = next(
            (k for k, ln in enumerate(block) if FINDINGS_H3_RE.match(ln)),
            None,
        )
        scan = block if first_finding is None else block[:first_finding]
        related_findings_under_it = sum(1 for ln in block if FINDINGS_H3_RE.match(ln))
        for ln in scan:
            m = BULLET_LINK_RE.match(ln)
            if m:
                target = m.group(1)
                # Only count NON-source links as legitimate Related-Page content.
                if target not in SOURCE_STEMS:
                    related_legitimate_links.append(target)

    # Inspect ## Sources block content.
    sources_h2_paper_links: list[str] = []
    sources_h2_other_lines: list[str] = []
    sources_h2_count = len(sources_h2_idx_list)
    for src_idx in sources_h2_idx_list:
        for ln in section_lines(src_idx):
            stripped = ln.strip()
            if not stripped:
                continue
            m = BULLET_LINK_RE.match(ln)
            if m:
                target = m.group(1)
                if target in SOURCE_STEMS:
                    sources_h2_paper_links.append(target)
                else:
                    # Non-source bullet under ## Sources — unusual.
                    sources_h2_other_lines.append(ln)
            else:
                sources_h2_other_lines.append(ln)

    # ### Sources (3-hash) — would be matched by the old buggy substring check.
    third_hash_sources = sum(1 for _, t in h3_indices if t.lower() == "sources")

    # Section ordering, condensed.
    section_order = []
    for i, t in h2_indices:
        section_order.append(t.lower())

    return {
        "path": str(path),
        "size": path.stat().st_size,
        "h2_titles": h2_titles,
        "h2_section_order": section_order,
        "n_sources_label": len(sources_label_lines),
        "n_sources_h2": sources_h2_count,
        "n_third_hash_sources": third_hash_sources,
        "n_related_pages_h2": 1 if related_h2_idx is not None else 0,
        "n_findings_h3_total": findings_count,
        "n_findings_under_related": related_findings_under_it,
        "related_legitimate_links": related_legitimate_links,
        "sources_h2_paper_links": sources_h2_paper_links,
        "sources_h2_paper_links_dedup": sorted(set(sources_h2_paper_links)),
        "sources_h2_paper_links_duplicate_count": len(sources_h2_paper_links) - len(set(sources_h2_paper_links)),
        "sources_h2_other_lines": sources_h2_other_lines,
    }


def bucket_key(info: dict) -> str:
    """Coarse bucket label that captures structural shape."""
    parts = [
        f"label={info['n_sources_label']}",
        f"h2sources={info['n_sources_h2']}",
        f"h2related={info['n_related_pages_h2']}",
        f"findings_under_rel={'yes' if info['n_findings_under_related'] > 0 else 'no'}",
        f"legit_rel_links={'yes' if info['related_legitimate_links'] else 'no'}",
        f"sources_other={'yes' if info['sources_h2_other_lines'] else 'no'}",
        f"third_hash={'yes' if info['n_third_hash_sources'] > 0 else 'no'}",
    ]
    # Section ordering matters: did the buggy code put ## Sources after
    # ## Related pages (expected) or in a weird order?
    order = info["h2_section_order"]
    try:
        rel_idx = order.index("related pages")
    except ValueError:
        rel_idx = -1
    try:
        src_idx = order.index("sources")
    except ValueError:
        src_idx = -1
    if rel_idx == -1 or src_idx == -1:
        order_label = "n/a"
    elif rel_idx < src_idx:
        order_label = "rel<src"
    else:
        order_label = "src<rel"
    parts.append(f"order={order_label}")
    return " | ".join(parts)


def main() -> int:
    paths_file = Path("/tmp/wrong_sources_files.txt")
    if not paths_file.exists():
        print("ERROR: /tmp/wrong_sources_files.txt not found.", file=sys.stderr)
        return 1
    paths = [Path(p) for p in paths_file.read_text().splitlines() if p.strip()]
    print(f"Classifying {len(paths)} files…")

    infos = []
    parse_errors: list[tuple[Path, str]] = []
    for p in paths:
        try:
            infos.append(parse_file(p))
        except Exception as e:
            parse_errors.append((p, repr(e)))

    if parse_errors:
        print(f"\n{len(parse_errors)} parse failures (showing first 5):")
        for p, e in parse_errors[:5]:
            print(f"  {p} : {e}")

    bucket_counter: Counter[str] = Counter()
    bucket_samples: dict[str, list[str]] = defaultdict(list)
    for info in infos:
        b = bucket_key(info)
        bucket_counter[b] += 1
        if len(bucket_samples[b]) < 3:
            bucket_samples[b].append(info["path"])

    print(f"\n=== Buckets (total {len(infos)} files in {len(bucket_counter)} buckets) ===\n")
    for b, n in bucket_counter.most_common():
        print(f"[{n:4d}]  {b}")
        for s in bucket_samples[b]:
            print(f"        {s}")

    # Cross-cutting stats.
    print("\n=== Cross-cutting stats ===")
    n_with_other_lines = sum(1 for i in infos if i["sources_h2_other_lines"])
    print(f"Pages with NON-bullet content under ## Sources: {n_with_other_lines}")
    if n_with_other_lines:
        for i in infos:
            if i["sources_h2_other_lines"]:
                print(f"  {i['path']}")
                for ln in i["sources_h2_other_lines"][:3]:
                    print(f"    > {ln!r}")
                if len(i["sources_h2_other_lines"]) > 3:
                    print(f"    > … {len(i['sources_h2_other_lines'])-3} more")
                if sum(1 for j in infos if j["sources_h2_other_lines"]) > 8 and \
                        infos.index(i) > 8:
                    print("  (truncated)")
                    break

    n_third_hash = sum(1 for i in infos if i["n_third_hash_sources"] > 0)
    print(f"\nPages also containing `### Sources` (3-hash) heading: {n_third_hash}")
    if n_third_hash:
        for i in infos:
            if i["n_third_hash_sources"] > 0:
                print(f"  {i['path']}")
                if sum(1 for j in infos if j["n_third_hash_sources"] > 0) > 8 and \
                        infos.index(i) > 8:
                    print("  (truncated)")
                    break

    n_dup_paper_links = sum(1 for i in infos if i["sources_h2_paper_links_duplicate_count"])
    print(f"\nPages with duplicate paper links inside ## Sources block: {n_dup_paper_links}")

    n_label_missing = sum(1 for i in infos if i["n_sources_label"] == 0)
    print(f"\nPages MISSING the top **Sources**: label entirely: {n_label_missing}")

    n_multi_h2_sources = sum(1 for i in infos if i["n_sources_h2"] > 1)
    print(f"\nPages with MORE THAN ONE ## Sources heading: {n_multi_h2_sources}")
    if n_multi_h2_sources:
        for i in infos:
            if i["n_sources_h2"] > 1:
                print(f"  {i['path']} (count={i['n_sources_h2']})")

    # Save full per-file info for downstream use.
    out_path = Path("/tmp/structural_classification.json")
    out_path.write_text(json.dumps(infos, indent=2))
    print(f"\nFull per-file classification → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
