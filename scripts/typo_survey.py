"""Step (c) — survey typo candidates.

Re-derives the broken-targets list, fuzzy-matches each against existing
pages, and groups by score band. Prints the distribution and writes a JSON
file with all candidate (target, suggestion, score) tuples for downstream
auto-fix and review steps.

Read-only.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lint_wiki import extract_aliases  # noqa: E402

WIKI = ROOT / "wiki"
SPECIAL = {WIKI / "index.md", WIKI / "log.md"}
WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")


def _slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()


def collect_pages() -> tuple[set[str], set[str]]:
    all_names: set[str] = set()
    normalized: set[str] = set()
    for f in WIKI.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = f.relative_to(WIKI).with_suffix("").as_posix()
        all_names.add(f.stem)
        all_names.add(rel)
        normalized.add(_slugify(f.stem))
        normalized.add(_slugify(rel))
        for a in extract_aliases(text):
            all_names.add(a)
            normalized.add(_slugify(a))
    return all_names, normalized


def collect_targets() -> tuple[Counter[str], dict[str, set[Path]]]:
    total: Counter[str] = Counter()
    pages: dict[str, set[Path]] = defaultdict(set)
    for f in WIKI.rglob("*.md"):
        if f in SPECIAL:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for raw in WIKILINK_RE.findall(text):
            target = raw.split("|", 1)[0].split("#", 1)[0].strip()
            if not target:
                continue
            total[target] += 1
            pages[target].add(f)
    return total, pages


def main() -> int:
    print("Indexing pages…")
    all_names, normalized = collect_pages()
    print(f"  {len(all_names):,} known names, {len(normalized):,} normalized")

    print("Scanning targets…")
    total, pages = collect_targets()
    truly_broken = [
        t for t in total
        if t not in all_names and _slugify(t) not in normalized
    ]
    print(f"  {len(truly_broken):,} truly broken")

    name_list = sorted(all_names)
    candidates: list[dict] = []
    for t in truly_broken:
        target_lower = t.lower()
        best: tuple[str, float] | None = None
        for name in name_list:
            if abs(len(name) - len(t)) > 3:
                continue
            r = difflib.SequenceMatcher(None, target_lower, name.lower()).ratio()
            if best is None or r > best[1]:
                best = (name, r)
        if best and best[1] >= 0.85:
            candidates.append({
                "target": t,
                "suggestion": best[0],
                "score": round(best[1], 3),
                "n_pages": len(pages[t]),
                "n_mentions": total[t],
                "first_pages": [p.relative_to(WIKI).as_posix() for p in list(pages[t])[:5]],
                # Slugify each side and compare — if they're slug-equal,
                # this is a pure case/spacing issue (Obsidian resolves it
                # automatically; including it would just be noise).
                "slug_equal": _slugify(t) == _slugify(best[0]),
            })

    # Filter out slug-equal candidates (Obsidian-equivalent already).
    real_candidates = [c for c in candidates if not c["slug_equal"]]

    # Score-band histogram.
    bands = Counter()
    for c in real_candidates:
        s = c["score"]
        if s >= 0.95:
            bands["≥0.95 (auto-fix safe)"] += 1
        elif s >= 0.90:
            bands["0.90 – 0.95 (review)"] += 1
        else:
            bands["0.85 – 0.90 (review, weak)"] += 1

    print(f"\nTypo candidates after dropping slug-equal duplicates: "
          f"{len(real_candidates)} (of {len(candidates)} total)")
    for k, v in bands.most_common():
        print(f"  {k}: {v}")

    # Examples per band.
    print("\n=== Score ≥ 0.95 (top 15 by mentions) ===")
    high = sorted([c for c in real_candidates if c["score"] >= 0.95],
                  key=lambda c: (-c["n_mentions"], c["target"]))
    for c in high[:15]:
        print(f"  [[{c['target']}]] → [[{c['suggestion']}]]  "
              f"score={c['score']}  ({c['n_mentions']}m / {c['n_pages']}p)")

    print("\n=== Score 0.90 – 0.95 (top 10) ===")
    mid = sorted([c for c in real_candidates if 0.90 <= c["score"] < 0.95],
                 key=lambda c: (-c["score"], -c["n_mentions"]))
    for c in mid[:10]:
        print(f"  [[{c['target']}]] → [[{c['suggestion']}]]  "
              f"score={c['score']}  ({c['n_mentions']}m / {c['n_pages']}p)")

    print("\n=== Score 0.85 – 0.90 (top 10) ===")
    low = sorted([c for c in real_candidates if 0.85 <= c["score"] < 0.90],
                 key=lambda c: (-c["score"], -c["n_mentions"]))
    for c in low[:10]:
        print(f"  [[{c['target']}]] → [[{c['suggestion']}]]  "
              f"score={c['score']}  ({c['n_mentions']}m / {c['n_pages']}p)")

    out = ROOT / ".backup" / "baselines" / "typo_candidates.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(real_candidates, indent=2))
    print(f"\nSaved → {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
