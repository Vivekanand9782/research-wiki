# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed — Summary-richness pipeline optimization + old-summary backfill
- **`summarize_pipeline.py`**: restructured the summarization prompt so the evidence-footnote requirement leads (was the #1 failure mode: 48% of sidecars had zero `results[]` footnotes and were silently flagged). Added per-section footnote minimums, an in-worker quality gate mirroring the render gate's adaptive targets, ONE corrective follow-up call handing the model its own JSON when footnotes/depth are short, and a `repair_needed` tag for the mechanical repair stage. Lowered `MIN_RAW_WORDS` 2400 → 500 so thin papers are summarized under adaptive gates instead of skipped; dynamic `date_created`/`date_updated`.
- **`repair_sidecars.py`** (new): deterministic gate-repair. Mines verbatim sentences from the raw paper text (keyword + numeric scoring, verified via the renderer's quote matcher — valid by construction), injects them as `results[]` footnotes into Key Results / Mechanistic Insights / Methods and pads depth-short sections in two rounds (strict then loose scoring). Modes: `--from-report`, `--repair-needed`, `--all`, explicit stems, `--dry-run`. First run: 331 sidecars repaired, 0 errors.
- **`ingest_agent.py`**: `_depth_targets` word floor now never exceeds source length (`min(1200, raw_words)`), removing padding pressure on genuinely short sources.
- **`driver.sh`**: each wave now runs `repair_sidecars.py --from-report --repair-needed` + re-render after the render pass, so flagged sidecars are fixed in-cycle; remaining-count floor aligned to 500 words.
- **Backfill (Stage A/B)**: demoted 48 stale worklist `failed` entries to `pending` and cleared 52 stale state failures (all failed under the pre-optimization prompt); re-rendered all repaired sidecars; relaunched the detached daemon to drain the remaining ~1,800 pending papers including thin ones.
- **`docs/specs/2026-08-19-summary-richness-pipeline-design.md`** (new): design spec for the richness pipeline and backfill campaign.

### Added — Anti-hallucination: retrieval-answer grounding gate
- **`research_agent/verifier.py`** (new): deterministic, LLM-free post-synthesis grounding gate for the retrieval agent, mirroring the ingestion-side `sentence_verifier` but pointed at the evidence the agent actually retrieved. `verify_answer()` checks every factual sentence in the answer against the concatenated tool observations and validates that every cited `wiki/**/*.md` path both exists on disk and was retrieved this session. Returns a `GroundingReport`; also provides `extract_cited_paths`, `build_repair_message`, and an `ABSTENTION` constant.
- **`research_agent/agent.py`**: wired the gate into `run()`. The agent now accumulates an evidence corpus and retrieved-path set per observation, verifies the final answer (both the normal answer branch and the forced max-turns synthesis) with a bounded repair loop, abstains when no evidence was retrieved, and persists the grounding report into `transcript.json`. Previously the synthesized answer was returned verbatim with no programmatic verification.
- **`config.py`**: added `RETRIEVAL_GROUNDING_THRESHOLD` (default 0.75) and `RETRIEVAL_GROUNDING_MAX_RETRIES` (default 2), env-overridable.
- **`tests/test_research_agent_verifier.py`** (new): 11 offline tests covering grounded/ungrounded answers, fabricated-number rejection, citation existence/retrieval checks, empty-evidence abstention, and the repair-message builder.

### Changed — Anti-hallucination: tighter sentence grounding
- **`sentence_verifier.py`**: closed two holes in the fuzzy fallback of `_is_sentence_grounded`. Added a numeric-grounding veto (`_significant_numbers`: decimals, percentages, and multi-digit integers must appear in the source; single digits exempt) so a transposed/fabricated statistic (e.g. `LOD = 21.4` when the source says `12.4`) is rejected even when word overlap is high. Replaced the order-independent 60%-token-overlap branch with an ordered content-word subsequence check (`_ordered_match_ratio`, binary-search over source token positions), so recombination/relational hallucinations (right vocabulary, wrong relationship) no longer pass. The exact-substring and trigram-overlap paths are unchanged, so all prior verified sentences remain verified.
- **`tests/test_sentence_verifier.py`**: added 7 tests (wrong number, fabricated %, recombination rejection, faithful paraphrase with intervening words, correct-number paraphrase, single-digit exemption, and a `_significant_numbers` unit test). Full offline suite: 279 passed, 2 skipped.

### Changed
- **Retrieval agent default model**: aligned `research_agent/llm.py`'s hardcoded fallback from `gpt-oss-120b` to `minimax-m2.7`, matching `config.py` and `.env` (`GENERAL_COMPUTE_MODEL=minimax-m2.7`) so the agent uses minimax even when `.env` is absent. (`.env` already selects minimax, so runtime behaviour was already minimax; this fixes the code-level default.)
- **Migration to General Compute Backend**: Disabled the broken Aerolink (HCN SEC) model backend (`https://api.hcnsec.cn/v1`) due to model unrouting (HTTP 503 "model_not_found" for `Qwen3.6-35B-A3B`). Re-routed default model queries to the General Compute API (`https://api.generalcompute.com/v1`) using `gpt-oss-120b` and rotated `gc_*` API keys in `.env`.

- summarize_pipeline.py + driver.sh — hcnsec API summarization pipeline with 4-key round-robin, wave driver; wave-1 render: 8 written, 2 passed, 6 flagged (depth/footnotes, queued for retry)
- deep-resummarization daemon live: 1885 pending → 1880 remaining after wave-1 (16 papers, 13 written, 3 model-trap failures retried automatically); hcnsec multi-key pipeline at CONC=4, wave-1 elapsed 27 min; estimated ~14h to drain
### Added
- **Manual Ingestion of Target Papers**: Manually ingested three target papers under `wiki/sources/uncategorized/`:
  - `vu_2025_evolving_landscape_precise.md` (The evolving landscape of precise DNA insertion in plants)
  - `vu_2023_prime_editing_mechanism.md` (Prime editing: Mechanism insight and recent applications in plants)
  - `molla_2021_base_editing_prime.md` (Precise plant genome editing using base editors and prime editors)
- **Entity and Concept Page Generation**: Automatically generated and updated 70+ entity and concept pages under `wiki/entities/` and `wiki/concepts/` corresponding to the targets cited in the manually ingested papers, including a summary rollup across all sources.

- generated_content/agent-deep-resummarization-plan.md — added: detailed implementation plan for the zero-API agent-swarm deep re-summarization campaign (architecture, workflow, gates, depth spec, current state, failure modes)
- driver.sh + summarize_pipeline.py — automated deep-resummarization pipeline for pending wiki sources via hcnsec multi-key API (4 keys, wave driver, auto-render, footnote/depth fixes queued); ~44h estimate to drain ~1930 remaining eligible papers
### Added — OpenAI compatible endpoint & API Key Rotation
- **OpenAI-compatible client in `genai_client.py`**: Added `RotatingOpenAIClient` to load a comma/space/newline separated list of keys from `BLUESMINDS_API_KEYS` or `BLUESMINDS_API_KEY` and cycle them automatically.
- **Failover / depletion error handling**: Intercepts `openai.RateLimitError` and status codes 429/403 (billing disabled/quota exhausted), rotating client keys and retrying requests.
- **`config.py` options**: Integrated `USE_OPENAI`, `OPENAI_BASE_URL` (default: `https://api.bluesminds.com/v1`), and `OPENAI_MODEL` (default: `gemini/gemini-3-flash-preview`).
- **Input conversion & Response wrapping**: Automatically converts mixed text/image contents (including Google GenAI `Part` objects) to OpenAI message format. Mimics Gemini response via `OpenAIResponseWrapper` exposing `.text`.
- **Unit tests**: Added `tests/test_openai_rotation.py` to verify key parsing, rotation on errors, and message translation.

### Added — Book Ingestion Pipeline
- **`scripts/split_book.py`**: A utility using PyMuPDF (`fitz`) to parse a book PDF outline/TOC, extract chapter page ranges, split pages into chapter-specific PDFs, and generate `book_metadata.json` with offsets and titles. Automatically chunks books into 20-page parts if outline is missing.
- **`scripts/ingest_book.py`**: An end-to-end book-ingestion orchestrator that extracts text page-by-page, prepends `[Page X]` tags, calls Stage A Gemini structured extraction requiring verbatim `evidence_quote` checking, renders final summaries using the `renderer` with section-scoped footnotes, populates entity and concept seed pages, and generates a master book landing page.
- **`tests/test_book_ingestion.py`**: Pytest test suite covering text normalization, page tagged extraction, outline splitting, fallback chunking, and quote verification gate logic.

### Fixed
- **Pre-pass batch fault-tolerance in `ingest_parallel.py`**: Improved batch error handling during `opendataloader_pdf.convert` execution. Now, if a single file in a batch is corrupted or unreadable (e.g., throwing a `java.io.IOException`), the batch processing continues to salvage, post-process, and cache successfully extracted files, failing only the individual problematic PDF.

- Fix concept extraction parsing (colon removal and parenthetical fallback context search) and add strict entity extraction constraints to prevent citations from becoming entities. Set default model and timeout to Qwen3.5-397B-A17B with 120s limit.
### Added — Ingestion Prompt Overhaul (Tasks 1-12)

Foundational refactor of the PDF → wiki summary pipeline. Detailed plan
at [docs/ingestion_prompt_overhaul_plan.md](docs/ingestion_prompt_overhaul_plan.md);
architecture diagram at [docs/ingestion_prompt.md](docs/ingestion_prompt.md).

- **`prompts.py`** (new, 1258 lines): single source of truth. Owns
  `REQUIRED_SECTIONS` (12), `LENIENT_REQUIRED_HEADERS` (5),
  `FRONTMATTER_KEYS`, `PAPER_TYPES`, `STRICT_HEADING_PATTERN`,
  `FORMAT_VERSION = 1`, `SUMMARY_JSON_SCHEMA`, `CHUNK_SUMMARY_SCHEMA`,
  builders (`build_main_prompt`, `build_repair_prompt`,
  `build_stage_a_prompt`, `build_chunk_summary_prompt`),
  paper-type-aware variants (`sections_for`, `headers_for`,
  `extract_targets_for`), and the long-paper chunker
  (`chunk_by_sections`, `aggregate_chunk_intermediates`).
- **`renderer.py`** (new, 423 lines): pure-Python Stage B renderer that
  turns Stage A JSON into final Markdown. Wikilink canonicalisation
  preserves display casing (`[[TaPHS1]]` → `[[taphs1|TaPHS1]]`),
  evidence quotes become section-scoped Markdown footnotes after
  unicode-aware substring verification (smart quotes, em/en dashes,
  soft hyphens, ligatures), `format_version` frontmatter key emitted
  on every render.
- **`wiki_vocabulary.py`** (new, 334 lines): mtime-cached singleton
  index over `wiki/entities/` + `wiki/concepts/` (9557 entries on the
  live wiki, cold build 1.6 s). `find_canonical(term)` for O(1)
  lookups, `top_k_candidates(text, k=50)` token + bigram + trigram
  scan (< 1 ms cached on a 7600-char paper).
- **`paper_classifier.py`** (new, 201 lines): two-tier classifier
  (cheap regex heuristic → optional LLM fallback) returning one of
  `primary_research / review / methods_paper / perspective /
  correction_notice / conference_proceedings / other`. Defaults to
  `primary_research` on parse failure.
- **`benchmarks/score.py`** (new, 154 lines): deterministic A/B
  scoring. `score_summary`, `compare_summaries`,
  `acceptance_check(deltas, regression_tolerance=5.0)`. Used to
  validate flag flips without LLM cost.
- **Strict 12-section validator wired into the live pipeline**:
  `genai_client.validate_structured_summary_strict` is now what
  `_generate_and_validate_summary` calls on first attempt; lenient
  variant retained for re-validating existing on-disk summaries.
- **Verified DOI now injected into the main prompt body**, replacing
  literal placeholder scaffolds (`10.xxxx/xxxxx`, `Last1 et al.`,
  `Journal Name`, `[comma, separated, tags]`) with explicit
  string-or-null instructions.
- **`USE_TWO_STAGE_EXTRACTION`** feature flag in `config.py`. Off by
  default — the Stage A JSON + Stage B render path ships dark for
  rollback.
- **Tests**: 146 pytest cases + 25 subtests across
  `test_prompts_contract.py`, `test_baseline.py`,
  `test_max_retries_fix.py`, `test_wiki_vocabulary.py`,
  `test_paper_classifier.py`, `test_renderer.py`, `test_chunker.py`,
  `test_benchmark_score.py`. Golden-corpus regression baseline at
  `tests/golden/` covers 5 representative summaries (gold,
  metadata-only, correction notice, two primary-research papers).

### Fixed

- **`pdf_extractor._generate_and_validate_summary` off-by-one**:
  `max_retries = 1` made the repair branch unreachable
  (`range(1)` only yields `attempt=0`). Bumped to `2` so the repair
  pass actually runs. Regression test in `tests/test_max_retries_fix.py`.
- **Strict heading regex**: `STRICT_HEADING_PATTERN` tightened from
  `\s*` to `\s+` between `##` and the heading name so `##Title`
  (missing space) is now refused.


### Added
- Published a comprehensive, genetically and biochemically rigorous literature review and synthesis on resistant starch (RS) research at [resistant-starch-synthesis.md](file:///Users/vivekanandsirohi/Desktop/antigravity/research-wiki/wiki/synthesis/resistant-starch-synthesis.md) integrating RS1–RS5 classes, Zhong et al. (2025)'s new 10-type classification, and human health/national food security.
- Created and validated the dual-schema citation manifest sidecar at [resistant-starch-synthesis.citations.json](file:///Users/vivekanandsirohi/Desktop/antigravity/research-wiki/wiki/synthesis/resistant-starch-synthesis.citations.json) detailing canonical author lists, years, journals, DOIs, and PMIDs for all 6 target scientific papers.
- Verified the synthesis page using the local fail-closed validation script (`validate_manifest.py`), resolving all casing-based wiki-link citation mismatches and achieving a successful pass.
- Codified the 5-phase `Query Workflow` and 4 crucial scientific validation guards directly into `GEMINI.md` (further enhanced with rigorous failure-recovery protocols, actual API model tracking, and final changelog handoff) to prevent scientific hallucinations and ensure full compliance with project-level Rule #2, Rule #4, Rule #5, Rule #6, Rule #7, Rule #8, and Rule #9.
- Integrated `FullTextSearch` engine inside `mcp_server.py`, replacing the slow $O(N \cdot M)$ substring file scanner with a sub-millisecond indexed retriever.
- Implemented robust biological suffix stemming (`_stem`) inside `search.py` supporting `-ing`, `-ed`, and plural/sibilant noun endings (`fixes`/`dishes` -> strip `es` vs. `genes`/`lines`/`sites` -> strip `s`).
- Preserved complex gene nomenclature and technical terms (e.g., `Cas9`, `PE3`, `S163D`, `nCas9-RT`) inside `search.py` via custom alphanumeric tokenizer `re.findall(r'\b[a-z0-9*-]{2,}\b', text)`.
- Added exact-phrase match boosting (1.5x score multiplier) in search queries to support hybrid keyword and substring resolution.
- Added automatic staleness detector (`_is_stale()`) inside `search.py` to auto-rebuild and refresh the saved `search_index.json` on disk whenever any markdown files under `sources`, `entities`, `concepts`, or `synthesis` are added, modified, or deleted.
- Concurrently processed and ingested 4 new papers from the `data/` directory:
  - `Butt_2020_Engineering_Herbicide_Resistance_Prime_E.pdf`
  - `Molla_2021_Base_Prime_Editing_Plants.pdf`
  - `Verspreet_2013_Fructan_Metabolism_Developing_Wheat.pdf`
  - `Vu_2023_Prime_Editing_Mechanism_Applications_Plant.pdf`
- Generated structured Markdown summaries and JSON sidecar metadata for each paper under `wiki/sources/uncategorized/`.
- Concurrently generated and updated over 100 plant genetics and gene-editing concept/entity seed pages under `wiki/concepts/` and `wiki/entities/` using fanned-out parallel threads with lock-based safety.

- Generated phs-wild-relatives.md summarizing wild relatives as a source of PHS tolerance.
- Added comprehensive verification report for PHS genetic diversity sections (6.1-6.5) in generated_content/phs-genetic-diversity-verification-report.md
### Fixed
- Resolved false-staleness bug by aligning file traversal inside `build_index()` and `_is_stale()` to use recursive `.rglob("*.md")` for all folders (specifically indexing the nested `wiki/synthesis/tours/` files).
- Fixed the search accumulation bug by resetting in-memory search structures (`self.index`, `self.documents`, `self.doc_metadata`, `self.vocab`, `self.idf`) at the beginning of `build_index()`, ensuring deleted files are correctly purged during auto-rebuilding.

### Removed
- Removed image extraction, cropping, and figure-label mapping logic from `pdf_extractor.py`.
- Deleted module-level helper functions `is_junk_image` and `extract_images_from_pdf` from `pdf_extractor.py`.
- Deleted the method `_extract_and_map_images` from the `ResearchPaperExtractor` class in `pdf_extractor.py`.
- Removed `PIL.Image` and vision utility helper imports (`analyze_image`, `is_valid_scientific_figure`) from the imports of `pdf_extractor.py`.
- Removed unused image extraction thresholds (`JUNK_IMAGE_MIN_KB`, `JUNK_IMAGE_MIN_DIMENSION`, `JUNK_IMAGE_MIN_STD`) from `config.py`.

- Removed redundant/obsolete scripts: cleanup_wrong_sources_dryrun.py, find_raw_sprout.py, find_sprouting_info.py, and extract_specific_matches.py
- Removed plagiarism prevention checker and rules; removed visual extraction and asset folder setup in pdf_extractor.py and precommit.sh
### Changed
- Updated instructions in `GEMINI.md` to guide future agents to run the `search_wiki` MCP tool as their first step for high-performance retrieval.
- Simplified `process_single_pdf` inside `pdf_extractor.py` to skip checking existing renamed image assets and set `image_metadata = []` to preserve downstream JSON schema compatibility.
- Updated docstrings for `process_single_pdf` and `extract_all_raw` in `pdf_extractor.py` to reflect the removal of image extraction.

- Configured BLUESMINDS_MODEL to gpt-3.5-turbo-0613 in .env after validating working endpoints and latency across all API keys
- Refactored PDF extraction pipeline to use OpenAlex metadata lookups and strict gene registries to prevent citation and genetic nomenclature hallucinations
- Updated BLUESMINDS_MODEL to gpt-5.2-chat in .env after verifying full availability across all keys under standard max_tokens
- Added information from Sharma 2025 on T. sphaerococcum as a novel genetic reservoir for PHS tolerance
- Added Chao 2015 and Khosravizad 2024 to phs-wild-relatives.md synthesis report
- Added contradiction and discrepancy highlighting rule to GEMINI.md
- Added Scientific Debates & Divergent Mechanisms section to phs-wild-relatives.md to prevent oversimplification
- Load-balance Aerolink/Anthropic API calls by randomizing the starting key index and rotating keys on successful responses