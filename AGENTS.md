# Research Wiki — Module Instructions

See the **root `AGENTS.md`** for the canonical workspace policy (citation manifest, no-touch dirs, changelog, permanent Git write prohibition, all 15 rules).

This file covers only what is unique to `research-wiki/`.

## Pipeline

```bash
cd ~/Desktop/antigravity
python research-wiki/ingest_parallel.py --help
python research-wiki/lint_wiki.py
cd research-wiki && python -m pytest tests/ -v
```

## Key files

| File | Role |
|---|---|
| `ingest_parallel.py` | Main pipeline — parallel, fingerprint-cached, resumable |
| `pdf_extractor.py` | `ResearchPaperExtractor` — extraction + summary + seed pages |
| `prompts.py` | 15-section contract, prompt builders, JSON schema, long-paper chunker |
| `genai_client.py` | General Compute client with key rotation + rate limiting |
| `config.py` | Model IDs + feature flags; reads workspace `.env` |
| `renderer.py` | Deterministic JSON → Markdown (Stage B) |
| `validation.py` | `SummaryValidator` (0–100); `REQUIRED_HEADERS` from `prompts.py` |
| `search.py` | BM25-style search facade + CLI |
| `rag_engine.py` | Fast grounded RAG engine (SQLite FTS5 + General Compute minimax-m2.7) |
| `query.py` | Direct RAG CLI and interactive Q&A shell |
| `lint_wiki.py` | Schema + structural validator → `wiki_lint_report.md` |

## Internal dependencies

`config.py` → all scripts. `prompts.py` → `pdf_extractor.py`, `renderer.py`, `validation.py`. `genai_client.py` → `ingest_parallel.py`, `lint_wiki_semantic.py`, `rollup_summaries.py`. `pipeline_state.py` → fingerprint cache shared across scripts.

## Generated (do not hand-edit)

`wiki/sources/` · `wiki/entities/` · `.backup/` · `wiki/.obsidian/workspace.json`

## Constraints

- `data/` at workspace root is the PDF source store
- Citation manifest workflow from root `AGENTS.md` applies to any cited content produced here
- `scripts/` contains one-shot / wave-based batch ops — not library code