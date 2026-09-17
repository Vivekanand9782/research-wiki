"""Tests for research_agent.verifier — the retrieval-answer grounding gate.

Fully offline: no LLM, no network. Exercises grounding, citation-existence,
abstention, and the repair-message builder.
"""

import pytest

from research_agent import verifier
from research_agent.verifier import (
    GroundingReport,
    extract_cited_paths,
    verify_answer,
    build_repair_message,
    ABSTENTION,
)


_EVIDENCE = [
    (
        "Observation from wiki_search:\n"
        '[{"path": "sources/uncategorized/zhang_2014.md", '
        '"snippet": "Seed dormancy is controlled by TaPHS1 in wheat."}]'
    ),
    (
        "Observation from read_lines:\n"
        "Seed dormancy is controlled by TaPHS1 in wheat. "
        "The QTL had LOD = 12.4 in the Yangmai population."
    ),
]
_RETRIEVED = {"sources/uncategorized/zhang_2014.md"}


def _all_exist(_canon: str) -> bool:
    return True


# ── extract_cited_paths ────────────────────────────────────────────

def test_extract_cited_paths_variants():
    answer = (
        "Claim one (sources/uncategorized/zhang_2014.md#Key Results). "
        "Claim two [[TaPHS1]] see wiki/entities/taphs1.md. "
        "Concept concepts/seed-dormancy.md and synthesis/overview.md."
    )
    paths = extract_cited_paths(answer)
    assert "sources/uncategorized/zhang_2014.md" in paths
    assert "entities/taphs1.md" in paths          # wiki/ prefix normalised off
    assert "concepts/seed-dormancy.md" in paths
    assert "synthesis/overview.md" in paths
    # #section suffix is not captured as part of the path
    assert all("#" not in p for p in paths)


def test_extract_cited_paths_dedupes():
    answer = "a sources/uncategorized/x.md b sources/uncategorized/x.md"
    assert extract_cited_paths(answer) == ["sources/uncategorized/x.md"]


# ── verify_answer: grounding ───────────────────────────────────────

def test_verify_answer_grounded_and_cited():
    answer = (
        "Seed dormancy is controlled by TaPHS1 in wheat. "
        "The QTL had LOD = 12.4 in the Yangmai population.\n\n"
        "References:\n"
        "- Zhang 2014, sources/uncategorized/zhang_2014.md#Key Results"
    )
    report = verify_answer(
        answer, _EVIDENCE, _RETRIEVED, threshold=0.75, path_exists=_all_exist
    )
    assert report.ok
    assert report.confidence == 1.0
    assert report.invalid_citations == []
    assert not report.evidence_empty


def test_verify_answer_ungrounded_claim_fails():
    answer = (
        "Seed dormancy is controlled by TaPHS1 in wheat. "
        "TaPHS1 also cures every viral disease in maize.\n\n"
        "References:\n- Zhang 2014, sources/uncategorized/zhang_2014.md"
    )
    report = verify_answer(
        answer, _EVIDENCE, _RETRIEVED, threshold=0.75, path_exists=_all_exist
    )
    assert not report.ok
    assert report.confidence < 0.75
    assert any("cures every viral disease" in s for s in report.unsupported)


def test_verify_answer_fabricated_number_fails():
    # Correct words, wrong statistic (LOD 12.4 -> 44.9) — numeric veto trips.
    answer = (
        "The QTL had LOD = 44.9 in the Yangmai population.\n\n"
        "References:\n- Zhang 2014, sources/uncategorized/zhang_2014.md"
    )
    report = verify_answer(
        answer, _EVIDENCE, _RETRIEVED, threshold=0.75, path_exists=_all_exist
    )
    assert not report.ok
    assert report.confidence < 0.75


# ── verify_answer: citation existence / retrieval ──────────────────

def test_verify_answer_uncited_path_never_retrieved():
    answer = (
        "Seed dormancy is controlled by TaPHS1 in wheat.\n\n"
        "References:\n- Fake 2099, sources/uncategorized/never_retrieved.md"
    )
    report = verify_answer(
        answer, _EVIDENCE, _RETRIEVED, threshold=0.75, path_exists=_all_exist
    )
    assert not report.ok
    assert "sources/uncategorized/never_retrieved.md" in report.invalid_citations


def test_verify_answer_cited_path_missing_on_disk():
    answer = (
        "Seed dormancy is controlled by TaPHS1 in wheat.\n\n"
        "References:\n- Zhang 2014, sources/uncategorized/zhang_2014.md"
    )
    report = verify_answer(
        answer, _EVIDENCE, _RETRIEVED, threshold=0.75, path_exists=lambda p: False
    )
    assert not report.ok
    assert "sources/uncategorized/zhang_2014.md" in report.invalid_citations


# ── verify_answer: abstention on empty evidence ────────────────────

def test_verify_answer_empty_evidence_flags():
    answer = "Seed dormancy is controlled by TaPHS1 in wheat."
    report = verify_answer(answer, [], set(), threshold=0.75)
    assert report.evidence_empty
    assert not report.ok


def test_verify_answer_no_factual_sentences_is_ok_when_evidence_present():
    # An answer with no verifiable factual sentences and no citations should
    # not be marked ungrounded purely on grounding (confidence defaults 1.0),
    # but empty evidence still blocks it.
    report = verify_answer("Not reported in this paper.", _EVIDENCE, _RETRIEVED,
                           threshold=0.75, path_exists=_all_exist)
    assert report.ok


# ── build_repair_message ───────────────────────────────────────────

def test_build_repair_message_mentions_problems():
    report = GroundingReport(
        confidence=0.4,
        supported=["ok sentence"],
        unsupported=["a fabricated claim about maize"],
        total=2,
        cited_paths=["sources/uncategorized/x.md"],
        invalid_citations=["sources/uncategorized/x.md"],
        evidence_empty=False,
        ok=False,
    )
    msg = build_repair_message(report)
    assert "fabricated claim about maize" in msg
    assert "sources/uncategorized/x.md" in msg
    assert "corrected JSON answer" in msg


def test_build_repair_message_empty_evidence_suggests_abstention():
    report = GroundingReport(0.0, [], [], 0, [], [], evidence_empty=True, ok=False)
    msg = build_repair_message(report)
    assert ABSTENTION in msg
