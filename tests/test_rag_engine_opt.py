"""Regression tests for the local RAG engine (rag_engine.RAGEngine).

Covers the FTS stemming fix in ``_fast_fts_search``: the persistent raw passage
index stores *stemmed* tokens, so an unstemmed query silently missed the vast
majority of matches for inflected words. The fix emits both the raw and the
stemmed FTS token per query word, making the match set a strict superset of the
old behaviour while recovering the stemmed hits.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _build_tiny_index(tmp_path):
    """Build a real (tiny) wiki + raw passage index under tmp_path."""
    import research_retrieval as rr

    wiki = tmp_path / "wiki"
    (wiki / "sources").mkdir(parents=True)
    raw_papers = tmp_path / "raw" / "papers"
    raw_papers.mkdir(parents=True)

    (wiki / "sources" / "demo.md").write_text(
        "# Demo study\n\n## Abstract Summary\nGene editing overview in wheat.\n",
        encoding="utf-8",
    )
    # Surface words 'editing', 'plants', 'regulating' are stored stemmed
    # ('edit', 'plant', 'regulat') by the index tokenizer.
    (raw_papers / "demo.md").write_text(
        "# Demo study\n\n## Results\n"
        "The editing of plants regulating growth was observed in wheat.\n",
        encoding="utf-8",
    )

    fts = rr.FullTextSearch(str(wiki))
    fts.build_index()
    raw_index = tmp_path / "raw" / rr.RAW_PASSAGE_INDEX_FILENAME
    assert raw_index.exists(), "raw passage index should have been built"
    return wiki, raw_index


def _engine_for(tmp_path):
    rag_engine = pytest.importorskip("rag_engine")
    wiki, raw_index = _build_tiny_index(tmp_path)
    engine = rag_engine.RAGEngine(wiki_folder=str(wiki))
    # RAGEngine defaults raw_index_path to the real corpus; point it at ours.
    engine.raw_index_path = raw_index
    engine._db_conn = None
    return engine


def test_fast_fts_matches_inflected_query_via_stemming(tmp_path):
    """'regulating' is stored only as the stem 'regulat'; the fix still hits."""
    engine = _engine_for(tmp_path)

    hits = engine._fast_fts_search("regulating", candidate_pool_size=10)

    assert hits, "stemmed-index query should match the inflected term"
    assert any("regulating" in h["full_context"].lower() for h in hits)


def test_fast_fts_matches_multiword_inflected_query(tmp_path):
    """A multi-word inflected query ('editing plants') resolves via stems."""
    engine = _engine_for(tmp_path)

    hits = engine._fast_fts_search("editing plants", candidate_pool_size=10)

    assert hits
    assert any("editing" in h["full_context"].lower() for h in hits)


def test_fast_fts_query_includes_raw_and_stemmed_tokens(tmp_path):
    """The FTS MATCH expression carries both the raw and stemmed token per word,
    guaranteeing the result set is a superset of the pre-fix behaviour."""
    engine = _engine_for(tmp_path)

    recorded: list = []

    class _RecordingCursor:
        def __init__(self, cursor):
            self._cursor = cursor

        def execute(self, sql, params=()):
            recorded.append((sql, params))
            return self._cursor.execute(sql, params)

        def __getattr__(self, name):
            return getattr(self._cursor, name)

    class _RecordingConn:
        def __init__(self, conn):
            self._conn = conn

        def cursor(self):
            return _RecordingCursor(self._conn.cursor())

        def __getattr__(self, name):
            return getattr(self._conn, name)

    engine._db_conn = _RecordingConn(engine._get_db())
    engine._fast_fts_search("editing", candidate_pool_size=5)

    matches = [p[0] for sql, p in recorded if "passage_fts MATCH" in sql and p]
    assert matches, "expected an FTS MATCH query to be executed"
    match_expr = matches[0]
    # raw 'editing' AND stemmed 'edit' must both be present.
    assert '"editing"' in match_expr
    assert '"edit"' in match_expr


def test_fast_fts_empty_query_returns_no_hits(tmp_path):
    """Degenerate all-short-token query yields no hits (wiki search covers it)."""
    engine = _engine_for(tmp_path)
    assert engine._fast_fts_search("a to of", candidate_pool_size=10) == []


def test_mmr_score_normalization_and_monotonicity(tmp_path):
    """Ensure top BM25 scores (most negative rank / highest abs score) are prioritized."""
    engine = _engine_for(tmp_path)
    candidates = [
        {
            "paper": "paper_c",
            "title": "Paper C",
            "canonical_key": "paper_c",
            "section": "Section C",
            "path": "raw/papers/paper_c.md",
            "lines": "1-10",
            "score": -10.0,  # Weak match
            "full_context": "Gene editing in wheat using TALENs.",
        },
        {
            "paper": "paper_b",
            "title": "Paper B",
            "canonical_key": "paper_b",
            "section": "Section B",
            "path": "raw/papers/paper_b.md",
            "lines": "1-10",
            "score": -20.0,  # Medium match
            "full_context": "CRISPR-Cas9 mediated genome modifications in maize plants.",
        },
        {
            "paper": "paper_a",
            "title": "Paper A",
            "canonical_key": "paper_a",
            "section": "Section A",
            "path": "raw/papers/paper_a.md",
            "lines": "1-10",
            "score": -30.0,  # Strongest match
            "full_context": "Direct delivery of Cas9 ribonucleoproteins into potato protoplasts.",
        },
    ]

    selected = engine._apply_section_aware_mmr(
        candidates=candidates,
        top_k=3,
        max_per_paper=1,
        lambda_rel=0.99,  # Strong relevance weight to test monotonicity
    )

    assert len(selected) == 3
    # Top score (-30.0, abs=30.0) must be ranked 1st, followed by -20.0 then -10.0
    assert selected[0]["paper"] == "paper_a"
    assert selected[1]["paper"] == "paper_b"
    assert selected[2]["paper"] == "paper_c"


def test_classify_intent_mechanistic_vs_survey(tmp_path):
    """Verify intent classifier assigns proper paper limits for techniques vs survey."""
    engine = _engine_for(tmp_path)

    intent, max_per_paper, _ = engine._classify_intent("Explain the techniques for generating transgenic crops")
    assert intent == "mechanistic_deep_dive"
    assert max_per_paper == 3  # Allows multi-section context from rich review papers

    intent, max_per_paper, _ = engine._classify_intent("Exhaustive list of all genes in wheat")
    assert intent == "survey_list"
    assert max_per_paper == 1


def test_query_decomposition_multitopic(tmp_path):
    """Verify multi-topic queries with scaffolding prefixes, commas, and 'and' decompose cleanly."""
    engine = _engine_for(tmp_path)

    q = "Explain the techniques for generating transgenic fish, nominated plants, and vegetatively propagated crops."
    subqueries = engine._decompose_query(q)
    assert subqueries == ["transgenic fish", "nominated plants", "vegetatively propagated crops"]

    q_comp = "Compare CRISPR-Cas9 vs TALENs in barley"
    sub_comp = engine._decompose_query(q_comp)
    assert "CRISPR-Cas9" in sub_comp
    assert "TALENs in barley" in sub_comp or "TALENs" in sub_comp

