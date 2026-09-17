"""Unit and integration tests for Adaptive Proximity Window & Multi-Clause RRF (Milestone 4 / R2)."""

from __future__ import annotations

import collections
import sqlite3
from pathlib import Path

import pytest
from rag_engine import RAGEngine, _compute_adaptive_window


class TestAdaptiveProximityAndRRF:
    """Milestone 4 Unit & Integration Tests."""

    def test_adaptive_window_formula(self):
        """Verify dynamic proximity window scaling: W(1..2)=240, W(3)=380, W(4)=520, W(5)=660, W(>=6)=800."""
        assert _compute_adaptive_window(1) == 240
        assert _compute_adaptive_window(2) == 240
        assert _compute_adaptive_window(3) == 380
        assert _compute_adaptive_window(4) == 520
        assert _compute_adaptive_window(5) == 660
        assert _compute_adaptive_window(6) == 800
        assert _compute_adaptive_window(10) == 800

    def test_multi_sentence_proximity_match(self):
        """Verify sliding window detects terms clustered across adjacent sentences within window."""
        # 3 terms spanning ~350 characters
        text = (
            "CRISPR-Cas9 ribonucleoproteins were assembled in vitro. "
            + ("Some intervening technical description of unrelated filler details. " * 3)
            + "The resulting potato plants exhibited marker-free targeted mutagenesis."
        )
        tokens = ["crispr-cas9", "potato"]
        assert RAGEngine._phrase_or_proximity(text.lower(), tokens, window=400) is True
        # Narrow window of 50 characters should fail because distance is > 200
        assert RAGEngine._phrase_or_proximity(text.lower(), tokens, window=50) is False

    def test_missing_optional_token_does_not_abort(self):
        """Verify proximity search does not abort when optional tokens are missing if needed threshold is met."""
        text = "Cas9 protein delivered via particle bombardment into wheat cells."
        # 4 tokens, needed = (4+1)//2 = 2. 'cas9' and 'wheat' exist, 'nonexistent1' and 'nonexistent2' do not.
        tokens = ["cas9", "nonexistent1", "wheat", "nonexistent2"]
        assert RAGEngine._phrase_or_proximity(text.lower(), tokens, window=300) is True

    def test_multi_clause_decomposition(self):
        """Verify comparative and compound queries decompose into independent clauses."""
        engine = RAGEngine()

        # Comparative query
        comp_clauses = [label for label, _ in engine._decompose_and_expand_clauses("Cas9 vs Cas12a in wheat")]
        assert len(comp_clauses) >= 2
        assert any("cas9" in c.lower() for c in comp_clauses)
        assert any("cas12a" in c.lower() for c in comp_clauses)

        # Prepositional query
        prep_clauses = [label for label, _ in engine._decompose_and_expand_clauses("TaMFT in seed dormancy across wheat")]
        assert len(prep_clauses) >= 2

    def test_reciprocal_rank_fusion_scoring(self, tmp_path):
        """Verify RRF fused ranking gives highest weight to candidates appearing high in multiple clauses."""
        wiki = tmp_path / "wiki"
        (wiki / "sources").mkdir(parents=True)
        raw_dir = tmp_path / "raw" / "papers" / "rrf"
        raw_dir.mkdir(parents=True)

        # Paper A matches both clauses
        (raw_dir / "paper_a.md").write_text(
            "# Cas9 and Cas12a comparative editing in wheat\n\n"
            "## Results\nCas9 targeted exon 1 and Cas12a targeted intron 2 with high efficiency in wheat cultivars.\n",
            encoding="utf-8",
        )
        (wiki / "sources" / "paper_a.md").write_text(
            "# Cas9 and Cas12a comparative editing in wheat\n\n## Abstract Summary\nCas9 and Cas12a in wheat.\n",
            encoding="utf-8",
        )

        # Paper B matches only Cas9
        (raw_dir / "paper_b.md").write_text(
            "# Cas9 single nuclease editing in wheat\n\n"
            "## Results\nCas9 nuclease editing in wheat leaves.\n",
            encoding="utf-8",
        )
        (wiki / "sources" / "paper_b.md").write_text(
            "# Cas9 single nuclease editing in wheat\n\n## Abstract Summary\nCas9 in wheat.\n",
            encoding="utf-8",
        )

        engine = RAGEngine(wiki_folder=str(wiki))
        engine.search_engine.build_index()

        hits, _, _ = engine.retrieve("Cas9 vs Cas12a in wheat", top_k=5)
        assert len(hits) >= 2
        assert "paper_a.md" in hits[0]["path"]
