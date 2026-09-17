"""Single source of truth for the wiki-summary contract.

Everything that needs to know "what does a valid summary look like" should
import from this module:

* `REQUIRED_SECTIONS` — ordered list of the 12 required H2 sections, with
  per-section rules (max words, whether the section is allowed to fall back
  to "Not reported in this paper.", and a short prose rule the prompt
  builder can quote).
* `LENIENT_REQUIRED_HEADERS` — the 5-section subset
  `genai_client.validate_structured_summary` historically enforced. Kept
  for backwards compatibility on the existing on-disk corpus (Task 2 will
  add a strict variant alongside it).
* `FRONTMATTER_KEYS` — typed schema for the YAML frontmatter every wiki
  summary must carry.
* `PAPER_TYPES` — the enum-like tuple of paper types the Task 5
  pre-classifier picks from.
* Helpers: `required_headers()`, `lenient_required_headers()`,
  `format_required_headings_block()`, `lint_summary()`.

This module deliberately has **no I/O and no third-party dependencies**
beyond the standard library, so it can be imported from tests, prompt
builders, validators, and CLI scripts without dragging Vertex/genai into
the import graph. Tests stub `genai_client` aggressively and we want this
module to remain stub-free.

Versioning: bump `FORMAT_VERSION` whenever a backwards-incompatible change
to `REQUIRED_SECTIONS` or `FRONTMATTER_KEYS` lands so downstream tools can
detect old vs new output formats.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from molecular_roles import (
    EVIDENCE_DIRECTNESS,
    MOLECULAR_ROLES,
    ontology_prompt_block,
)

MOLECULAR_ROLE_PROMPT = ontology_prompt_block()

# ---------------------------------------------------------------------------
# Format version
# ---------------------------------------------------------------------------

#: Bump on any backwards-incompatible change to REQUIRED_SECTIONS or
#: FRONTMATTER_KEYS. Task 12 will surface this as a `format_version`
#: frontmatter key on newly-emitted summaries.
FORMAT_VERSION = 2


# ---------------------------------------------------------------------------
# Paper types
# ---------------------------------------------------------------------------

#: Tuple chosen so iteration order matches the Task 5 classifier prompt.
#: `primary_research` is the safe default on parse failure.
PAPER_TYPES: tuple[str, ...] = (
    "primary_research",
    "review",
    "methods_paper",
    "perspective",
    "correction_notice",
    "conference_proceedings",
    "other",
)

#: The least-disruptive default used by the classifier on parse failure.
DEFAULT_PAPER_TYPE = "primary_research"


# ---------------------------------------------------------------------------
# Section contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SectionRule:
    """One required H2 section in the wiki summary contract.

    Attributes
    ----------
    name:
        Heading text exactly as it must appear after the ``## `` marker.
        Comparisons are case-insensitive but the heading must otherwise be
        a verbatim match (no leading numbers, no bold, no extra characters).
    max_words:
        Soft cap surfaced in the prompt. ``0`` means "no cap".
    required:
        Whether the section MUST appear. All 12 default sections are
        required today; correction-notice / review variants in Task 8 will
        flip this on a per-section basis.
    in_lenient_subset:
        Whether the historically-permissive 5-section validator in
        ``genai_client.validate_structured_summary`` enforces this section.
        Used to keep backwards compatibility on the existing corpus.
    rule:
        One-line prose rule quoted verbatim by the prompt builder. Keep
        these short; per-paper-type extraction targets live in Task 8's
        ``sections_for(paper_type)`` variant table, not here.
    """

    name: str
    max_words: int = 0
    required: bool = True
    in_lenient_subset: bool = False
    rule: str = ""

    @property
    def heading(self) -> str:
        """The full Markdown H2 heading line, e.g. ``## Title & Metadata``."""
        return f"## {self.name}"


#: Ordered list of the 12 required H2 sections. **Authoritative.**
#: Both `validation.py` and `genai_client.validate_structured_summary`
#: derive their checks from this list (Task 1).
REQUIRED_SECTIONS: tuple[SectionRule, ...] = (
    SectionRule(
        name="Title & Metadata",
        in_lenient_subset=True,
        rule="Full paper title, authors, year, journal, DOI.",
    ),
    SectionRule(
        name="Abstract Summary",
        max_words=150,
        in_lenient_subset=True,
        rule="Faithful prose summary of the paper's abstract.",
    ),
    SectionRule(
        name="Introduction & Background",
        max_words=250,
        rule="Frame the problem and prior art the authors cite.",
    ),
    SectionRule(
        name="Key Concepts & Theory",
        max_words=200,
        rule=(
            "Define central scientific concepts. You MUST format each concept "
            "as a bullet point starting with '- **[[Concept Name]]**: Definition.' "
            "wrapping the concept name in both bold stars and double brackets. "
            "Preserve natural capitalization, punctuation, and spacing for the concept name (e.g., "
            "'- **[[Seed Dormancy]]**: Definition.' instead of '- **[[seed-dormancy]]**: Definition.'). "
            "Do NOT use slugified/kebab-case formats inside the brackets. Avoid vague, generic, or common terms."
        ),
    ),
    SectionRule(
        name="Important Entities",
        rule=(
            "Exhaustive list of specific genes, proteins, organisms, cultivars, and tools. "
            "Preserve natural capitalization, punctuation, and spacing (e.g., '[[CIMMYT]]' instead of '[[cimmyt]]', "
            "'[[AC Domain]]' instead of '[[ac-domain]]', '[[Triticum aestivum]]' instead of '[[triticum-aestivum]]'). "
            "Do NOT use slugified/kebab-case formats inside the double brackets. "
            "Organize them explicitly into categories using these bulleted subheadings: "
            "'* **Genes/Proteins**:', '* **Organisms**:', '* **Tools/Techniques/Software**:'. "
            "Do NOT list academic paper citations, authors, or study references here. "
            "Avoid generic nouns (like '[[chromosome-bin]]', '[[gene]]', '[[protein]]') or duplicate synonyms."
        ),
    ),
    SectionRule(
        name="Methods & Experimental Design",
        max_words=300,
        in_lenient_subset=True,
        rule="Population, sample sizes, statistical tests, software with versions.",
    ),
    SectionRule(
        name="Key Results & Data",
        max_words=400,
        in_lenient_subset=True,
        rule=(
            "Quantitative results with units. Reference tables/equations by "
            "their {{TAB_n_<paper>}} / {{EQ_n_<paper>}} ID rather than "
            "transcribing them."
        ),
    ),
    SectionRule(
        name="Mechanistic Insights",
        max_words=300,
        rule="Cause-and-effect chain the authors draw from the data.",
    ),
    SectionRule(
        name="Conclusions & Implications",
        max_words=200,
        in_lenient_subset=True,
        rule="What the authors claim follows from the results.",
    ),
    SectionRule(
        name="Limitations & Caveats",
        max_words=200,
        rule=(
            "Authors' own caveats plus any truncation/coverage warnings the "
            "ingestion pipeline emits."
        ),
    ),
    SectionRule(
        name="Contradictory Findings",
        max_words=200,
        rule=(
            "Results that conflict with prior studies or are internally "
            "inconsistent across the paper's own experiments/genotypes/"
            "environments. 'Not reported in this paper.' if none."
        ),
    ),
    SectionRule(
        name="Outdated Models",
        max_words=150,
        rule=(
            "Theories, classifications, or methods the authors flag as "
            "superseded, oversimplified, or in need of revision. 'Not reported "
            "in this paper.' if none."
        ),
    ),
    SectionRule(
        name="Under-Researched Populations",
        max_words=150,
        rule=(
            "Germplasm, genetic backgrounds, environments, or conditions the "
            "authors note are understudied or untested. 'Not reported in this "
            "paper.' if none."
        ),
    ),
    SectionRule(
        name="Future Directions",
        max_words=150,
        rule="Authors' stated next steps, not your speculation.",
    ),
    SectionRule(
        name="Key References to Follow Up",
        rule="3-7 references the authors lean on most heavily.",
    ),
)


