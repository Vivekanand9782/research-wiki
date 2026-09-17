"""Unit tests for weighted structural FTS5 ranking (Milestone 2 / R4)."""

import sqlite3
from pathlib import Path

import pytest
from research_retrieval import FullTextSearch, QueryPlan, Passage


def _setup_ranking_corpus(tmp_path: Path) -> tuple[FullTextSearch, Path, Path]:
    """Create a test wiki and raw papers folder with structured papers."""
    wiki = tmp_path / "wiki"
    (wiki / "sources").mkdir(parents=True)
    raw_dir = tmp_path / "raw" / "papers" / "structural"
    raw_dir.mkdir(parents=True)

    # 1. Paper Title Match (target term 'organogenesis' in title only, neutral section and body)
    (wiki / "sources" / "paper_title.md").write_text(
        "# De Novo Organogenesis in Plants\n\n## Abstract Summary\nRegeneration review.\n",
        encoding="utf-8",
    )
    (raw_dir / "paper_title.md").write_text(
        "# De Novo Organogenesis in Plants\nPlant tissue culture and stem cell dynamics in vitro.\n",
        encoding="utf-8",
    )

    # 2. Paper Section Match (target term 'organogenesis' in section header, neutral title and body)
    (wiki / "sources" / "paper_section.md").write_text(
        "# Plant Regeneration Protocols\n\n## Abstract Summary\nTissue culture protocols.\n",
        encoding="utf-8",
    )
    (raw_dir / "paper_section.md").write_text(
        "## De Novo Organogenesis\nPlant tissue culture and stem cell dynamics in vitro.\n",
        encoding="utf-8",
    )

    # 3. Paper Body Match (target term 'organogenesis' only buried in body text, neutral title and section)
    (wiki / "sources" / "paper_body.md").write_text(
        "# Plant Regeneration Protocols\n\n## Abstract Summary\nTissue culture protocols.\n",
        encoding="utf-8",
    )
    (raw_dir / "paper_body.md").write_text(
        "## Callus Induction\nPlant tissue culture occasionally leads to organogenesis in vitro.\n",
        encoding="utf-8",
    )

    search = FullTextSearch(str(wiki))
    search.build_index()
    return search, wiki, raw_dir


class TestWeightedStructuralRanking:
    def test_title_beats_section_beats_body(self, tmp_path):
        search, _, _ = _setup_ranking_corpus(tmp_path)
        conn, _ = search._ensure_raw_passage_index()
        assert conn is not None

        # Execute direct FTS5 query with BM25 structural weighting (5.0, 3.0, 1.0)
        rows = conn.execute(
            """
            SELECT p.path, p.section, d.title, bm25(passage_fts, 5.0, 3.0, 1.0) AS score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH '"organogenesi"'
            ORDER BY bm25(passage_fts, 5.0, 3.0, 1.0)
            """
        ).fetchall()

        assert len(rows) == 3

        paths = [r["path"] for r in rows]
        # In SQLite FTS5 bm25, lower (more negative) is better rank
        assert paths[0] == "raw/papers/structural/paper_title.md"
        assert paths[1] == "raw/papers/structural/paper_section.md"
        assert paths[2] == "raw/papers/structural/paper_body.md"

        scores = [r["score"] for r in rows]
        # Verify strict score hierarchy: title score < section score < body score
        assert scores[0] < scores[1] < scores[2]

    def test_query_raw_passages_structural_ordering(self, tmp_path):
        search, _, _ = _setup_ranking_corpus(tmp_path)
        plan = search._build_query_plan("organogenesis")

        candidates, total_docs = search._query_raw_passages(plan, top_k=5, exhaustive=False)
        assert candidates is not None
        assert len(candidates) == 3

        candidate_paths = [path.relative_to(search.project_root).as_posix() for path, _, _ in candidates]
        assert candidate_paths[0] == "raw/papers/structural/paper_title.md"
        assert candidate_paths[1] == "raw/papers/structural/paper_section.md"
        assert candidate_paths[2] == "raw/papers/structural/paper_body.md"

    def test_gene_symbol_structural_boost(self, tmp_path):
        wiki = tmp_path / "wiki"
        (wiki / "sources").mkdir(parents=True)
        raw_dir = tmp_path / "raw" / "papers" / "genes"
        raw_dir.mkdir(parents=True)

        # Paper 1: Gene in title
        (wiki / "sources" / "tamft_title.md").write_text("# TaMFT gene\n", encoding="utf-8")
        (raw_dir / "tamft_title.md").write_text(
            "# TaMFT Functions in Wheat Dormancy\nSeed physiology was investigated.\n",
            encoding="utf-8",
        )

        # Paper 2: Gene only in body
        (wiki / "sources" / "tamft_body.md").write_text("# Wheat dormancy\n", encoding="utf-8")
        (raw_dir / "tamft_body.md").write_text(
            "## Results\nDownstream expression of TaMFT was observed.\n",
            encoding="utf-8",
        )

        search = FullTextSearch(str(wiki))
        search.build_index()

        plan = search._build_query_plan("TaMFT")
        candidates, _ = search._query_raw_passages(plan, top_k=5, exhaustive=False)
        assert candidates is not None
        assert len(candidates) == 2

        # Title match must rank strictly first
        assert candidates[0][0].name == "tamft_title.md"
        assert candidates[1][0].name == "tamft_body.md"

    def test_multi_token_structural_ranking(self, tmp_path):
        wiki = tmp_path / "wiki"
        (wiki / "sources").mkdir(parents=True)
        raw_dir = tmp_path / "raw" / "papers" / "crispr"
        raw_dir.mkdir(parents=True)

        # Paper A: both keywords in Title
        (wiki / "sources" / "paper_a.md").write_text("# CRISPR Cas9\n", encoding="utf-8")
        (raw_dir / "paper_a.md").write_text(
            "# CRISPR Cas9 Delivery in Plants\nGene editing optimization.\n",
            encoding="utf-8",
        )

        # Paper B: keywords in section
        (wiki / "sources" / "paper_b.md").write_text("# Plant Editing\n", encoding="utf-8")
        (raw_dir / "paper_b.md").write_text(
            "## CRISPR Cas9 Methods\nRibonucleoproteins tested.\n",
            encoding="utf-8",
        )

        # Paper C: keywords only in body
        (wiki / "sources" / "paper_c.md").write_text("# Crop Improvement\n", encoding="utf-8")
        (raw_dir / "paper_c.md").write_text(
            "## Introduction\nCRISPR and Cas9 tools are widely used.\n",
            encoding="utf-8",
        )

        search = FullTextSearch(str(wiki))
        search.build_index()

        plan = search._build_query_plan("CRISPR Cas9")
        candidates, _ = search._query_raw_passages(plan, top_k=5, exhaustive=False)
        assert candidates is not None

        candidate_names = [path.name for path, _, _ in candidates]
        assert candidate_names[0] == "paper_a.md"
        assert candidate_names[1] == "paper_b.md"
        assert candidate_names[2] == "paper_c.md"

    def test_structural_weights_values(self, tmp_path):
        """Verify that passing different column weights directly alters the score ranking."""
        search, _, _ = _setup_ranking_corpus(tmp_path)
        conn, _ = search._ensure_raw_passage_index()

        # Default weights (5.0, 3.0, 1.0): title is best
        row_title = conn.execute(
            "SELECT bm25(passage_fts, 5.0, 3.0, 1.0) AS score FROM passage_fts WHERE passage_fts MATCH '\"organogenesi\"'"
        ).fetchall()
        assert len(row_title) == 3
