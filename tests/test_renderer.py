"""Tests for renderer.py (Task 7 Stage B)."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module", autouse=True)
def _stub_genai():
    """Stub heavy imports the same way test_prompts_contract.py does so we
    can import genai_client.validate_structured_summary_strict cleanly."""
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
            def from_bytes(*a, **kw): return None

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

    for name in ("genai_client", "prompts", "validation", "renderer"):
        sys.modules.pop(name, None)
    yield


def _full_payload(**overrides) -> dict:
    """Build a minimal-but-valid Stage A payload for tests."""
    from prompts import required_headers
    payload = {
        "frontmatter": {
            "tags": ["test"],
            "doi": "10.1/test",
            "authors": "Smith et al.",
            "year": 2026,
            "journal": "Test Journal",
        },
        "paper_type": "primary_research",
        "sections": {h: {"text": f"Body for {h}."} for h in required_headers()},
    }
    if "frontmatter" in overrides:
        payload["frontmatter"].update(overrides.pop("frontmatter"))
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# 1. Round-trip: full payload renders into a strict-validator-passing summary
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_full_payload_passes_strict_validator(self):
        from renderer import render_summary_from_json
        from genai_client import validate_structured_summary_strict
        r = render_summary_from_json(
            _full_payload(), paper_name="test_paper", today_iso="2026-05-27",
        )
        v = validate_structured_summary_strict(r.markdown)
        assert v["valid"], f"missing: {v['missing_sections']}"

    def test_renders_all_12_sections_in_canonical_order(self):
        from renderer import render_summary_from_json
        from prompts import required_headers
        r = render_summary_from_json(_full_payload(), today_iso="2026-05-27")
        positions = [r.markdown.index(f"## {h}") for h in required_headers()]
        assert positions == sorted(positions), (
            "sections not in canonical order"
        )

    def test_includes_format_version(self):
        from renderer import render_summary_from_json
        from prompts import FORMAT_VERSION
        r = render_summary_from_json(_full_payload(), today_iso="2026-05-27")
        assert f"format_version: {FORMAT_VERSION}" in r.markdown


# ---------------------------------------------------------------------------
# 2. Frontmatter — nullables, types, defaults
# ---------------------------------------------------------------------------

class TestFrontmatter:
    def test_null_doi_renders_as_yaml_null(self):
        from renderer import render_summary_from_json
        r = render_summary_from_json(
            _full_payload(frontmatter={"doi": None}), today_iso="2026-05-27",
        )
        assert "\ndoi: null\n" in r.markdown
        # And NOT the placeholder string.
        assert "10.xxxx/xxxxx" not in r.markdown

    def test_null_authors_renders_as_yaml_null(self):
        from renderer import render_summary_from_json
        r = render_summary_from_json(
            _full_payload(frontmatter={"authors": None}), today_iso="2026-05-27",
        )
        assert "\nauthors: null\n" in r.markdown

    def test_authors_with_colon_gets_quoted(self):
        from renderer import render_summary_from_json
        r = render_summary_from_json(
            _full_payload(frontmatter={"authors": "Smith: et al."}),
            today_iso="2026-05-27",
        )
        # Colon-bearing strings must be quoted to avoid YAML parse drift.
        assert 'authors: "Smith: et al."' in r.markdown

    def test_required_keys_default_when_missing(self):
        from renderer import render_summary_from_json
        # Drop 'type' and 'source_count' from the payload — renderer fills in.
        payload = _full_payload()
        payload["frontmatter"].pop("type", None)
        payload["frontmatter"].pop("source_count", None)
        r = render_summary_from_json(payload, today_iso="2026-05-27")
        assert "type: source" in r.markdown
        assert "source_count: 1" in r.markdown

    def test_dates_default_to_today_iso(self):
        from renderer import render_summary_from_json
        r = render_summary_from_json(_full_payload(), today_iso="2026-05-27")
        assert "date_created: 2026-05-27" in r.markdown
        assert "date_updated: 2026-05-27" in r.markdown


# ---------------------------------------------------------------------------
# 3. Section fallback
# ---------------------------------------------------------------------------

class TestSectionFallback:
    def test_missing_section_renders_not_reported(self):
        from renderer import render_summary_from_json
        from prompts import NOT_REPORTED
        payload = _full_payload()
        del payload["sections"]["Mechanistic Insights"]
        r = render_summary_from_json(payload, today_iso="2026-05-27")
        # NOT_REPORTED should appear under Mechanistic Insights.
        idx = r.markdown.index("## Mechanistic Insights")
        next_h = r.markdown.index("## ", idx + 5)
        body = r.markdown[idx:next_h]
        assert NOT_REPORTED in body

    def test_empty_section_text_renders_not_reported(self):
        from renderer import render_summary_from_json
        from prompts import NOT_REPORTED
        payload = _full_payload()
        payload["sections"]["Future Directions"] = {"text": "   "}
        r = render_summary_from_json(payload, today_iso="2026-05-27")
        assert NOT_REPORTED in r.markdown
        # And a warning was logged.
        assert any("Future Directions" in w for w in r.warnings)

    def test_string_section_value_is_accepted(self):
        """Older / sloppier payloads might use a bare string instead of {text}."""
        from renderer import render_summary_from_json
        payload = _full_payload()
        payload["sections"]["Abstract Summary"] = "Bare string body."
        r = render_summary_from_json(payload, today_iso="2026-05-27")
        idx = r.markdown.index("## Abstract Summary")
        assert "Bare string body." in r.markdown[idx:idx + 200]


# ---------------------------------------------------------------------------
# 4. Wikilink canonicalisation
# ---------------------------------------------------------------------------

class _FakeVocab:
    """Minimal stand-in for wiki_vocabulary.VocabularyIndex."""

    def __init__(self, mapping: dict[str, str]):
        self._m = {k.lower(): v for k, v in mapping.items()}

    def find_canonical(self, term: str) -> str | None:
        return self._m.get(term.strip().lower())


class TestWikilinkCanonicalisation:
    def test_resolved_link_gets_aliased_form(self):
        from renderer import render_summary_from_json
        vocab = _FakeVocab({"TaPHS1": "taphs1", "Cas9": "cas9"})
        payload = _full_payload()
        payload["sections"]["Important Entities"] = {
            "text": "We targeted [[TaPHS1]] using [[Cas9]]."
        }
        r = render_summary_from_json(
            payload, vocab_index=vocab, today_iso="2026-05-27",
        )
        # Both display tokens differ in case from their canonical slug,
        # so both get the alias form to preserve display casing.
        assert "[[taphs1|TaPHS1]]" in r.markdown
        assert "[[cas9|Cas9]]" in r.markdown
        assert r.canonicalised == {"TaPHS1": "taphs1", "Cas9": "cas9"}

    def test_link_collapses_when_display_equals_slug(self):
        from renderer import render_summary_from_json
        vocab = _FakeVocab({"cas9": "cas9"})
        payload = _full_payload()
        payload["sections"]["Important Entities"] = {
            "text": "Plain [[cas9]] link with display == slug."
        }
        r = render_summary_from_json(
            payload, vocab_index=vocab, today_iso="2026-05-27",
        )
        # Display IS the slug verbatim → emit bare [[cas9]] not [[cas9|cas9]].
        assert "[[cas9]]" in r.markdown
        assert "[[cas9|cas9]]" not in r.markdown

    def test_unresolved_link_left_as_is_and_recorded(self):
        from renderer import render_summary_from_json
        vocab = _FakeVocab({"Cas9": "cas9"})
        payload = _full_payload()
        payload["sections"]["Important Entities"] = {
            "text": "[[NewGene]] interacts with [[Cas9]]."
        }
        r = render_summary_from_json(
            payload, vocab_index=vocab, today_iso="2026-05-27",
        )
        assert "[[NewGene]]" in r.markdown
        assert "NewGene" in r.new_candidates
        assert "Cas9" not in r.new_candidates

    def test_already_aliased_link_left_alone(self):
        from renderer import render_summary_from_json
        vocab = _FakeVocab({"taphs1": "taphs1"})
        payload = _full_payload()
        payload["sections"]["Important Entities"] = {
            "text": "Pre-aliased [[taphs1|TaPHS1 alt]] should not be rewritten."
        }
        r = render_summary_from_json(
            payload, vocab_index=vocab, today_iso="2026-05-27",
        )
        assert "[[taphs1|TaPHS1 alt]]" in r.markdown

    def test_no_vocab_index_leaves_links_untouched(self):
        from renderer import render_summary_from_json
        payload = _full_payload()
        payload["sections"]["Important Entities"] = {
            "text": "[[Foo]] [[Bar|bar alt]]"
        }
        r = render_summary_from_json(payload, today_iso="2026-05-27")
        assert "[[Foo]]" in r.markdown
        assert "[[Bar|bar alt]]" in r.markdown
        assert r.canonicalised == {}


# ---------------------------------------------------------------------------
# 5. Source PDF footer
# ---------------------------------------------------------------------------

class TestSourceFooter:
    def test_footer_when_paper_name_provided(self):
        from renderer import render_summary_from_json
        r = render_summary_from_json(
            _full_payload(), paper_name="aslam_2026", today_iso="2026-05-27",
        )
        assert "**Source PDF:** `data/aslam_2026.pdf`" in r.markdown

    def test_footer_omitted_when_paper_name_missing(self):
        from renderer import render_summary_from_json
        r = render_summary_from_json(_full_payload(), today_iso="2026-05-27")
        assert "**Source PDF:**" not in r.markdown


# ---------------------------------------------------------------------------
# 6. Task 9 — evidence-quote anchors as Markdown footnotes
# ---------------------------------------------------------------------------

class TestQuoteNormalisation:
    def test_smart_quotes_collapse_to_ascii(self):
        from renderer import _normalise_for_quote_match
        assert _normalise_for_quote_match("\u201cFoo\u201d") == '"foo"'
        assert _normalise_for_quote_match("\u2018Bar\u2019") == "'bar'"

    def test_em_and_en_dashes_collapse_to_hyphen(self):
        from renderer import _normalise_for_quote_match
        assert _normalise_for_quote_match("a\u2014b\u2013c") == "a-b-c"

    def test_soft_hyphens_dropped_and_whitespace_collapsed(self):
        from renderer import _normalise_for_quote_match
        assert _normalise_for_quote_match("po\u00adta\u00adto") == "potato"
        assert _normalise_for_quote_match("a   \n  b") == "a b"

    def test_ligatures_expand(self):
        from renderer import _normalise_for_quote_match
        # U+FB01 = fi (just 2 chars), U+FB03 = ffi (3 chars), U+FB02 = fl.
        assert _normalise_for_quote_match("e\ufb01cient") == "eficient"
        assert _normalise_for_quote_match("e\ufb03cient") == "efficient"
        assert _normalise_for_quote_match("\ufb02ower") == "flower"


class TestQuoteVerification:
    def test_exact_match(self):
        from renderer import _verify_quote_in_source, _normalise_for_quote_match
        src = _normalise_for_quote_match("The QTL had LOD = 12.4 in Yangmai.")
        assert _verify_quote_in_source("had LOD = 12.4", src)

    def test_unicode_source_ascii_quote_matches(self):
        from renderer import _verify_quote_in_source, _normalise_for_quote_match
        # Source uses curly quotes; quote uses ASCII.
        src = _normalise_for_quote_match("\u201cthe QTL\u201d had LOD = 12.4")
        assert _verify_quote_in_source('"the QTL"', src)

    def test_unfound_quote_returns_false(self):
        from renderer import _verify_quote_in_source, _normalise_for_quote_match
        src = _normalise_for_quote_match("only this text exists")
        assert not _verify_quote_in_source("totally absent", src)

    def test_empty_inputs(self):
        from renderer import _verify_quote_in_source
        assert not _verify_quote_in_source("", "abc")
        assert not _verify_quote_in_source("x", "")


def _payload_with_results(results):
    """Build a payload whose Key Results & Data section has the given results."""
    from prompts import required_headers
    return {
        "frontmatter": {"tags": ["t"], "doi": None, "authors": None,
                        "year": None, "journal": None},
        "paper_type": "primary_research",
        "sections": {
            **{h: {"text": f"Body for {h}."} for h in required_headers()},
            "Key Results & Data": {"text": "Major findings:", "results": results},
        },
    }


class TestFootnoteRendering:
    def test_verified_quote_yields_footnote(self):
        from renderer import render_summary_from_json
        src = "We observed LOD = 12.4 on 4A in Yangmai 158."
        r = render_summary_from_json(
            _payload_with_results([
                {"claim": "QTL on 4A with LOD 12.4",
                 "evidence_quote": "LOD = 12.4 on 4A",
                 "source_locator": "p.4, Methods"},
            ]),
            source_text=src, today_iso="2026-05-27",
        )
        # Footnote ref + definition.
        assert "- QTL on 4A with LOD 12.4.[^key-results-data-1]" in r.markdown
        assert ('[^key-results-data-1]: "LOD = 12.4 on 4A" — p.4, Methods'
                in r.markdown)

    def test_unverified_quote_drops_footnote_and_warns(self):
        from renderer import render_summary_from_json
        src = "Source text with no overlap."
        r = render_summary_from_json(
            _payload_with_results([
                {"claim": "Bogus claim",
                 "evidence_quote": "this is nowhere in the source"},
            ]),
            source_text=src, today_iso="2026-05-27",
        )
        # Bullet still appears, but with no footnote anchor.
        assert "- Bogus claim." in r.markdown
        assert "[^" not in r.markdown.split("## Key Results & Data", 1)[1]\
            .split("## ", 1)[0], "no footnote anchors should appear"
        # Warning logged.
        assert any("evidence quote not found" in w for w in r.warnings)

    def test_footnote_ids_are_section_scoped(self):
        from renderer import render_summary_from_json
        src = "alpha beta gamma"
        # Stuff results into TWO different sections to confirm the IDs
        # don't collide.
        from prompts import required_headers
        sections = {h: {"text": f"Body for {h}."} for h in required_headers()}
        sections["Key Results & Data"] = {
            "text": "K:", "results": [
                {"claim": "Found alpha", "evidence_quote": "alpha"},
            ],
        }
        sections["Mechanistic Insights"] = {
            "text": "M:", "results": [
                {"claim": "Saw beta", "evidence_quote": "beta"},
            ],
        }
        payload = {
            "frontmatter": {"tags": ["t"], "doi": None, "authors": None,
                            "year": None, "journal": None},
            "paper_type": "primary_research",
            "sections": sections,
        }
        from renderer import render_summary_from_json
        r = render_summary_from_json(payload, source_text=src, today_iso="2026-05-27")
        # Distinct section slugs, not [^1] / [^2] colliding.
        assert "[^key-results-data-1]" in r.markdown
        assert "[^mechanistic-insights-1]" in r.markdown

    def test_no_source_text_means_no_footnotes(self):
        """Without source_text, quotes can't be verified, so no footnotes
        are emitted but the bullets still render."""
        from renderer import render_summary_from_json
        r = render_summary_from_json(
            _payload_with_results([
                {"claim": "Some claim", "evidence_quote": "quote"},
            ]),
            source_text=None, today_iso="2026-05-27",
        )
        kr_block = r.markdown.split("## Key Results & Data", 1)[1].split("## ", 1)[0]
        assert "Some claim." in kr_block
        assert "[^" not in kr_block


# ---------------------------------------------------------------------------
# 7. paper_type kwarg in renderer
# ---------------------------------------------------------------------------

class TestRendererPaperTypeAware:
    def test_correction_notice_renders_only_4_sections(self):
        from renderer import render_summary_from_json
        payload = {
            "frontmatter": {"tags": ["correction"], "doi": "10.1/x",
                            "authors": "A", "year": 2025, "journal": "J"},
            "paper_type": "correction_notice",
            "sections": {
                "Title & Metadata": {"text": "Correction to: ..."},
                "Correction Summary": {"text": "Diacritics added."},
                "Original Citation": {"text": "Li, Z. et al. (2024)."},
                "Limitations & Caveats": {"text": "No new data."},
            },
        }
        r = render_summary_from_json(
            payload, paper_type="correction_notice", today_iso="2026-05-27",
        )
        # 4 H2 headings, not 12.
        n = r.markdown.count("\n## ")
        assert n == 4, f"expected 4 sections, got {n}"
        assert "## Correction Summary" in r.markdown
        assert "## Original Citation" in r.markdown
        # 12-section headings that don't apply must NOT appear.
        assert "## Mechanistic Insights" not in r.markdown
        assert "## Future Directions" not in r.markdown

    def test_review_variant_renders_reviewed_literature_heading(self):
        from renderer import render_summary_from_json
        from prompts import headers_for
        sections = {h: {"text": f"x for {h}"} for h in headers_for("review")}
        payload = {
            "frontmatter": {"tags": ["t"], "doi": None, "authors": None,
                            "year": None, "journal": None},
            "paper_type": "review",
            "sections": sections,
        }
        r = render_summary_from_json(
            payload, paper_type="review", today_iso="2026-05-27",
        )
        assert "## Reviewed Literature & Inclusion Criteria" in r.markdown
        # Methods heading is replaced.
        assert "## Methods & Experimental Design" not in r.markdown

    def test_no_paper_type_keeps_12_section_default(self):
        from renderer import render_summary_from_json
        from prompts import required_headers
        payload = {
            "frontmatter": {"tags": ["t"], "doi": None, "authors": None,
                            "year": None, "journal": None},
            "paper_type": "primary_research",
            "sections": {h: {"text": f"x for {h}"} for h in required_headers()},
        }
        r = render_summary_from_json(payload, today_iso="2026-05-27")
        n = r.markdown.count("\n## ")
        assert n == 15
