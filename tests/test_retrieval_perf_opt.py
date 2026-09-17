"""Regression tests for the retrieval performance optimizations.

Covers two changes:

1. ``WIKI_SEARCH_PHRASE_PREFILTER`` — a necessary-condition token prefilter in
   :meth:`FullTextSearch._bm25_score` that skips the tolerant full-text phrase
   regex for candidates that cannot contain the phrase. Must be *byte-for-byte*
   equivalent to the unconditional regex while calling the regex fewer times.

2. ``WIKI_VOCAB_VALIDATION_INTERVAL`` default raised to 30s so the recursive
   entity/concept ``stat`` walk is throttled between queries.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# Docs deliberately mix documents that DO and DO NOT contain the query phrases
# so the prefilter has candidates to skip.
_DOCS = {
    "smith_2024_seed.md": (
        "# Seed dormancy transcription factor in hexaploid wheat\n\n"
        "## Results\n"
        "The seed dormancy transcription factor tightly regulates germination "
        "in wheat grain and after-ripening.\n"
        + "dormancy germination seed grain regulation wheat " * 25
    ),
    "jones_2023_tf.md": (
        "# CRISPR editing of a transcription factor in rice\n\n"
        "## Results\n"
        "This study reports transcription factor activity during editing but no "
        "dormancy phenotype was observed.\n"
        + "transcription factor rice editing crispr activity " * 25
    ),
    "lee_2022_starch.md": (
        "# Starch branching enzyme characterization\n\n"
        "## Results\n"
        "Only starch, amylose, and enzyme kinetics are discussed here.\n"
        + "starch enzyme amylose kinetics granule " * 25
    ),
}

_PHRASE_QUERY = "seed dormancy transcription factor"


def _build_search(tmp_path):
    import research_retrieval as rr

    wiki = tmp_path / "wiki"
    sources = wiki / "sources"
    sources.mkdir(parents=True)
    for name, text in _DOCS.items():
        (sources / name).write_text(text, encoding="utf-8")
    search = rr.FullTextSearch(str(wiki))
    search.build_index()
    return search


def _fingerprint(results):
    return [
        (r.paper, round(r.score, 9), tuple(r.matches))
        for r in results
    ]


def test_phrase_prefilter_is_result_equivalent(tmp_path, monkeypatch):
    """Prefilter ON must yield identical ranking + scores to prefilter OFF."""
    import research_retrieval as rr

    search = _build_search(tmp_path)

    monkeypatch.setattr(rr, "PHRASE_PREFILTER_ENABLED", True)
    search._summary_query_cache.clear()
    on = search.search(_PHRASE_QUERY, top_k=10, mode="summary")

    monkeypatch.setattr(rr, "PHRASE_PREFILTER_ENABLED", False)
    search._summary_query_cache.clear()
    off = search.search(_PHRASE_QUERY, top_k=10, mode="summary")

    assert on, "expected non-empty results for the phrase query"
    assert _fingerprint(on) == _fingerprint(off)


def test_phrase_prefilter_is_equivalent_in_hybrid_mode(tmp_path, monkeypatch):
    """Hybrid mode (uncached) is also equivalent under the prefilter."""
    import research_retrieval as rr

    search = _build_search(tmp_path)

    monkeypatch.setattr(rr, "PHRASE_PREFILTER_ENABLED", True)
    on = search.search(_PHRASE_QUERY, top_k=10, mode="hybrid")
    monkeypatch.setattr(rr, "PHRASE_PREFILTER_ENABLED", False)
    off = search.search(_PHRASE_QUERY, top_k=10, mode="hybrid")

    assert _fingerprint(on) == _fingerprint(off)


def test_phrase_prefilter_skips_regex_for_impossible_documents(tmp_path, monkeypatch):
    """With the prefilter on, the phrase regex runs strictly fewer times."""
    import research_retrieval as rr

    search = _build_search(tmp_path)
    original = rr.FullTextSearch._contains_normalized_phrase
    counter = {"n": 0}

    def _counting(value, phrase):
        counter["n"] += 1
        return original(value, phrase)

    monkeypatch.setattr(
        rr.FullTextSearch,
        "_contains_normalized_phrase",
        staticmethod(_counting),
    )

    monkeypatch.setattr(rr, "PHRASE_PREFILTER_ENABLED", True)
    search._summary_query_cache.clear()
    search.search(_PHRASE_QUERY, top_k=10, mode="summary")
    on_calls = counter["n"]

    counter["n"] = 0
    monkeypatch.setattr(rr, "PHRASE_PREFILTER_ENABLED", False)
    search._summary_query_cache.clear()
    search.search(_PHRASE_QUERY, top_k=10, mode="summary")
    off_calls = counter["n"]

    assert off_calls > 0
    assert on_calls < off_calls


def test_query_plan_exposes_aligned_phrase_tokens(tmp_path):
    """Every plan phrase has an aligned tokenised entry used by the prefilter."""
    search = _build_search(tmp_path)
    plan = search._build_query_plan(_PHRASE_QUERY)

    assert plan.phrases, "domain phrases should be detected for this query"
    assert len(plan.phrase_tokens) == len(plan.phrases)
    for phrase, tokens in zip(plan.phrases, plan.phrase_tokens):
        assert tokens == tuple(search._tokenize(phrase))


def test_query_plan_phrase_tokens_default_empty():
    """Direct QueryPlan construction (e.g. _generate_snippet) stays valid."""
    import research_retrieval as rr

    plan = rr.QueryPlan(
        query="x",
        base_tokens=("x",),
        term_weights={"x": 1.0},
        phrases=(),
        canonical_terms=(),
    )
    assert plan.phrase_tokens == ()


def test_phrase_prefilter_enabled_by_default():
    """The optimization ships enabled; the disable path is exercised by the
    monkeypatched equivalence/skip tests above."""
    import research_retrieval as rr

    assert rr.PHRASE_PREFILTER_ENABLED is True


def test_vocab_default_interval_throttles_recursive_walk(tmp_path, monkeypatch):
    """With no env override, an immediate re-query skips the stat walk."""
    import wiki_vocabulary as vocabulary

    monkeypatch.delenv("WIKI_VOCAB_VALIDATION_INTERVAL", raising=False)
    wiki = tmp_path / "wiki"
    page = wiki / "entities" / "gene.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        "---\ntags: [entity]\ntype: entity\nsource_count: 1\n---\n\n"
        "# Gene\n\n" + "substantive description " * 20,
        encoding="utf-8",
    )
    vocabulary.reset_cache()
    first = vocabulary.get_index(wiki)

    def _fail(_root):
        raise AssertionError(
            "default interval should throttle the recursive stat walk"
        )

    monkeypatch.setattr(vocabulary, "_max_mtime", _fail)
    second = vocabulary.get_index(wiki)
    assert second is first
