# Paper Agent Configuration File
# Modify these values to update settings across all scripts.

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

RESEARCH_WIKI_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = RESEARCH_WIKI_ROOT.parent

for _p in [RESEARCH_WIKI_ROOT, WORKSPACE_ROOT]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

if (RESEARCH_WIKI_ROOT / ".env").exists():
    load_dotenv(RESEARCH_WIKI_ROOT / ".env", override=False)
if (WORKSPACE_ROOT / ".env").exists():
    load_dotenv(WORKSPACE_ROOT / ".env", override=False)
load_dotenv(override=False)

import llm_config


# --- Matplotlib Cache ---
# Silence the "not a writable directory" warnings in the terminal
# Use a cross-platform temporary directory
os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib")

# --- Unified LLM Hub Settings ---
# All scripts route through llm_config. Legacy names preserved for backward compatibility.
GENERAL_COMPUTE_BASE_URL = llm_config.get_base_url()
GENERAL_COMPUTE_MODEL = llm_config.get_model()
GENERAL_COMPUTE_LONG_CONTEXT_MODEL = llm_config.get_long_context_model()

# Compatibility names consumed by existing Research Wiki callers.
AI_MODEL = GENERAL_COMPUTE_MODEL
FILTER_MODEL = llm_config.get_filter_model()
VISION_MODEL = llm_config.get_vision_model()

# --- API Politeness / Identity ---
# Your email is used for Crossref, Unpaywall, and OpenAlex.
# Load from environment variable to avoid hardcoding PII
DEFAULT_EMAIL = os.environ.get("DEFAULT_EMAIL", "")

# --- Performance Settings ---
DEFAULT_WORKERS = 7
DEFAULT_REC_LIMIT = 5

# Bound transport attempts independently of higher-level summary/repair passes.
# Five attempts with 2/4/8/16-second backoff gives a transient provider outage
# time to recover without letting one paper retry forever.
AI_MAX_TRANSPORT_ATTEMPTS = max(
    1,
    int(
        os.environ.get("RESEARCH_WIKI_AI_MAX_TRANSPORT_ATTEMPTS")
        or os.environ.get("GENERAL_COMPUTE_MAX_RETRIES")
        or "5"
    ),
)
GENERAL_COMPUTE_CONNECT_TIMEOUT_SECONDS = max(
    0.1, float(os.environ.get("GENERAL_COMPUTE_CONNECT_TIMEOUT_SECONDS", "10"))
)
GENERAL_COMPUTE_READ_TIMEOUT_SECONDS = max(
    1.0, float(os.environ.get("GENERAL_COMPUTE_READ_TIMEOUT_SECONDS", "300"))
)
GENERAL_COMPUTE_RETRY_BASE_SECONDS = max(
    0.1, float(os.environ.get("GENERAL_COMPUTE_RETRY_BASE_SECONDS", "2"))
)
GENERAL_COMPUTE_RETRY_MAX_SECONDS = max(
    GENERAL_COMPUTE_RETRY_BASE_SECONDS,
    float(os.environ.get("GENERAL_COMPUTE_RETRY_MAX_SECONDS", "30")),
)
# Concurrency gate for all LLM calls (summary, repair, rollup, seed pages).
# Tuned for General Compute per-key limits: 1M TPM / 100 RPM / 50K req/day.
# 7 workers × 7 GC keys = 1 worker/key — well within limits. Measured
# 2026-08-01 at 18 workers: 18 PDFs in 149s, 0 x 429. Conservative default
# is 7 workers to give headroom on TPM (1 worker = ~91K tokens/min at typical
# 13K tokens/request; far below 1M TPM limit).
GENERAL_COMPUTE_MAX_IN_FLIGHT = max(
    1, int(os.environ.get("GENERAL_COMPUTE_MAX_IN_FLIGHT", "7"))
)
# Output-token ceiling for requests through this workspace. claude-opus-5-thinking
# accepts large budgets (hidden reasoning tokens count against it), so the default
# is 50000; per-model ceilings are enforced again in genai_client._MODEL_OUTPUT_LIMITS.
GENERAL_COMPUTE_MAX_OUTPUT_TOKENS = min(
    50000,
    max(1, int(os.environ.get("GENERAL_COMPUTE_MAX_OUTPUT_TOKENS", "50000"))),
)
# General Compute per-key token budget (TPM). The genai client paces requests so each
# key's rolling one-minute window stays under this, preventing 429 storms.
# Limit: 1,000,000 tokens/min per key.
GENERAL_COMPUTE_MAX_TPM_PER_KEY = max(
    1, int(os.environ.get("GENERAL_COMPUTE_MAX_TPM_PER_KEY", "1000000"))
)
# Group-wide requests-per-minute ceiling across ALL keys. General Compute
# documents 60 RPM per credential, so 7 keys give ~420 RPM of headroom; 300 is
# a safety net that the pipeline should never reach at 4-7 workers, not the
# primary throttle (per-key cooldowns and TPM headroom do that work).
GENERAL_COMPUTE_MAX_REQ_PER_WINDOW = max(
    1, int(os.environ.get("GENERAL_COMPUTE_MAX_REQ_PER_WINDOW", "300"))
)
GENERAL_COMPUTE_CONTEXT_GUARD_CHARS = max(
    1, int(os.environ.get("GENERAL_COMPUTE_CONTEXT_GUARD_CHARS", "320000"))
)
# Once one request exhausts all transient retries, already-running workers fail
# fast during this cooldown instead of each replaying the same provider outage.
GENERAL_COMPUTE_OUTAGE_COOLDOWN_SECONDS = max(
    0.0, float(os.environ.get("GENERAL_COMPUTE_OUTAGE_COOLDOWN_SECONDS", "30"))
)