def required_headers() -> list[str]:
    """Return the 15 heading names in canonical order.

    Backwards-compatible drop-in replacement for the historical
    `validation.REQUIRED_HEADERS` list.
    """
    return [s.name for s in REQUIRED_SECTIONS]


def lenient_required_headers() -> list[str]:
    """Return the 5-section subset enforced by the historical lenient validator.

    Used by `genai_client.validate_structured_summary` for backwards
    compatibility. Strict validation goes through `required_headers()`.
    """
    return [s.name for s in REQUIRED_SECTIONS if s.in_lenient_subset]


def section_by_name(name: str) -> SectionRule | None:
    """Look up a SectionRule by its heading text (case-insensitive)."""
    needle = name.strip().lower()
    for s in REQUIRED_SECTIONS:
        if s.name.lower() == needle:
            return s
    return None


def format_required_headings_block() -> str:
    """Render the required-headings block exactly as the prompt should see it.

    Used by Task 3's `build_main_prompt` so the inline 12-heading lists in
    `generate_paper_summary` and `repair_paper_summary` collapse into a
    single string sourced from `REQUIRED_SECTIONS`.
    """
    return "\n".join(s.heading for s in REQUIRED_SECTIONS)


# ---------------------------------------------------------------------------
# Frontmatter schema
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FrontmatterKey:
    """One typed key in the wiki-summary YAML frontmatter."""

    name: str
    yaml_type: str  # "string", "list[string]", "int", "date"
    required: bool = True
    nullable: bool = False
    description: str = ""


#: Typed schema for the YAML frontmatter every wiki summary must carry.
#: ``nullable=True`` keys may be emitted as JSON ``null`` (which the Stage B
#: renderer in Task 7 will turn into "Not reported in this paper." or omit).
FRONTMATTER_KEYS: tuple[FrontmatterKey, ...] = (
    FrontmatterKey("tags", "list[string]", required=True,
                   description="Controlled-vocabulary tags from existing wiki entities/concepts."),
    FrontmatterKey("type", "string", required=True,
                   description="Always 'source' for ingested papers."),
    FrontmatterKey("date_created", "date", required=True,
                   description="ISO YYYY-MM-DD; today's date on first creation."),
    FrontmatterKey("date_updated", "date", required=True,
                   description="ISO YYYY-MM-DD; today's date on every regeneration."),
    FrontmatterKey("source_count", "int", required=True,
                   description="Always 1 for a single-paper summary."),
    FrontmatterKey("doi", "string", required=True, nullable=True,
                   description="Verified DOI from PDF metadata. null if genuinely unknown."),
    FrontmatterKey("authors", "string", required=True, nullable=True,
                   description="\"Last1 et al.\" form, or null if not extractable."),
    FrontmatterKey("year", "int", required=True, nullable=True,
                   description="4-digit publication year, or null."),
    FrontmatterKey("journal", "string", required=True, nullable=True,
                   description="Journal/venue name, or null."),
)


def required_frontmatter_keys() -> list[str]:
    """Return the names of all required frontmatter keys."""
    return [k.name for k in FRONTMATTER_KEYS if k.required]


# ---------------------------------------------------------------------------
# Heading regex
# ---------------------------------------------------------------------------

#: Strict heading regex template. Used by both `validation.SummaryValidator`
#: and (Task 2) the strict `validate_structured_summary` in genai_client.
#: Anchored to ^ and $ to refuse numbered headings (`## 1. Title`), bolded
#: headings (`## **Title**`), missing-space headings (`##Title`), and any
#: extra characters.
STRICT_HEADING_PATTERN = r"(?im)^##\s+{name}\s*$"


def strict_heading_regex(name: str) -> re.Pattern[str]:
    """Compile the strict heading regex for one section name."""
    return re.compile(STRICT_HEADING_PATTERN.format(name=re.escape(name)))


# ---------------------------------------------------------------------------
# Lint report
# ---------------------------------------------------------------------------

@dataclass
class LintReport:
    """Rich validator output. Used by `lint_summary()` and Task 7's
    pipeline integration.

    Returns the `validation.SummaryValidator` result (which already
    computes a 0-100 score) wrapped in a stable shape that doesn't
    require importing `validation` directly.
    """

    valid: bool
    score: float  # 0-100
    missing_sections: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    wikilink_count: int = 0
    has_frontmatter: bool = False

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "score": self.score,
            "missing_sections": list(self.missing_sections),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "wikilink_count": self.wikilink_count,
            "has_frontmatter": self.has_frontmatter,
        }


def lint_summary(summary_text: str) -> LintReport:
    """Run the rich validator and return a `LintReport`.

    Implementation note: this delegates to `validation.SummaryValidator`,
    but is exposed here so callers don't have to know about that module.
    Imported lazily so that test stubs of `genai_client`/`config` keep
    working — `validation` itself has no third-party imports, but we still
    keep this lazy for symmetry with the rest of the prompts module.
    """
    # Lazy import to avoid a hard cycle at module import time. validation.py
    # itself imports REQUIRED_HEADERS from this module at import time, so a
    # top-level `from validation import ...` would create a circular import.
    from validation import SummaryValidator

    result = SummaryValidator().validate(summary_text)
    wikilinks = re.findall(r"\[\[(.*?)\]\]", summary_text)
    has_frontmatter = bool(re.search(r"^---\n", summary_text, re.MULTILINE))
    return LintReport(
        valid=result.valid,
        score=float(result.score),
        missing_sections=list(result.missing_sections),
        errors=list(result.errors),
        warnings=list(result.warnings),
        wikilink_count=len(wikilinks),
        has_frontmatter=has_frontmatter,
    )


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Prompt builders (Task 3)
# ---------------------------------------------------------------------------

#: Maximum number of table captions listed in the prompt. Beyond this we
#: append "...and N more" to keep prompt size bounded for review-style
#: papers with many tables. From the Task 6 performance budget.
MAX_TABLE_CAPTIONS_IN_PROMPT = 20

