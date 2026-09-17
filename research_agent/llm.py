"""Thin OpenAI-compatible chat client for General Compute.

Reads keys from antigravity's .env (or llm_config), round-robins across them
with exponential backoff and robust handling for HTTP 403 / 429 / 5xx,
and falls back cleanly if no key is available.
Standard library only — no external dependencies.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ANTIGRAVITY_ROOT = os.environ.get(
    "ANTIGRAVITY_ROOT", os.path.expanduser("~/Desktop/antigravity")
)
if str(ANTIGRAVITY_ROOT) not in sys.path:
    sys.path.insert(0, str(ANTIGRAVITY_ROOT))

try:
    import llm_config
except ImportError:
    llm_config = None

_BASE_URL = "https://api.generalcompute.com/v1"
_MODEL = "minimax-m2.7"
_KEYS: list[str] = []
_cursor = 0
_SOCKET_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "15"))


def _parse_env() -> None:
    global _BASE_URL, _MODEL, _KEYS
    if llm_config is not None:
        try:
            _BASE_URL = llm_config.get_base_url()
            _MODEL = llm_config.get_model()
            _KEYS = llm_config.get_api_keys()
            return
        except Exception:
            pass

    env_path = Path(ANTIGRAVITY_ROOT) / ".env"
    if not env_path.is_file():
        return
    env = {}
    try:
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    except Exception:
        return

    _BASE_URL = env.get("LLM_BASE_URL", env.get("GENERAL_COMPUTE_BASE_URL", _BASE_URL))
    _MODEL = env.get("LLM_MODEL", env.get("RESEARCH_AGENT_MODEL", env.get("RAG_MODEL", _MODEL)))
    raw_keys = env.get("LLM_API_KEYS", env.get("GENERAL_COMPUTE_API_KEYS", env.get("LLM_API_KEY", "")))
    _KEYS = [k.strip() for k in re.split(r"[,;\s]+", raw_keys) if k.strip()]


def has_key() -> bool:
    _parse_env()
    return bool(_KEYS)


# The justwoker.icu gateway rejects requests carrying urllib's default
# "Python-urllib/x.y" User-Agent with HTTP 403; any explicit UA passes.
_USER_AGENT = "antigravity-research-agent/1.0"


def _message_content(message: dict) -> str | None:
    """Extract answer text, tolerating reasoning models that may return the
    final answer in a dedicated reasoning field when content is null."""
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    for field in ("reasoning_content", "reasoning"):
        value = message.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _get_retry_delay(err: urllib.error.HTTPError | Exception, attempt: int) -> float:
    """Determine appropriate backoff delay in seconds based on error type and headers."""
    if isinstance(err, urllib.error.HTTPError):
        # Check for Retry-After header
        retry_after = err.headers.get("Retry-After") if err.headers else None
        if retry_after:
            try:
                return max(0.5, min(float(retry_after), 10.0))
            except (ValueError, TypeError):
                pass
        if err.code == 429:
            # Exponential backoff for rate limiting: 0.5s, 1.0s, 2.0s, max 6.0s
            return min(0.5 * (2 ** attempt), 6.0)
        if err.code in (401, 403):
            # Fast failover to next key
            return 0.05
        if err.code >= 500:
            # Server error backoff
            return min(0.5 * (attempt + 1), 3.0)
    return min(0.25 * (attempt + 1), 2.0)


def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4000,
) -> str:
    """Send a chat completion.

    Rotates across all available API keys with exponential backoff for 429/403/5xx errors.
    Raises LLMUnavailable if no key is configured or all attempts fail.
    """
    _parse_env()
    if not _KEYS:
        return _no_llm_fallback(messages)

    # Bluesminds endpoint is archived / non-functional
    if "bluesminds.com" in _BASE_URL or (os.environ.get("DISABLE_BLUESMINDS", "1") == "1" and "bluesminds" in _BASE_URL):
        return _no_llm_fallback(messages)

    global _cursor
    url = f"{_BASE_URL}/chat/completions"
    payload = json.dumps({
        "model": model or _MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    max_attempts = max(len(_KEYS) * 2, 3)
    last_err: Exception | None = None

    for attempt in range(max_attempts):
        key_idx = (_cursor + attempt) % len(_KEYS)
        key = _KEYS[key_idx]
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": _USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=_SOCKET_TIMEOUT) as resp:
                body = json.loads(resp.read().decode("utf-8", errors="replace"))
            choices = body.get("choices") or []
            if not choices:
                last_err = LLMUnavailable(f"empty choices in LLM response: {body}")
                delay = _get_retry_delay(last_err, attempt)
                if delay > 0 and attempt < max_attempts - 1:
                    time.sleep(delay)
                continue

            message = choices[0].get("message") or {}
            content = _message_content(message)
            if content is None:
                # Reasoning models can exhaust max_completion_tokens before emitting content
                last_err = LLMUnavailable(
                    f"empty completion content (finish_reason="
                    f"{choices[0].get('finish_reason')!r}, "
                    f"usage={body.get('usage')})"
                )
                delay = _get_retry_delay(last_err, attempt)
                if delay > 0 and attempt < max_attempts - 1:
                    time.sleep(delay)
                continue

            # Advance global cursor past the successful key
            _cursor = (key_idx + 1) % len(_KEYS)
            return content

        except urllib.error.HTTPError as e:
            last_err = e
            delay = _get_retry_delay(e, attempt)
            if delay > 0 and attempt < max_attempts - 1:
                time.sleep(delay)
            continue
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
            last_err = e
            delay = _get_retry_delay(e, attempt)
            if delay > 0 and attempt < max_attempts - 1:
                time.sleep(delay)
            continue
        except Exception as e:
            last_err = e
            delay = _get_retry_delay(e, attempt)
            if delay > 0 and attempt < max_attempts - 1:
                time.sleep(delay)
            continue

    raise LLMUnavailable(f"All {len(_KEYS)} keys failed after {max_attempts} attempts: {last_err}")


def chat_stream(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 3000,
):
    """Stream chat completion tokens. Yields string chunks as they arrive."""
    _parse_env()
    if not _KEYS:
        yield _no_llm_fallback(messages)
        return

    # Bluesminds endpoint is archived / non-functional
    if "bluesminds.com" in _BASE_URL or (os.environ.get("DISABLE_BLUESMINDS", "1") == "1" and "bluesminds" in _BASE_URL):
        yield _no_llm_fallback(messages)
        return

    global _cursor
    url = f"{_BASE_URL}/chat/completions"
    payload = json.dumps({
        "model": model or _MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }).encode("utf-8")

    max_attempts = max(len(_KEYS) * 2, 3)
    last_err: Exception | None = None

    for attempt in range(max_attempts):
        key_idx = (_cursor + attempt) % len(_KEYS)
        key = _KEYS[key_idx]
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": _USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=_SOCKET_TIMEOUT) as resp:
                _cursor = (key_idx + 1) % len(_KEYS)
                for line in resp:
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if not line_str or line_str.startswith(":") or line_str == "data: [DONE]":
                        continue
                    if line_str.startswith("data: "):
                        try:
                            chunk = json.loads(line_str[6:])
                            if chunk.get("choices") and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {}).get("content", "")
                                if delta:
                                    yield delta
                        except json.JSONDecodeError:
                            continue
                return
        except urllib.error.HTTPError as e:
            last_err = e
            delay = _get_retry_delay(e, attempt)
            if delay > 0 and attempt < max_attempts - 1:
                time.sleep(delay)
            continue
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last_err = e
            delay = _get_retry_delay(e, attempt)
            if delay > 0 and attempt < max_attempts - 1:
                time.sleep(delay)
            continue
        except Exception as e:
            last_err = e
            delay = _get_retry_delay(e, attempt)
            if delay > 0 and attempt < max_attempts - 1:
                time.sleep(delay)
            continue

    raise LLMUnavailable(f"All keys failed for streaming after {max_attempts} attempts: {last_err}")


class LLMUnavailable(Exception):
    pass


def _no_llm_fallback(messages: list[dict]) -> str:
    return "[LLM unavailable — tools-only mode]"


