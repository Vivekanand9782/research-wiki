"""Tests for paper_classifier (Task 5)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RAW_PAPERS = ROOT / "raw" / "papers" / "uncategorized"


# ---------------------------------------------------------------------------
# Heuristic cases
# ---------------------------------------------------------------------------

class TestHeuristicCorrectionNotice:
    def test_correction_to_prefix(self):
        from paper_classifier import classify_paper_type
        text = "Correction to: The heat shock factor 20-HSF4 module regulates ..."
        r = classify_paper_type(text)
        assert r.paper_type == "correction_notice"
        assert r.source == "heuristic"

    def test_erratum(self):
        from paper_classifier import classify_paper_type
        r = classify_paper_type("Erratum: A previous report contained ...")
        assert r.paper_type == "correction_notice"

    def test_author_correction(self):
        from paper_classifier import classify_paper_type
        r = classify_paper_type("Author Correction: Figure 3 was mislabeled ...")
        assert r.paper_type == "correction_notice"

    def test_retraction(self):
        from paper_classifier import classify_paper_type
        r = classify_paper_type("Retraction notice for the paper ...")
        assert r.paper_type == "correction_notice"


class TestHeuristicReview:
    def test_title_contains_review(self):
        from paper_classifier import classify_paper_type
        text = "# A comprehensive review of CRISPR genome editing in plants\n\nAbstract ..."
        r = classify_paper_type(text)
        assert r.paper_type == "review"

    def test_self_described_review(self):
        from paper_classifier import classify_paper_type
        text = "Abstract\n\nThis review discusses the latest advances in lignin biosynthesis."
        r = classify_paper_type(text)
        assert r.paper_type == "review"

    def test_systematic_review(self):
        from paper_classifier import classify_paper_type
        r = classify_paper_type("This is a systematic review of pre-harvest sprouting QTLs.")
        assert r.paper_type == "review"


class TestHeuristicMethodsPaper:
    def test_protocol_in_title(self):
        from paper_classifier import classify_paper_type
        text = "# A protocol for high-efficiency wheat transformation\n\nAbstract ..."
        r = classify_paper_type(text)
        assert r.paper_type == "methods_paper"

    def test_describes_a_novel_method(self):
        from paper_classifier import classify_paper_type
        text = (
            "Abstract\n\nWe describe a novel method for fast genotyping of wheat. "
            "The pipeline ..."
        )
        r = classify_paper_type(text)
        assert r.paper_type == "methods_paper"


class TestHeuristicPerspective:
    def test_perspective_in_title(self):
        from paper_classifier import classify_paper_type
        text = "# Perspective: the future of plant synthetic biology\n\n..."
        r = classify_paper_type(text)
        assert r.paper_type == "perspective"

    def test_commentary_in_title(self):
        from paper_classifier import classify_paper_type
        text = "# Commentary on recent advances in CRISPR editing\n\n..."
        r = classify_paper_type(text)
        assert r.paper_type == "perspective"


class TestHeuristicDefault:
    def test_no_signal_returns_primary_research_default(self):
        from paper_classifier import classify_paper_type
        text = (
            "# Identification of QTL controlling pre-harvest sprouting in wheat\n\n"
            "Abstract\n\nWe phenotyped 200 RILs across two environments. "
            "Composite interval mapping identified a major QTL on 4A ..."
        )
        r = classify_paper_type(text)
        # No heuristic should fire; with no LLM caller, default applies.
        assert r.paper_type == "primary_research"
        assert r.source == "default"

    def test_empty_text_returns_default(self):
        from paper_classifier import classify_paper_type
        r = classify_paper_type("")
        assert r.paper_type == "primary_research"
        assert r.source == "default"


# ---------------------------------------------------------------------------
# LLM fallback
# ---------------------------------------------------------------------------

class TestLLMFallback:
    def test_llm_word_used_when_heuristic_misses(self):
        from paper_classifier import classify_paper_type
        text = "A mid-length scientific document with no obvious classification cues."

        def fake_llm(prompt: str) -> str:
            assert "category" in prompt.lower()
            return "review"

        r = classify_paper_type(text, llm_caller=fake_llm)
        assert r.paper_type == "review"
        assert r.source == "llm"

    def test_llm_strips_punctuation_and_extra_words(self):
        from paper_classifier import classify_paper_type
        text = "An ambiguous abstract."
        r = classify_paper_type(text, llm_caller=lambda p: "  Methods_Paper.\n")
        assert r.paper_type == "methods_paper"

    def test_llm_unknown_word_falls_back_to_default(self):
        from paper_classifier import classify_paper_type
        text = "An ambiguous abstract."
        r = classify_paper_type(text, llm_caller=lambda p: "blahblah")
        assert r.paper_type == "primary_research"
        assert r.source == "default"

    def test_llm_exception_is_caught(self):
        from paper_classifier import classify_paper_type

        def boom(prompt: str) -> str:
            raise RuntimeError("rate limit")

        r = classify_paper_type("ambiguous", llm_caller=boom)
        assert r.paper_type == "primary_research"
        assert r.source == "default"
        assert "rate limit" in r.rationale


# ---------------------------------------------------------------------------
# Live raw markdown smoke test
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not RAW_PAPERS.is_dir(),
                    reason="raw papers directory not present")
class TestLiveRawSmoke:
    def test_li_2025_correction_is_detected(self):
        from paper_classifier import classify_paper_type
        path = RAW_PAPERS / "li_2025_correction_heat_shock.md"
        if not path.exists():
            pytest.skip("li_2025_correction_heat_shock.md not present")
        r = classify_paper_type(path.read_text(encoding="utf-8"))
        assert r.paper_type == "correction_notice"
        assert r.source == "heuristic"

    def test_aslam_2026_classifies_without_crash(self):
        from paper_classifier import classify_paper_type
        from prompts import PAPER_TYPES
        path = RAW_PAPERS / "aslam_2026_crispr_mediated_engineering.md"
        if not path.exists():
            pytest.skip("aslam_2026 raw markdown not present")
        # Smoke test: real OpenDataLoader output has publisher boilerplate
        # at the head, which the heuristic doesn't recognise as a review.
        # In production the LLM fallback handles this. Here we only verify
        # the classifier returns a valid PAPER_TYPES entry without crashing.
        r = classify_paper_type(path.read_text(encoding="utf-8"))
        assert r.paper_type in PAPER_TYPES
        assert r.source in ("heuristic", "default")  # no llm_caller passed
