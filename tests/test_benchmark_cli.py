"""Smoke test for benchmarks/run_two_stage.py (Task 11 final deliverable)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _evict_modules():
    """Ensure modules are re-imported fresh so the benchmark uses the
    real prompts/wiki_vocabulary, not stubs other tests left behind."""
    for name in ("prompts", "validation", "genai_client", "renderer",
                 "wiki_vocabulary", "paper_classifier",
                 "benchmarks", "benchmarks.score", "benchmarks.run_two_stage"):
        sys.modules.pop(name, None)
    yield


@pytest.mark.skipif(
    not (ROOT / "wiki" / "sources" / "uncategorized").is_dir(),
    reason="live wiki not present",
)
class TestBenchmarkCLI:
    def test_dry_run_writes_a_report(self, tmp_path):
        from benchmarks.run_two_stage import main as run_main

        out = tmp_path / "report.md"
        # Tiny strata so the test stays fast.
        rc = run_main([
            "--dry-run", "--sample", "3",
            "--strata", '{"correction_notice": 1, "primary_research": 1, "review": 1}',
            "--out", str(out),
        ])
        assert rc == 0
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# Two-stage extraction A/B benchmark" in content
        assert "## Stratification" in content
        assert "## Dry-run scoring (no LLM calls)" in content
        # The table header should be present.
        assert "| paper |" in content

    def test_live_mode_returns_nonzero_until_implemented(self, tmp_path):
        from benchmarks.run_two_stage import main as run_main

        out = tmp_path / "report.md"
        rc = run_main([
            "--live", "--sample", "3",
            "--strata", '{"primary_research": 1}',
            "--out", str(out),
        ])
        # Live mode is intentionally a stub — it returns 1 and doesn't
        # write a report so the user knows API calls weren't made.
        assert rc == 1
