"""Regression test for the `max_retries` off-by-one bug.

Before Task 2.5 of the ingestion-prompt overhaul plan,
`pdf_extractor._generate_and_validate_summary` set `max_retries = 1` and
iterated with `for attempt in range(max_retries)`, which only yields
`attempt = 0`. The `else: structured_summary = self.repair_paper_summary(...)`
branch was therefore unreachable — the repair pass never ran, despite
the docstring claiming "one main call + at most one repair pass".

Setting `max_retries = 2` makes the repair branch reachable. This test
locks the new behaviour: when the first generator call returns an
incomplete summary, repair is called exactly once, and the result of
the repair call is what the orchestrator returns.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent


def _import_pdf_extractor_with_stubs():
    """Mirrors the stub-and-reload pattern from test_pdf_extractor.py so
    importing pdf_extractor.py doesn't require Vertex / opendataloader.
    """
    fake_config = types.ModuleType("config")
    fake_config.AI_MODEL = "gpt-oss-120b"
    fake_config.FILTER_MODEL = "gpt-oss-120b"
    fake_config.VISION_MODEL = "gpt-oss-120b"
    fake_config.HALLUCINATION_CONFIDENCE_THRESHOLD = 0.90
    fake_config.MAX_HALLUCINATION_REPAIR_RETRIES = 2
    sys.modules["config"] = fake_config

    # genai_client stub: lazily-imported `validate_structured_summary` is
    # called by `_generate_and_validate_summary`, so we provide a real
    # implementation that delegates to `prompts.lenient_required_headers()`.
    fake_genai = types.ModuleType("genai_client")
    fake_genai.genai_client = None
    fake_genai.get_ai_response = lambda *a, **kw: "stub"
    fake_genai.get_embeddings = lambda *a, **kw: []
    fake_genai.generate_content_with_retry = (
        lambda **kw: types.SimpleNamespace(text="{}")
    )

    def _validate(text: str, paper_type=None) -> dict:
        # Use the same lenient regex genai_client has now. Importing the
        # real one is fine because prompts.py has no third-party deps.
        sys.path.insert(0, str(ROOT))
        from prompts import lenient_required_headers
        import re
        missing = []
        for name in lenient_required_headers():
            pattern = rf"(?im)(?:^|\n)\s*##?\s*{re.escape(name)}\s*$"
            if re.search(pattern, text) is None:
                missing.append(name)
        return {"valid": not missing, "missing_sections": missing}

    fake_genai.validate_structured_summary = _validate
    sys.modules["genai_client"] = fake_genai

    spec = importlib.util.spec_from_file_location(
        "pdf_extractor", ROOT / "pdf_extractor.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_summary(headings: list[str]) -> str:
    """Synthesize a valid-looking summary with the given headings."""
    return "\n".join(f"## {h}\nContent.\n" for h in headings)


@pytest.fixture
def extractor():
    """A bare ResearchPaperExtractor with a fake logger."""
    pdf = _import_pdf_extractor_with_stubs()
    e = pdf.ResearchPaperExtractor.__new__(pdf.ResearchPaperExtractor)

    class _Logger:
        def __init__(self):
            self.events: list = []

        def log_summary_validation(self, **kw):
            self.events.append(("validation", kw))

        def log_error(self, msg):
            self.events.append(("error", msg))

    e.logger = _Logger()
    return e


def test_repair_runs_when_first_call_is_incomplete(extractor):
    """Stub generate to return only the lenient 5; stub repair to return all 12.
    The repair branch must actually fire and the final summary must validate.
    """
    from prompts import lenient_required_headers, required_headers

    incomplete = _make_summary(lenient_required_headers())  # only 5 headings
    complete = _make_summary(required_headers())            # all 12

    calls: list[str] = []

    def fake_generate(self, full_text, pdf_name, extracted_doi=None, **kwargs):
        calls.append("generate")
        # Return a summary that fails the *lenient* validator on purpose:
        # only Title & Metadata, missing the other lenient sections so
        # repair is forced to run.
        return _make_summary(["Title & Metadata"])

    def fake_repair(self, full_text, draft, missing, pdf_name, extracted_doi=None, **kwargs):
        calls.append("repair")
        return complete

    extractor.generate_paper_summary = fake_generate.__get__(extractor)
    extractor.repair_paper_summary = fake_repair.__get__(extractor)

    result = extractor._generate_and_validate_summary(
        full_raw_text="raw text",
        pdf_name="test_paper",
    )

    assert calls == ["generate", "repair"], (
        f"expected exactly one generate + one repair, got {calls}"
    )
    assert result == complete


def test_no_repair_when_first_call_is_complete(extractor):
    """If the first call already passes, repair should not run."""
    from prompts import required_headers

    complete = _make_summary(required_headers())

    calls: list[str] = []

    def fake_generate(self, full_text, pdf_name, extracted_doi=None, **kwargs):
        calls.append("generate")
        return complete

    def fake_repair(self, full_text, draft, missing, pdf_name, extracted_doi=None, **kwargs):
        calls.append("repair")
        raise AssertionError("repair should not run when first call validates")

    extractor.generate_paper_summary = fake_generate.__get__(extractor)
    extractor.repair_paper_summary = fake_repair.__get__(extractor)

    result = extractor._generate_and_validate_summary(
        full_raw_text="raw text",
        pdf_name="test_paper",
    )

    assert calls == ["generate"]
    assert result == complete


def test_max_retries_is_at_least_2():
    """Read the source to confirm we didn't regress to 1."""
    src = (ROOT / "pdf_extractor.py").read_text(encoding="utf-8")
    # Find the line in _generate_and_validate_summary.
    import re
    in_method = False
    found_value: int | None = None
    for line in src.splitlines():
        if "def _generate_and_validate_summary" in line:
            in_method = True
            continue
        if in_method:
            m = re.match(r"\s*max_retries\s*=\s*(\d+)", line)
            if m:
                found_value = int(m.group(1))
                break
            if line.startswith("    def ") and "_generate_and_validate_summary" not in line:
                break  # left the method without finding it
    assert found_value is not None, "could not find max_retries assignment"
    assert found_value >= 2, (
        f"max_retries={found_value} regressed; the repair branch needs >= 2 "
        "to be reachable"
    )


