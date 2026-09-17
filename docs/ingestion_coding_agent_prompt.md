# Ingest Raw Paper .md Files — Coding Agent Prompt

When given raw paper `.md` files from `raw/papers/<topic>/`, follow this workflow for **each paper, start to finish, never skipping any phase**. Do not use any LLM APIs — you ARE the language model. Every wiki page you produce is a direct file write.

**CRITICAL: NEVER skip a phase. Every paper gets all four phases before moving to the next paper.**

---

## BEFORE STARTING: Load Tracking State

1. Read `processed_papers.json` from the project root.
2. List all `.md` files under `raw/papers/<topic>/` (excluding `temp_odl_*` and `*_data_objects.json`).
3. Skip any paper whose filename is already in `processed_papers.json` with `status: "completed"`.
4. Process remaining papers in **alphabetical order**.
5. After every paper fully completes all four phases, immediately add it to `processed_papers.json`.

---

## PHASE 0: Gather Inputs (per paper)

1. **Read** the raw `.md` file.
2. **Extract the DOI** — search for `10.\d{4,}/...` in the first 2000 chars or scan for `doi:` / `DOI` / `https://doi.org/`.
3. **Fetch OpenAlex metadata** if DOI found:

   ```
   https://api.openalex.org/works/https://doi.org/<DOI>
   ```

   Extract: `title`, `publication_year`, `primary_location.source.display_name` (journal), `authorships[].author.display_name` with first/last positions.
4. **Identify the paper type**: scan for "review", "REVIEW", "correction", "methods", "opinion", "ORIGINAL RESEARCH" in the first 2000 chars. Default: `primary_research`.

---

## PHASE 1: Write the Source Page

Write to `wiki/sources/uncategorized/<paper_slug>.md` where `<paper_slug>` matches the raw filename without the `.md` extension.

### Frontmatter (YAML)

```yaml
---
tags: [<3-6 kebab-case tags derived from paper content>]
type: source
date_created: YYYY-MM-DD
date_updated: YYYY-MM-DD
source_count: 1
doi: <DOI or null>
authors: <Last et al. or null>
year: <YYYY or null>
journal: <journal name or null>
---
```

### 15 Required H2 Sections (exact order, exact text — no numbers/bold/extra chars)

| ## Heading                           | Max Words | Rule                                                                                                                                                                                                               |
| ------------------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `## Title & Metadata`              | ∞        | Full title, authors, year, journal, DOI.                                                                                                                                                                           |
| `## Abstract Summary`              | ∞        | Faithful prose of the paper's abstract.                                                                                                                                                                            |
| `## Introduction & Background`     | ∞        | Frame problem + prior art authors cite.                                                                                                                                                                            |
| `## Key Concepts & Theory`         | ∞        | Central concepts using`[[wikilinks]]`. At minimum 3-7 wikilinks.                                                                                                                                                 |
| `## Important Entities`            | ∞        | Genes, proteins, organisms, tools —**all** in `[[wikilinks]]`. Organize: `* **Genes/Proteins**:`, `* **Organisms**:`, `* **Tools/Techniques**:`. Minimum 5 entities unless paper is extremely thin. |
| `## Methods & Experimental Design` | ∞        | Population, sample sizes, stats tests, software versions.                                                                                                                                                          |
| `## Key Results & Data`            | ∞        | Quantitative results with units. Reference`{{TAB_n_<paper>}}` placeholders by ID.                                                                                                                                |
| `## Mechanistic Insights`          | ∞        | Cause-and-effect chain from data.                                                                                                                                                                                  |
| `## Conclusions & Implications`    | ∞        | What authors claim follows from results.                                                                                                                                                                           |
| `## Limitations & Caveats`         | ∞        | Authors' caveats + any truncation/coverage warnings.                                                                                                                                                               |
| `## Contradictory Findings`        | ∞        | Conflicts with prior studies or internal inconsistencies. Write`Not reported in this paper.` if none.                                                                                                            |
| `## Outdated Models`               | ∞        | Superseded theories/methods. Write`Not reported in this paper.` if none.                                                                                                                                         |
| `## Under-Researched Populations`  | ∞        | Understudied germplasm/conditions. Write`Not reported in this paper.` if none.                                                                                                                                   |
| `## Future Directions`             | ∞        | Authors' stated next steps, not your speculation.                                                                                                                                                                  |
| `## Key References to Follow Up`   | ∞        | 3-7 references authors lean on most.                                                                                                                                                                               |