#: Truncation threshold matching pdf_extractor._truncate_for_context.
#: Source markdown longer than this triggers the chunk-and-merge path (Task 10)
#: instead of the single-call path. Raised to 300,000 for Qwen3.5-397B-A17B
#: on hcnsec.cn API, which supports functional reasoning up to 500,000 chars.
TRUNCATION_THRESHOLD_CHARS = 300_000


def _metadata_block(api_metadata: dict | None, extracted_doi: str | None) -> str:
    """Render the verified metadata block injected at the top of the prompt body.

    If `api_metadata` is provided, the model is instructed to use those exact
    values verbatim. If only `extracted_doi` is provided, it uses that for DOI
    and extracts the rest. When None, the model is told to extract a DOI
    only if one is unambiguously present in the source, else emit JSON
    null in the frontmatter.
    """
    if api_metadata:
        authors = api_metadata.get('authors', [])
        if len(authors) > 1:
            authors_str = f'"{authors[0].split(",")[0]} et al."'
        elif authors:
            authors_str = f'"{authors[0].split(",")[0]}"'
        else:
            authors_str = 'null'
            
        return (
            "VERIFIED METADATA FROM PDF (authoritative — use these exact values):\n"
            f"  doi: {api_metadata.get('doi') or 'null'}\n"
            f"  authors: {authors_str}\n"
            f"  year: {api_metadata.get('year') or 'null'}\n"
            f"  journal: \"{api_metadata.get('journal') or 'null'}\"\n"
            "  → Copy these values verbatim into the frontmatter. Do NOT invent or "
            "modify them.\n"
        )
    elif extracted_doi:
        return (
            "VERIFIED METADATA FROM PDF (authoritative — use these exact values):\n"
            f"  doi: {extracted_doi}\n"
            "  → Copy this DOI verbatim into the frontmatter. Do NOT invent or "
            "modify it.\n"
        )
    return (
        "VERIFIED METADATA FROM PDF: none.\n"
        "  → If a DOI is unambiguously present in the source text, extract it. "
        "Otherwise emit `doi: null` in the frontmatter. Do NOT invent a DOI.\n"
    )


def _tables_block(tables: list[dict] | None, *, paper_stem: str | None = None) -> str:
    """Render the table-of-tables awareness block (Task 6).

    `tables` is the list from the slim sidecar JSON
    (raw/papers/<paper>_data_objects.json), each entry shaped like
    ``{"id": "TAB_1_<paper>", "caption": "...", "page": N}``. The model
    is instructed to reference these by their ``{{...}}`` ID rather than
    transcribing their full contents into prose.

    Caption list is capped at MAX_TABLE_CAPTIONS_IN_PROMPT to keep
    prompts bounded on review-style papers with many tables.
    """
    if not tables:
        return "TABLES IN THIS PAPER: none detected.\n"

    n = len(tables)
    lines = [f"TABLES IN THIS PAPER ({n}):"]
    cap = MAX_TABLE_CAPTIONS_IN_PROMPT
    for t in tables[:cap]:
        tid = t.get("id") or "TAB_?"
        caption = (t.get("caption") or "").strip().replace("\n", " ")
        page = t.get("page")
        page_part = f" (p.{page})" if page else ""
        cap_part = f": {caption[:200]}" if caption else ""
        lines.append(f"  - {{{{{tid}}}}}{page_part}{cap_part}")
    if n > cap:
        lines.append(f"  ...and {n - cap} more (see sidecar JSON for full list)")
    lines.append(
        "Reference these by their {{TAB_n_<paper>}} ID inside Key Results & "
        "Data; do NOT transcribe their full contents into prose."
    )
    return "\n".join(lines) + "\n"


def _equations_block(equations: list[dict] | None) -> str:
    """Render the equation-awareness block (Task 6).

    Equations don't usually have captions, so we just enumerate IDs and
    instruct the model to reference them when discussing the underlying
    mathematics.
    """
    if not equations:
        return ""
    n = len(equations)
    ids = ", ".join(f"{{{{{e.get('id') or 'EQ_?'}}}}}" for e in equations[:30])
    suffix = f"...({n - 30} more)" if n > 30 else ""
    return (
        f"EQUATIONS IN THIS PAPER ({n}):\n"
        f"  IDs: {ids}{suffix}\n"
        "Reference equations by their {{EQ_n_<paper>}} ID where the "
        "underlying mathematics matters; do not transcribe.\n"
    )


def _truncation_block(was_truncated: bool, original_len: int = 0) -> str:
    """Render the truncation transparency warning (Task 6).

    When the source markdown was truncated by ``_truncate_for_context``,
    the model is told the tail of the document is missing so it can be
    explicit in Limitations & Caveats rather than silently guessing.
    """
    if not was_truncated:
        return ""
    return (
        "INPUT TRUNCATION WARNING:\n"
        f"  The source text was truncated to {TRUNCATION_THRESHOLD_CHARS:,} "
        f"chars (original ~{original_len:,} chars). Discussion / References / "
        "tail sections may be incomplete. Mention this in `Limitations & "
        "Caveats` and do NOT speculate about the missing tail.\n"
    )


_FRONTMATTER_RULES = """\
Frontmatter rules:
  tags          — list of 2-6 tags from the controlled vocabulary (existing
                  wiki entity / concept slugs preferred). Use [] only if the
                  paper is too sparse to tag; do NOT emit literal placeholders.
  type          — always the literal string "source".
  date_created  — today's date as YYYY-MM-DD.
  date_updated  — today's date as YYYY-MM-DD.
  source_count  — always the integer 1.
  doi           — string from VERIFIED METADATA above when provided, else
                  null (no quotes around null).
  authors       — string in "Last1 et al." form, or null when not extractable.
  year          — 4-digit integer, or null when not extractable.
  journal       — string with full venue name, or null when not extractable.

DO NOT emit literal placeholders like `10.xxxx/xxxxx`, `Last1 et al.`,
`Journal Name`, or `[comma, separated, tags]`. Use a real value or null.\
"""


