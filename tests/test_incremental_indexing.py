"""Unit tests for incremental SQLite FTS5 passage indexing and auto-sync (Milestone 1)."""

import os
import sqlite3
import time
from pathlib import Path

import pytest
from research_retrieval import FullTextSearch, RAW_PASSAGE_INDEX_VERSION


def _setup_corpus(tmp_path: Path) -> tuple[FullTextSearch, Path, Path]:
    """Create a test wiki and raw papers folder with initial test files."""
    wiki = tmp_path / "wiki"
    (wiki / "sources").mkdir(parents=True)
    raw_dir = tmp_path / "raw" / "papers" / "sample"
    raw_dir.mkdir(parents=True)

    (wiki / "sources" / "paper_a.md").write_text(
        "# Paper A\n\n## Abstract Summary\nInitial summary for paper A.\n",
        encoding="utf-8",
    )
    paper_a = raw_dir / "paper_a.md"
    paper_a.write_text(
        "# Paper A: Genetic Discovery\n\n## Results\n"
        "TaMFT gene expression controls wheat seed dormancy phenotypes.\n\n"
        "## Methods\nCRISPR editing in wheat embryos.\n",
        encoding="utf-8",
    )

    search = FullTextSearch(str(wiki))
    search.build_index()
    return search, wiki, raw_dir


class TestIncrementalIndexingSchema:
    def test_schema_version_3_structure(self, tmp_path):
        search, _, _ = _setup_corpus(tmp_path)
        conn, _ = search._ensure_raw_passage_index()
        assert conn is not None

        # Check metadata
        meta = dict(conn.execute("SELECT key, value FROM metadata").fetchall())
        assert meta.get("version") == str(RAW_PASSAGE_INDEX_VERSION)
        assert meta.get("version") == "3"
        assert "signature" in meta

        # Check raw_documents columns
        doc_cols = [r[1] for r in conn.execute("PRAGMA table_info(raw_documents)").fetchall()]
        assert set(doc_cols) == {"path", "title", "size", "mtime_ns"}

        # Check passages columns and index
        passage_cols = [r[1] for r in conn.execute("PRAGMA table_info(passages)").fetchall()]
        assert set(passage_cols) == {"id", "path", "section", "line_start", "line_end", "text"}

        indices = [r[1] for r in conn.execute("PRAGMA index_list(passages)").fetchall()]
        assert "idx_passages_path" in indices

        # Check passage_fts multi-column virtual table
        fts_cols = [r[1] for r in conn.execute("PRAGMA table_info(passage_fts)").fetchall()]
        assert "title" in fts_cols
        assert "section" in fts_cols
        assert "body" in fts_cols


