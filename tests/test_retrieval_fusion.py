"""Regression tests for dual-channel rank fusion in ``rag_engine.RAGEngine.retrieve``.

Guards three defects found by comparing retrieval output across ``top_k`` values:

1. **Channel starvation.** The raw full-text FTS5 channel and the wiki
   knowledge-graph channel score on incomparable scales (FTS5 ``rank`` is
   negative; wiki scores are positive magnitudes in the hundreds). Mixing them
   by raw score let the wiki channel crowd the raw-passage channel out of the
   result set entirely. Fusion must be rank-based.
2. **Non-monotonicity in top_k.** Candidate pools derived from ``top_k`` made the
   whole ranking shift when ``top_k`` changed -- the highest-scoring hit at
   ``top_k=10`` could disappear at ``top_k=12``. Pools are now constant.
3. **Query-specific overfitting.** The out-of-domain guardrail must not contain
   hard-coded paper names or topic terms, or it stops generalising beyond the
   queries it was developed against.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _build_index(tmp_path, n_papers: int = 16):
    """Build a real (small) wiki + raw passage index with several distinct papers."""
    import research_retrieval as rr

    wiki = tmp_path / "wiki"
    (wiki / "sources").mkdir(parents=True)
    raw_papers = tmp_path / "raw" / "papers"
    raw_papers.mkdir(parents=True)

    for i in range(n_papers):
        (raw_papers / f"paper_{i:02d}.md").write_text(
            f"# Transformation study {i}\n\n"
            f"## Results\n"
            f"Agrobacterium mediated transformation of cassava cultivar C{i} produced "
            f"somatic embryogenesis and regenerated plants in trial {i}. Friable "
            f"embryogenic callus was induced on medium supplemented with picloram, and "
            f"cotyledon stage somatic embryos were recovered after four weeks of "
            f"selection. Regenerated plantlets were acclimatised and transferred to "
            f"soil, where transformation efficiency was scored per explant across "
            f"three independent biological replicates of experiment {i}.\n\n"
            f"## Discussion\n"
            f"Particle bombardment of banana embryogenic cell suspension {i} gave "
            f"transgene free edited plants after selection. Biolistic delivery of the "
            f"editing cassette avoided stable integration, and the resulting clonal "
            f"lines were screened by PCR and restriction digest to confirm the absence "
            f"of vector backbone sequence in the regenerated population of trial {i}.\n",
            encoding="utf-8",
        )
        (wiki / "sources" / f"paper_{i:02d}.md").write_text(
            f"# Transformation study {i}\n\n## Abstract Summary\n"
            f"Cassava and banana transformation overview {i}.\n",
            encoding="utf-8",
        )

    fts = rr.FullTextSearch(str(wiki))
    fts.build_index()
    raw_index = tmp_path / "raw" / rr.RAW_PASSAGE_INDEX_FILENAME
    assert raw_index.exists(), "raw passage index should have been built"
    return wiki, raw_index


def _engine_for(tmp_path, n_papers: int = 16):
    rag_engine = pytest.importorskip("rag_engine")
    wiki, raw_index = _build_index(tmp_path, n_papers=n_papers)
    engine = rag_engine.RAGEngine(wiki_folder=str(wiki))
    engine.raw_index_path = raw_index
    engine._db_conn = None
    return engine


def _keys(hits):
    return [f"{h['path']}:{h['lines']}" for h in hits]


# --------------------------------------------------------------------------- #
# 1. Monotonicity in top_k
# --------------------------------------------------------------------------- #

def test_retrieve_is_monotonic_in_top_k(tmp_path):
    """A smaller top_k must return a strict prefix of a larger top_k."""
    engine = _engine_for(tmp_path)
    query = "Agrobacterium transformation of cassava and particle bombardment of banana"

    small, _, _ = engine.retrieve(query, top_k=4)
    large, _, _ = engine.retrieve(query, top_k=9)

    assert len(small) >= 1, "fixture should yield hits"
    assert _keys(small) == _keys(large)[: len(small)], (
        "retrieval is not monotonic in top_k: the smaller result is not a prefix "
        "of the larger one, so increasing top_k can drop a previously top-ranked hit"
    )


def test_candidate_pools_do_not_depend_on_top_k(tmp_path):
    """Pool sizes must be constants, not functions of top_k."""
    rag_engine = pytest.importorskip("rag_engine")
    assert isinstance(rag_engine._FTS_CANDIDATE_POOL, int)
    assert isinstance(rag_engine._WIKI_CANDIDATE_POOL, int)
    src = inspect.getsource(rag_engine.RAGEngine.retrieve)
    assert "top_k * " not in src and "top_k*" not in src, (
        "retrieve() must not derive candidate pool sizes from top_k; that is what "
        "made the ranking shift whenever top_k changed"
    )


# --------------------------------------------------------------------------- #
# 2. Rank-based fusion keeps both channels commensurate
# --------------------------------------------------------------------------- #

def test_fused_scores_are_rank_derived_not_raw_channel_scores(tmp_path):
    """Every fused score must be a bounded RRF value, not a native channel score."""
    rag_engine = pytest.importorskip("rag_engine")
    engine = _engine_for(tmp_path)
    hits, _, _ = engine.retrieve("cassava somatic embryogenesis transformation", top_k=8)
    assert hits

    # RRF contribution per list is at most weight/(k+1); total mass across the two
    # channels is therefore bounded well below the hundreds-magnitude wiki scores.
    ceiling = 1000.0 * 2.0 / (rag_engine._RRF_K + 1.0)
    for h in hits:
        assert h["score"] > 0, "fused scores should be positive RRF magnitudes"
        assert h["score"] <= ceiling, (
            f"score {h['score']} exceeds the RRF ceiling {ceiling}; a raw native "
            "channel score has leaked into the fused ranking"
        )
        assert "rrf_score" in h, "fused candidates should carry their raw RRF mass"


def test_raw_fulltext_channel_is_not_starved(tmp_path):
    """The raw full-text passage channel must survive fusion.

    AGENTS.md rule 16 requires RAG synthesis to run on raw full-text passages;
    a regression here means answers are grounded in short wiki summaries instead.
    """
    engine = _engine_for(tmp_path)
    hits, _, _ = engine.retrieve("cassava banana transformation regenerated plants", top_k=8)
    assert hits
    raw_hits = [h for h in hits if str(h["path"]).startswith("raw/")]
    assert raw_hits, "no raw/papers passages survived fusion -- channel starvation regression"
    # Raw passages carry the whole passage body. Wiki-channel evidence is a
    # truncated snippet, so exceeding the snippet cap proves full-text grounding.
    assert max(len(h["full_context"]) for h in raw_hits) > 400


# --------------------------------------------------------------------------- #
# 3. The guardrail must stay generic
# --------------------------------------------------------------------------- #

def test_filter_by_relevance_has_no_query_specific_blacklist():
    """The out-of-domain guardrail must not hard-code papers or topic terms."""
    rag_engine = pytest.importorskip("rag_engine")
    src = inspect.getsource(rag_engine.RAGEngine._filter_by_relevance).lower()
    for banned in (
        "shinmyo",
        "mouse brain",
        "in utero",
        "food_laws",
        "rpsc",
        "nominated",
        "transgenic fish",
        "zebrafish",
        "salmon",
        "fish lj",
    ):
        assert banned not in src, (
            f"_filter_by_relevance contains the hard-coded token {banned!r}; the "
            "guardrail must be structural so it generalises to other queries"
        )


def test_phrase_or_proximity_accepts_phrase_and_rejects_scattered_terms():
    """Proximity is what separates a topical passage from a coincidental term match."""
    rag_engine = pytest.importorskip("rag_engine")
    prox = rag_engine.RAGEngine._phrase_or_proximity

    assert prox("techniques for generating transgenic fish embryos", ["transgenic", "fish"])
    # 'transgenic' about plants, with 'fish' only as a distant reference surname.
    scattered = (
        "transgenic wheat plants were regenerated after biolistic delivery. "
        + "filler text " * 60
        + "fish lj and jones rb, plant biotechnology journal"
    )
    assert not prox(scattered, ["transgenic", "fish"])


def test_phrase_or_proximity_single_token_always_passes():
    rag_engine = pytest.importorskip("rag_engine")
    assert rag_engine.RAGEngine._phrase_or_proximity("anything at all", ["cassava"])