def build_main_prompt(
    full_text: str,
    *,
    extracted_doi: str | None = None,
    api_metadata: dict | None = None,
    gene_registry_text: str = "",
    candidate_tags: list[str] | None = None,
    candidate_wikilinks: list[str] | None = None,
    paper_type: str = DEFAULT_PAPER_TYPE,
    today_iso: str | None = None,
    tables: list[dict] | None = None,
    equations: list[dict] | None = None,
    source_was_truncated: bool = False,
    original_text_len: int = 0,
) -> str:
    """Build the main extraction prompt.

    Single source of truth for the prompt structure (Task 3 of the
    overhaul plan). Both ``generate_paper_summary`` and downstream tools
    consume from this builder.

    Parameters
    ----------
    full_text:
        Source markdown produced by OpenDataLoader (already truncated by
        the caller to ~150 k chars).
    extracted_doi:
        Verified DOI from PDF metadata, if any. Injected verbatim into
        the prompt body so the model treats it as authoritative.
    candidate_tags:
        Top-K candidate tags from the wiki vocabulary index (Task 4).
        Empty list / None for now; later tasks fill this in.
    candidate_wikilinks:
        Top-K candidate canonical wikilink slugs (Task 4). Same caveat.
    paper_type:
        One of ``PAPER_TYPES``. Currently informational only; Task 8 will
        switch to per-paper-type section scaffolds.
    today_iso:
        Today's date in YYYY-MM-DD form. Defaults to "today" when None,
        which the prompt then asks the model to compute itself.
    tables, equations:
        Slim sidecar entries from
        ``raw/papers/<paper>_data_objects.json`` (Task 6). When provided
        the prompt lists table captions and equation IDs and instructs
        the model to reference them by ``{{TAB_n_<paper>}}`` /
        ``{{EQ_n_<paper>}}`` rather than transcribing.
    source_was_truncated:
        True when ``len(full_raw_text) > TRUNCATION_THRESHOLD_CHARS``
        before truncation. Triggers the truncation warning block so the
        model can flag the missing tail in Limitations & Caveats.
    original_text_len:
        Length of the un-truncated raw text, used in the warning block.
    """
    candidate_tags = candidate_tags or []
    candidate_wikilinks = candidate_wikilinks or []
    paper_type = paper_type if paper_type in PAPER_TYPES else DEFAULT_PAPER_TYPE
    date_clause = (
        f'today\'s date is {today_iso}; use it for date_created and date_updated.'
        if today_iso else
        "use today's date in YYYY-MM-DD format for date_created and date_updated."
    )

    headings_block = format_required_headings_block()
    section_rules_block = format_section_rules_block_for(paper_type)

    cand_tags_block = (
        "Candidate tags (use these slugs verbatim if applicable; you may also "
        "introduce new ones):\n  " + ", ".join(candidate_tags)
        if candidate_tags else
        "Candidate tags: none — pick 2-6 short, lower-kebab-case tags yourself."
    )
    cand_wl_block = (
        "Candidate canonical wikilinks (existing wiki pages — prefer these "
        "exact slugs when wrapping in [[...]]):\n  " + ", ".join(candidate_wikilinks)
        if candidate_wikilinks else
        "Candidate wikilinks: none injected — emit [[Display Text]] for new entities."
    )

    # Task 6 blocks. Each helper returns "" when its input is empty so
    # the prompt collapses cleanly when no sidecar / no truncation.
    tables_text = _tables_block(tables)
    equations_text = _equations_block(equations)
    truncation_text = _truncation_block(source_was_truncated, original_text_len)

    # Task 8 — domain-specific extraction targets. Empty for unknown
    # paper types so the prompt collapses cleanly.
    extract_targets_text = _extract_targets_block(paper_type)

    gene_registry_block = (
        f"GENE REGISTRY (Standard Nomenclature):\n{gene_registry_text}\n"
        "→ When discussing genes or loci, you MUST use the standard names exactly as they appear in the Gene Registry above. Do not invent new names or use aliases.\n\n"
    ) if gene_registry_text else ""

    return f"""\
You are an expert scientific researcher in plant genetics, wheat breeding,
CRISPR genome editing, and synthetic biology. Produce a highly structured
Markdown summary of the paper below for an Obsidian-flavoured research wiki.

PAPER TYPE: {paper_type}

{_metadata_block(api_metadata, extracted_doi)}
{gene_registry_block}{tables_text}{equations_text}{truncation_text}{cand_tags_block}

{cand_wl_block}

{extract_targets_text}{MOLECULAR_ROLE_PROMPT}

OUTPUT CONTRACT
Your response MUST start with a YAML frontmatter block and contain every
required H2 section in the exact order shown. Do NOT wrap the response in
a code block — start the raw text directly with `---`.

Frontmatter ({date_clause}):
---
tags: [...]
type: source
date_created: YYYY-MM-DD
date_updated: YYYY-MM-DD
source_count: 1
doi: ...
authors: ...
year: ...
journal: ...
---

{_FRONTMATTER_RULES}

Required H2 headings (exact text, exact order, no numbers/bold/extra chars):
{headings_block}

Section-by-section content and formatting rules:
{section_rules_block}

CRITICAL RULES
- ZERO HALLUCINATION: extract ONLY facts explicitly present in the source
  text. Do not use any outside knowledge. If a section is unsupported,
  write EXACTLY: `Not reported in this paper.`
- Preserve hedged language verbatim ("suggests", "may indicate", etc).
- NEVER wrap your response in a code block (no ```markdown, no ```, nothing).
  Start the raw output directly with `---`.
- When the source markdown contains placeholders like `{{{{TAB_n_<paper>}}}}` or `{{{{EQ_n_<paper>}}}}`, REFERENCE them by ID inside Key Results & Data rather than transcribing their contents.

WIKILINK FORMAT RULES (CRITICAL — do NOT skip)
- Every concept name in `## Key Concepts & Theory` MUST be in [[double brackets]].
  Format: `- **[[Concept Name]]**: one-sentence definition.`
  MINIMUM: 3 wikilinked concepts. More is better.
- Every entity in `## Important Entities` MUST be in [[double brackets]].
  Use natural capitalization exactly as the paper writes it (e.g. `[[Triticum aestivum]]`, `[[CRISPR-Cas9]]`, not `[[triticum-aestivum]]`).
  MINIMUM: 5 wikilinked entities total. More is better.
- Do NOT leave `## Key Concepts & Theory` or `## Important Entities` empty or with plain text only.

FORMAT EXAMPLE — Key Concepts & Theory:
- **[[Seed Dormancy]]**: A physiological state in which seeds fail to germinate under otherwise favorable conditions.
- **[[Pre-Harvest Sprouting]]**: Premature germination of grain on the spike before harvest, reducing grain quality.
- **[[Abscisic Acid (ABA)]]**: A plant hormone that promotes dormancy and suppresses premature germination.
- **[[Quantitative Trait Loci (QTL)]]**: Genomic regions associated with continuous variation in a quantitative trait.

FORMAT EXAMPLE — Important Entities:
* **Genes/Proteins**:
  - [[TaMFT]] — wheat MOTHER OF FT AND TFL1 homolog
  - [[VP1]] — viviparous1 ABI3-class transcription factor regulating ABA signaling
  - [[R genes]] — dominant genes controlling red seed coat pigmentation
* **Organisms**:
  - [[Triticum aestivum]] — hexaploid bread wheat
  - [[Arabidopsis thaliana]] — model dicot plant used for gene function studies
* **Tools/Techniques/Software**:
  - [[DArT markers]] — Diversity Arrays Technology genotyping platform
  - [[TASSEL]] — software for association mapping of complex traits
  - [[STRUCTURE]] — software for inferring population genetic structure

PER-SECTION SOFT LIMITS (words):
- Abstract Summary: 150
- Introduction & Background: 250
- Key Concepts & Theory: 200
- Methods & Experimental Design: 300
- Key Results & Data: 400
- Mechanistic Insights: 300
- Conclusions & Implications: 200
- Limitations & Caveats: 200
- Contradictory Findings: 200
- Outdated Models: 150
- Under-Researched Populations: 150
- Future Directions: 150

SOURCE TEXT
{full_text}
"""