sk-wh1Q1iZQ9PLIWYhhJozXgBv7cCWEDDFiwwrAp2NSuJNpdAym

### Critical Rules

- **ZERO HALLUCINATION**: Only facts explicitly present in the source text. No outside knowledge.
- Unsupported sections → write exactly `Not reported in this paper.`
- Preserve hedged language: "suggests", "may indicate", "appears to".
- `## Key Concepts & Theory`: extract every central concept the paper discusses and wrap in `[[wikilinks]]`. These drive Phase 2 concept page creation.
- `## Important Entities`: **aggressively identify** every gene, protein, organism, cultivar, tool, software, technique mentioned. Wrap each in `[[wikilinks]]`. Do not include category labels as wikilinks (e.g., the text `Genes/Proteins:` itself is not a wikilink).
- When the raw text has `{{TAB_n_<paper>}}` or `{{EQ_n_<paper>}}` placeholders, reference them by ID in Key Results — do not transcribe their contents.

---

## PHASE 2: Create or Update Entity & Concept Pages (MANDATORY — NEVER SKIP)

**After writing the source page, you MUST create or update ALL referenced entity and concept pages before moving to Phase 3.**

Extract all wikilinks from:

- `## Key Concepts & Theory` → these are **concepts**
- `## Important Entities` → these are **entities**

For **each and every** wikilink from both sections (skip only bare category labels like `Genes/Proteins:`, `Organisms:`, `Tools/Techniques:`):

### Determine the page type and slug

