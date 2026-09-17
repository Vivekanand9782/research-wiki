"""Step 2 (read-only): produce a prioritized broken-wikilinks report.

For every target ``[[name]]`` whose target file does not exist:
  * count how many distinct pages mention it (mention_pages)
  * count total mentions across the wiki (mention_count)
  * record the first 5 referencing pages (so you can find context fast)
  * bucket it:
      - Tier 1: mention_pages >= 3   → high-value, likely a real concept
      - Tier 2: mention_pages == 2   → may be worth a page
      - Tier 3: mention_pages == 1   → often typos or one-offs
  * for Tier 3, fuzzy-match against existing page names. If a close match
    exists (Levenshtein ratio >= 0.85, |len_diff| <= 3), flag as a typo
    candidate with the suggested correct name.

Writes ``wiki_broken_links_prioritized.md``. Does NOT modify any wiki page.
"""
from __future__ import annotations

import difflib
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
REPORT_PATH = ROOT / "wiki_broken_links_prioritized.md"

TYPO_RATIO_CUTOFF = 0.85  # difflib SequenceMatcher.ratio()
TYPO_LEN_DIFF_MAX = 3      # hard cap on stem length difference


def collect_page_names() -> tuple[set[str], dict[str, str], set[str]]:
    """Return (all_page_names, alias_map, normalized_page_names).

    ``all_page_names`` contains: bare stems (``foo``), relative paths
    without extension (``concepts/foo``), and YAML ``aliases`` from
    frontmatter.

    ``alias_map`` maps every name back to its canonical relative path so we
    can present typo suggestions as the canonical page.

    ``normalized_page_names`` contains the slugified+lowercased version of
    every name above. Used to detect case/slug-only mismatches that
    Obsidian would resolve transparently.
    """
    all_names: set[str] = set()
    alias_map: dict[str, str] = {}
    normalized: set[str] = set()
    for f in WIKI.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = f.relative_to(WIKI).with_suffix("").as_posix()
        stem = f.stem
        all_names.add(stem)
        all_names.add(rel)
        alias_map[stem] = rel
        alias_map[rel] = rel
        normalized.add(_slugify(stem))
        normalized.add(_slugify(rel))
        for a in extract_aliases(text):
            all_names.add(a)
            alias_map[a] = rel
            normalized.add(_slugify(a))
    return all_names, alias_map, normalized


def _slugify(name: str) -> str:
    """Mirror the ``populate_wiki_nodes`` rule in pdf_extractor.py:
    non-alnum runs become a single dash, lowercased, with leading/trailing
    dashes stripped. Used so we can recognise that ``[[Zea mays]]`` and
    ``zea-mays.md`` refer to the same page.
    """
    return re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()


def collect_links() -> tuple[
    dict[str, int],            # target -> total mentions
    dict[str, set[Path]],      # target -> set of pages mentioning it
    dict[str, list[Path]],     # target -> ordered list (first 5) of referencing pages
]:
    total: Counter[str] = Counter()
    pages: dict[str, set[Path]] = defaultdict(set)
    examples: dict[str, list[Path]] = defaultdict(list)
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
            if f not in pages[target]:
                pages[target].add(f)
                if len(examples[target]) < 5:
                    examples[target].append(f)
    return dict(total), dict(pages), dict(examples)


def fuzzy_suggest(target: str, all_names: list[str]) -> list[tuple[str, float]]:
    """Return (name, ratio) pairs that are close to ``target``."""
    target_lower = target.lower()
    candidates: list[tuple[str, float]] = []
    for name in all_names:
        if abs(len(name) - len(target)) > TYPO_LEN_DIFF_MAX:
            continue
        ratio = difflib.SequenceMatcher(None, target_lower, name.lower()).ratio()
        if ratio >= TYPO_RATIO_CUTOFF:
            candidates.append((name, ratio))
    candidates.sort(key=lambda kv: -kv[1])
    return candidates[:3]


