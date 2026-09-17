"""Offline regression tests for Research Wiki runtime optimizations."""
from __future__ import annotations

import hashlib
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _manual_fingerprint(content: bytes, *tokens: str) -> str:
    digest = hashlib.sha256(content)
    for token in tokens:
        digest.update(b"\x00")
        digest.update(token.encode("utf-8"))
    return digest.hexdigest()


def test_fingerprint_cache_preserves_digest_and_reuses_file_read(tmp_path):
    from pipeline_state import _cached_file_hasher, fingerprint_file

    payload = b"pdf-like-content" * 100
    source = tmp_path / "paper.pdf"
    source.write_bytes(payload)
    _cached_file_hasher.cache_clear()

    first = fingerprint_file(source, "extractor:v1")
    second = fingerprint_file(source, "raw-prepass:v3")

    assert first == _manual_fingerprint(payload, "extractor:v1")
    assert second == _manual_fingerprint(payload, "raw-prepass:v3")
    info = _cached_file_hasher.cache_info()
    assert info.misses == 1
    assert info.hits >= 1


def test_fingerprint_cache_invalidates_when_file_changes(tmp_path):
    from pipeline_state import _cached_file_hasher, fingerprint_file

    source = tmp_path / "paper.pdf"
    _cached_file_hasher.cache_clear()
    source.write_bytes(b"first")
    first = fingerprint_file(source, "v1")
    source.write_bytes(b"second-content")
    second = fingerprint_file(source, "v1")
    assert first != second
    assert _cached_file_hasher.cache_info().misses == 2


def test_corrupt_pipeline_states_get_unique_backups(tmp_path):
    from pipeline_state import PipelineState

    state_path = tmp_path / "pipeline_state.json"
    state_path.write_text("{bad json", encoding="utf-8")
    assert PipelineState(state_path).stats() == {}
    state_path.write_text("{bad again", encoding="utf-8")
    assert PipelineState(state_path).stats() == {}

    backups = sorted(tmp_path.glob("pipeline_state.corrupt-*.json"))
    assert len(backups) == 2
    assert {p.read_text(encoding="utf-8") for p in backups} == {
        "{bad json", "{bad again"
    }


