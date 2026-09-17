"""ingest_parallel.py — concurrent ingestion of PDFs with fingerprint-based caching.

Inspired by Understand-Anything's parallel ``file-analyzer`` agents (5 concurrent,
20–30 files per batch). Wraps the existing ``ResearchPaperExtractor`` so we don't
have to refactor it: each PDF runs in a worker thread, gated by an
``asyncio.Semaphore``. The genai client's ``TokenBucket`` already enforces
upstream rate limits, so workers will queue politely on 429s.

Cache keys are content fingerprints (sha256 of PDF bytes + extractor version + prompt
version) rather than file paths — so re-OCR'd PDFs and improved prompts both
invalidate correctly. State persists in ``pipeline_state.json``.

Usage::

    python3 ingest_parallel.py                       # default: ../data, 5 workers
    python3 ingest_parallel.py --pdf-folder /path/to/pdfs
    python3 ingest_parallel.py --workers 3 --skip-summary
    python3 ingest_parallel.py --dry-run             # show plan, don't process
    python3 ingest_parallel.py --force               # ignore cache + existing .md
"""
from __future__ import annotations

import argparse
import asyncio
import functools
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from pdf_extractor import ResearchPaperExtractor
from pipeline_state import PipelineState, fingerprint_file

# Bump these to bust the cache after a prompt or extractor change.
EXTRACTOR_VERSION = "extractor:v1"
SUMMARY_PROMPT_VERSION = "summary-prompt:v1"

DEFAULT_PDF_FOLDER = Path(__file__).resolve().parent.parent / "data"
DEFAULT_OUTPUT_FOLDER = Path(__file__).resolve().parent / "wiki" / "sources"
DEFAULT_TEXT_FOLDER = Path(__file__).resolve().parent / "raw" / "papers"


def _topic_for(pdf_path: Path, root: Path) -> str:
    if pdf_path.parent == root:
        return "uncategorized" if root.name == "data" else root.name
    return pdf_path.parent.name


def _existing_output(extractor: ResearchPaperExtractor, pdf_path: Path) -> Path:
    """Where the extractor would land the markdown for this PDF."""
    return extractor.output_folder / "uncategorized" / f"{pdf_path.stem}.md"


def _fingerprint(pdf_path: Path, skip_summary: bool) -> str:
    tokens = [EXTRACTOR_VERSION]
    if not skip_summary:
        tokens.append(SUMMARY_PROMPT_VERSION)
    return fingerprint_file(pdf_path, *tokens)


def _process_one(extractor: ResearchPaperExtractor, pdf_path: Path,
                 skip_summary: bool, skip_pageindex: bool = False) -> tuple[str, dict | None]:
    """Synchronous worker — called via run_in_executor."""
    topic = _topic_for(pdf_path, extractor.pdf_folder)
    try:
        data = extractor.process_single_pdf(pdf_path, topic, skip_summary=skip_summary, skip_pageindex=skip_pageindex)
    except Exception as exc:
        return ("error", {"pdf": str(pdf_path), "error": str(exc)})
    if not data or data.get("extraction_method") == "failed":
        details = {
            "pdf": str(pdf_path),
            "error": (data or {}).get("error") or "paper processing failed",
        }
        if (data or {}).get("retryable"):
            details["retryable"] = True
            return ("provider_unavailable", details)
        if (data or {}).get("skipped_no_text"):
            # Scanned/junk PDF with no extractable text layer — not a failure.
            return ("no_text", data)
        # A failed paper is an error for process exit status; silently exiting 0
        # made large batches look successful even when every paper failed.
        return ("error", details)
    if not skip_summary and "ai_structured_summary" in data:
        output_topic = str(data.get("topic_folder") or topic)
        md_file = extractor.output_folder / output_topic / f"{pdf_path.stem}.md"
        try:
            extractor.update_wiki_indexes(pdf_path.stem, md_file, data["ai_structured_summary"])
        except Exception as exc:
            data.setdefault("warnings", []).append(f"index-update-failed: {exc}")
    return ("ok", data)


