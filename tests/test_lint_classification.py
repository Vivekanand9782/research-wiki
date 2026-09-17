from lint_wiki import classify_page_findings


def test_empty_relations_and_unsourced_prose_are_content_debt_only():
    content = """---
tags: [entity]
type: entity
date_created: 2026-07-29
date_updated: 2026-07-29
---

# Example

**Summary**:
A short summary.

**Sources**:
- [[paper]]

**Last updated**: 2026-07-29

---

This explanatory paragraph has no source wikilink.

## Related pages
"""

    structural, debt = classify_page_findings(
        content, is_source=False, source_stems={"paper"}
    )

    assert structural == []
    assert "'## Related pages' section is empty" in debt
    assert any(item.startswith("Unsourced body paragraph:") for item in debt)


def test_wrong_heading_and_misplaced_source_link_are_structural_errors():
    content = """# Example

## Sources
- [[paper]]

## Related pages
- [[paper]]
"""

    structural, debt = classify_page_findings(
        content, is_source=False, source_stems={"paper"}
    )

    assert len(structural) == 2
    assert any("## Sources" in item for item in structural)
    assert any("Source-paper wikilink" in item for item in structural)
    assert debt == []


def test_source_pages_get_only_applicable_structural_checks():
    content = """---
type: source
date_created: 2026-07-29
---

## Sources
- [[paper]]

## Related pages
"""

    structural, debt = classify_page_findings(
        content, is_source=True, source_stems={"paper"}
    )

    assert len(structural) == 1
    assert "## Sources" in structural[0]
    assert debt == []
