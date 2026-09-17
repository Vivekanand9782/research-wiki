# Research-Wiki Retrieval Agent

A grounded query-retrieval agent over the Antigravity research-wiki (~2,700 paper summaries, ~29k entities, ~12k concepts).

## Components

| File | Purpose |
|------|---------|
| `wiki_tools.py` | Local tools wrapping `research_retrieval.FullTextSearch` — BM25 search with quality scores, page reading, line-range evidence, wikilink graph traversal |
| `llm.py` | OpenAI-compatible chat client for General Compute, round-robin key rotation from antigravity's `.env` |
| `agent.py` | Agent loop: parse query → LLM decides tool → observe → repeat → synthesize grounded answer with inline citations |
| `output/` | Per-session artifacts (`transcript.json`, `answer.md`) |

## Architecture

```
  query ──► agent loop ──► LLM (General Compute) decides tool
                  ▲                     │
                  │   observation       ▼
                  └───────────── wiki_tools (local, free)
                                  └─ FullTextSearch (BM25, 55MB index)
                                  └─ read_page / read_lines / related_pages
```

## Quick start

Ask questions in natural language — you don't pick tools, just ask:

```bash
python3 -m research_agent.agent "preharvest sprouting in wheat"
python3 -m research_agent.agent "which papers cite liang_2017_efficient_dna_free"
python3 -m research_agent.agent "show me later work on wang_2014_simultaneous_editing_three"
```

### Query modes

| Flag | What it does |
|------|-------------|
| `--mode evidence` | Return hard evidence (exact lines) instead of summaries |
| `--mode hybrid` | Default — mix of summary + evidence quality scoring |
| `--no-llm` | Raw search results only, no LLM synthesis |
| `--top-k 12` | More or fewer search results per turn |
| `--turns 5` | Limit agent loop iterations (fewer for simple queries) |
| `--quiet` | Suppress console noise, show only answer and output path |

### Citation navigation tools

Agent autonomously traces literature networks without you specifying tools:

| Pattern | What happens |
|---------|-------------|
| "what does \<paper\> cite? | calls `papers_i_cite` — outgoing references |
| "who cites \<paper\>?" | calls `papers_citing` — incoming citations |
| "find similar papers to \<paper\>" | calls `related_papers` — Jaccard similarity |
| "connect \<paper_a\> to \<paper_b\>" | calls `citation_chain` — shortest path |
| multi-hop tracing | chains any combination across tool calls |

### Examples

```bash
# Trace lineage from early CRISPR to recent applications
python3 -m research_agent.agent \
  "trace genome editing research from zhang_2014_cloning_seed_dormancy to modern applications"

# Follow a paper's references
python3 -m research_agent.agent "zhang_2014_cloning_seed_dormancy citations"

# Find what builds on a key paper
python3 -m research_agent.agent "later work building on liang_2017_efficient_dna_free"

# Evidence-only with more results
python3 -m research_agent.agent "CRISPR delivery methods potato" \
  --mode evidence --top-k 12
```

No LLM → degrades to raw search listing. No keys available → same fallback. Output is written to `output/<timestamp>-<slug>/answer.md` (grounded synthesis with References block) and `transcript.json` (full loop history).

Set `ANTIGRAVITY_ROOT` to override the default `~/Desktop/antigravity` location.

## Output format

Each run creates `output/<timestamp>-<slug>/` with:
- `answer.md` — grounded synthesis with inline citations and a References block
- `transcript.json` — full agent loop history

## Failure modes

- No LLM key available → degrades to tools-only (search results listing)
- LLM rate-limit → client rotates across keys automatically
- Search returns nothing → agent reports "no evidence in wiki"
