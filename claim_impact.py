"""claim_impact.py — diff-style impact analysis for a newly-ingested paper.

Inspired by Understand-Anything's ``/understand-diff``. When a new source page
lands in ``wiki/sources/``, this script:

  1. Finds the concepts/entities it links to.
  2. For each, pulls the matching wiki page (the "prior art").
  3. Asks the LLM to classify the new paper's contribution as
     **agree** / **contradict** / **extend** / **orthogonal** for each claim.
  4. Writes a synthesis candidate to ``wiki/synthesis/impacts/<paper-stem>.md``.

The result is far more valuable than a stand-alone summary: it tells you
exactly *where this paper changes the picture*.

Usage::

    python3 claim_impact.py --paper Wang_2024_Knockout_ZmNST2_Bioethanol_Production_Co
    python3 claim_impact.py --paper sources/uncategorized/Wang_2024_*.md
    python3 claim_impact.py --paper Wang_2024_... --max-claims 8 --dry-run
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import yaml

import config  # noqa: F401
from genai_client import get_ai_response

WIKI = Path(__file__).resolve().parent / "wiki"
IMPACTS_DIR = WIKI / "synthesis" / "impacts"
LOG_PATH = WIKI / ".understand-anything" / "intermediate" / "claim_impact.jsonl"
WIKILINK_RE = re.compile(r"\[\[(.*?)\]\]")

PER_PAGE_CHAR_LIMIT = 5000


PROMPT_TEMPLATE = """You are a research analyst comparing a newly-ingested paper to a curated wiki.

The wiki uses ``[[wikilink]]`` syntax. Every claim must cite its source.

Your task: for each prior-art entry below, decide whether the **new paper** \
*agrees with*, *contradicts*, *extends*, or is *orthogonal to* the existing entry.

Output **valid JSON** matching exactly this schema (no prose, no markdown fences):

{{
  "summary": "<one paragraph: what does this paper change about the wiki?>",
  "findings": [
    {{
      "anchor": "<filename-stem of the prior-art page, exactly as given>",
      "verdict": "agree" | "contradict" | "extend" | "orthogonal",
      "claim_in_wiki": "<short quote or paraphrase of the relevant existing claim>",
      "what_paper_says": "<one sentence — what the new paper actually states>",
      "suggested_edit": "<one-sentence edit hint for the existing page; '' if no change needed>"
    }},
    ...
  ],
  "novel_claims": ["<one-line claim>", ...]
}}

Constraints:
- Only emit a finding if the new paper genuinely intersects the prior-art entry. Skip silent ones.
- ``contradict`` is reserved for direct disagreement on a factual claim, not for differences in scope.
- ``extend`` means "same direction, new evidence/method/target". ``agree`` means "same conclusion, replicates".
- ``novel_claims`` collects assertions that have **no** matching anchor in the prior art.
- Do not invent prior-art anchors not in the input list.

---

## New paper

### `{paper_stem}` ({paper_name})

{paper_body}

---

## Prior art ({n_prior} pages)

{prior_block}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
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


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    return text[end + 4:] if end > 0 else text


def _slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "impact"


JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _parse_llm_json(raw: str) -> dict | None:
    raw = raw.strip()
    for candidate in (raw, *(m.group(1) for m in JSON_FENCE_RE.finditer(raw))):
        try:
            return json.loads(candidate)
        except (ValueError, TypeError):
            continue
    if "{" in raw and "}" in raw:
        try:
            return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
        except (ValueError, TypeError):
            return None
    return None


