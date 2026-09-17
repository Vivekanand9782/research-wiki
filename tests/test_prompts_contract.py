"""Contract tests: prompts.py, validation.py, and genai_client.py must agree.

These tests lock the section/frontmatter contract so future changes to any
one of the three files can't silently drift apart. They also pin the
strict-vs-lenient regex distinction the refactored
`genai_client.validate_structured_summary` and
`validate_structured_summary_strict` rely on.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module", autouse=True)
def _stub_genai_dependencies():
    """genai_client imports `google.genai` and `config` at module load. Stub
    them like tests/test_pdf_extractor.py does so this test file is hermetic.

    Also evict any pre-stubbed `genai_client` from sys.modules so we get a
    fresh import of the real module — `test_pdf_extractor.py` installs a
    stub `genai_client` that lacks `validate_structured_summary_strict`,
    and pytest may run that test first.
    """
    fake_config = types.ModuleType("config")
    fake_config.AI_MODEL = "gpt-oss-120b"
    fake_config.FILTER_MODEL = "gpt-oss-120b"
    fake_config.VISION_MODEL = "gpt-oss-120b"
    fake_config.PROJECT_ID = "stub"
    fake_config.LOCATION = "global"
    sys.modules["config"] = fake_config

    if "google" not in sys.modules:
        google_mod = types.ModuleType("google")
        genai_mod = types.ModuleType("google.genai")
        genai_types_mod = types.ModuleType("google.genai.types")

        class _StubPart:
            @staticmethod
            def from_bytes(*a, **kw):
                return None

        genai_types_mod.Part = _StubPart
        genai_types_mod.GenerateContentConfig = lambda **kw: None
        genai_types_mod.EmbedContentConfig = lambda **kw: None

        class _StubClient:
            def __init__(self, *a, **kw):
                self.models = types.SimpleNamespace(
                    generate_content=lambda **kw: types.SimpleNamespace(text=""),
                    embed_content=lambda **kw: types.SimpleNamespace(embeddings=[]),
                )

        genai_mod.Client = _StubClient
        genai_mod.types = genai_types_mod
        google_mod.genai = genai_mod
        sys.modules["google"] = google_mod
        sys.modules["google.genai"] = genai_mod
        sys.modules["google.genai.types"] = genai_types_mod

    sys.path.insert(0, str(ROOT))
    # Evict possibly-stubbed genai_client / prompts / validation so the real
    # modules get imported on demand inside each test.
    for name in ("genai_client", "prompts", "validation"):
        sys.modules.pop(name, None)
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_full_summary(
    *, frontmatter: bool = True, headings: list[str] | None = None,
    extra_wikilinks: int = 5,
) -> str:
    """Synthesize a syntactically-clean summary with the requested headings."""
    import prompts
    if headings is None:
        headings = prompts.required_headers()
    parts = []
    if frontmatter:
        parts.append(
            "---\n"
            "tags: [test]\n"
            "type: source\n"
            "date_created: 2026-05-27\n"
            "date_updated: 2026-05-27\n"
            "source_count: 1\n"
            'doi: "10.1234/test"\n'
            'authors: "Test et al."\n'
            "year: 2026\n"
            'journal: "Test Journal"\n'
            "---\n"
        )
    for h in headings:
        # The prompt rules for these two sections mandate wikilinks, and the
        # strict validator now reports a section that renders with none. A
        # "syntactically-clean summary" has to satisfy that to represent valid
        # output.
        if h == "Key Concepts & Theory":
            body = ("- **[[Seed Dormancy]]**: Definition.\n"
                    "- **[[Abscisic Acid]]**: Definition.\n"
                    "- **[[Gibberellin]]**: Definition.")
        elif h == "Important Entities":
            body = ("* **Genes/Proteins**:\n- [[TaPHS1]]\n- [[MKK3]]\n"
                    "* **Organisms**:\n- [[Triticum aestivum]]\n"
                    "* **Tools/Techniques/Software**:\n- [[CRISPR-Cas9]]\n- [[qRT-PCR]]")
        else:
            body = f"Content for {h}."
        parts.append(f"## {h}\n{body}\n")
    if extra_wikilinks > 0:
        parts.append(" ".join(f"[[entity{i}]]" for i in range(extra_wikilinks)))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 1. Single-source-of-truth invariants
# ---------------------------------------------------------------------------

class TestSingleSourceOfTruth:
    def test_prompts_required_sections_count(self):
        import prompts
        assert len(prompts.REQUIRED_SECTIONS) == 15
        assert len(prompts.required_headers()) == 15

    def test_prompts_lenient_subset_count(self):
        import prompts
        assert len(prompts.lenient_required_headers()) == 5

    def test_prompts_lenient_is_subset_of_strict(self):
        import prompts
        strict = set(prompts.required_headers())
        lenient = set(prompts.lenient_required_headers())
        assert lenient.issubset(strict), (
            f"lenient sections {lenient - strict} are not in the 12-section contract"
        )

    def test_prompts_lenient_matches_historical_5(self):
        import prompts
        # These are the exact 5 that genai_client.validate_structured_summary
        # checked before the refactor. If you change them, every existing
        # on-disk summary may suddenly fail re-validation.
        assert prompts.lenient_required_headers() == [
            "Title & Metadata",
            "Abstract Summary",
            "Methods & Experimental Design",
            "Key Results & Data",
            "Conclusions & Implications",
        ]

    def test_validation_required_headers_matches_prompts(self):
        import prompts
        from validation import REQUIRED_HEADERS
        assert REQUIRED_HEADERS == prompts.required_headers()

    def test_required_sections_are_in_canonical_order(self):
        import prompts
        canonical = [
            "Title & Metadata",
            "Abstract Summary",
            "Introduction & Background",
            "Key Concepts & Theory",
            "Important Entities",
            "Methods & Experimental Design",
            "Key Results & Data",
            "Mechanistic Insights",
            "Conclusions & Implications",
            "Limitations & Caveats",
            "Contradictory Findings",
            "Outdated Models",
            "Under-Researched Populations",
            "Future Directions",
            "Key References to Follow Up",
        ]
        assert prompts.required_headers() == canonical


# ---------------------------------------------------------------------------
# 2. Round-trip: a full summary passes both validators
# ---------------------------------------------------------------------------

class TestRoundTripBothValidators:
    def test_full_summary_passes_lenient(self):
        from genai_client import validate_structured_summary
        result = validate_structured_summary(_build_full_summary())
        assert result == {"valid": True, "missing_sections": []}

    def test_full_summary_passes_strict(self):
        from genai_client import validate_structured_summary_strict
        result = validate_structured_summary_strict(_build_full_summary())
        assert result == {"valid": True, "missing_sections": []}

    def test_full_summary_passes_summary_validator(self):
        from validation import SummaryValidator
        result = SummaryValidator().validate(_build_full_summary())
        assert result.valid is True
        assert result.missing_sections == []

    def test_lenient_only_summary_fails_strict(self):
        """A summary with only the 5 lenient sections passes lenient but
        must fail strict — that's the whole point of the strict variant."""
        import prompts
        from genai_client import (
            validate_structured_summary,
            validate_structured_summary_strict,
        )
        s = _build_full_summary(headings=prompts.lenient_required_headers())
        assert validate_structured_summary(s)["valid"] is True
        strict = validate_structured_summary_strict(s)
        assert strict["valid"] is False
        assert len(strict["missing_sections"]) == 10