def build_repair_prompt(
    full_text: str,
    draft_summary: str,
    missing_sections: list[str],
    *,
    extracted_doi: str | None = None,
    api_metadata: dict | None = None,
    gene_registry_text: str = "",
) -> str:
    """Build the repair prompt for an incomplete summary.

    Mirrors `build_main_prompt` for the metadata block + headings list
    but asks the model to PRESERVE existing correct content and ADD the
    missing sections rather than regenerate from scratch.
    """
    missing_list = ", ".join(missing_sections) if missing_sections else "None"
    headings_block = format_required_headings_block()

    gene_registry_block = (
        f"GENE REGISTRY (Standard Nomenclature):\n{gene_registry_text}\n"
        "→ When discussing genes or loci, you MUST use the standard names exactly as they appear in the Gene Registry above. Do not invent new names or use aliases.\n\n"
    ) if gene_registry_text else ""

    return f"""\
You are revising an existing structured summary so it passes a strict
section validator. Preserve all correct text already present in the
draft; add only the missing sections; return the COMPLETE revised
markdown document.

{_metadata_block(api_metadata, extracted_doi)}
{gene_registry_block}The draft is missing these required sections: {missing_list}

Rules:
- Use the exact required H2 headings and order below. No numbers, no
  bold, no extra characters.
- If a section is unsupported by the source text, write
  `Not reported in this paper.` inside it.
- Do not add preface or closing commentary outside the required sections.
- Do NOT emit literal frontmatter placeholders. If a metadata field is
  unknown, emit JSON null.

Required H2 headings:
{headings_block}

Current draft:
{draft_summary}

Source text:
{full_text}
"""


def build_hallucination_repair_prompt(
    full_text: str,
    draft_summary: str,
    unverified_sentences: list[str],
    confidence: float,
) -> str:
    """Build a repair prompt that targets hallucinated / unverifiable sentences.

    The prompt tells the model to replace flagged sentences with EXACT
    source sentences (no rephrasing) or delete them entirely if no
    source sentence conveys the same fact.
    """
    unverified_list = "\n".join(
        f"{i}. {s}" for i, s in enumerate(unverified_sentences, start=1)
    )

    return f"""\
You are revising a structured research-paper summary to eliminate
hallucinated content.  The summary was generated from a source text
but some sentences do NOT appear verbatim in that source.

HALLUCINATION CONFIDENCE: {confidence:.0%} ({len(unverified_sentences)} sentences not found in source)

The following sentences in your summary could NOT be found as exact
sentences in the source paper.  Replace each one with an EXACT sentence
copied directly from the source text — do NOT rephrase, summarize, or
modify the wording:

{unverified_list}

CRITICAL RULES
- For every sentence listed above, find the EXACT source sentence that
  conveys the same fact and use it verbatim.
- If the source text contains NO sentence conveying an equivalent fact,
  delete the sentence entirely and replace with:
  ``Not reported in this paper.``
- Do NOT change any other sentences — keep all verified content as-is.
- Preserve ALL required H2 headings, YAML frontmatter, `[[wikilinks]]`,
  and section structure exactly as in the draft.
- Return the COMPLETE revised markdown document (frontmatter + all
  sections).  Do NOT add any preface or commentary.

Current draft:
{draft_summary}

Source text:
{full_text}
"""


__all__ = [
    "FORMAT_VERSION",
    "PAPER_TYPES",
    "DEFAULT_PAPER_TYPE",
    "SectionRule",
    "REQUIRED_SECTIONS",
    "FrontmatterKey",
    "FRONTMATTER_KEYS",
    "STRICT_HEADING_PATTERN",
    "LintReport",
    "required_headers",
    "lenient_required_headers",
    "section_by_name",
    "format_required_headings_block",
    "required_frontmatter_keys",
    "strict_heading_regex",
    "lint_summary",
    "build_main_prompt",
    "build_repair_prompt",
    "build_hallucination_repair_prompt",
    "MAX_TABLE_CAPTIONS_IN_PROMPT",
    "TRUNCATION_THRESHOLD_CHARS",
    "SUMMARY_JSON_SCHEMA",
    "build_stage_a_prompt",
    "NOT_REPORTED",
    "sections_for",
    "headers_for",
    "extract_targets_for",
    "MAX_CHUNK_CHARS",
    "MIN_CHUNK_CHARS",
    "chunk_by_sections",
    "build_chunk_summary_prompt",
    "aggregate_chunk_intermediates",
    "CHUNK_SUMMARY_SCHEMA",
]


# ---------------------------------------------------------------------------
# Task 10 — hierarchical summarisation for long papers
# ---------------------------------------------------------------------------

#: Soft cap on per-chunk character count fed to the chunk-summariser. The
#: docs/ingestion_prompt_overhaul_plan.md performance budget says 30k.
MAX_CHUNK_CHARS = 30_000

#: Below this, chunks are merged with their predecessor / successor so the
#: summariser doesn't waste an LLM call on a 200-byte paragraph.
MIN_CHUNK_CHARS = 1_500


_HEADING_LINE_RE = re.compile(r"(?m)^(#{2,3})\s+(.+?)\s*$")


def chunk_by_sections(
    md: str,
    *,
    max_chars: int = MAX_CHUNK_CHARS,
    min_chars: int = MIN_CHUNK_CHARS,
) -> list[tuple[str, str]]:
    """Split `md` into ``(heading, body)`` chunks bounded by char count.

    1. Splits at every H2/H3 boundary. Content before the first heading
       becomes a chunk titled ``"(preface)"`` (often metadata / TOC).
    2. Merges adjacent chunks whose combined size stays ≤ ``max_chars``
       and whose individual size is < ``min_chars``. This squashes
       1-paragraph subsection chunks into the surrounding section.
    3. If a single section's body still exceeds ``max_chars``, it's
       split into N equal-ish slices keyed by the same heading
       (``heading``, ``heading (cont. 2/N)``, …).

    Returns
    -------
    A list of ``(heading, body)`` tuples in document order. Always
    non-empty when `md` is non-empty.
    """
    if not md:
        return []

    # 1) Split at H2/H3 boundaries.
    matches = list(_HEADING_LINE_RE.finditer(md))
    raw_chunks: list[tuple[str, str]] = []
    if not matches or matches[0].start() > 0:
        preface = md[: matches[0].start()] if matches else md
        if preface.strip():
            raw_chunks.append(("(preface)", preface.rstrip()))
    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        body = md[body_start:body_end].strip()
        raw_chunks.append((heading, body))

    if not raw_chunks:
        return []

    # 2) Merge tiny adjacent chunks while staying under max_chars.
    merged: list[tuple[str, str]] = []
    for heading, body in raw_chunks:
        if (merged
                and len(body) < min_chars
                and len(merged[-1][1]) + len(body) + len(heading) + 4 <= max_chars):
            prev_h, prev_b = merged[-1]
            joined = f"{prev_b}\n\n## {heading}\n{body}".rstrip()
            merged[-1] = (prev_h, joined)
        else:
            merged.append((heading, body))

    # 3) Split oversized chunks into N slices.
    final: list[tuple[str, str]] = []
    for heading, body in merged:
        if len(body) <= max_chars:
            final.append((heading, body))
            continue
        n = (len(body) + max_chars - 1) // max_chars
        slice_size = (len(body) + n - 1) // n
        for k in range(n):
            slc = body[k * slice_size : (k + 1) * slice_size]
            label = heading if k == 0 else f"{heading} (cont. {k + 1}/{n})"
            final.append((label, slc.strip()))

    return final


