# GEMINI.md — LLM Wiki Schema for Plant Genetics Research

## Domain
Plant genetics, wheat breeding, CRISPR genome editing, nitrogen-use efficiency (NUE),
nitrogen fixation, synthetic biology, regulatory frameworks (DBT, GEAC, Rules 1989 India).

## Directory Structure
- ../data/<topic>/: Immutable source PDF documents, organized by topic subfolders (e.g., bioethanol/, crispr_wheat/). Uncategorized PDFs sit at the root.
- raw/papers/<topic>/: Raw AI-transcribed Markdown text, and JSON metadata (tables, equations, image mapping) extracted from PDFs.
- wiki/: Your output. All pages are markdown with YAML frontmatter.
- wiki/index.md: Master index dynamically rendered via Dataview. (No manual updates required).

## Page Types
- concepts/: One page per idea (e.g., base-editing, NUE, nitrogen-fixation, RBD-design)
- entities/: One page per gene, protein, organism, tool (e.g., TaNRT2, Cas9, CRISPR-TILLING)
- sources/<topic>/: One summary page per ingested paper (include DOI, authors, year, key claims), organized by topic.
- synthesis/: Cross-cutting pages (e.g., "Comparison of delivery methods in cereals")

## YAML Frontmatter (required on all pages)
Frontmatter requirements vary by page type to optimize Obsidian compatibility:

**Universal (All pages)**
```yaml
tags: [list]
type: concept | entity | source | synthesis
date_created: YYYY-MM-DD
date_updated: YYYY-MM-DD
```

**Sources Only**
```yaml
source_count: n   # number of sources this page draws from
doi: "10.xxxx/xxxxx"
authors: "Last1 et al."
year: YYYY
journal: "Journal Name"
```

**Concepts & Entities Only**
```yaml
aliases: [list]   # e.g., aliases: [NUE, Nitrogen Use Efficiency] for graph linking
```

## Page format
Every wiki page should follow this structure below its YAML frontmatter:

```markdown
# Page Title

**Summary**: One to two sentences describing this page.

**Sources**: List of raw source files this page draws from.

**Last updated**: Date of most recent update.

---

Main content goes here. Use clear headings and short paragraphs.

Link to related concepts using [[wiki-links]] throughout the text.

## Related pages

- [[related-concept-1]]
- [[related-concept-2]]
```

## Ingest Workflow
When I say "ingest [filename]" or ask you to run the extraction pipeline:
1. Read the full source document from `../data/<topic>/` or `raw/`
2. Discuss key takeaways with the user before writing anything
3. Ensure the automated pipeline places the generated summary page in `wiki/sources/<topic>/` (or create a summary page in `wiki/` named after the source if doing it manually)
4. Update or create concept and entity pages touched by this source
5. Add cross-links ([[concept-name]] wikilink syntax) to connect related pages
*(Note: Dataview dynamically handles indices and logs. You do not need to manually update index.md or log.md).*

A single source may touch 10-15 wiki pages. That is normal.

## Query Workflow
When the user asks a question, execute this structured, multi-phase workflow:

