"""Centralized LLM Configuration & Provider Registry for Antigravity Workspace.

Single source of truth for LLM models, provider endpoints, credentials,
context windows, and token limits across all subprojects (paper_agent,
research-wiki, PageIndex, scripts, exam_prep).

Updating the model or provider here (or via LLM_MODEL/LLM_PROVIDER in .env)
automatically applies to all consumers across the repository.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from dotenv import load_dotenv

# Canonical workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent

# Load .env without overriding explicitly provided shell/process environment
load_dotenv(WORKSPACE_ROOT / ".env", override=False)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Provider Presets & Registry
# ─────────────────────────────────────────────────────────────────────────────

PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "justwoker": {
        "name": "Justwoker (Scrapped / Non-Functional)",
        "base_url": "https://api.justwoker.icu/v1",
        "default_model": "claude-opus-5-thinking",
        "default_long_context_model": "claude-opus-5-thinking",
        "env_key_names": ["JUSTWOKER_API_KEY", "LLM_API_KEYS", "LLM_API_KEY"],
        "active": False,
        "disabled": True,
        "disabled_reason": "Justwoker (api.justwoker.icu) is permanently non-functional: Cloudflare WAF HTTP 403 challenge on chat completions and empty /v1/models list. Decommissioned and scrapped.",
    },
    "general_compute": {
        "name": "General Compute",
        "base_url": "https://api.generalcompute.com/v1",
        "default_model": "minimax-m2.7",
        "default_long_context_model": "minimax-m2.7",
        "env_key_names": ["GENERAL_COMPUTE_API_KEYS", "GENERAL_COMPUTE_API_KEY", "LLM_API_KEYS", "LLM_API_KEY"],
    },
    "hcnsec": {
        "name": "HCN SEC (Archived / Inactive)",
        "base_url": "https://api.hcnsec.cn/v1",
        "default_model": "kat-coder-pro-v2.5",
        "default_long_context_model": "kat-coder-pro-v2.5",
        "env_key_names": ["HCN_SEC_API_KEYS", "HCN_SEC_API_KEY"],
        "active": False,
        "disabled": True,
        "disabled_reason": "HCN SEC (api.hcnsec.cn) unrouted / HTTP 401 authentication rejection. Archived as inactive.",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "default_long_context_model": "gpt-4o",
        "env_key_names": ["OPENAI_API_KEY", "OPENAI_API_KEYS", "LLM_API_KEYS", "LLM_API_KEY"],
    },
    "deepseek": {
        "name": "DeepSeek Official",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "default_long_context_model": "deepseek-chat",
        "env_key_names": ["DEEPSEEK_API_KEY", "DEEPSEEK_API_KEYS", "LLM_API_KEYS", "LLM_API_KEY"],
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "default_long_context_model": "llama-3.3-70b-versatile",
        "env_key_names": ["GROQ_API_KEY", "GROQ_API_KEYS", "LLM_API_KEYS", "LLM_API_KEY"],
    },
    "ollama": {
        "name": "Ollama Local",
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.1:latest",
        "default_long_context_model": "llama3.1:latest",
        "env_key_names": ["OLLAMA_API_KEY", "LLM_API_KEY"],
    },
    "apinex": {
        "name": "APInex",
        "base_url": "https://api.apinex.bond/v1",
        "default_model": "deepseek-v4-flash",
        "default_long_context_model": "deepseek-v4-flash",
        "env_key_names": ["APINEX_API_KEY", "LLM_API_KEYS", "LLM_API_KEY"],
    },
    "custom": {
        "name": "Custom OpenAI-Compatible Endpoint",
        "base_url": "https://api.generalcompute.com/v1",
        "default_model": "minimax-m2.7",
        "default_long_context_model": "minimax-m2.7",
        "env_key_names": ["LLM_API_KEYS", "LLM_API_KEY", "GENERAL_COMPUTE_API_KEYS", "OPENAI_API_KEY"],
    },
    "bluesminds": {
        "name": "Bluesminds (Archived / Inactive)",
        "base_url": "https://api.bluesminds.com/v1",
        "default_model": "gpt-5.6-terra",
        "default_long_context_model": "gpt-5.6-terra",
        "env_key_names": ["BLUESMINDS_API_KEY", "BLUESMINDS_API_KEYS", "LLM_API_KEYS", "LLM_API_KEY"],
        "active": False,
        "disabled": True,
        "disabled_reason": "Bluesminds proxy endpoints suffer from high latency, TLS timeouts, and queue stalls. Archived as inactive.",
    },
}

DEFAULT_PROVIDER = "general_compute"
FALLBACK_MODEL = "minimax-m2.7"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Model Limits & Capabilities Registry
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_MODEL_OUTPUT_LIMITS: dict[str, int] = {
    "claude-opus-4-8": 16384,
    "claude-opus-4-8-thinking": 50000,
    "claude-opus-5": 16384,
    "claude-opus-5-thinking": 50000,
    "kat-coder-pro-v2.5": 8192,
    "gpt-oss-120b": 8192,
    "minimax-m2.7": 128000,
    "deepseek-v3.2": 8192,
    "deepseek-v3.1": 8192,
    "deepseek-chat": 8192,
    "deepseek-reasoner": 8192,
    "Qwen3.6-35B-A3B": 32768,
    "gpt-4o": 16384,
    "gpt-4o-mini": 16384,
    "DeepSeek-V4-Pro": 16384,
    "DeepSeek-V4-Flash": 16384,
    "deepseek-v4-pro": 16384,
    "deepseek-v4-flash": 16384,
    "claude-sonnet-5": 16384,
    "gemini-2.5-flash": 65536,
    "step-router-v1": 32768,
    "step-3.7-flash": 32768,
    "step-explore": 32768,
    "Qwen3.8-27B": 16384,
    "MiniMax-M3": 16384,
    "kimi-k3": 16384,
    "glm-4.5-air": 8192,
    "claude-sonnet-5": 16384,
    "gemini-2.5-pro": 65536,
    "gemini-3.8-flash": 65536,
    "gemini-flash": 65536,
}

KNOWN_MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "claude-opus-4-8": 200000,
    "claude-opus-4-8-thinking": 200000,
    "claude-opus-5": 200000,
    "claude-opus-5-thinking": 200000,
    "kat-coder-pro-v2.5": 128000,
    "DeepSeek-V4-Pro": 128000,
    "DeepSeek-V4-Flash": 128000,
    "deepseek-v4-pro": 128000,
    "deepseek-v4-flash": 128000,
    "claude-sonnet-5": 200000,
    "gemini-2.5-flash": 1048576,
    "step-router-v1": 256000,
    "step-3.7-flash": 256000,
    "step-explore": 256000,
    "Qwen3.8-27B": 128000,
    "MiniMax-M3": 128000,
    "kimi-k3": 128000,
    "glm-4.5-air": 128000,
    "gpt-oss-120b": 131072,
    "minimax-m2.7": 192000,
    "deepseek-v3.2": 65536,
    "deepseek-v3.1": 65536,
    "deepseek-chat": 65536,
    "deepseek-reasoner": 65536,
    "Qwen3.6-35B-A3B": 131072,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "claude-sonnet-5": 200000,
    "gemini-2.5-pro": 2097152,
    "gemini-3.8-flash": 1048576,
    "gemini-flash": 1048576,
}

SUPPORTED_MODEL_PRESETS: frozenset[str] = frozenset(
    set(KNOWN_MODEL_OUTPUT_LIMITS.keys())
    | {"auto", "DeepSeek-V4-Flash", "DeepSeek-V4-Pro", "glm-5.2", "llama-3.3-70b-versatile"}
)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Dynamic Resolvers
# ─────────────────────────────────────────────────────────────────────────────

def get_provider() -> str:
    """Return the active provider key (e.g. 'justwoker', 'openrouter', 'openai', 'gemini')."""
    configured = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if configured and configured in PROVIDER_PRESETS:
        return configured

    explicit_base = (
        os.environ.get("LLM_BASE_URL")
        or os.environ.get("AEROLINK_BASE_URL")
        or os.environ.get("HCN_SEC_BASE_URL")
        or os.environ.get("GENERAL_COMPUTE_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
        or ""
    ).lower()

    if "bluesminds" in explicit_base:
        return "bluesminds"
    if "justwoker" in explicit_base:
        return "justwoker"
    if "generalcompute" in explicit_base:
        return "general_compute"
    if "hcnsec" in explicit_base:
        return "hcnsec"
    if "openrouter" in explicit_base:
        return "openrouter"
    if "api.openai.com" in explicit_base:
        return "openai"
    if "deepseek.com" in explicit_base:
        return "deepseek"
    if "groq.com" in explicit_base:
        return "groq"
    if "localhost:11434" in explicit_base or "127.0.0.1:11434" in explicit_base:
        return "ollama"

    return DEFAULT_PROVIDER


def get_base_url(endpoint: str = "") -> str:
    """Return normalized base URL or full endpoint URL."""
    provider_name = get_provider()
    preset_url = PROVIDER_PRESETS.get(provider_name, {}).get("base_url", "https://api.generalcompute.com/v1")

    base = (
        os.environ.get("LLM_BASE_URL")
        or os.environ.get("AEROLINK_BASE_URL")
        or os.environ.get("HCN_SEC_BASE_URL")
        or os.environ.get("GENERAL_COMPUTE_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
        or preset_url
    ).strip()

    if base.endswith("/"):
        base = base[:-1]

    if not endpoint:
        if base.endswith("/chat/completions"):
            base = base[:-len("/chat/completions")]
        return base

    endpoint_clean = endpoint.strip("/")
    if base.endswith(f"/{endpoint_clean}"):
        return base
    return f"{base}/{endpoint_clean}"


def get_chat_completions_url() -> str:
    """Return the exact chat/completions endpoint URL."""
    return get_base_url("chat/completions")


def get_model(default: str | None = None) -> str:
    """Return the active master model name across the entire workspace.
    
    Resolution order:
    1. LLM_MODEL
    2. AEROLINK_MODEL
    3. HCN_SEC_MODEL
    4. GENERAL_COMPUTE_MODEL
    5. RAG_MODEL
    6. RESEARCH_AGENT_MODEL
    7. AI_MODEL
    8. OPENAI_MODEL
    9. Provider preset default model
    10. FALLBACK_MODEL ('claude-opus-5-thinking')
    """
    provider_name = get_provider()
    provider_default = PROVIDER_PRESETS.get(provider_name, {}).get("default_model", FALLBACK_MODEL)

    model = (
        os.environ.get("LLM_MODEL")
        or os.environ.get("AEROLINK_MODEL")
        or os.environ.get("HCN_SEC_MODEL")
        or os.environ.get("GENERAL_COMPUTE_MODEL")
        or os.environ.get("RAG_MODEL")
        or os.environ.get("RESEARCH_AGENT_MODEL")
        or os.environ.get("AI_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or default
        or provider_default
        or FALLBACK_MODEL
    ).strip()

    return model


def get_long_context_model(default: str | None = None) -> str:
    """Return model used when context length is exceeded."""
    provider_name = get_provider()
    provider_default = PROVIDER_PRESETS.get(provider_name, {}).get("default_long_context_model", get_model())

    return (
        os.environ.get("LLM_LONG_CONTEXT_MODEL")
        or os.environ.get("AEROLINK_LONG_CONTEXT_MODEL")
        or os.environ.get("HCN_SEC_LONG_CONTEXT_MODEL")
        or os.environ.get("GENERAL_COMPUTE_LONG_CONTEXT_MODEL")
        or default
        or provider_default
        or get_model()
    ).strip()


def get_filter_model(default: str | None = None) -> str:
    """Return model used for fast filtering and ranking."""
    return (
        os.environ.get("LLM_FILTER_MODEL")
        or os.environ.get("PAPER_AGENT_FILTERING_MODEL")
        or os.environ.get("GENERAL_COMPUTE_FILTER_MODEL")
        or os.environ.get("FILTER_MODEL")
        or default
        or get_model()
    ).strip()


def get_vision_model(default: str | None = None) -> str:
    """Return model used for multimodal / vision tasks."""
    return (
        os.environ.get("LLM_VISION_MODEL")
        or os.environ.get("GENERAL_COMPUTE_VISION_MODEL")
        or os.environ.get("VISION_MODEL")
        or default
        or get_model()
    ).strip()


def get_api_keys() -> list[str]:
    """Return list of valid API keys for round-robin rotation."""
    provider_name = get_provider()
    preset_keys = PROVIDER_PRESETS.get(provider_name, {}).get("env_key_names", [])
    env_keys_to_check = [
        *preset_keys,
        "LLM_API_KEYS",
        "LLM_API_KEY",
        "JUSTWOKER_API_KEY",
        "AEROLINK_API_KEYS",
        "HCN_SEC_API_KEYS",
        "GENERAL_COMPUTE_API_KEYS",
        "GENERAL_COMPUTE_API_KEY",
        "OPENAI_API_KEY",
    ]

    for env_name in env_keys_to_check:
        raw_val = os.environ.get(env_name, "").strip()
        if raw_val:
            keys = [k.strip() for k in re.split(r"[,;\s]+", raw_val) if k.strip()]
            if keys:
                return keys

    return []


def get_primary_api_key() -> str:
    """Return the first available API key or empty string."""
    keys = get_api_keys()
    return keys[0] if keys else ""


def get_max_output_tokens(model: str | None = None) -> int:
    """Return max completion token ceiling for a model."""
    m = model or get_model()
    if m in KNOWN_MODEL_OUTPUT_LIMITS:
        limit = KNOWN_MODEL_OUTPUT_LIMITS[m]
    elif "thinking" in m.lower() or "reason" in m.lower():
        limit = 50000
    else:
        limit = 8192

    env_override = os.environ.get("LLM_MAX_OUTPUT_TOKENS") or os.environ.get("GENERAL_COMPUTE_MAX_OUTPUT_TOKENS")
    if env_override and env_override.strip().isdigit():
        return int(env_override)

    return limit


def get_context_length(model: str | None = None) -> int:
    """Return estimated input context window in tokens."""
    m = model or get_model()
    if m in KNOWN_MODEL_CONTEXT_LIMITS:
        return KNOWN_MODEL_CONTEXT_LIMITS[m]
    if "thinking" in m.lower() or "claude" in m.lower():
        return 200000
    if "flash" in m.lower() or "gemini" in m.lower():
        return 1000000
    return 128000


def is_supported_model(model: str | None) -> bool:
    """Validate whether model string is usable.
    
    Accepts all non-empty model names so new models work out-of-the-box
    without manual code edits.
    """
    if not model or not isinstance(model, str):
        return False
    return bool(model.strip())


# ─────────────────────────────────────────────────────────────────────────────
# 4. CLI / Programmatic Mutation Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_config_summary() -> dict[str, Any]:
    """Return full active configuration dictionary."""
    keys = get_api_keys()
    masked_keys = [f"{k[:6]}...{k[-4:]}" if len(k) > 10 else "***" for k in keys]
    model = get_model()
    return {
        "provider": get_provider(),
        "base_url": get_base_url(),
        "chat_completions_url": get_chat_completions_url(),
        "model": model,
        "long_context_model": get_long_context_model(),
        "filter_model": get_filter_model(),
        "vision_model": get_vision_model(),
        "max_output_tokens": get_max_output_tokens(model),
        "context_length_tokens": get_context_length(model),
        "key_count": len(keys),
        "keys_preview": masked_keys,
    }


def update_env_file(updates: Mapping[str, str]) -> Path:
    """Update or append keys in workspace .env file."""
    env_path = WORKSPACE_ROOT / ".env"
    lines: list[str] = []
    found_keys: set[str] = set()

    if env_path.exists():
        with env_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, _ = stripped.split("=", 1)
            k = k.strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}\n")
                found_keys.add(k)
                continue
        new_lines.append(line)

    remaining = [k for k in updates if k not in found_keys]
    if remaining:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append("\n# Added by Unified LLM Config\n")
        for k in remaining:
            new_lines.append(f"{k}={updates[k]}\n")

    with env_path.open("w", encoding="utf-8") as f:
        f.writelines(new_lines)

    for k, v in updates.items():
        os.environ[k] = str(v)

    return env_path