# ---------------------------------------------------------------------------
# Per-chunk extraction prompt
# ---------------------------------------------------------------------------

#: Tight schema for the per-chunk summariser. Smaller than
#: SUMMARY_JSON_SCHEMA on purpose — chunk summaries feed the final
#: Stage A call, so we want them dense and structured but not full
#: 12-section.
CHUNK_SUMMARY_SCHEMA = {
    "type": "object",
    "required": ["heading", "key_points", "entities", "data_points"],
    "properties": {
        "heading": {"type": "string"},
        "key_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-7 single-sentence factual claims.",
        },
        "entities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Genes / proteins / cultivars / methods named in this chunk.",
        },
        "data_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Quantitative facts: QTL names + LOD, p-values, n=, effect sizes, "
                "table/equation IDs as {{TAB_n_<paper>}}/{{EQ_n_<paper>}}."
            ),
        },
    },
}


def build_chunk_summary_prompt(heading: str, body: str) -> str:
    """Tight prompt for one section/chunk → structured JSON."""
    import json as _json
    return f"""\
Summarise the SECTION below into a JSON object conforming to this schema.
Respond with a SINGLE JSON object containing the actual data extracted from the text. Do NOT output the JSON schema definition itself. Your response must be a valid instance of the schema, populated with the extracted facts.

{_json.dumps(CHUNK_SUMMARY_SCHEMA, indent=2)}

Rules:
- Extract ONLY facts present in the section text. No outside knowledge.
- Preserve hedged language verbatim ("suggests", "may indicate").
- For data_points, keep numbers and units exactly as reported.
- Reference table/equation placeholders by ID, do not transcribe contents.
- Respond with the JSON object only — no Markdown, no prose, no fences.

SECTION HEADING: {heading}

SECTION BODY:
{body}
"""


def aggregate_chunk_intermediates(intermediates: list[dict]) -> str:
    """Concatenate N chunk-summary JSONs into the synthetic input the
    Stage A prompt sees instead of the raw text.

    Stage A is told upfront this is "pre-summarised over N chunks" so
    the model knows to reason over the curated points rather than
    inventing detail. Returns a Markdown-flavoured block.
    """
    if not intermediates:
        return ""

    parts: list[str] = [
        "PRE-SUMMARISED CHUNKS (the source PDF was too long to fit in one "
        f"prompt; reasoning is over {len(intermediates)} per-section "
        "summaries below):",
        "",
    ]
    for i, item in enumerate(intermediates, 1):
        if not isinstance(item, dict):
            continue
        heading = item.get("heading") or f"chunk {i}"
        parts.append(f"### chunk {i}: {heading}")
        kps = item.get("key_points") or []
        if kps:
            parts.append("Key points:")
            for k in kps:
                parts.append(f"  - {k}")
        ents = item.get("entities") or []
        if ents:
            parts.append("Entities: " + ", ".join(str(e) for e in ents))
        dps = item.get("data_points") or []
        if dps:
            parts.append("Data points:")
            for d in dps:
                parts.append(f"  - {d}")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Task 8 — paper-type-aware section variants + domain extraction targets
# ---------------------------------------------------------------------------

#: Correction-notice variant: 4 sections instead of 12. Avoids the
#: "9 sections of Not reported in this paper." failure mode for errata.
_CORRECTION_NOTICE_SECTIONS: tuple[SectionRule, ...] = (
    SectionRule(
        name="Title & Metadata",
        in_lenient_subset=True,
        rule="Title of the correction, authors, year, journal, DOI of the correction itself.",
    ),
    SectionRule(
        name="Correction Summary",
        max_words=150,
        rule="What was changed and why. One paragraph of plain prose.",
    ),
    SectionRule(
        name="Original Citation",
        rule="Full citation of the original paper this correction amends, including its DOI.",
    ),
    SectionRule(
        name="Limitations & Caveats",
        max_words=200,
        rule="Anything the correction does NOT address. Often a single sentence.",
    ),
)


def _build_review_variant() -> tuple[SectionRule, ...]:
    """Review variant: 12 sections, but Methods becomes Reviewed Literature."""
    out: list[SectionRule] = []
    for s in REQUIRED_SECTIONS:
        if s.name == "Methods & Experimental Design":
            out.append(SectionRule(
                name="Reviewed Literature & Inclusion Criteria",
                max_words=300,
                in_lenient_subset=False,
                rule=(
                    "Search/inclusion criteria, databases queried, time window, "
                    "and the count of papers reviewed."
                ),
            ))
        else:
            out.append(s)
    return tuple(out)


_REVIEW_SECTIONS: tuple[SectionRule, ...] = _build_review_variant()


#: Map of paper-type → ordered SectionRule tuple. Paper types not listed here
#: fall back to the 12-section default (REQUIRED_SECTIONS) — the safe choice.
_SECTIONS_BY_PAPER_TYPE: dict[str, tuple[SectionRule, ...]] = {
    "correction_notice": _CORRECTION_NOTICE_SECTIONS,
    "review": _REVIEW_SECTIONS,
}


def sections_for(paper_type: str) -> tuple[SectionRule, ...]:
    """Return the SectionRule tuple for ``paper_type``.

    Falls back to ``REQUIRED_SECTIONS`` (the 12-section default) when the
    paper type isn't in the variant map. This is the safe default — old
    output formats and unknown types keep validating against the 12.
    """
    return _SECTIONS_BY_PAPER_TYPE.get(paper_type, REQUIRED_SECTIONS)


def headers_for(paper_type: str) -> list[str]:
    """Return the heading-name list for ``paper_type``."""
    return [s.name for s in sections_for(paper_type)]


def format_required_headings_block_for(paper_type: str) -> str:
    """Like ``format_required_headings_block`` but per paper type."""
    return "\n".join(s.heading for s in sections_for(paper_type))


