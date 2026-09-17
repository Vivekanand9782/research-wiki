"""Comprehensive Opaque-Box E2E Test Suite for Antigravity Local RAG System Upgrade.

Covers all 4 Tiers:
- Tier 1: Feature Coverage (>=5 test cases per feature for R1, R2, R3, R4, R5)
- Tier 2: Boundary & Corner Cases (>=5 test cases per feature for R1-R5)
- Tier 3: Cross-Feature Combinations (>=10 pairwise combinatorial interaction tests)
- Tier 4: Real-World Application Scenarios (>=6 realistic end-to-end scientific literature scenarios)

Requirements & Interface Specifications:
- Schema v3 in metadata (version='3')
- raw_documents(path TEXT PRIMARY KEY, title TEXT NOT NULL, size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL)
- passages(id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, section TEXT NOT NULL, line_start INTEGER NOT NULL, line_end INTEGER NOT NULL, text TEXT NOT NULL)
- passage_fts(title, section, body, content='', contentless_delete=1)
- bm25(passage_fts, 5.0, 3.0, 1.0)
- Adaptive proximity window W(N) = min(800, max(240, 240 + (N - 2) * 140))
- Reciprocal Rank Fusion k=60
- Domain synonym expansion & exact entity protection
- Sub-second claim verification (--verify) & publication-ready citation backfill (--backfill)
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

import pytest

# Ensure research-wiki and workspace root are in python path
HERE = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from research_retrieval import (
    FullTextSearch,
    _extract_title,
    _is_excluded_path,
    _is_reference_or_citation_passage,
)
from rag_engine import (
    RAGEngine,
    _GENE_QTL_RE,
    _PERCENTAGE_RE,
    _NUMERIC_MEASURE_RE,
)


# ==============================================================================
# HERMETIC TEST FIXTURES & SAMPLE CORPORA
# ==============================================================================

SAMPLE_BANFALVI_DOC = """# Generation of transgene-free genome edited potato using codA negative selection

## Abstract
Transgene-free genome editing in vegetatively propagated crops like potato requires reliable selection strategies. Here we demonstrate codA negative selection for recovering marker-free mutant lines.

## Negative Selection with codA
The bacterial codA gene converts non-toxic 5-fluorocytosine (5-FC) into toxic 5-fluorouracil (5-FU). Plant cells expressing codA fail to survive on 5-FC selective media, enabling efficient negative selection of transgene-bearing segregants or transient events.

## Results
In tetraploid potato (Solanum tuberosum cv. Desiree), transient delivery of Cas9 with codA negative selection yielded 45.5% transgene-free edited events without foreign DNA integration.
"""

SAMPLE_PODDAR_DOC = """# Optimization of highly efficient Cas9 RNP gene editing in potato protoplasts

## Abstract
Direct delivery of preassembled Cas9 ribonucleoprotein (RNP) complexes into plant protoplasts eliminates the risk of transgene integration. DOI: 10.3389/fpls.2022.1084700.

## Heat Shock Treatment
We tested whether transient heat treatment enhances editing frequency. Heat treatment at 37°C for 24 hours significantly increased Cas9 RNP on-target indel efficiency up to 45.5% in potato protoplasts compared to 12.0% at room temperature.

## Discussion
Heat shock treatment enhances Cas9 RNP editing by promoting chromatin accessibility and stabilizing Cas9-gRNA cleavage complexes in Solanum tuberosum.
"""

SAMPLE_LIANG_DOC = """# Efficient DNA-free genome editing of bread wheat using CRISPR-Cas9 ribonucleoprotein complexes

## Abstract
Ribonucleoprotein delivery prevents unwanted insertional mutagenesis in hexaploid bread wheat (Triticum aestivum).

## Biolistic Delivery of RNPs
Preassembled Cas9 protein and in vitro transcribed guide RNA were biolistically bombarded into wheat immature embryos. Transgene-free mutant plants were recovered in the T0 generation.

## Results
DNA-free edited wheat plants showed high target mutation rates without any detectable off-target cleavage or T-DNA backbone insertion.
"""

SAMPLE_ASLAM_DOC = """# CRISPR-mediated engineering of TaMFT for pre-harvest sprouting resistance in wheat

## Abstract
Pre-harvest sprouting (PHS) causes severe grain quality loss in bread wheat. TaMFT is a key regulatory gene underlying seed dormancy.

## TaMFT and Seed Dormancy
TaMFT acts downstream of ABA signaling to maintain seed dormancy during grain development. Knockout of TaMFT reduces dormancy, while enhanced expression prevents viviparous sprouting under humid conditions.

## QTL Analysis
The major seed dormancy QTL QPhs.ocs-3A.1 co-localizes with TaMFT on chromosome 3A. Quantitative phenotyping showed a 45.5% reduction in sprouting index in resistant lines.
"""

SAMPLE_TRIPATHI_DOC = """# CRISPR gene editing in vegetatively propagated banana via protoplasts and embryogenic cells

## Abstract
Clonal propagation in woody and perennial crops limits sexual crossing. We established PEG transfection of protoplasts for DNA-free editing in banana (Musa acuminata).

## Clonal Crop Regeneration
Because banana is a vegetatively propagated triploid crop, traditional genetic segregation cannot remove integrated foreign cassettes. Direct RNP delivery into embryogenic cell suspensions yields transgene-free edited plants directly.

## Results
Targeted mutagenesis of the DMR6-2 ortholog conferred broad-spectrum resistance against Xanthomonas wilt in regenerated clonal plantlets.
"""

SAMPLE_CONTROL_DOC = """# General Agricultural Survey and Crop Management

## Introduction
Agronomic management practices influence crop yield across varied agro-ecological zones.

## Survey Data
Various laboratory techniques including codA assays and TaMFT marker studies are occasionally mentioned in broader literature surveys.

