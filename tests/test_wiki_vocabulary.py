"""Tests for wiki_vocabulary (Task 4 of the ingestion-prompt overhaul).

Synthetic-wiki tests cover the hot paths (find_canonical, top_k_candidates,
mtime cache invalidation, stub-redirect skipping). One smoke test on the
live wiki/entities + wiki/concepts confirms a handful of known-canonical
lookups work today.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _write_page(path: Path, *, title: str, body: str = "Body text.",
                aliases: list[str] | None = None,
                kind: str = "entity",
                size_padding: int = 200) -> None:
    """Write a synthetic wiki page that exceeds the 200-byte stub threshold."""
    fm = ["---", f"tags: [{kind}]", f"type: {kind}",
          "date_created: 2026-05-27", "date_updated: 2026-05-27",
          "source_count: 1"]
    if aliases:
        fm.append(f"aliases: [{', '.join(aliases)}]")
    fm.append("---")
    pad = "x" * size_padding
    page = "\n".join(fm) + f"\n\n# {title}\n\n{body}\n\n{pad}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")


@pytest.fixture
def mini_wiki(tmp_path):
    """Build a tiny synthetic wiki with 4 entities + 2 concepts."""
    root = tmp_path / "wiki"
    _write_page(root / "entities" / "cas9.md", title="Cas9",
                aliases=["SpCas9", "CRISPR-associated 9"])
    _write_page(root / "entities" / "crispr-cas9.md", title="CRISPR/Cas9",
                aliases=["CRISPR Cas9"])
    _write_page(root / "entities" / "taphs1.md", title="TaPHS1")
    _write_page(root / "entities" / "stub-page.md", title="Stub",
                size_padding=0)  # below 200 bytes → should be skipped
    _write_page(root / "concepts" / "phenylpropanoid-pathway.md",
                title="Phenylpropanoid Pathway", kind="concept")
    _write_page(root / "concepts" / "lignin-biosynthesis.md",
                title="Lignin Biosynthesis", kind="concept")
    return root


@pytest.fixture(autouse=True)
def _reset_cache():
    """Ensure each test gets a clean module cache."""
    from wiki_vocabulary import reset_cache
    reset_cache()
    yield
    reset_cache()


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------

class TestBuildIndex:
    def test_counts_non_stub_pages(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        # 3 entities (stub-page skipped) + 2 concepts = 5
        assert len(idx) == 5

    def test_skips_stub_redirects(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        assert "stub-page" not in idx.entries

    def test_separates_entities_and_concepts_by_kind(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        assert idx.entries["cas9"].kind == "entity"
        assert idx.entries["phenylpropanoid-pathway"].kind == "concept"


# ---------------------------------------------------------------------------
# find_canonical
# ---------------------------------------------------------------------------

class TestFindCanonical:
    def test_exact_slug(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        assert idx.find_canonical("cas9") == "cas9"

    def test_case_insensitive(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        assert idx.find_canonical("CAS9") == "cas9"
        assert idx.find_canonical("Cas9") == "cas9"

    def test_alias_lookup(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        assert idx.find_canonical("SpCas9") == "cas9"
        assert idx.find_canonical("CRISPR-associated 9") == "cas9"

    def test_slug_with_hyphen_to_space(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        assert idx.find_canonical("crispr cas9") == "crispr-cas9"
        assert idx.find_canonical("CRISPR/Cas9") == "crispr-cas9"
        assert idx.find_canonical("phenylpropanoid pathway") == "phenylpropanoid-pathway"

    def test_unknown_term_returns_none(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        assert idx.find_canonical("NotAThing") is None
        assert idx.find_canonical("") is None


# ---------------------------------------------------------------------------
# top_k_candidates
# ---------------------------------------------------------------------------

class TestTopKCandidates:
    def test_returns_slugs_for_terms_in_text(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        text = "We used CRISPR/Cas9 to edit Cas9 in TaPHS1."
        cands = idx.top_k_candidates(text, k=10)
        assert "cas9" in cands
        assert "crispr-cas9" in cands
        assert "taphs1" in cands

    def test_ranks_by_frequency(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        text = "Cas9 Cas9 Cas9 Cas9 Cas9 TaPHS1"
        cands = idx.top_k_candidates(text, k=5)
        assert cands[0] == "cas9", f"expected cas9 first, got {cands}"

    def test_caps_at_k(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        text = "Cas9 CRISPR/Cas9 TaPHS1 phenylpropanoid pathway lignin biosynthesis"
        cands = idx.top_k_candidates(text, k=2)
        assert len(cands) == 2

    def test_empty_text_returns_empty(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        assert idx.top_k_candidates("", k=10) == []

    def test_multi_word_alias_via_bigram(self, mini_wiki):
        from wiki_vocabulary import build_index
        idx = build_index(mini_wiki)
        # bigram match on "phenylpropanoid pathway"
        cands = idx.top_k_candidates(
            "The phenylpropanoid pathway produces monolignols.", k=5
        )
        assert "phenylpropanoid-pathway" in cands


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

class TestCaching:
    def test_get_index_returns_singleton(self, mini_wiki):
        from wiki_vocabulary import get_index
        a = get_index(mini_wiki)
        b = get_index(mini_wiki)
        assert a is b

    def test_get_index_rebuilds_on_file_change(self, mini_wiki):
        from wiki_vocabulary import get_index
        a = get_index(mini_wiki)
        # Add a new entity and bump the wiki dir mtime.
        time.sleep(0.01)
        _write_page(mini_wiki / "entities" / "newgene.md", title="NewGene")
        # Touch the parent dir so its mtime advances reliably on macOS APFS.
        (mini_wiki / "entities").touch()
        b = get_index(mini_wiki)
        assert a is not b
        assert "newgene" in b.entries

    def test_force_rebuild(self, mini_wiki):
        from wiki_vocabulary import get_index
        a = get_index(mini_wiki)
        b = get_index(mini_wiki, force_rebuild=True)
        assert a is not b


# ---------------------------------------------------------------------------
# Live wiki smoke test (acts on the real corpus)
# ---------------------------------------------------------------------------

LIVE_WIKI = ROOT / "wiki"


@pytest.mark.skipif(not (LIVE_WIKI / "entities").exists(),
                    reason="live wiki not present")
class TestLiveWikiSmoke:
    def test_index_has_thousands_of_entries(self):
        from wiki_vocabulary import build_index
        idx = build_index(LIVE_WIKI)
        # Expected roughly 8500 entities + 1500 concepts; allow a wide
        # band so the test doesn't churn whenever the wiki grows.
        assert len(idx) > 5000

    def test_known_canonical_lookups(self):
        from wiki_vocabulary import build_index
        idx = build_index(LIVE_WIKI)
        for term in ("Cas9", "CRISPR/Cas9", "phenylpropanoid pathway"):
            assert idx.find_canonical(term) is not None, (
                f"expected {term!r} to resolve against the live wiki"
            )
