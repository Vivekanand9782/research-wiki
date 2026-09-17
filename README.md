# Research Wiki & Local RAG: Scientific Knowledge Graph & Retrieval Engine

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-441%20passed-success.svg)](tests/)
[![License: All Rights Reserved](https://img.shields.io/badge/License-All%20Rights%20Reserved-red.svg)](LICENSE)
[![CI](https://github.com/Vivekanand9782/research-wiki/actions/workflows/ci.yml/badge.svg)](https://github.com/Vivekanand9782/research-wiki/actions)

An autonomous scientific research knowledge graph and sub-millisecond local RAG platform. Ingests academic literature PDFs, generates structured 15-section Obsidian vaults with bidirectional `[[wikilinks]]`, provides sub-millisecond SQLite FTS5/BM25 retrieval with Section-Aware MMR, and executes multi-hop citation graph reasoning.

```
                    ┌────────────────────────────────┐
                    │     Research Paper PDFs        │
                    └───────────────┬────────────────┘
                                    │
                                    ▼
                    ┌────────────────────────────────┐
                    │  Parallel Ingestion Pipeline   │
                    │   (pdf_extractor / prompts)    │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    ▼                                ▼
       ┌─────────────────────────┐      ┌─────────────────────────┐
       │   Obsidian Vault Graph  │      │  SQLite FTS5 Raw Passages│
       │  (sources, entities,    │      │  (BM25, line provenance,│
       │   concepts, wikilinks)  │      │   sub-millisecond index)│
       └────────────┬────────────┘      └────────────┬────────────┘
                    │                                │
                    └───────────────┬────────────────┘
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │             Dual-Tier Local RAG & Agent Hub              │
       │  • Fast FTS5 + Section-Aware MMR (query.py)              │
       │  • Multi-Hop Citation Reasoning (research_agent.agent)    │
       │  • MCP Knowledge Server (mcp_server.py)                  │
       └──────────────────────────────────────────────────────────┘
```

---

## ⚡ Quickstart

### 1. Installation

```bash
git clone https://github.com/Vivekanand9782/research-wiki.git
cd research-wiki

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies and package
pip install -r requirements.txt
pip install -e .
```

### 2. Configuration

```bash
cp .env.example .env
# Set DEFAULT_EMAIL and your LLM API keys in .env
```

### 3. Usage: Local RAG & Citation Agent

```bash
# Fast sub-millisecond SQLite FTS5 / BM25 evidence retrieval:
python3 query.py "What is the function of TaMFT in wheat seed dormancy?"

# Interactive Q&A research shell:
python3 query.py --interactive

# Multi-hop citation graph navigation:
python3 -m research_agent.agent "which papers cite liang_2017_efficient_dna_free" --turns 5
```

---

## Directory structure

```
research-wiki/
├── ingest_parallel.py     ★ main ingest pipeline (parallel, fingerprint-cached, resumable)
├── pdf_extractor.py         extraction + summary + seed-page engine (ResearchPaperExtractor)
├── pdf_extract_phases.py    phased raw-extraction helpers
├── prompts.py             ★ single source of truth: 15-section contract, prompt builders,
│                            frontmatter schema, JSON schema, long-paper chunker
├── validation.py            SummaryValidator (0–100 score); REQUIRED_HEADERS sourced from prompts
├── genai_client.py          General Compute client, key rotation, rate limiting, validators
├── paper_classifier.py      paper-type classifier (cheap regex heuristic → optional LLM fallback)
├── search.py                quality-aware BM25-style search facade + CLI
├── research_retrieval.py    raw-paper evidence retrieval, provenance, and coverage reporting
├── molecular_roles.py       strict TF/non-TF molecular-role ontology and validation
├── wiki_vocabulary.py       mtime-cached alias index over entities/ + concepts/ (canonicalisation)
├── renderer.py              Stage B deterministic JSON→Markdown renderer (two-stage path)
├── rollup_summaries.py    ★ re-synthesize entity/concept Summary from accumulated findings
├── pipeline_state.py        fingerprint cache (pipeline_state.json) for resumable runs
├── pipeline_logger.py       structured per-run logging
├── config.py                model ids + feature flags
├── lint_wiki.py             deterministic schema + structural validator → wiki_lint_report.md
├── lint_wiki_semantic.py    LLM semantic linter (contradictions / outdated claims / duplicates)
├── tour_builder.py          guided reading tours per high-degree concept
├── claim_impact.py          per-paper impact diff vs. everything already in the wiki
├── process_analyzer.py      workflow/pathway extraction for a topic
├── obsidian_sync.py         mirror the wiki into an Obsidian vault
├── mcp_server.py            expose the wiki to MCP-compatible clients
├── reference_converter.py   bibliography / reference helpers
├── fix_related_sources.py   one-shot link repair
├── benchmarks/              A/B harness (run_two_stage.py, score.py) + dated reports
├── docs/                    ingestion_prompt.md (wiring) + ingestion_prompt_overhaul_plan.md
├── tests/                   pytest suite (test_*.py) + golden/ snapshots
├── scripts/                 one-shot cleanup and utility tools (convert_to_bib.py, etc.)
├── raw/papers/<topic>/      raw markdown extraction cache: <paper>.md
├── .backup/                 timestamped backups taken before any in-place edit
└── wiki/                  ← the knowledge graph (also a valid Obsidian vault)
    ├── index.md             master index of ingested papers + syntheses
    ├── log.md               chronological ingest log
    ├── sources/<topic>/     one 15-section summary per PDF  (e.g. uncategorized/<paper>.md)
    ├── entities/*.md        ~33,600 seed pages: genes / proteins / organisms / cultivars / tools
    ├── concepts/*.md        ~15,200 seed pages: ideas / mechanisms / pathways / methods
    ├── synthesis/           cross-cutting essays + tours/ (per-concept) + impacts/
    ├── search_index.json    versioned quality-aware index built by research_retrieval.py
    ├── vocabulary_index.json  persisted alias index (skips re-reading every seed page)
    ├── ../raw/raw_passage_index.sqlite3  persistent FTS5 raw-passage index with line provenance
    └── .obsidian/           Obsidian vault config
```

PDFs live **outside** this folder, in `../data/<topic>/` (or just `../data/`).

### Anatomy of a seed page (entity / concept)

```
---
tags: [entity]            type, dates, source_count in frontmatter
---
# <Name>
**Summary**:             ← cross-source synthesis (rollup_summaries.py keeps this fresh)
...
**Sources**:             ← every paper that cites this node
- [[paper_a]]
- [[paper_b]]
**Last updated**: <date>
---
### Findings from [[paper_a]]   ← one block per source (stub/empty findings are skipped)
...
## Related pages
```

---

## How it works (workflow)

The live path is the **two-stage** path (`config.USE_TWO_STAGE_EXTRACTION = True`):
Stage A produces validated structured JSON and Stage B renders deterministic Markdown. A
non-retryable Stage A parse/validation failure can use the guarded legacy summary fallback.
Per run:

1. **Discover** PDFs under `../data/` (recursive).
2. **Bulk pre-pass** — `pymupdf4llm` extracts raw markdown per PDF into
   `raw/papers/<topic>/`, falling back to the Datalab cloud API only for PDFs it
   cannot parse. Deterministic, no LLM, fingerprint-cached.
3. **Per PDF (parallel workers):**
   1. reuse the cached raw text,
   2. classify the paper type (heuristic),
   3. build the **15-section prompt** (`prompts.build_main_prompt`) — injects the verified
      DOI, lists table/equation IDs, flags truncation, and chunks very long papers,
   4. LLM generates the 15-section summary → **strict validator** → one **repair** pass if
      any section is missing,
   5. write `wiki/sources/<topic>/<paper>.md`,
   6. **`populate_wiki_nodes`** — pull entities/concepts from the summary, apply the
      **significance gate** (entities in bare `[[wikilink]]` lists *or* with < 80 chars of
      prose context are skipped — no page, no LLM call, so no "stub" pages get created),
      then create/update seed pages. A page is "done" for a paper only once it carries a real
      `### Findings from [[paper]]` block, so a `--force` re-run repairs pages that previously
      held only a bare citation,
   7. **`update_wiki_indexes`** — append to `index.md` + `log.md`.
4. **Post-ingest lint** of the files touched by that paper.
5. **End-of-run auto-rollup** — once all papers are done, `rollup_summaries.run_rollup`
   re-synthesizes the `**Summary**` of every seed page the run touched, so an entity newly
   cited by this batch gets a fresh cross-source summary with no separate command. It is
   **fingerprint-gated** (see below), so a touched page costs an LLM call only when a new
   source actually added a finding. Skip it with `--no-rollup`.

Re-running is resumable: already-processed PDFs are skipped via the fingerprint cache and
existing `.md` files. `--force` ignores both and reprocesses everything.

**Why the rollup is a step, not inline:** ingest's per-paper pass only *appends* a
`### Findings from [[paper]]` block to each seed page — it does **not** rewrite the page's
`**Summary**`. Synthesizing the cross-source Summary the moment each finding is appended
would cost ~1 LLM call per entity *per paper* (and synthesize a shared page like `lignin`
once per citing paper in the same batch). Deferring to a single end-of-run rollup means each
touched page is synthesized **at most once per run, and only if its findings changed**.

**Standalone use (`rollup_summaries.py`):** the same rollup also runs as a separate command
for the cases ingest can't cover — re-synthesizing without re-ingesting any PDF (e.g. after a
prompt change), or backfilling fingerprints (`--reindex`). This is what keeps an entity cited
by 20 papers from being stuck with a one-paper summary.

### The 15-section summary contract

Defined once in `prompts.REQUIRED_SECTIONS` (`FORMAT_VERSION = 2`):

1. Title & Metadata · 2. Abstract Summary · 3. Introduction & Background ·
4. Key Concepts & Theory · 5. Important Entities · 6. Methods & Experimental Design ·
7. Key Results & Data · 8. Mechanistic Insights · 9. Conclusions & Implications ·
10. Limitations & Caveats · 11. **Contradictory Findings** · 12. **Outdated Models** ·
13. **Under-Researched Populations** · 14. Future Directions · 15. Key References to Follow Up

Unsupported sections render as `Not reported in this paper.` Correction notices use a
reduced 4-section variant; reviews swap *Methods* for *Reviewed Literature & Inclusion
Criteria*.

---

## Query Workflow (asking Kiro about the wiki)

When you ask me "from the wiki tell me...", here's how I route your question to the right tool:

| Your question | Tool | Usage |
|---|---|---|
| "what papers discuss X?" or "search for Y" | `search.py` | `python3 search.py --mode evidence --doc-type paper --verbose "query terms"` |
| "show me the pathway for X" or "how does Y work?" | `process_analyzer.py` | `python3 process_analyzer.py --topic <name> --kind pathway` |
| "what does paper X contribute?" | `claim_impact.py` | `python3 claim_impact.py --paper <paper_stem>` |
| "tell me about entity/concept X" | Direct file read | Read `wiki/entities/X.md` or `wiki/concepts/X.md` |

**My workflow:**
1. Parse your question → infer what you're looking for
2. Pick the appropriate tool from the table above
3. Execute it with the right parameters
4. Extract and present results from the wiki

**STRICT RULE: All answers must come from the wiki only.** I do not use external knowledge, web search, or prior training data to answer queries. If the wiki does not contain an answer, I explicitly state that.

**CITATION REQUIREMENT: Every claim in a report must include wikilinks to the `[[source]]` that supports it.** When extracting content from wiki pages, always include the `**Sources**` section to maintain traceability to the original papers.

**Just ask naturally** — you don't need to specify which tool to use. Examples:
- "from the wiki, what regulates auxin transport?" → I call `search.py`
- "from the wiki, show me the lignin degradation pathway" → I call `process_analyzer.py`
- "from the wiki, what did the 2023 starch paper contribute?" → I call `claim_impact.py`

### Evidence search options

`search.py` is backward-compatible, but now uses the quality-aware `FullTextSearch` engine:

```bash
# Compiled wiki summaries only.
python3 search.py --mode summary --doc-type paper "seed dormancy"

# Rerank linked raw-paper text while retaining wiki metadata.
python3 search.py --mode hybrid --top-k 20 "dormancy transcription factors"

# Search raw Markdown papers through the persistent FTS5 passage index.
python3 search.py --mode evidence --doc-type paper --top-k 50 --verbose \
  "sequence-specific transcription factors associated with seed dormancy"

# Return every positive match instead of truncating to top-k.
python3 search.py --mode evidence --doc-type paper --exhaustive \
  "bud dormancy transcription factors"
```

Search results include the document ID, score, document type, evidence quality, quality flags,
matched terms, source path, section, and exact `line_start`/`line_end` provenance. The search
report includes the index version, raw documents scanned, indexed raw-document count, passage
candidate count, positive/returned counts, candidate scope, and per-context coverage for seed,
bud, and tuber dormancy. `--include-stubs` includes low-information generated pages; it is off by
default. `--rebuild` rebuilds the versioned wiki index and warms the raw passage index; normal
queries refresh the raw index lazily when raw Markdown changes.

**Index freshness is incremental.** A query compares each page's size and mtime against the
persisted index and re-indexes only the pages that changed, added, or disappeared, then rewrites
`search_index.json`. A newly ingested batch therefore costs seconds instead of a full
50k-document rebuild; `--rebuild` still forces the complete pass. The alias vocabulary is cached
the same way in `wiki/vocabulary_index.json`, so a fresh process does not re-read every
entity/concept page. Both caches are validated (never trusted blindly) and rebuild themselves
when their inputs move.

Optional environment knobs: `WIKI_SEARCH_CACHE_SIZE` (summary-query result cache),
`WIKI_PASSAGE_CACHE_SIZE` (passage feature cache), `WIKI_STEM_CACHE_SIZE` (memoised stemmer;
must exceed the corpus vocabulary, currently ~162k tokens),
`WIKI_RAW_PASSAGE_CANDIDATE_LIMIT` (FTS5 candidate ceiling),
`WIKI_SEARCH_PHRASE_PREFILTER` (default on; when set to `0`/`off`, disables the phrase-token
prefilter below and restores the unconditional phrase regex), and
`WIKI_VOCAB_VALIDATION_INTERVAL` (seconds between full vocabulary revalidation scans; default
`30`, previously `1`).

**Query-time retrieval performance.** Two measured optimizations keep search fast on the full
57k-document corpus without changing results:

* *Phrase-token prefilter* (`WIKI_SEARCH_PHRASE_PREFILTER`, default on): phrase scoring previously
  ran a whitespace/dash-tolerant regex over the full text of every scored candidate. A phrase can
  only occur where every one of its word tokens occurs, so the regex is now gated on a cheap
  necessary-condition check against the in-memory term maps. This is byte-for-byte equivalent to
  the old path (verified by equivalence tests) and cut per-query latency by **~61% (summary,
  945→365 ms)** and **~54% (hybrid, 1229→560 ms)** in profiling, mostly by removing full-document
  phrase regex work.
* *Throttled vocabulary revalidation* (`WIKI_VOCAB_VALIDATION_INTERVAL`, default raised 1→30 s):
  the recursive entity/concept `stat` walk (~750k paths, ~280 ms) used to run about once per second
  during querying. Additions and deletions are still detected immediately via the two-directory
  signature; only in-place edits to existing pages are subject to the interval, and the vocabulary
  is a soft alias-expansion aid, so a bounded staleness window is safe.
* *RAG fast-path stemming alignment* (`rag_engine.RAGEngine._fast_fts_search`): the persistent raw
  passage index stores suffix-stemmed tokens, so the direct FTS5 query must be stemmed to match.
  The fast path now emits both the raw and the stemmed FTS token per query word (a strict superset
  of the old matches), recovering the stemmed hits that inflected words previously missed — e.g.
  `regulating` matched 3 passages before vs 3,796 for the stem `regulat`; `plants` 842 vs 47,066.

`mode=evidence` is the preferred mode for research-paper drafting because it searches exact
passages through the persistent local raw-paper index while retaining line-level provenance. It
does not claim literature-wide exhaustiveness: `--exhaustive` means all positive matches in this
indexed corpus only. If SQLite FTS5 is unavailable or the index cannot be built, the engine falls
back to the legacy full raw-paper scan. Results must still be screened for study design,
biological role, and evidence strength.

### Molecular-role rules for dormancy queries

Strict TF results include only `sequence_specific_transcription_factor`. A dormancy association
alone does not make a protein a TF. The enforced controls are:

- `MFT`, `AtMFT`, `TaMFT`, and `TaPHS1` → `signaling_regulator`
- `DELLA`, `GAI`, and `RGA` → `transcriptional_coregulator`

Use these as associated regulators/interactors, not as sequence-specific TFs, unless the ontology
is deliberately revised with direct DNA-binding evidence.

### MCP search

Run `python3 mcp_server.py` from the repository root and configure it as an MCP stdio server.
The `search_wiki` tool accepts `query`, `top_k` (1–200), `mode` (`summary`, `hybrid`, or
`evidence`), `doc_type` (`source`/`paper`/`entity`/`concept`/`synthesis`), `include_stubs`, and
`exhaustive`. Its response preserves the search report and returns provenance and quality fields
for every result. Use `mode=evidence` plus `doc_type=paper` when the downstream answer needs
source-linked passages rather than only compiled page summaries. `list_pages` is paginated
(`limit` 1–2000, default 200, plus `offset`) and reports `total_pages`/`truncated`, so it lists a
window of the 50k+ page corpus instead of dumping all of it into the context.

### Retrieval agent with citation tracing

A grounded QA agent that chains tool calls across the wiki corpus and citation graph. Ask
questions in natural language — you don't pick tools. The LLM decides which tool to call based
on your question, observes the results, repeats until it has enough evidence, then synthesizes
a final answer with inline citations and a References block.

```bash
# Normal mode (LLM auto-chains tools)
cd research-wiki && source ../.venv/bin/activate
python3 -m research_agent.agent "what papers cite liang_2017_efficient_dna_free"
python3 -m research_agent.agent "later work referencing wang_2014_simultaneous_editing_three"
python3 -m research_agent.agent "find similar papers to wu_2023_viral_vector_delivery"

# Evidence-only + more results
python3 -m research_agent.agent "CRISPR delivery methods potato" --mode evidence --top-k 12

# No-LLM mode — raw search listing only
python3 -m research_agent.agent "seed dormancy" --no-llm

# Quiet mode — suppress console noise
python3 -m research_agent.agent "my query" --quiet

# Limit turns for simple queries
python3 -m research_agent.agent "simple fact" --turns 5
```

**Agent architecture:** model (LLM) → tools → loop (retries on bad JSON, forces synthesis at
max_turns) → memory (transcript.json). Each run saves `output/<timestamp>-<slug>/answer.md`
and `transcript.json`. Falls back gracefully if no LLM key is configured.

Available tools (user never specifies these — the LLM picks automatically):

| Tool | What it does |
|------|-------------|
| `wiki_search` | Knowledge-augmented BM25 search over paper/entity/concept pages |
| `read_page` | Read a full wiki page by path (up to 6000 chars) |
| `read_lines` | Extract exact lines from a hit by line range |
| `related_pages` | Follow `[[wikilinks]]` from a page into the graph |
| `papers_i_cite` | Outgoing citations — what this paper cites |
| `papers_citing` | Incoming citations — who cites this paper |
| `related_papers` | Shared-citation similarity (Jaccard index) |
| `citation_chain` | BFS shortest path between two papers |

Citation patterns the agent recognizes:

| Natural-language trigger | Action |
|---|---|
| "what does\<paper\> cite?" | calls `papers_i_cite` |
| "who cites\<paper\>?" / "later work on\<paper\>" | calls `papers_citing` |
| "similar papers to\<paper\>" / "papers sharing references with\<paper\>" | calls `related_papers` |
| "connect A to B" / "trace lineage from A to B" | calls `citation_chain` |
| multi-hop tracing | chains any combination across tool calls |

Set `ANTIGRAVITY_ROOT` env var to override the default `~/Desktop/antigravity` location.

---

## Setup

```bash
cd research-wiki
source ../.venv/bin/activate
```

Configure General Compute in the workspace `.env` (one level above this directory):

```env
GENERAL_COMPUTE_BASE_URL=https://api.generalcompute.com/v1
GENERAL_COMPUTE_API_KEYS=<key-1>,<key-2>,<key-3>
GENERAL_COMPUTE_MODEL=minimax-m2.7
GENERAL_COMPUTE_LONG_CONTEXT_MODEL=minimax-m2.7
```

`GENERAL_COMPUTE_API_KEY` is also accepted for a single credential. The only supported
models are `gpt-oss-120b` and `minimax-m2.7`; other names are rejected before a request is
sent. Research Wiki does not fall back to Vertex, Aerolink, Ollama, Anthropic, or legacy
OpenAI credentials.

---

## Step-by-step operating guide (recommended)

This is the canonical workflow for normal ingestion and recovery runs. Run every command from
`research-wiki/`; do not run maintenance commands while an ingest process is still active.

### Step 1 — Enter the project and load configuration

```bash
cd /Users/vivekanandsirohi/Desktop/antigravity/research-wiki
source ../.venv/bin/activate  # omit if the environment is already active
```

General Compute credentials are read from the workspace `.env`. Never print the key values.
A shell-level `GENERAL_COMPUTE_API_KEYS` overrides `.env`; unset it first if the workspace file
should be authoritative.

### Step 2 — Preview the work (no writes, no API calls)

```bash
python3 ingest_parallel.py --pdf-folder ../data --dry-run
```

For a path list, validate exactly what it selects before the real run:

```bash
tr '\n' '\0' < path/to/retry-list.txt \
| xargs -0 python3 ingest_parallel.py \
    --pdf-folder ../data --force --skip-prepass --workers 6 --dry-run
```

Check `PDFs found`, the `would process` count, and every printed path. Positional PDF paths
override the recursive `--pdf-folder` scan.

### Step 3 — Run the ingest

Normal resumable run (cached papers are skipped):

```bash
GENERAL_COMPUTE_MODEL=minimax-m2.7 \
PYTHONDONTWRITEBYTECODE=1 \
python3 ingest_parallel.py \
  --pdf-folder ../data \
  --workers 2
```

Six-request run, only after all six credentials pass a live health check and the provider is
stable:

```bash
GENERAL_COMPUTE_MODEL=minimax-m2.7 \
GENERAL_COMPUTE_MAX_IN_FLIGHT=6 \
PYTHONDONTWRITEBYTECODE=1 \
python3 ingest_parallel.py \
  --pdf-folder ../data \
  --workers 6
```

Targeted forced recovery from a newline-delimited path list (recommended instead of rerunning the
whole corpus):

```bash
tr '\n' '\0' < path/to/retry-list.txt \
| xargs -0 env \
    GENERAL_COMPUTE_MODEL=minimax-m2.7 \
    GENERAL_COMPUTE_MAX_IN_FLIGHT=6 \
    PYTHONDONTWRITEBYTECODE=1 \
    python3 ingest_parallel.py \
      --pdf-folder ../data \
      --force \
      --skip-prepass \
      --workers 6
```

Use `--skip-prepass` only when raw Markdown is already cached. Use `--force` only for deliberate
regeneration or a targeted recovery list.

### Step 4 — Verify completion before maintenance

Wait for `PARALLEL INGEST SUMMARY` and, when seed pages changed, the final `Rolled up ...` line.
A successful run has:

- `Failed: 0`
- `Errors: 0`
- `Deferred (provider): 0`
- no `General Compute is unavailable; deferring ...` message
- the final rollup line reports `0 failed` (if rollup ran)

The process exit code is useful, but the terminal counts are the authoritative completion gate.
Confirm that no ingest process remains:

```bash
pgrep -fl 'python3 ingest_parallel.py' || echo 'No ingest process is running.'
```

Detailed per-paper records are appended to `wiki/sources/pipeline_log.jsonl`; resumable cache state
is in `wiki/.understand-anything/intermediate/pipeline_state.json`. Do not edit either by hand.
If any paper failed, build a path-specific retry list from that run and repeat Steps 2–4 for only
those paths.

### Step 5 — Refresh the human-readable processed-paper manifest

```bash
python3 update_processed_manifest.py
```

This idempotently regenerates `wiki/processed_papers.json` from the current source pages. It is a
human/tooling inventory; `pipeline_state.json` remains the cache used by ingestion.

### Step 6 — Run read-only validation

```bash
python3 lint_wiki.py
```

The linter writes `wiki_lint_report.md` and exits non-zero only when format errors or actionable
structural errors exist. Advisory content debt remains fully reported without making a read-only
validation run fail. Review the report; do **not** immediately run `--fix` across the corpus. For an
optional read-only broken-link inventory:

```bash
python3 scripts/broken_links_report.py
```

This writes `wiki_broken_links_prioritized.md` without changing wiki pages.

### Step 7 — Smoke-test retrieval (and refresh the search index)

```bash
python3 search.py \
  --mode evidence \
  --doc-type paper \
  --top-k 5 \
  --verbose \
  "CRISPR Cas9"
```

Search compares indexed file paths, sizes, and mtimes with the wiki. If the persisted index is
missing or stale, this command rebuilds it automatically before searching. An explicit rebuild is
also available with `--rebuild`, but is normally unnecessary.

### Step 8 — Optional maintenance, only when there is a specific reason

- Ingest already runs a fingerprint-gated rollup. If the run used `--no-rollup`, or rollup failed,
  preview with `python3 rollup_summaries.py`, then apply with
  `python3 rollup_summaries.py --apply --workers 2`.
- `python3 lint_wiki_semantic.py --entity <slug>` performs an LLM semantic audit and writes a
  report; add `--fix` only after reviewing the proposed scope.
- `python3 lint_wiki.py --fix`, `python3 auto_improve_wiki.py`, and
  `python3 reconcile_wiki.py` mutate many files. They are not routine post-ingestion commands.
  Reconciliation is intended for manually authored source pages and can create a large number of
  stubs; use it deliberately and inspect backups/diffs afterward.
- Citation manifests (`scripts/build_manifest.py` and `scripts/validate_manifest.py`) apply to
  authored synthesis documents, not ordinary PDF ingestion.

### What ingestion already does automatically

A successful ingest writes raw caches and source summaries, creates or updates significant seed
pages, appends `wiki/index.md` and `wiki/log.md`, lints files touched by each paper, records
fingerprint state and per-paper logs, and rolls up changed multi-source seed-page summaries. Do not
repeat those steps manually after every run.

## Detailed command reference

### 1. Ingest (`ingest_parallel.py` — recommended)

```bash
python3 ingest_parallel.py                 # ingest ../data, 2 workers, resumable
python3 ingest_parallel.py --dry-run       # list what would be processed (no LLM, no writes)
python3 ingest_parallel.py --limit 1       # smoke-test a single paper first
python3 ingest_parallel.py --pdf-folder /path/to/pdfs
python3 ingest_parallel.py --workers 2     # lower concurrency (the endpoint is rate-limited)
python3 ingest_parallel.py --force         # ignore cache + existing .md; regenerate everything
python3 ingest_parallel.py --skip-summary  # raw extraction + caches only, no LLM / wiki writes
python3 ingest_parallel.py paperA.pdf paperB.pdf   # specific files (positional)
```

`--skip-prepass` skips the bulk raw-extraction phase and jumps straight to the AI
worker pool — useful when the pre-pass cache is already warm (all PDFs fingerprinted).

**Note:** If `GENERAL_COMPUTE_API_KEYS` is set in your shell, `load_dotenv()` uses
`override=False`, so that shell value takes precedence over `.env`. Run
`unset GENERAL_COMPUTE_API_KEYS` (and `unset GENERAL_COMPUTE_API_KEY` when applicable)
before re-invoking if you want to load corrected workspace values.

Other flags: `--no-rollup` (skip the end-of-run auto-rollup), `--batch-workers`,
`--output-folder`, and `--text-folder`.
The lower-level engine `pdf_extractor.py` also runs directly (`--phase 1` raw only,
`--phase 2` summary on already-extracted text).

### 2. Refresh seed-page summaries (`rollup_summaries.py`)

Re-synthesizes `**Summary**` from each page's accumulated findings (cross-source). Needs no
PDFs. **Ingest already runs this automatically at end-of-run** (step 5) — reach for the
standalone command only when no ingest is happening. Dry-run is free (no LLM); `--apply`
writes (1 LLM call/qualifying page, backups to `.backup/`). Synthesis runs in parallel
(`--workers`, default 4); the genai rate-limiter is shared and thread-safe, so it
auto-throttles on 429s.

**Fingerprint-gated:** each page stores a `rollup_fp:` hash of the sources that contributed a
real (non-stub) finding. A page is re-synthesized only when that set changes, so an unchanged
page is never redone and re-running `--apply` is cheap. `--reindex` stamps the current
fingerprints **with no LLM call** — run it once after a full `--apply` so already-fresh pages
aren't re-synthesized next run (only use it when you trust the on-page Summaries are current).

**On your next ingest**, a touched page's `**Summary**` is re-synthesized automatically — but
only when **all** of these hold (otherwise the page is skipped, no LLM call):
- the run is a real ingest — no `--no-rollup` / `--skip-summary` / `--dry-run`, and ≥1 paper succeeded;
- the new source added a *real* finding — a bare `[[wikilink]]` mention or < 80 chars of context
  is gated out, so it adds no `### Findings` block and the fingerprint doesn't change;
- the page now carries **≥ 2** non-stub findings — a brand-new single-source page has nothing
  cross-source to merge yet, so its one-paper Summary stands until a second real source lands.

```bash
python3 rollup_summaries.py                              # dry-run: list qualifying pages
python3 rollup_summaries.py --apply                      # synthesize + write (4 workers)
python3 rollup_summaries.py --apply --workers 8          # more concurrency
python3 rollup_summaries.py --apply --limit 100          # in batches (rate-limit friendly)
python3 rollup_summaries.py --reindex --apply            # backfill fingerprints (no LLM)
python3 rollup_summaries.py --kind concepts --min-findings 3 --apply
```

### 3. Optional mutating maintenance (`auto_improve_wiki.py`)

**This is not a routine post-ingestion step.** Use it only when you intentionally want a
whole-wiki mutation pass after reviewing the canonical operating guide above. It runs a 4-step
pipeline in sequence to audit and **automatically repair** your wiki:

| Step | What it does | Scope | Auto-repair? | Skip flag |
|---|---|---|---|---|
| 1. Reconcile | Creates missing seed pages from wikilinks, rebuilds search index | All broken links | ✅ Auto-creates stubs | `--skip-reconcile` |
| 2. Rollup | Re-synthesizes `**Summary**` on entity/concept pages from accumulated findings | Touched pages | ✅ Rewrites summaries | `--skip-rollup` |
| 3. Structural lint | Deterministic schema + format validation and auto-repair | **100% of 22,800+ pages** | ✅ Auto-fixes 7 issue types | `--skip-lint` |
| 4. Semantic audit | LLM-powered contradiction / outdated claim / unsourced claim audit & repair | Sub-graph clusters | ✅ LLM auto-fixes prose | `--skip-semantic` |

> 🛡️ **Safety Guarantee**: Every file modified by Step 3 or Step 4 is **automatically backed up** to `research-wiki/.backup/` with a timestamp before any edit is written.

#### Step 3: Structural Auto-Repair (Covers 100% of All 22,800+ Pages)

Step 3 scans every single markdown file in the wiki and deterministically auto-fixes:
- Missing YAML frontmatter or missing fields (`tags:`, `type:`, `date_created:`, `date_updated:`)
- Missing schema sections (`**Summary**:`, `**Sources**:`, `**Last updated**:`, `## Related pages`)
- Heading drift (e.g. rewriting `## Sources` → `**Sources**:`)
- Duplicate headings (e.g. deduplicating multiple consecutive `## Related pages` headers into one)

#### Step 4: Semantic LLM Audit & Auto-Repair Modes

Step 4 uses the configured General Compute model to find cross-page contradictions, unsourced claims, and format drift, and **automatically repairs the affected pages by re-submitting them to the LLM with a targeted repair prompt**:

| Mode | Flag | What it does |
|---|---|---|
| **Auto-discover** (default) | `--auto-discover` | Finds the N most-recently-changed entities/concepts and audits + repairs each one's **complete sub-graph cluster** (target page + all citing source papers + neighbor pages). This is the foolproof mode — every connected paper is included, so cross-page contradictions are guaranteed to be caught. |
| **Single entity** | `--entity SLUG` | Audits and repairs one entity/concept's full sub-graph cluster. Use for targeted deep audits (e.g. `--entity nifa` or `--entity cut-dip-budding-cdb`). |
| **Report-only** | `--no-semantic-fix` | Runs the semantic audit and generates `wiki_lint_semantic_report.md` without modifying pages. |
| **Legacy mtime** | `--pages N` | Picks the N most-recently-modified pages regardless of relationships. **Not recommended** — misses contradictions between unrelated pages. |

#### Quick reference

```bash
# ── Full pipeline: auto-repair 100% of pages structurally + audit/repair top 5 entity clusters ──
python3 auto_improve_wiki.py

# ── Full pipeline: audit & auto-repair top 20 entity sub-graph clusters ──
python3 auto_improve_wiki.py --discover-top 20

# ── Full pipeline: audit & auto-repair a specific entity sub-graph cluster ──
python3 auto_improve_wiki.py --entity nifa

# ── Semantic audit & repair only (skip steps 1–3) ──
python3 auto_improve_wiki.py --skip-reconcile --skip-rollup --skip-lint --entity cut-dip-budding-cdb

# ── Report-only mode (audit without modifying files) ──
python3 auto_improve_wiki.py --no-semantic-fix

# ── Everything except semantic audit (fast structural repair only) ──
python3 auto_improve_wiki.py --skip-semantic
```

#### What to run after a batch

Use Steps 4–7 in the canonical operating guide: verify counts, refresh the processed-paper
manifest, run read-only structural lint, and smoke-test retrieval. Do not run
`auto_improve_wiki.py` solely because a batch completed; it reconciles stubs and performs
whole-wiki auto-repair. Run it only when those mutations are explicitly desired.

#### Individual scripts (for one-off debugging only)

You generally **do not need** to run these directly — `auto_improve_wiki.py` calls them
internally. They remain available for targeted troubleshooting:

```bash
python3 lint_wiki.py --fix                 # deterministic schema repair → wiki_lint_report.md
python3 lint_wiki_semantic.py --entity X --fix # semantic audit + repair for entity X
python3 rollup_summaries.py --apply        # re-synthesize summaries only
python3 reconcile_wiki.py                  # full manual-source reconciliation (mutating)
python3 scripts/audit_cited_doc.py wiki/sources/uncategorized/paper.md
python3 tour_builder.py --top 30 --min-papers 5
python3 -m pytest -q                       # full offline test suite
```

`lint_wiki.py` reads every `wiki/**/*.md`, applies type-aware schema validation, and writes
`wiki_lint_report.md` in five sections: **orphan pages** (no inbound link), **missing pages**
(broken `[[wikilinks]]`, slug-normalised so case/punctuation mismatches don't false-positive),
**format errors** (schema violations), **structural errors** (actionable heading or link-placement
defects), and **content debt** (advisory empty `## Related pages` and unsourced body prose).
Only format and structural errors make the command exit non-zero.

Healthy baseline: **0 format errors and 0 structural errors**. Missing pages, orphans, and content
debt are tracked curation queues rather than ingestion failures. If format errors are non-zero,
fix the upstream paper's extraction rather than hand-editing the page.

### 4. Query / analyse / export

```bash
python3 search.py "starch synthesis"                       # full-text search (builds index)
python3 claim_impact.py --paper PAPER_STEM                  # diff one paper vs prior art
python3 process_analyzer.py --topic lignin --kind pathway  # extract a pathway/workflow chain
python3 obsidian_sync.py                                   # mirror to an Obsidian vault
python3 mcp_server.py                                      # serve the wiki to MCP clients
```

### 5. Convert References to BibTeX

Convert any RTF or text file containing academic references to a clean, resolved BibTeX `.bib` file:

```bash
python3 scripts/convert_to_bib.py /path/to/input.rtf /path/to/output.bib
```

This script extracts DOIs and queries them directly from the doi.org API in the foreground, bypassing GenAI LLM billing/quota limits. It also uses a local manual override mapping for references without DOIs.

---

## Configuration (`config.py`)

| Key | Meaning |
|---|---|
| `AI_MODEL` / `FILTER_MODEL` / `VISION_MODEL` | General Compute model IDs. `FILTER_MODEL` drives lightweight seed-page/classifier calls. |
| `USE_TWO_STAGE_EXTRACTION` | `True` = active Stage A (JSON) + Stage B (`renderer.py`) path; persists `raw/papers/<paper>.summary.json`. `False` selects the legacy single-call fallback path. |

`prompts.FORMAT_VERSION` is stamped into every rendered page; bump it on any change to the
section contract so downstream tools can tell formats apart.

---

## Maintenance scripts (`scripts/`, one-shots)

Used during cleanups; the live pipeline now prevents the bugs they fix. All default to
**dry-run** (`--apply` to write; backups under `.backup/`).

| Script | Fixes |
|---|---|
| `scripts/audit_cited_doc.py` | audits cited documents for unverified claims, genetic precision, and completeness |
| `scripts/build_manifest.py` | resolves raw seeds to verified DOIs and author lists via OpenAlex/PubMed |
| `fix_related_sources.py` | source-paper wikilinks misplaced under `## Related pages` |
| `delete_stub_pages.py` | deletes *whole-stub* seed pages (Summary itself is `_Stub:`); keeps pages that merely contain stub findings |
| `cleanup_wrong_sources.py` | `## Sources` heading drift |
| `autofix_typos.py` | high-confidence (≥0.95) typo wikilinks |
| `create_missing_stubs.py` | stubs for high-value broken wikilinks |
| `broken_links_report.py` | prioritised broken-link report (Tier 1/2/3 + typo suggestions) |
| `typo_review_list.py` | human-review list for medium-confidence typo candidates |
| `classify_schema_missing.py` | investigative classifier for "format error" pages |
| `classify_wrong_sources.py` | investigative classifier for `## Sources` drift pages |

---

## Troubleshooting

- **`General Compute request rejected with HTTP 401/403` / all keys unavailable** — one or
  more configured credentials is invalid. Correct `GENERAL_COMPUTE_API_KEYS` in `.env` (and
  unset an overriding shell value); the client disables only the exact rejected key.
- **Slow / many `429`s** — General Compute is rate-limiting the key pool. The client rotates
  keys and honors `Retry-After`; lower `--workers` (try 2) if pressure persists.
- **`⚠️ refusing to write Concept/Entity ... validation failed`** — the LLM returned a seed
  page that failed schema validation; the bad content was **not** written. Re-running the
  paper retries; persistent failures indicate poor source extraction.
- **`AI Error: ...` text inside a wiki page** — predates the write-time guard; delete the
  file (a backup is kept) and re-ingest the paper that introduced it.
- **`Unsupported General Compute model` / model configuration warning** — use exactly
  `gpt-oss-120b` or `minimax-m2.7`. Other model names are blocked locally and no inference
  request is sent.
- **Deleted a PDF** — its `raw/papers/*.md` and `wiki/sources/*.md` are *not* auto-removed;
  they remain as orphans (the pipeline is PDF-driven and only processes existing PDFs).
- **New sections / significance gate apply to future ingests only** — existing pages change
  only when re-ingested (`--force`) or via `rollup_summaries.py`. A `--force` re-run now also
  *repairs* a page that previously held only a bare citation by adding the missing
  `### Findings from [[paper]]` block. Legacy *whole-stub* pages from older runs aren't
  rewritten — clear them with `scripts/delete_stub_pages.py --apply`, then re-ingest.

---

## 📄 License & Portfolio Notice

Copyright © 2026 Vivekanand Sirohi. All Rights Reserved.

This repository and software are made publicly accessible on GitHub exclusively as an engineering portfolio and CV demonstration. All rights are reserved. Unauthorized reproduction, distribution, commercial use, modification, or training of third-party models is strictly prohibited.
