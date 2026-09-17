"""(c2) Emit a human-review markdown list of medium-confidence typo
candidates (score in [0.85, 0.95)).

For each candidate, includes:
  * the broken target and proposed correction
  * the score, mention count, and citing-page paths
  * one snippet of context (the line in the citing page that contains the
    `[[target]]`) so you can decide quickly without opening files

Read-only — writes ``wiki_typo_review.md`` to the project root.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
CANDIDATES = ROOT / ".backup" / "baselines" / "typo_candidates.json"
OUT = ROOT / "wiki_typo_review.md"
WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")


def find_context(target: str, file_path: Path) -> str:
    """Return the first line of file_path that contains [[target]]."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return "(file unreadable)"
    pat = re.compile(r"\[\[\s*" + re.escape(target) + r"\s*(?:#[^\]|]*)?(?:\|[^\]]*)?\s*\]\]")
    for line in text.splitlines():
        if pat.search(line):
            return line.strip()[:200]
    return "(target not found inline — frontmatter only?)"


def main() -> int:
    if not CANDIDATES.exists():
        print(f"ERROR: {CANDIDATES} not found. Run typo_survey.py first.")
        return 1

    cands = json.loads(CANDIDATES.read_text())
    selected = [c for c in cands if 0.85 <= c["score"] < 0.95]
    selected.sort(key=lambda c: (-c["score"], -c["n_mentions"], c["target"]))

    print(f"Building review list for {len(selected)} medium-confidence candidates…")

    lines: list[str] = []
    lines.append("# Typo Review List (medium-confidence)")
    lines.append("")
    lines.append("Each entry is a wikilink target that fuzzy-matches an existing page "
                 "with score in [0.85, 0.95). Auto-fix would be too risky — please "
                 "review and either:")
    lines.append("")
    lines.append("- ✅ accept: the suggestion is right; do `[[target]] → [[suggestion]]`")
    lines.append("- ❌ reject: target is a different concept; either create a real page "
                 "or strip the brackets")
    lines.append("- 🤔 unsure: leave as-is for now")
    lines.append("")
    lines.append("---")
    lines.append("")

    band_92_95 = [c for c in selected if c["score"] >= 0.90]
    band_85_90 = [c for c in selected if c["score"] < 0.90]

    def render(group_label: str, group: list[dict]) -> None:
        lines.append(f"## {group_label}  ({len(group)} entries)")
        lines.append("")
        if not group:
            lines.append("_None._")
            lines.append("")
            return
        for c in group:
            target = c["target"]
            sugg = c["suggestion"]
            score = c["score"]
            np = c["n_pages"]
            nm = c["n_mentions"]
            first = c["first_pages"][:3]
            ctx = find_context(target, WIKI / first[0]) if first else "(no citing pages)"
            lines.append(f"### `[[{target}]]` → `[[{sugg}]]`")
            lines.append("")
            lines.append(f"- **Score**: {score} | **Pages**: {np} | **Mentions**: {nm}")
            lines.append(f"- **Citing**: " + ", ".join(f"`{p}`" for p in first))
            lines.append(f"- **Context**: {ctx}")
            lines.append("")

    render("Score 0.90 – 0.95 (review)", band_92_95)
    render("Score 0.85 – 0.90 (review, weak — many will be rejects)", band_85_90)

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
