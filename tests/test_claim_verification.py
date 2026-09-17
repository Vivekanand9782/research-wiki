"""Unit and integration tests for Sub-Second Claim Verification (Milestone 5 / R5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rag_engine import ClaimVerificationResult, RAGEngine


def _setup_verification_corpus(tmp_path: Path) -> tuple[RAGEngine, Path]:
    """Create isolated test workspace for claim verification."""
    wiki = tmp_path / "wiki"
    (wiki / "sources").mkdir(parents=True)
    raw_dir = tmp_path / "raw" / "papers" / "verify"
    raw_dir.mkdir(parents=True)

    # Paper 1: codA negative selection
    (raw_dir / "bhattacharjee_2023_coda.md").write_text(
        "# Strategic Transgene-Free Approaches of CRISPR in Plants\n\n"
        "## Negative Selection Systems\n"
        "Application of codA negative selection enables rapid screening of transgene-free genome-edited progeny.\n",
        encoding="utf-8",
    )
    (wiki / "sources" / "bhattacharjee_2023_coda.md").write_text(
        "# Strategic Transgene-Free Approaches\n\n## Abstract Summary\ncodA selection in plants.\n",
        encoding="utf-8",
    )

    # Paper 2: Cas9 off-target rates
    (raw_dir / "liang_2017_offtargets.md").write_text(
        "# Off-target Analysis in Wheat Genome Editing\n\n"
        "## Results\n"
        "CRISPR-Cas9 editing frequencies ranged from 15% to 65%, with detectable off-target cleavages at homologous loci.\n",
        encoding="utf-8",
    )
    (wiki / "sources" / "liang_2017_offtargets.md").write_text(
        "# Off-target Analysis in Wheat\n\n## Abstract Summary\nOff-targets in wheat.\n",
        encoding="utf-8",
    )

    engine = RAGEngine(wiki_folder=str(wiki))
    engine.search_engine.build_index()
    return engine, tmp_path


class TestClaimVerification:
    """Milestone 5 Claim Verification Tests."""

    def test_verify_supported_claim(self, tmp_path):
        """Verify directly corroborated claim returns SUPPORTED verdict with evidence."""
        engine, _ = _setup_verification_corpus(tmp_path)
        res = engine.verify_claim("codA negative selection enables transgene-free genome editing")

        assert isinstance(res, ClaimVerificationResult)
        assert res.verdict == "SUPPORTED"
        assert res.confidence >= 0.85
        assert res.primary_source is not None
        assert res.path is not None
        assert res.evidence_snippet is not None
        assert "codA" in res.evidence_snippet

    def test_verify_contradicted_claim(self, tmp_path):
        """Verify universal claim contradicted by empirical evidence returns CONTRADICTED verdict."""
        engine, _ = _setup_verification_corpus(tmp_path)
        res = engine.verify_claim("Cas9 guarantees 100% editing efficiency without off-targets in all plant species")

        assert isinstance(res, ClaimVerificationResult)
        assert res.verdict == "CONTRADICTED"
        assert res.confidence >= 0.80
        assert res.primary_source is not None
        assert "100%" in res.reason or "universal" in res.reason or "off-targets" in res.reason

    def test_verify_not_found_claim(self, tmp_path):
        """Verify unindexed out-of-domain claim returns NOT_FOUND verdict."""
        engine, _ = _setup_verification_corpus(tmp_path)
        res = engine.verify_claim("zebrafish fin regeneration through oct4 reprogramming")

        assert isinstance(res, ClaimVerificationResult)
        assert res.verdict == "NOT_FOUND"
        assert res.confidence == 0.0
        assert res.primary_source is None

    def test_verify_out_of_domain_claims_all_not_found(self, tmp_path):
        """Verify multiple out-of-domain / fabricated claims strictly evaluate to NOT_FOUND."""
        engine, _ = _setup_verification_corpus(tmp_path)
        ood_claims = [
            "bovine somatotropin increases milk production in dairy cattle",
            "metformin induces pluripotency in wheat shoot apical meristem",
            "zebrafish fin regeneration through oct4 reprogramming",
            "aspirin inhibits prostaglandin synthesis in human platelets",
            "asdfghjk zxcvbnm completely fabricated nonexistent query 123456789",
        ]
        for claim in ood_claims:
            res = engine.verify_claim(claim)
            assert isinstance(res, ClaimVerificationResult)
            assert res.verdict == "NOT_FOUND", f"False positive on '{claim}': {res.verdict} (conf={res.confidence})"
            assert res.confidence < 0.30

    def test_verify_slug_author_extraction_prefixed(self, tmp_path):
        """Verify author extraction from prefixed slugs (e.g. s_bhattacharjee_2023)."""
        # Use canonical raw/ layout so FullTextSearch.raw_root resolves correctly
        wiki = tmp_path / "wiki"
        (wiki / "sources").mkdir(parents=True)
        raw_dir = tmp_path / "raw" / "papers" / "verify"
        raw_dir.mkdir(parents=True)

        (raw_dir / "s_bhattacharjee_2023_coda.md").write_text(
            "# Strategic Transgene-Free Approaches of CRISPR in Plants\n\n"
            "## Negative Selection Systems\n"
            "Application of codA negative selection enables rapid screening of transgene-free genome-edited progeny.\n",
            encoding="utf-8",
        )
        (wiki / "sources" / "s_bhattacharjee_2023_coda.md").write_text(
            "# Strategic Transgene-Free Approaches\n\n## Abstract Summary\ncodA selection.\n",
            encoding="utf-8",
        )

        engine = RAGEngine(wiki_folder=str(wiki))
        engine.search_engine.build_index()

        res = engine.verify_claim("codA negative selection enables transgene-free genome editing")
        assert res.verdict == "SUPPORTED"
        assert "Bhattacharjee" in res.primary_source
        assert "Author" not in res.primary_source


    def test_verify_empty_string(self, tmp_path):
        """Verify empty claim returns NOT_FOUND verdict cleanly."""
        engine, _ = _setup_verification_corpus(tmp_path)
        res = engine.verify_claim("   ")

        assert isinstance(res, ClaimVerificationResult)
        assert res.verdict == "NOT_FOUND"
        assert res.confidence == 0.0

    def test_verify_subsecond_performance(self, tmp_path):
        """Verify verify_claim completes in sub-second time without LLM synthesis."""
        engine, _ = _setup_verification_corpus(tmp_path)
        res = engine.verify_claim("codA negative selection")

        assert res.total_ms < 1000.0  # < 1.0s target
        assert res.verification_ms >= 0.0

    def test_verify_result_to_dict_and_json(self, tmp_path):
        """Verify to_dict produces valid JSON with required schema fields."""
        engine, _ = _setup_verification_corpus(tmp_path)
        res = engine.verify_claim("codA negative selection")
        d = res.to_dict()

        assert "claim" in d
        assert "verdict" in d
        assert "confidence" in d
        assert "reason" in d
        assert "primary_source" in d
        assert "total_ms" in d

        # Must be JSON serializable
        json_str = json.dumps(d)
        assert len(json_str) > 0
