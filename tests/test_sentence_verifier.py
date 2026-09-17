"""Tests for sentence_verifier.py — exact-sentence hallucination detection."""

import pytest
from sentence_verifier import (
    extract_sentences,
    extract_factual_sentences_from_summary,
    verify_summary_against_source,
    SentencesResult,
    _significant_numbers,
)


# ── extract_sentences ──────────────────────────────────────────────

def test_extract_simple():
    assert extract_sentences("One. Two. Three.") == ["One", "Two", "Three"]


def test_extract_single():
    assert extract_sentences("Just one sentence without period") == [
        "Just one sentence without period"
    ]


def test_extract_empty():
    assert extract_sentences("") == []
    assert extract_sentences("   ") == []
    assert extract_sentences(None) == []  # type: ignore[arg-type]


def test_extract_abbreviations_et_al():
    result = extract_sentences("Smith et al. 2020 found X. Another finding.")
    assert len(result) == 2
    assert result[0] == "Smith et al. 2020 found X"


def test_extract_abbreviations_eg_ie():
    result = extract_sentences("Some e.g. apples and i.e. fruit. Second sentence.")
    assert len(result) == 2
    assert "e.g. apples" in result[0]
    assert "i.e. fruit" in result[0]


def test_extract_abbreviations_fig():
    result = extract_sentences("See Fig. 3A for details. The results were clear.")
    assert len(result) == 2
    assert "See Fig. 3A for details" in result[0]


def test_extract_decimal_numbers():
    result = extract_sentences("p < 0.05 was considered significant. N = 100.")
    assert len(result) == 2
    assert "p < 0.05" in result[0]


def test_extract_question():
    result = extract_sentences("What is the mechanism? We investigated this.")
    assert len(result) == 2
    assert result[0] == "What is the mechanism"


def test_extract_parenthetical_ref():
    result = extract_sentences("The method was described (p. 5). Next section.")
    assert len(result) == 2


# ── extract_factual_sentences_from_summary ──────────────────────────

def test_extract_factual_strips_yaml():
    md = """---
tags: [foo]
type: source
---
This is the first sentence. And a second one."""
    result = extract_factual_sentences_from_summary(md)
    assert "This is the first sentence" in result
    assert "tags:" not in " ".join(result)


def test_extract_factual_strips_headings():
    md = """---
---
## Title & Metadata
Some content here.
## Abstract Summary
The abstract text.
## Key Results & Data
Result one. Result two."""
    result = extract_factual_sentences_from_summary(md)
    assert "Title & Metadata" not in " ".join(result)
    assert "Abstract Summary" not in " ".join(result)
    assert "Some content here" in result
    assert "The abstract text" in result
    assert "Result one" in result


def test_extract_factual_strips_wikilinks():
    md = """---
---
[[TaPHS1]] is a gene. It regulates [[drought-tolerance]]."""
    result = extract_factual_sentences_from_summary(md)
    combined = " ".join(result)
    assert "[[TaPHS1]]" not in combined
    assert "TaPHS1" in combined
    assert "[[drought-tolerance]]" not in combined
    assert "drought-tolerance" in combined


def test_extract_factual_strips_bold_italic():
    md = """---
---
**Bold text** and *italic text* are present. Plain sentence."""
    result = extract_factual_sentences_from_summary(md)
    combined = " ".join(result)
    assert "**" not in combined
    assert "Bold text" in combined
    assert "italic text" in combined


def test_extract_factual_filters_not_reported():
    md = """---
---
This is real. Not reported in this paper. Another real one."""
    result = extract_factual_sentences_from_summary(md)
    assert "Not reported in this paper" not in result
    assert "This is real" in result
    assert "Another real one" in result


def test_extract_factual_strips_footer():
    md = """---
---
Content here.
---
**Source PDF:** data/paper.pdf"""
    result = extract_factual_sentences_from_summary(md)
    assert "Source PDF" not in " ".join(result)
    assert "Content here" in result


def test_extract_factual_empty_summary():
    result = extract_factual_sentences_from_summary("---\n---\nNot reported in this paper.")
    assert result == []


# ── verify_summary_against_source ──────────────────────────────────

def test_verify_all_match():
    sentences = ["The QTL had LOD = 12.4", "Yangmai showed high yield"]
    raw = "The QTL had LOD = 12.4 in Yangmai. Yangmai showed high yield under drought."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 1.0
    assert len(result.verified) == 2
    assert len(result.unverified) == 0


