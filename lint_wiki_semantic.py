"""LLM-based semantic audit of the wiki — the graph-reviewer pattern.

Runs alongside ``lint_wiki.py`` (which handles structural validation).
This script asks an LLM to find issues a parser cannot:

  * contradictions between pages
  * claims that look outdated relative to newer sources
  * concepts mentioned in body text without a corresponding wiki page
  * missing or weak citations

Usage::

    python3 lint_wiki_semantic.py                  # audits 20 most-recently-changed pages
    python3 lint_wiki_semantic.py --pages 50       # change page budget
    python3 lint_wiki_semantic.py --pattern "synthesis/*.md"   # restrict to a glob
    python3 lint_wiki_semantic.py --dry-run        # print prompt but don't call LLM

Output is appended to ``wiki_lint_semantic_report.md`` next to the
structural ``wiki_lint_report.md``.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Iterable

import config  # noqa: F401  -- imported for side effects (env / project setup)
from genai_client import get_ai_response

WIKI_DIR = Path(__file__).resolve().parent / "wiki"
REPORT_PATH = Path(__file__).resolve().parent / "wiki_lint_semantic_report.md"
INDEX_PATH = WIKI_DIR / "index.md"

# Cap individual page bodies so the prompt stays well under model context
# limits. A typical concept page is < 4 KB; sources can be larger.
PER_PAGE_CHAR_LIMIT = 6000
INDEX_CHAR_LIMIT = 15000

AUDIT_PROMPT = """You are a senior research-wiki reviewer auditing a Karpathy-pattern LLM wiki on plant genetics.

The wiki schema is:
- concepts/   — one page per idea
- entities/   — one page per gene, protein, organism, tool
- sources/    — one page per ingested paper (DOI, authors, year, key claims)
- synthesis/  — cross-cutting answers

Citation rule: every factual claim must reference its source via ``[[source-filename]]``.
If sources disagree the page must say so explicitly.

You will be given (a) the wiki master index and (b) a sample of recently-edited pages.
Find issues a regex-based linter cannot detect. Focus on:

