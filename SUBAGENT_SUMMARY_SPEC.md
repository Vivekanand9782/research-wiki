# Subagent Summary Spec — direct wiki page generation

> Self-contained specification for summarization subagents. Read this spec,
> read your assigned raw paper text, write ONE rich wiki summary page
> directly. No APIs, no scripts — you are the summarizer.

## Task

1. Read the raw paper text at the path you were given.
2. If a page already exists at your target path: note its `date_created`
   value, then copy the old file to `wiki/sources/.attic/<stem>.pre-agent.md`
   before overwriting.
3. Write the complete rich summary to the target path.
4. Do nothing else. No web searches, no other files.

## Output format (exactly)

Start with YAML frontmatter:

```
---
tags: [3-8 lowercase kebab-case topic tags]
type: source
date_created: <preserve the existing page's value if present, else today's date>
date_updated: <today's date>
source_count: 1
doi: <DOI exactly as it appears in the raw text, else: null>
authors: <FirstAuthor et al., else: null>
year: <4-digit year, else: null>
journal: <full journal name, else: null>
format_version: 2
---
```

Never invent DOI/authors/year/journal not present in the raw text. Use bare
`null` for unknown values, never "Unknown" or "N/A".

Then these sections in order (H2 headings, exactly these names):

1. `## Title & Metadata` — **Title:**, **Authors:** (full list), **Year:**, **Journal:**, **DOI:**, plus a 100–150-word overview paragraph of what the paper is and does.
2. `## Abstract Summary` — faithful prose of the abstract, ~150–200 words.
3. `## Introduction & Background` — problem framing, prior art, knowledge gap, ~250–350 words.
4. `## Key Concepts & Theory` — bullets: `- **[[Concept Name]]**: 1–2 sentence definition.` ~200–300 words.
5. `## Important Entities` — sub-groups `**Genes/Proteins**`, `**Organisms**`, `**Tools/Techniques/Software**`; bullets: `- **[[Entity]]**: brief role/description.` Exhaustive; do NOT list citations or generic terms like [[gene]].
6. `## Methods & Experimental Design` — populations, samples, stats, software+versions, ~300–450 words (for reviews: `## Reviewed Literature & Inclusion Criteria`).
7. `## Key Results & Data` — quantitative results WITH units, ~400–600 words, PLUS 5–6 evidence footnotes (see below).
8. `## Mechanistic Insights` — causal interpretation, ~300–450 words, PLUS 2–3 evidence footnotes.
9. `## Conclusions & Implications` — ~200–300 words.
10. `## Limitations & Caveats` — genuine limitations, ~200–300 words.
11. `## Contradictory Findings` — real content if the paper discusses conflicts with prior work, else exactly `Not reported in this paper.` ~150–250 words.
12. `## Outdated Models` — models/assumptions this paper challenges, or `Not reported in this paper.`
13. `## Under-Researched Populations` — or `Not reported in this paper.`
14. `## Future Directions` — what the authors suggest, ~150–250 words.
15. `## Key References to Follow Up` — 5–10 works cited BY this paper, each with a 1-line relevance note.

End with:

```
---
**Source PDF:** `data/<stem>.pdf`
```

where `<stem>` is the target file's basename without `.md`.

## Evidence footnotes (mandatory: 8–15 total per page)

Anchor key factual/quantitative claims with inline footnote references at the
end of the sentence, then define them after the paragraph or at section end:

```
The major QTL explained up to 40.42% of phenotypic variation.[^key-results-data-1]

[^key-results-data-1]: "The PVE by individual QTL ranged from 3.22% to 40.42%." — Results section, 3.3.1
```

Rules:
- The quoted text MUST be a verbatim, contiguous substring of the raw paper
  text — copy it character-for-character (keep ×, ±, italics markers, etc.).
  Never paraphrase inside quotes. If you cannot find an exact sentence, pick
  a different sentence.
- Use slugs like `key-results-data-N`, `mechanistic-insights-N`,
  `methods-N` per section.
- Concentrate footnotes in Key Results & Data (5–6), Mechanistic Insights
  (2–3), Methods (1–2).
- Short sources: scale down proportionally (min 3 footnotes) but never pad.

## Wikilinks

Wrap entity/concept names in `[[Name]]` with natural capitalization:
`[[Root Nodule Symbiosis]]`, `[[Triticum aestivum]]`, `[[CRISPR-Cas9]]`.
Never kebab-case inside links, never generic words alone.

## Depth targets

| Metric | Target |
|---|---|
| Total page words | 3,000–4,500 for full papers |
| Key Results & Data | 400–600 words |
| Methods | 300–450 words |
| Mechanistic Insights | 300–450 words |
| Evidence footnotes | 8–15 (scale to min 3 for short sources) |

If the raw source is short (< ~1,500 words), scale targets to ~50% of source
length — never pad or fabricate beyond what the source supports.

## Integrity

- Every factual claim must come from the paper text you read.
- No external knowledge, no web search, no invented numbers.
- Language you cannot read or garbled text: write the page with sections set
  to `Extraction failed: raw text was unreadable.`