def format_section_rules_block_for(paper_type: str) -> str:
    """Render the section rules block for the prompt based on paper type."""
    lines = []
    for s in sections_for(paper_type):
        limit_str = f" (Soft limit: {s.max_words} words)" if s.max_words else ""
        lines.append(f"- {s.name}{limit_str}: {s.rule}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Domain-specific extraction targets
# ---------------------------------------------------------------------------

#: Per-paper-type, per-section structured extraction targets. Rendered
#: into the prompt as an <extract_targets> XML block so the model knows
#: exactly what to lift out of the source text. Only sections with
#: meaningful targets are listed; the rest get the section's default rule.
_EXTRACT_TARGETS: dict[str, dict[str, list[str]]] = {
    "primary_research": {
        "Important Entities": [
            "Genes/proteins (e.g., TaPHS1, ZmMYB31, Cas9, sgRNA designs)",
            "Cultivars / germplasm with full names (e.g., 'Yangmai 158', 'CIMMYT 1234')",
            "Organisms with Latin binomial when given (e.g., Triticum aestivum)",
            "Software with version (e.g., 'QTL IciMapping v4.2', 'TASSEL 5')",
        ],
        "Methods & Experimental Design": [
            "Population type and size (RIL/DH/F2; n = ?)",
            "Phenotyping environments (years × locations)",
            "Marker types and density (SSR / SNP / GBS chip)",
            "Mapping software with version",
            "Statistical tests used (composite interval mapping / GWAS / mixed model)",
        ],
        "Key Results & Data": [
            "QTL nomenclature exactly as reported "
            "(e.g., Qphs.<lab>-<chrom>, with chromosome arm + LOD + R²)",
            "Effect sizes with units and direction",
            "p-values as reported (e.g., p < 0.001, p = 0.034)",
            "Sample sizes for each comparison (n =)",
            "Reference table/equation IDs as {{TAB_n_<paper>}} / {{EQ_n_<paper>}}",
        ],
        "Contradictory Findings": [
            "Results conflicting with prior studies, or inconsistent allelic/"
            "treatment effects across this paper's own experiments, genotypes, "
            "or environments (with the authors' explanation if given)",
        ],
        "Outdated Models": [
            "Theories, classifications, or methods the authors flag as superseded, "
            "oversimplified, or in need of revision",
        ],
        "Under-Researched Populations": [
            "Untested germplasm, genetic backgrounds, environments, traits, or "
            "mechanisms the authors flag as understudied",
        ],
    },
    "review": {
        "Reviewed Literature & Inclusion Criteria": [
            "Databases queried (PubMed / Scopus / Web of Science / Google Scholar)",
            "Time window (e.g., 2010-2024)",
            "Number of papers screened vs included",
            "Inclusion criteria (e.g., 'wheat-only', 'GWAS-only')",
        ],
        "Key Results & Data": [
            "Major themes the review identifies",
            "Common QTL / gene names recurring across the cited literature",
            "Quantitative ranges across studies (e.g., LOD range, R² range)",
        ],
        "Contradictory Findings": [
            "Where studies in the reviewed literature disagree, and the authors' "
            "explanation for the discrepancy",
        ],
        "Outdated Models": [
            "Models or classifications the review argues are superseded or no "
            "longer adequate",
        ],
        "Under-Researched Populations": [
            "Untested germplasm, environments, traits, or mechanisms the review "
            "identifies as gaps",
        ],
    },
    "methods_paper": {
        "Methods & Experimental Design": [
            "What input the method/protocol takes",
            "What output it produces, in what units",
            "Software/hardware dependencies with versions",
            "Validation dataset(s) used",
        ],
        "Key Results & Data": [
            "Sensitivity / specificity / accuracy with confidence intervals",
            "Throughput (samples/hour) when given",
            "Comparison metrics vs prior methods",
        ],
    },
    "correction_notice": {
        "Correction Summary": [
            "What specific element was wrong (figure / table / value / author list)",
            "What the correct value or wording is",
            "Whether the correction affects the original conclusions",
        ],
        "Original Citation": [
            "Full author list of the ORIGINAL paper",
            "Year, journal, volume, pages",
            "Original DOI (often distinct from the correction's DOI)",
        ],
    },
}


def extract_targets_for(paper_type: str) -> dict[str, list[str]]:
    """Return the {section_name: [target, ...]} map for `paper_type`.

    Empty dict for paper types that have no per-section targets defined —
    callers can render an empty extraction block in that case.
    """
    return _EXTRACT_TARGETS.get(paper_type, {})


def _extract_targets_block(paper_type: str) -> str:
    """Render the <extract_targets> XML block for the prompt.

    Empty string when `paper_type` has no targets defined, so the prompt
    collapses cleanly. Placed inline in build_main_prompt and
    build_stage_a_prompt by Task 11's wiring (today the builders ignore
    paper_type for the targets block — flipping that on is a small
    follow-up the wiring task will handle).
    """
    targets = extract_targets_for(paper_type)
    if not targets:
        return ""
    lines = [f"<extract_targets paper_type={paper_type!r}>"]
    for section_name, items in targets.items():
        lines.append(f"  <section name={section_name!r}>")
        for item in items:
            lines.append(f"    - {item}")
        lines.append("  </section>")
    lines.append("</extract_targets>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Task 7 — Stage A JSON schema + builder
# ---------------------------------------------------------------------------

#: The literal string Stage B renders for nullable string fields whose JSON
#: value is null. Mirrors what the legacy single-call path emitted so the
#: existing on-disk corpus reads consistently with new output.
NOT_REPORTED = "Not reported in this paper."


#: JSON schema (informally — not strict JSONSchema) for Stage A output.
#: Stage B (renderer) consumes this shape; the schema also gets stringified
#: into the Stage A prompt so the model sees the contract.
SUMMARY_JSON_SCHEMA = {
    "type": "object",
    "required": ["frontmatter", "paper_type", "sections"],
    "properties": {
        "frontmatter": {
            "type": "object",
            "required": [k.name for k in FRONTMATTER_KEYS if k.required],
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}},
                "type": {"type": "string", "const": "source"},
                "date_created": {"type": "string", "format": "date"},
                "date_updated": {"type": "string", "format": "date"},
                "source_count": {"type": "integer", "const": 1},
                "doi": {"type": ["string", "null"]},
                "authors": {"type": ["string", "null"]},
                "year": {"type": ["integer", "null"]},
                "journal": {"type": ["string", "null"]},
            },
        },
        "paper_type": {"type": "string", "enum": list(PAPER_TYPES)},
        "sections": {
            "type": "object",
            "description": (
                "One key per required H2 heading in the 12-section contract. "
                "Each value is an object with a `text` field (markdown body) "
                "and optional structured fields like `entities`, `results`, "
                "`references`."
            ),
            "required": list(required_headers()),
            "properties": {
                name: {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {"type": "string"},
                    },
                }
                for name in required_headers()
            },
        },
        "entities": {
            "type": "array",
            "description": (
                "Flat list of entities mentioned anywhere in the paper. "
                "Each item has `text` (display form) and optional "
                "`canonical_candidate` (a wiki slug suggestion). The "
                "renderer canonicalises against wiki_vocabulary."
            ),
            "items": {
                "type": "object",
                "required": [
                    "text",
                    "molecular_role",
                    "evidence_directness",
                    "role_evidence_quote",
                    "source_section",
                ],
                "properties": {
                    "text": {"type": "string"},
                    "canonical_candidate": {"type": ["string", "null"]},
                    "molecular_role": {
                        "type": "string",
                        "enum": list(MOLECULAR_ROLES),
                    },
                    "evidence_directness": {
                        "type": "string",
                        "enum": list(EVIDENCE_DIRECTNESS),
                    },
                    "role_evidence_quote": {
                        "type": "string",
                        "description": "Exact contiguous quote supporting the role.",
                    },
                    "source_section": {"type": "string"},
                },
            },
        },
    },
}


