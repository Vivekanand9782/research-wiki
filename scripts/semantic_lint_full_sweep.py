"""Full-wiki semantic-lint sweep, batched.

Batches every candidate page into chunks of ``--batch-size`` pages (default
200) and runs ``lint_wiki_semantic.py``'s prompt against each chunk
sequentially. Each batch's output is saved to its own file so a mid-run
failure doesn't lose work. Re-running with the same sweep timestamp resumes
from where you left off (already-saved batches are skipped).

Outputs:
  * Per-batch reports under ``.backup/semantic_lint_full/<sweep_ts>/``
    e.g. ``batch_001_of_024.md``
  * Aggregated report at ``wiki_lint_semantic_full_report.md`` with
    findings grouped by the original 6 sections.
  * Run manifest at ``.backup/semantic_lint_full/<sweep_ts>/manifest.json``
    (lists every batch, its file paths, status, and prompt size).

The script reuses functions from ``lint_wiki_semantic.py`` so prompt
construction stays identical to the one-shot tool.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Reuse all prompt-building primitives from the existing tool.
from lint_wiki_semantic import (  # noqa: E402
    AUDIT_PROMPT,
    INDEX_CHAR_LIMIT,
    PER_PAGE_CHAR_LIMIT,
    WIKI_DIR,
    _build_prompt,
    _candidate_pages,
    _format_page_block,
    _read_index,
    _select_recent,
)
import config  # noqa: E402
from genai_client import get_ai_response  # noqa: E402

SWEEP_ROOT = ROOT / ".backup" / "semantic_lint_full"
AGGREGATE_PATH = ROOT / "wiki_lint_semantic_full_report.md"

SECTION_HEADINGS = [
    "## 1. Contradictions",
    "## 2. Outdated claims",
    "## 3. Mentioned-but-missing",
    "## 4. Unsourced claims",
    "## 5. Format drift",
    "## 6. Other notable issues",
]


def _batch_id(batch: list[Path]) -> str:
    """Deterministic short id for a batch (so resumes match)."""
    h = hashlib.sha256()
    for p in batch:
        h.update(p.relative_to(WIKI_DIR).as_posix().encode())
        h.update(b"\0")
    return h.hexdigest()[:10]


def _split_batches(files: list[Path], batch_size: int) -> list[list[Path]]:
    return [files[i:i + batch_size] for i in range(0, len(files), batch_size)]


def _split_sections(report: str) -> dict[str, str]:
    """Parse a single-batch report into {section_heading: section_body}."""
    out: dict[str, str] = {h: "" for h in SECTION_HEADINGS}
    for i, h in enumerate(SECTION_HEADINGS):
        next_h = SECTION_HEADINGS[i + 1] if i + 1 < len(SECTION_HEADINGS) else None
        # Find heading + body until the next heading (or EOF).
        pat = re.escape(h)
        if next_h:
            m = re.search(pat + r"(.*?)(?=\n" + re.escape(next_h) + r")", report, re.DOTALL)
        else:
            m = re.search(pat + r"(.*?)$", report, re.DOTALL)
        if m:
            out[h] = m.group(1).strip()
    return out


def _aggregate(batch_reports: list[tuple[int, Path, str, list[Path]]]) -> str:
    """Combine all per-batch reports into one consolidated document."""
    by_section: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for idx, _path, body, _batch_pages in batch_reports:
        for h, content in _split_sections(body).items():
            if content and content.lower() != "_none found._":
                by_section[h].append((idx, content))

    today = datetime.datetime.now().isoformat(timespec="seconds")
    n_batches = len(batch_reports)
    total_pages = sum(len(pages) for _, _, _, pages in batch_reports)

    lines: list[str] = []
    lines.append("# Wiki Semantic Lint — Full Sweep Report")
    lines.append("")
    lines.append(f"_Generated: {today}_")
    lines.append(f"_Batches: {n_batches}_")
    lines.append(f"_Pages reviewed: {total_pages}_")
    lines.append("")
    lines.append(
        "Findings are grouped by the original 6 sections. Each finding is "
        "tagged with `[batch N]` so you can trace it back to a specific batch "
        "report under `.backup/semantic_lint_full/<sweep_ts>/`."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    for h in SECTION_HEADINGS:
        lines.append(h)
        lines.append("")
        items = by_section.get(h, [])
        if not items:
            lines.append("_None found across any batch._")
            lines.append("")
            continue
        for batch_idx, body in items:
            lines.append(f"### From batch {batch_idx}")
            lines.append("")
            lines.append(body.strip())
            lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=200,
                        help="Pages per batch (default 200)")
    parser.add_argument("--pattern", default=None,
                        help="Optional glob restricting candidates (e.g. 'entities/*.md')")
    parser.add_argument("--model", default=None,
                        help="Override AI model (defaults to config.AI_MODEL)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print batch plan and prompt sizes; make NO LLM calls")
    parser.add_argument("--sweep-id", default=None,
                        help="Resume an existing sweep directory by id")
    parser.add_argument("--retries", type=int, default=2,
                        help="Per-batch retry count on errors (default 2)")
    parser.add_argument("--retry-delay", type=int, default=10,
                        help="Seconds to sleep between retries (default 10)")
    args = parser.parse_args()

    if not WIKI_DIR.exists():
        print(f"ERROR: wiki directory not found: {WIKI_DIR}", file=sys.stderr)
        return 2

    # 1) Build the candidate list and split into batches deterministically.
    candidates = _candidate_pages(args.pattern)
    if not candidates:
        print("No candidate pages found.", file=sys.stderr)
        return 1
    ordered = _select_recent(candidates, len(candidates))  # newest first
    batches = _split_batches(ordered, args.batch_size)
    n_batches = len(batches)

    # 2) Pick / create the sweep directory.
    sweep_id = args.sweep_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sweep_dir = SWEEP_ROOT / sweep_id
    sweep_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = sweep_dir / "manifest.json"

    print(f"Sweep id      : {sweep_id}")
    print(f"Sweep dir     : {sweep_dir.relative_to(ROOT)}")
    print(f"Pages         : {len(candidates):,} (pattern={args.pattern or 'all'})")
    print(f"Batch size    : {args.batch_size}")
    print(f"Total batches : {n_batches}")
    if args.dry_run:
        print("\nMode          : DRY-RUN (no LLM calls)")
    print()

    model = args.model or getattr(config, "AI_MODEL", "minimax-m2.7")
    print(f"Model         : {model}")

    # 3) Pre-flight: build prompts and report sizes (cheap).
    print()
    print("Pre-flight (prompt sizes per batch):")
    plans: list[tuple[int, list[Path], str, int, Path, str]] = []
    total_prompt_chars = 0
    for i, batch in enumerate(batches, 1):
        bid = _batch_id(batch)
        out_path = sweep_dir / f"batch_{i:03d}_of_{n_batches:03d}_{bid}.md"
        prompt = _build_prompt(batch)
        plans.append((i, batch, bid, len(prompt), out_path, prompt))
        total_prompt_chars += len(prompt)
        status = "DONE" if out_path.exists() else "TODO"
        print(f"  batch {i:3d}/{n_batches}: {len(batch):3d} pages, "
              f"{len(prompt):>7,} chars, {status}, {out_path.name}")
    pending = sum(1 for _, _, _, _, p, _ in plans if not p.exists())
    print()
    print(f"Total prompt chars: {total_prompt_chars:,}")
    print(f"Pending batches  : {pending}/{n_batches}")
    print(f"Already complete : {n_batches - pending}/{n_batches}")

    # 4) Persist plan to manifest (so a resume understands what was planned).
    manifest = {
        "sweep_id": sweep_id,
        "model": model,
        "batch_size": args.batch_size,
        "total_pages": len(candidates),
        "total_batches": n_batches,
        "pattern": args.pattern,
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "batches": [
            {
                "idx": i,
                "n_pages": len(batch),
                "batch_id": bid,
                "out_path": str(out_path.relative_to(ROOT)),
                "prompt_chars": prompt_chars,
                "status": "done" if out_path.exists() else "todo",
            }
            for i, batch, bid, prompt_chars, out_path, _ in plans
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    if args.dry_run:
        print(f"\nDry-run complete. Manifest at {manifest_path.relative_to(ROOT)}")
        return 0

    # 5) Run pending batches sequentially.
    print(f"\nExecuting {pending} pending batch(es)…")
    failures: list[tuple[int, str]] = []
    for i, batch, bid, prompt_chars, out_path, prompt in plans:
        if out_path.exists():
            continue
        attempt = 0
        last_err: str | None = None
        while attempt <= args.retries:
            attempt += 1
            t0 = time.time()
            print(f"  [batch {i:3d}/{n_batches}] attempt {attempt} "
                  f"({len(batch)} pages, {prompt_chars:,} chars)…", flush=True)
            try:
                audit = get_ai_response(
                    prompt, model=model, raise_on_error=True
                )
                if not audit or not audit.strip():
                    raise RuntimeError("empty LLM response")
                # Persist immediately.
                header = (
                    "# Wiki Semantic Lint Report (batch)\n\n"
                    f"_Sweep: {sweep_id}, batch {i}/{n_batches}_  \n"
                    f"_Model: `{model}`_  \n"
                    f"_Pages reviewed: {len(batch)}_  \n"
                    f"_Prompt chars: {prompt_chars:,}_\n\n"
                    "**Reviewed pages:**\n\n"
                    + "\n".join(
                        f"- `{p.relative_to(WIKI_DIR).as_posix()}`" for p in batch
                    )
                    + "\n\n---\n\n"
                )
                out_path.write_text(header + audit.strip() + "\n", encoding="utf-8")
                dt = time.time() - t0
                print(f"      done in {dt:.1f}s → {out_path.name}")
                last_err = None
                break
            except Exception as e:
                last_err = repr(e)
                print(f"      error: {last_err}", file=sys.stderr)
                if attempt <= args.retries:
                    time.sleep(args.retry_delay)
        if last_err:
            failures.append((i, last_err))

    # 6) Aggregate everything we have.
    print()
    completed = [
        (i, p, p.read_text(encoding="utf-8"), batch)
        for i, batch, _bid, _pc, p, _pr in plans if p.exists()
    ]
    aggregated = _aggregate(completed)
    AGGREGATE_PATH.write_text(aggregated, encoding="utf-8")
    print(f"Aggregated report → {AGGREGATE_PATH.relative_to(ROOT)} "
          f"({len(completed)} batches included)")
    if failures:
        print(f"\nFAILED batches ({len(failures)}):")
        for idx, err in failures:
            print(f"  batch {idx}: {err}")
        print(
            f"\nRe-run with --sweep-id {sweep_id} to resume the failed batches."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
