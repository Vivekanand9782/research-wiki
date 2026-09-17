# Research Wiki — Code Organization Map

A navigable map of the `research-wiki/` codebase, generated from an AST import
graph over the whole tree (the codebase has **no dynamic imports**, so the graph
is authoritative). Use this to know what is safe to touch.

> **Layout note:** the Python modules live flat at the package root. That is
> intentional — modules import each other by bare name (`from pdf_extractor
> import ...`) and the CLI entrypoints assume same-directory imports, so moving a
> module into a subpackage would break both the import surface and the
> documented `python3 <module>.py` invocations. Organization here means a
> documented taxonomy + pruned stale files, **not** a moved import surface.

## Core pipeline modules (imported by non-test code — do not move)

| module | role |
|---|---|
| `config.py` | model ids, feature flags, concurrency/limit settings |
| `genai_client.py` | General Compute LLM client: key round-robin, TPM/RPM pacing, retries |
| `prompts.py` | prompt builders + `REQUIRED_SECTIONS` contract + per-paper-type variants |
| `pdf_extractor.py` | `ResearchPaperExtractor` — the per-paper engine (extract → summarize → seed pages) |
| `renderer.py` | Stage-A JSON → final wiki markdown; entity/concept wikilinking |
| `paper_classifier.py` | heuristic paper-type classifier (drives `sections_for`) |
| `paper_metadata.py` | DOI extraction + OpenAlex metadata resolution |
| `datalab_extractor.py` | Datalab cloud OCR fallback for PDFs pymupdf4llm can't parse |
| `pipeline_state.py` | content-fingerprint cache for resumable runs (`pipeline_state.json`) |
| `pipeline_logger.py` | structured per-run JSONL logging |
| `wiki_vocabulary.py` | alias/vocabulary index for wikilink canonicalization |
| `research_retrieval.py` | FTS5 raw-passage evidence index + retrieval |
| `sentence_verifier.py` | hallucination check of summary sentences vs. source |
| `validation.py` | shared validation helpers (headers sourced from `prompts`) |
| `molecular_roles.py` | controlled vocabulary of molecular roles |
| `lint_wiki.py` | deterministic schema/structure validator → `wiki_lint_report.md` |
| `lint_wiki_semantic.py` | LLM semantic linter (contradictions / outdated / duplicates) |
| `rollup_summaries.py` | re-synthesize entity/concept **Summary** from accumulated findings |
| `reconcile_wiki.py` | reconcile/repair wiki cross-links |
| `search.py` | wiki search helper |

## CLI entrypoints (standalone `__main__`; documented — do not move)

`ingest_parallel.py` (main pipeline), `mcp_server.py`, `pdf_extract_phases.py`,
`pdf_to_md.py`, `auto_improve_wiki.py`, `claim_impact.py`,
`fix_related_sources.py`, `obsidian_sync.py`, `process_analyzer.py`,
`reference_converter.py`, `tour_builder.py`, `update_processed_manifest.py`,
`wikilink_build_mapping.py`, `wikilink_inject.py`.

## Directories

| dir | contents |
|---|---|
| `wiki/` | the knowledge graph (sources / entities / concepts) — the corpus |
| `raw/papers/<topic>/` | raw markdown extraction cache (`<paper>.md`) |
| `tests/` | pytest suite (`testpaths = tests/`) + golden snapshots |
| `scripts/` | one-shot utilities + policy-referenced citation tooling (`build_manifest.py`, `audit_cited_doc.py`, `validate_manifest.py`, `log_change.py`, `current_model.py`) |
| `research_agent/` | grounded QA agent with citation-tracing tools |
| `benchmarks/` | A/B harness (`run_two_stage.py`, `score.py`) + dated reports |
| `docs/` | ingestion wiring + this map |
| `.understand-anything/intermediate/` | live run state (`ingest_watch.*`) + JSONL logs |
| `.attic/` | reversible archive of pruned stale files (see `.attic/README.md`) |
| `.quarantine/` | quarantined bad-data records (e.g. wrong-PDF downloads) |

## Do-not-touch (Rule #11 + live state)

`.git/`, `.backup/`, `.codegraph/`, `.venv/`, `.vscode/`, `.obsidian/`,
`.commandcode/`; the live `ingest_watch.*` daemon files; `research-wiki.code-workspace`
and `.clinerules` (editor/agent config).

## Cleanup performed 2026-08-13

- **Pruned (regenerable):** `__pycache__/` (6), `*.pyc` (105), `.DS_Store` (21),
  `.pytest_cache/`, empty `lint_report.jsonl`.
- **Archived reversibly** to `.attic/organize_20260813_*/`: 2 dead modules
  (`entity_linking.py`, `logging_utils.py`), a stale dated audit, 3 dated
  preview dirs + 6 dated 2026-07-29 one-off artifacts + one isolated repair
  script, and the `legacy-ingest-scripts-*.tar.gz` backup.
- **Verified after:** research-wiki 261 passed / 2 skipped; paper_agent 213
  passed; 34/34 modules import cleanly.