async def _run_all(pdfs: list[Path], extractor: ResearchPaperExtractor,
                    state: PipelineState, workers: int, skip_summary: bool,
                    force: bool, dry_run: bool, skip_pageindex: bool = False) -> dict:
    """Schedule PDFs, stopping cleanly when the shared AI provider is down."""
    sem = asyncio.Semaphore(workers)
    provider_unavailable = asyncio.Event()
    loop = asyncio.get_running_loop()
    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ingest")
    results = {"ok": 0, "failed": 0, "error": 0, "skipped_cache": 0,
               "skipped_existing": 0, "skipped_no_text": 0,
               "deferred_provider": 0, "errors": []}
    started = time.monotonic()

    async def _bounded(idx: int, pdf_path: Path) -> None:
        if provider_unavailable.is_set():
            results["deferred_provider"] += 1
            return

        # Pre-flight: skip if we have a cached fingerprint and not forced.
        fp = _fingerprint(pdf_path, skip_summary)
        if not force:
            if state.is_done("ingest", fp):
                results["skipped_cache"] += 1
                return
            existing = _existing_output(extractor, pdf_path)
            if existing.exists():
                # Path-based skip from the existing pipeline — promote it into the cache
                # so subsequent runs are even faster.
                state.mark_done("ingest", fp, payload={"output": str(existing.relative_to(extractor.output_folder.parent))})
                results["skipped_existing"] += 1
                return
        if dry_run:
            print(f"  [{idx + 1:>4}/{len(pdfs)}] would process {pdf_path.name}")
            return
        async with sem:
            # Tasks may have queued on the semaphore before another worker
            # diagnosed a provider outage. Leave them uncached for the next run.
            if provider_unavailable.is_set():
                results["deferred_provider"] += 1
                return

            print(f"  [{idx + 1:>4}/{len(pdfs)}] start {pdf_path.name}")
            t0 = time.monotonic()
            status, payload = await loop.run_in_executor(
                pool, functools.partial(_process_one, extractor, pdf_path, skip_summary, skip_pageindex)
            )
            dt = time.monotonic() - t0
            if status == "ok":
                state.mark_done("ingest", fp, payload={
                    "output": payload.get("md_file") or payload.get("output"),
                    "topic": _topic_for(pdf_path, extractor.pdf_folder),
                    "duration_s": round(dt, 1),
                })
                results["ok"] += 1
                tree_note = f" [tree: {Path(payload['pageindex_tree']).name}]" if (payload and payload.get("pageindex_tree")) else ""
                print(f"  [{idx + 1:>4}/{len(pdfs)}] ✓     {pdf_path.name}  ({dt:.1f}s){tree_note}")
            elif status == "failed":
                results["failed"] += 1
                print(f"  [{idx + 1:>4}/{len(pdfs)}] ⚠  failed {pdf_path.name}")
            elif status == "no_text":
                # Scanned/junk PDF: nothing to summarise. Cache the content
                # fingerprint so later runs skip it quietly (fingerprint is
                # content-based, so replacing the file retriggers processing).
                state.mark_done("ingest", fp, payload={
                    "topic": _topic_for(pdf_path, extractor.pdf_folder),
                    "skipped_no_text": True,
                })
                results["skipped_no_text"] += 1
                print(f"  [{idx + 1:>4}/{len(pdfs)}] ⤷ skip  {pdf_path.name} (no extractable text)")
            else:
                results["error"] += 1
                results["errors"].append(payload)
                print(f"  [{idx + 1:>4}/{len(pdfs)}] ✗  error  {pdf_path.name}: {payload['error']}")
                if status == "provider_unavailable" and not provider_unavailable.is_set():
                    provider_unavailable.set()
                    print("  [!] General Compute is unavailable; deferring all remaining "
                          "uncached PDFs for a safe resume.")

    try:
        await asyncio.gather(*(_bounded(i, p) for i, p in enumerate(pdfs)))
    finally:
        pool.shutdown(wait=True)
        if not dry_run:
            state.save()

    results["wall_seconds"] = round(time.monotonic() - started, 1)
    return results