# ---------------------------------------------------------------------------
# 3. Strict regex refuses drift the lenient regex tolerates
# ---------------------------------------------------------------------------

class TestStrictRefusesDrift:
    @pytest.fixture
    def strict(self):
        from genai_client import validate_structured_summary_strict
        return validate_structured_summary_strict

    @pytest.fixture
    def lenient(self):
        from genai_client import validate_structured_summary
        return validate_structured_summary

    def _summary_with_one_drifted_heading(self, drifted: str) -> str:
        """Build a summary where exactly the first heading is replaced with `drifted`."""
        import prompts
        headings = prompts.required_headers()
        parts = ["---\n"
                 "tags: [test]\ntype: source\ndate_created: 2026-05-27\n"
                 "date_updated: 2026-05-27\nsource_count: 1\n"
                 'doi: "10.x/y"\nauthors: "T"\nyear: 2026\n'
                 'journal: "J"\n---\n']
        for i, h in enumerate(headings):
            line = drifted if i == 0 else f"## {h}"
            parts.append(f"{line}\nContent.\n")
        return "\n".join(parts)

    @pytest.mark.parametrize("drifted_heading", [
        "## 1. Title & Metadata",      # leading number
        "## **Title & Metadata**",     # bolded
        "### Title & Metadata",        # H3 instead of H2
        "##Title & Metadata",          # missing space
        "## Title & Metadata extra",   # trailing junk
    ])
    def test_strict_rejects_drift(self, strict, drifted_heading):
        s = self._summary_with_one_drifted_heading(drifted_heading)
        result = strict(s)
        assert result["valid"] is False, (
            f"strict validator should have rejected {drifted_heading!r}"
        )
        assert "Title & Metadata" in result["missing_sections"]

    def test_lenient_tolerates_numbered_and_bold(self, lenient):
        # The lenient validator was historically forgiving of these, and
        # the existing on-disk corpus relies on that. Don't tighten without
        # bumping FORMAT_VERSION.
        for drifted in ["## 1. Title & Metadata", "## **Title & Metadata**"]:
            s = self._summary_with_one_drifted_heading(drifted)
            result = lenient(s)
            assert result["valid"] is True, (
                f"lenient validator should have accepted {drifted!r}, got {result}"
            )


