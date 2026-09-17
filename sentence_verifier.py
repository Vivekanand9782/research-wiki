"""Exact-sentence hallucination verifier for wiki summaries.

Compares every factual sentence in a ``wiki/sources/`` summary against the
corresponding ``raw/papers/`` source text.  A sentence is "verified" iff it
appears as a verbatim substring of the source after normalisation (Unicode
quotes → ASCII, ligature expansion, whitespace collapse, lowercase).

This is an additional safety gate run **after** structural validation.  If
confidence falls below ``config.HALLUCINATION_CONFIDENCE_THRESHOLD`` the
pipeline triggers a hallucination-specific repair + retry loop.
"""

from __future__ import annotations

import re
from bisect import bisect_right
from dataclasses import dataclass

from renderer import _normalise_for_quote_match as _normalise

# ---------------------------------------------------------------------------
# Sentence extraction
# ---------------------------------------------------------------------------

_ABBREVIATIONS = (
    "et al",
    r"e\.g",
    r"i\.e",
    "Fig",
    "cf",
    "viz",
    "vs",
    "p",
    "pp",
    "vol",
    "no",
    "ed",
    "eds",
    "ref",
    "refs",
    "ca",
    "approx",
    "Eq",
    "Eqs",
    "Dr",
    "Prof",
    "Mr",
    "Mrs",
    "Ms",
    "St",
    "Ave",
    "Inc",
    "Ltd",
    "Co",
    "Jr",
    "Sr",
)

def _build_sentence_re() -> re.Pattern:
    """Construct a regex that splits on ``[.?!]`` not preceded by known abbreviations."""
    # (?<!abbrev)  — negative lookbehind for each abbreviation token.
    lookbehinds = "".join(f"(?<!\\b{abbr})" for abbr in _ABBREVIATIONS)
    return re.compile(
        rf"{lookbehinds}[.?!](?=(?:\s+[A-Z])|\s+['\"\u201C\u201D]?\s*$|\s*\)?\s*$)",
    )

_SENTENCE_SPLIT_RE = _build_sentence_re()

def extract_sentences(text: str) -> list[str]:
    """Split *text* into sentences using regex rules.

    Handles abbreviations (``et al.``, ``e.g.``, ``Fig. 3``, etc.),
    decimal numbers (``p < 0.05``), and parenthetical page references
    (``(p. 5)``).
    """
    if not text or not text.strip():
        return []

    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


# Markdown stripping helpers -------------------------------------------------

_YAML_BOUNDARY_RE = re.compile(r"^---\s*$", re.MULTILINE)
_H2_HEADING_RE    = re.compile(r"^##\s+.+$", re.MULTILINE)
_WIKILINK_RE      = re.compile(r"\[\[([^\]]+)\]\]")
# Citation wikilinks that are pure reference slugs: author_year_description
# These should be removed entirely, not kept as display text.
_CITATION_SLUG    = re.compile(r"\b[a-z]+_\d{4}(?:_[a-z0-9-]+)+\b")
_MARKDOWN_MARKUP  = re.compile(r"\*{1,2}([^*]+)\*{1,2}")
_HORIZONTAL_RULE  = re.compile(r"^-{3,}\s*$", re.MULTILINE)
_PDF_FOOTER_RE    = re.compile(r"\*\*Source PDF:\*\*.*$", re.MULTILINE)
_NOT_REPORTED_RE  = re.compile(r"Not\s+reported\s+in\s+this\s+paper\.?", re.IGNORECASE)


def _strip_yaml(text: str) -> str:
    """Remove YAML frontmatter delimited by ``---``."""
    # Three-or-more dashes on a line by themselves.
    m = re.match(r"^-{3,}\s*$", text, re.MULTILINE)
    if not m:
        return text
    start = m.end()
    # Search for a second row of dashes.
    closing = re.search(r"^-{3,}\s*$", text[start:], re.MULTILINE)
    if not closing:
        return text
    return text[start + closing.end():]


def extract_factual_sentences_from_summary(summary_md: str) -> list[str]:
    """Return factual sentences from a wiki-summary Markdown string.

    Removes YAML frontmatter, H2 headings, wikilink markup (``[[…]]``),
    bold/italic markers, the PDF footer, and the ``NOT_REPORTED``
    sentinel.  The remaining prose is split into sentences.
    """
    text = _strip_yaml(summary_md)
    text = _H2_HEADING_RE.sub("", text)
    text = _PDF_FOOTER_RE.sub("", text)
    text = _HORIZONTAL_RULE.sub("", text)
    text = _WIKILINK_RE.sub(r"\1", text)
    # Strip bare citation slugs (author_year_description) left behind
    text = _CITATION_SLUG.sub("", text)
    text = _MARKDOWN_MARKUP.sub(r"\1", text)

    sentences = extract_sentences(text)
    # Filter out NOT_REPORTED boilerplate and empty strings.
    return [
        s for s in sentences
        if not _NOT_REPORTED_RE.fullmatch(s.strip(".").strip())
    ]


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

@dataclass
class SentencesResult:
    confidence: float       # verified / total  (1.0 if no factual sentences)
    verified: list[str]     # sentences confirmed present in source
    unverified: list[str]   # sentences NOT found in source
    total: int              # total factual sentences checked

    def as_dict(self) -> dict:
        return {
            "confidence": self.confidence,
            "verified_count": len(self.verified),
            "unverified_count": len(self.unverified),
            "total": self.total,
            "unverified": self.unverified,
        }


_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "when", "where", "how", "who", "which", "this", "that", "these", "those",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "to", "from", "in", "out", "on", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "just", "should", "now", "also", "with", "by", "for", "at", "of", "about",
    "into", "through", "during", "before", "after", "above", "below"
}