# Phase token for the deterministic raw-extraction step. Bump this when the
# extractor version or the output format changes — that busts the cache and
# triggers re-extraction even on PDFs whose .md file already exists.
#
# v1: raw OpenDataLoader layout-dump JSON, full markdown with pipe-tables and image embeds.
# v2: post-processed slim JSON ({tables, equations} only, structure preserved as
#     2D arrays), markdown rewritten with {{TAB_n_<paper>}}/{{EQ_n_<paper>}}
#     placeholders, image embeds stripped.
# v3: pymupdf4llm primary with Datalab fallback; markdown only, no JSON sidecar.
RAW_PREPASS_VERSION = "raw-prepass:v3"


def _bulk_raw_prepass(extractor: ResearchPaperExtractor, pdfs: list[Path],
                     batch_workers: int,
                     force: bool, state: PipelineState | None = None,
                     skip_pageindex: bool = False) -> dict:
    """Extract raw markdown for all PDFs before the AI worker pool starts.

    Delegates to ``ResearchPaperExtractor._extract_raw_text``, which is the
    single PDF→markdown implementation: pymupdf4llm locally, with a per-PDF
    Datalab cloud fallback when the local parse fails.
    Also synchronizes PageIndex hierarchical trees unless skip_pageindex is set.
    """
    plan = []
    for pdf_path in pdfs:
        if pdf_path.parent == extractor.pdf_folder:
            topic = "uncategorized" if extractor.pdf_folder.name == "data" else extractor.pdf_folder.name
        else:
            topic = pdf_path.parent.name
        text_folder = extractor.text_folder / topic
        text_folder.mkdir(parents=True, exist_ok=True)
        text_path = text_folder / f"{pdf_path.stem}.md"

        try:
            fp = fingerprint_file(pdf_path, RAW_PREPASS_VERSION)
        except Exception:
            fp = None

        cache_hit = False
        if not force and state is not None and fp is not None:
            cached = state.get("raw_prepass", fp)
            if cached and text_path.exists():
                cache_hit = True

        if cache_hit:
            continue

        need_text = force or not text_path.exists()

        if not need_text:
            if state is not None and fp is not None:
                state.mark_done("raw_prepass", fp, payload={
                    "text": str(text_path),
                    "promoted": True,
                })
            continue

        plan.append((pdf_path, text_path, fp))

    summary = {"prepass_total": len(pdfs), "prepass_to_extract": len(plan),
               "prepass_ok": 0, "prepass_failed": 0,
               "prepass_seconds": 0.0}
    if not plan:
        return summary

    print(f"\n📦 Raw pre-pass: {len(plan)} PDFs (pymupdf4llm, Datalab fallback)\n")
    t0 = time.monotonic()

    # Extraction runs in a single bounded pool. The previous nested one-thread
    # executor did not enforce its advertised timeout: leaving its context
    # waited for the running thread anyway, while doubling thread creation for
    # every PDF.
    from concurrent.futures import ThreadPoolExecutor as _TPE

    def _do_extract(item):
        pdf_path, text_path, fp = item
        t_start = time.monotonic()
        # ``_extract_raw_text`` swallows its own failures and returns "" so a
        # single bad PDF never aborts the batch.
        md = extractor._extract_raw_text(pdf_path, None, text_path)
        elapsed = time.monotonic() - t_start
        if md:
            print(f"  ✓ pre-pass: {pdf_path.name} ({elapsed:.1f}s)")
            if not skip_pageindex:
                try:
                    from pageindex_ingest_hook import hook_pageindex_index
                    hook_pageindex_index(pdf_path, md_path=text_path)
                except Exception:
                    pass
        else:
            print(f"  ✗ pre-pass failed ({elapsed:.1f}s): {pdf_path.name}")
        return (pdf_path, text_path, fp, bool(md))

    with _TPE(max_workers=min(batch_workers, len(plan))) as ex:
        futures = [ex.submit(_do_extract, item) for item in plan]
        for f in futures:
            pdf_path, text_path, fp, ok = f.result()
            if not ok:
                summary["prepass_failed"] += 1
                continue
            summary["prepass_ok"] += 1
            if state is not None and fp is not None:
                state.mark_done("raw_prepass", fp, payload={"text": str(text_path)})

    if state is not None:
        try:
            state.save()
        except Exception:
            pass

    summary["prepass_seconds"] = round(time.monotonic() - t0, 1)
    print(f"\n✅ Raw pre-pass done: {summary['prepass_ok']} ok, "
          f"{summary['prepass_failed']} failed, {summary['prepass_seconds']}s wall.\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-folder", default=str(DEFAULT_PDF_FOLDER),
                        help=f"Root folder containing PDFs (default {DEFAULT_PDF_FOLDER})")
    parser.add_argument("--output-folder", default=str(DEFAULT_OUTPUT_FOLDER),
                        help="Where extracted markdown lands (default wiki/sources)")
    parser.add_argument("--text-folder", default=str(DEFAULT_TEXT_FOLDER),
                        help="Where raw extracted markdown lands (default raw/papers)")
    parser.add_argument("--workers", type=int, default=7,
                        help="Max concurrent PDFs in the AI phase (default 7; "
                             "7 workers × 7 GC keys = 1 worker/key, well within "
                             "1M TPM / 100 RPM per key limits)")
    parser.add_argument("--skip-summary", action="store_true",
                        help="Run extraction phases only; skip the LLM summary phase")
    parser.add_argument("--force", action="store_true",
                        help="Ignore the fingerprint cache and existing markdown files")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process at most N PDFs (0 = no limit). Useful for smoke tests.")
    parser.add_argument("--dry-run", action="store_true",
                        help="List what would be processed without doing the work")
    parser.add_argument("--no-rollup", action="store_true",
                        help="Skip the automatic seed-page summary rollup that runs after ingest")
    # Bulk pre-pass tuning. Defaults are tuned for a ~10-core machine.
    parser.add_argument("--skip-prepass", action="store_true",
                        help="Skip the bulk raw pre-pass. "
                             "Per-PDF extraction will then happen inline in each worker, which "
                             "is significantly slower on cold caches.")
    parser.add_argument("--batch-workers", type=int, default=12,
                        help="Max concurrent extractions in the pre-pass (default 12; "
                             "cap at 12 workers per taste guidance).")
    parser.add_argument("--skip-pageindex", action="store_true",
                        help="Skip PageIndex hierarchical tree generation")
    parser.add_argument("pdf_files", nargs="*", default=[],
                        help="Specific PDF files to process (overrides --pdf-folder directory scan)")
    args = parser.parse_args(argv)

    if args.pdf_files:
        pdfs = [Path(f).expanduser().resolve() for f in args.pdf_files]
        invalid = [p for p in pdfs if not p.exists() or p.suffix.lower() != ".pdf"]
        if invalid:
            print(f"ERROR: Invalid or missing PDF file(s): {[str(p) for p in invalid]}", file=sys.stderr)
            return 2
        pdf_root = Path(args.pdf_folder).expanduser().resolve()
    else:
        pdf_root = Path(args.pdf_folder).expanduser().resolve()
        if not pdf_root.exists():
            print(f"ERROR: pdf folder not found: {pdf_root}", file=sys.stderr)
            return 2
        pdfs = sorted(pdf_root.rglob("*.pdf"))
        if args.limit > 0:
            pdfs = pdfs[:args.limit]

    if not pdfs:
        if args.pdf_files:
            print("No valid PDFs specified.")
        else:
            print(f"No PDFs under {pdf_root}")
        return 0

    extractor = ResearchPaperExtractor(
        pdf_folder=str(pdf_root),
        output_folder=args.output_folder,
        text_folder=args.text_folder,
    )

    state = PipelineState()
    print(f"PDFs found     : {len(pdfs)}")
    print(f"Output folder  : {args.output_folder}")
    print(f"Workers (AI)   : {args.workers}")
    print(f"Force          : {args.force}")
    print(f"Skip summary   : {args.skip_summary}")
    print(f"Skip pageindex : {args.skip_pageindex}")
    print(f"Skip prepass   : {args.skip_prepass}")
    if not args.skip_prepass:
        print(f"Prepass        : pymupdf4llm (Datalab fallback), workers={args.batch_workers}")
    print(f"State file     : {state.path}")
    print(f"Cached steps   : {state.stats() or '(empty)'}")
    print()

    # Phase 1: bulk-extract raw markdown via the shared extractor
    # (pymupdf4llm, Datalab fallback). After this returns, every PDF has a .md
    # file, so the per-PDF AI worker pool below skips extraction and just does
    # summary + seed pages.
    prepass_summary = {"prepass_total": 0, "prepass_to_extract": 0,
                       "prepass_ok": 0, "prepass_failed": 0, "prepass_seconds": 0.0}
    if not args.skip_prepass and not args.dry_run:
        prepass_summary = _bulk_raw_prepass(
            extractor=extractor, pdfs=pdfs,
            batch_workers=args.batch_workers,
            force=args.force,
            state=state,
            skip_pageindex=args.skip_pageindex,
        )

    results = asyncio.run(_run_all(
        pdfs, extractor, state, args.workers, args.skip_summary, args.force, args.dry_run, args.skip_pageindex
    ))

    print()
    print("=" * 50)
    print(" PARALLEL INGEST SUMMARY")
    print("=" * 50)
    print(f" Total PDFs       : {len(pdfs)}")
    print(f" Pre-pass extracted: {prepass_summary['prepass_ok']}/{prepass_summary['prepass_to_extract']} "
          f"({prepass_summary['prepass_seconds']}s)")
    print(f" Processed (ok)   : {results['ok']}")
    print(f" Failed           : {results['failed']}")
    print(f" Errors           : {results['error']}")
    print(f" Deferred (provider): {results['deferred_provider']}")
    print(f" Skipped (cache)  : {results['skipped_cache']}")
    print(f" Skipped (exists) : {results['skipped_existing']}")
    print(f" Skipped (no text): {results['skipped_no_text']}")
    print(f" PageIndex synced : {'Disabled (--skip-pageindex)' if args.skip_pageindex else 'Enabled (PageIndex/extracted_trees/)'}")
    print(f" Wall time        : {results['wall_seconds']}s")
    if results["errors"]:
        print("\nFirst errors:")
        for e in results["errors"][:5]:
            print(f"  - {Path(e['pdf']).name}: {e['error']}")
    print("=" * 50)

    # Auto-rollup: refresh the **Summary** of seed pages this run touched, so an
    # entity newly cited by this batch gets its cross-source summary updated
    # without a separate command. Fingerprint-gated in run_rollup, so only pages
    # whose findings actually changed cost an LLM call.
    if (not args.dry_run and not args.skip_summary and not args.no_rollup
            and results["ok"] > 0):
        seed_pages = [p for p in getattr(extractor, "_run_touched_files", set())
                      if p.parent.name in ("entities", "concepts")]
        if seed_pages:
            print(f"\n🔄 Rolling up {len(seed_pages)} touched seed pages (only those with new findings)...")
            from rollup_summaries import run_rollup
            r = run_rollup(apply=True, workers=args.workers, pages=seed_pages)
            print(f" Rolled up {r['done']}; {r['skipped']} unchanged; {r['failed']} failed.")

    return 0 if results["error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