# ---------------------------------------------------------------------------
# 4. Frontmatter schema
# ---------------------------------------------------------------------------

class TestFrontmatterSchema:
    def test_required_keys_match_documented_set(self):
        import prompts
        # If you add/remove a frontmatter key here, you must also update
        # the prompt builder (Task 3) and the renderer (Task 7).
        expected = {"tags", "type", "date_created", "date_updated",
                    "source_count", "doi", "authors", "year", "journal"}
        assert set(prompts.required_frontmatter_keys()) == expected

    def test_nullable_keys_are_the_metadata_ones(self):
        import prompts
        nullable = {k.name for k in prompts.FRONTMATTER_KEYS if k.nullable}
        # tags/type/dates/source_count must always be filled. The metadata
        # fields (doi/authors/year/journal) may be JSON null when genuinely
        # unknown — Stage B (Task 7) renders null → "Not reported in this paper."
        assert nullable == {"doi", "authors", "year", "journal"}


# ---------------------------------------------------------------------------
# 5. lint_summary helper
# ---------------------------------------------------------------------------

class TestLintSummary:
    def test_lint_full_summary_is_valid_high_score(self):
        from prompts import lint_summary
        report = lint_summary(_build_full_summary())
        assert report.valid is True
        assert report.score >= 90  # full summary, frontmatter, 5 wikilinks
        assert report.has_frontmatter is True
        assert report.wikilink_count >= 5

    def test_lint_missing_sections(self):
        from prompts import lint_summary
        # Drop the last 3 headings.
        import prompts
        headings = prompts.required_headers()[:9]
        report = lint_summary(_build_full_summary(headings=headings))
        assert report.valid is False
        assert len(report.missing_sections) == 6

    def test_lint_no_frontmatter(self):
        from prompts import lint_summary
        report = lint_summary(_build_full_summary(frontmatter=False))
        assert report.has_frontmatter is False
        assert any("frontmatter" in e.lower() for e in report.errors)


# ---------------------------------------------------------------------------
# 6. Task 6 — table/equation placeholder awareness + truncation transparency
# ---------------------------------------------------------------------------

class TestTablesEquationsTruncationBlocks:
    def test_tables_block_lists_captions(self):
        from prompts import build_main_prompt
        tables = [
            {"id": "TAB_1_paper", "caption": "QTL summary", "page": 4},
            {"id": "TAB_2_paper", "caption": "Cultivars used", "page": 6},
        ]
        p = build_main_prompt("SRC", tables=tables)
        assert "TABLES IN THIS PAPER (2)" in p
        assert "{{TAB_1_paper}}" in p
        assert "QTL summary" in p
        assert "Cultivars used" in p
        # Instruction to reference by ID.
        assert "Reference these by their {{TAB_n_<paper>}} ID" in p

    def test_tables_block_caps_captions_at_max(self):
        from prompts import build_main_prompt, MAX_TABLE_CAPTIONS_IN_PROMPT
        big = [
            {"id": f"TAB_{i}_p", "caption": f"caption {i}", "page": i}
            for i in range(MAX_TABLE_CAPTIONS_IN_PROMPT + 5)
        ]
        p = build_main_prompt("SRC", tables=big)
        assert f"TABLES IN THIS PAPER ({MAX_TABLE_CAPTIONS_IN_PROMPT + 5})" in p
        assert "and 5 more" in p
        # First N captions appear, the (N+1)th does not.
        assert f"caption {MAX_TABLE_CAPTIONS_IN_PROMPT - 1}" in p
        assert f"caption {MAX_TABLE_CAPTIONS_IN_PROMPT}" not in p

    def test_tables_block_collapses_when_empty(self):
        from prompts import build_main_prompt
        p = build_main_prompt("SRC")
        assert "TABLES IN THIS PAPER: none detected." in p
        # No specific table IDs (TAB_1_, TAB_2_, etc) when there are no tables.
        # The rules block still mentions {{TAB_n_<paper>}} as a format
        # reference, so we don't forbid the literal `{{TAB_` outright.
        assert "{{TAB_1_" not in p
        assert "{{TAB_2_" not in p

    def test_equations_block_renders_ids_only(self):
        from prompts import build_main_prompt
        eqs = [{"id": "EQ_1_p"}, {"id": "EQ_2_p"}]
        p = build_main_prompt("SRC", equations=eqs)
        assert "EQUATIONS IN THIS PAPER (2)" in p
        assert "{{EQ_1_p}}" in p and "{{EQ_2_p}}" in p

    def test_equations_block_collapses_when_empty(self):
        from prompts import build_main_prompt
        p = build_main_prompt("SRC")
        assert "EQUATIONS IN THIS PAPER" not in p

    def test_truncation_warning_appears(self):
        from prompts import build_main_prompt
        p = build_main_prompt("SRC", source_was_truncated=True,
                              original_text_len=200_000)
        assert "INPUT TRUNCATION WARNING" in p
        assert "200,000" in p
        assert "Limitations & Caveats" in p

    def test_truncation_warning_collapses_when_not_truncated(self):
        from prompts import build_main_prompt
        p = build_main_prompt("SRC", source_was_truncated=False)
        assert "INPUT TRUNCATION WARNING" not in p