# --- Feature flags ---
# Two-stage extraction: Stage A asks the LLM for a JSON payload conforming
# to prompts.SUMMARY_JSON_SCHEMA; Stage B (renderer.py) deterministically
# turns the JSON into the final wiki Markdown. Adds wikilink
# canonicalisation against wiki_vocabulary, evidence-quote footnotes, and
# paper-type-aware section variants. False ships the legacy single-call
# Markdown path (Tasks 1-6 still apply: strict validator, DOI injection,
# placeholder removal, table awareness). Flip to True after the Task 11
# A/B benchmark confirms no regressions.
USE_TWO_STAGE_EXTRACTION = True

# ───────────────────────────────────────────────────────────────
#  Hallucination verification
# ───────────────────────────────────────────────────────────────

# Minimum fraction of factual sentences that must be verified as exact
# substrings of the raw source text before a summary is accepted.
# Environment variable: HALLUCINATION_CONFIDENCE_THRESHOLD
HALLUCINATION_CONFIDENCE_THRESHOLD = float(
    os.environ.get("HALLUCINATION_CONFIDENCE_THRESHOLD", "0.90")
)

# Maximum repair attempts when hallucination confidence is below the
# threshold. Environment variable: MAX_HALLUCINATION_REPAIR_RETRIES
MAX_HALLUCINATION_REPAIR_RETRIES = int(
    os.environ.get("MAX_HALLUCINATION_REPAIR_RETRIES", "2")
)

# ───────────────────────────────────────────────────────────────
#  Retrieval-answer grounding (research_agent)
# ───────────────────────────────────────────────────────────────

# Minimum fraction of the retrieval agent's answer sentences that must be
# grounded in the evidence it actually retrieved before the answer is
# returned. Lower than the ingestion threshold (0.90) because retrieval
# answers legitimately paraphrase and synthesise across multiple pages and
# are checked against retrieved snippets rather than a full source document.
# Environment variable: RETRIEVAL_GROUNDING_THRESHOLD
RETRIEVAL_GROUNDING_THRESHOLD = float(
    os.environ.get("RETRIEVAL_GROUNDING_THRESHOLD", "0.75")
)

# Maximum re-synthesis attempts when a retrieval answer fails the grounding
# or citation-existence checks. Environment variable:
# RETRIEVAL_GROUNDING_MAX_RETRIES
RETRIEVAL_GROUNDING_MAX_RETRIES = int(
    os.environ.get("RETRIEVAL_GROUNDING_MAX_RETRIES", "2")
)