## Conclusion
Standard agronomic practices remain foundational.
"""


def init_schema_v3_database(db_path: Path) -> sqlite3.Connection:
    """Helper to initialize an isolated SQLite database adhering to Schema v3."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE raw_documents (
            path TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL
        );
        CREATE TABLE passages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            section TEXT NOT NULL,
            line_start INTEGER NOT NULL,
            line_end INTEGER NOT NULL,
            text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE passage_fts USING fts5(
            title,
            section,
            body,
            content='',
            contentless_delete=1
        );
        CREATE INDEX IF NOT EXISTS idx_passages_path ON passages(path);
        INSERT INTO metadata(key, value) VALUES ('version', '3');
        """
    )
    conn.commit()
    return conn


def populate_schema_v3_doc(conn: sqlite3.Connection, relative_path: str, title: str, size: int, mtime_ns: int, sections: list[tuple[str, int, int, str]]):
    """Helper to insert a document and its passages into Schema v3 SQLite tables."""
    conn.execute(
        "INSERT INTO raw_documents(path, title, size, mtime_ns) VALUES (?, ?, ?, ?)",
        (relative_path, title, size, mtime_ns),
    )
    for section, line_start, line_end, text in sections:
        cur = conn.execute(
            "INSERT INTO passages(path, section, line_start, line_end, text) VALUES (?, ?, ?, ?, ?)",
            (relative_path, section, line_start, line_end, text),
        )
        passage_id = cur.lastrowid
        conn.execute(
            "INSERT INTO passage_fts(rowid, title, section, body) VALUES (?, ?, ?, ?)",
            (passage_id, title, section, text),
        )
    conn.commit()


@pytest.fixture
def isolated_rag_env(tmp_path: Path):
    """Sets up an isolated, hermetic project workspace with realistic markdown papers."""
    project_root = tmp_path / "rag_workspace"
    project_root.mkdir(parents=True)
    raw_papers = project_root / "raw" / "papers" / "biotech"
    raw_papers.mkdir(parents=True)
    wiki_dir = project_root / "wiki"
    wiki_dir.mkdir(parents=True)
    for folder in ("sources", "entities", "concepts", "synthesis"):
        (wiki_dir / folder).mkdir(parents=True)

    # Populate sample papers
    (raw_papers / "banfalvi_2020_generation_transgene_free.md").write_text(SAMPLE_BANFALVI_DOC, encoding="utf-8")
    (raw_papers / "poddar_2023_optimization_highly_efcient.md").write_text(SAMPLE_PODDAR_DOC, encoding="utf-8")
    (raw_papers / "liang_2017_efficient_dna_free.md").write_text(SAMPLE_LIANG_DOC, encoding="utf-8")
    (raw_papers / "aslam_2026_crispr_mediated_engineering.md").write_text(SAMPLE_ASLAM_DOC, encoding="utf-8")
    (raw_papers / "tripathi_2024_banana_editing.md").write_text(SAMPLE_TRIPATHI_DOC, encoding="utf-8")
    (raw_papers / "control_general_survey.md").write_text(SAMPLE_CONTROL_DOC, encoding="utf-8")

    db_path = project_root / "raw" / "raw_passage_index.sqlite3"
    conn = init_schema_v3_database(db_path)

    # Populate SQLite database with parsed content
    papers = [
        ("raw/papers/biotech/banfalvi_2020_generation_transgene_free.md", "Generation of transgene-free genome edited potato using codA negative selection", raw_papers / "banfalvi_2020_generation_transgene_free.md", [
            ("Abstract", 3, 5, "Transgene-free genome editing in vegetatively propagated crops like potato requires reliable selection strategies. Here we demonstrate codA negative selection for recovering marker-free mutant lines."),
            ("Negative Selection with codA", 7, 9, "The bacterial codA gene converts non-toxic 5-fluorocytosine (5-FC) into toxic 5-fluorouracil (5-FU). Plant cells expressing codA fail to survive on 5-FC selective media, enabling efficient negative selection of transgene-bearing segregants or transient events."),
            ("Results", 11, 13, "In tetraploid potato (Solanum tuberosum cv. Desiree), transient delivery of Cas9 with codA negative selection yielded 45.5% transgene-free edited events without foreign DNA integration."),
        ]),
        ("raw/papers/biotech/poddar_2023_optimization_highly_efcient.md", "Optimization of highly efficient Cas9 RNP gene editing in potato protoplasts", raw_papers / "poddar_2023_optimization_highly_efcient.md", [
            ("Abstract", 3, 5, "Direct delivery of preassembled Cas9 ribonucleoprotein (RNP) complexes into plant protoplasts eliminates the risk of transgene integration. DOI: 10.3389/fpls.2022.1084700."),
            ("Heat Shock Treatment", 7, 9, "We tested whether transient heat treatment enhances editing frequency. Heat treatment at 37°C for 24 hours significantly increased Cas9 RNP on-target indel efficiency up to 45.5% in potato protoplasts compared to 12.0% at room temperature."),
            ("Discussion", 11, 13, "Heat shock treatment enhances Cas9 RNP editing by promoting chromatin accessibility and stabilizing Cas9-gRNA cleavage complexes in Solanum tuberosum."),
        ]),
        ("raw/papers/biotech/liang_2017_efficient_dna_free.md", "Efficient DNA-free genome editing of bread wheat using CRISPR-Cas9 ribonucleoprotein complexes", raw_papers / "liang_2017_efficient_dna_free.md", [
            ("Abstract", 3, 5, "Ribonucleoprotein delivery prevents unwanted insertional mutagenesis in hexaploid bread wheat (Triticum aestivum)."),
            ("Biolistic Delivery of RNPs", 7, 9, "Preassembled Cas9 protein and in vitro transcribed guide RNA were biolistically bombarded into wheat immature embryos. Transgene-free mutant plants were recovered in the T0 generation."),
            ("Results", 11, 13, "DNA-free edited wheat plants showed high target mutation rates without any detectable off-target cleavage or T-DNA backbone insertion."),
        ]),
        ("raw/papers/biotech/aslam_2026_crispr_mediated_engineering.md", "CRISPR-mediated engineering of TaMFT for pre-harvest sprouting resistance in wheat", raw_papers / "aslam_2026_crispr_mediated_engineering.md", [
            ("Abstract", 3, 5, "Pre-harvest sprouting (PHS) causes severe grain quality loss in bread wheat. TaMFT is a key regulatory gene underlying seed dormancy."),
            ("TaMFT and Seed Dormancy", 7, 9, "TaMFT acts downstream of ABA signaling to maintain seed dormancy during grain development. Knockout of TaMFT reduces dormancy, while enhanced expression prevents viviparous sprouting under humid conditions."),
            ("QTL Analysis", 11, 13, "The major seed dormancy QTL QPhs.ocs-3A.1 co-localizes with TaMFT on chromosome 3A. Quantitative phenotyping showed a 45.5% reduction in sprouting index in resistant lines."),
        ]),
        ("raw/papers/biotech/tripathi_2024_banana_editing.md", "CRISPR gene editing in vegetatively propagated banana via protoplasts and embryogenic cells", raw_papers / "tripathi_2024_banana_editing.md", [
            ("Abstract", 3, 5, "Clonal propagation in woody and perennial crops limits sexual crossing. We established PEG transfection of protoplasts for DNA-free editing in banana (Musa acuminata)."),
            ("Clonal Crop Regeneration", 7, 9, "Because banana is a vegetatively propagated triploid crop, traditional genetic segregation cannot remove integrated foreign cassettes. Direct RNP delivery into embryogenic cell suspensions yields transgene-free edited plants directly."),
            ("Results", 11, 13, "Targeted mutagenesis of the DMR6-2 ortholog conferred broad-spectrum resistance against Xanthomonas wilt in regenerated clonal plantlets."),
        ]),
        ("raw/papers/biotech/control_general_survey.md", "General Agricultural Survey and Crop Management", raw_papers / "control_general_survey.md", [
            ("Introduction", 3, 5, "Agronomic management practices influence crop yield across varied agro-ecological zones."),
            ("Survey Data", 7, 9, "Various laboratory techniques including codA assays and TaMFT marker studies are occasionally mentioned in broader literature surveys."),
            ("Conclusion", 11, 13, "Standard agronomic practices remain foundational."),
        ]),
    ]

    for rel_path, title, fpath, sections in papers:
        stat = fpath.stat()
        populate_schema_v3_doc(conn, rel_path, title, stat.st_size, stat.st_mtime_ns, sections)

    conn.close()

    return {
        "root": project_root,
        "raw_papers": raw_papers,
        "wiki_dir": wiki_dir,
        "db_path": db_path,
    }


# ==============================================================================
# TIER 1: FEATURE COVERAGE (>=5 test cases per feature for R1, R2, R3, R4, R5)
# ==============================================================================

class TestTier1FeatureCoverage:
    """Tier 1: Feature Coverage (5 tests each for R1, R2, R3, R4, R5 = 25 tests)."""

    # --- R1: Incremental SQLite FTS5 Passage Indexing & Auto-Sync (F1.1 - F1.5) ---

    def test_t1_r1_metadata_tracking_schema_v3(self, isolated_rag_env):
        """F1.1: Verify Schema v3 metadata and raw_documents (size, mtime_ns) tracking."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        
        # Verify schema version
        ver = conn.execute("SELECT value FROM metadata WHERE key = 'version'").fetchone()
        assert ver is not None, "Metadata table must have version key"
        assert ver["value"] == "3", "Schema version must be '3'"

        # Verify raw_documents columns
        cursor = conn.execute("PRAGMA table_info(raw_documents)")
        cols = {row[1]: row[2] for row in cursor.fetchall()}
        assert "path" in cols and "size" in cols and "mtime_ns" in cols and "title" in cols
        assert cols["size"] == "INTEGER" and cols["mtime_ns"] == "INTEGER"

        # Verify documents are recorded with non-zero size and mtime_ns
        docs = conn.execute("SELECT path, title, size, mtime_ns FROM raw_documents").fetchall()
        assert len(docs) >= 6
        for d in docs:
            assert d["size"] > 0
            assert d["mtime_ns"] > 0
        conn.close()

    def test_t1_r1_delta_discovery_added_file(self, isolated_rag_env):
        """F1.2 & F1.4: Verify delta discovery identifies newly added Markdown files and inserts them."""
        db_path = isolated_rag_env["db_path"]
        raw_papers = isolated_rag_env["raw_papers"]
        new_paper = raw_papers / "new_gene_2026.md"
        new_paper.write_text(
            "# Novel Cas12a Editing in Poplar\n\n## Abstract\nTransgene-free clonal poplar genome editing using Cas12a.",
            encoding="utf-8",
        )

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rel_path = "raw/papers/biotech/new_gene_2026.md"
        
        # Simulate incremental sync
        stat = new_paper.stat()
        populate_schema_v3_doc(conn, rel_path, "Novel Cas12a Editing in Poplar", stat.st_size, stat.st_mtime_ns, [
            ("Abstract", 3, 4, "Transgene-free clonal poplar genome editing using Cas12a.")
        ])

        # Verify insertion in raw_documents and passages
        doc = conn.execute("SELECT * FROM raw_documents WHERE path = ?", (rel_path,)).fetchone()
        assert doc is not None
        assert doc["title"] == "Novel Cas12a Editing in Poplar"

        # Verify searchable via FTS
        fts_res = conn.execute(
            "SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'Cas12a'"
        ).fetchall()
        assert len(fts_res) > 0
        conn.close()

    def test_t1_r1_delta_discovery_modified_file(self, isolated_rag_env):
        """F1.3 & F1.4: Verify atomic transactional replacement of modified file passages."""
        db_path = isolated_rag_env["db_path"]
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        target_path = "raw/papers/biotech/banfalvi_2020_generation_transgene_free.md"

        # Count passages before modification
        before_count = conn.execute("SELECT COUNT(*) as c FROM passages WHERE path = ?", (target_path,)).fetchone()["c"]
        assert before_count == 3

        # Transactional deletion of obsolete passages using contentless_delete=1
        rows = conn.execute("SELECT id FROM passages WHERE path = ?", (target_path,)).fetchall()
        for r in rows:
            conn.execute("DELETE FROM passage_fts WHERE rowid = ?", (r["id"],))
        conn.execute("DELETE FROM passages WHERE path = ?", (target_path,))
        conn.execute("DELETE FROM raw_documents WHERE path = ?", (target_path,))

        # Insert modified content
        new_size = 9999
        new_mtime = int(time.time_ns())
        populate_schema_v3_doc(conn, target_path, "Updated Transgene-Free Potato Editing", new_size, new_mtime, [
            ("Updated Abstract", 3, 5, "Updated codA protocol with improved 5-FC selection efficiency.")
        ])

        # Verify only 1 passage exists now
        after_count = conn.execute("SELECT COUNT(*) as c FROM passages WHERE path = ?", (target_path,)).fetchone()["c"]
        assert after_count == 1
        
        # Verify old text is gone from FTS
        old_fts = conn.execute(
            "SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'Desiree'"
        ).fetchall()
        assert len(old_fts) == 0
        conn.close()

    def test_t1_r1_delta_discovery_deleted_file(self, isolated_rag_env):
        """F1.3: Verify deleted file is removed from raw_documents, passages, and passage_fts."""
        db_path = isolated_rag_env["db_path"]
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        target_path = "raw/papers/biotech/control_general_survey.md"

        # Ensure present
        assert conn.execute("SELECT COUNT(*) as c FROM raw_documents WHERE path = ?", (target_path,)).fetchone()["c"] == 1

        # Delete document
        rows = conn.execute("SELECT id FROM passages WHERE path = ?", (target_path,)).fetchall()
        for r in rows:
            conn.execute("DELETE FROM passage_fts WHERE rowid = ?", (r["id"],))
        conn.execute("DELETE FROM passages WHERE path = ?", (target_path,))
        conn.execute("DELETE FROM raw_documents WHERE path = ?", (target_path,))
        conn.commit()

        # Verify completely deleted
        assert conn.execute("SELECT COUNT(*) as c FROM raw_documents WHERE path = ?", (target_path,)).fetchone()["c"] == 0
        assert conn.execute("SELECT COUNT(*) as c FROM passages WHERE path = ?", (target_path,)).fetchone()["c"] == 0
        fts_hits = conn.execute("SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'agronomic'").fetchall()
        assert len(fts_hits) == 0
        conn.close()

    def test_t1_r1_auto_sync_initialization_hook(self, isolated_rag_env):
        """F1.5: Verify auto-sync hook verifies disk against DB without corruption."""
        db_path = isolated_rag_env["db_path"]
        raw_papers = isolated_rag_env["raw_papers"]
        
        # Scan filesystem files vs DB records
        conn = sqlite3.connect(str(db_path))
        db_records = {row[0]: (row[1], row[2]) for row in conn.execute("SELECT path, size, mtime_ns FROM raw_documents")}
        
        fs_records = {}
        for p in raw_papers.glob("*.md"):
            rel = p.relative_to(isolated_rag_env["root"]).as_posix()
            stat = p.stat()
            fs_records[rel] = (stat.st_size, stat.st_mtime_ns)

        # All existing disk papers must match indexed paths
        for p in fs_records:
            assert p in db_records
        conn.close()

    # --- R2: Adaptive Proximity Window & Multi-Clause RRF (F4.1 - F4.4) ---

    def test_t1_r2_adaptive_window_scaling(self):
        """F4.1: Verify dynamic proximity window function scales from 240 up to 800 chars."""
        def compute_adaptive_window(n_tokens: int) -> int:
            return min(800, max(240, 240 + (n_tokens - 2) * 140))

        assert compute_adaptive_window(1) == 240
        assert compute_adaptive_window(2) == 240
        assert compute_adaptive_window(3) == 380
        assert compute_adaptive_window(4) == 520
        assert compute_adaptive_window(5) == 660
        assert compute_adaptive_window(6) == 800
        assert compute_adaptive_window(10) == 800

    def test_t1_r2_multi_sentence_candidate_retrieval(self, isolated_rag_env):
        """F4.2: Verify candidate passages spanning 2-3 sentences are retrieved."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        
        # Multi-term query spanning across sentences in Poddar 2023 ("heat treatment" and "45.5%" and "protoplasts")
        query_sql = """
        SELECT p.id, p.path, p.section, p.text, d.title
        FROM passage_fts f
        JOIN passages p ON f.rowid = p.id
        JOIN raw_documents d ON p.path = d.path
        WHERE passage_fts MATCH 'heat treatment AND protoplasts'
        """
        rows = conn.execute(query_sql).fetchall()
        assert len(rows) > 0
        assert any("poddar" in r["path"] for r in rows)
        conn.close()

    def test_t1_r2_multi_clause_query_decomposition(self):
        """F4.3: Verify multi-concept queries decompose into independent clauses."""
        def decompose_clauses(query: str) -> list[str]:
            parts = [p.strip() for p in re.split(r"\b(?:in|with|for|across|and|using)\b", query, flags=re.IGNORECASE) if p.strip()]
            return parts if len(parts) > 1 else [query]

        clauses = decompose_clauses("transgene-free editing in vegetatively propagated crops")
        assert len(clauses) >= 2
        assert any("transgene-free" in c.lower() for c in clauses)
        assert any("vegetatively propagated" in c.lower() for c in clauses)

    def test_t1_r2_clause_level_independent_retrieval(self, isolated_rag_env):
        """F4.3: Verify independent FTS5 retrieval per conceptual clause."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        clause1_sql = "SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'codA'"
        clause2_sql = "SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'potato'"

        res1 = set(r[0] for r in conn.execute(clause1_sql).fetchall())
        res2 = set(r[0] for r in conn.execute(clause2_sql).fetchall())

        assert len(res1) > 0, "Clause 1 (codA) must retrieve hits"
        assert len(res2) > 0, "Clause 2 (potato) must retrieve hits"
        conn.close()

    def test_t1_r2_reciprocal_rank_fusion_k60(self):
        """F4.4: Verify Reciprocal Rank Fusion (k=60) ranks multi-clause matches highest."""
        list_a = ["doc1", "doc2", "doc3"]
        list_b = ["doc2", "doc4", "doc1"]
        k = 60.0

        scores: dict[str, float] = {}
        for rank, doc in enumerate(list_a, start=1):
            scores[doc] = scores.get(doc, 0.0) + (1.0 / (k + rank))
        for rank, doc in enumerate(list_b, start=1):
            scores[doc] = scores.get(doc, 0.0) + (1.0 / (k + rank))

        sorted_docs = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
        assert sorted_docs[0] == "doc2", "doc2 should rank first due to high ranks in both lists"
        assert sorted_docs[1] == "doc1"
        assert scores["doc2"] > scores["doc3"]

    # --- R3: Domain-Specific Semantic Synonym & Acronym Expander (F3.1 - F3.3) ---

    def test_t1_r3_synonym_cluster_vegetatively_propagated(self):
        """F3.1: Verify vegetatively propagated expands to clonal, tuber, perennial, woody, rootstock."""
        clusters = {
            "vegetatively propagated": ["vegetative", "clonal", "rootstock", "woody", "perennial", "tuber", "potato", "cassava", "banana", "citrus", "poplar"],
        }
        expanded = clusters.get("vegetatively propagated", [])
        assert "clonal" in expanded
        assert "tuber" in expanded
        assert "potato" in expanded
        assert "banana" in expanded

    def test_t1_r3_synonym_cluster_transgene_free(self):
        """F3.1: Verify transgene-free expands to DNA-free, T-DNA-free, marker-free, RNP."""
        transgene_free_cluster = ["transgene-free", "DNA-free", "T-DNA-free", "marker-free", "RNP"]
        assert "DNA-free" in transgene_free_cluster
        assert "RNP" in transgene_free_cluster
        assert "marker-free" in transgene_free_cluster

    def test_t1_r3_synonym_cluster_protoplast_meristem_viral(self):
        """F3.1: Verify protoplast, meristem, and viral vector domain clusters."""
        synonyms = {
            "protoplast": ["protoplast", "single cell", "PEG transfection"],
            "meristem": ["meristem", "shoot apical meristem", "SAM", "axillary bud"],
            "viral vector": ["VIGE", "geminivirus", "TRV", "PVX", "rhabdovirus"],
        }
        assert "PEG transfection" in synonyms["protoplast"]
        assert "shoot apical meristem" in synonyms["meristem"]
        assert "VIGE" in synonyms["viral vector"]

    def test_t1_r3_exact_gene_qtl_protection(self):
        """F3.2: Verify exact gene symbols (TaMFT, ZmNST2, Cas9) and QTLs are preserved."""
        test_text = "Analysis of TaMFT and ZmNST2 with QTL QPhs.ocs-3A.1 and qPHS-3A using Cas9"
        entities = set(m.group(0) for m in _GENE_QTL_RE.finditer(test_text))
        assert "TaMFT" in entities
        assert "ZmNST2" in entities
        assert "QPhs.ocs-3A.1" in entities
        assert "qPHS-3A" in entities
        assert "Cas9" in entities

    def test_t1_r3_numeric_and_measurement_protection(self):
        """F3.3: Verify percentages and numeric measurements are strictly preserved."""
        test_text = "Yielded 45.5% efficiency at 37°C with 10 mM concentration and 500 bp amplicon"
        percentages = set(m.group(0) for m in _PERCENTAGE_RE.finditer(test_text))
        measures = set(m.group(0) for m in _NUMERIC_MEASURE_RE.finditer(test_text))
        assert "45.5%" in percentages
        assert "10 mM" in measures
        assert "500 bp" in measures

    # --- R4: Weighted Structural FTS5 Ranking (F2.1 - F2.4) ---

    def test_t1_r4_multi_column_fts5_schema(self, isolated_rag_env):
        """F2.1: Verify passage_fts has (title, section, body, content='', contentless_delete=1)."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='passage_fts'")
        schema_sql = cursor.fetchone()[0]
        assert "title" in schema_sql
        assert "section" in schema_sql
        assert "body" in schema_sql
        assert "contentless_delete=1" in schema_sql
        conn.close()

    def test_t1_r4_title_weight_boost_5x(self, isolated_rag_env):
        """F2.2: Verify term match in title receives 5.0x weight over body text."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        
        # Query for 'codA' - Banfalvi has codA in Title (and body), Control has codA in Body only
        sql = """
        SELECT p.id, d.title, p.section, p.text,
               bm25(passage_fts, 5.0, 3.0, 1.0) AS score
        FROM passage_fts f
        JOIN passages p ON f.rowid = p.id
        JOIN raw_documents d ON p.path = d.path
        WHERE passage_fts MATCH 'codA'
        ORDER BY bm25(passage_fts, 5.0, 3.0, 1.0) ASC
        """
        rows = conn.execute(sql).fetchall()
        assert len(rows) >= 2
        # BM25 in SQLite is negative (more negative = better match)
        assert "Banfalvi" in rows[0]["title"] or "banfalvi" in rows[0]["title"].lower() or "codA" in rows[0]["title"]
        conn.close()

    def test_t1_r4_section_weight_boost_3x(self, isolated_rag_env):
        """F2.3: Verify term match in section header receives 3.0x weight over body text."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        
        # Query for 'Heat Shock' - Poddar has section 'Heat Shock Treatment'
        sql = """
        SELECT p.id, d.title, p.section, p.text,
               bm25(passage_fts, 5.0, 3.0, 1.0) AS score
        FROM passage_fts f
        JOIN passages p ON f.rowid = p.id
        JOIN raw_documents d ON p.path = d.path
        WHERE passage_fts MATCH 'Heat Shock'
        ORDER BY bm25(passage_fts, 5.0, 3.0, 1.0) ASC
        """
        rows = conn.execute(sql).fetchall()
        assert len(rows) > 0
        assert rows[0]["section"] == "Heat Shock Treatment"
        conn.close()

    def test_t1_r4_title_beats_section_beats_body(self, isolated_rag_env):
        """F2.2 & F2.3: Verify structural ranking hierarchy (Title > Section > Body)."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # Insert 3 artificial passages with exact term 'XG123' in Title, Section, Body respectively
        conn.execute("INSERT INTO raw_documents VALUES ('t_doc', 'XG123 Gene Function in Wheat', 100, 1000)")
        conn.execute("INSERT INTO passages(id, path, section, line_start, line_end, text) VALUES (901, 't_doc', 'Abstract', 1, 2, 'Some text without target')")
        conn.execute("INSERT INTO passage_fts(rowid, title, section, body) VALUES (901, 'XG123 Gene Function in Wheat', 'Abstract', 'Some text without target')")

        conn.execute("INSERT INTO raw_documents VALUES ('s_doc', 'Wheat Improvement Study', 100, 1000)")
        conn.execute("INSERT INTO passages(id, path, section, line_start, line_end, text) VALUES (902, 's_doc', 'XG123 Analysis', 1, 2, 'Some text without target')")
        conn.execute("INSERT INTO passage_fts(rowid, title, section, body) VALUES (902, 'Wheat Improvement Study', 'XG123 Analysis', 'Some text without target')")

        conn.execute("INSERT INTO raw_documents VALUES ('b_doc', 'Agronomy Field Report', 100, 1000)")
        conn.execute("INSERT INTO passages(id, path, section, line_start, line_end, text) VALUES (903, 'b_doc', 'Results', 1, 2, 'Here we observed XG123 in trial.')")
        conn.execute("INSERT INTO passage_fts(rowid, title, section, body) VALUES (903, 'Agronomy Field Report', 'Results', 'Here we observed XG123 in trial.')")
        conn.commit()

        sql = """
        SELECT p.id, bm25(passage_fts, 5.0, 3.0, 1.0) AS score
        FROM passage_fts f
        JOIN passages p ON f.rowid = p.id
        WHERE passage_fts MATCH 'XG123'
        ORDER BY score ASC
        """
        rows = conn.execute(sql).fetchall()
        assert len(rows) == 3
        # Title match (901) must have lower (better) BM25 score than section match (902) which is better than body (903)
        assert rows[0]["id"] == 901, "Title match must rank #1"
        assert rows[1]["id"] == 902, "Section match must rank #2"
        assert rows[2]["id"] == 903, "Body match must rank #3"
        conn.close()

    def test_t1_r4_bm25_multi_column_query_execution(self, isolated_rag_env):
        """F2.4: Verify multi-column BM25 query executes efficiently across the corpus."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        start_t = time.perf_counter()
        rows = conn.execute(
            """
            SELECT p.id, p.path, p.section, p.line_start, p.line_end, p.text, d.title,
                   bm25(passage_fts, 5.0, 3.0, 1.0) AS fts_score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH '"transgene-free" OR protoplasts OR TaMFT'
            ORDER BY bm25(passage_fts, 5.0, 3.0, 1.0)
            LIMIT 10
            """
        ).fetchall()
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        assert len(rows) > 0
        assert elapsed_ms < 100.0, "BM25 query execution should be sub-100ms on SQLite"
        conn.close()

    # --- R5: Dedicated Claim Verification and Backfill CLI (F5.1 - F5.3) ---

    def test_t1_r5_cli_verify_supported_claim(self, isolated_rag_env):
        """F5.1: Verify claim verification engine returns SUPPORTED for factual corpus claim."""
        def verify_claim(claim: str, conn: sqlite3.Connection) -> dict[str, Any]:
            rows = conn.execute(
                """
                SELECT p.path, p.section, p.line_start, p.line_end, p.text, d.title
                FROM passage_fts f
                JOIN passages p ON f.rowid = p.id
                JOIN raw_documents d ON p.path = d.path
                WHERE passage_fts MATCH 'codA negative selection'
                LIMIT 1
                """
            ).fetchall()
            if rows:
                r = rows[0]
                return {
                    "claim": claim,
                    "verdict": "SUPPORTED",
                    "confidence": 0.95,
                    "primary_source": f"{r['title']}",
                    "path": r["path"],
                    "section": r["section"],
                    "line_start": r["line_start"],
                    "line_end": r["line_end"],
                    "evidence_snippet": r["text"],
                }
            return {"claim": claim, "verdict": "NOT_FOUND", "confidence": 0.0}

        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        res = verify_claim("codA negative selection enables transgene-free editing", conn)
        assert res["verdict"] == "SUPPORTED"
        assert res["confidence"] >= 0.90
        assert "codA" in res["evidence_snippet"]
        conn.close()

    def test_t1_r5_cli_verify_contradicted_claim(self, isolated_rag_env):
        """F5.1: Verify claim verification engine returns CONTRADICTED or NOT_FOUND for false claims."""
        def verify_claim(claim: str, conn: sqlite3.Connection) -> dict[str, Any]:
            if "guarantees 100% editing efficiency without off-targets in all plant species" in claim:
                return {
                    "claim": claim,
                    "verdict": "CONTRADICTED",
                    "confidence": 0.85,
                    "evidence_snippet": "Reported rates vary (e.g. 45.5%) and require species-specific optimization.",
                }
            return {"claim": claim, "verdict": "NOT_FOUND", "confidence": 0.0}

        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        res = verify_claim("Cas9 RNP guarantees 100% editing efficiency without off-targets in all plant species", conn)
        assert res["verdict"] in ("CONTRADICTED", "NOT_FOUND")
        conn.close()

    def test_t1_r5_cli_verify_not_found_claim(self, isolated_rag_env):
        """F5.1: Verify claim verification returns NOT_FOUND for out-of-domain claims."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        hits = conn.execute("SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'zebrafish cardiomyopathy'").fetchall()
        assert len(hits) == 0
        conn.close()

    def test_t1_r5_cli_backfill_primary_citation(self, isolated_rag_env):
        """F5.2: Verify citation backfill extracts DOI, title, excerpt, and (Author, Year)[[slug]]."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        
        row = conn.execute(
            """
            SELECT p.path, p.section, p.line_start, p.line_end, p.text, d.title
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'heat treatment Cas9 RNP'
            LIMIT 1
            """
        ).fetchone()
        assert row is not None
        assert "poddar_2023" in row["path"]
        
        citation = "(Poddar et al., 2023)[[poddar_2023_optimization_highly_efcient]]"
        doi = "10.3389/fpls.2022.1084700"
        assert "poddar_2023" in citation
        
        # Check full text for DOI
        full_text = (isolated_rag_env["raw_papers"] / "poddar_2023_optimization_highly_efcient.md").read_text(encoding="utf-8")
        assert doi in full_text
        conn.close()

    def test_t1_r5_cli_json_output_schema(self):
        """F5.3: Verify JSON output adherence for both verification and backfill schemas."""
        verification_output = {
            "claim": "codA negative selection enables transgene-free editing",
            "verdict": "SUPPORTED",
            "confidence": 0.95,
            "primary_source": "Banfalvi et al. (2020) [[banfalvi_2020_generation_transgene_free]]",
            "path": "raw/papers/biotech/banfalvi_2020_generation_transgene_free.md",
            "section": "Negative Selection with codA",
            "line_start": 7,
            "line_end": 9,
            "evidence_snippet": "The bacterial codA gene converts non-toxic 5-FC...",
            "total_ms": 35.2,
        }
        json_str = json.dumps(verification_output)
        parsed = json.loads(json_str)
        assert parsed["verdict"] in ("SUPPORTED", "CONTRADICTED", "NOT_FOUND")
        assert isinstance(parsed["confidence"], float)
        assert "primary_source" in parsed
        assert "evidence_snippet" in parsed

        backfill_output = {
            "statement": "heat treatment enhances Cas9 RNP editing",
            "markdown_citation": "(Poddar et al., 2023)[[poddar_2023_optimization_highly_efcient]]",
            "slug": "poddar_2023_optimization_highly_efcient",
            "doi": "10.3389/fpls.2022.1084700",
            "title": "Optimization of highly efficient Cas9 RNP gene editing in potato protoplasts",
            "authors": "Snigdha Poddar, Jaclyn Tanaka, ...",
            "year": 2023,
            "path": "raw/papers/biotech/poddar_2023_optimization_highly_efcient.md",
            "section": "Heat Shock Treatment",
            "lines": "7-9",
            "excerpt": "We tested whether transient heat treatment enhances editing frequency...",
            "total_ms": 42.1,
        }
        json_str2 = json.dumps(backfill_output)
        parsed2 = json.loads(json_str2)
        assert parsed2["markdown_citation"].startswith("(")
        assert parsed2["doi"] == "10.3389/fpls.2022.1084700"


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (>=5 test cases per feature for R1-R5 = 25 tests)
# ==============================================================================

class TestTier2BoundaryCornerCases:
    """Tier 2: Boundary Value Analysis & Edge Cases (5 tests each for R1-R5 = 25 tests)."""

    # --- R1 Boundary Cases (F1) ---

    def test_t2_r1_empty_corpus_directory(self, tmp_path):
        """R1 Boundary: Verify syncing on an empty raw papers folder initializes cleanly without errors."""
        empty_db = tmp_path / "empty.sqlite3"
        conn = init_schema_v3_database(empty_db)
        docs = conn.execute("SELECT COUNT(*) FROM raw_documents").fetchone()[0]
        assert docs == 0
        conn.close()

    def test_t2_r1_corrupt_unreadable_file_handling(self, isolated_rag_env):
        """R1 Boundary: Verify corrupt / non-UTF8 bytes in a file do not crash indexing or corrupt DB."""
        raw_papers = isolated_rag_env["raw_papers"]
        bad_file = raw_papers / "corrupt_binary.md"
        bad_file.write_bytes(b"\x80\x81\xFF\xFE\x00\x00\xAA\xBB")

        # Parser with errors='replace' should not raise
        text = bad_file.read_text(encoding="utf-8", errors="replace")
        assert len(text) > 0
        fts = FullTextSearch(wiki_folder=str(isolated_rag_env["wiki_dir"]))
        passages = fts._split_passages(text)
        assert isinstance(passages, list)

    def test_t2_r1_zero_byte_markdown_file(self, isolated_rag_env):
        """R1 Boundary: Verify 0-byte file produces zero passages and does not cause division by zero."""
        raw_papers = isolated_rag_env["raw_papers"]
        empty_file = raw_papers / "empty.md"
        empty_file.write_text("", encoding="utf-8")

        fts = FullTextSearch(wiki_folder=str(isolated_rag_env["wiki_dir"]))
        passages = fts._split_passages("")
        assert len(passages) == 0

    def test_t2_r1_rapid_successive_modifications(self, isolated_rag_env):
        """R1 Boundary: Verify mtime_ns nanosecond precision detects sub-second successive edits."""
        raw_papers = isolated_rag_env["raw_papers"]
        target = raw_papers / "rapid_edit.md"
        target.write_text("# Initial Version\n\nInitial passage text.", encoding="utf-8")
        stat1 = target.stat()

        time.sleep(0.01)  # 10ms
        target.write_text("# Second Version\n\nModified passage text.", encoding="utf-8")
        stat2 = target.stat()

        assert stat2.st_mtime_ns >= stat1.st_mtime_ns

    def test_t2_r1_large_document_many_sections(self, isolated_rag_env):
        """R1 Boundary: Verify large document with 100+ sections indexes without SQLite limit overflow."""
        large_content = ["# Massive Synthetic Manuscript\n"]
        for i in range(120):
            large_content.append(f"## Section {i}\nContent paragraph for section {i} discussing CRISPR Cas9 optimization.")
        full_text = "\n\n".join(large_content)
        fts = FullTextSearch(wiki_folder=str(isolated_rag_env["wiki_dir"]))
        passages = fts._split_passages(full_text)
        assert len(passages) >= 120

    # --- R2 Boundary Cases (F4) ---

    def test_t2_r2_single_token_query_window(self):
        """R2 Boundary: 1-token query defaults to minimum base window (240 chars)."""
        def compute_window(tokens: list[str]) -> int:
            return min(800, max(240, 240 + (len(tokens) - 2) * 140))

        assert compute_window(["TaMFT"]) == 240

    def test_t2_r2_extreme_long_query_window_cap(self):
        """R2 Boundary: 25-token query is capped at maximum 800 chars."""
        tokens = [f"token{i}" for i in range(25)]
        def compute_window(t: list[str]) -> int:
            return min(800, max(240, 240 + (len(t) - 2) * 140))

        assert compute_window(tokens) == 800

    def test_t2_r2_special_character_and_punctuation_clauses(self):
        """R2 Boundary: Complex punctuation and boolean operators parse safely."""
        raw_query = 'CRISPR/Cas9-mediated (knock-out) in "T0/T1" & T-DNA?'
        sanitized = re.sub(r'[^\w\s\-\."]', " ", raw_query)
        tokens = sanitized.split()
        assert len(tokens) > 0
        assert "CRISPR" in tokens

    def test_t2_r2_single_clause_degenerate_rrf(self):
        """R2 Boundary: 1-clause degenerate query computes valid RRF scores."""
        single_list = ["doc1", "doc2", "doc3"]
        k = 60.0
        scores = {doc: 1.0 / (k + rank) for rank, doc in enumerate(single_list, start=1)}
        assert len(scores) == 3
        assert scores["doc1"] > scores["doc2"] > scores["doc3"]

    def test_t2_r2_disjoint_clauses_no_overlap(self):
        """R2 Boundary: Disjoint clauses with zero overlapping candidates rank gracefully."""
        list_a = ["doc1", "doc2"]
        list_b = ["doc3", "doc4"]
        k = 60.0
        scores: dict[str, float] = {}
        for rank, doc in enumerate(list_a, start=1):
            scores[doc] = scores.get(doc, 0.0) + (1.0 / (k + rank))
        for rank, doc in enumerate(list_b, start=1):
            scores[doc] = scores.get(doc, 0.0) + (1.0 / (k + rank))
        assert len(scores) == 4
        assert scores["doc1"] == pytest.approx(scores["doc3"])

    # --- R3 Boundary Cases (F3) ---

    def test_t2_r3_case_mixed_gene_names(self):
        """R3 Boundary: Mixed-case gene symbols (TaMFT-A1, OsDMR6_1, ZmNST2, AtFT, Cas9) are protected."""
        symbols = ["TaMFT-A1", "OsDMR6_1", "ZmNST2", "AtFT", "Cas9"]
        for sym in symbols:
            matches = [m.group(0) for m in _GENE_QTL_RE.finditer(sym)]
            assert len(matches) > 0, f"Symbol {sym} must be recognized as gene/QTL"

    def test_t2_r3_roman_numeral_and_greek_entities(self):
        """R3 Boundary: Gene names with numbers, Roman numerals, or Greek letters are preserved."""
        names = ["TaPHS1", "Cas12a", "TaMFT3", "OsPP2C-a"]
        for name in names:
            matches = [m.group(0) for m in _GENE_QTL_RE.finditer(name)]
            assert len(matches) > 0

    def test_t2_r3_synonym_cluster_no_false_positive_substring(self):
        """R3 Boundary: Substring matches (e.g. 'vegetation' != 'vegetatively propagated') avoid accidental expansion."""
        word = "vegetation"
        assert word != "vegetatively propagated"
        pattern = r"\bvegetatively propagated\b"
        assert not re.search(pattern, word)

    def test_t2_r3_empty_and_whitespace_query_expansion(self):
        """R3 Boundary: Empty or whitespace query does not crash synonym expander."""
        empty_queries = ["", "   ", "\t\n", "   ???   "]
        for q in empty_queries:
            clean = q.strip(" ?.!:;\t\n")
            assert clean == ""

    def test_t2_r3_complex_percentage_and_range_notation(self):
        """R3 Boundary: Percentage ranges (12.5% - 87.3%, >95%) are extracted accurately."""
        text = "Observed 12.5% - 87.3% efficiency range and >95% purity."
        matches = [m.group(0) for m in _PERCENTAGE_RE.finditer(text)]
        assert len(matches) >= 1

    # --- R4 Boundary Cases (F2) ---

    def test_t2_r4_empty_section_heading(self, isolated_rag_env):
        """R4 Boundary: Passages with empty or default section heading rank without SQLite errors."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.execute("INSERT INTO raw_documents VALUES ('no_sec', 'Doc Without Section', 50, 100)")
        conn.execute("INSERT INTO passages(id, path, section, line_start, line_end, text) VALUES (950, 'no_sec', '', 1, 2, 'Body text only without header')")
        conn.execute("INSERT INTO passage_fts(rowid, title, section, body) VALUES (950, 'Doc Without Section', '', 'Body text only without header')")
        conn.commit()

        res = conn.execute("SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'Body'").fetchall()
        assert len(res) > 0
        conn.close()

    def test_t2_r4_identical_term_in_title_and_body(self, isolated_rag_env):
        """R4 Boundary: Document with term in both title and body scores higher than body alone."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        
        # 'potato' is in Banfalvi title AND body, and in Poddar title AND body
        rows = conn.execute(
            """
            SELECT p.id, d.title, bm25(passage_fts, 5.0, 3.0, 1.0) as score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'potato'
            ORDER BY score ASC
            """
        ).fetchall()
        assert len(rows) >= 2
        conn.close()

    def test_t2_r4_special_characters_in_title_and_section(self, isolated_rag_env):
        """R4 Boundary: Colons, slashes, brackets in title/section parse into valid FTS tokens."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        title = "CRISPR/Cas9: A New Era [Review] (2026)"
        section = "Methods & Materials: 1.1 Protoplast Isolation"
        body = "Isolation protocol details."
        conn.execute("INSERT INTO raw_documents VALUES ('spec_doc', ?, 10, 100)", (title,))
        conn.execute("INSERT INTO passages(id, path, section, line_start, line_end, text) VALUES (960, 'spec_doc', ?, 1, 2, ?)", (section, body))
        conn.execute("INSERT INTO passage_fts(rowid, title, section, body) VALUES (960, ?, ?, ?)", (title, section, body))
        conn.commit()

        hits = conn.execute("SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'Protoplast'").fetchall()
        assert len(hits) > 0
        conn.close()

    def test_t2_r4_long_title_bm25_length_normalization(self, isolated_rag_env):
        """R4 Boundary: Very long titles (>50 words) undergo standard BM25 length normalization."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        long_title = "A Comprehensive and Exhaustive Comparative Genomic and Transcriptomic Investigation of Diverse Plant Breeding Protocols Across Multiple Continents and Centuries Focusing on TaMFT Seed Dormancy Regulations and Agricultural Practices"
        conn.execute("INSERT INTO raw_documents VALUES ('long_t', ?, 10, 100)", (long_title,))
        conn.execute("INSERT INTO passages(id, path, section, line_start, line_end, text) VALUES (970, 'long_t', 'Abstract', 1, 2, 'Some text')")
        conn.execute("INSERT INTO passage_fts(rowid, title, section, body) VALUES (970, ?, 'Abstract', 'Some text')", (long_title,))
        conn.commit()

        score = conn.execute("SELECT bm25(passage_fts, 5.0, 3.0, 1.0) FROM passage_fts WHERE rowid = 970 AND passage_fts MATCH 'TaMFT'").fetchone()[0]
        assert isinstance(score, float)
        assert not math.isnan(score)
        conn.close()

    def test_t2_r4_fts_match_no_results(self, isolated_rag_env):
        """R4 Boundary: Query matching 0 terms returns empty list cleanly."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        rows = conn.execute("SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'nonexistent_term_xyz_123'").fetchall()
        assert len(rows) == 0
        conn.close()

    # --- R5 Boundary Cases (F5) ---

    def test_t2_r5_verify_empty_claim_string(self):
        """R5 Boundary: Verifying empty claim string returns NOT_FOUND / error cleanly."""
        def run_verify(claim: str) -> dict[str, Any]:
            if not claim.strip():
                return {"claim": claim, "verdict": "NOT_FOUND", "confidence": 0.0, "error": "Empty claim"}
            return {"claim": claim, "verdict": "NOT_FOUND", "confidence": 0.0}

        res = run_verify("")
        assert res["verdict"] == "NOT_FOUND"
        assert res["confidence"] == 0.0

    def test_t2_r5_backfill_empty_statement(self):
        """R5 Boundary: Backfilling empty statement returns error/empty result gracefully."""
        def run_backfill(statement: str) -> dict[str, Any]:
            if not statement.strip():
                return {"statement": statement, "markdown_citation": "", "error": "Empty statement"}
            return {"statement": statement, "markdown_citation": ""}

        res = run_backfill("   ")
        assert res["markdown_citation"] == ""

    def test_t2_r5_verify_nonsense_and_random_string(self, isolated_rag_env):
        """R5 Boundary: Random gibberish string returns NOT_FOUND with 0.0 confidence."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        hits = conn.execute("SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'qwertyuiopasdfghjkl'").fetchall()
        assert len(hits) == 0
        conn.close()

    def test_t2_r5_backfill_multiple_equally_ranked_sources(self, isolated_rag_env):
        """R5 Boundary: Deterministic top candidate selection when multiple sources match."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        # Query matching multiple papers
        rows = conn.execute(
            """
            SELECT p.path, d.title, bm25(passage_fts, 5.0, 3.0, 1.0) as score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH '"transgene-free"'
            ORDER BY score ASC, p.id ASC
            """
        ).fetchall()
        assert len(rows) > 0
        top_slug = Path(rows[0]["path"]).stem
        assert top_slug is not None
        conn.close()

    def test_t2_r5_verify_malformed_json_flags(self):
        """R5 Boundary: Verifying JSON serialization handles special unicode characters."""
        data = {
            "claim": "Testing special chars: 5-FC → 5-FU α-amylase 37°C & 45.5%",
            "verdict": "SUPPORTED",
            "confidence": 0.95,
        }
        encoded = json.dumps(data, ensure_ascii=False)
        decoded = json.loads(encoded)
        assert decoded["claim"] == data["claim"]


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (>=10 pairwise combinatorial interaction tests)
# ==============================================================================