# ---------------------------------------------------------------------------
# 7. Task 8 — paper-type-aware section variants + extraction targets
# ---------------------------------------------------------------------------

class TestPaperTypeVariants:
    def test_correction_notice_has_4_sections(self):
        from prompts import headers_for
        h = headers_for("correction_notice")
        assert h == [
            "Title & Metadata",
            "Correction Summary",
            "Original Citation",
            "Limitations & Caveats",
        ]

    def test_review_swaps_methods_for_reviewed_literature(self):
        from prompts import headers_for
        h = headers_for("review")
        assert "Methods & Experimental Design" not in h
        assert "Reviewed Literature & Inclusion Criteria" in h
        assert len(h) == 15

    def test_primary_research_uses_12_section_default(self):
        from prompts import headers_for, required_headers
        assert headers_for("primary_research") == required_headers()

    def test_unknown_type_falls_back_to_12(self):
        from prompts import headers_for, required_headers
        assert headers_for("totally_unknown") == required_headers()


class TestExtractTargets:
    def test_primary_research_has_qtl_targets(self):
        from prompts import extract_targets_for
        et = extract_targets_for("primary_research")
        assert "Key Results & Data" in et
        joined = " ".join(et["Key Results & Data"])
        assert "QTL" in joined
        assert "p-values" in joined.lower() or "p-value" in joined.lower()

    def test_review_has_inclusion_criteria_targets(self):
        from prompts import extract_targets_for
        et = extract_targets_for("review")
        assert "Reviewed Literature & Inclusion Criteria" in et

    def test_correction_notice_has_original_citation_targets(self):
        from prompts import extract_targets_for
        et = extract_targets_for("correction_notice")
        assert "Original Citation" in et

    def test_unknown_type_returns_empty(self):
        from prompts import extract_targets_for
        assert extract_targets_for("totally_unknown") == {}


class TestExtractTargetsRenderInPrompts:
    def test_primary_research_prompt_contains_qtl_target_line(self):
        from prompts import build_main_prompt
        p = build_main_prompt("SRC", paper_type="primary_research")
        assert "<extract_targets" in p
        assert "QTL nomenclature" in p

    def test_correction_notice_prompt_uses_4_headings(self):
        from prompts import build_stage_a_prompt
        p = build_stage_a_prompt("SRC", paper_type="correction_notice")
        # The CSV of headings the model is told to emit.
        assert "Title & Metadata" in p
        assert "Correction Summary" in p
        assert "Original Citation" in p
        # The 12-section primary headings must NOT appear in the
        # Stage A required-keys directive when paper_type is correction.
        # (They may appear elsewhere in the schema dump — this is a
        # narrow check on the headings_csv line.)
        # Find the "exactly these keys, in order" line.
        idx = p.find("exactly these keys, in order")
        assert idx > 0
        snippet = p[idx:idx + 400]
        assert "Mechanistic Insights" not in snippet


# ---------------------------------------------------------------------------
# 8. Paper-type-aware strict validator
# ---------------------------------------------------------------------------

