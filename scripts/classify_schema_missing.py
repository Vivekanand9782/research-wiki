"""Classify the 136 schema-missing pages so we can decide per-bucket what to
do (exempt, upgrade, delete). Read-only — emits a JSON classification and
prints summary buckets + sample paths.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lint_wiki import validate_page, extract_frontmatter  # noqa: E402

WIKI = ROOT / "wiki"
SOURCES_DIR = WIKI / "sources"
SPECIAL = {WIKI / "index.md", WIKI / "log.md"}
WIKILINK_RE = re.compile(r"\[\[(.*?)\]\]")
H_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def classify(p: Path) -> dict:
    text = p.read_text(encoding="utf-8", errors="replace")
    rel = p.relative_to(WIKI).as_posix()
    fm = extract_frontmatter(text)
    has_fm = fm is not None
    fm_keys: list[str] = []
    if has_fm:
        for line in fm.splitlines():
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line)
            if m:
                fm_keys.append(m.group(1))

    lines = text.splitlines()
    headings: list[tuple[int, str]] = []
    for ln in lines:
        m = H_RE.match(ln)
        if m:
            headings.append((len(m.group(1)), m.group(2).strip()))

    wikilinks = WIKILINK_RE.findall(text)
    body_no_fm = re.sub(r"^---.*?\n---\n", "", text, count=1, flags=re.DOTALL)

    return {
        "path": rel,
        "size": p.stat().st_size,
        "category": rel.split("/", 1)[0] if "/" in rel else "(root)",
        "has_frontmatter": has_fm,
        "frontmatter_keys": fm_keys,
        "first_h1": next((t for lvl, t in headings if lvl == 1), None),
        "n_headings_total": len(headings),
        "h2_titles": [t for lvl, t in headings if lvl == 2],
        "n_wikilinks": len(wikilinks),
        "first_wikilinks": wikilinks[:5],
        "body_chars": len(body_no_fm.strip()),
        "validate_errors": validate_page(text),
    }


def main() -> int:
    candidates = []
    for f in WIKI.rglob("*.md"):
        if f in SPECIAL:
            continue
        try:
            f.relative_to(SOURCES_DIR)
            continue
        except ValueError:
            pass
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if validate_page(text):
            candidates.append(f)

    print(f"Files with format errors: {len(candidates)}")
    infos = [classify(p) for p in candidates]

    # Bucket primarily by category, secondarily by content shape.
    by_cat = Counter(i["category"] for i in infos)
    print("\n=== By category ===")
    for cat, n in by_cat.most_common():
        print(f"  {n:4d}  {cat}")

    print("\n=== By body size ===")
    sizes = [i["body_chars"] for i in infos]
    sizes.sort()
    if sizes:
        n = len(sizes)
        print(f"  min={sizes[0]}, p25={sizes[n//4]}, median={sizes[n//2]}, "
              f"p75={sizes[3*n//4]}, max={sizes[-1]}")

    print("\n=== Frontmatter status ===")
    fm_yes = sum(1 for i in infos if i["has_frontmatter"])
    print(f"  has frontmatter   : {fm_yes}")
    print(f"  no frontmatter    : {len(infos) - fm_yes}")

    print("\n=== Body content presence ===")
    no_body = sum(1 for i in infos if i["body_chars"] == 0)
    has_body = len(infos) - no_body
    print(f"  empty body        : {no_body}")
    print(f"  has body content  : {has_body}")

    print("\n=== Headings shape ===")
    no_h1 = sum(1 for i in infos if i["first_h1"] is None)
    print(f"  pages without H1 title : {no_h1}")
    h2_counter = Counter()
    for i in infos:
        for t in i["h2_titles"]:
            h2_counter[t] += 1
    if h2_counter:
        print(f"  most common H2 headings (top 10):")
        for t, n in h2_counter.most_common(10):
            print(f"    {n:4d}  ## {t}")

    # Bucket: (category, has_frontmatter, has_body, has_h1)
    buckets: dict[tuple, list[str]] = defaultdict(list)
    for i in infos:
        key = (
            i["category"],
            "fm" if i["has_frontmatter"] else "no-fm",
            "body" if i["body_chars"] > 0 else "empty",
            "h1" if i["first_h1"] else "no-h1",
        )
        buckets[key].append(i["path"])

    print("\n=== Final buckets (category, fm, body, h1) ===")
    for key in sorted(buckets, key=lambda k: -len(buckets[k])):
        members = buckets[key]
        print(f"  [{len(members):4d}]  {key}")
        for s in members[:3]:
            print(f"          {s}")

    out = ROOT / ".backup" / "baselines" / "schema_missing_classification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(infos, indent=2))
    print(f"\nFull per-file classification → {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
