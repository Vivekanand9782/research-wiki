"""Unit and integration tests for RAG Query CLI arguments and formatters (Milestone 5 / R5)."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from query import main


class TestRAGQueryCLI:
    """Milestone 5 CLI Integration Tests."""

    def test_cli_verify_human_readable(self, capsys):
        """Verify --verify outputs formatted publication-grade audit report."""
        exit_code = main(["--verify", "codA negative selection enables transgene-free editing"])
        assert exit_code == 0
        captured = capsys.readouterr().out

        assert "ANTIGRAVITY CLAIM VERIFICATION AUDIT" in captured
        assert "CLAIM:" in captured
        assert "VERDICT:" in captured
        assert "PERFORMANCE:" in captured

    def test_cli_verify_json(self, capsys):
        """Verify --verify --json outputs valid JSON dictionary."""
        exit_code = main(["--verify", "codA negative selection enables transgene-free editing", "--json"])
        assert exit_code == 0
        captured = capsys.readouterr().out.strip()

        data = json.loads(captured)
        assert "claim" in data
        assert "verdict" in data
        assert "confidence" in data
        assert "primary_source" in data
        assert "total_ms" in data

    def test_cli_backfill_human_readable(self, capsys, monkeypatch):
        """Verify --backfill outputs structured citation backfill report."""
        from rag_engine import CitationBackfillResult, RAGEngine
        mock_res = CitationBackfillResult(
            statement="heat treatment enhances Cas9 RNP editing",
            markdown_citation="[LeBlanc et al. (2018)](doi:10.1016/j.plantsci.2017.11.004)",
            slug="leblanc_2018_heat_treatment",
            doi="10.1016/j.plantsci.2017.11.004",
            title="Heat treatment enhances Cas9 RNP editing efficiency in plants",
            authors="LeBlanc et al.",
            year=2018,
            path="raw/papers/leblanc_2018.md",
            lines="45-52",
            section="Results",
            excerpt="Heat stress at 37C significantly elevated targeted mutation rates.",
            total_ms=1.5,
        )
        monkeypatch.setattr(RAGEngine, "backfill_citation", lambda self, *args, **kwargs: mock_res)
        exit_code = main(["--backfill", "heat treatment enhances Cas9 RNP editing"])
        assert exit_code == 0
        captured = capsys.readouterr().out

        assert "ANTIGRAVITY CITATION BACKFILL" in captured
        assert "STATEMENT:" in captured
        assert "MARKDOWN CITATION:" in captured
        assert "DOI:" in captured
        assert "PERFORMANCE:" in captured

    def test_cli_backfill_json(self, capsys, monkeypatch):
        """Verify --backfill --json outputs valid JSON dictionary."""
        from rag_engine import CitationBackfillResult, RAGEngine
        mock_res = CitationBackfillResult(
            statement="heat treatment enhances Cas9 RNP editing",
            markdown_citation="[LeBlanc et al. (2018)](doi:10.1016/j.plantsci.2017.11.004)",
            slug="leblanc_2018_heat_treatment",
            doi="10.1016/j.plantsci.2017.11.004",
            title="Heat treatment enhances Cas9 RNP editing efficiency in plants",
            authors="LeBlanc et al.",
            year=2018,
            path="raw/papers/leblanc_2018.md",
            lines="45-52",
            section="Results",
            excerpt="Heat stress at 37C significantly elevated targeted mutation rates.",
            total_ms=1.5,
        )
        monkeypatch.setattr(RAGEngine, "backfill_citation", lambda self, *args, **kwargs: mock_res)
        exit_code = main(["--backfill", "heat treatment enhances Cas9 RNP editing", "--json"])
        assert exit_code == 0
        captured = capsys.readouterr().out.strip()

        data = json.loads(captured)
        assert "statement" in data
        assert "markdown_citation" in data
        assert "slug" in data
        assert "doi" in data
        assert "title" in data
        assert "total_ms" in data

    def test_cli_save_flag(self, tmp_path, capsys):
        """Verify --save writes response output to specified markdown path."""
        out_file = tmp_path / "test_rag_output.md"
        exit_code = main(["TaMFT seed dormancy", "--mode", "evidence", "--save", str(out_file)])
        assert exit_code == 0

        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_cli_default_mode_is_evidence(self, capsys):
        """Verify running without --mode or --llm defaults to evidence retrieval with evidence drawer."""
        exit_code = main(["maize ethanol", "--top-k", "2"])
        assert exit_code == 0
        captured = capsys.readouterr().out
        assert "Mode: Local SQLite FTS5/BM25 (Direct Cognitive Execution)" in captured
        assert "RETRIEVAL: evidence" in captured
        assert "RETRIEVED EVIDENCE SOURCES" in captured

    def test_cli_llm_flag_activates_hybrid_mode(self):
        """Verify passing --llm flag switches mode to hybrid."""
        with patch("query.RAGEngine") as mock_engine_cls:
            mock_engine = mock_engine_cls.return_value
            mock_res = type("DummyRes", (), {
                "answer": "Test answer",
                "hits": [],
                "total_ms": 100.0,
                "retrieval_ms": 50.0,
                "synthesis_ms": 50.0,
                "grounding_ok": True,
                "grounding_confidence": 1.0,
                "verified_entities": [],
                "unsupported_entities": [],
            })()
            mock_engine.query.return_value = mock_res
            exit_code = main(["maize ethanol", "--llm", "--no-stream"])
            assert exit_code == 0
            mock_engine.query.assert_called_once()
            _, kwargs = mock_engine.query.call_args
            assert kwargs.get("mode") == "hybrid"

