"""Regression tests for the PDF-extractor seed-page generator and its
safety helpers.

These tests document and lock down the invariants we discovered during the
May 2026 cleanup session:

  1. Schema-clean seed pages are produced for both fresh creation and
     subsequent merges.
  2. Generator output is byte-identical to ``cleanup_page`` output for
     equivalent inputs (so historical pages and new pages stay in sync).
  3. LLM responses that look like failure text ("AI Error: ...", refusal
     patterns, empty body) are treated as failures even when no exception
     was raised.
  4. ``validate_seed_page_content`` accepts schema-clean pages and rejects
     missing-section / wrong-heading drift.
  5. ``validate_ai_model_name`` flags typos in ``config.AI_MODEL`` so a
     silent fallback to a different backend is loud.

Run with::

    python3 -m pytest tests/test_pdf_extractor.py -v

or directly::

    python3 tests/test_pdf_extractor.py
"""
from __future__ import annotations

import importlib.util
import re
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


# ─────────────────────────────────────────────────────────────────────────────
# Minimal-stub import of pdf_extractor — the real module pulls in
# ``google.genai`` and ``opendataloader_pdf`` which aren't useful for unit
# tests. We stub them and reload so the test suite is hermetic.
# ─────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent


def _import_pdf_extractor():
    fake_config = types.ModuleType("config")
    fake_config.FILTER_MODEL = "gpt-oss-120b"
    fake_config.AI_MODEL = "gpt-oss-120b"
    sys.modules["config"] = fake_config

    fake_genai = types.ModuleType("genai_client")
    fake_genai.genai_client = None
    fake_genai.get_ai_response = lambda *a, **kw: "stub"
    fake_genai.get_embeddings = lambda *a, **kw: []
    fake_genai.generate_content_with_retry = (
        lambda **kw: types.SimpleNamespace(text="{}")
    )
    sys.modules["genai_client"] = fake_genai

    spec = importlib.util.spec_from_file_location(
        "pdf_extractor", ROOT / "pdf_extractor.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PDF = _import_pdf_extractor()
E = PDF.ResearchPaperExtractor

# Real paper stems so the cleanup_page comparison test passes its
# SOURCE_STEMS check.
SEED_PAPER = "Vu_2023_Prime_Editing_Mechanism_Applications_Plant"
NEW_PAPER = "Molla_2021_Base_Prime_Editing_Plants"


class FreshSeedPageTests(unittest.TestCase):
    """`_render_seed_page` produces a schema-clean page."""

    def test_schema_clean(self):
        page = E._render_seed_page(
            name="ZmTCP7", category="Entity",
            summary_text="ZmTCP7 is a transcription factor.",
            sources=[SEED_PAPER], today_iso="2026-05-25",
        )
        # Every required schema element present.
        self.assertIn("**Summary**:", page)
        self.assertIn("**Sources**:", page)
        self.assertIn("**Last updated**:", page)
        self.assertIn("## Related pages", page)
        # And no forbidden duplicates.
        self.assertNotRegex(page, r"^##\s+Sources\s*$")
        # Frontmatter is well-formed.
        self.assertTrue(page.startswith("---\n"))
        self.assertGreater(page.find("\n---\n"), 0)


class MergeFindingTests(unittest.TestCase):
    """`_merge_finding_into_page` updates frontmatter, **Sources**, **Last
    updated**, and inserts the finding before ## Related pages."""

    EXISTING = (
        "---\n"
        "tags: [entity]\n"
        "type: entity\n"
        "date_created: 2024-01-01\n"
        "date_updated: 2024-01-01\n"
        "source_count: 1\n"
        "---\n"
        "\n"
        "# ZmTCP7\n"
        "\n"
        "**Summary**:\n"
        "ZmTCP7 is a transcription factor.\n"
        "\n"
        "**Sources**:\n"
        f"- [[{SEED_PAPER}]]\n"
        "\n"
        "**Last updated**: 2024-01-01\n"
        "\n"
        "---\n"
        "## Related pages\n"
        "- [[zma-mirna319]]\n"
    )

    def test_full_merge(self):
        merged = E._merge_finding_into_page(
            self.EXISTING,
            pdf_name=NEW_PAPER,
            finding_text="Activates AGPase via direct binding.",
            today_iso="2026-05-25",
        )
        # Sources extended (old + new), no duplicate ## Sources heading.
        self.assertIn(f"- [[{SEED_PAPER}]]", merged)
        self.assertIn(f"- [[{NEW_PAPER}]]", merged)
        self.assertNotRegex(merged, r"(?m)^##\s+Sources\s*$")
        # Frontmatter source_count bumped, dates updated.
        self.assertIn("source_count: 2", merged)
        self.assertIn("date_updated: 2026-05-25", merged)
        # Body **Last updated** also bumped.
        self.assertIn("**Last updated**: 2026-05-25", merged)
        # Findings section present.
        self.assertIn(f"### Findings from [[{NEW_PAPER}]]", merged)
        # No triple newlines.
        self.assertNotRegex(merged, r"\n\n\n")

    def test_safety_helper_validates_merged_output(self):
        merged = E._merge_finding_into_page(
            self.EXISTING,
            pdf_name=NEW_PAPER,
            finding_text="Activates AGPase via direct binding.",
            today_iso="2026-05-25",
        )
        self.assertEqual(PDF.validate_seed_page_content(merged), [])

    def test_empty_finding_records_source_without_block(self):
        # Thin/stub snippet → finding_text=None: source recorded, no noise block.
        merged = E._merge_finding_into_page(
            self.EXISTING,
            pdf_name=NEW_PAPER,
            finding_text=None,
            today_iso="2026-05-25",
        )
        self.assertIn(f"- [[{NEW_PAPER}]]", merged)
        self.assertIn("source_count: 2", merged)
        self.assertNotIn(f"### Findings from [[{NEW_PAPER}]]", merged)


class NodeContextTests(unittest.TestCase):
    """`_node_context` keeps entities discussed in prose, drops list-only ones."""

    SUMMARY = (
        "## Key Results & Data\n"
        "[[ZmMYB31]] directly represses maize lignin biosynthesis genes.\n"
        "\n"
        "## Important Entities\n"
        "[[ZmMYB31]], [[ZmMYB42]], [[PAL]], [[C4H]]\n"
    )

    def test_discussed_entity_kept_with_context(self):
        ctx = E._node_context("ZmMYB31", self.SUMMARY)
        self.assertTrue(ctx)
        self.assertIn("represses", ctx)

    def test_list_only_entity_skipped(self):
        # PAL appears only in the bare entity list → no substantive context.
        self.assertEqual(E._node_context("PAL", self.SUMMARY), "")


class GeneratorEquivalenceTest(unittest.TestCase):
    """Generator output for a fresh page + first finding must be byte-equal
    to ``cleanup_page`` output for the equivalent buggy input. Locks in the
    invariant we established when re-anchoring the regex in
    ``_merge_finding_into_page``."""

    def test_byte_equal_to_cleanup(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from cleanup_wrong_sources import cleanup_page  # noqa: E402

        seed = E._render_seed_page(
            name="Foo", category="Concept",
            summary_text="Foo is a thing.",
            sources=[SEED_PAPER], today_iso="2026-05-25",
        )
        gen = E._merge_finding_into_page(
            seed,
            pdf_name=NEW_PAPER,
            finding_text="According to the paper, Foo behaves differently.",
            today_iso="2026-05-25",
        )
        buggy = (
            "---\n"
            "tags: [concept]\n"
            "type: concept\n"
            "date_created: 2026-05-25\n"
            "date_updated: 2026-05-25\n"
            "source_count: 1\n"
            "---\n"
            "\n"
            "# Foo\n"
            "\n"
            "**Summary**:\n"
            "Foo is a thing.\n"
            "\n"
            "**Sources**:\n"
            f"- [[{SEED_PAPER}]]\n"
            "\n"
            "**Last updated**: 2026-05-25\n"
            "\n"
            "---\n"
            "## Related pages\n"
            "\n"
            f"### Findings from [[{NEW_PAPER}]]\n"
            "According to the paper, Foo behaves differently.\n"
            "\n"
            "## Sources\n"
            f"- [[{NEW_PAPER}]]\n"
        )
        cleaned, _ = cleanup_page(buggy, today_iso="2026-05-25")
        self.assertEqual(gen, cleaned)


class LLMFailureTextTests(unittest.TestCase):
    """`is_llm_failure_text` catches LLM responses that no exception
    flagged but are still bad. This is what made `t-zeatin.md` get
    persisted as ``AI Error: ...`` — we never want to write that again."""

    def test_known_failure_strings(self):
        for s in [
            "AI Error: [Errno 8] nodename nor servname provided",
            "[Errno 8] something",
            "Error: too many requests",
            "I cannot help with that.",
            "I'm sorry, I cannot do that.",
            "Sorry, I do not have access to that.",
            "As an AI language model, I cannot",
            "",
            "   ",
            None,
        ]:
            with self.subTest(s=s):
                self.assertTrue(
                    PDF.is_llm_failure_text(s),
                    f"should flag {s!r} as failure text",
                )

    def test_legitimate_responses(self):
        for s in [
            "ZmTCP7 is a maize transcription factor that regulates AGPase.",
            "The compound is found in many plants and modulates growth.",
            "Foo and bar interact under drought stress conditions.",
        ]:
            with self.subTest(s=s):
                self.assertFalse(
                    PDF.is_llm_failure_text(s),
                    f"should NOT flag {s!r}",
                )


class SeedContentValidationTests(unittest.TestCase):
    GOOD = (
        "---\n"
        "tags: [concept]\n"
        "type: concept\n"
        "date_created: 2026-05-25\n"
        "date_updated: 2026-05-25\n"
        "source_count: 1\n"
        "---\n"
        "\n"
        "# Foo\n"
        "\n"
        "**Summary**:\n"
        "Foo is a thing.\n"
        "\n"
        "**Sources**:\n"
        "- [[paper]]\n"
        "\n"
        "**Last updated**: 2026-05-25\n"
        "\n"
        "---\n"
        "## Related pages\n"
    )

    def test_accepts_clean_page(self):
        self.assertEqual(PDF.validate_seed_page_content(self.GOOD), [])

    def test_rejects_missing_frontmatter(self):
        no_fm = self.GOOD[self.GOOD.find("# Foo"):]
        errs = PDF.validate_seed_page_content(no_fm)
        self.assertTrue(any("frontmatter" in e for e in errs))

    def test_rejects_each_missing_section(self):
        for section in ("**Summary**:", "**Sources**:", "**Last updated**:",
                        "## Related pages"):
            with self.subTest(section=section):
                broken = self.GOOD.replace(section, "_REMOVED_")
                errs = PDF.validate_seed_page_content(broken)
                self.assertTrue(
                    any(section in e for e in errs),
                    f"should flag missing {section}: got {errs}",
                )

    def test_rejects_h2_sources_heading(self):
        bad = self.GOOD + "\n## Sources\n- [[paper2]]\n"
        errs = PDF.validate_seed_page_content(bad)
        self.assertTrue(any("## Sources" in e for e in errs))


class ConfigValidationTests(unittest.TestCase):
    def test_recognised_models(self):
        for m in ("gpt-oss-120b", "minimax-m2.7"):
            with self.subTest(m=m):
                ok, _ = PDF.validate_ai_model_name(m)
                self.assertTrue(ok)

    def test_rejects_typos_and_empty(self):
        for m in ("gemini-2.5-flash", "gptoss-120b", "GPT-4", "", None):
            with self.subTest(m=m):
                ok, _ = PDF.validate_ai_model_name(m)
                self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()


class RuntimeOptimizationTests(unittest.TestCase):
    def test_node_lock_is_shared_across_extractor_instances(self):
        first = E.__new__(E)
        second = E.__new__(E)
        path = ROOT / "wiki" / "concepts" / "shared-lock-test.md"
        self.assertIs(first._get_node_lock(path), second._get_node_lock(path))

    def test_process_single_pdf_does_not_load_unused_pdf_bytes(self):
        class Logger:
            def __init__(self):
                self.current_paper = {}

            def start_paper(self, _path):
                self.current_paper = {}

            def finish_paper(self):
                return None

            def log_error(self, _message):
                return None

        with TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "paper.pdf"
            pdf_path.write_bytes(b"%PDF placeholder")

            extractor = E.__new__(E)
            extractor.base_dir = root
            extractor.pdf_folder = root
            extractor.output_folder = root / "wiki" / "sources"
            extractor.text_folder = root / "raw" / "papers"
            extractor.logger = Logger()
            extractor.output_folder.mkdir(parents=True)
            extractor.text_folder.mkdir(parents=True)

            def forbidden_load(_path):
                raise AssertionError("full PDF bytes should not be loaded")

            seen = {}

            def fake_extract(self, source, pdf_part, text_path):
                seen["pdf_part"] = pdf_part
                seen["text_path"] = text_path
                return "Extracted source text without a DOI. " * 10

            def fake_summary(self, full_text, pdf_name, extracted_doi=None,
                             api_metadata=None):
                seen["summary_called"] = True
                return (
                    "---\ntags: [test]\ntype: source\n"
                    "date_created: 2026-07-29\ndate_updated: 2026-07-29\n"
                    "source_count: 1\n---\n\n"
                    "## Title & Metadata\nSource-grounded title.\n\n"
                    "## Abstract Summary\nSource-grounded summary.\n"
                )

            extractor._load_pdf_part = forbidden_load
            extractor._extract_raw_text = types.MethodType(fake_extract, extractor)
            extractor._generate_and_validate_summary = types.MethodType(
                fake_summary, extractor
            )
            extractor.populate_wiki_nodes = lambda *_args, **_kwargs: None

            result = extractor.process_single_pdf(
                pdf_path, "uncategorized", skip_summary=False
            )
            expected_text = (
                extractor.text_folder / "uncategorized" / "paper.md"
            )
            self.assertEqual(result["extraction_method"], "datalab_general_compute")
            self.assertIsNone(seen["pdf_part"])
            self.assertEqual(seen["text_path"], expected_text)
            self.assertTrue(seen["summary_called"])
            # The `<paper>_data_objects.json` sidecar was removed; nothing in
            # the pipeline should recreate it.
            self.assertEqual(
                sorted(p.name for p in
                       (extractor.text_folder / "uncategorized").glob("*_data_objects.json")),
                [],
            )
