"""Deterministic grounding gate for the retrieval agent's final answer.

Mirrors the ingestion-side hallucination gate (``research-wiki/sentence_verifier``)
but points it at the evidence the agent *actually retrieved* rather than a raw
PDF. Pure Python — no LLM, no network — so it runs cheaply on every answer and
is unit-testable offline.

Two independent checks:

* **Grounding** — every factual sentence in the answer must be supported by the
  concatenated text of the tool observations the agent saw, using the very same
  sentence-level verifier the ingestion pipeline uses. This closes the retrieval
  gap where the final answer was previously returned verbatim with no
  programmatic verification.
* **Citation existence** — every wiki ``.md`` path the answer cites must both
  exist on disk and have actually been retrieved during the run, so the agent
  cannot cite a plausible-looking page it never opened.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# sentence_verifier + its renderer dependency live at the research-wiki root.
# Ensure it is importable even if this module is imported before wiki_tools.
_RESEARCH_WIKI = (
    Path(os.environ.get("ANTIGRAVITY_ROOT", Path.home() / "Desktop" / "antigravity"))
    / "research-wiki"
)
if str(_RESEARCH_WIKI) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_WIKI))

from sentence_verifier import (  # noqa: E402
    extract_factual_sentences_from_summary,
    verify_summary_against_source,
)

# Canonical wiki markdown path anywhere in free text (inline or References
# block). The `#section` suffix, if any, sits after `.md` and is intentionally
# excluded from the captured path.
_MD_PATH_RE = re.compile(
    r"(?:wiki/)?((?:sources|entities|concepts|synthesis)/[^\s)\]\"'>]+\.md)"
)

ABSTENTION = "No supporting evidence was found in the wiki for this question."


def _canon(path: str) -> str:
    """Reduce any path form to its ``<kind>/…​.md`` suffix for comparison."""
    m = _MD_PATH_RE.search(path)
    return m.group(1) if m else path.strip().lstrip("/")


def extract_cited_paths(answer: str) -> list[str]:
    """Return the distinct canonical wiki md paths referenced in *answer*."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _MD_PATH_RE.finditer(answer):
        canon = m.group(1)
        if canon not in seen:
            seen.add(canon)
            out.append(canon)
    return out


_REFERENCES_HEADING_RE = re.compile(r"(?im)^\s*#{0,6}\s*\**references\**\s*:?\s*$")


def _strip_for_grounding(answer: str) -> str:
    """Return the claim-bearing body of *answer* for sentence verification.

    Drops the trailing References block (those lines are citations, not claims)
    and removes inline ``.md`` path citations so the grounding check measures
    the factual statement, not the citation apparatus wrapped around it.
    """
    body = _REFERENCES_HEADING_RE.split(answer, maxsplit=1)[0]
    body = _MD_PATH_RE.sub("", body)
    return body


@dataclass
class GroundingReport:
    confidence: float
    supported: list[str]
    unsupported: list[str]
    total: int
    cited_paths: list[str]
    invalid_citations: list[str]
    evidence_empty: bool
    ok: bool

    def as_dict(self) -> dict:
        return {
            "confidence": round(self.confidence, 3),
            "supported_count": len(self.supported),
            "unsupported_count": len(self.unsupported),
            "total": self.total,
            "cited_paths": self.cited_paths,
            "invalid_citations": self.invalid_citations,
            "evidence_empty": self.evidence_empty,
            "ok": self.ok,
            "unsupported": self.unsupported,
        }


def verify_answer(
    answer: str,
    evidence_chunks: list[str],
    retrieved_paths: set[str] | None = None,
    *,
    threshold: float = 0.75,
    path_exists=None,
) -> GroundingReport:
    """Verify *answer* against the evidence the agent retrieved.

    Parameters
    ----------
    answer:
        The agent's synthesised answer markdown.
    evidence_chunks:
        The raw text of every tool observation the agent saw this session.
    retrieved_paths:
        Wiki paths that appeared in observations or read-tool arguments. When
        provided, a cited path absent from this set is flagged as invalid.
    threshold:
        Minimum grounded-sentence fraction for ``ok``.
    path_exists:
        Optional callable ``canon_path -> bool`` used to confirm a cited path
        exists on disk. When ``None``, existence is not checked (only retrieval).
    """
    retrieved_canon = {_canon(p) for p in (retrieved_paths or set())}
    corpus = "\n\n".join(c for c in evidence_chunks if c)
    evidence_empty = not corpus.strip()

    sentences = extract_factual_sentences_from_summary(_strip_for_grounding(answer))
    result = verify_summary_against_source(sentences, corpus)

    cited = extract_cited_paths(answer)
    invalid: list[str] = []
    for c in cited:
        canon = _canon(c)
        exists = True if path_exists is None else bool(path_exists(canon))
        # Only enforce "was retrieved" when we actually tracked retrieved paths.
        retrieved = (canon in retrieved_canon) if retrieved_canon else True
        if not exists or not retrieved:
            invalid.append(c)

    ok = (not evidence_empty) and result.confidence >= threshold and not invalid
    return GroundingReport(
        confidence=result.confidence,
        supported=result.verified,
        unsupported=result.unverified,
        total=result.total,
        cited_paths=cited,
        invalid_citations=invalid,
        evidence_empty=evidence_empty,
        ok=ok,
    )


def build_repair_message(report: GroundingReport) -> str:
    """Construct a corrective user message for a failed grounding check."""
    lines = [
        "Your draft answer failed grounding verification against the evidence "
        "you actually retrieved. Revise it so every factual claim is supported "
        "by a retrieved observation, and cite only pages you opened this "
        "session.",
    ]
    if report.evidence_empty:
        lines.append(
            "- No evidence has been retrieved yet. Call a search/read tool "
            'first, or, if the corpus is exhausted, abstain: {"answer": '
            f'"{ABSTENTION}"}}'
        )
    if report.unsupported:
        lines.append(
            "- These sentences are NOT supported by retrieved text — remove "
            "them or replace with a claim quoted from an observation:"
        )
        for s in report.unsupported[:8]:
            lines.append(f"    • {s[:160]}")
    if report.invalid_citations:
        lines.append(
            "- These cited paths were never retrieved this session or do not "
            "exist — cite only pages you actually opened:"
        )
        for c in report.invalid_citations[:8]:
            lines.append(f"    • {c}")
    lines.append('Reply with a corrected JSON answer: {"answer": "..."}')
    return "\n".join(lines)
