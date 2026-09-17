"""pdf_extract_phases.py — explicit, fingerprint-cached pipeline phases.

This module is the *pattern half* of Understand-Anything's deterministic-vs-semantic
split. Their codebase uses Tree-sitter (deterministic) and LLMs (semantic) in two
phases that can be re-run independently. Our equivalent split is **already present**
at the orchestrator level (``ResearchPaperExtractor.extract_all_raw`` is deterministic;
``process_all_with_ai`` is semantic), but two things were missing:

  1. **Content fingerprints** — the existing skip logic checks for the output path,
     so a re-OCR'd PDF or a prompt-version bump silently produces stale results.
  2. **Independent phase versioning** — there's no way to invalidate "rerun the
     summary phase only because the prompt changed".

This module wires both in. It does **not** refactor the 1100-line
``ResearchPaperExtractor`` class — a code-level split would be a multi-hour
operation and high risk given 4,000+ already-ingested papers depend on the
current logic. Instead it sits *next to* the extractor and provides phase
wrappers callers can opt into. Future ingestion code (e.g. ``ingest_parallel.py``)
calls these wrappers to get caching for free.

If you later want a true code-level split, the natural seams are:

  Deterministic phases (idempotent, never need LLM):
    - extract_raw_text       → ResearchPaperExtractor._extract_raw_text
    - extract_figure_images  → ResearchPaperExtractor._extract_and_map_images (image-cropping part)
    - parse_references       → (currently inline in process_single_pdf; new code)
    - extract_metadata_doi   → (currently inline; could call CrossRef)

  Semantic phases (call the LLM; non-deterministic; cache-key includes prompt version):
    - classify_figures       → ResearchPaperExtractor._extract_and_map_images (vision part)
    - generate_summary       → ResearchPaperExtractor._generate_and_validate_summary
    - generate_seed_pages    → ResearchPaperExtractor.populate_wiki_nodes
    - rename_pdf             → ResearchPaperExtractor.rename_pdf_if_needed
    - claim_impact_analysis  → claim_impact.py (already split)

Phase version tokens
====================
Bump these when the implementation or prompt changes. The next run will
invalidate the cache for that phase only (other phases stay cached).

Each phase computes::

    fingerprint = sha256(pdf_bytes + DETERMINISTIC_VERSION + phase_version)

so re-OCR'd PDFs and version bumps both bust the cache automatically.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Callable

from pipeline_state import PipelineState, fingerprint_file


# Bump these when the corresponding implementation or prompt changes.
# Keep them as strings so they show up verbatim in pipeline_state.json.
DETERMINISTIC_VERSION = "extract:v1"
SEMANTIC_VERSIONS = {
    "classify_figures":     "vision-filter:v1",
    "generate_summary":     "summary-prompt:v1",
    "generate_seed_pages":  "seed-pages-prompt:v1",
    "rename_pdf":           "rename-prompt:v1",
}


@dataclasses.dataclass
class PhaseResult:
    """What a phase wrapper returns to its caller."""

    phase: str
    fingerprint: str
    cached: bool          # True if we hit the cache
    payload: Any          # Whatever the underlying function returned (or the cached payload)


def _phase_fingerprint(pdf_path: Path, phase: str, deterministic: bool) -> str:
    tokens = [DETERMINISTIC_VERSION]
    if not deterministic:
        tokens.append(SEMANTIC_VERSIONS.get(phase, f"{phase}:v0"))
    tokens.append(phase)  # discriminate per-phase entries
    return fingerprint_file(pdf_path, *tokens)


# ─────────────────────────────────────────────────────────────────────────────
# Wrapper primitives
# ─────────────────────────────────────────────────────────────────────────────
def run_phase(
    *,
    state: PipelineState,
    pdf_path: Path,
    phase: str,
    deterministic: bool,
    work: Callable[[], Any],
    payload_to_cache: Callable[[Any], Any] | None = None,
    save_immediately: bool = False,
) -> PhaseResult:
    """Run ``work()`` unless this phase is already cached for this PDF.

    Parameters
    ----------
    state
        The shared PipelineState (call ``state.save()`` when the batch is done,
        or pass ``save_immediately=True`` to persist after each phase).
    pdf_path
        Source PDF — its content + version tokens form the cache key.
    phase
        Phase name; must match a key in SEMANTIC_VERSIONS for semantic phases.
    deterministic
        If True, the fingerprint excludes the semantic version token.
    work
        Zero-arg callable executed when the cache misses. Should return the
        result the caller wants (e.g. raw text, summary string, etc.).
    payload_to_cache
        Optional projection — what to store in pipeline_state.json. Defaults
        to caching nothing (the cache only records that the phase ran).
        Use this when the cached payload is small (e.g. an output path); avoid
        caching big blobs.
    save_immediately
        If True, ``state.save()`` is called after marking the phase done.
        Off by default so a batch of phases shares one disk write.

    Returns
    -------
    PhaseResult
        ``cached=True`` and ``payload=<what was cached>`` on a hit;
        ``cached=False`` and ``payload=<work() return value>`` on a miss.
    """
    fp = _phase_fingerprint(pdf_path, phase, deterministic)
    cached = state.get(phase, fp)
    if cached is not None:
        return PhaseResult(phase=phase, fingerprint=fp, cached=True, payload=cached.get("payload"))

    result = work()

    cache_payload = payload_to_cache(result) if payload_to_cache else None
    state.mark_done(phase, fp, payload=cache_payload)
    if save_immediately:
        state.save()
    return PhaseResult(phase=phase, fingerprint=fp, cached=False, payload=result)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience helpers — opinionated wrappers around the existing extractor
# ─────────────────────────────────────────────────────────────────────────────
def extract_raw_text(state: PipelineState, extractor, pdf_path: Path) -> PhaseResult:
    """Deterministic phase 1: PDF → markdown text + topic folder side-effects."""
    return run_phase(
        state=state, pdf_path=pdf_path, phase="extract_raw_text", deterministic=True,
        work=lambda: extractor._extract_raw_text(pdf_path),
        payload_to_cache=lambda r: {"chars": len(r) if isinstance(r, str) else None},
    )


def generate_summary(state: PipelineState, extractor, pdf_path: Path,
                      raw_text: str, image_summaries: list[str] | None = None) -> PhaseResult:
    """Semantic phase: LLM-generated structured summary. Cache key includes prompt version."""
    return run_phase(
        state=state, pdf_path=pdf_path, phase="generate_summary", deterministic=False,
        work=lambda: extractor._generate_and_validate_summary(
            pdf_path, raw_text, image_summaries or []),
        payload_to_cache=lambda r: {"chars": len(r) if isinstance(r, str) else None},
    )


def generate_seed_pages(state: PipelineState, extractor, pdf_path: Path,
                         summary_text: str, topic_folder: str) -> PhaseResult:
    """Semantic phase: per-paper concept/entity seed pages."""
    return run_phase(
        state=state, pdf_path=pdf_path, phase="generate_seed_pages", deterministic=False,
        work=lambda: extractor.populate_wiki_nodes(pdf_path.stem, summary_text, topic_folder),
        payload_to_cache=lambda r: {"created": len(r) if hasattr(r, "__len__") else None},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tiny CLI for cache inspection
# ─────────────────────────────────────────────────────────────────────────────
def _cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Phase-level cache diagnostics")
    parser.add_argument("--pdf", required=True, help="Path to a PDF to inspect")
    parser.add_argument("--phase", default=None,
                        help="Limit to this phase (default: report all)")
    args = parser.parse_args()

    state = PipelineState()
    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        print(f"ERROR: not found: {pdf_path}")
        return 2

    phases_to_check = [args.phase] if args.phase else [
        "extract_raw_text", "extract_data_objects",
        "classify_figures", "generate_summary", "generate_seed_pages", "rename_pdf",
    ]
    print(f"PDF: {pdf_path}")
    for phase in phases_to_check:
        deterministic = phase in {"extract_raw_text", "extract_data_objects"}
        fp = _phase_fingerprint(pdf_path, phase, deterministic)
        hit = state.get(phase, fp)
        marker = "✓ cached" if hit else "✗ missing"
        ts = (hit or {}).get("timestamp", "")
        payload = (hit or {}).get("payload", "")
        print(f"  {marker:10s}  {phase:25s}  {ts}  {payload or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
