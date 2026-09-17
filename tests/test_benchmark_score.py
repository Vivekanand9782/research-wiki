"""Tests for benchmarks/score.py (Task 11)."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module", autouse=True)
def _stub_genai():
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
    for name in ("genai_client", "prompts", "validation", "renderer", "wiki_vocabulary"):
        sys.modules.pop(name, None)
    yield


def _full_summary(headings, *, with_frontmatter=True, wikilinks=5,
                  footnotes=0):
    parts = []
    if with_frontmatter:
        parts.append(
            "---\ntags: [t]\ntype: source\ndate_created: 2026-05-27\n"
            "date_updated: 2026-05-27\nsource_count: 1\n"
            'doi: "10.1/x"\nauthors: "A"\nyear: 2026\njournal: "J"\n---\n'
        )
    for h in headings:
        parts.append(f"## {h}\nBody for {h}.")
        if wikilinks:
            parts.append(" ".join(f"[[entity{i}]]" for i in range(wikilinks)))
            wikilinks = 0
        parts.append("")
    for i in range(footnotes):
        parts.append(f"[^fn-{i}]: \"verbatim quote\" — p.{i+1}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# score_summary
# ---------------------------------------------------------------------------

class TestScoreSummary:
    def test_full_summary_passes_strict(self):
        from prompts import required_headers
        from benchmarks.score import score_summary
        s = score_summary(_full_summary(required_headers()))
        assert s.strict_pass is True
        assert s.lenient_pass is True
        assert s.score >= 90
        assert s.wikilink_count >= 5

    def test_lenient_only_summary_fails_strict(self):
        from prompts import lenient_required_headers
        from benchmarks.score import score_summary
        s = score_summary(_full_summary(lenient_required_headers()))
        # Only 5/12 headings.
        assert s.strict_pass is False
        # Lenient validator is happy with the 5.
        assert s.lenient_pass is True

    def test_canonicalised_rate_with_vocab(self):
        from prompts import required_headers
        from benchmarks.score import score_summary

        class FakeVocab:
            def find_canonical(self, term):
                # "entity0", "entity1" resolve; rest do not.
                return term if term in ("entity0", "entity1") else None

        s = score_summary(_full_summary(required_headers()), vocab_index=FakeVocab())
        # 5 wikilinks, 2 resolve -> 0.4
        assert abs(s.canonicalised_rate - 0.4) < 0.001

    def test_canonicalised_rate_zero_without_vocab(self):
        from prompts import required_headers
        from benchmarks.score import score_summary
        s = score_summary(_full_summary(required_headers()))
        assert s.canonicalised_rate == 0.0

    def test_footnote_count(self):
        from prompts import required_headers
        from benchmarks.score import score_summary
        s = score_summary(_full_summary(required_headers(), footnotes=3))
        assert s.footnote_count == 3


# ---------------------------------------------------------------------------
# compare_summaries
# ---------------------------------------------------------------------------

class TestCompareSummaries:
    def test_deltas_positive_when_two_stage_better(self):
        from prompts import required_headers, lenient_required_headers
        from benchmarks.score import compare_summaries
        legacy = _full_summary(lenient_required_headers())
        two_stage = _full_summary(required_headers())
        c = compare_summaries("paper1", legacy, two_stage)
        d = c.deltas()
        # Two-stage passes strict, legacy doesn't, so delta is +1.
        assert d["strict_pass"] == 1
        # Score went up (two_stage is the full 12-section version).
        assert d["score"] >= 0


# ---------------------------------------------------------------------------
# acceptance_check
# ---------------------------------------------------------------------------

class TestAcceptanceCheck:
    def test_accepts_improvements(self):
        from benchmarks.score import acceptance_check
        deltas = [
            {"score": 5, "wikilink_count": 10, "canonicalised_rate": 0.1},
            {"score": 3, "wikilink_count": 5, "canonicalised_rate": 0.05},
        ]
        ok, reasons = acceptance_check(deltas)
        assert ok, reasons

    def test_rejects_score_regression(self):
        from benchmarks.score import acceptance_check
        deltas = [
            {"score": -10, "wikilink_count": 0, "canonicalised_rate": 0.0},
            {"score": -8, "wikilink_count": 0, "canonicalised_rate": 0.0},
        ]
        ok, reasons = acceptance_check(deltas)
        assert not ok
        assert any("score regressed" in r for r in reasons)

    def test_rejects_wikilink_collapse(self):
        from benchmarks.score import acceptance_check
        deltas = [{"score": 0, "wikilink_count": -5, "canonicalised_rate": 0.0}]
        ok, reasons = acceptance_check(deltas)
        assert not ok
        assert any("wikilink_count" in r for r in reasons)

    def test_no_comparisons_rejects(self):
        from benchmarks.score import acceptance_check
        ok, reasons = acceptance_check([])
        assert not ok