def build_stage_a_prompt(
    full_text: str,
    *,
    extracted_doi: str | None = None,
    api_metadata: dict | None = None,
    gene_registry_text: str = "",
    candidate_tags: list[str] | None = None,
    candidate_wikilinks: list[str] | None = None,
    paper_type: str = DEFAULT_PAPER_TYPE,
    today_iso: str | None = None,
    tables: list[dict] | None = None,
    equations: list[dict] | None = None,
    source_was_truncated: bool = False,
    original_text_len: int = 0,
    compact_output: bool = False,
) -> str:
    """Build the Stage A (JSON) extraction prompt.

    Same contextual blocks as ``build_main_prompt`` (DOI, tables,
    equations, truncation, candidate vocabulary) but the model is asked
    to return a JSON payload conforming to ``SUMMARY_JSON_SCHEMA``
    rather than free-form Markdown. Stage B (``renderer.py``) turns
    the JSON into the final wiki page deterministically.

    Behind the ``USE_TWO_STAGE_EXTRACTION`` feature flag (Task 11). Until
    flipped, this builder ships dark.
    """
    candidate_tags = candidate_tags or []
    candidate_wikilinks = candidate_wikilinks or []
    paper_type = paper_type if paper_type in PAPER_TYPES else DEFAULT_PAPER_TYPE
    date_clause = (
        f'today\'s date is {today_iso}; use it for date_created and date_updated.'
        if today_iso else
        "use today's date in YYYY-MM-DD format for date_created and date_updated."
    )

    cand_tags_block = (
        "Candidate tags (use these slugs verbatim if applicable):\n  "
        + ", ".join(candidate_tags)
        if candidate_tags else
        "Candidate tags: none — pick 2-6 short, lower-kebab-case tags yourself."
    )
    cand_wl_block = (
        "Candidate canonical wikilinks (existing wiki page slugs — prefer "
        "these in entities[].canonical_candidate):\n  "
        + ", ".join(candidate_wikilinks)
        if candidate_wikilinks else
        "Candidate wikilinks: none injected."
    )

    tables_text = _tables_block(tables)
    equations_text = _equations_block(equations)
    truncation_text = _truncation_block(source_was_truncated, original_text_len)
    extract_targets_text = _extract_targets_block(paper_type)

    headings_csv = ", ".join(f'"{h}"' for h in headers_for(paper_type))

    import json as _json
    schema_str = _json.dumps(SUMMARY_JSON_SCHEMA, indent=2)

    gene_registry_block = (
        f"GENE REGISTRY (Standard Nomenclature):\n{gene_registry_text}\n"
        "→ When discussing genes or loci, you MUST use the standard names exactly as they appear in the Gene Registry above. Do not invent new names or use aliases.\n\n"
    ) if gene_registry_text else ""
    section_rules_block = format_section_rules_block_for(paper_type)

    compact_block = (
        "\nCOMPACT OUTPUT (hard limits to fit your output token budget — "
        "a truncated JSON is a HARD FAILURE):\n"
        "  - Emit MINIFIED JSON: no indentation or newlines between tokens.\n"
        "  - sections[name].text: at most 700 characters each.\n"
        "  - entities: at most 8 items; role_evidence_quote at most 200 characters.\n"
        "  - key_results / data_points lists: at most 6 items per section.\n"
        "  - Do not use trailing commas. End with the closing `}`.\n"
        if compact_output else ""
    )

    return f"""\
You are an expert scientific researcher in plant genetics, wheat breeding,
CRISPR genome editing, and synthetic biology. Extract a STRUCTURED JSON
summary of the paper below for an Obsidian-flavoured research wiki.

PAPER TYPE: {paper_type}

{_metadata_block(api_metadata, extracted_doi)}
{gene_registry_block}{tables_text}{equations_text}{truncation_text}{cand_tags_block}

{cand_wl_block}

{extract_targets_text}{MOLECULAR_ROLE_PROMPT}

OUTPUT CONTRACT
Respond with a SINGLE JSON object containing the actual data extracted from the text.
Do NOT output the JSON schema definition itself. Your response must be a valid instance of the schema, populated with the extracted facts. No Markdown, no code fences, no prose preamble.

The JSON must conform to this schema (informal):

{schema_str}

The `sections` object must have exactly these keys, in order:
  {headings_csv}

Frontmatter rules ({date_clause}):
  - tags: array of 2-6 controlled-vocabulary strings (or [] if too sparse)
  - type: always the string "source"
  - source_count: always the integer 1
  - doi: string from VERIFIED METADATA above when provided, else null
    (literal JSON null, not the string "null")
  - authors: "Last1 et al." form, or null
  - year: 4-digit integer, or null
  - journal: full venue name, or null
  - DO NOT emit literal placeholder strings like "10.xxxx/xxxxx",
    "Last1 et al.", "Journal Name", or ["comma", "separated", "tags"].

Section rules:
{section_rules_block}
  - Each `sections[name].text` is the Markdown body of that section.
    No `## heading` line — the renderer adds those. Use bullet lists,
    Obsidian [[wikilinks]], and Markdown footnotes inside `text`.
  - If a section is unsupported by the source, set `text` to
    "Not reported in this paper." (string, not null).
  - Reference {{TAB_n_<paper>}}/{{EQ_n_<paper>}} placeholders by ID
    inside Key Results & Data; do NOT transcribe table contents.

Entity rules:
  - `entities` is a flat list of all genes/proteins/cultivars/tools
    mentioned. Each item has `text` (display form), `canonical_candidate`
    (a wiki slug suggestion or null), `molecular_role` (one ontology value),
    `evidence_directness`, `role_evidence_quote` (an exact contiguous quote
    copied from SOURCE TEXT), and `source_section`.
  - Molecular roles describe what a molecule is, not merely its association
    with a phenotype. A regulator is not automatically a transcription factor.

CRITICAL RULES
- ZERO HALLUCINATION: extract ONLY facts explicitly present in the
  source text. No outside knowledge. No invented DOIs/authors/years.
- Preserve hedged language verbatim ("suggests", "may indicate", etc).
{compact_block}
SOURCE TEXT
{full_text}
"""
