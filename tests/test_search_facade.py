"""Tests for search.py facade and SearchCLI integration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_search_facade_exports():
    """Verify all re-exported symbols and classes exist on search module."""
    import search

    assert hasattr(search, "DOC_TYPES")
    assert hasattr(search, "INDEX_VERSION")
    assert hasattr(search, "SEARCH_MODES")
    assert hasattr(search, "FullTextSearch")
    assert hasattr(search, "SearchCLI")
    assert hasattr(search, "SearchResult")
    assert hasattr(search, "main")


def test_search_cli_empty_results(tmp_path, capsys):
    """Test SearchCLI on an empty wiki folder."""
    import search

    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    cli = search.SearchCLI(str(wiki_dir))
    cli.run("CRISPR Cas9", verbose=True)

    captured = capsys.readouterr()
    assert "No results found." in captured.out


def test_search_cli_with_content(tmp_path, capsys):
    """Test SearchCLI indexing and query retrieval with sample markdown."""
    import search

    wiki_dir = tmp_path / "wiki"
    sources_dir = wiki_dir / "sources"
    sources_dir.mkdir(parents=True)

    sample_md = sources_dir / "smith_2024_wheat.md"
    sample_md.write_text(
        "# High-efficiency CRISPR-Cas9 genome editing in hexaploid wheat\n\n"
        "## Abstract\n"
        "Here we demonstrate targeted mutagenesis in Triticum aestivum using CRISPR Cas9 ribonucleoproteins.\n\n"
        "## Results\n"
        "Editing efficiency reached 85% in TaGW2 promoter regions without off-target activity.\n",
        encoding="utf-8",
    )

    cli = search.SearchCLI(str(wiki_dir))
    cli.run("CRISPR Cas9 hexaploid wheat", verbose=True, top_k=5)

    captured = capsys.readouterr()
    assert "Results for" in captured.out
    assert "smith_2024_wheat" in captured.out or "CRISPR" in captured.out
