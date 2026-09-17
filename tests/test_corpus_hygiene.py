"""Unit tests for corpus hygiene: .attic filtering, reference section filtering, and deduplication.

Covers:
1. Exclusion of any paths matching `*/.attic/*` or `*.pre-agent.md`.
2. Filtering out passages whose section heading matches references/bibliography/literature cited
   or whose text is primarily a citation list.
3. Deduplication of documents by DOI / content hash / canonical filename across search & RAG engine.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research_retrieval import (
    FullTextSearch,
    Passage,
    SearchResult,
    _canonical_doc_key,
    _extract_doi,
    _is_excluded_path,
    _is_reference_or_citation_passage,
)
from rag_engine import RAGEngine


def test_is_excluded_path():
    """Verify that .attic paths and .pre-agent files are recognized and excluded."""
    assert _is_excluded_path("sources/.attic/paper.pre-agent.md")
    assert _is_excluded_path("wiki/sources/.attic/some_paper.md")
    assert _is_excluded_path("raw/papers/.attic/summary.pre-agent.json")
    assert _is_excluded_path("/Users/antigravity/research-wiki/.attic/file.md")
    assert _is_excluded_path("sources/tripathi_2024.pre-agent.md")
    assert _is_excluded_path("sources/tripathi_2024.pre-agent")
    assert _is_excluded_path(Path("wiki/sources/.attic/test.md"))
    
    # Live valid paths must NOT be excluded
    assert not _is_excluded_path("sources/uncategorized/sakthivel_2025.md")
    assert not _is_excluded_path("raw/papers/vpc_transgene_free/sakthivel_2025.md")
    assert not _is_excluded_path("entities/tamft.md")
    assert not _is_excluded_path("concepts/seed-dormancy.md")


def test_is_reference_or_citation_passage_headings():
    """Verify reference section heading matching while preserving biological references."""
    # Reference section headings
    assert _is_reference_or_citation_passage("References", "Some body text")
    assert _is_reference_or_citation_passage("**References**", "Some body text")
    assert _is_reference_or_citation_passage("## References", "Some body text")
    assert _is_reference_or_citation_passage("9. References", "Some body text")
    assert _is_reference_or_citation_passage("## 8. References and Notes", "Some body text")
    assert _is_reference_or_citation_passage("Literature Cited", "Some body text")
    assert _is_reference_or_citation_passage("## Literature Cited", "Some body text")
    assert _is_reference_or_citation_passage("Bibliography", "Some body text")
    assert _is_reference_or_citation_passage("Works Cited", "Some body text")
    assert _is_reference_or_citation_passage("Reference List", "Some body text")
    assert _is_reference_or_citation_passage("Reference", "Some body text")

    # Biological terms containing reference must NOT be classified as bibliography
    assert not _is_reference_or_citation_passage("Reference genome assembly", "We sequenced the reference genome")
    assert not _is_reference_or_citation_passage("Reference cultivar", "Nipponbare was used as the reference cultivar")
    assert not _is_reference_or_citation_passage("Reference sequence", "Alignment to the wheat reference sequence")
    assert not _is_reference_or_citation_passage("Results", "Standard gene expression results")


def test_is_reference_or_citation_passage_text_list():
    """Verify detection of citation list text even under generic headings."""
    citation_text = (
        "[1] Smith, J. et al. (2020) CRISPR editing in potato. Nature 500:10-15. https://doi.org/10.1038/s41586-020-001\n"
        "[2] Jones, A. & Miller, C. (2021) Plant genome engineering. Science 360:123-128. doi: 10.1126/science.123456\n"
        "[3] Zhang, Y. (2022) Vegetative propagation traits. Plant Cell 34:45-60. https://doi.org/10.1093/plcell/koac001"
    )
    assert _is_reference_or_citation_passage("Document opening", citation_text)

    regular_biological_text = (
        "We targeted the StGBSSI gene in potato using CRISPR/Cas9 ribonucleoproteins. "
        "Transformation efficiency reached 42.5% in the Russet Burbank background, as previously "
        "suggested (Smith et al., 2020). Amylose content was significantly reduced."
    )
    assert not _is_reference_or_citation_passage("Results", regular_biological_text)


def test_canonical_doc_key_deduplication():
    """Verify that duplicate papers with different paths/stems resolve to identical canonical keys."""
    doi_text_1 = "TYPE Review PUBLISHED 2025 DOI 10.3389/fgene.2025.1599242\n# Enhancing quality and climate..."
    doi_text_2 = "## CITATION Sakthivel SK 2025 doi: 10.3389/fgene.2025.1599242\n## Enhancing quality..."
    
    key1 = _canonical_doc_key(
        doc_id="sources/vpc/Sakthivel_SK_2025_Enhancing_quality_a54c2c2c67",
        title="Enhancing quality and climate resilient traits in vegetatively propagated polyploids",
        text=doi_text_1,
        source_path="raw/papers/vpc_transgene_free/Sakthivel_SK_2025_Enhancing_quality_a54c2c2c67.md",
    )
    key2 = _canonical_doc_key(
        doc_id="sources/uncategorized/sakthivel_2025_enhancing_quality_climate",
        title="Enhancing quality and climate resilient traits in vegetatively propagated polyploids",
        text=doi_text_2,
        source_path="raw/papers/PHS_tolerance/sakthivel_2025_enhancing_quality_climate.md",
    )

    assert key1 == "doi:10.3389/fgene.2025.1599242"
    assert key2 == "doi:10.3389/fgene.2025.1599242"
    assert key1 == key2


def test_search_excludes_attic_and_references_and_deduplicates(tmp_path):
    """End-to-end test verifying search exclusions and deduplication."""
    wiki = tmp_path / "wiki"
    sources = wiki / "sources"
    attic = sources / ".attic"
    sources.mkdir(parents=True)
    attic.mkdir(parents=True)

    # 1. Live document 1 (Sakthivel copy A)
    doc_a = (
        "---\ntags: [paper, gene_editing]\ndoi: 10.3389/fgene.2025.1599242\n---\n"
        "# Enhancing quality and climate resilient traits in vegetatively propagated polyploids\n\n"
        "## Results\n"
        "Genome editing in vegetatively propagated polyploid crops like potato and sugarcane offers huge gains."
    )
    (sources / "Sakthivel_SK_2025_a54c2c2c67.md").write_text(doc_a, encoding="utf-8")

    # 2. Duplicate document 2 (Sakthivel copy B with same DOI)
    doc_b = (
        "---\ntags: [paper, climate]\ndoi: 10.3389/fgene.2025.1599242\n---\n"
        "# Enhancing quality and climate resilient traits in vegetatively propagated polyploids\n\n"
        "## Discussion\n"
        "Vegetatively propagated crops face somaclonal variation challenges during tissue culture."
    )
    (sources / "sakthivel_2025_enhancing_quality.md").write_text(doc_b, encoding="utf-8")

    # 3. Archived draft in .attic (must NEVER be indexed/retrieved)
    doc_attic = (
        "---\ntags: [paper, draft]\n---\n"
        "# Draft Advancements in vegetatively propagated crops\n\n"
        "## Results\n"
        "Vegetatively propagated crops draft notes."
    )
    (attic / "tripathi_2024.pre-agent.md").write_text(doc_attic, encoding="utf-8")

    # 4. Another paper with a References section and Results section
    doc_c = (
        "---\ntags: [paper]\n---\n"
        "# Jayakody 2024 Vegetatively Propagated Potato\n\n"
        "## Results\n"
        "Targeted editing in vegetatively propagated Solanum tuberosum.\n\n"
        "## References\n"
        "1. Smith et al. (2020) Vegetatively propagated crops review. Nature 10:1-5. https://doi.org/10.1000/1\n"
        "2. Jones et al. (2021) Polyploids. Science 20:10-15. https://doi.org/10.1000/2"
    )
    (sources / "jayakody_2024_potato.md").write_text(doc_c, encoding="utf-8")

    search = FullTextSearch(str(wiki))
    search.build_index()

    # Verify indexed documents count (.attic draft must NOT be in documents)
    assert not any(".attic" in doc_id for doc_id in search.documents)
    assert not any(".pre-agent" in doc_id for doc_id in search.documents)

    # Search for vegetatively propagated
    results = search.search("vegetatively propagated crops", top_k=10, mode="summary")
    
    # Assert zero .attic
    assert not any(".attic" in r.paper or ".attic" in r.path for r in results)
    assert not any(".pre-agent" in r.paper for r in results)

    # Assert zero References section
    assert not any("references" in r.section.lower() or "bibliography" in r.section.lower() for r in results)

    # Assert Sakthivel is deduplicated (only 1 result for DOI 10.3389/fgene.2025.1599242)
    sakthivel_hits = [r for r in results if r.canonical_key == "doi:10.3389/fgene.2025.1599242"]
    assert len(sakthivel_hits) == 1, f"Expected 1 Sakthivel hit, got {len(sakthivel_hits)}"
