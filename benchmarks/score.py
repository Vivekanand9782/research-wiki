"""Deterministic A/B benchmark scoring (Task 11).

Compares two wiki-summary Markdown strings (legacy vs two-stage) on:

  * strict_pass — passes the 12-section anchored validator
  * lenient_pass — passes the historical 5-section validator
  * score — ``validation.SummaryValidator`` 0-100 score
  * wikilink_count — total ``[[...]]`` tokens
  * canonicalised_rate — fraction of wikilinks whose slug resolves
    against the live ``wiki_vocabulary`` index (proxy for canonicalisation)
  * footnote_count — ``[^foo]:`` definition lines (Task 9 evidence anchors)

Pure deterministic, no LLM calls, so the A/B sweep runs in seconds.
The Task 11 CLI imports ``score_summary`` and ``compare_summaries`` from
here.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Optional

# These imports are heavy enough to defer until first use.


@dataclass
class SummaryScore:
    """Single-summary metrics."""

    strict_pass: bool
    lenient_pass: bool
    score: float            # 0-100 from validation.SummaryValidator
    wikilink_count: int
    canonicalised_rate: float  # 0-1, requires vocab_index
    footnote_count: int
    hallucination_confidence: float = 1.0  # 1.0 when no raw text available

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Comparison:
    """Result of comparing legacy vs two-stage on one paper."""

    paper: str
    legacy: SummaryScore
    two_stage: SummaryScore

    def deltas(self) -> dict[str, float]:
        """``two_stage - legacy`` per metric."""
        out: dict[str, float] = {}
        a = self.two_stage.as_dict()
        b = self.legacy.as_dict()
        for k, v in a.items():
            if isinstance(v, bool):
                out[k] = int(v) - int(b[k])
            else:
                out[k] = v - b[k]
        return out


_WIKILINK_RE = re.compile(r"\[\[([^\]\|]+?)(?:\|[^\]]+?)?\]\]")
_FOOTNOTE_DEF_RE = re.compile(r"(?m)^\[\^[^\]]+?\]:")


def score_summary(markdown: str, vocab_index=None, raw_text: str | None = None) -> SummaryScore:
    """Compute the metric set for one summary.

    Pass ``vocab_index`` (a ``wiki_vocabulary.VocabularyIndex``) to fill
    in ``canonicalised_rate``; without it the field is 0.0.

    Pass ``raw_text`` (the raw/papers/*.md source) to compute
    ``hallucination_confidence``; without it the field is 1.0.
    """
    from genai_client import (
        validate_structured_summary,
        validate_structured_summary_strict,
    )
    from validation import SummaryValidator

    strict = validate_structured_summary_strict(markdown)
    lenient = validate_structured_summary(markdown)
    sv = SummaryValidator().validate(markdown)

    # Wikilinks: extract all [[...]] tokens. The first capture is the
    # display text; we count both bare and aliased forms.
    wikilinks = _WIKILINK_RE.findall(markdown)
    wl_count = len(wikilinks)

    if vocab_index is not None and wl_count > 0:
        resolved = sum(
            1 for wl in wikilinks if vocab_index.find_canonical(wl) is not None
        )
        canonicalised_rate = resolved / wl_count
    else:
        canonicalised_rate = 0.0

    footnote_count = len(_FOOTNOTE_DEF_RE.findall(markdown))

    hallucination_confidence = 1.0
    if raw_text:
        from sentence_verifier import (
            extract_factual_sentences_from_summary,
            verify_summary_against_source,
        )
        sentences = extract_factual_sentences_from_summary(markdown)
        hall_result = verify_summary_against_source(sentences, raw_text)
        hallucination_confidence = hall_result.confidence

    return SummaryScore(
        strict_pass=bool(strict.get("valid", False)),
        lenient_pass=bool(lenient.get("valid", False)),
        score=float(sv.score),
        wikilink_count=wl_count,
        canonicalised_rate=canonicalised_rate,
        footnote_count=footnote_count,
        hallucination_confidence=hallucination_confidence,
    )


def compare_summaries(
    paper: str,
    legacy_md: str,
    two_stage_md: str,
    *,
    vocab_index=None,
    legacy_raw_text: str | None = None,
    two_stage_raw_text: str | None = None,
) -> Comparison:
    """Score both summaries and return a Comparison."""
    return Comparison(
        paper=paper,
        legacy=score_summary(legacy_md, vocab_index=vocab_index, raw_text=legacy_raw_text),
        two_stage=score_summary(two_stage_md, vocab_index=vocab_index, raw_text=two_stage_raw_text),
    )


def acceptance_check(deltas: list[dict[str, float]],
                     *, regression_tolerance: float = 5.0) -> tuple[bool, list[str]]:
    """Acceptance gate for flipping ``USE_TWO_STAGE_EXTRACTION``.

    The plan calls for "no metric regresses by more than 5 points" in
    aggregate. ``deltas`` is a list of ``Comparison.deltas()`` dicts.
    Returns ``(ok, reasons)`` where ``reasons`` lists every metric that
    regressed too far.
    """
    if not deltas:
        return False, ["no comparisons supplied"]

    keys = set().union(*(d.keys() for d in deltas))
    reasons: list[str] = []
    for k in keys:
        avg = sum(d.get(k, 0.0) for d in deltas) / len(deltas)
        if k == "score" and avg < -regression_tolerance:
            reasons.append(f"score regressed by {avg:.1f} points (avg)")
        elif k == "canonicalised_rate" and avg < -regression_tolerance / 100:
            reasons.append(f"canonicalised_rate regressed by {avg:.3f} (avg)")
        elif k == "wikilink_count" and avg < -2:
            reasons.append(f"wikilink_count regressed by {avg:.1f} (avg)")
    return (not reasons), reasons


__all__ = [
    "SummaryScore",
    "Comparison",
    "score_summary",
    "compare_summaries",
    "acceptance_check",
]
