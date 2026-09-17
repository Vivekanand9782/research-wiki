"""Paper-type pre-classifier (Task 5 of the ingestion-prompt overhaul).

Picks one of ``prompts.PAPER_TYPES`` from the first ~3000 chars of the
source markdown. Two-tier strategy:

1. **Cheap heuristic.** Regex matches against the head of the source
   text catch the obvious cases (correction notices, errata, reviews,
   methods papers, perspectives) without an LLM call.
2. **LLM fallback.** When the heuristic is ambiguous, callers can pass a
   one-word LLM prompt callable (typically
   ``functools.partial(genai_client.get_ai_response,
   model=config.FILTER_MODEL, temperature=0)``).

On parse failure or when no signal is found, the classifier returns
``prompts.DEFAULT_PAPER_TYPE`` (``primary_research``) — the
least-disruptive default.

This module has no third-party imports so it stays test-friendly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

from prompts import DEFAULT_PAPER_TYPE, PAPER_TYPES

# Number of characters at the head of the source we consider. The Task 11
# benchmark may revisit this; 3000 is enough to catch a 1-page errata or
# a typical paper title + abstract.
HEAD_CHAR_BUDGET = 3000


# ---------------------------------------------------------------------------
# Heuristic patterns
# ---------------------------------------------------------------------------

# Paired: (compiled regex, paper_type, short rationale).
# Order matters — earlier patterns take precedence.
_HEURISTIC_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    # Correction notices — the narrowest, most reliable signal.
    (re.compile(r"(?i)^\s*correction\s+to\s*:", re.MULTILINE),
     "correction_notice", "starts with 'Correction to:'"),
    (re.compile(r"(?i)\b(erratum|corrigend(?:um|a))\b"),
     "correction_notice", "contains 'Erratum' / 'Corrigendum'"),
    (re.compile(r"(?i)^\s*(?:author\s+)?correction\b", re.MULTILINE),
     "correction_notice", "starts with 'Correction' / 'Author Correction'"),
    (re.compile(r"(?i)^\s*editorial\s+(?:expression\s+of\s+concern|note|comment)",
                re.MULTILINE),
     "correction_notice", "editorial expression of concern"),
    (re.compile(r"(?i)^\s*retraction\s+(?:of|note|notice)", re.MULTILINE),
     "correction_notice", "retraction notice"),

    # Reviews — common phrasing in the abstract / opening lines.
    (re.compile(r"(?i)^#.*\breview\b", re.MULTILINE),
     "review", "title contains 'review'"),
    (re.compile(r"(?i)\b(this|the present)\s+review\s+(?:discusses|covers|"
                r"summari[sz]es|highlights|examines)"),
     "review", "self-described review"),
    (re.compile(r"(?i)\bhere\s+we\s+review\b"),
     "review", "'here we review' phrasing"),
    (re.compile(r"(?i)\bsystematic\s+review\b"),
     "review", "systematic review"),
    (re.compile(r"(?i)\bmeta[\s-]?analysis\b"),
     "review", "meta-analysis"),

    # Methods papers — protocols, standardised methods.
    (re.compile(r"(?i)^#.*\b(protocol|standard\s+operating\s+procedure)\b",
                re.MULTILINE),
     "methods_paper", "title contains 'Protocol' / 'SOP'"),
    (re.compile(r"(?i)\bwe\s+(?:describe|present|introduce)\s+a\s+(?:novel\s+)?"
                r"(?:method|protocol|procedure|tool|software|pipeline)\s+for"),
     "methods_paper", "introduces a method/protocol/tool"),

    # Perspectives / commentaries.
    (re.compile(r"(?i)^#.*\b(perspective|commentary|opinion)\b", re.MULTILINE),
     "perspective", "title contains 'Perspective' / 'Commentary' / 'Opinion'"),

    # Conference proceedings — explicit phrasing.
    (re.compile(r"(?i)\b(?:proceedings|conference\s+paper)\s+of\b"),
     "conference_proceedings", "conference proceedings phrasing"),
]


@dataclass(frozen=True)
class ClassificationResult:
    """Outcome of a single classification call."""

    paper_type: str
    source: str  # "heuristic" | "llm" | "default"
    rationale: str = ""

    def is_default(self) -> bool:
        return self.source == "default"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_paper_type(
    source_text: str,
    *,
    llm_caller: Optional[Callable[[str], str]] = None,
    head_chars: int = HEAD_CHAR_BUDGET,
) -> ClassificationResult:
    """Classify the paper type from the head of the source text.

    Parameters
    ----------
    source_text:
        Raw markdown produced by OpenDataLoader.
    llm_caller:
        Optional callable ``(prompt: str) -> str`` used as a fallback when
        the heuristic doesn't fire. The pipeline integration will pass
        ``functools.partial(get_ai_response, model=config.FILTER_MODEL,
        temperature=0)``. None means "skip the LLM fallback and return
        the default".
    head_chars:
        How many leading characters to scan. 3000 is enough to capture
        the title + abstract for typical PDFs.
    """
    if not source_text:
        return ClassificationResult(DEFAULT_PAPER_TYPE, "default",
                                    "empty source text")

    head = source_text[:head_chars]

    # Tier 1: cheap heuristic.
    hit = _heuristic_classify(head)
    if hit is not None:
        paper_type, rationale = hit
        return ClassificationResult(paper_type, "heuristic", rationale)

    # Tier 2: LLM fallback.
    if llm_caller is not None:
        try:
            llm_type = _classify_with_llm(head, llm_caller)
            if llm_type in PAPER_TYPES:
                return ClassificationResult(llm_type, "llm",
                                            "LLM single-word answer")
        except Exception as exc:  # noqa: BLE001 — never break the pipeline
            return ClassificationResult(
                DEFAULT_PAPER_TYPE, "default",
                f"LLM error: {exc!r}; defaulted to {DEFAULT_PAPER_TYPE}",
            )

    return ClassificationResult(DEFAULT_PAPER_TYPE, "default",
                                "no signal; defaulted")


def _heuristic_classify(head: str) -> tuple[str, str] | None:
    """Return (paper_type, rationale) on a heuristic hit, else None."""
    for pattern, paper_type, rationale in _HEURISTIC_PATTERNS:
        if pattern.search(head):
            return paper_type, rationale
    return None


_LLM_CLASSIFY_PROMPT = """\
You are classifying a scientific document into ONE of these categories:

  primary_research, review, methods_paper, perspective, correction_notice,
  conference_proceedings, other

Reply with only the category name — one word, no quotes, no explanation.

If the document looks like a 1-2 page errata / Author Correction / Erratum,
say `correction_notice`.
If it summarises or surveys other people's work without new experiments,
say `review`.
If it primarily introduces a new method, protocol, or pipeline, say
`methods_paper`.
If it is a commentary / perspective / opinion piece, say `perspective`.
If it presents new experimental results, say `primary_research`.
If unclear, say `other`.

Document head (first ~3000 chars):
---
{head}
---

Category:"""


def _classify_with_llm(head: str, llm_caller: Callable[[str], str]) -> str:
    """Invoke the LLM caller and parse its single-word response."""
    response = llm_caller(_LLM_CLASSIFY_PROMPT.format(head=head))
    if not response:
        return ""
    # Take first non-empty token, lower it, strip punctuation.
    first = response.strip().split()[0].lower().strip(".,;:'\"")
    return first


__all__ = [
    "ClassificationResult",
    "classify_paper_type",
    "HEAD_CHAR_BUDGET",
]