def find_paper(spec: str) -> Path | None:
    """Resolve --paper argument: accepts bare stem, relative path, or glob."""
    if "/" in spec or spec.endswith(".md"):
        candidate = WIKI / spec
        if candidate.exists():
            return candidate
        # Glob
        matches = list(WIKI.glob(spec))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            print(f"ERROR: glob matched {len(matches)} files; be more specific", file=sys.stderr)
            return None
    # Bare stem — search sources/
    matches = list((WIKI / "sources").rglob(f"{spec}.md"))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"ERROR: stem '{spec}' matched {len(matches)} files in sources/; be more specific",
              file=sys.stderr)
        return None
    # Substring search
    fuzzy = [p for p in (WIKI / "sources").rglob("*.md") if spec.lower() in p.stem.lower()]
    if len(fuzzy) == 1:
        return fuzzy[0]
    if len(fuzzy) > 1:
        print(f"ERROR: substring '{spec}' matched {len(fuzzy)} files; be more specific", file=sys.stderr)
        for p in fuzzy[:5]:
            print(f"  - {p.relative_to(WIKI)}", file=sys.stderr)
        return None
    return None


def gather_prior_art(paper_path: Path, max_claims: int) -> list[Path]:
    """Collect concept/entity pages this paper wikilinks to that have content of their own."""
    body = _strip_frontmatter(paper_path.read_text(encoding="utf-8", errors="replace"))
    targets = {link.split("|")[0].split("#")[0].strip() for link in WIKILINK_RE.findall(body)}
    # Prefer concepts and entities; ignore other source links and self-link
    paper_stem = paper_path.stem
    candidates: list[Path] = []
    for kind in ("concepts", "entities"):
        kind_dir = WIKI / kind
        if not kind_dir.exists():
            continue
        for f in kind_dir.rglob("*.md"):
            if f.stem in targets and f.stem != paper_stem:
                candidates.append(f)
    # De-dup; rank by file size (proxy for "this page actually has claims")
    seen, ordered = set(), []
    for c in sorted(candidates, key=lambda p: -p.stat().st_size):
        if c not in seen:
            ordered.append(c)
            seen.add(c)
    return ordered[:max_claims]


def render_impact_page(parsed: dict, paper_path: Path, prior: list[Path]) -> str:
    today = datetime.date.today().isoformat()
    valid_anchors = {p.stem for p in prior}
    findings = parsed.get("findings") or []
    # Drop hallucinated anchors
    findings = [f for f in findings if f.get("anchor") in valid_anchors]

    lines = [
        "---",
        "tags: [synthesis, impact, auto-generated]",
        "type: synthesis",
        f"date_created: {today}",
        f"date_updated: {today}",
        f"source_count: 1",
        "---",
        "",
        f"# Impact analysis: {paper_path.stem}",
        "",
        f"**Summary**: {parsed.get('summary') or 'See findings below.'}",
        "",
        f"**Sources**: [[{paper_path.stem}]] versus {len(prior)} prior-art pages",
        "",
        f"**Last updated**: {today}",
        "",
        "---",
        "",
        f"## Findings ({len(findings)})",
        "",
    ]
    if not findings:
        lines += ["_No notable agreements, contradictions, or extensions detected._", ""]
    for f in findings:
        anchor = f.get("anchor", "?")
        verdict = f.get("verdict", "?").upper()
        lines += [
            f"### {verdict} · `[[{anchor}]]`",
            "",
            f"- **Claim in wiki**: {f.get('claim_in_wiki') or '_(none extracted)_'}",
            f"- **What this paper says**: {f.get('what_paper_says') or '_(none)_'}",
            f"- **Suggested edit**: {f.get('suggested_edit') or '_(none)_'}",
            "",
        ]

    novel = parsed.get("novel_claims") or []
    lines.append("## Novel claims (no matching prior-art page)")
    lines.append("")
    if not novel:
        lines.append("_None._")
    else:
        for c in novel:
            lines.append(f"- {c}")
    lines += [
        "",
        "## Related pages",
        "",
        f"- [[{paper_path.stem}]]",
    ]
    for p in prior:
        lines.append(f"- [[{p.stem}]]")
    lines += [
        "",
        "_Generated by `claim_impact.py`. Manual edits are preserved on regeneration if you "
        "remove the ``auto-generated`` tag from the frontmatter._",
    ]
    return "\n".join(lines) + "\n"