class TestIncrementalAddModifyDelete:
    def test_incremental_add_paper(self, tmp_path):
        search, _, raw_dir = _setup_corpus(tmp_path)

        # 1. Add new paper with a unique token
        new_paper = raw_dir / "new_paper.md"
        new_paper.write_text(
            "# Novel Discovery\n\n## Results\n"
            "XyloseIsomeraseNovelAllele confers high efficiency transformation.\n",
            encoding="utf-8",
        )

        start_time = time.perf_counter()
        conn, paths = search._ensure_raw_passage_index()
        elapsed = time.perf_counter() - start_time

        assert elapsed < 1.5, f"Sync took too long: {elapsed:.3f}s"
        assert conn is not None

        # 2. Verify new passage is immediately searchable
        results = search.search("XyloseIsomeraseNovelAllele", mode="evidence", doc_type="paper")
        assert len(results) >= 1
        assert "XyloseIsomeraseNovelAllele" in results[0].snippet or "xyloseisomerasenovelallel" in results[0].snippet.lower()
        assert results[0].source_path == "raw/papers/sample/new_paper.md"
        assert search.last_search_report["raw_index_used"] is True

    def test_incremental_modify_paper(self, tmp_path):
        search, _, raw_dir = _setup_corpus(tmp_path)

        new_paper = raw_dir / "mutable_paper.md"
        new_paper.write_text(
            "# Mutable Paper\n\n## Results\n"
            "InitialAlleleToken active in target lines.\n",
            encoding="utf-8",
        )
        search._ensure_raw_passage_index()
        assert len(search.search("InitialAlleleToken", mode="evidence", doc_type="paper")) == 1

        # Modify file: replace token and change mtime
        st = new_paper.stat()
        new_paper.write_text(
            "# Mutable Paper\n\n## Results\n"
            "UpdatedVariantMarker replaces the previous allele.\n",
            encoding="utf-8",
        )
        os.utime(new_paper, ns=(st.st_atime_ns, st.st_mtime_ns + 100_000_000))

        search._ensure_raw_passage_index()

        # Old token must return 0 results; new token must return 1 result
        assert search.search("InitialAlleleToken", mode="evidence", doc_type="paper") == []
        updated_hits = search.search("UpdatedVariantMarker", mode="evidence", doc_type="paper")
        assert len(updated_hits) == 1
        assert updated_hits[0].source_path == "raw/papers/sample/mutable_paper.md"

        # Check no duplicate document records
        conn, _ = search._ensure_raw_passage_index()
        doc_count = conn.execute(
            "SELECT count(*) FROM raw_documents WHERE path = 'raw/papers/sample/mutable_paper.md'"
        ).fetchone()[0]
        assert doc_count == 1

    def test_incremental_delete_paper(self, tmp_path):
        search, _, raw_dir = _setup_corpus(tmp_path)

        new_paper = raw_dir / "ephemeral_paper.md"
        new_paper.write_text(
            "# Ephemeral Paper\n\n## Results\n"
            "EphemeralGeneMarker detected.\n",
            encoding="utf-8",
        )
        search._ensure_raw_passage_index()
        assert len(search.search("EphemeralGeneMarker", mode="evidence", doc_type="paper")) == 1

        # Delete file
        new_paper.unlink()
        search._ensure_raw_passage_index()

        assert search.search("EphemeralGeneMarker", mode="evidence", doc_type="paper") == []

        conn, _ = search._ensure_raw_passage_index()
        rel_path = "raw/papers/sample/ephemeral_paper.md"
        assert conn.execute("SELECT count(*) FROM raw_documents WHERE path = ?", (rel_path,)).fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM passages WHERE path = ?", (rel_path,)).fetchone()[0] == 0


class TestSchemaMigrationAndIntegrity:
    def test_outdated_schema_triggers_rebuild(self, tmp_path):
        search, _, _ = _setup_corpus(tmp_path)
        conn, _ = search._ensure_raw_passage_index()

        # Simulate older schema version
        conn.execute("UPDATE metadata SET value = '2' WHERE key = 'version'")
        conn.commit()
        search._close_raw_index()

        # Next sync must detect version mismatch and rebuild to v3
        new_conn, _ = search._ensure_raw_passage_index()
        assert new_conn is not None
        version = new_conn.execute("SELECT value FROM metadata WHERE key = 'version'").fetchone()[0]
        assert version == "3"

    def test_excluded_paths_are_skipped(self, tmp_path):
        search, _, raw_dir = _setup_corpus(tmp_path)

        attic_dir = raw_dir / ".attic"
        attic_dir.mkdir(parents=True)
        (attic_dir / "old_draft.md").write_text(
            "# Attic Draft\n\n## Results\nAtticUniqueDraftToken in storage.\n",
            encoding="utf-8",
        )

        preagent_file = raw_dir / "notes.pre-agent.md"
        preagent_file.write_text(
            "# Pre-agent\n\n## Results\nPreAgentSecretToken in storage.\n",
            encoding="utf-8",
        )

        search._ensure_raw_passage_index()
        assert search.search("AtticUniqueDraftToken", mode="evidence", doc_type="paper") == []
        assert search.search("PreAgentSecretToken", mode="evidence", doc_type="paper") == []

    def test_reference_sections_excluded_from_indexing(self, tmp_path):
        search, _, raw_dir = _setup_corpus(tmp_path)

        ref_paper = raw_dir / "ref_paper.md"
        ref_paper.write_text(
            "# Reference Test\n\n## Results\nValidTargetGene was characterized.\n\n"
            "## References\n1. Smith et al. IsolatedBibliographyCitationToken (2021) Nature 10.1038/s41586-021-00000-0\n"
            "2. Jones et al. (2022) Science 10.1126/science.1234567\n",
            encoding="utf-8",
        )
        search._ensure_raw_passage_index()

        # Valid content in Results is indexed
        assert len(search.search("ValidTargetGene", mode="evidence", doc_type="paper")) == 1

        # Pure citation tokens from bibliography are excluded
        assert search.search("IsolatedBibliographyCitationToken", mode="evidence", doc_type="paper") == []