_NUMERIC_TOKEN_RE = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
_WORD_TOKEN_RE = re.compile(r"\b[a-z0-9_-]+\b")


def _significant_numbers(text: str) -> list[str]:
    """Return numeric tokens whose exact value matters for grounding.

    "Significant" = decimal (``12.4``), percentage (``30%``), or multi-digit
    integer (``2023``, ``150``). Single-digit integers are ignored: they are
    frequently spelled out or purely structural (``3 genes``) and are a poor
    hallucination signal. Thousands separators are stripped and any trailing
    ``%`` removed so the numeric *core* can be substring-matched against a
    likewise comma-stripped source.
    """
    cores: list[str] = []
    for m in _NUMERIC_TOKEN_RE.finditer(text):
        norm = m.group(0).replace(",", "")
        core = norm.rstrip("%")
        digits_only = core.replace(".", "")
        if not digits_only.isdigit():
            continue
        is_significant = ("." in core) or norm.endswith("%") or len(digits_only) >= 2
        if is_significant:
            cores.append(core)
    return cores


def _ordered_match_ratio(words: list[str], raw_token_positions: dict[str, list[int]]) -> float:
    """Fraction of *words* that occur in the source in the same relative order.

    Greedily walks the sentence's content words, matching each to the earliest
    source position strictly after the previous match (binary search over each
    token's sorted position list). This rewards faithful paraphrase — where the
    words keep their source order — and penalises *recombination* hallucinations
    that reuse the paper's vocabulary in a relationship the paper never stated
    (e.g. swapping the subject and object of a regulatory claim). Robust to
    intervening stop-words because it matches a subsequence, not adjacency.
    """
    if not words:
        return 0.0
    last = -1
    matched = 0
    for w in words:
        positions = raw_token_positions.get(w)
        if not positions:
            continue
        idx = bisect_right(positions, last)
        if idx < len(positions):
            last = positions[idx]
            matched += 1
    return matched / len(words)


def _is_sentence_grounded(
    sentence: str,
    raw_normalised: str,
    raw_no_commas: str,
    raw_token_positions: dict[str, list[int]],
) -> bool:
    """Check whether *sentence* is grounded in the source text.

    Grounding tiers, strongest first:

    1. **Exact substring** of the normalised source — always accepted.
    2. **Numeric veto** — every "significant" number in the sentence (decimals,
       percentages, multi-digit integers) must appear in the source. A sentence
       that reuses the source's words but states a number the source never gives
       (e.g. ``LOD = 21.4`` when the source says ``12.4``) is rejected here even
       when its word overlap is perfect.
    3. **Ordered evidence** — accepted only when the content words appear in the
       source *in order* (>= 60% ordered coverage) or >= 30% of the sentence's
       content trigrams occur verbatim. Order-independent bag-of-words overlap
       is no longer sufficient on its own, which is what previously let a
       recombined/relational hallucination pass.
    """
    norm = _normalise(sentence)
    if not norm:
        return False

    # 1. Exact substring match — strongest signal.
    if norm in raw_normalised:
        return True

    # 2. Numeric grounding veto: a fabricated/transposed number is a hard fail,
    #    regardless of how well the surrounding words overlap the source.
    for num in _significant_numbers(norm):
        if num not in raw_no_commas:
            return False

    # Content words (drop stop-words and very short tokens).
    words = [w for w in _WORD_TOKEN_RE.findall(norm) if w not in _STOP_WORDS and len(w) >= 3]
    if not words:
        return True

    # 3a. Ordered content-word coverage — replaces the old order-independent
    #     token-overlap test that let recombination hallucinations through.
    ordered_ratio = _ordered_match_ratio(words, raw_token_positions)

    # 3b. Verbatim trigram overlap — order-sensitive within 3-word windows.
    if len(words) >= 3:
        trigrams = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]
        trigram_matches = sum(1 for tg in trigrams if tg in raw_normalised)
        trigram_overlap = trigram_matches / len(trigrams)
    else:
        trigram_overlap = 1.0 if ordered_ratio >= 0.5 else 0.0

    # Grounded when the words appear largely in source order OR a meaningful
    # share of verbatim trigrams is present.
    return ordered_ratio >= 0.60 or trigram_overlap >= 0.30


def verify_summary_against_source(
    summary_sentences: list[str],
    raw_text: str,
) -> SentencesResult:
    """Check each *summary_sentences* against *raw_text*.

    A sentence is verified when it appears as a verbatim substring or
    has high n-gram/key-token overlap with the raw source text.
    """
    if not summary_sentences:
        return SentencesResult(1.0, [], [], 0)

    raw_normalised = _normalise(raw_text)
    # Comma-stripped copy so numeric cores ("12000") match sources that write
    # "12,000"; positional index powers the ordered content-word check.
    raw_no_commas = raw_normalised.replace(",", "")
    raw_tokens = _WORD_TOKEN_RE.findall(raw_normalised)
    raw_token_positions: dict[str, list[int]] = {}
    for i, tok in enumerate(raw_tokens):
        raw_token_positions.setdefault(tok, []).append(i)

    verified: list[str] = []
    unverified: list[str] = []

    for sentence in summary_sentences:
        if _is_sentence_grounded(sentence, raw_normalised, raw_no_commas, raw_token_positions):
            verified.append(sentence)
        else:
            unverified.append(sentence)

    total = len(verified) + len(unverified)
    confidence = len(verified) / total if total > 0 else 1.0
    return SentencesResult(confidence, verified, unverified, total)