AUTO_TAG_MARKER = "auto-generated"


def write_impact(parsed: dict, paper_path: Path, prior: list[Path]) -> Path:
    IMPACTS_DIR.mkdir(parents=True, exist_ok=True)
    out = IMPACTS_DIR / f"{_slugify(paper_path.stem)}.md"
    if out.exists():
        existing = out.read_text(encoding="utf-8", errors="replace")
        if AUTO_TAG_MARKER not in existing[:300]:
            print(f"  · skipping {out.name}: file has manual edits")
            return out
    out.write_text(render_impact_page(parsed, paper_path, prior), encoding="utf-8")
    return out


def log_run(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", required=True,
                        help="Source page: bare stem (e.g. Wang_2024_...), relative path, or glob")
    parser.add_argument("--max-claims", type=int, default=10,
                        help="Cap the number of prior-art pages compared (default 10)")
    parser.add_argument("--model", default=None, help="Override the AI model")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompt size and bail without calling the LLM")
    args = parser.parse_args(argv)

    paper_path = find_paper(args.paper)
    if not paper_path:
        print(f"ERROR: could not resolve --paper '{args.paper}'", file=sys.stderr)
        return 1

    prior = gather_prior_art(paper_path, args.max_claims)
    if not prior:
        print(f"ERROR: paper {paper_path.stem} doesn't link to any concept/entity pages "
              "with content — nothing to compare against.", file=sys.stderr)
        return 1

    paper_body = _strip_frontmatter(paper_path.read_text(encoding="utf-8", errors="replace"))[:PER_PAGE_CHAR_LIMIT]
    paper_fm = _read_frontmatter(paper_path.read_text(encoding="utf-8", errors="replace"))
    paper_name = paper_fm.get("title") or paper_path.stem

    prior_block = "\n\n".join(
        f"### `{p.stem}` (`{p.relative_to(WIKI)}`)\n\n"
        f"{_strip_frontmatter(p.read_text(encoding='utf-8', errors='replace'))[:PER_PAGE_CHAR_LIMIT]}"
        for p in prior
    )
    prompt = PROMPT_TEMPLATE.format(
        paper_stem=paper_path.stem, paper_name=paper_name,
        paper_body=paper_body, n_prior=len(prior), prior_block=prior_block,
    )

    print(f"  Paper      : {paper_path.relative_to(WIKI)}")
    print(f"  Prior art  : {len(prior)} pages")
    print(f"  Prompt size: {len(prompt)} chars")

    if args.dry_run:
        return 0

    chosen_model = args.model or getattr(config, "AI_MODEL", "claude-opus-5-thinking")
    print(f"  Calling {chosen_model}…")
    try:
        raw = get_ai_response(prompt, model=chosen_model, raise_on_error=True)
    except Exception as e:
        print(f"  ERROR: LLM call failed: {e}", file=sys.stderr)
        return 1

    parsed = _parse_llm_json(raw)
    if not parsed or not isinstance(parsed.get("findings"), list):
        debug_path = LOG_PATH.parent / f"claim_impact_failed_{paper_path.stem}.txt"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(raw, encoding="utf-8")
        print(f"  ERROR: could not parse LLM output as JSON. Raw saved to {debug_path}", file=sys.stderr)
        return 1

    out = write_impact(parsed, paper_path, prior)
    log_run({
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "paper": paper_path.stem, "model": chosen_model,
        "n_findings": len(parsed.get("findings") or []),
        "n_novel": len(parsed.get("novel_claims") or []),
        "prior_art": [p.stem for p in prior],
        "output": str(out.relative_to(WIKI)),
    })
    print(f"  ✓ Wrote {out.relative_to(WIKI)}  "
          f"({len(parsed.get('findings') or [])} findings, "
          f"{len(parsed.get('novel_claims') or [])} novel claims)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
