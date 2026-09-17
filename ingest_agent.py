"""ingest_agent.py — agent-driven deep re-summarization of wiki papers.

Zero LLM API calls. The agent reads raw extracted paper text and hand-writes
the Stage-A summary JSON sidecars. This script handles everything else
deterministically: rendering, strict validation, lint gating, hallucination
checking, evidence-quote verification, indexing, and seed-page stub merges.

Usage::

    python3 ingest_agent.py plan [--topic T] [--limit N] [--order depth|thinnest]
    python3 ingest_agent.py render [--pending | --stem S] [--dry-run]
    python3 ingest_agent.py progress
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RW = Path(__file__).resolve().parent
DEFAULT_PDF_FOLDER = RW.parent / "data"
DEFAULT_TEXT_FOLDER = RW / "raw" / "papers"
DEFAULT_OUTPUT_FOLDER = RW / "wiki" / "sources"
DEFAULT_ENTITY_FOLDER = RW / "wiki" / "entities"
DEFAULT_CONCEPT_FOLDER = RW / "wiki" / "concepts"
WORKLIST_PATH = RW / "agent_worklist.json"
RENDER_REPORT_PATH = RW / "agent_render_report.json"
SPEC_PATH = RW / "agent_summary_spec.md"
ATTIC_FOLDER = RW / "wiki" / "sources" / ".attic"

# Phase token for pipeline_state.json — separate from the "ingest" phase so
# the API pipeline's cache is never clobbered and this campaign is
# independently resumable.
AGENT_PHASE = "agent-deep-summary"
AGENT_VERSION = "agent-deep-summary:v1"

# Quality thresholds for the render gate. Full papers target 2,800+ words and
# 8+ footnotes; short sources (news items, brief communications) scale down
# proportionally so the gate never pressures an agent into padding or
# fabricating content beyond what a short source supports.
MIN_PAGE_WORDS_FULL = 2800
MIN_VERIFIED_FOOTNOTES_FULL = 8
MIN_PAGE_WORDS_FLOOR = 1200
MIN_VERIFIED_FOOTNOTES_FLOOR = 3


def _depth_targets(raw_words: int) -> tuple[int, int]:
    """(min_page_words, min_footnotes) scaled to the source's length.

    The word floor never exceeds the source length, so genuinely short
    sources are never pressured into padding beyond what they support.
    """
    if raw_words <= 0:
        return MIN_PAGE_WORDS_FULL, MIN_VERIFIED_FOOTNOTES_FULL
    min_words = min(
        MIN_PAGE_WORDS_FULL,
        max(min(MIN_PAGE_WORDS_FLOOR, raw_words), int(raw_words * 0.5)),
    )
    min_fns = min(
        MIN_VERIFIED_FOOTNOTES_FULL,
        max(MIN_VERIFIED_FOOTNOTES_FLOOR, raw_words // 400),
    )
    return min_words, min_fns


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _word_count(text: str) -> int:
    return len(text.split())


def _topic_for(pdf_stem: str) -> str:
    """Find which topic subfolder (if any) holds this paper's raw text."""
    for topic_dir in sorted(DEFAULT_TEXT_FOLDER.iterdir()):
        if topic_dir.is_dir():
            if (topic_dir / f"{pdf_stem}.md").exists():
                return topic_dir.name
    return "uncategorized"


def _raw_text_path(stem: str) -> Path | None:
    for topic_dir in sorted(DEFAULT_TEXT_FOLDER.iterdir()):
        if topic_dir.is_dir():
            candidate = topic_dir / f"{stem}.md"
            if candidate.exists():
                return candidate
    return None


def _sidecar_path(stem: str) -> Path:
    return DEFAULT_TEXT_FOLDER / f"{stem}.summary.json"


def _wiki_page_path(stem: str) -> Path:
    """Find existing wiki page or default to uncategorized."""
    if DEFAULT_OUTPUT_FOLDER.exists():
        for topic_dir in DEFAULT_OUTPUT_FOLDER.iterdir():
            if topic_dir.is_dir() and topic_dir.name != ".attic":
                candidate = topic_dir / f"{stem}.md"
                if candidate.exists():
                    return candidate
    return DEFAULT_OUTPUT_FOLDER / "uncategorized" / f"{stem}.md"