def main() -> int:
    print("Building page-name index…")
    all_names, alias_map, normalized = collect_page_names()
    print(f"  {len(all_names):,} known names (stems + paths + aliases)")
    print(f"  {len(normalized):,} normalized (slug+lowercase) names")

    print("Scanning wikilinks…")
    total, pages, examples = collect_links()
    print(f"  {len(total):,} distinct wikilink targets")

    # Phase 1 — strict case-sensitive comparison (Obsidian-strict).
    strict_broken = [t for t in total if t not in all_names]
    # Phase 2 — Obsidian-default semantics: also accept slug-normalized matches.
    truly_broken = [t for t in strict_broken if _slugify(t) not in normalized]
    print(f"  {len(strict_broken):,} broken targets (strict comparison)")
    print(f"  {len(truly_broken):,} broken targets (after slug-normalized match)")
    print(f"  → {len(strict_broken) - len(truly_broken):,} are case/slug "
          "mismatches that Obsidian resolves automatically (false positives).")

    broken_targets = truly_broken

    # Bucket
    tier1: list[str] = []  # >=3 pages
    tier2: list[str] = []  # ==2 pages
    tier3: list[str] = []  # ==1 page
    for t in broken_targets:
        n = len(pages[t])
        if n >= 3:
            tier1.append(t)
        elif n == 2:
            tier2.append(t)
        else:
            tier3.append(t)

    # Sort by mention_pages desc, then total mentions desc
    sort_key = lambda t: (-len(pages[t]), -total[t], t.lower())
    tier1.sort(key=sort_key)
    tier2.sort(key=sort_key)
    tier3.sort(key=sort_key)

    # Fuzzy match for Tier 3 only (typo candidates).
    print("Computing typo suggestions for Tier 3…")
    name_list = sorted(all_names)
    typo_suggestions: dict[str, list[tuple[str, float]]] = {}
    for t in tier3:
        suggs = fuzzy_suggest(t, name_list)
        if suggs:
            typo_suggestions[t] = suggs

    # ---- emit report ----
    lines: list[str] = []
    lines.append("# Broken Wikilinks — Prioritized Report")
    lines.append("")
    lines.append(
        f"Strict broken targets (case-sensitive): **{len(strict_broken):,}**  "
        f"— {len(strict_broken) - len(truly_broken):,} are case/slug "
        "mismatches Obsidian resolves automatically."
    )
    lines.append(
        f"Genuinely broken targets (after slug-normalisation): "
        f"**{len(truly_broken):,}**"
    )
    lines.append(f"Total broken-link occurrences: **{sum(total[t] for t in broken_targets):,}**")
    lines.append("")
    lines.append(
        f"- **Tier 1** (mentioned in ≥3 distinct pages): **{len(tier1)}** targets — "
        "high-value; each likely deserves a real page."
    )
    lines.append(
        f"- **Tier 2** (mentioned in exactly 2 pages): **{len(tier2)}** targets — "
        "may deserve a page if scope-aligned."
    )
    lines.append(
        f"- **Tier 3** (mentioned in exactly 1 page): **{len(tier3)}** targets — "
        "many are typos or one-offs; review and either strip brackets or fix."
    )
    lines.append(
        f"- **Tier 3 with fuzzy match to an existing page**: "
        f"**{len(typo_suggestions)}** likely typos."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    def render_tier(name: str, items: list[str], with_typos: bool = False) -> None:
        lines.append(f"## {name}  ({len(items)} targets)")
        lines.append("")
        if not items:
            lines.append("_None._")
            lines.append("")
            return
        if with_typos:
            lines.append("Format: `[[target]]` — N pages — first refs — *typo suggestion*")
        else:
            lines.append("Format: `[[target]]` — N pages, total mentions — first refs")
        lines.append("")
        for t in items:
            n_pages = len(pages[t])
            n_total = total[t]
            ex = ", ".join(
                f"`{p.relative_to(WIKI).as_posix()}`" for p in examples[t][:3]
            )
            base = f"- `[[{t}]]` — **{n_pages}p / {n_total}m** — {ex}"
            if with_typos and t in typo_suggestions:
                top = typo_suggestions[t][0]
                base += f" *(typo? → `[[{top[0]}]]` score={top[1]:.2f})*"
            lines.append(base)
        lines.append("")

    render_tier("Tier 1 — high-value", tier1)
    render_tier("Tier 2 — medium-value", tier2)
    render_tier("Tier 3 — singletons (with typo suggestions)", tier3, with_typos=True)

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {REPORT_PATH.relative_to(ROOT)}")
    print()
    print(f"Tier 1: {len(tier1)} targets")
    print(f"Tier 2: {len(tier2)} targets")
    print(f"Tier 3: {len(tier3)} targets ({len(typo_suggestions)} with typo suggestions)")

    # ---- print 10 examples per tier for the hard-stop summary ----
    def show_n(label: str, items: list[str], n: int = 10) -> None:
        print(f"\n=== {label} (top {n}) ===")
        for t in items[:n]:
            n_pages = len(pages[t])
            n_total = total[t]
            sugg = ""
            if t in typo_suggestions:
                sugg = f"  → typo? [[{typo_suggestions[t][0][0]}]]"
            print(f"  [[{t}]]  ({n_pages}p / {n_total}m){sugg}")

    show_n("Tier 1", tier1)
    show_n("Tier 2", tier2)
    show_n("Tier 3 with typo suggestion",
           [t for t in tier3 if t in typo_suggestions])
    show_n("Tier 3 without typo suggestion (probably orphan concepts)",
           [t for t in tier3 if t not in typo_suggestions])
    return 0


if __name__ == "__main__":
    sys.exit(main())