def test_verify_none_match():
    sentences = ["Totally fabricated text"]
    raw = "Nothing like it."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 0.0
    assert len(result.verified) == 0
    assert len(result.unverified) == 1


def test_verify_partial():
    sentences = ["This is real", "This is fake"]
    raw = "This is real text in the source."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 0.5
    assert result.verified == ["This is real"]
    assert result.unverified == ["This is fake"]


def test_verify_substring():
    sentences = ["QTL had LOD = 12.4"]
    raw = "The QTL had LOD = 12.4 in Yangmai which was significant."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 1.0
    assert len(result.verified) == 1


def test_verify_unicode_normalization():
    sentences = ['"the QTL" had LOD = 12.4']
    raw = "\u201cthe QTL\u201d had LOD = 12.4 in Yangmai."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 1.0


def test_verify_ligature_expansion():
    sentences = ["efficient process"]
    raw = "e\ufb03cient process was observed."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 1.0


def test_verify_empty_input():
    result = verify_summary_against_source([], "some source text")
    assert result.confidence == 1.0
    assert result.total == 0


def test_verify_case_insensitive():
    sentences = ["The QTL WAS SIGNIFICANT"]
    raw = "the qtl was significant at p < 0.05."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 1.0


# ── tightened grounding: numeric veto + ordered evidence ───────────

def test_verify_rejects_transposed_number():
    # Same words as the source, but the statistic is wrong (12.4 -> 21.4).
    # Old bag-of-words overlap accepted this; the numeric veto now rejects it.
    sentences = ["The QTL had LOD = 21.4"]
    raw = "The QTL had LOD = 12.4 in Yangmai which was significant."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 0.0
    assert result.unverified == ["The QTL had LOD = 21.4"]


def test_verify_rejects_fabricated_percentage():
    sentences = ["Yield increased by 80% under drought"]
    raw = "Yield increased by 25% under drought stress in the field trial."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 0.0


def test_verify_rejects_recombination_hallucination():
    # All content words are present in the source, but the regulatory
    # relationship is reversed. No verbatim trigrams and low ordered coverage.
    sentences = ["ABA regulates VP1 dormancy signaling"]
    raw = "VP1 regulates ABA signaling in wheat seed dormancy pathways."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 0.0
    assert result.unverified == ["ABA regulates VP1 dormancy signaling"]


def test_verify_accepts_faithful_paraphrase_with_intervening_words():
    # Not a verbatim substring (source inserts "the ... gene"), but the content
    # words appear in source order, so ordered coverage accepts it.
    sentences = ["Seed dormancy is controlled by TaPHS1"]
    raw = "Seed dormancy is controlled by the TaPHS1 gene in hexaploid wheat."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 1.0
    assert result.verified == ["Seed dormancy is controlled by TaPHS1"]


def test_verify_accepts_correct_number_paraphrase():
    # Correct number present in source and words largely in order -> grounded.
    sentences = ["Expression increased 2.5 fold in mutants"]
    raw = "In mutants, expression increased 2.5 fold relative to wild type."
    result = verify_summary_against_source(sentences, raw)
    assert result.confidence == 1.0


def test_verify_single_digit_not_vetoed():
    # Single-digit integers are not treated as significant numbers, so they
    # never trigger the numeric veto on their own.
    assert _significant_numbers("3 genes were edited") == []
    assert _significant_numbers("2 of the 3 lines") == []


def test_significant_numbers_helper():
    assert _significant_numbers("LOD = 12.4") == ["12.4"]
    assert _significant_numbers("increased by 30%") == ["30"]
    assert _significant_numbers("published in 2023") == ["2023"]
    assert _significant_numbers("150 samples") == ["150"]
    # single digits with no decimal/percent are ignored
    assert _significant_numbers("only 5 plants") == []
    # thousands separators are stripped to the numeric core
    assert _significant_numbers("12,000 reads") == ["12000"]


# ── SentencesResult dataclass ──────────────────────────────────────

def test_sentences_result_dataclass():
    sr = SentencesResult(0.75, ["a", "b", "c"], ["d"], 4)
    d = sr.as_dict()
    assert d == {
        "confidence": 0.75,
        "verified_count": 3,
        "unverified_count": 1,
        "total": 4,
        "unverified": ["d"],
    }


def test_sentences_result_json_roundtrip():
    import json
    sr = SentencesResult(0.5, ["verified"], ["unverified"], 2)
    d = sr.as_dict()
    json_str = json.dumps(d)
    loaded = json.loads(json_str)
    assert loaded["confidence"] == 0.5
    assert loaded["verified_count"] == 1
    assert loaded["unverified_count"] == 1