1. **Contradictions** — two pages that disagree on a factual claim without flagging it.
2. **Outdated claims** — assertions on a page that are likely obsolete given a more recent source listed in the index.
3. **Mentioned-but-missing** — a concept named in body text but with no dedicated page.
4. **Unsourced claims** — factual claims with no ``[[source]]`` wikilink.
5. **Format drift** — pages that violate the GEMINI.md schema (missing ``**Summary**``, ``**Sources**``, ``## Related pages``, citation format).

Return your findings as a single Markdown document with these exact top-level sections:

## 1. Contradictions
## 2. Outdated claims
## 3. Mentioned-but-missing
## 4. Unsourced claims
## 5. Format drift
## 6. Other notable issues

Under each section use a numbered list. Each item must:
- Quote the page filename in backticks.
- Quote the offending phrase in italics if applicable.
- State the suggested fix in one sentence.

If a section has no findings, write ``_None found._`` under it. Do not invent issues.
Do not repeat the wiki contents verbatim. Be terse.

---

## Wiki index (first {index_chars} chars)

{index}

---

## Pages under review ({n_pages} pages)

{pages}
"""


def _read_index() -> str:
    if not INDEX_PATH.exists():
        return "(index.md missing)"
    text = INDEX_PATH.read_text(encoding="utf-8", errors="replace")
    if len(text) > INDEX_CHAR_LIMIT:
        text = text[:INDEX_CHAR_LIMIT] + "\n…(index truncated)…"
    return text


def _candidate_pages(pattern: str | None) -> list[Path]:
    """Pages eligible for review, excluding index/log."""
    if pattern:
        files = list(WIKI_DIR.glob(pattern))
    else:
        files = list(WIKI_DIR.rglob("*.md"))
    skip = {WIKI_DIR / "index.md", WIKI_DIR / "log.md"}
    return [f for f in files if f not in skip and f.is_file()]


def _select_recent(files: Iterable[Path], limit: int) -> list[Path]:
    """Return the most-recently-modified ``limit`` files, sorted newest first."""
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def _select_entity_subgraph(entity_slug: str, limit: int = 50) -> list[Path]:
    """Select the complete sub-graph cluster for a target entity/concept.
    Includes target page, all citing source papers, and related neighbor pages."""
    import re
    slug_clean = entity_slug.strip().lower()
    selected: set[Path] = set()

    # 1. Target entity/concept page
    for sub in ["entities", "concepts"]:
        p = WIKI_DIR / sub / f"{slug_clean}.md"
        if p.exists():
            selected.add(p)
            break

    # 2. Citing source papers
    pattern = re.compile(rf"\[\[{re.escape(slug_clean)}(\||\])", re.IGNORECASE)
    sources = list((WIKI_DIR / "sources").rglob("*.md"))
    for s in sources:
        try:
            txt = s.read_text(encoding="utf-8", errors="replace")
            if pattern.search(txt):
                selected.add(s)
        except Exception:
            pass

    # 3. Add neighbor entity/concept pages linked from the target page
    if selected:
        for p_target in list(selected):
            try:
                txt = p_target.read_text(encoding="utf-8", errors="replace")
                for m in re.findall(r"\[\[([^\]]+)\]\]", txt):
                    ref_slug = m.split("|")[0].strip().lower()
                    for sub in ["entities", "concepts"]:
                        p = WIKI_DIR / sub / f"{ref_slug}.md"
                        if p.exists():
                            selected.add(p)
            except Exception:
                pass

    return sorted(list(selected), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def _format_page_block(path: Path) -> str:
    rel = path.relative_to(WIKI_DIR).as_posix()
    body = path.read_text(encoding="utf-8", errors="replace")
    if len(body) > PER_PAGE_CHAR_LIMIT:
        body = body[:PER_PAGE_CHAR_LIMIT] + "\n…(truncated)…"
    return f"### `{rel}`\n\n{body}\n"


def _build_prompt(pages: list[Path]) -> str:
    return AUDIT_PROMPT.format(
        index_chars=INDEX_CHAR_LIMIT,
        index=_read_index(),
        n_pages=len(pages),
        pages="\n\n".join(_format_page_block(p) for p in pages),
    )


def _write_report(audit: str, pages: list[Path], model: str) -> None:
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    rels = [p.relative_to(WIKI_DIR).as_posix() for p in pages]
    header = (
        "# Wiki Semantic Lint Report\n\n"
        f"_Generated: {ts}_\n"
        f"_Model: `{model}`_\n"
        f"_Pages reviewed: {len(pages)}_\n\n"
        "**Reviewed pages:**\n\n"
        + "\n".join(f"- `{r}`" for r in rels)
        + "\n\n---\n\n"
    )
    REPORT_PATH.write_text(header + audit.strip() + "\n", encoding="utf-8")
    print(f"✓ Wrote {REPORT_PATH}")


def _emit_pipeline_log(pages: list[Path], model: str, char_count: int) -> None:
    """Append a one-line JSONL record to wiki/.understand-anything/intermediate/semantic_lint.jsonl."""
    log_dir = WIKI_DIR / ".understand-anything" / "intermediate"
    log_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "pages_reviewed": len(pages),
        "prompt_chars": char_count,
        "files": [p.relative_to(WIKI_DIR).as_posix() for p in pages],
    }
    with (log_dir / "semantic_lint.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Semantic auto-repair engine
# ---------------------------------------------------------------------------

REPAIR_PROMPT = """You are a wiki page editor. You will be given:
1. The current content of a wiki page.
2. A list of specific issues found by an auditor.

Your task is to fix ALL the listed issues and return the COMPLETE corrected page.

Rules:
- Fix unsourced claims by adding inline ``[[source-filename]]`` citations from the page's **Sources** list.
- Fix duplicate headings by keeping only one instance.
- Fix format drift by conforming to the schema (YAML frontmatter, **Summary**:, **Sources**:, **Last updated**:, ## Related pages).
- Do NOT add information that isn't already on the page or in its sources.
- Do NOT remove existing content unless the issue specifically requires it (e.g. duplicate headings).
- Do NOT add markdown code fences around your output.
- Return ONLY the corrected page content, nothing else. No explanations, no preamble.

---

## Current page content

```
{page_content}
```

---

## Issues to fix

{issues}
"""


def _extract_page_issues(audit_text: str, pages: list[Path]) -> dict[Path, list[str]]:
    """Parse the audit report and map findings back to specific pages."""
    page_issues: dict[Path, list[str]] = {p: [] for p in pages}

    # Match lines like:
    #   1. `entities/foo.md`: ...
    #   1. ``entities/foo.md`` The claim ...
    #   1. entities/foo.md: ...
    issue_re = re.compile(
        r'^\s*\d+\.\s+(?:`{1,2}|")?((?:entities|concepts|sources|synthesis)/[^\s`"]+\.md)(?:`{1,2}|")?\s*:?\s*(.+)',
        re.MULTILINE | re.IGNORECASE
    )

    for m in issue_re.finditer(audit_text):
        rel_path = m.group(1).strip()
        issue_text = m.group(2).strip()

        # Also grab continuation lines (suggested fix, etc.)
        start = m.end()
        continuation = []
        for line in audit_text[start:].splitlines():
            stripped = line.strip()
            if not stripped:
                break
            if stripped.startswith(('#', '_')):
                break
            if re.match(r'^\s*\d+\.\s+', stripped):
                break
            continuation.append(stripped)

        full_issue = issue_text
        if continuation:
            full_issue += '\n   ' + '\n   '.join(continuation)

        # Match to a page path
        for p in pages:
            p_rel = p.relative_to(WIKI_DIR).as_posix()
            if p_rel.lower() == rel_path.lower() or p.stem.lower() in rel_path.lower():
                page_issues[p].append(full_issue)
                break

    # Fallback: if no structured match, search for page stem anywhere in numbered lines
    if not any(page_issues.values()):
        for p in pages:
            stem = p.stem.lower()
            p_rel = p.relative_to(WIKI_DIR).as_posix().lower()
            matched_lines = []
            for line in audit_text.splitlines():
                if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    if stem in line.lower() or p_rel in line.lower():
                        matched_lines.append(line.strip())
            if matched_lines:
                page_issues[p].extend(matched_lines)

    return {p: issues for p, issues in page_issues.items() if issues}


def _repair_pages(audit_text: str, pages: list[Path], model: str) -> int:
    """Send each affected page + its issues to the LLM for repair. Returns count of repaired pages."""
    import shutil

    page_issues = _extract_page_issues(audit_text, pages)

    if not page_issues:
        print("  ✓ No pages need semantic repair.")
        return 0

    backup_dir = Path(__file__).resolve().parent / '.backup'
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    repaired = 0
    for page_path, issues in page_issues.items():
        rel = page_path.relative_to(WIKI_DIR).as_posix()
        print(f"  🔧 Repairing `{rel}` ({len(issues)} issues)...")

        page_content = page_path.read_text(encoding="utf-8", errors="replace")
        issues_text = "\n".join(f"{i+1}. {issue}" for i, issue in enumerate(issues))

        prompt = REPAIR_PROMPT.format(
            page_content=page_content,
            issues=issues_text,
        )

        try:
            fixed_content = get_ai_response(prompt, model=model, raise_on_error=True)
        except Exception as e:
            print(f"    ❌ LLM repair failed for `{rel}`: {e}")
            continue

        # Strip markdown code fences if the LLM wrapped its output
        fixed_content = fixed_content.strip()
        if fixed_content.startswith('```'):
            # Remove opening fence
            first_nl = fixed_content.find('\n')
            if first_nl != -1:
                fixed_content = fixed_content[first_nl + 1:]
            # Remove closing fence
            if fixed_content.rstrip().endswith('```'):
                fixed_content = fixed_content.rstrip()[:-3].rstrip()

        # Sanity check: repaired content should still have frontmatter
        if not fixed_content.startswith('---'):
            print(f"    ⚠️  Skipping `{rel}`: repaired content missing frontmatter (LLM may have stripped it)")
            continue

        # Backup and write
        backup_dest = backup_dir / f"{page_path.stem}_{ts}.md"
        shutil.copy2(page_path, backup_dest)
        page_path.write_text(fixed_content + '\n', encoding="utf-8")
        repaired += 1
        print(f"    ✓ Repaired `{rel}` (backup: {backup_dest.name})")

    return repaired


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=int, default=20,
                        help="Number of pages to audit (default 20)")
    parser.add_argument("--entity", default=None,
                        help="Target entity or concept slug to perform an exhaustive sub-graph cluster audit (e.g. 'nifa' or 'nitrogenase')")
    parser.add_argument("--pattern", default=None,
                        help="Optional glob pattern (relative to wiki/) to restrict the candidate set, "
                             "e.g. 'synthesis/*.md'")
    parser.add_argument("--model", default=None,
                        help="Override the AI model (defaults to config.AI_MODEL)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the prompt and exit without calling the LLM")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-repair pages after auditing (sends findings to LLM for correction, "
                             "backups saved to .backup/)")
    args = parser.parse_args(argv)

    if not WIKI_DIR.exists():
        print(f"ERROR: wiki directory not found: {WIKI_DIR}", file=sys.stderr)
        return 2

    if args.entity:
        selected = _select_entity_subgraph(args.entity, limit=args.pages)
        print(f"Auditing sub-graph cluster for entity '{args.entity}' ({len(selected)} connected pages)")
    else:
        candidates = _candidate_pages(args.pattern)
        if not candidates:
            print("No candidate pages found.", file=sys.stderr)
            return 1
        selected = _select_recent(candidates, args.pages)
        print(f"Auditing {len(selected)} pages out of {len(candidates)} candidates "
              f"(pattern={args.pattern or 'all'})")

    prompt = _build_prompt(selected)

    if args.dry_run:
        print(f"\n--- PROMPT ({len(prompt)} chars) ---\n")
        print(prompt[:3000])
        print("\n…(truncated for display)…" if len(prompt) > 3000 else "")
        return 0

    import config as _cfg  # local re-import so dry-run path doesn't require it
    model = args.model or getattr(_cfg, "AI_MODEL", "claude-opus-5-thinking")
    print(f"Calling {model}…  ({len(prompt)} prompt chars)")

    try:
        audit = get_ai_response(prompt, model=model, raise_on_error=True)
    except Exception as e:
        print(f"ERROR: LLM call failed: {e}", file=sys.stderr)
        return 1

    _write_report(audit, selected, model)
    _emit_pipeline_log(selected, model, len(prompt))

    # ── Auto-repair pass ──
    if args.fix:
        print(f"\n🔧 Semantic auto-repair pass...")
        repaired = _repair_pages(audit, selected, model)
        print(f"  ✓ Semantic repair complete: {repaired} page(s) fixed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