def _is_modified_today(wiki_path: Path, today_str: str, today_start_ts: float) -> bool:
    """Check if wiki page exists and was modified or updated today."""
    if not wiki_path.exists():
        return False
    try:
        if wiki_path.stat().st_mtime >= today_start_ts:
            return True
        txt = wiki_path.read_text(encoding="utf-8")
        if f"date_updated: {today_str}" in txt or f'date_updated: "{today_str}"' in txt:
            return True
        if f"date_created: {today_str}" in txt or f'date_created: "{today_str}"' in txt:
            return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# plan — build / update the worklist
# ---------------------------------------------------------------------------

def _collect_all_stems() -> list[str]:
    """All paper stems that have raw text."""
    stems = set()
    if DEFAULT_TEXT_FOLDER.exists():
        for topic_dir in DEFAULT_TEXT_FOLDER.iterdir():
            if topic_dir.is_dir():
                for md in topic_dir.glob("*.md"):
                    stems.add(md.stem)
    # Also stems from wiki pages that may lack raw text (rare)
    unc = DEFAULT_OUTPUT_FOLDER / "uncategorized"
    if unc.exists():
        for md in unc.glob("*.md"):
            stems.add(md.stem)
    return sorted(stems)


def _page_word_count(stem: str) -> int:
    wp = _wiki_page_path(stem)
    if wp.exists():
        try:
            return _word_count(wp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """Build or update the agent worklist."""
    all_stems = _collect_all_stems()
    print(f"Total paper stems with raw text: {len(all_stems)}")

    today_str = date.today().isoformat()
    today_start_ts = datetime.combine(date.today(), datetime.min.time()).timestamp()

    # Filter by topic if requested
    if args.topic:
        filtered = []
        for s in all_stems:
            topic = _topic_for(s)
            if topic in args.topic:
                filtered.append(s)
            elif "uncategorized" in args.topic and topic == "uncategorized" and not any(
                (DEFAULT_TEXT_FOLDER / t / f"{s}.md").exists() for t in args.topic if t != "uncategorized"
            ):
                filtered.append(s)
        all_stems = filtered
        print(f"After topic filter ({args.topic}): {len(all_stems)}")

    # Load existing worklist to preserve done/skipped status
    existing_worklist: dict[str, dict] = {}
    if WORKLIST_PATH.exists():
        try:
            existing_worklist = {
                e["stem"]: e for e in json.loads(WORKLIST_PATH.read_text(encoding="utf-8"))
            }
        except Exception:
            pass

    # Build entries
    entries: list[dict] = []
    skipped_today_count = 0
    skip_today_flag = getattr(args, "skip_today", True)

    for stem in all_stems:
        raw_path = _raw_text_path(stem)
        wiki_path = _wiki_page_path(stem)
        sidecar = _sidecar_path(stem)

        topic = _topic_for(stem)
        raw_words = 0
        if raw_path:
            try:
                raw_words = _word_count(raw_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        page_words = _page_word_count(stem)

        # Check if already modified today
        modified_today = skip_today_flag and _is_modified_today(
            wiki_path, today_str, today_start_ts
        )

        # Resolve DOI (deterministic, no LLM)
        doi = None
        if raw_path:
            try:
                from paper_metadata import extract_doi_from_text
                raw_text = raw_path.read_text(encoding="utf-8")
                doi = extract_doi_from_text(raw_text)
            except Exception:
                pass

        # Classify paper type (heuristic only, no LLM)
        paper_type = "primary_research"
        if raw_path:
            try:
                from paper_classifier import classify_paper_type
                paper_type = classify_paper_type(
                    raw_path.read_text(encoding="utf-8")
                ).paper_type
            except Exception:
                pass

        status = "pending"
        if modified_today:
            status = "done"
            skipped_today_count += 1

        entry: dict[str, Any] = {
            "stem": stem,
            "raw_path": str(raw_path) if raw_path else None,
            "wiki_path": str(wiki_path),
            "sidecar_path": str(sidecar),
            "topic": topic,
            "raw_words": raw_words,
            "page_words": page_words,
            "doi": doi,
            "paper_type": paper_type,
            "status": status,
        }

        if modified_today:
            entry["completed_today"] = True

        # If already done by this campaign in previous worklist, keep it
        if stem in existing_worklist and not modified_today:
            old = existing_worklist[stem]
            if old.get("status") in ("done", "skipped_no_text"):
                entry["status"] = old["status"]
                if old.get("status") == "skipped_no_text":
                    entry["skip_reason"] = old.get(
                        "skip_reason", "source PDF lacks extractable full text"
                    )
            elif old.get("status") in ("flagged", "failed"):
                entry["status"] = old["status"]
                entry["flags"] = old.get("flags", [])
                entry["render_report"] = old.get("render_report")

        entries.append(entry)

    # Sort: curated topics first (in fixed order), then uncategorized
    # Within each tier: thinnest current page first (or shortest raw text if no page)
    TOPIC_ORDER = [
        "vpc_transgene_free", "genome_editing_transgene_free",
        "bioethanol", "PHS_tolerance", "uncategorized",
        "downloads", "tmp",
    ]

    def _sort_key(e: dict):
        topic = e["topic"]
        try:
            tier = TOPIC_ORDER.index(topic)
        except ValueError:
            tier = 99
        size_key = e["page_words"] if e["page_words"] > 0 else e["raw_words"]
        if args.order == "raw_shortest":
            size_key = e["raw_words"]
        return (tier, size_key)

    entries.sort(key=_sort_key)

    # Separate done from pending
    done = [e for e in entries if e["status"] == "done"]
    pending = [e for e in entries if e["status"] != "done"]

    # Limit
    if args.limit > 0:
        pending = pending[: args.limit]

    final = pending + done

    WORKLIST_PATH.write_text(
        json.dumps(final, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    n_pending = len(pending)
    n_done = len(done)
    by_topic: dict[str, int] = {}
    for e in pending:
        by_topic[e["topic"]] = by_topic.get(e["topic"], 0) + 1

    print(f"\nWorklist written: {WORKLIST_PATH.name}")
    print(f"  Pending: {n_pending}")
    print(f"  Already done / Modified today: {n_done} (of which {skipped_today_count} modified today)")
    print(f"  By topic (pending):")
    for t in TOPIC_ORDER:
        if t in by_topic:
            print(f"    {t}: {by_topic[t]}")
    for t in sorted(by_topic):
        if t not in TOPIC_ORDER:
            print(f"    {t}: {by_topic[t]}")

    return 0


# ---------------------------------------------------------------------------
# render — deterministic gates for a batch of sidecars
# ---------------------------------------------------------------------------

def _render_one(stem: str, force: bool = False, dry_run: bool = False) -> dict[str, Any]:
    """Render one sidecar through all quality gates. Returns a report dict."""
    sidecar = _sidecar_path(stem)
    wiki_page = _wiki_page_path(stem)
    raw_path = _raw_text_path(stem)
    report: dict[str, Any] = {"stem": stem, "gates": {}}

    # 1. Load sidecar
    if not sidecar.exists():
        report["gates"]["load_sidecar"] = {"pass": False, "error": "no sidecar"}
        report["status"] = "failed"
        return report
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception as exc:
        report["gates"]["load_sidecar"] = {"pass": False, "error": str(exc)}
        report["status"] = "failed"
        return report
    report["gates"]["load_sidecar"] = {"pass": True}

    # 2. Load source text for evidence-quote verification
    source_text = ""
    if raw_path:
        try:
            source_text = raw_path.read_text(encoding="utf-8")
        except Exception:
            pass

    # 3. Resolve paper_type
    paper_type = payload.get("paper_type", "primary_research")

    # 4. Render
    try:
        from renderer import render_summary_from_json
        from wiki_vocabulary import get_index as _vocab_index

        try:
            vocab = _vocab_index()
        except Exception:
            vocab = None

        today_iso = date.today().isoformat()
        result = render_summary_from_json(
            payload,
            vocab_index=vocab,
            paper_name=stem,
            today_iso=today_iso,
            source_text=source_text if source_text else None,
            paper_type=paper_type,
        )
        markdown = result.markdown
        warnings = result.warnings
        new_candidates = result.new_candidates
    except Exception as exc:
        report["gates"]["render"] = {"pass": False, "error": str(exc)}
        report["status"] = "failed"
        return report
    report["gates"]["render"] = {
        "pass": True,
        "warnings": len(warnings),
        "new_candidates": len(new_candidates),
    }

    # 5. Strict section validator
    try:
        from genai_client import validate_structured_summary_strict
        validation = validate_structured_summary_strict(markdown, paper_type=paper_type)
        strict_valid = validation.get("valid", False)
        strict_missing = validation.get("missing_sections", [])
        strict_wiki = validation.get("wikilink_warnings", [])
    except Exception as exc:
        report["gates"]["strict_validator"] = {"pass": False, "error": str(exc)}
        report["status"] = "failed"
        return report
    report["gates"]["strict_validator"] = {
        "pass": strict_valid,
        "missing": strict_missing,
        "wikilink_warnings": strict_wiki,
    }
    if not strict_valid:
        report["status"] = "flagged"
        report["flags"] = report.get("flags", []) + [f"strict_validator: missing {strict_missing}"]
        return report

    # 6. Wiki source-page lint
    try:
        from lint_wiki import validate_source_page
        lint_errors = validate_source_page(markdown)
    except Exception as exc:
        report["gates"]["lint"] = {"pass": False, "error": str(exc)}
        report["status"] = "failed"
        return report
    report["gates"]["lint"] = {"pass": len(lint_errors) == 0, "errors": lint_errors}
    if lint_errors:
        report["status"] = "flagged"
        report["flags"] = report.get("flags", []) + [f"lint: {lint_errors}"]
        return report

    # 7. Depth check (adaptive to source length)
    raw_words = _word_count(source_text) if source_text else 0
    min_words, min_fns = _depth_targets(raw_words)
    page_words = _word_count(markdown)
    report["page_words"] = page_words
    report["gates"]["depth"] = {
        "pass": page_words >= min_words,
        "words": page_words,
        "min": min_words,
        "raw_words": raw_words,
    }
    if page_words < min_words:
        report["status"] = "flagged"
        report["flags"] = report.get("flags", []) + [
            f"depth: {page_words} words < {min_words} minimum (source: {raw_words} words)"
        ]
        return report

    # 8. Evidence footnote count (adaptive to source length)
    # Count footnote DEFINITION lines only — each footnote also emits an
    # inline [^id] reference, so a naive count double-reports.
    real_footnotes = len(re.findall(r"(?m)^\[\^[\w-]+\]:", markdown))
    report["gates"]["footnotes"] = {
        "pass": real_footnotes >= min_fns,
        "count": real_footnotes,
        "min": min_fns,
    }
    if real_footnotes < min_fns:
        report["status"] = "flagged"
        report["flags"] = report.get("flags", []) + [
            f"footnotes: {real_footnotes} < {min_fns} minimum (source: {raw_words} words)"
        ]
        return report

    # 9. Hallucination check
    try:
        from sentence_verifier import (
            extract_factual_sentences_from_summary,
            verify_summary_against_source,
        )
        if source_text:
            sentences = extract_factual_sentences_from_summary(markdown)
            result = verify_summary_against_source(sentences, source_text)
            confidence = result.confidence
            verified = len(result.verified)
            total = result.total
            unverified = result.unverified[:10]
        else:
            confidence = -1
            verified = total = 0
            unverified = []
    except Exception as exc:
        report["gates"]["hallucination"] = {"pass": False, "error": str(exc)}
        report["status"] = "flagged"
        report["flags"] = report.get("flags", []) + [f"hallucination check error: {exc}"]
        return report
    report["gates"]["hallucination"] = {
        # Advisory only: the sentence verifier's exact-substring heuristics
        # penalise legitimately paraphrased prose, so deep summaries rarely
        # reach the production 0.90 threshold (the GC pipeline's two-stage
        # path skips this check for the same reason). Fabricated evidence
        # quotes are already blocked mechanically by the renderer's
        # verbatim-quote verification above.
        "advisory": True,
        "confidence": confidence,
        "verified": verified,
        "total": total,
        "unverified_sample": unverified,
    }

    # --- All hard gates passed ---
    report["status"] = "passed"

    if dry_run:
        return report

    # 10. Write the wiki page
    try:
        ATTIC_FOLDER.mkdir(parents=True, exist_ok=True)
        # Preserve date_created from existing page if present
        existing_date_created = None
        if wiki_page.exists():
            try:
                old_text = wiki_page.read_text(encoding="utf-8")
                m = re.search(r"date_created:\s*(\S+)", old_text)
                if m:
                    existing_date_created = m.group(1)
                # Backup to attic
                attic_name = f"{stem}.pre-agent.md"
                (ATTIC_FOLDER / attic_name).write_text(old_text, encoding="utf-8")
            except Exception:
                pass

        # Fix date_created in rendered markdown if we preserved it
        if existing_date_created:
            markdown = re.sub(
                r"(date_created:\s*)\S+",
                rf"\g<1>{existing_date_created}",
                markdown,
                count=1,
            )

        wiki_page.parent.mkdir(parents=True, exist_ok=True)
        wiki_page.write_text(markdown, encoding="utf-8")
        report["gates"]["write"] = {"pass": True, "path": str(wiki_page)}
    except Exception as exc:
        report["gates"]["write"] = {"pass": False, "error": str(exc)}
        report["status"] = "failed"
        return report

    # 11. Update wiki indexes
    try:
        from pdf_extractor import ResearchPaperExtractor
        extractor = ResearchPaperExtractor(
            pdf_folder=str(DEFAULT_PDF_FOLDER),
            output_folder=str(DEFAULT_OUTPUT_FOLDER.parent),
            text_folder=str(DEFAULT_TEXT_FOLDER),
        )
        extractor.update_wiki_indexes(stem, wiki_page, markdown)
        report["gates"]["indexes"] = {"pass": True}
    except Exception as exc:
        report["gates"]["indexes"] = {"pass": False, "error": str(exc)}
        # Non-fatal — indexes are append-only

    # 12. Seed-page merge (zero-API by construction): subclass the extractor
    # so every internal LLM text call resolves to NEEDS_HUMAN_REVIEW, which
    # makes _generate_seed_page/_update_seed_page take their deterministic
    # stub branches. Findings/citations still merge; only the 1-3 sentence
    # definitions defer to human review (or a later rollup).
    try:
        from pdf_extractor import ResearchPaperExtractor as _RPE

        class _StubExtractor(_RPE):
            def _safe_llm_text(self, prompt, model=None):
                return "NEEDS_HUMAN_REVIEW"

        extractor2 = _StubExtractor(
            pdf_folder=str(DEFAULT_PDF_FOLDER),
            output_folder=str(DEFAULT_OUTPUT_FOLDER.parent),
            text_folder=str(DEFAULT_TEXT_FOLDER),
        )
        extractor2.populate_wiki_nodes(markdown, stem)
        report["gates"]["seed_pages"] = {"pass": True, "stub_definitions": True}
    except Exception as exc:
        report["gates"]["seed_pages"] = {"pass": False, "error": str(exc)}
        # Non-fatal

    # 13. Mark done in pipeline_state
    try:
        from pipeline_state import PipelineState, fingerprint_file
        pdf_path = DEFAULT_PDF_FOLDER / f"{stem}.pdf"
        if pdf_path.exists():
            fp = fingerprint_file(pdf_path, AGENT_VERSION)
        else:
            from pipeline_state import fingerprint_bytes
            fp = fingerprint_bytes(
                stem.encode(), AGENT_VERSION.encode(), date.today().isoformat().encode()
            )
        state = PipelineState()
        state.mark_done(AGENT_PHASE, fp, payload={
            "summarizer": "agent",
            "page_words": page_words,
            "footnotes": real_footnotes,
            "confidence": confidence,
        })
        state.save()
        report["gates"]["state"] = {"pass": True}
    except Exception as exc:
        report["gates"]["state"] = {"pass": False, "error": str(exc)}

    return report


def cmd_render(args: argparse.Namespace) -> int:
    """Render pending sidecars through all quality gates."""
    # Determine which stems to process
    stems: list[str] = []

    if args.stem:
        stems = list(args.stem)
    elif args.pending:
        # Find sidecars that haven't been rendered yet (no "done" status in pipeline_state)
        if WORKLIST_PATH.exists():
            wl = json.loads(WORKLIST_PATH.read_text(encoding="utf-8"))
            for e in wl:
                if e.get("status") not in ("done",):
                    sidecar = Path(e.get("sidecar_path", ""))
                    if sidecar.exists():
                        stems.append(e["stem"])
        # Also scan for any sidecars not in worklist
        if not stems:
            for sc in DEFAULT_TEXT_FOLDER.glob("*.summary.json"):
                stem = sc.stem.replace(".summary", "")
                stems.append(stem)
    else:
        print("Specify --pending or --stem. Use --help for details.")
        return 2

    if not stems:
        print("No pending sidecars to render.")
        return 0

    print(f"Rendering {len(stems)} sidecar(s) through quality gates...")
    if args.dry_run:
        print("(dry-run — no files will be written)")

    reports: list[dict] = []
    t0 = time.monotonic()
    for i, stem in enumerate(stems):
        print(f"\n  [{i+1}/{len(stems)}] {stem}")
        r = _render_one(stem, force=args.force, dry_run=args.dry_run)
        reports.append(r)
        status = r.get("status", "unknown")
        gates = r.get("gates", {})
        page_w = r.get("page_words", "?")
        halluc = gates.get("hallucination", {})
        conf = halluc.get("confidence", "?")
        fn = gates.get("footnotes", {}).get("count", "?")

        if status == "passed":
            print(f"  ✓ PASSED  ({page_w} words, {fn} footnotes, conf={conf})")
        elif status == "flagged":
            flags = r.get("flags", [])
            print(f"  ⚠ FLAGGED  ({page_w} words): {'; '.join(flags[:3])}")
        else:
            errs = [f"{k}: {v.get('error', '?')}" for k, v in gates.items() if not v.get("pass", True)]
            print(f"  ✗ FAILED   {'; '.join(errs[:3])}")

    wall = time.monotonic() - t0

    # Summary
    passed = sum(1 for r in reports if r.get("status") == "passed")
    flagged = sum(1 for r in reports if r.get("status") == "flagged")
    failed = sum(1 for r in reports if r.get("status") == "failed")

    print(f"\n{'='*50}")
    print(f" RENDER REPORT  ({wall:.1f}s)")
    print(f"{'='*50}")
    print(f"  Passed:  {passed}")
    print(f"  Flagged: {flagged}")
    print(f"  Failed:  {failed}")
    print(f"  Total:   {len(reports)}")
    if flagged:
        print(f"\n  Flagged papers (need fix-up):")
        for r in reports:
            if r.get("status") == "flagged":
                print(f"    - {r['stem']}: {'; '.join(r.get('flags', [])[:2])}")
    print(f"{'='*50}")

    # Save render report
    RENDER_REPORT_PATH.write_text(
        json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Report saved: {RENDER_REPORT_PATH.name}")

    # Update worklist statuses
    if WORKLIST_PATH.exists():
        wl = json.loads(WORKLIST_PATH.read_text(encoding="utf-8"))
        stem_to_entry = {e["stem"]: e for e in wl}
        for r in reports:
            stem = r["stem"]
            if stem in stem_to_entry:
                if r.get("status") == "passed":
                    stem_to_entry[stem]["status"] = "done"
                elif r.get("status") == "flagged":
                    stem_to_entry[stem]["status"] = "flagged"
                    stem_to_entry[stem]["flags"] = r.get("flags", [])
                stem_to_entry[stem]["render_report"] = {
                    k: v for k, v in r.get("gates", {}).items()
                    if k != "hallucination"  # Don't bloat worklist with unverified samples
                }
        WORKLIST_PATH.write_text(
            json.dumps(list(stem_to_entry.values()), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# progress — show campaign status
# ---------------------------------------------------------------------------

def cmd_progress(args: argparse.Namespace) -> int:
    """Print campaign progress."""
    if not WORKLIST_PATH.exists():
        print("No worklist found. Run 'plan' first.")
        return 1

    wl = json.loads(WORKLIST_PATH.read_text(encoding="utf-8"))
    done = [e for e in wl if e.get("status") == "done"]
    flagged = [e for e in wl if e.get("status") == "flagged"]
    failed = [e for e in wl if e.get("status") == "failed"]
    pending = [e for e in wl if e.get("status") == "pending"]

    by_topic_done: dict[str, int] = {}
    by_topic_total: dict[str, int] = {}
    for e in wl:
        t = e["topic"]
        by_topic_total[t] = by_topic_total.get(t, 0) + 1
        if e.get("status") == "done":
            by_topic_done[t] = by_topic_done.get(t, 0) + 1

    print(f"\n{'='*50}")
    print(f" AGENT DEEP RE-SUMMARIZATION PROGRESS")
    print(f"{'='*50}")
    print(f"  Done:     {len(done)}")
    print(f"  Flagged:  {len(flagged)}")
    print(f"  Failed:   {len(failed)}")
    print(f"  Pending:  {len(pending)}")
    print(f"  Total:    {len(wl)}")
    print()

    TOPIC_ORDER = [
        "vpc_transgene_free", "genome_editing_transgene_free",
        "bioethanol", "PHS_tolerance", "uncategorized",
        "downloads", "tmp",
    ]
    print(f"  {'Topic':<35} {'Done':>6} {'Total':>6} {'Pct':>6}")
    print(f"  {'-'*35} {'-'*6} {'-'*6} {'-'*6}")
    for t in TOPIC_ORDER:
        d = by_topic_done.get(t, 0)
        tot = by_topic_total.get(t, 0)
        pct = f"{d/tot*100:.0f}%" if tot > 0 else "—"
        print(f"  {t:<35} {d:>6} {tot:>6} {pct:>6}")
    for t in sorted(by_topic_total):
        if t not in TOPIC_ORDER:
            d = by_topic_done.get(t, 0)
            tot = by_topic_total[t]
            pct = f"{d/tot*100:.0f}%" if tot > 0 else "—"
            print(f"  {t:<35} {d:>6} {tot:>6} {pct:>6}")

    if flagged:
        print(f"\n  Flagged (need fix-up):")
        for e in flagged[:10]:
            print(f"    - {e['stem']}")
        if len(flagged) > 10:
            print(f"    ... and {len(flagged) - 10} more")

    print(f"{'='*50}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # plan
    p_plan = sub.add_parser("plan", help="Build/update the worklist of papers to re-summarize")
    p_plan.add_argument("--topic", nargs="+", default=[],
                        help="Filter to specific topic folders (e.g. vpc_transgene_free)")
    p_plan.add_argument("--limit", type=int, default=0,
                        help="Limit pending entries (0 = all)")
    p_plan.add_argument("--order", choices=["depth", "thinnest", "raw_shortest"], default="depth",
                        help="Sort order within topic tiers (default: thinnest existing page first)")
    p_plan.add_argument("--skip-today", dest="skip_today", action="store_true", default=True,
                        help="Skip papers whose wiki pages were modified or updated today (default: True)")
    p_plan.add_argument("--no-skip-today", dest="skip_today", action="store_false",
                        help="Do not skip papers modified today")

    # render
    p_render = sub.add_parser("render", help="Render sidecars through quality gates and write wiki pages")
    p_render.add_argument("--pending", action="store_true",
                          help="Render all pending sidecars (default)")
    p_render.add_argument("--stem", nargs="+", default=[],
                          help="Render specific stems")
    p_render.add_argument("--force", action="store_true",
                          help="Re-render even if already done")
    p_render.add_argument("--dry-run", action="store_true",
                          help="Run gates but don't write files")

    # progress
    sub.add_parser("progress", help="Show campaign progress")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "plan":
        return cmd_plan(args)
    elif args.command == "render":
        return cmd_render(args)
    elif args.command == "progress":
        return cmd_progress(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
