"""Unit and integration tests for Domain Synonym Expander & Exact Entity Protection (Milestone 3 / R3)."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest
from rag_engine import (
    DOMAIN_SYNONYM_CLUSTERS,
    RAGEngine,
    _GENE_QTL_RE,
    _NUMERIC_MEASURE_RE,
    _PERCENTAGE_RE,
)
from research_retrieval import FullTextSearch


def _setup_synonym_corpus(tmp_path: Path) -> tuple[RAGEngine, Path]:
    """Create isolated test workspace with papers testing synonym expansion and entity protection."""
    wiki = tmp_path / "wiki"
    (wiki / "sources").mkdir(parents=True)
    raw_dir = tmp_path / "raw" / "papers" / "synonyms"
    raw_dir.mkdir(parents=True)

    # Paper 1: Mentions potato and clonal (synonyms of vegetatively propagated) and Cas9 RNP (synonym of transgene-free)
    (raw_dir / "potato_rnp.md").write_text(
        "# High-Efficiency Clonal Gene Editing in Potato Protoplasts\n\n"
        "## Results\n"
        "Transient delivery of Cas9 RNP into Solanum tuberosum protoplasts produced 45.5% marker-free mutant lines.\n",
        encoding="utf-8",
    )
    (wiki / "sources" / "potato_rnp.md").write_text(
        "# High-Efficiency Clonal Gene Editing in Potato Protoplasts\n\n## Abstract Summary\nPotato protoplast RNP editing.\n",
        encoding="utf-8",
    )

    # Paper 2: Mentions banana and PEG transfection (synonyms)
    (raw_dir / "banana_peg.md").write_text(
        "# Clonal Propagation and PEG Transfection in Banana\n\n"
        "## Methods\n"
        "Direct PEG-mediated delivery of ribonucleoprotein into perennial banana cells.\n",
        encoding="utf-8",
    )
    (wiki / "sources" / "banana_peg.md").write_text(
        "# Clonal Propagation and PEG Transfection in Banana\n\n## Abstract Summary\nBanana editing.\n",
        encoding="utf-8",
    )

    # Paper 3: Mentions TaMFT, QPhs.ocs-3A.1, and 45.5%
    (raw_dir / "tamft_qtl.md").write_text(
        "# TaMFT Underlying Seed Dormancy QTL in Wheat\n\n"
        "## QTL Mapping\n"
        "TaMFT co-segregates with QPhs.ocs-3A.1 and qPHS-3A, conferring 45.5% dormancy increase at 10 mM ABA.\n",
        encoding="utf-8",
    )
    (wiki / "sources" / "tamft_qtl.md").write_text(
        "# TaMFT Underlying Seed Dormancy QTL in Wheat\n\n## Abstract Summary\nTaMFT QTL mapping.\n",
        encoding="utf-8",
    )

    # Paper 4: Vegetation control (must not expand)
    (raw_dir / "vegetation_ecology.md").write_text(
        "# Natural Vegetation Canopy Dynamics\n\n"
        "## Introduction\n"
        "Wild vegetation cover across temperate forests.\n",
        encoding="utf-8",
    )
    (wiki / "sources" / "vegetation_ecology.md").write_text(
        "# Natural Vegetation Canopy Dynamics\n\n## Abstract Summary\nForest vegetation survey.\n",
        encoding="utf-8",
    )

    engine = RAGEngine(wiki_folder=str(wiki))
    engine.search_engine.build_index()
    return engine, tmp_path


class TestSynonymExpander:
    """Milestone 3 Unit & Integration Tests."""

    def test_plant_genetics_synonym_clusters(self):
        """Verify all domain clusters are defined with comprehensive biotechnology synonyms."""
        assert "vegetatively propagated" in DOMAIN_SYNONYM_CLUSTERS
        veg = DOMAIN_SYNONYM_CLUSTERS["vegetatively propagated"]
        assert "clonal" in veg
        assert "tuber" in veg
        assert "potato" in veg
        assert "banana" in veg
        assert "poplar" in veg
        assert "citrus" in veg

        assert "transgene-free" in DOMAIN_SYNONYM_CLUSTERS
        tg = DOMAIN_SYNONYM_CLUSTERS["transgene-free"]
        assert "dna-free" in tg
        assert "marker-free" in tg
        assert "rnp" in tg
        assert "ribonucleoprotein" in tg

        assert "protoplast" in DOMAIN_SYNONYM_CLUSTERS
        proto = DOMAIN_SYNONYM_CLUSTERS["protoplast"]
        assert "single cell" in proto
        assert "peg transfection" in proto

        assert "meristem" in DOMAIN_SYNONYM_CLUSTERS
        meri = DOMAIN_SYNONYM_CLUSTERS["meristem"]
        assert "shoot apical meristem" in meri
        assert "sam" in meri

        assert "viral vector" in DOMAIN_SYNONYM_CLUSTERS
        viral = DOMAIN_SYNONYM_CLUSTERS["viral vector"]
        assert "vige" in viral
        assert "geminivirus" in viral
        assert "trv" in viral

    def test_exact_symbols_unmutated(self):
        """Verify exact gene symbols, QTLs, percentages, and measurements are protected verbatim."""
        engine = RAGEngine()
        query = "TaMFT seed dormancy QPhs.ocs-3A.1 45.5% at 37°C and 10 mM"
        clauses = engine._decompose_and_expand_clauses(query)

        assert len(clauses) >= 1
        all_tokens = [tok for _, tokens in clauses for tok in tokens]

        assert "TaMFT" in all_tokens
        assert "QPhs.ocs-3A.1" in all_tokens
        assert "45.5%" in all_tokens
        assert "37°C" in all_tokens
        assert "10 mM" in all_tokens

    def test_cross_concept_recall_vegetative(self, tmp_path):
        """Verify querying 'vegetatively propagated crops transgene-free' retrieves potato and banana papers."""
        engine, _ = _setup_synonym_corpus(tmp_path)
        hits, _, _ = engine.retrieve("vegetatively propagated crops transgene-free", top_k=5)

        assert len(hits) >= 2
        paths = [h["path"] for h in hits]
        assert any("potato_rnp.md" in p for p in paths)
        assert any("banana_peg.md" in p for p in paths)
        # Vegetation paper should not rank top
        assert not any("vegetation_ecology.md" in p for p in paths[:2])

    def test_no_false_positive_substring_expansion(self):
        """Verify word boundary matching prevents false expansions of substrings like 'vegetation'."""
        engine = RAGEngine()
        clauses = engine._decompose_and_expand_clauses("vegetation canopy cover")
        all_tokens = [tok.lower() for _, tokens in clauses for tok in tokens]

        assert "potato" not in all_tokens
        assert "banana" not in all_tokens
        assert "clonal" not in all_tokens

    def test_empty_and_whitespace_query_expansion(self):
        """Verify empty and whitespace queries return empty list safely."""
        engine = RAGEngine()
        assert engine._decompose_and_expand_clauses("") == []
        assert engine._decompose_and_expand_clauses("   ") == []

    def test_mixed_case_and_roman_numerals(self):
        """Verify complex mixed-case gene symbols and suffixes remain intact."""
        engine = RAGEngine()
        query = "Cas12a TaMFT-A1 OsPP2C-a DMR6-2 IPR001841"
        clauses = engine._decompose_and_expand_clauses(query)
        all_tokens = [tok for _, tokens in clauses for tok in tokens]

        assert "Cas12a" in all_tokens
        assert "TaMFT-A1" in all_tokens
        assert "OsPP2C-a" in all_tokens
        assert "DMR6-2" in all_tokens
        assert "IPR001841" in all_tokens

    def test_multi_cluster_entity_preservation(self):
        """Verify queries with multiple synonym clusters without prepositions preserve protected entities."""
        engine = RAGEngine()
        query = "TaMFT Cas9 vegetatively propagated transgene-free"
        clauses = engine._decompose_and_expand_clauses(query)

        assert len(clauses) >= 2
        all_tokens = [tok for _, tokens in clauses for tok in tokens]

        assert "TaMFT" in all_tokens or "tamft" in [t.lower() for t in all_tokens]
        assert "Cas9" in all_tokens or "cas9" in [t.lower() for t in all_tokens]
        # Also ensure synonym clusters expanded
        all_lower = [t.lower() for t in all_tokens]
        assert "potato" in all_lower or "clonal" in all_lower
        assert "dna-free" in all_lower or "marker-free" in all_lower
