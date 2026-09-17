"""Stage B renderer (Task 7 of the ingestion-prompt overhaul plan).

Turns a Stage A JSON payload — produced by the model under
``prompts.build_stage_a_prompt`` — into the final Obsidian-flavoured
Markdown wiki page. **Pure Python**: no I/O, no LLM, no third-party
imports beyond the standard library. Heavily testable.

Public API
----------
``render_summary_from_json(payload, *, vocab_index=None, paper_name=None,
today_iso=None) -> RenderResult``

Returns a ``RenderResult(markdown, warnings, canonicalised, new_candidates)``
so callers can inspect what was canonicalised and what new entity
candidates the entity-creation pipeline should pick up.

Design notes
------------
* **Frontmatter:** rendered as YAML between ``---`` markers. Required
  keys come from ``prompts.required_frontmatter_keys()``. Nullable string
  fields (``doi``, ``authors``, ``journal``) emit JSON ``null`` when the
  payload value is None — the YAML representation we choose is
  ``key: null`` (no quotes) to match the Stage A prompt instructions.
* **Sections:** every key in ``prompts.required_headers()`` is emitted
  in canonical order, even if the payload omits it. Missing or empty
  text becomes ``prompts.NOT_REPORTED``.
* **Wikilinks:** if ``vocab_index`` is provided, every ``[[Display]]`` /
  ``[[Display|alt]]`` token in section text is rewritten to
  ``[[canonical-slug|Display]]`` when the canonical slug exists. Tokens
  that don't resolve are left as-is and reported in
  ``RenderResult.new_candidates`` for the entity-creation pipeline.
* **Format version:** ``format_version: <FORMAT_VERSION>`` is appended
  to the frontmatter so downstream tools can distinguish new vs. old
  output formats (Task 12 will bump this).
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from prompts import (
    FORMAT_VERSION,
    FRONTMATTER_KEYS,
    NOT_REPORTED,
    PAPER_TYPES,
    DEFAULT_PAPER_TYPE,
    headers_for,
    required_headers,
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class RenderResult:
    """Outcome of one Stage B render."""

    markdown: str
    warnings: list[str] = field(default_factory=list)
    canonicalised: dict[str, str] = field(default_factory=dict)
    """{display_text: canonical_slug} for every wikilink that resolved."""
    new_candidates: list[str] = field(default_factory=list)
    """Display texts that didn't resolve — feed to entity-creation pipeline."""

    def as_dict(self) -> dict:
        return {
            "markdown": self.markdown,
            "warnings": list(self.warnings),
            "canonicalised": dict(self.canonicalised),
            "new_candidates": list(self.new_candidates),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WIKILINK_RE = re.compile(r"\[\[([^\]\|]+?)(?:\|([^\]]+?))?\]\]")


# ---------------------------------------------------------------------------
# Task 9 — evidence-quote validation + footnote rendering
# ---------------------------------------------------------------------------

#: Unicode → ASCII normalisations for quote matching. Source PDFs (and
#: the OpenDataLoader output we feed to the LLM) often have curly quotes,
#: en/em dashes, ligatures, soft hyphens, and non-breaking spaces. We
#: collapse those to ASCII equivalents so a verbatim quote from the
#: model still matches when the LLM emitted ASCII while the source has
#: typography. Whitespace is also collapsed to single spaces.
_QUOTE_TRANSLATION = str.maketrans({
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201A": "'",   # single low-9 quote
    "\u201C": '"',   # left double quote
    "\u201D": '"',   # right double quote
    "\u201E": '"',   # double low-9 quote
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u2212": "-",   # minus sign
    "\u00AD": "",    # soft hyphen (drop)
    "\u00A0": " ",   # non-breaking space
    "\u2009": " ",   # thin space
    "\u202F": " ",   # narrow no-break space
})

#: Multi-char replacements (str.maketrans can't expand 1 char → many).
_LIGATURE_REPLACEMENTS = (
    ("\ufb03", "ffi"),
    ("\ufb04", "ffl"),
    ("\ufb00", "ff"),
    ("\ufb01", "fi"),
    ("\ufb02", "fl"),
)


def _normalise_for_quote_match(text: str) -> str:
    """Normalise text for verbatim-quote substring matching.

    Lowercases, replaces fancy unicode punctuation with ASCII, drops
    soft hyphens, replaces ligatures with their letter sequences, and
    collapses whitespace runs to single spaces.
    """
    if not text:
        return ""
    s = text.translate(_QUOTE_TRANSLATION)
    for src, dst in _LIGATURE_REPLACEMENTS:
        if src in s:
            s = s.replace(src, dst)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def _verify_quote_in_source(quote: str, source_normalised: str) -> bool:
    """True iff `quote` appears verbatim in the already-normalised source."""
    if not quote or not source_normalised:
        return False
    needle = _normalise_for_quote_match(quote)
    if not needle:
        return False
    return needle in source_normalised


def _render_results_with_footnotes(
    results: list[dict],
    source_normalised: str,
    *,
    section_name: str,
    warnings: list[str],
) -> str:
    """Render a list of result dicts as bullets with section-scoped footnotes.

    Each result is shaped:
      {"claim": str, "evidence_quote": str?, "source_locator": str?}

    Returns the markdown body for the bullets plus the footnote
    definition block. Footnote IDs are scoped per section using the
    pattern ``<section-slug>-N`` so multiple sections in one document
    don't collide.
    """
    if not results:
        return ""

    section_slug = re.sub(r"[^a-z0-9]+", "-", section_name.lower()).strip("-")
    bullets: list[str] = []
    footnote_defs: list[str] = []
    counter = 0

    for r in results:
        if not isinstance(r, dict):
            continue
        claim = (r.get("claim") or "").strip()
        if not claim:
            continue
        quote = (r.get("evidence_quote") or "").strip()
        locator = (r.get("source_locator") or "").strip()

        if quote and source_normalised and _verify_quote_in_source(quote, source_normalised):
            counter += 1
            fn_id = f"{section_slug}-{counter}"
            bullets.append(f"- {claim}.[^{fn_id}]")
            locator_part = f" — {locator}" if locator else ""
            # Strip newlines from the quote so the footnote stays one-line.
            quote_oneline = re.sub(r"\s+", " ", quote).strip()
            footnote_defs.append(f'[^{fn_id}]: "{quote_oneline}"{locator_part}')
        else:
            bullets.append(f"- {claim}.")
            if quote:
                warnings.append(
                    f"section {section_name!r}: evidence quote not found in source "
                    f"(dropped footnote): {quote[:60]!r}"
                )

    parts = ["\n".join(bullets)]
    if footnote_defs:
        parts.append("\n".join(footnote_defs))
    return "\n\n".join(parts)


def _yaml_string(value: str) -> str:
    """Render a Python string as a YAML string value, quoting when needed."""
    s = str(value)
    # Quote when the string contains characters that would change YAML
    # parsing (colons, leading dashes, the literal "null", "true", "false",
    # numbers). Otherwise emit bare for readability.
    needs_quote = (
        ":" in s
        or s.strip() != s
        or s.lower() in {"null", "true", "false", "yes", "no", "~", ""}
        or s.startswith("-")
        or s.startswith("[")
        or s.startswith("#")
        or re.fullmatch(r"-?\d+(?:\.\d+)?", s) is not None
    )
    if needs_quote:
        return '"' + s.replace('\\', r"\\").replace('"', r'\"') + '"'
    return s


def _yaml_value(key_name: str, value: Any) -> str:
    """Render one frontmatter value for the given key.

    ``null`` is JSON-null; lists are inline ``[a, b]``; ints are bare;
    strings go through ``_yaml_string``.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_yaml_string(str(v)) for v in value) + "]"
    return _yaml_string(str(value))


def _canonicalise_wikilinks(
    text: str,
    vocab_index,
    canonicalised: dict[str, str],
    new_candidates: list[str],
) -> str:
    """Rewrite ``[[Display]]`` / ``[[slug|Display]]`` tokens in `text`.

    If ``slug|Display`` is already supplied, leave it. Otherwise look up
    the display text in ``vocab_index`` and rewrite to
    ``[[canonical|Display]]`` if found, else leave as ``[[Display]]`` and
    record it in ``new_candidates``.
    """
    if not vocab_index:
        return text

    seen_new: set[str] = set(new_candidates)

    def repl(m: re.Match[str]) -> str:
        first, alt = m.group(1).strip(), (m.group(2) or "").strip()
        # Already an aliased link: [[slug|display]] -> leave alone.
        if alt:
            return f"[[{first}|{alt}]]"
        slug = vocab_index.find_canonical(first)
        if slug:
            canonicalised[first] = slug
            # Only collapse to [[slug]] when the display IS the slug
            # verbatim — preserve display casing otherwise so
            # [[TaPHS1]] becomes [[taphs1|TaPHS1]] not [[taphs1]].
            if slug == first:
                return f"[[{slug}]]"
            return f"[[{slug}|{first}]]"
        if first not in seen_new:
            seen_new.add(first)
            new_candidates.append(first)
        return f"[[{first}]]"

    return _WIKILINK_RE.sub(repl, text)


def _frontmatter_lines(payload_fm: dict, today_iso: str) -> tuple[list[str], list[str]]:
    """Render the frontmatter key:value lines + warnings."""
    warnings: list[str] = []
    out: list[str] = []
    for key in FRONTMATTER_KEYS:
        name = key.name
        if name in payload_fm:
            value = payload_fm[name]
        elif name == "type":
            value = "source"
        elif name == "source_count":
            value = 1
        elif name in ("date_created", "date_updated"):
            value = today_iso
        elif key.nullable:
            value = None
        else:
            value = None
            warnings.append(f"frontmatter: missing required key {name!r}")
        if value is None and not key.nullable:
            warnings.append(f"frontmatter: required key {name!r} is null")
        out.append(f"{name}: {_yaml_value(name, value)}")
    # Always append format_version so downstream tools can detect v1 vs vN.
    out.append(f"format_version: {FORMAT_VERSION}")
    return out, warnings


def _section_body(
    section_payload: Any,
    *,
    name: str,
    source_normalised: str,
    warnings: list[str],
) -> str:
    """Pull the markdown body out of one sections[name] entry.

    If the payload includes a ``results`` array (Task 9), it is rendered
    as bullets with section-scoped Markdown footnotes whose verbatim
    quotes are validated against ``source_normalised``. Quotes that
    don't validate are dropped (the bullet still renders) and a warning
    is appended to ``warnings``.
    """
    if isinstance(section_payload, dict):
        text = section_payload.get("text")
        results = section_payload.get("results") or []
    elif isinstance(section_payload, str):
        text = section_payload
        results = []
    else:
        text = None
        results = []
    text = (text or "").strip()

    rendered_results = _render_results_with_footnotes(
        results, source_normalised, section_name=name, warnings=warnings,
    )

    if text and rendered_results:
        return f"{text}\n\n{rendered_results}"
    if rendered_results:
        return rendered_results
    return text or NOT_REPORTED


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

ENTITY_SECTION = "Important Entities"

#: Bullet line in ``## Important Entities``, e.g.
#: ``- RpaR (transcriptional regulator, signaling_regulator)`` or ``* TaPHS1``.
#: Group 1 is the bullet marker + spacing, group 2 the entity display name,
#: group 3 the trailing role/description remainder.
_ENTITY_BULLET_RE = re.compile(
    r"^(\s*[-*]\s+)([^\[\n:(][^\n(]*?)(\s*(?:\(.*)?)$"
)
#: A category label followed by an inline comma-separated list rather than one
#: bullet per entity, e.g. ``* **Genes/Proteins**: nifH, eIF4E1-S, PR1``.
_INLINE_CATEGORY_RE = re.compile(r"^(\s*[-*]\s+\*\*[^*\n]+\*\*\s*:\s*)(\S.*)$")
#: A "no entities in this category" filler the LLM emits, e.g. ``None reported.``
_EMPTY_CATEGORY_RE = re.compile(r"^(none|not)\b", re.IGNORECASE)


def _linkify_inline_entity_list(remainder: str) -> tuple[str, int]:
    """Wrap each comma-separated entity in an inline category list in ``[[...]]``.

    Emphasis markers around a name (``*Triticum aestivum*``) are dropped and a
    trailing parenthetical gloss (``(wheat)``) is kept outside the link, so
    ``*Triticum aestivum* (wheat)`` becomes ``[[Triticum aestivum]] (wheat)``.
    A ``None reported.`` remainder is left untouched.
    """
    if _EMPTY_CATEGORY_RE.match(remainder.strip()):
        return remainder, 0
    linked = 0
    parts: list[str] = []
    for chunk in remainder.split(","):
        item = chunk.strip()
        if not item or "[[" in item:
            parts.append(item)
            continue
        gloss = ""
        gm = re.match(r"^(.*?)(\s*\([^)]*\))\s*$", item)
        if gm:
            item, gloss = gm.group(1).strip(), gm.group(2)
        # Markdown emphasis asterisks (``*Triticum aestivum*``) are never part
        # of an entity name and may sit mid-string, so drop them all; only
        # underscores/spaces are stripped from the edges.
        name = re.sub(r"\*+", "", item).strip("_ ").strip()
        if not name or not re.search(r"[A-Za-z0-9]", name):
            parts.append(chunk.strip())
            continue
        parts.append(f"[[{name}]]{gloss}")
        linked += 1
    return ", ".join(p for p in parts if p), linked


def _linkify_entity_bullets(body: str, known: set[str]) -> tuple[str, int]:
    """Wrap bare entity names in ``## Important Entities`` in ``[[...]]``.

    The two-stage Stage A schema returns ``entities[]`` as structured objects
    whose ``text`` is a plain display form, and its own description promises
    "the renderer canonicalises against wiki_vocabulary". Canonicalisation only
    ever *rewrote* existing ``[[...]]`` tokens, so entity bullets rendered as
    plain text and the section ended up with zero wikilinks — silently breaking
    the prompt's "Every entity in ## Important Entities MUST be in [[double
    brackets]]" rule and orphaning the entity graph.

    Handles both layouts the LLM emits: one entity per bullet
    (``- RpaR (regulator)``) and an inline list under a category label
    (``* **Genes/Proteins**: nifH, PR1``). Category subheadings themselves are
    never treated as entities, and bullets/lines already containing a wikilink
    are left untouched, so this is idempotent.

    ``known`` is the set of display names from ``entities[].text`` when the
    payload provides them; a *per-bullet* name is linked when it is in ``known``
    or when ``known`` is empty. The inline-list branch does not cross-check
    against ``known`` because the LLM often reformats names (adds a gloss,
    strips italics) between the flat list and the rendered category line.
    """
    linked = 0
    out: list[str] = []
    for line in body.splitlines():
        if "[[" in line:
            out.append(line)
            continue
        inline = _INLINE_CATEGORY_RE.match(line)
        if inline:
            rest, n = _linkify_inline_entity_list(inline.group(2))
            if n:
                out.append(inline.group(1) + rest)
                linked += n
            else:
                out.append(line)
            continue
        m = _ENTITY_BULLET_RE.match(line)
        if not m:
            out.append(line)
            continue
        marker, name, tail = m.group(1), m.group(2).strip(), m.group(3)
        # Category subheadings (``* **Genes/Proteins**:``) carry ``**`` and are
        # never entities. Strip markdown italics (``*opaque 2*``) from genuine
        # entity names, which the regex now admits.
        if not name or name.endswith(":") or "**" in name:
            out.append(line)
            continue
        name = re.sub(r"\*+", "", name).strip()
        if not name:
            out.append(line)
            continue
        if known and name not in known:
            out.append(line)
            continue
        out.append(f"{marker}[[{name}]]{tail}")
        linked += 1
    return "\n".join(out), linked



def render_summary_from_json(
    payload: dict,
    *,
    vocab_index=None,
    paper_name: str | None = None,
    today_iso: str | None = None,
    source_text: str | None = None,
    paper_type: str | None = None,
) -> RenderResult:
    """Render a Stage A JSON payload into the final Markdown wiki page.

    Parameters
    ----------
    payload:
        Dict matching ``prompts.SUMMARY_JSON_SCHEMA``. Sections may carry
        an optional ``results: [{claim, evidence_quote, source_locator}]``
        array; bullets whose ``evidence_quote`` is verified against
        ``source_text`` get rendered with a Markdown footnote (Task 9).
    vocab_index:
        Optional ``wiki_vocabulary.VocabularyIndex`` for wikilink
        canonicalisation.
    paper_name:
        Used in the trailing ``**Source PDF:** data/<paper>.pdf`` footer.
    today_iso:
        Today's date as YYYY-MM-DD. Defaults to ``datetime.date.today()``.
    source_text:
        Raw OpenDataLoader markdown for evidence-quote verification.
        When None, quotes are not validated and footnotes are skipped.
    paper_type:
        Optional ``prompts.PAPER_TYPES`` value. When provided, iterates
        ``headers_for(paper_type)`` so a correction notice renders just
        its 4 sections rather than 12. None or unknown falls back to
        the 12-section default (backwards compatible).
    """
    today_iso = today_iso or _dt.date.today().isoformat()
    payload = payload or {}
    fm = payload.get("frontmatter") or {}
    sections = payload.get("sections") or {}

    canonicalised: dict[str, str] = {}
    new_candidates: list[str] = []
    warnings: list[str] = []

    source_normalised = _normalise_for_quote_match(source_text or "")

    # Frontmatter
    fm_lines, fm_warnings = _frontmatter_lines(fm, today_iso=today_iso)
    warnings.extend(fm_warnings)

    # Pick the heading list per paper type. None / unknown -> 12-section default.
    if paper_type:
        section_names = headers_for(paper_type)
    else:
        section_names = required_headers()

    body_chunks: list[str] = []
    # Display names Stage A reported in the structured `entities[]` array. Used
    # to cross-check which Important Entities bullets are genuine entities.
    entity_names = {
        str((e or {}).get("text", "")).strip()
        for e in (payload.get("entities") or [])
        if isinstance(e, dict) and str((e or {}).get("text", "")).strip()
    }
    for name in section_names:
        raw_body = _section_body(
            sections.get(name), name=name,
            source_normalised=source_normalised, warnings=warnings,
        )
        if name == ENTITY_SECTION and raw_body != NOT_REPORTED:
            raw_body, n_linked = _linkify_entity_bullets(raw_body, entity_names)
            if n_linked:
                warnings.append(
                    f"section {name!r}: wikilinked {n_linked} bare entity bullet(s)"
                )
        rewritten = _canonicalise_wikilinks(
            raw_body, vocab_index, canonicalised, new_candidates,
        )
        body_chunks.append(f"## {name}\n{rewritten}\n")
        if raw_body == NOT_REPORTED and name in sections:
            warnings.append(f"section {name!r} fell back to NOT_REPORTED")

    md_parts = ["---"] + fm_lines + ["---", ""] + body_chunks
    if paper_name:
        md_parts.append(f"---\n**Source PDF:** `data/{paper_name}.pdf`\n")

    md = "\n".join(md_parts).rstrip() + "\n"

    return RenderResult(
        markdown=md,
        warnings=warnings,
        canonicalised=canonicalised,
        new_candidates=new_candidates,
    )


__all__ = [
    "RenderResult",
    "render_summary_from_json",
]
