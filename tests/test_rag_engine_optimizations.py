"""Unit tests verifying Local RAG engine optimizations."""

import sqlite3
import pytest
from pathlib import Path
from rag_engine import (
    RAGEngine,
    _jaccard_similarity,
    _extract_scientific_entities,
    verify_rag_grounding,
)


def test_phrase_or_proximity_sliding_window_accuracy():
    """Verify linear O(N) sliding window correctly identifies phrases and clustered tokens."""
    # Exact phrase
    assert RAGEngine._phrase_or_proximity("transgenic wheat lines were developed", ["transgenic", "wheat"]) is True
    
    # Clustered within window (window=240)
    text_clustered = "transgenic " + ("filler " * 10) + "wheat"
    assert RAGEngine._phrase_or_proximity(text_clustered, ["transgenic", "wheat"], window=240) is True
    
    # Far apart beyond window
    text_separated = "transgenic " + ("filler " * 100) + "wheat"
    assert RAGEngine._phrase_or_proximity(text_separated, ["transgenic", "wheat"], window=100) is False
    
    # Single token always True
    assert RAGEngine._phrase_or_proximity("any text", ["any"]) is True
    
    # Multi-token threshold (e.g. 3 tokens -> needed=2)
    text_three = "alpha is expressed in beta tissues while gamma is absent"
    assert RAGEngine._phrase_or_proximity(text_three, ["alpha", "beta", "gamma"], window=200) is True


def test_intent_classification_precompiled_patterns():
    """Verify intent classification accurately handles deep-dive, survey, and mechanistic queries."""
    engine = RAGEngine()
    
    intent, cap, author = engine._classify_intent("In Andersson 2018 potato genome editing")
    assert intent == "paper_deep_dive"
    assert cap == 6
    assert author == "andersson"
    
    intent, cap, author = engine._classify_intent("exhaustive list of methods for DNA-free editing")
    assert intent == "survey_list"
    assert cap == 1
    assert author is None
    
    intent, cap, author = engine._classify_intent("molecular mechanism of TaMFT in seed dormancy regulation")
    assert intent == "mechanistic_deep_dive"
    assert cap == 3
    assert author is None
    
    intent, cap, author = engine._classify_intent("CRISPR Cas9 in wheat")
    assert intent == "general"
    assert cap == 2
    assert author is None


def test_query_decomposition():
    """Verify query decomposition splits multi-topic and comparative queries."""
    engine = RAGEngine()
    
    # Comparative
    subqueries = engine._decompose_query("compare CRISPR vs TALENs in potato")
    assert len(subqueries) == 2
    assert "CRISPR" in subqueries[0]
    assert "TALENs in potato" in subqueries[1]
    
    # Semicolon split
    subqueries = engine._decompose_query("seed dormancy in wheat; somatic embryogenesis in maize")
    assert len(subqueries) == 2
    assert "seed dormancy in wheat" in subqueries
    assert "somatic embryogenesis in maize" in subqueries


def test_verify_rag_grounding_slug_and_entity():
    """Verify grounding verification extracts entities and detects valid/invalid citations."""
    wiki_dir = Path(__file__).resolve().parent.parent / "wiki"
    
    answer = (
        "In wheat (*Triticum aestivum*), **[[tamft]]** regulates seed dormancy with an editing efficiency of 45.5%. "
        "Mutations in *TaMFT-A1* were analyzed by (Author, 2020)[[fake_nonexistent_paper_slug_xyz123]].\n\n"
        "## References\n"
        "- Author (2020). [[fake_nonexistent_paper_slug_xyz123]]"
    )
    evidence_chunks = [
        "The TaMFT gene, including TaMFT-A1, controls seed dormancy in bread wheat with 45.5% germination reduction."
    ]
    retrieved_paths = {"sources/uncategorized/chen_2008_major_qtl_controlling.md"}
    
    ok, conf, verified, unsupported, invalid_cits = verify_rag_grounding(
        answer, evidence_chunks, retrieved_paths, wiki_dir
    )
    
    assert "fake_nonexistent_paper_slug_xyz123" in invalid_cits
    assert "45.5%" in verified
    assert "TaMFT" in verified or "TaMFT-A1" in verified
