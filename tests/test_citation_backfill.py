"""Unit and integration tests for Citation Backfill (Milestone 5 / R5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rag_engine import CitationBackfillResult, RAGEngine


def _setup_backfill_corpus(tmp_path: Path) -> tuple[RAGEngine, Path]:
    """Create isolated test workspace for citation backfill."""
    wiki = tmp_path / "wiki"
    (wiki / "sources").mkdir(parents=True)
    raw_dir = tmp_path / "raw" / "papers" / "backfill"
    raw_dir.mkdir(parents=True)

    # Paper 1 with DOI and structured metadata
    (raw_dir / "poddar_2023_heat_treatment.md").write_text(
        "# Heat Treatment Enhances Cas9 RNP Editing in Wheat\n\n"
        "**Authors:** Suman Poddar, Jianping Chen, and Fredy Altpeter\n\n"
        "**DOI:** 10.1093/nar/gkz1136\n\n"
        "## Results\n"
        "Brief heat treatment at 37°C significantly enhances Cas9 ribonucleoprotein editing efficiency in wheat.\n",
        encoding="utf-8",
    )
    (wiki / "sources" / "poddar_2023_heat_treatment.md").write_text(
        "# Heat Treatment in Wheat\n\n## Abstract Summary\nHeat treatment Cas9 in wheat.\n",
        encoding="utf-8",
    )

    engine = RAGEngine(wiki_folder=str(wiki))
    engine.search_engine.build_index()
    return engine, tmp_path


class TestCitationBackfill:
    """Milestone 5 Citation Backfill Tests."""

    def test_backfill_primary_citation(self, tmp_path):
        """Verify backfilling citation returns complete structured metadata and wikilink markdown."""
        engine, _ = _setup_backfill_corpus(tmp_path)
        res = engine.backfill_citation("heat treatment enhances Cas9 RNP editing")

        assert isinstance(res, CitationBackfillResult)
        assert res.statement == "heat treatment enhances Cas9 RNP editing"
        assert res.slug == "poddar_2023_heat_treatment"
        assert res.markdown_citation == "(Poddar et al., 2023)[[poddar_2023_heat_treatment]]"
        assert res.doi == "10.1093/nar/gkz1136"
        assert "Poddar" in res.authors
        assert res.year == 2023
        assert "heat treatment" in res.excerpt.lower()
        assert res.total_ms > 0

    def test_backfill_prefers_content_relevance_over_title_bias(self, tmp_path):
        """Verify backfill selects paper with specific statement text over generic title matches."""
        # Use canonical raw/ layout so FullTextSearch.raw_root resolves correctly
        wiki = tmp_path / "wiki"
        (wiki / "sources").mkdir(parents=True)
        raw_dir = tmp_path / "raw" / "papers" / "backfill"
        raw_dir.mkdir(parents=True)

        # Paper A: Generic title match with high BM25 title weights
        (raw_dir / "generic_title_enhances_cas9.md").write_text(
            "# Enhances CRISPR Cas9 Genome Editing Efficiency\n\n"
            "## Discussion\n"
            "Chemical additives increase general Cas9 editing efficiency.\n",
            encoding="utf-8",
        )
        (wiki / "sources" / "generic_title_enhances_cas9.md").write_text(
            "# Enhances CRISPR Cas9\n\n## Abstract Summary\nChemical additives.\n",
            encoding="utf-8",
        )

        # Paper B: Specific experimental text in body (Poddar) — no heat/treatment in title
        (raw_dir / "poddar_2023_heat_treatment.md").write_text(
            "# Optimization of editing in wheat\n\n"
            "**DOI:** 10.1093/nar/gkz1136\n\n"
            "## Results\n"
            "Heat treatment at 37°C significantly enhances Cas9 RNP editing efficiency in wheat.\n",
            encoding="utf-8",
        )
        (wiki / "sources" / "poddar_2023_heat_treatment.md").write_text(
            "# Optimization of editing in wheat\n\n## Abstract Summary\nHeat treatment Cas9.\n",
            encoding="utf-8",
        )

        engine = RAGEngine(wiki_folder=str(wiki))
        engine.search_engine.build_index()

        res = engine.backfill_citation("heat treatment enhances Cas9 RNP editing")
        assert res.slug == "poddar_2023_heat_treatment"
        assert "Poddar" in res.markdown_citation
        assert "heat treatment" in res.excerpt.lower()

    def test_backfill_slug_author_initials(self, tmp_path):
        """Verify author surname extraction from slugs with author initials or prefixes."""
        # Use canonical raw/ layout so FullTextSearch.raw_root resolves correctly
        wiki = tmp_path / "wiki"
        (wiki / "sources").mkdir(parents=True)
        raw_dir = tmp_path / "raw" / "papers" / "backfill"
        raw_dir.mkdir(parents=True)

        (raw_dir / "s_bhattacharjee_2023_coda.md").write_text(
            "# Strategic Transgene-Free Approaches of CRISPR in Plants\n\n"
            "**DOI:** 10.1016/j.plantsci.2023.111648\n\n"
            "## Negative Selection\n"
            "Application of codA negative selection enables rapid screening of transgene-free progeny.\n",
            encoding="utf-8",
        )
        (wiki / "sources" / "s_bhattacharjee_2023_coda.md").write_text(
            "# Strategic Transgene-Free Approaches\n\n## Abstract Summary\ncodA selection.\n",
            encoding="utf-8",
        )

        engine = RAGEngine(wiki_folder=str(wiki))
        engine.search_engine.build_index()

        res = engine.backfill_citation("codA negative selection enables transgene-free")
        assert res.slug == "s_bhattacharjee_2023_coda"
        assert "Bhattacharjee" in res.markdown_citation
        assert "Author" not in res.markdown_citation
        assert res.year == 2023

    def test_backfill_empty_statement(self, tmp_path):
        """Verify empty statement returns blank citation result safely."""
        engine, _ = _setup_backfill_corpus(tmp_path)
        res = engine.backfill_citation("   ")

        assert isinstance(res, CitationBackfillResult)
        assert res.slug == ""
        assert res.markdown_citation == ""
        assert res.year == 0

    def test_backfill_subsecond_performance(self, tmp_path):
        """Verify citation backfill completes in sub-second time (<1.0s)."""
        engine, _ = _setup_backfill_corpus(tmp_path)
        res = engine.backfill_citation("heat treatment Cas9")

        assert res.total_ms < 1000.0  # < 1.0s target

    def test_backfill_to_dict_and_json(self, tmp_path):
        """Verify to_dict produces valid JSON with required schema fields."""
        engine, _ = _setup_backfill_corpus(tmp_path)
        res = engine.backfill_citation("heat treatment Cas9")
        d = res.to_dict()

        assert "statement" in d
        assert "markdown_citation" in d
        assert "slug" in d
        assert "doi" in d
        assert "title" in d
        assert "authors" in d
        assert "year" in d
        assert "excerpt" in d
        assert "total_ms" in d

        # Must be JSON serializable
        json_str = json.dumps(d)
        assert len(json_str) > 0