class TestPaperTypeAwareValidator:
    @staticmethod
    def _with_source_envelope(body: str) -> str:
        return (
            "---\ntags: [test]\ntype: source\ndate_created: 2026-07-29\n"
            "date_updated: 2026-07-29\nsource_count: 1\n---\n\n" + body
        )

    def test_correction_notice_4_section_validates_with_paper_type(self):
        from genai_client import validate_structured_summary_strict
        md = (
            "## Title & Metadata\nx\n"
            "## Correction Summary\nx\n"
            "## Original Citation\nx\n"
            "## Limitations & Caveats\nx\n"
        )
        md = self._with_source_envelope(md)
        v = validate_structured_summary_strict(md, paper_type="correction_notice")
        assert v["valid"] is True
        assert v["missing_sections"] == []

    def test_correction_notice_4_section_fails_default_12(self):
        from genai_client import validate_structured_summary_strict
        md = (
            "## Title & Metadata\nx\n"
            "## Correction Summary\nx\n"
            "## Original Citation\nx\n"
            "## Limitations & Caveats\nx\n"
        )
        md = self._with_source_envelope(md)
        v = validate_structured_summary_strict(md)  # no paper_type
        assert v["valid"] is False
        # Of the 4 correction-notice headings, only 2 (Title & Metadata,
        # Limitations & Caveats) are also in the 15-section default.
        # Correction Summary and Original Citation are correction-only.
        # So the default validator finds 2 of 15 and reports 13 missing.
        assert len(v["missing_sections"]) == 13

    def test_review_variant_validates(self):
        from genai_client import validate_structured_summary_strict
        # Build a 12-heading md but with Reviewed Literature replacing Methods.
        from prompts import headers_for
        md = "\n".join(f"## {h}\nbody\n" for h in headers_for("review"))
        md = self._with_source_envelope(md)
        v = validate_structured_summary_strict(md, paper_type="review")
        assert v["valid"] is True

    def test_unknown_paper_type_falls_back_to_12(self):
        from prompts import required_headers
        from genai_client import validate_structured_summary_strict
        md = "\n".join(f"## {h}\nbody\n" for h in required_headers())
        md = self._with_source_envelope(md)
        v = validate_structured_summary_strict(md, paper_type="totally_unknown")
        assert v["valid"] is True


# ---------------------------------------------------------------------------
# 9. Source-document envelope guards (recovery regression, 2026-07-29)
# ---------------------------------------------------------------------------

class TestSourceDocumentEnvelopeValidation:
    @staticmethod
    def _valid_source(*, paper_type: str | None = None) -> str:
        from prompts import headers_for, required_headers

        headings = headers_for(paper_type) if paper_type else required_headers()
        frontmatter = (
            "---\n"
            "tags: [test]\n"
            "type: source\n"
            "date_created: 2026-07-29\n"
            "date_updated: 2026-07-29\n"
            "source_count: 1\n"
            "---\n\n"
        )
        return frontmatter + "\n".join(f"## {heading}\nBody.\n" for heading in headings)

    @pytest.mark.parametrize(
        "mutate, expected_issue",
        [
            (lambda text: text[text.index("## Title & Metadata"):], "YAML frontmatter"),
            (lambda text: text.replace("\n---\n\n## Title", "\n...\n\n## Title", 1), "YAML frontmatter"),
            (lambda text: text.replace("type: source\n", "", 1), "frontmatter.type"),
            (lambda text: text.replace("date_created: 2026-07-29\n", "", 1), "frontmatter.date_created"),
            (lambda text: "I will repair the document.\n" + text, "YAML frontmatter"),
            (lambda text: "```markdown\n" + text + "\n```", "YAML frontmatter"),
            (lambda text: text.replace("type: source", "type: research-paper", 1), "frontmatter.type"),
        ],
    )
    def test_strict_validator_rejects_malformed_source_envelopes(self, mutate, expected_issue):
        from genai_client import validate_structured_summary_strict

        result = validate_structured_summary_strict(mutate(self._valid_source()))
        assert result["valid"] is False
        assert expected_issue in result["missing_sections"]

    def test_correction_notice_with_valid_envelope_passes(self):
        from genai_client import validate_structured_summary_strict

        result = validate_structured_summary_strict(
            self._valid_source(paper_type="correction_notice"),
            paper_type="correction_notice",
        )
        assert result == {"valid": True, "missing_sections": []}

    def test_linter_accepts_correction_summary_as_abstract_variant(self):
        from lint_wiki import validate_source_page

        content = self._valid_source(paper_type="correction_notice")
        assert validate_source_page(content) == []
