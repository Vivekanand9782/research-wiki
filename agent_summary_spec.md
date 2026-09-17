# Agent Summary Specification

> **Version**: 1.0 | **Purpose**: Self-contained specification for every summarization agent
> in the deep re-summarization campaign. Read this spec, read the assigned raw paper text,
> write the sidecar JSON. Nothing else.

---

## What you produce

One file per paper: `raw/papers/<stem>.summary.json`

That is the **only file you may write**. Do not create, modify, or delete anything else.

---

## JSON Schema (follow exactly)

The JSON must be a single object with these top-level keys:

### `frontmatter` (object, 9 keys, all required)

| key | type | value |
|---|---|---|
| `tags` | `array[string]` | 3-8 lowercase kebab-case tags describing the paper's core topics |
| `type` | `string` | Always `"source"` |
| `date_created` | `string` | ISO date of today (e.g. `"2026-08-16"`) |
| `date_updated` | `string` | Same as `date_created` |
| `source_count` | `integer` | Always `1` |
| `doi` | `string or null` | The paper's DOI **as it appears in the raw text**, or `null` if none found |
| `authors` | `string or null` | `"Last1 et al."` form (first author surname + "et al."), or `null` |
| `year` | `integer or null` | 4-digit publication year, or `null` |
| `journal` | `string or null` | Full journal name, or `null` |

**Rules**:
- Never invent a DOI, author, year, or journal not present in the raw text.
- Use literal `null` (JSON null, not the string "null") for unknown values.
- Never use placeholder strings like "unknown" or "N/A".

### `paper_type` (string, required)

One of: `"primary_research"`, `"review"`, `"methods_paper"`, `"perspective"`,
`"correction_notice"`, `"conference_proceedings"`, `"other"`.

Use `"correction_notice"` if the paper is an author correction, erratum, or retraction.
Use `"review"` if the paper is a literature review, systematic review, or meta-analysis.

### `sections` (object, required)

Keyed by **section heading names**. Each value is an object with at minimum `"text"` (string).
Optionally include a `"results"` array for evidence-anchored footnotes (see below).

#### Section list for `primary_research`, `methods_paper`, `perspective`, `other`, `conference_proceedings`:

1. `Title & Metadata` — Full title, all authors, year, journal, DOI
2. `Abstract Summary` (~150-200 words) — Faithful prose of the abstract
3. `Introduction & Background` (~250-350 words) — Problem framing, prior art, knowledge gap
4. `Key Concepts & Theory` (~200-300 words) — Define central concepts as wikilinked bullets
5. `Important Entities` — Exhaustive gene/protein/organism/tool list, categorized
6. `Methods & Experimental Design` (~300-450 words) — Populations, samples, stats, software+versions
7. `Key Results & Data` (~400-600 words) — Quantitative results with units, evidence footnotes
8. `Mechanistic Insights` (~300-450 words) — Causal/mechanistic interpretation
9. `Conclusions & Implications` (~200-300 words) — What the findings mean for the field
10. `Limitations & Caveats` (~200-300 words) — Genuine limitations from the paper
11. `Contradictory Findings` (~150-250 words) — Results that conflict with prior work (or `"Not reported in this paper."`)
12. `Outdated Models` (~150-250 words) — Models or assumptions this paper challenges (or `"Not reported in this paper."`)
13. `Under-Researched Populations` (~150-250 words) — Populations/varieties/contexts understudied (or `"Not reported in this paper."`)
14. `Future Directions` (~150-250 words) — What the authors suggest next
15. `Key References to Follow Up` — 5-10 key cited works with 1-line relevance notes

#### Section list for `correction_notice` (4 sections only):

1. `Title & Metadata`
2. `Correction Summary` (~150-200 words)
3. `Original Citation`
4. `Limitations & Caveats`

#### Section list for `review` (replace Methods with Reviewed Literature):

Same as default but replace `Methods & Experimental Design` with `Reviewed Literature & Inclusion Criteria`.

### `entities` (array, optional but strongly recommended)

Each element is an object:

```json
{
  "text": "GeneSymbol or ProteinName",
  "molecular_role": "one_of_eight_roles",
  "evidence_directness": "one_of_four_values",
  "role_evidence_quote": "Exact contiguous quote from the raw paper text",
  "source_section": "Introduction & Background",
  "canonical_candidate": null
}
```

**Molecular roles** (pick exactly one per gene/protein):
- `sequence_specific_transcription_factor` — DNA-binding TF with named domain
- `transcriptional_coregulator` — DELLA, coactivator, corepressor (no direct DNA binding)
- `chromatin_regulator` — remodeler, histone modifier, methylation factor
- `signaling_regulator` — MFT, TaPHS1, PEBP family, developmental regulators
- `enzyme` — catalytic metabolic enzyme (not receptor/kinase)
- `receptor_or_kinase` — receptor, kinase, phosphatase, cascade component
- `noncoding_rna` — miRNA, siRNA, lncRNA, antisense RNA
- `locus_or_uncharacterized_protein` — QTL, locus, candidate, uncharacterized