def test_two_stage_invalid_output_falls_back_to_legacy(extractor, monkeypatch):
    """A malformed Stage B document must not be marked successful."""
    from prompts import required_headers

    config = sys.modules["config"]
    config.USE_TWO_STAGE_EXTRACTION = True
    malformed = _make_summary(required_headers())  # headings but no source envelope
    complete = (
        "---\ntags: [test]\ntype: source\ndate_created: 2026-07-29\n"
        "date_updated: 2026-07-29\nsource_count: 1\n---\n\n"
        + _make_summary(required_headers())
    )
    calls = []

    def fake_two_stage(*args, **kwargs):
        calls.append("two-stage")
        raise RuntimeError("Stage B output validation failed: YAML frontmatter")

    def fake_generate(*args, **kwargs):
        calls.append("legacy")
        return complete

    extractor._generate_via_two_stage = fake_two_stage
    extractor.generate_paper_summary = fake_generate
    extractor.repair_paper_summary = lambda *a, **k: complete

    result = extractor._generate_and_validate_summary("raw text", "paper")
    assert calls == ["two-stage", "legacy"]
    assert result == complete


def test_legacy_output_still_invalid_after_repair_raises(extractor):
    """Never proceed to disk after both structural attempts fail."""
    invalid = _make_summary(["Title & Metadata"])
    extractor.generate_paper_summary = lambda *a, **k: invalid
    extractor.repair_paper_summary = lambda *a, **k: invalid

    with pytest.raises(RuntimeError, match="validation failed"):
        extractor._generate_and_validate_summary("raw text", "paper")
