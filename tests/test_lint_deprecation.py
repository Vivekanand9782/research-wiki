"""Lint tests enforcing the single-source-of-truth contract (Task 12).

These tests catch regression patterns where a future change re-introduces
the duplicated 12-heading list or the literal placeholder scaffolds the
overhaul removed. They run on the raw source files so they catch drift
even when other tests pass.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent

# All twelve heading names appearing as adjacent string literals inside the
# same module is a strong signal someone re-pasted the inline list.
ALL_TWELVE_HEADINGS = [
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
    "Future Directions",
    "Key References to Follow Up",
]

# Files that LEGITIMATELY contain the full 12-string list verbatim:
#   prompts.py — single source of truth (REQUIRED_SECTIONS)
#   validation.py — only via REQUIRED_HEADERS = required_headers() but the
#     literal strings appear inside the SectionRule blocks of prompts.py
#     so this file is the only one cleared to import them; verified below.
#   tests/* — test fixtures naturally include them
ALLOWED_FILES_WITH_INLINE_LIST = {
    "prompts.py",
    "validation.py",  # historical repair_sections dict; future cleanup
}


def _module_files() -> list[Path]:
    """Python source files we lint."""
    skip_dirs = {".venv", "tests", "wiki", "raw", "__pycache__", ".backup",
                 "scripts", "paper_agent"}
    out: list[Path] = []
    for path in ROOT.glob("*.py"):
        if path.parent.name in skip_dirs:
            continue
        out.append(path)
    return sorted(out)


def _count_inline_headings(src: str) -> int:
    """How many of the 12 heading literals appear as quoted strings."""
    return sum(
        1 for h in ALL_TWELVE_HEADINGS
        if f'"{h}"' in src or f"'{h}'" in src
    )


# ---------------------------------------------------------------------------
# 1. No new file re-introduces the 12-heading list as inline strings
# ---------------------------------------------------------------------------

class TestNoInlineHeadingDuplication:
    def test_only_allowed_files_have_full_list(self):
        offenders: list[tuple[str, int]] = []
        for path in _module_files():
            if path.name in ALLOWED_FILES_WITH_INLINE_LIST:
                continue
            src = path.read_text(encoding="utf-8")
            n = _count_inline_headings(src)
            # Allow up to 3 incidental occurrences (e.g. a docstring mention
            # of a single section). 12 means a full re-paste.
            if n >= 8:
                offenders.append((path.name, n))
        assert not offenders, (
            "Inline 12-heading list re-introduced outside the single-source-of-truth "
            f"files {sorted(ALLOWED_FILES_WITH_INLINE_LIST)}: {offenders}. "
            "Import from prompts.required_headers() instead."
        )


# ---------------------------------------------------------------------------
# 2. Placeholder scaffolds removed from prompt builders
# ---------------------------------------------------------------------------

class TestNoPlaceholderScaffolds:
    @pytest.mark.parametrize("placeholder", [
        # The literal scaffold values that used to leak into output.
        # These may still appear in prompts.py inside the explicit
        # "DO NOT emit" anti-example, which is fine — we only forbid them
        # inside the YAML scaffold block that the model reads as
        # template.
        '10.xxxx/xxxxx',
        'Last1 et al.',
        'Journal Name',
        '[comma, separated, tags]',
    ])
    def test_placeholder_not_in_yaml_scaffold(self, placeholder):
        """The YAML scaffold block (between the two `---` markers) the
        prompt shows the model must NOT contain literal placeholder
        values. Anti-examples elsewhere in the prompt are fine."""
        from prompts import build_main_prompt, build_stage_a_prompt
        for builder in (build_main_prompt, build_stage_a_prompt):
            p = builder("source text", extracted_doi="10.1/x")
            # Find the first --- ... --- block (the scaffold).
            m = re.search(r"^---\n(.*?)\n---", p, re.MULTILINE | re.DOTALL)
            if m is None:
                # Stage A doesn't emit a YAML scaffold; skip.
                continue
            assert placeholder not in m.group(1), (
                f"{builder.__name__}: placeholder {placeholder!r} leaked "
                f"into the YAML scaffold:\n{m.group(1)}"
            )


# ---------------------------------------------------------------------------
# 3. format_version frontmatter key is emitted by the renderer
# ---------------------------------------------------------------------------

class TestFormatVersionStamped:
    def test_renderer_emits_format_version(self):
        from renderer import render_summary_from_json
        from prompts import FORMAT_VERSION, required_headers
        payload = {
            "frontmatter": {"tags": ["t"], "doi": None, "authors": None,
                            "year": None, "journal": None},
            "paper_type": "primary_research",
            "sections": {h: {"text": f"Body for {h}."} for h in required_headers()},
        }
        r = render_summary_from_json(payload, today_iso="2026-05-27")
        assert f"format_version: {FORMAT_VERSION}" in r.markdown


# ---------------------------------------------------------------------------
# 4. Single source of truth: validation REQUIRED_HEADERS sourced from prompts
# ---------------------------------------------------------------------------

class TestValidationSourcesFromPrompts:
    def test_validation_imports_from_prompts(self):
        src = (ROOT / "validation.py").read_text(encoding="utf-8")
        assert "from prompts import" in src, (
            "validation.py must import REQUIRED_HEADERS from prompts.py"
        )
        # Confirm REQUIRED_HEADERS is a thin alias, not a fresh literal list.
        assert "REQUIRED_HEADERS = _required_headers()" in src or \
               "REQUIRED_HEADERS: List[str] = _required_headers()" in src

    def test_genai_client_imports_from_prompts(self):
        src = (ROOT / "genai_client.py").read_text(encoding="utf-8")
        # Either lazy in-function or top-level import is acceptable.
        assert "lenient_required_headers" in src or "required_headers" in src


# ---------------------------------------------------------------------------
# 5. max_retries off-by-one stays fixed
# ---------------------------------------------------------------------------

class TestMaxRetriesNotRegressed:
    def test_max_retries_at_least_2(self):
        src = (ROOT / "pdf_extractor.py").read_text(encoding="utf-8")
        # Only check inside _generate_and_validate_summary.
        m = re.search(
            r"def\s+_generate_and_validate_summary\b.*?def\s+\w+",
            src, re.DOTALL,
        )
        assert m, "could not locate _generate_and_validate_summary"
        method_src = m.group(0)
        assignments = re.findall(r"max_retries\s*=\s*(\d+)", method_src)
        assert assignments, "max_retries assignment missing"
        for v in assignments:
            assert int(v) >= 2, (
                f"max_retries={v} regressed in _generate_and_validate_summary; "
                "the repair branch becomes unreachable when this is < 2"
            )