### Phase 1: Search & Retrieval
1. **Targeted Search**: First, query the `search_wiki` MCP tool (utilizing the optimized, indexed sub-millisecond search engine) to retrieve relevant documents and context snippets matching the query.
2. **Index Fallback**: If needed, read `wiki/index.md` as a fallback or to browse categories and high-level page registries.
3. **Examine Target Pages**: Read the specific Markdown pages identified (e.g., in `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, or `wiki/synthesis/`) to capture core facts.

### Phase 2: Verification & Contradiction Resolution
1. **Source Mapping**: Every factual claim MUST reference its source file. If a claim has no source, mark it as needing verification.
2. **Conflict Resolution**: If two or more sources disagree, note the contradiction explicitly in your response.

### Phase 3: [DECOMMISSIONED] Visual & Figure Lookup
Phase 3 has been decommissioned. No image discovery or figure insertions are required as visual extraction has been stopped.

### Phase 4: Formatting & Citation Mapping
1. **Obsidian Wikilinks**: Use double-bracket wiki-links (e.g., `[[concept-name]]`) within the body of the response to ensure proper graph connectivity.
2. **In-Text Citations**: Apply academic author-date citations attached directly to the wikilinks, ordered chronologically when grouping multiple citations:
   - Single author: `(Wang, 2024)[[wang_2024_knockout_zmnst2]]`
   - Two authors: `(Poovaiah and Bewg, 2016)[[poovaiah_2016_sugarcane_transgenics]]`
   - Three or more authors: `(Shen et al., 2013)[[shen_2013_enhanced_characteristics]]`
3. **References List**: Append a rigorous References section at the end of your response in academic format.

### Phase 5: Scientific Validation Guards (CRITICAL)
In executing this workflow, you MUST enforce the following four validation guards:
1. **Genetics & Transgenics Precision (Rule #6)**: Never assume or fabricate experimental designs. Report or mark as `[NOT REPORTED]` the following 7 fields verbatim for every genetic/transgenic experiment:
   - Allele or haplotype name(s) (with database accession if available)
   - Parental background / cultivar / accession
   - Transformation or editing method (e.g., Agrobacterium, biolistics, CRISPR-Cas9 with specific guide RNA)
   - Generation reported (T0, T1, T2, BC1, etc.)
   - Control genotype (null-segregant, isogenic line, untransformed cultivar)
   - Phenotyping environment (greenhouse, growth chamber, or country & year if field)
   - Sample size and replicate count
2. **Mandatory Generative Auditing (Rule #7)**: Run the following explicit checklist:
   - Every gene symbol cross-checked against UniProt / NCBI Gene (no protein/gene name swaps).
   - Every mutation/allele cross-checked against the cited paper or TAIR/Gramene/Wheat@URGI.
   - Every phenotype claim ties to a specific cited study and reports the cultivar/background.
   - Every historical claim verified against at least one secondary source.
   - No claim originates from parametric memory; every claim traces to a manifest or `[CITATION NEEDED]`.
3. **Citation Manifest Gate (Rule #2 & #5)**: If the response is valuable, offer to save it as a new wiki page in `wiki/synthesis/`. If creating/updating a synthesis page with scholarly citations, you MUST use the three-pass manifest loop:
   - **Pass 1 (Researcher)**: Query PubMed/CrossRef/OpenAlex to write a `<doc>.citations.json` manifest first. No prose.
     * *Model Tracking (Rule #4)*: Write the **actual API model ID** of the agent call (e.g., `gemini-3.5-flash`), retrieved from the CLI logs, into the manifest's `"model"` field.
     * *Failure Recovery (Rule #2)*: If APIs are rate-limited or unreachable, do not guess; mark the entry `[CITATION NEEDED]` with `"_status": "deferred"`, report the outage, and ask whether to retry, switch to OpenAlex, or pause. If a DOI resolves but metadata is incomplete, try OpenAlex or surface to the user. If the builder script errors, capture `stderr` and report it; do not manually bypass.
   - **Pass 2 (Writer)**: Read the manifest and write prose, citing *only* by manifest keys.
   - **Pass 3 (Validator)**: Run `validate_manifest.py` on the page. It must exit 0.
   - **Final Handoff (Rule #9)**: Once the validator passes, record the changes under the `## [Unreleased]` section of `CHANGELOG.md` at the project root following Keep-a-Changelog conventions as the absolute last step before marking the task complete.
---

## Citation rules
- Every factual claim MUST reference its source file. This is a strict mandate.
- If two sources disagree, note the contradiction explicitly.
- If a claim has no source, mark it as needing verification.

### In-Text Citation Format
Use **author-date** citations for readability, with the Obsidian wikilink embedded:

```
(Author et al., Year)[[source-filename]]
```

**Examples:**
- Single author: `(Wang, 2024)[[wang_2024_knockout_zmnst2]]`
- Two authors: `(Poovaiah and Bewg, 2016)[[poovaiah_2016_sugarcane_transgenics]]`
- Three+ authors: `(Shen et al., 2013)[[shen_2013_enhanced_characteristics]]`

**How it works:**
1. Extract authors and year from the source page's YAML frontmatter
2. Use `et al.` for 3+ authors
3. Append the `[[wikilink]]` to preserve graph connectivity
4. The wikilink uses the filename without `.md` extension

### Reference List Format
At the end of your response, include a **References** section in academic format:

```
## References

Author1, A., Author2, B., & Author3, C. (Year). Title of the paper. *Journal Name*. DOI: https://doi.org/10.xxxx/xxxxx [[source-filename]]
```

**Example:**
```
## References

Wang, Y., Xing, Y., Yang, X., Yu, Y., Li, J., Zhao, C., ... & Gou, M. (2024). Knockout of ZmNST2 promotes bioethanol production from corn stover. *Plant Biotechnology Journal*. DOI: https://doi.org/10.1111/pbi.14432 [[wang_2024_knockout_zmnst2]]

Poovaiah, C. R., Bewg, W. P., Lan, W., Ralph, J., & Coleman, H. D. (2016). Sugarcane transgenics expressing MYB transcription factors show improved glucose release. *Biotechnology for Biofuels*, 9, 143. DOI: https://doi.org/10.1186/s13068-016-0559-1 [[poovaiah_2016_sugarcane_transgenics]]
```

### Reference Construction Rules
1. **Authors:** List all authors if ≤6; for >6 authors, list first 6 then "et al."
2. **Year:** In parentheses after authors
3. **Title:** Sentence case (only first word and proper nouns capitalized)
4. **Journal:** Italicized
5. **DOI:** Full URL format with `https://doi.org/` prefix
6. **Wikilink:** `[[filename]]` at the end for graph mapping

### When Multiple Sources Support a Claim
Group citations chronologically:
```
Several studies have shown that MYB transcription factors regulate lignin biosynthesis (Fornale et al., 2010)[[fornale_2010_zmmyb31]]; (Poovaiah et al., 2016)[[poovaiah_2016_sugarcane_transgenics]]; (Fan et al., 2022)[[fan_2022_overexpression_ptomyb115]].
```

## Lint
When the user asks you to lint or audit the wiki, first run `python lint_wiki.py` to gather programmatic errors, then perform an LLM-based audit to:
- Check for contradictions between pages
- Find orphan pages (no inbound links from other pages)
- Identify concepts mentioned in pages that lack their own page
- Flag claims that may be outdated based on newer sources
- Check that all pages follow the page format above
- Report findings as a numbered list with suggested fixes

# Rules & Constraints
- **Exhaustive Query Answering:** Any time you answer a user query, you MUST generate an exhaustive and comprehensive answer. Do not miss any key information from the wiki. Read all relevant sources and synthesize them fully.
- **Contradiction and Discrepancy Highlighting:** When answering queries or generating synthesis reports from multiple scientific sources, you MUST NOT homogenize differing results or gloss over conflicts. You MUST explicitly highlight, compare, and contrast any inconsistencies, discrepancies, or contradictions (e.g., presence/absence of QTLs in different species or lines, environmental sensitivities, or competing candidate genes) to prevent oversimplification.
- Never modify anything in the `raw/` folder
- Keep page names lowercase with hyphens (e.g. `machine-learning.md`)
- Write in clear, plain language
- When uncertain about how to categorize something, ask the user
- **README upkeep:** Update `README.md` *only* when a change affects how the pipeline is **used** —
  new/changed/removed commands, flags, or user-visible behavior. Edit the exact sections that
  changed (don't rewrite the file), and keep the example commands runnable. Do **not** touch the
  README for purely internal changes (refactors, comments, tests) that don't alter usage.
- **Reference to BibTeX Conversion:** When asked to convert a list of references (from RTF, TXT, etc.) into a `.bib` file, always run the dedicated script `python3 scripts/convert_to_bib.py <input_file> <output_file>` in the foreground. Never use LLM-based API calls for this task; the script queries the doi.org API directly and handles manual mappings, making it faster, more accurate, and immune to billing/quota issues.


## Pipeline Execution
- **Background Tasks:** NEVER run long processes (like pipelines or filtering scripts) in the background via `execute_command` unless explicitly asked by the user. Run them in the foreground so the user can see live updates. If a command times out naturally in the CLI tool after 30 seconds, use `tail -f` to help the user stream it.

## API Limits & Embeddings (GenAI SDK)
- **Quota Exceeded (429 Errors):** Google Cloud GenAI imposes strict rate limits on embedding models like `textembedding-gecko` and `text-embedding-005`. 
- **Local Fallback:** Always maintain and use the `_local_fallback_embedding` method (MD5 hashing algorithm) in `genai_client.py` if quota issues arise, to guarantee the script does not hang or return all `0.000` scores for `cosine_similarity`.
- **Batching:** When fetching embeddings, always use batched arrays (`get_embeddings(texts: list)`) to minimize API requests.

## Filtering & Deduplication Logic (Pipeline Scripts / app.py)
- **Exclusive Lists:** The filtering logic must ALWAYS be mutually exclusive. A candidate paper should be evaluated and placed in *EITHER* the `kept_recs` list (AI-Verified output) *OR* the `uncertain_papers` list (Manual review output), but NEVER both.
- **Ensemble Checks:** Ensure that failed embeddings (empty vectors) do not artificially trigger uncertainty discrepancies (like `abs(llm_score - sim) > 0.35`). Always check `is_valid_sim = len(avg_orig_emb) > 0` before doing delta-based routing.

# Karpathy-Inspired Coding Guidelines (from https://github.com/forrestchang/andrej-karpathy-skills)

## 1. Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First
**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes
**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution
**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.