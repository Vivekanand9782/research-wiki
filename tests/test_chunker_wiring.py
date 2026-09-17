"""Regression test for the long-paper chunker wiring (Task 10/11).

Confirms that when ``USE_TWO_STAGE_EXTRACTION = True`` and the source
markdown exceeds ``TRUNCATION_THRESHOLD_CHARS``, the orchestrator
runs ``_run_chunked_extraction`` per-chunk before the Stage A call,
and that the per-paper LLM-call count is bounded.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _import_pdf_extractor_with_stubs():
    """Stub config + genai_client (and the renderer's vocab call) so the
    test runs hermetically.
    """
    fake_config = types.ModuleType("config")
    fake_config.AI_MODEL = "gpt-oss-120b"
    fake_config.FILTER_MODEL = "gpt-oss-120b"
    fake_config.VISION_MODEL = "gpt-oss-120b"
    fake_config.PROJECT_ID = "stub"
    fake_config.LOCATION = "global"
    fake_config.USE_TWO_STAGE_EXTRACTION = True  # force the two-stage path
    fake_config.HALLUCINATION_CONFIDENCE_THRESHOLD = 0.90
    fake_config.MAX_HALLUCINATION_REPAIR_RETRIES = 2
    sys.modules["config"] = fake_config

    # Reset modules that might be cached.
    for name in ("genai_client", "prompts", "validation", "renderer",
                 "wiki_vocabulary", "paper_classifier", "pdf_extractor"):
        sys.modules.pop(name, None)

    fake_genai = types.ModuleType("genai_client")
    fake_genai.genai_client = None
    fake_genai.get_embeddings = lambda *a, **kw: []
    fake_genai.generate_content_with_retry = (
        lambda **kw: types.SimpleNamespace(text="{}")
    )

    # Real validators come from prompts.py — but the orchestrator imports
    # validate_structured_summary_strict by name, so provide a stub that
    # always passes (we're not exercising the validator here).
    fake_genai.validate_structured_summary = lambda t, **kw: {"valid": True, "missing_sections": []}
    fake_genai.validate_structured_summary_strict = lambda t, **kw: {"valid": True, "missing_sections": []}

    # The Stage A call returns a complete payload. Each chunk-summary
    # call returns a tight JSON. The fake_get_ai_response below
    # discriminates by prompt content.
    call_log: list[str] = []

    def fake_get_ai_response(prompt, *, raise_on_error=False, **kw):
        call_log.append(prompt)
        if "chunk" in prompt.lower() and "key_points" in prompt:
            # Per-chunk summariser.
            return json.dumps({
                "heading": "Stub Heading",
                "key_points": ["stub key point"],
                "entities": ["StubEntity"],
                "data_points": ["LOD = 12.4"],
            })
        # Stage A fallthrough — return a complete-enough payload.
        from prompts import required_headers
        sections = {h: {"text": f"Body for {h}."} for h in required_headers()}
        return json.dumps({
            "frontmatter": {"tags": ["t"], "doi": "10.1/x", "authors": "A",
                            "year": 2026, "journal": "J"},
            "paper_type": "primary_research",
            "sections": sections,
        })

    fake_genai.get_ai_response = fake_get_ai_response
    fake_genai._call_log = call_log
    sys.modules["genai_client"] = fake_genai

    # Stub wiki_vocabulary so the renderer doesn't try to scan disk.
    fake_vocab = types.ModuleType("wiki_vocabulary")
    fake_vocab.get_index = lambda *a, **kw: types.SimpleNamespace(
        find_canonical=lambda term: None,
    )
    sys.modules["wiki_vocabulary"] = fake_vocab

    spec = importlib.util.spec_from_file_location(
        "pdf_extractor", ROOT / "pdf_extractor.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, call_log


@pytest.fixture
def extractor_factory(tmp_path):
    """Return (extractor, call_log) with text_folder pointed at tmp_path.
    Cleans up its sys.modules patches at teardown so other tests get a
    fresh wiki_vocabulary / genai_client.
    """
    mod, call_log = _import_pdf_extractor_with_stubs()

    e = mod.ResearchPaperExtractor.__new__(mod.ResearchPaperExtractor)
    e.text_folder = tmp_path

    class _Logger:
        def log_summary_validation(self, **kw): pass
        def log_error(self, msg): pass

    e.logger = _Logger()
    yield e, call_log
    # Teardown: drop the stubs so other test files re-import the real
    # modules. The autouse fixtures in test_wiki_vocabulary.py and
    # test_renderer.py also pop their own caches, but we belt-and-braces
    # here so this file's stubs don't bleed.
    for name in ("genai_client", "prompts", "validation", "renderer",
                 "wiki_vocabulary", "paper_classifier", "pdf_extractor",
                 "config"):
        sys.modules.pop(name, None)


# ---------------------------------------------------------------------------
# Long paper triggers chunker
# ---------------------------------------------------------------------------

class TestChunkerWiring:
    def test_long_paper_triggers_chunked_extraction(self, extractor_factory):
        from prompts import TRUNCATION_THRESHOLD_CHARS
        extractor, call_log = extractor_factory

        # Synthetic long markdown: several H2 sections each big enough
        # to NOT merge under MIN_CHUNK_CHARS. Total exceeds the
        # truncation threshold so the chunker path triggers.
        sections = [
            f"\n## Section {i}\n" + ("xyz " * 1000)
            for i in range(5)
        ]
        # Ensure total > TRUNCATION_THRESHOLD_CHARS.
        long_md = "\n".join(sections)
        while len(long_md) <= TRUNCATION_THRESHOLD_CHARS:
            long_md += sections[0]

        result = extractor._generate_and_validate_summary(long_md, "long_paper")
        assert "## Title & Metadata" in result, "Stage B render failed"

        # Chunk-summariser prompts contain the literal "key_points"
        # property name; the Stage A prompt contains "OUTPUT CONTRACT".
        chunk_prompts = [p for p in call_log if "key_points" in p and "data_points" in p]
        stage_a_prompts = [p for p in call_log if "OUTPUT CONTRACT" in p]

        assert len(chunk_prompts) >= 1, (
            "long paper should have triggered ≥ 1 chunk-summary LLM call"
        )
        assert len(stage_a_prompts) == 1, (
            f"expected exactly 1 Stage A call, got {len(stage_a_prompts)}"
        )

        # Stage A's prompt body should reference the aggregated chunks.
        assert "PRE-SUMMARISED CHUNKS" in stage_a_prompts[0]

    def test_short_paper_skips_chunker(self, extractor_factory):
        extractor, call_log = extractor_factory

        # Short paper — well under truncation threshold.
        short_md = "## Methods\n" + ("x" * 500) + "\n## Results\n" + ("y" * 500)
        result = extractor._generate_and_validate_summary(short_md, "short_paper")
        assert "## Title & Metadata" in result

        chunk_prompts = [p for p in call_log if "key_points" in p and "data_points" in p]
        stage_a_prompts = [p for p in call_log if "OUTPUT CONTRACT" in p]

        assert len(chunk_prompts) == 0, (
            f"short paper should not have triggered chunking, got {len(chunk_prompts)} chunk calls"
        )
        assert len(stage_a_prompts) == 1


# ---------------------------------------------------------------------------
# LLM-call count bound
# ---------------------------------------------------------------------------

class TestLLMCallBound:
    def test_long_paper_call_count_matches_chunker(self, extractor_factory):
        """LLM-call count = (1 per chunk) + 1 Stage A. The chunker's
        actual output count varies with H2 boundary density, so we
        assert against ``chunk_by_sections`` directly rather than the
        worst-case ⌈len/30k⌉ bound."""
        from prompts import TRUNCATION_THRESHOLD_CHARS, chunk_by_sections
        extractor, call_log = extractor_factory

        sections = [f"\n## S{i}\n" + ("xyz " * 1500) for i in range(8)]
        long_md = "\n".join(sections)
        while len(long_md) <= TRUNCATION_THRESHOLD_CHARS:
            long_md += sections[0]

        # Use the same chunker the orchestrator will use.
        expected_chunks = len(chunk_by_sections(long_md))

        extractor._generate_and_validate_summary(long_md, "bounded_paper")

        chunk_calls = sum(1 for p in call_log if "key_points" in p and "data_points" in p)
        stage_a_calls = sum(1 for p in call_log if "OUTPUT CONTRACT" in p)

        assert chunk_calls == expected_chunks, (
            f"expected {expected_chunks} chunk calls (one per chunk_by_sections "
            f"output), got {chunk_calls}"
        )
        assert stage_a_calls == 1, (
            f"expected exactly 1 Stage A call, got {stage_a_calls}"
        )


class TestTwoStageContextForwarding:
    def test_api_metadata_and_gene_registry_are_forwarded(self, extractor_factory):
        extractor, _call_log = extractor_factory
        extractor.gene_registry_text = "ZmABC — canonical registry entry"
        captured = {}
        original = extractor._generate_via_two_stage

        def recording_two_stage(*args, **kwargs):
            captured.update(kwargs)
            return original(*args, **kwargs)

        extractor._generate_via_two_stage = recording_two_stage
        api_metadata = {
            "title": "Verified title",
            "doi": "10.1111/pbi.13433",
            "year": 2020,
        }
        extractor._generate_and_validate_summary(
            "## Methods\nsource text " * 100,
            "metadata_paper",
            extracted_doi="10.1111/pbi.13433",
            api_metadata=api_metadata,
        )

        assert captured["api_metadata"] is api_metadata
        assert captured["gene_registry_text"] == extractor.gene_registry_text
