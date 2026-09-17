"""Tests and benchmarks for optimized retrieval and indexing routines."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from rag_engine import _jaccard_similarity, _tokenize_text_set
from research_retrieval import FullTextSearch, _is_excluded_path
from wiki_vocabulary import VocabularyEntry, VocabularyIndex, _build_alias_to_slug, get_index


def test_is_excluded_path_equivalence():
    """Verify _is_excluded_path accurately identifies excluded and clean paths."""
    assert not _is_excluded_path("sources/uncategorized/Wang_2024.md")
    assert not _is_excluded_path(Path("sources/uncategorized/Wang_2024.md"))
    assert not _is_excluded_path("entities/TaMFT.md")
    assert not _is_excluded_path("concepts/seed-dormancy.md")
    assert not _is_excluded_path("")
    assert not _is_excluded_path(None)

    # Excluded attic and pre-agent paths
    assert _is_excluded_path(".attic/sources/old.md")
    assert _is_excluded_path("sources/.attic/old.md")
    assert _is_excluded_path(Path("wiki/.attic/sources/old.md"))
    assert _is_excluded_path("sources/uncategorized/Wang_2024.pre-agent.md")
    assert _is_excluded_path(Path("sources/uncategorized/Wang_2024.pre-agent.md"))


def test_jaccard_similarity_accuracy():
    """Verify Jaccard similarity mathematical precision with union optimization."""
    set1 = {"gene", "dormancy", "wheat", "tamft"}
    set2 = {"gene", "dormancy", "barley", "hvmft"}
    # intersection = {"gene", "dormancy"} -> 2
    # union = 4 + 4 - 2 = 6
    # jaccard = 2 / 6 = 1/3 ~ 0.3333333333333333
    sim = _jaccard_similarity(set1, set2)
    assert pytest.approx(sim, 0.0001) == 2.0 / 6.0

    # Disjoint sets
    assert _jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0
    # Empty sets
    assert _jaccard_similarity(set(), {"a"}) == 0.0
    assert _jaccard_similarity(set(), set()) == 0.0
    # Identical sets
    assert _jaccard_similarity({"x", "y"}, {"x", "y"}) == 1.0


def test_document_markers_fast_set_operations():
    """Verify _document_markers fast set intersection logic."""
    search = FullTextSearch()
    search.index["doc1"] = {"tamft": 2, "dormancy": 5}
    search.doc_metadata["doc1"] = {
        "title_terms": {"wheat": 1, "seed": 1},
        "tag_terms": {"dormancy": 1},
    }

    contexts, has_dormancy, has_tf = search._document_markers("doc1")
    assert has_dormancy is True
    assert "seed_dormancy" in contexts
    assert search._document_marker_cache.get("doc1") == (contexts, has_dormancy, has_tf)


def test_vocabulary_index_alias_mapping():
    """Verify VocabularyIndex alias normalization and retrieval."""
    entries = {
        "tamft": VocabularyEntry(
            slug="tamft",
            title="TaMFT",
            kind="entity",
            aliases=("TaPHS1", "Mother of FT"),
        ),
        "seed-dormancy": VocabularyEntry(
            slug="seed-dormancy",
            title="Seed Dormancy",
            kind="concept",
            aliases=("grain dormancy", "primary dormancy"),
        ),
    }
    alias_map = _build_alias_to_slug(entries)
    assert alias_map["taphs1"] == "tamft"
    assert alias_map["mother of ft"] == "tamft"
    assert alias_map["grain dormancy"] == "seed-dormancy"
    assert alias_map["primary dormancy"] == "seed-dormancy"


def test_full_text_search_throttled_validation():
    """Verify load_index reuses loaded index within validation interval."""
    search = FullTextSearch()
    search.load_index()
    assert len(search.doc_metadata) > 0

    t0 = time.perf_counter()
    # Second load within interval should be sub-millisecond
    search.load_index()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert elapsed_ms < 5.0, f"Expected instant cached load (<5ms), got {elapsed_ms:.2f}ms"