- **Concepts** are abstract ideas: metabolic flux, RNA silencing, genome editing, speed breeding, shade avoidance, seed dormancy, CRISPR activation.
- **Entities** are named things: genes (Cas9, BBM, TaMFT), proteins (RUBISCO, PEPC), organisms (maize, wheat, Arabidopsis), tools/techniques (CRISPR-Cas9, GWAS, RNP), specific accessions (Frontana, Clark's Cream).
- **Slug**: lowercase the wikilink text, replace `[^a-zA-Z0-9]+` with `-`, strip leading/trailing `-`. Example: `CRISPR-Cas9` → `crispr-cas9`, `Agrobacterium-mediated-transformation` → `agrobacterium-mediated-transformation`.

### If the page DOES NOT EXIST (`wiki/concepts/<slug>.md` AND `wiki/entities/<slug>.md` both absent)

Create as concept or entity depending on type:

```markdown
---
tags: [<concept|entity>]
type: <concept|entity>
date_created: YYYY-MM-DD
date_updated: YYYY-MM-DD
source_count: 1
---

# <Display Name>

**Summary**:
<1-3 sentence factual definition based ONLY on what this paper says. No outside knowledge. If the paper provides <80 chars of context, write: `_Stub: snippet too thin to summarize.`>

**Sources**:
- [[<paper_slug>]]

**Last updated**: YYYY-MM-DD

---

### Findings from [[<paper_slug>]]
<1-3 sentences: what THIS paper specifically claims about this thing. Factual, neutral.>

## Related pages
```

### If the page EXISTS (in `wiki/concepts/` or `wiki/entities/`)

1. **Read** the existing file.
2. **Check** if it already has `### Findings from [[<paper_slug>]]`. If yes → **skip this page entirely** (already updated from a prior run).
3. If no:
   - Increment `source_count` in frontmatter.
   - Update `date_updated` to today.
   - Add `- [[<paper_slug>]]` to the **Sources**: list.
   - Insert a `### Findings from [[<paper_slug>]]` block before `## Related pages`.
   - Update the **Summary** to incorporate the new findings if the stub is thin.

### After ALL pages are created/updated

Run this verification:

```bash
grep -A20 'Key Concepts & Theory' wiki/sources/uncategorized/<paper_slug>.md | grep -oE '\[\[([^]]+)\]\]' | sed 's/\[\[//;s/\]\]//' | while read term; do
  slug=$(echo "$term" | tr 'A-Z' 'a-z' | sed 's/[^a-zA-Z0-9]/-/g;s/--*/-/g;s/^-//;s/-$//')
  [ -f "wiki/concepts/$slug.md" ] || [ -f "wiki/entities/$slug.md" ] || echo "MISSING: $term"
done
```

Do the same for `## Important Entities`. **Every single wikilink MUST resolve to an existing page.** If any are missing, you haven't finished Phase 2 — create them now.

---

## PHASE 3: Hallucination Repair (MANDATORY — NEVER SKIP)

1. Re-read the raw `.md` file.
2. For every factual claim in the source page (skip section headers, frontmatter, "Not reported in this paper." text):
   - Can you find this fact expressed in the raw source text? Allow for paraphrasing, Unicode normalization, case changes.
   - **Quantitative claims** (percentages, fold changes, sample sizes): must match source within rounding.
   - **Gene/protein names**: must appear in source.
   - **Causal claims** ("X causes Y"): must be stated or clearly implied by the source.
3. Count unverifiable claims. If >10% of factual sentences cannot be traced to source → **repair is triggered**.
4. Repair: rewrite the offending sections using ONLY language directly traceable to the raw text. No inference. Maximum 2 repair attempts per section.
5. Special case: paper is extremely thin (<500 chars of extractable text). Mark the source page with `_Thin source: limited extractable content.` in Limitations. Do not invent facts.

---

## PHASE 4: Concept Updation — Rollup (MANDATORY — NEVER SKIP)

For each entity/concept page that was touched (created or had `source_count` incremented) in Phase 2:

1. Read the full page content.
2. Extract all non-stub `### Findings from [[...]]` blocks.
3. Synthesize a new **Summary** (1-3 sentences) that reflects ALL findings across ALL sources listed. Reconcile overlapping claims. Note contradictions. Do not just append — rewrite the summary entirely.
4. Replace the old Summary text with the new synthesis.
5. If the page has only one source and the Summary already matches the findings block, skip the write.

**Exception**: if the Summary already says `_Stub:` and there's still not enough to write a real one, leave it. But if with the new findings block there IS enough context, rewrite it.

---

## AFTER EACH PAPER: Update Tracking

Immediately after a paper completes all 4 phases, append its entry to `processed_papers.json`:

```json
{
  "filename": "<raw_filename>.md",
  "relative_path": "wiki/sources/uncategorized/<paper_slug>.md",
  "slug": "<paper_slug>",
  "title": "<paper title>",
  "doi": "<DOI or null>",
  "authors": "<Last et al.>",
  "year": <YYYY or null>,
  "journal": "<journal or null>",
  "date_processed": "YYYY-MM-DD",
  "date_updated": "YYYY-MM-DD",
  "status": "completed"
}
```

Increment `processed_count` and update `last_updated` to current timestamp.

---

## BATCH PROCESSING: When Processing Multiple Papers

1. Read `processed_papers.json` to find which papers are already done.
2. Get the list of unprocessed papers from `raw/papers/uncategorized/` (alphabetically).
3. Process papers **one at a time, start to finish, all four phases** before moving to the next.
4. After each paper: update `processed_papers.json`.
5. At session end: do a final check that `processed_papers.json` is saved and accurate.
6. **Never skip Phase 2 for speed.** Every paper gets entity and concept pages created or updated. Batch-creating entities across multiple papers (doing Phase 1 for 50 papers, then Phase 2 for all 50) is acceptable if every [[wikilink]] resolves.
7. If a paper has very thin content (<500 chars of extractable material), still create the source page with `Not reported in this paper.` in unsupported sections, still create entity/concept stubs, still run hallucination repair. Do not skip the paper entirely.

---

## META: Edge Cases

- **Thin context** (<80 chars about an entity): create the page with `_Stub: snippet too thin to summarize.` — do not invent facts.
- **Section header names** in wikilink lists (e.g., `Genes/Proteins:`, `Tools/Techniques:`): these are category labels — do not create pages for them.
- **No DOI found**: still create the source page, set `doi: null`.
- **Image-heavy sections**: describe figure captions and data that IS extractable — that's your content.
- **Non-plant papers** (mouse depression, human genetics, etc.): still process them. They still get source pages, entity pages, and concept pages following the same rules. Facts must be from the source.
- **Pages with 0 entities listed**: the paper may be too thin. Set `## Important Entities` to `Not reported in this paper.` — do not invent any.

---

## MANDATORY RULES — READ CAREFULLY

1. **NEVER skip Phase 2.** Entity and concept pages MUST be created or updated for every paper.
2. **NEVER skip Phase 3.** Hallucination repair MUST run on every source page.
3. **NEVER skip Phase 4.** Rollup summaries MUST be updated for every touched page.
4. **Always verify [[wikilinks]] resolve.** After Phase 2, grep the source page for `[[...]]`, derive slugs, and confirm files exist.
5. **Always update processed_papers.json** after each paper completes all 4 phases.
6. **Never invent facts.** If the source doesn't say it, you don't write it.
7. **Never generate alternative prompts or workflows.** This document is the only prompt you follow.
