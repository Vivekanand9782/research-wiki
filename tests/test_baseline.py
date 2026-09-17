"""Baseline scoring of the 5 representative golden summaries.

This is a *reporting harness*, not a hard gate — it prints today's
strict/lenient pass rate and SummaryValidator score for each golden
snapshot so the team can see numerically where the existing corpus
stands. It will start failing as a gate only once Tasks 2/3/7 land and
we have a clear acceptance threshold per paper type.

Today's expected behaviour (May 2026, before the prompt overhaul):

* All 5 snapshots pass the *lenient* validator (5/5).
* aslam_2026 (gold) passes the *strict* validator with a high score.
* franke_2001 (metadata-only fallback) passes lenient but has a low
  SummaryValidator score because every section is "Not reported in this
  paper.".
* li_2025 (correction) passes lenient but the SummaryValidator score is
  middling because Methods/Mechanisms/Future Directions are empty.
* bi_2014 / liton_2020 (typical primary research) should pass both.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = Path(__file__).resolve().parent / "golden"


GOLDEN_SAMPLES: list[tuple[str, str]] = [
    ("aslam_2026 (gold)",        "aslam_2026_crispr_mediated_engineering.md"),
    ("franke_2001 (metadata)",   "franke_2001_modified_lignin_tobacco.md"),
    ("li_2025 (correction)",     "li_2025_correction_heat_shock.md"),
    ("bi_2014 (primary)",        "bi_2014_characterization_dfr_allelic.md"),
    ("liton_2020 (primary)",     "liton_2020_identification_loci_preharvest.md"),
]


@pytest.fixture(scope="module", autouse=True)
def _stub_genai_dependencies():
    """Same stub-and-evict pattern as test_prompts_contract.py."""
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

    sys.path.insert(0, str(ROOT))
    for name in ("genai_client", "prompts", "validation"):
        sys.modules.pop(name, None)
    yield


def test_golden_directory_present():
    assert GOLDEN.is_dir(), f"missing golden corpus at {GOLDEN}"
    found = {p.name for p in GOLDEN.glob("*.md")}
    expected = {fn for _, fn in GOLDEN_SAMPLES}
    missing = expected - found
    assert not missing, f"missing golden files: {sorted(missing)}"


def test_baseline_score_table(capsys):
    """Print the baseline score table. Always passes — this is the bar
    we want subsequent tasks to *raise*.
    """
    from genai_client import (
        validate_structured_summary,
        validate_structured_summary_strict,
    )
    from prompts import lint_summary

    rows = []
    for label, fname in GOLDEN_SAMPLES:
        text = (GOLDEN / fname).read_text(encoding="utf-8")
        lenient = validate_structured_summary(text)
        strict = validate_structured_summary_strict(text)
        report = lint_summary(text)
        rows.append({
            "label": label,
            "size_kb": round(len(text) / 1024, 2),
            "lenient_pass": lenient["valid"],
            "strict_pass": strict["valid"],
            "score": report.score,
            "wikilinks": report.wikilink_count,
            "missing_strict": len(strict["missing_sections"]),
        })

    # Compose a fixed-width table.
    header = (
        f"{'paper':<28} "
        f"{'size':>7} "
        f"{'lenient':>8} "
        f"{'strict':>7} "
        f"{'score':>6} "
        f"{'wikilinks':>10} "
        f"{'miss(strict)':>13}"
    )
    sep = "-" * len(header)
    print()
    print(sep)
    print(header)
    print(sep)
    for r in rows:
        print(
            f"{r['label']:<28} "
            f"{r['size_kb']:>5} KB "
            f"{('PASS' if r['lenient_pass'] else 'FAIL'):>8} "
            f"{('PASS' if r['strict_pass'] else 'FAIL'):>7} "
            f"{r['score']:>6.1f} "
            f"{r['wikilinks']:>10} "
            f"{r['missing_strict']:>13}"
        )
    print(sep)
    print(
        f"lenient pass: {sum(r['lenient_pass'] for r in rows)}/{len(rows)} | "
        f"strict pass: {sum(r['strict_pass'] for r in rows)}/{len(rows)}"
    )
    print(sep)

    # Sanity gates that must hold today. Don't tighten without bumping
    # FORMAT_VERSION — these are documenting "where we are", not where we
    # want to be.
    assert all(r["lenient_pass"] for r in rows), (
        "Existing on-disk summaries should all pass the lenient validator. "
        "If this regresses, the lenient regex was tightened too aggressively."
    )

    # Print the captured output even when pytest is in capture mode so
    # the team sees the table when running locally.
    captured = capsys.readouterr()
    sys.stdout.write(captured.out)


def test_aslam_is_the_strongest_in_corpus():
    """The gold-standard counterexample should outscore the metadata-only
    failure mode by a wide margin. If this gap closes, our baseline is
    miscalibrated."""
    from prompts import lint_summary

    aslam = lint_summary((GOLDEN / "aslam_2026_crispr_mediated_engineering.md").read_text())
    franke = lint_summary((GOLDEN / "franke_2001_modified_lignin_tobacco.md").read_text())

    assert aslam.score > franke.score, (
        f"aslam ({aslam.score}) should outscore franke ({franke.score})"
    )
    assert aslam.wikilink_count > franke.wikilink_count
    # franke is metadata-only fallback, so its wikilink count should be
    # essentially zero. If this jumps, something has back-filled it.
    assert franke.wikilink_count <= 3