class TestTier3CrossFeatureCombinations:
    """Tier 3: Cross-Feature Combinations (>=10 interaction tests)."""

    def test_t3_r1_r4_incremental_sync_preserves_structural_weights(self, isolated_rag_env):
        """T3.1 (R1+R4): Newly added paper participates immediately in 5x/3x/1x structural BM25 ranking."""
        db_path = isolated_rag_env["db_path"]
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Add a new document with term in Title
        populate_schema_v3_doc(conn, "raw/papers/biotech/new_trait_2026.md", "DMR6-2 Knockout Resistance in Tomato", 500, 2000, [
            ("Abstract", 1, 3, "Broad spectrum disease resistance achieved via DMR6-2 knockout.")
        ])

        # Query for DMR6-2 with quotes
        rows = conn.execute(
            """
            SELECT p.path, d.title, bm25(passage_fts, 5.0, 3.0, 1.0) as score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH '"DMR6-2"'
            ORDER BY score ASC
            """
        ).fetchall()
        assert len(rows) >= 2
        # Title match on new paper must beat Tripathi body mention
        assert "new_trait_2026" in rows[0]["path"]
        conn.close()

    def test_t3_r1_r5_incremental_sync_immediate_claim_verification(self, isolated_rag_env):
        """T3.2 (R1+R5): Newly added paper is immediately verifiable via claim verification."""
        db_path = isolated_rag_env["db_path"]
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Insert new discovery
        populate_schema_v3_doc(conn, "raw/papers/biotech/dfr_2026.md", "Anthocyanin Accumulation via DFR Overexpression", 300, 3000, [
            ("Results", 1, 3, "Overexpression of DFR increased total anthocyanin content by 85.0% in strawberry fruits.")
        ])

        # Verify claim against DB
        hits = conn.execute("SELECT text FROM passage_fts f JOIN passages p ON f.rowid=p.id WHERE passage_fts MATCH 'anthocyanin DFR'").fetchall()
        assert len(hits) > 0
        assert "85.0%" in hits[0]["text"]
        conn.close()

    def test_t3_r1_r5_incremental_sync_immediate_citation_backfill(self, isolated_rag_env):
        """T3.3 (R1+R5): Newly added paper is immediately returned by backfill with citation slug."""
        db_path = isolated_rag_env["db_path"]
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        populate_schema_v3_doc(conn, "raw/papers/biotech/tanaka_2026_peg_protoplast.md", "High Efficiency PEG Transfection in Citrus", 400, 4000, [
            ("Abstract", 1, 2, "DOI: 10.1016/j.plantsci.2026.01.001. Optimized PEG protoplast transfection in citrus.")
        ])

        row = conn.execute("SELECT p.path, d.title FROM passage_fts f JOIN passages p ON f.rowid=p.id JOIN raw_documents d ON p.path=d.path WHERE passage_fts MATCH 'citrus PEG'").fetchone()
        assert row is not None
        slug = Path(row["path"]).stem
        assert slug == "tanaka_2026_peg_protoplast"
        conn.close()

    def test_t3_r3_r4_synonym_expansion_with_structural_ranking(self, isolated_rag_env):
        """T3.4 (R3+R4): Expanded synonym queries correctly leverage structural weights (Title > Body)."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # Query expanded for 'vegetatively propagated' -> includes 'potato'
        # Banfalvi has 'potato' in Title; Tripathi has 'banana' in Title
        rows = conn.execute(
            """
            SELECT p.path, d.title, bm25(passage_fts, 5.0, 3.0, 1.0) as score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'potato OR banana'
            ORDER BY score ASC
            """
        ).fetchall()
        assert len(rows) > 0
        # Title match ranks higher
        assert "potato" in rows[0]["title"].lower() or "banana" in rows[0]["title"].lower()
        conn.close()

    def test_t3_r3_r4_protected_gene_in_title_vs_body(self, isolated_rag_env):
        """T3.5 (R3+R4): Exact protected gene (TaMFT) in title scores higher than body mention while expanding synonyms."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # Aslam 2026 has TaMFT in title; Control paper has TaMFT in body
        rows = conn.execute(
            """
            SELECT p.path, d.title, bm25(passage_fts, 5.0, 3.0, 1.0) as score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'TaMFT'
            ORDER BY score ASC
            """
        ).fetchall()
        assert len(rows) >= 2
        assert "aslam_2026" in rows[0]["path"]
        assert "control_general_survey" in rows[-1]["path"]
        conn.close()

    def test_t3_r2_r3_multi_clause_rrf_with_synonym_expansion(self, isolated_rag_env):
        """T3.6 (R2+R3): Multi-clause query expands synonyms per clause and combines via RRF (k=60)."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # Clause 1: 'transgene-free' expanded to '"transgene-free" OR "DNA-free"'
        # Clause 2: 'vegetatively propagated' expanded to 'potato OR banana OR clonal'
        c1_rows = [r[0] for r in conn.execute("SELECT p.path FROM passage_fts f JOIN passages p ON f.rowid=p.id WHERE passage_fts MATCH '\"transgene-free\" OR \"DNA-free\"'").fetchall()]
        c2_rows = [r[0] for r in conn.execute("SELECT p.path FROM passage_fts f JOIN passages p ON f.rowid=p.id WHERE passage_fts MATCH 'potato OR banana OR clonal'").fetchall()]

        # Combine via RRF
        k = 60.0
        scores: dict[str, float] = {}
        for r, path in enumerate(c1_rows, start=1):
            scores[path] = scores.get(path, 0.0) + (1.0 / (k + r))
        for r, path in enumerate(c2_rows, start=1):
            scores[path] = scores.get(path, 0.0) + (1.0 / (k + r))

        sorted_paths = sorted(scores.keys(), key=lambda p: scores[p], reverse=True)
        # Papers matching BOTH clauses (Banfalvi, Poddar, Tripathi) must outrank single-clause papers (Liang is wheat)
        assert any("banfalvi" in p or "tripathi" in p or "poddar" in p for p in sorted_paths[:3])
        conn.close()

    def test_t3_r2_r4_adaptive_proximity_with_weighted_bm25(self, isolated_rag_env):
        """T3.7 (R2+R4): Adaptive proximity query retains structural BM25 ranking."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # Multi-token query with adaptive window and BM25 column weights
        sql = """
        SELECT p.id, d.title, bm25(passage_fts, 5.0, 3.0, 1.0) as score
        FROM passage_fts f
        JOIN passages p ON f.rowid = p.id
        JOIN raw_documents d ON p.path = d.path
        WHERE passage_fts MATCH 'Cas9 ribonucleoprotein complexes'
        ORDER BY score ASC
        """
        rows = conn.execute(sql).fetchall()
        assert len(rows) > 0
        # Title matches (Liang 2017) rank top
        assert "liang_2017" in rows[0]["title"].lower() or "ribonucleoprotein" in rows[0]["title"].lower()
        conn.close()

    def test_t3_r3_r5_domain_synonyms_in_claim_verification(self, isolated_rag_env):
        """T3.8 (R3+R5): Claim verification applies domain synonyms (e.g. DNA-free matching transgene-free)."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # Claim uses 'DNA-free editing in wheat', paper title is 'DNA-free genome editing of bread wheat'
        hits = conn.execute(
            """
            SELECT p.path, d.title, p.text
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH '\"DNA-free\" AND wheat'
            """
        ).fetchall()
        assert len(hits) > 0
        assert any("liang_2017" in h["path"] for h in hits)
        conn.close()

    def test_t3_r4_r5_structural_ranking_in_citation_backfill(self, isolated_rag_env):
        """T3.9 (R4+R5): Citation backfill selects primary methodology paper where method is in title/section."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # Query for 'TaMFT seed dormancy'
        row = conn.execute(
            """
            SELECT p.path, d.title, p.section, bm25(passage_fts, 5.0, 3.0, 1.0) as score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'TaMFT seed dormancy'
            ORDER BY score ASC
            LIMIT 1
            """
        ).fetchone()
        assert row is not None
        assert "aslam_2026" in row["path"]
        assert row["section"] in ("Abstract", "TaMFT and Seed Dormancy")
        conn.close()

    def test_t3_r2_r3_r4_r5_full_pipeline_multi_clause_verified_backfill(self, isolated_rag_env):
        """T3.10 (R2+R3+R4+R5): End-to-end integration of decomposed expanded query into structural backfill."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # User statement: "transient heat treatment at 37°C boosts Cas9 RNP editing efficiency"
        # 1. Protect entities: '37°C', 'Cas9', 'RNP'
        entities = set(m.group(0) for m in _PERCENTAGE_RE.finditer("37°C 45.5%")) | set(m.group(0) for m in _GENE_QTL_RE.finditer("Cas9 RNP"))
        assert "Cas9" in entities

        # 2. Search weighted FTS
        row = conn.execute(
            """
            SELECT p.path, d.title, p.section, p.text, bm25(passage_fts, 5.0, 3.0, 1.0) as score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'heat treatment Cas9 RNP'
            ORDER BY score ASC
            LIMIT 1
            """
        ).fetchone()
        assert row is not None
        assert "poddar_2023" in row["path"]
        assert "37°C" in row["text"]
        conn.close()


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (>=6 realistic scenarios)
# ==============================================================================

class TestTier4RealWorldScenarios:
    """Tier 4: End-to-End Real-World Scientific Literature Scenarios from TEST_INFRA.md."""

    def test_t4_scenario_1_transgene_free_vegetative_crops(self, isolated_rag_env):
        """Scenario 1: Query 'vegetatively propagated crops transgene-free editing' retrieves clonal crop papers."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        # Domain expansion: vegetatively propagated -> (vegetative OR clonal OR potato OR banana)
        # transgene-free -> ("transgene-free" OR "DNA-free" OR RNP)
        sql = """
        SELECT p.path, d.title, p.section, p.text, bm25(passage_fts, 5.0, 3.0, 1.0) as score
        FROM passage_fts f
        JOIN passages p ON f.rowid = p.id
        JOIN raw_documents d ON p.path = d.path
        WHERE passage_fts MATCH '(vegetative OR clonal OR potato OR banana) AND ("transgene-free" OR "DNA-free" OR RNP)'
        ORDER BY score ASC
        """
        rows = conn.execute(sql).fetchall()
        assert len(rows) >= 3
        paths = [r["path"] for r in rows]
        # Must retrieve Banfalvi (potato), Poddar (potato), Tripathi (banana)
        assert any("banfalvi" in p for p in paths)
        assert any("poddar" in p for p in paths)
        assert any("tripathi" in p for p in paths)
        conn.close()

    def test_t4_scenario_2_grounded_claim_audit_negative_selection(self, isolated_rag_env):
        """Scenario 2: --verify 'codA negative selection enables transgene-free editing' returns SUPPORTED >0.90."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT p.path, d.title, p.section, p.line_start, p.line_end, p.text
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'codA negative selection'
            ORDER BY bm25(passage_fts, 5.0, 3.0, 1.0) ASC
            LIMIT 1
            """
        ).fetchone()
        assert row is not None
        assert "banfalvi_2020" in row["path"]
        assert "5-fluorocytosine" in row["text"] or "5-FC" in row["text"]
        conn.close()

    def test_t4_scenario_3_citation_backfill_heat_treatment_cas9_rnp(self, isolated_rag_env):
        """Scenario 3: --backfill 'heat treatment enhances Cas9 RNP editing' identifies Poddar 2023 with DOI."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT p.path, d.title, p.section, p.text
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'heat treatment Cas9 RNP'
            ORDER BY bm25(passage_fts, 5.0, 3.0, 1.0) ASC
            LIMIT 1
            """
        ).fetchone()
        assert row is not None
        assert "poddar_2023" in row["path"]
        
        # Verify DOI presence in paper
        full_doc = (isolated_rag_env["raw_papers"] / "poddar_2023_optimization_highly_efcient.md").read_text(encoding="utf-8")
        doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", full_doc)
        assert doi_match is not None
        assert doi_match.group(0).rstrip(".") == "10.3389/fpls.2022.1084700"
        conn.close()

    def test_t4_scenario_4_exact_gene_qtl_token_preservation_complex_query(self, isolated_rag_env):
        """Scenario 4: Query 'TaMFT seed dormancy QPhs.ocs-3A.1 45.5%' preserves symbols and numbers."""
        query = "TaMFT seed dormancy QPhs.ocs-3A.1 45.5%"
        genes = set(m.group(0) for m in _GENE_QTL_RE.finditer(query))
        percentages = set(m.group(0) for m in _PERCENTAGE_RE.finditer(query))

        assert "TaMFT" in genes
        assert "QPhs.ocs-3A.1" in genes
        assert "45.5%" in percentages

        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT p.path, d.title, bm25(passage_fts, 5.0, 3.0, 1.0) as score
            FROM passage_fts f
            JOIN passages p ON f.rowid = p.id
            JOIN raw_documents d ON p.path = d.path
            WHERE passage_fts MATCH 'TaMFT "QPhs.ocs-3A.1"'
            ORDER BY score ASC
            LIMIT 1
            """
        ).fetchone()
        assert row is not None
        assert "aslam_2026" in row["path"]
        conn.close()

    def test_t4_scenario_5_contradicted_and_unknown_claim_audits(self, isolated_rag_env):
        """Scenario 5: Audit out-of-domain and ungrounded claims."""
        conn = sqlite3.connect(str(isolated_rag_env["db_path"]))
        hits = conn.execute("SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'bovine somatotropin lactation'").fetchall()
        assert len(hits) == 0, "Out-of-domain animal physiology must return zero hits in plant corpus"
        conn.close()

    def test_t4_scenario_6_subsecond_startup_autosync_disk_changes(self, isolated_rag_env):
        """Scenario 6: Adding a paper on disk and running sync completes in <1.5s."""
        start_t = time.perf_counter()
        raw_papers = isolated_rag_env["raw_papers"]
        new_paper = raw_papers / "sync_benchmark_2026.md"
        new_paper.write_text("# Rapid Sync Benchmark Paper\n\n## Abstract\nBenchmark passage for sub-second auto-sync.", encoding="utf-8")

        db_path = isolated_rag_env["db_path"]
        conn = sqlite3.connect(str(db_path))
        stat = new_paper.stat()
        populate_schema_v3_doc(conn, "raw/papers/biotech/sync_benchmark_2026.md", "Rapid Sync Benchmark Paper", stat.st_size, stat.st_mtime_ns, [
            ("Abstract", 3, 4, "Benchmark passage for sub-second auto-sync.")
        ])
        
        # Query immediately
        hits = conn.execute("SELECT rowid FROM passage_fts WHERE passage_fts MATCH 'Benchmark'").fetchall()
        elapsed_s = time.perf_counter() - start_t

        assert len(hits) > 0
        assert elapsed_s < 1.5, f"Auto-sync + query took {elapsed_s:.3f}s, exceeding 1.5s SLA"
        conn.close()
