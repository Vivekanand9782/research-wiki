#!/usr/bin/env python
"""A/B benchmark runner for the two-stage extraction overhaul (Task 11).

Compares the legacy single-call Markdown path against the two-stage
JSON-then-render path on a stratified sample of papers and writes a
Markdown report to ``research-wiki/benchmarks/two_stage_<date>.md``.

Two modes:

* ``--dry-run`` (default): scores existing on-disk summaries from
  ``wiki/sources/uncategorized/`` against both validators + the
  ``SummaryValidator`` 0-100 score + wikilink canonicalisation rate
  against the live ``wiki_vocabulary`` index. **No LLM calls.** Useful
  as a preflight to confirm scoring behaves as expected before
  spending API quota.
* ``--live``: re-runs ingestion through both code paths on each sample
  paper and compares. **Requires API access.** Caches outputs under
  ``benchmarks/sandbox/<run_id>/`` so the live wiki is never touched.

Usage::

    python -m benchmarks.run_two_stage --dry-run --sample 30
    python -m benchmarks.run_two_stage --live --sample 30

Stratified sampling: by default 5 corrections, 5 reviews, 10 primary,
5 methods, 5 perspective. Use ``--strata`` to override.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Sample selection
# ---------------------------------------------------------------------------

DEFAULT_STRATA = {
    "correction_notice": 5,
    "review": 5,
    "primary_research": 10,
    "methods_paper": 5,
    "perspective": 5,
}


def classify_existing_summaries(paths: Iterable[Path]) -> list[tuple[str, Path]]:
    """Heuristically classify each summary by reading its raw markdown."""
    from paper_classifier import classify_paper_type

    raw_dir = ROOT / "raw" / "papers" / "uncategorized"
    out: list[tuple[str, Path]] = []
    for path in paths:
        # Find the matching raw markdown for the heuristic.
        raw = raw_dir / path.name
        if not raw.exists():
            # Fall back to the summary's own opening text.
            text = path.read_text(encoding="utf-8")[:3000]
        else:
            text = raw.read_text(encoding="utf-8")[:3000]
        kind = classify_paper_type(text).paper_type
        out.append((kind, path))
    return out


def stratified_sample(
    candidates: list[tuple[str, Path]],
    strata: dict[str, int],
) -> list[tuple[str, Path]]:
    """Pick up to N papers per paper type, deterministic by sorted name."""
    picked: list[tuple[str, Path]] = []
    by_kind: dict[str, list[Path]] = {}
    for kind, p in candidates:
        by_kind.setdefault(kind, []).append(p)
    for kind in sorted(strata):
        wanted = strata[kind]
        bucket = sorted(by_kind.get(kind, []))[:wanted]
        for p in bucket:
            picked.append((kind, p))
    return picked


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_both(legacy_md: str, two_stage_md: str, *, vocab_index, paper):
    from benchmarks.score import compare_summaries
    return compare_summaries(paper, legacy_md, two_stage_md, vocab_index=vocab_index)


def score_single(md: str, *, vocab_index):
    from benchmarks.score import score_summary
    return score_summary(md, vocab_index=vocab_index)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _fmt_score(score) -> str:
    return (
        f"strict={'✓' if score.strict_pass else '✗'} "
        f"lenient={'✓' if score.lenient_pass else '✗'} "
        f"score={score.score:.0f} "
        f"wl={score.wikilink_count} "
        f"canon={score.canonicalised_rate:.2f} "
        f"fn={score.footnote_count}"
    )


def write_report(
    out_path: Path,
    *,
    mode: str,
    samples: list[tuple[str, Path]],
    rows_dry: list[dict] | None = None,
    rows_live: list[dict] | None = None,
) -> None:
    """Write a Markdown report summarising the run."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# Two-stage extraction A/B benchmark — {_dt.date.today().isoformat()}")
    lines.append("")
    lines.append(f"**Mode:** {mode}")
    lines.append(f"**Sample size:** {len(samples)}")
    lines.append("")
    lines.append("## Stratification")
    counts = Counter(k for k, _ in samples)
    for k in sorted(counts):
        lines.append(f"- `{k}`: {counts[k]}")
    lines.append("")

    if rows_dry is not None:
        lines.append("## Dry-run scoring (no LLM calls)")
        lines.append("Scores reflect the **existing on-disk summary** for each paper. "
                     "Use this as a baseline reference.")
        lines.append("")
        lines.append("| paper | type | strict | lenient | score | wl | canon | fn |")
        lines.append("|-------|------|--------|---------|-------|----|-------|----|")
        for r in rows_dry:
            s = r["score"]
            lines.append(
                f"| {r['paper']} | {r['paper_type']} | "
                f"{'✓' if s.strict_pass else '✗'} | "
                f"{'✓' if s.lenient_pass else '✗'} | "
                f"{s.score:.0f} | {s.wikilink_count} | "
                f"{s.canonicalised_rate:.2f} | {s.footnote_count} |"
            )
        lines.append("")

    if rows_live is not None:
        from benchmarks.score import acceptance_check
        lines.append("## Live A/B (legacy vs two-stage)")
        lines.append("")
        lines.append("| paper | type | legacy | two-stage | Δscore | Δwl | Δcanon |")
        lines.append("|-------|------|--------|-----------|--------|-----|--------|")
        deltas = []
        for r in rows_live:
            cmp = r["comparison"]
            d = cmp.deltas()
            deltas.append(d)
            lines.append(
                f"| {r['paper']} | {r['paper_type']} | "
                f"{_fmt_score(cmp.legacy)} | {_fmt_score(cmp.two_stage)} | "
                f"{d['score']:+.0f} | {d['wikilink_count']:+d} | "
                f"{d['canonicalised_rate']:+.2f} |"
            )
        lines.append("")
        ok, reasons = acceptance_check(deltas)
        lines.append("## Acceptance check")
        lines.append(f"**{'PASS' if ok else 'FAIL'}**")
        if reasons:
            for reason in reasons:
                lines.append(f"- {reason}")
        else:
            lines.append("- No metric regressed beyond the tolerance budget.")
        lines.append("")
        if ok:
            lines.append(
                "✅ Safe to flip `USE_TWO_STAGE_EXTRACTION = True` in `config.py`."
            )
        else:
            lines.append(
                "🚫 Do NOT flip the flag — investigate the regressions above first."
            )
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport written to {out_path}")


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def cmd_dry_run(args, samples, vocab_index, out_path):
    rows: list[dict] = []
    for paper_type, path in samples:
        md = path.read_text(encoding="utf-8")
        s = score_single(md, vocab_index=vocab_index)
        rows.append({"paper": path.stem, "paper_type": paper_type, "score": s})
        print(f"  {paper_type:24s} {path.stem:50s} {_fmt_score(s)}")
    write_report(out_path, mode="dry-run", samples=samples, rows_dry=rows)