**Evidence directness** (pick exactly one):
- `direct` — paper shows direct experimental evidence
- `indirect` — inferred from expression, correlation, homology
- `review_summary` — paper is a review summarizing others' findings
- `unclear` — cannot determine from the text

**Critical**: `role_evidence_quote` must be a **verbatim, contiguous substring** from the raw
paper text. The renderer will normalize whitespace and Unicode typography, then check that the
quote appears in the source. If it does not match, the footnote is dropped and a warning emitted.
Paraphrased or invented quotes will be caught.

**Known overrides** (enforced by the pipeline, do not fight them):
- MFT / TaMFT / TaPHS1 → always `signaling_regulator`, never TF
- DELLA / GAI / RGA / RGL1-3 → always `transcriptional_coregulator`, never TF

---

## Evidence footnotes (sections.*.results[])

For sections where claims should be grounded to source text (especially `Key Results & Data`,
`Mechanistic Insights`, `Methods & Experimental Design`), add a `"results"` array alongside `"text"`:

```json
{
  "Key Results & Data": {
    "text": "Markdown body of the section (no H2 heading — the renderer adds it)...",
    "results": [
      {
        "claim": "Wild-type NFR5 complemented nodulation in all 68 plants assayed.",
        "evidence_quote": "Wild-type NFR5 complemented nodulation in all 68 plants assayed (Figure 4B).",
        "source_locator": "Results section, Figure 4B"
      }
    ]
  }
}
```

**Rules for evidence quotes**:
- Must be an exact contiguous substring from the raw paper text.
- Each footnote should anchor a specific quantitative or factual claim.
- Target 8-15 footnotes per paper across the substantive sections.
- The renderer converts these into `[^slug-N]` footnotes in the rendered markdown.
- If a quote fails verification (not found in source), it is silently dropped — so never paraphrase inside quotes.

---

## Wikilink rules

In section text, wrap entity/concept names in `[[Name]]` using **natural capitalization**:

- ✅ `[[Root Nodule Symbiosis]]`, `[[CIMMYT]]`, `[[Triticum aestivum]]`
- ❌ `[[root-nodule-symbiosis]]`, `[[cimmyt]]`, `[[triticum-aestivum]]`

In `Key Concepts & Theory`, format each concept as:
```
- **[[Concept Name]]**: 1-2 sentence definition.
```

In `Important Entities`, organize under category subheadings:
```
* **Genes/Proteins**:
  - **[[GeneSymbol]]**: Brief functional description.
* **Organisms**:
  - **[[Species name]]**: Role in the study.
* **Tools/Techniques/Software**:
  - **[[Tool Name]]**: How it was used.
```

Do NOT list paper citations, author names, or study references in Important Entities.
Do NOT use generic terms: `[[gene]]`, `[[protein]]`, `[[chromosome]]`.

---

## Negative sections

For `Contradictory Findings`, `Outdated Models`, and `Under-Researched Populations`:
- If the paper genuinely discusses these, write real content (~150-250 words each).
- If the paper does not address them at all, use exactly: `"Not reported in this paper."`
- Never pad with generic filler. A short genuine section is better than a long vague one.

---

## Section text formatting

- Do NOT include the `## Heading` line in the `text` value — the renderer adds it.
- Use Markdown within section bodies: bold, italic, bullet lists, numbered lists are fine.
- Do not use H1 (`#`) or H2 (`##`) inside section bodies.
- Reference tables/equations by ID if present: `{{TAB_n_<paper>}}` / `{{EQ_n_<paper>}}`.

---

## Null metadata policy

When the raw text does not contain a DOI, author list, year, or journal name:
- Set the corresponding frontmatter field to JSON `null`.
- Do NOT guess, infer, or fabricate any metadata.
- If the raw text has a DOI that looks plausible but you cannot fully verify, include it as-is from the text.

---

## Safety constraints

1. **Read only**: the assigned raw paper text at the path given to you.
2. **Write only**: the single `raw/papers/<stem>.summary.json` file.
3. **No web searches, no git operations, no modifications to any other file.**
4. **Every factual claim in the summary must come from the paper text you read.**
5. **Every evidence quote must be a verbatim substring from that text.**
6. If the paper is in a language you cannot read, or the text is too corrupted/garbled to summarize, write the JSON with all section texts as `"Extraction failed: raw text was unreadable."` and set `paper_type` to `"other"`.

---

## Depth targets (summary)

| Metric | Target |
|---|---|
| Total page words (after rendering) | 3,500 – 4,500 |
| Key Results & Data words | 400 – 600 |
| Methods & Experimental Design words | 300 – 450 |
| Mechanistic Insights words | 300 – 450 |
| Evidence footnotes (corpus of results[]) | 8 – 15 per paper |
| Entities in entities[] | All identifiable genes/proteins with roles |
| Negative sections | Real content if paper addresses them; null-stub if not |