def test_pipeline_state_thread_safe_mark_and_save(tmp_path):
    from pipeline_state import PipelineState

    state_path = tmp_path / "state.json"
    state = PipelineState(state_path)

    def worker(offset: int) -> None:
        for value in range(50):
            state.mark_done("ingest", f"{offset + value}", {"value": value})

    threads = [threading.Thread(target=worker, args=(i * 50,)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()
    state.save()

    assert PipelineState(state_path).stats() == {"ingest": 200}


def test_config_and_client_have_no_machine_specific_env_override():
    for relative in ("config.py", "genai_client.py"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "/Users/" not in source
        assert "override=True" not in source
    config_source = (ROOT / "config.py").read_text(encoding="utf-8")
    assert 'DEFAULT_EMAIL = os.environ.get("DEFAULT_EMAIL", "")' in config_source


def _search_fixture(tmp_path):
    from research_retrieval import FullTextSearch

    search = FullTextSearch(str(tmp_path / "wiki"))
    doc_id = "sources/example"
    content = (
        "# Lignin study\n\n"
        "## Results\n"
        "Lignin biosynthesis was reduced in the edited plants. " * 8
    )
    search.documents = {doc_id: content}
    search.index = {doc_id: {"lignin": 8, "biosynthesis": 8, "plant": 8}}
    search.doc_metadata = {
        doc_id: {
            "title": "Lignin study",
            "type": "paper",
            "tags": [],
            "path": "sources/example.md",
            "length": 24,
            "title_terms": {"lignin": 1},
            "tag_terms": {},
            "is_stub": False,
            "evidence_quality": 0.9,
            "quality_flags": [],
        }
    }
    search.idf = {"lignin": 1.0, "biosynthesis": 1.0, "plant": 1.0}
    search.average_doc_length = 24.0
    search.index_version = 4
    return search


def test_summary_search_cache_returns_independent_results(tmp_path):
    search = _search_fixture(tmp_path)
    original_score = search._bm25_score
    calls = 0

    def counted(doc_id, plan):
        nonlocal calls
        calls += 1
        return original_score(doc_id, plan)

    search._bm25_score = counted
    first = search.search("lignin biosynthesis", top_k=10, mode="summary")
    calls_after_first = calls
    assert first and calls_after_first > 0
    assert search.last_search_report["cache_hit"] is False

    first[0].title = "mutated by caller"
    first[0].matches.append("caller-only")
    second = search.search("lignin biosynthesis", top_k=10, mode="summary")

    assert calls == calls_after_first
    assert search.last_search_report["cache_hit"] is True
    assert second[0].title == "Lignin study"
    assert "caller-only" not in second[0].matches


def test_vocabulary_cached_lookup_skips_recursive_stat_walk(tmp_path, monkeypatch):
    import wiki_vocabulary as vocabulary

    wiki = tmp_path / "wiki"
    page = wiki / "entities" / "gene.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        "---\ntags: [entity]\ntype: entity\nsource_count: 1\n---\n\n"
        "# Gene\n\n" + "substantive description " * 20,
        encoding="utf-8",
    )
    vocabulary.reset_cache()
    monkeypatch.setenv("WIKI_VOCAB_VALIDATION_INTERVAL", "60")
    first = vocabulary.get_index(wiki)

    def fail_full_scan(_root):
        raise AssertionError("cached lookup unexpectedly performed a recursive stat walk")

    monkeypatch.setattr(vocabulary, "_max_mtime", fail_full_scan)
    second = vocabulary.get_index(wiki)
    assert second is first


def _raw_search_fixture(tmp_path):
    from research_retrieval import FullTextSearch

    wiki = tmp_path / "wiki"
    raw_path = tmp_path / "raw" / "papers" / "demo" / "paper.md"
    (wiki / "sources").mkdir(parents=True)
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        "# Raw paper\n\n## Results\n"
        "Lignin biosynthesis was reduced in edited plants.\n",
        encoding="utf-8",
    )

    search = FullTextSearch(str(wiki))
    search.documents = {"sources/demo": "# Demo study\n"}
    search.index = {"sources/demo": {"lignin": 1, "biosynthesi": 1}}
    search.doc_metadata = {
        "sources/demo": {
            "title": "Demo study",
            "type": "paper",
            "tags": [],
            "path": "sources/demo.md",
            "length": 3,
            "title_terms": {"demo": 1},
            "tag_terms": {},
            "is_stub": False,
            "evidence_quality": 0.9,
            "quality_flags": [],
            "raw_path": "raw/papers/demo/paper.md",
        }
    }
    search._raw_path_to_docs = {
        "raw/papers/demo/paper.md": ["sources/demo"]
    }
    search.idf = {"lignin": 1.0, "biosynthesi": 1.0}
    search.average_doc_length = 3.0
    return search, raw_path


def test_evidence_skips_summary_stage_and_keeps_line_provenance(tmp_path):
    search, _ = _raw_search_fixture(tmp_path)

    def fail_summary_scoring(*args, **kwargs):
        raise AssertionError("evidence mode unexpectedly ran summary scoring")

    search._bm25_score = fail_summary_scoring
    results = search.search(
        "lignin biosynthesis", top_k=5, mode="evidence", doc_type="paper"
    )

    assert results
    assert results[0].paper == "sources/demo"
    assert results[0].source_path == "raw/papers/demo/paper.md"
    assert results[0].line_start == 3
    assert results[0].line_end == 4
    assert search.last_search_report["first_stage_matches"] == 0
    assert search.last_search_report["raw_index_used"] is True
    assert search.last_search_report["raw_documents_scanned"] == 0


def test_raw_passage_index_invalidates_when_source_changes(tmp_path):
    search, raw_path = _raw_search_fixture(tmp_path)
    first = search.search("lignin", mode="evidence", doc_type="paper")
    assert first
    assert search._raw_index_path.exists()

    previous = raw_path.stat()
    raw_path.write_text(
        "# Raw paper\n\n## Results\n"
        "The beta pathway changed in edited plants.\n",
        encoding="utf-8",
    )
    os.utime(raw_path, ns=(previous.st_atime_ns, previous.st_mtime_ns + 1))

    assert search.search("lignin", mode="evidence", doc_type="paper") == []
    changed = search.search("beta", mode="evidence", doc_type="paper")
    assert changed
    assert changed[0].source_path == "raw/papers/demo/paper.md"
    assert search.last_search_report["raw_index_used"] is True


def test_evidence_falls_back_to_raw_scan_when_fts_build_fails(tmp_path, monkeypatch):
    import sqlite3

    search, _ = _raw_search_fixture(tmp_path)

    def fail_index_build(*args, **kwargs):
        raise sqlite3.OperationalError("FTS5 unavailable")

    monkeypatch.setattr(search, "_build_raw_passage_index", fail_index_build)
    results = search.search("lignin", mode="evidence", doc_type="paper")

    assert results
    assert results[0].source_path == "raw/papers/demo/paper.md"
    assert search.last_search_report["raw_index_used"] is False
    assert search.last_search_report["raw_documents_scanned"] == 1


def test_build_index_warms_raw_passage_index(tmp_path):
    from research_retrieval import FullTextSearch

    wiki = tmp_path / "wiki"
    (wiki / "sources").mkdir(parents=True)
    raw_path = tmp_path / "raw" / "papers" / "demo.md"
    raw_path.parent.mkdir(parents=True)
    (wiki / "sources" / "demo.md").write_text(
        "# Demo study\n\n## Abstract Summary\nLignin biosynthesis study.\n",
        encoding="utf-8",
    )
    raw_path.write_text(
        "# Demo study\n\n## Results\nLignin biosynthesis changed.\n",
        encoding="utf-8",
    )

    search = FullTextSearch(str(wiki))
    search.build_index()

    assert search._raw_index_path.exists()
    results = search.search("lignin biosynthesis", mode="evidence", doc_type="paper")
    assert results
    assert search.last_search_report["raw_index_used"] is True