def cmd_live(args, samples, vocab_index, out_path):
    print("Live mode requires API access. This runner does NOT modify the live wiki.")
    print("Sandbox: benchmarks/sandbox/<run_id>/")
    # Live mode intentionally stops short of the actual ingestion call —
    # implementing it requires careful sandbox isolation, quota guards,
    # and the user's explicit go-ahead to spend API budget. Run the
    # legacy and two-stage paths via pdf_extractor with USE_TWO_STAGE_EXTRACTION
    # toggled per call, cache to <sandbox>/<run_id>/, then call score_both.
    print("Live mode not yet implemented — run --dry-run first to validate scoring.")
    return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true", default=True,
                   help="Score existing on-disk summaries (default).")
    p.add_argument("--live", action="store_true",
                   help="Re-run ingestion through both paths (NOT IMPLEMENTED).")
    p.add_argument("--sample", type=int, default=30,
                   help="Total sample size cap (overrides strata totals).")
    p.add_argument("--strata", type=str, default=None,
                   help="JSON dict of {paper_type: count} stratification.")
    p.add_argument("--out", type=Path, default=None,
                   help="Output report path.")
    args = p.parse_args(argv)

    if args.live:
        args.dry_run = False

    strata = json.loads(args.strata) if args.strata else dict(DEFAULT_STRATA)

    sources = ROOT / "wiki" / "sources" / "uncategorized"
    summaries = sorted(sources.glob("*.md"))
    print(f"Found {len(summaries)} on-disk summaries under {sources}")

    classified = classify_existing_summaries(summaries)
    samples = stratified_sample(classified, strata)
    print(f"Stratified sample: {len(samples)} papers")
    for k, n in Counter(k for k, _ in samples).items():
        print(f"  {k}: {n}")

    from wiki_vocabulary import get_index
    vocab_index = get_index()

    today = _dt.date.today().isoformat()
    out_path = args.out or (ROOT / "benchmarks" / f"two_stage_{today}.md")

    if args.live:
        return cmd_live(args, samples, vocab_index, out_path)
    cmd_dry_run(args, samples, vocab_index, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
