"""Tests for Task 10 — hierarchical summarisation chunker + helpers."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module", autouse=True)
def _stub_genai():
    """Same minimal stub other tests use so prompts.py imports cleanly."""
    fake_config = types.ModuleType("config")
    fake_config.AI_MODEL = "gpt-oss-120b"
    fake_config.FILTER_MODEL = "gpt-oss-120b"
    fake_config.VISION_MODEL = "gpt-oss-120b"
    fake_config.PROJECT_ID = "stub"
    fake_config.LOCATION = "global"
    sys.modules["config"] = fake_config
    if "google" not in sys.modules:
        google_mod = types.ModuleType("google")
        genai_mod = types.ModuleType("google.genai")
        genai_types_mod = types.ModuleType("google.genai.types")
        genai_types_mod.Part = type("Part", (), {"from_bytes": staticmethod(lambda *a, **kw: None)})
        genai_types_mod.GenerateContentConfig = lambda **kw: None
        genai_types_mod.EmbedContentConfig = lambda **kw: None
        genai_mod.Client = lambda *a, **kw: types.SimpleNamespace(models=types.SimpleNamespace())
        genai_mod.types = genai_types_mod
        google_mod.genai = genai_mod
        sys.modules["google"] = google_mod
        sys.modules["google.genai"] = genai_mod
        sys.modules["google.genai.types"] = genai_types_mod
    for name in ("prompts",):
        sys.modules.pop(name, None)
    yield


def _section(name: str, body_chars: int) -> str:
    """Build a `## name` section with `body_chars` of filler."""
    return f"\n## {name}\n" + ("x" * body_chars) + "\n"


# ---------------------------------------------------------------------------
# chunk_by_sections
# ---------------------------------------------------------------------------

class TestChunker:
    def test_empty_input(self):
        from prompts import chunk_by_sections
        assert chunk_by_sections("") == []

    def test_no_headings_yields_one_preface_chunk(self):
        from prompts import chunk_by_sections
        chunks = chunk_by_sections("just some text without any headings here.")
        assert len(chunks) == 1
        assert chunks[0][0] == "(preface)"

    def test_h2_boundaries_become_chunks(self):
        from prompts import chunk_by_sections, MIN_CHUNK_CHARS
        # Each section above the merge threshold so they stay separate.
        big = MIN_CHUNK_CHARS + 500
        md = "# Title\n\npreface " + "x" * big
        md += _section("Introduction", big)
        md += _section("Methods", big)
        chunks = chunk_by_sections(md)
        headings = [h for h, _ in chunks]
        assert "Introduction" in headings
        assert "Methods" in headings

    def test_tiny_adjacent_chunks_merge(self):
        from prompts import chunk_by_sections, MIN_CHUNK_CHARS
        # Two H2 sections both below MIN_CHUNK_CHARS -> should merge.
        md = "# Title\n\n" + _section("Introduction", 200) + _section("Methods", 200)
        chunks = chunk_by_sections(md)
        # Merging keeps the *first* heading. Body of Methods is appended.
        assert len(chunks) <= 2
        joined = "\n".join(b for _, b in chunks)
        assert "Methods" in joined  # the merged-in H2 line is preserved as text

    def test_oversized_chunk_splits_into_slices(self):
        from prompts import chunk_by_sections, MAX_CHUNK_CHARS
        big_body = "x" * (MAX_CHUNK_CHARS * 2 + 500)  # clearly > 2x
        md = f"## Methods\n{big_body}\n"
        chunks = chunk_by_sections(md)
        # Expect at least 3 slices for the same logical heading.
        assert len(chunks) >= 3
        # First slice keeps the bare heading; subsequent ones get the
        # "(cont. k/N)" suffix.
        assert chunks[0][0] == "Methods"
        assert any("cont." in h for h, _ in chunks[1:])

    def test_each_chunk_within_max_chars(self):
        from prompts import chunk_by_sections, MAX_CHUNK_CHARS
        big_body = "x" * (MAX_CHUNK_CHARS * 3)
        md = f"## Big\n{big_body}\n"
        chunks = chunk_by_sections(md)
        for _, body in chunks:
            assert len(body) <= MAX_CHUNK_CHARS, (
                f"chunk len {len(body)} > MAX_CHUNK_CHARS"
            )


# ---------------------------------------------------------------------------
# build_chunk_summary_prompt
# ---------------------------------------------------------------------------

class TestChunkSummaryPrompt:
    def test_contains_heading_and_body(self):
        from prompts import build_chunk_summary_prompt
        p = build_chunk_summary_prompt("Methods", "We did X.")
        assert "Methods" in p
        assert "We did X." in p

    def test_renders_schema_inline(self):
        from prompts import build_chunk_summary_prompt
        p = build_chunk_summary_prompt("Methods", "body")
        # The literal property names from CHUNK_SUMMARY_SCHEMA show up.
        assert "key_points" in p
        assert "entities" in p
        assert "data_points" in p

    def test_includes_no_outside_knowledge_rule(self):
        from prompts import build_chunk_summary_prompt
        p = build_chunk_summary_prompt("Methods", "body")
        assert "ONLY facts" in p or "no outside knowledge" in p.lower()


# ---------------------------------------------------------------------------
# aggregate_chunk_intermediates
# ---------------------------------------------------------------------------

class TestAggregateIntermediates:
    def test_empty_input_returns_empty_string(self):
        from prompts import aggregate_chunk_intermediates
        assert aggregate_chunk_intermediates([]) == ""

    def test_renders_per_chunk_blocks(self):
        from prompts import aggregate_chunk_intermediates
        out = aggregate_chunk_intermediates([
            {"heading": "Methods", "key_points": ["Did X"], "entities": ["TaPHS1"], "data_points": ["LOD = 12.4"]},
            {"heading": "Results", "key_points": ["Found Y"], "entities": [], "data_points": []},
        ])
        assert "PRE-SUMMARISED CHUNKS" in out
        assert "Methods" in out and "Results" in out
        assert "TaPHS1" in out
        assert "LOD = 12.4" in out

    def test_handles_missing_fields(self):
        """A chunk dict missing optional keys shouldn't crash."""
        from prompts import aggregate_chunk_intermediates
        out = aggregate_chunk_intermediates([{"heading": "Bare"}])
        assert "Bare" in out

    def test_skips_non_dict_entries(self):
        from prompts import aggregate_chunk_intermediates
        out = aggregate_chunk_intermediates([
            {"heading": "Real", "key_points": ["pt"]},
            "garbage",
            None,
        ])
        assert "Real" in out
        # No crash, no garbage in output
        assert "garbage" not in out
