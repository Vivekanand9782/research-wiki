"""General Compute LLM client used by Research Wiki.

The module accepts ``GENERAL_COMPUTE_API_KEYS`` credentials (round-robin)
and falls back to ``GENERAL_COMPUTE_API_KEY``.  It preserves the small
Gemini-style ``genai_client.models.generate_content`` surface used by
existing callers while sending OpenAI-compatible chat-completion payloads
to the workspace chat-completions endpoint (default ``https://api.generalcompute.com/v1``, minimax-m2.7).
"""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import os
import re
import threading
import time
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv
import sys
from requests.adapters import HTTPAdapter

# The workspace root owns the canonical .env. Explicit process values win.
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

load_dotenv(_WORKSPACE_ROOT / ".env", override=False)

import config
import llm_config


_CONTEXT_ERROR_MARKERS = (
    "context_length_exceeded",
    "maximum context length",
    "too many tokens",
    "prompt is too long",
    "context window",
)
# 403 is emitted intermittently by the justwoker.icu WAF on otherwise
# valid requests; retries with backoff succeed, so treat it as transient.
_RETRYABLE_STATUS_CODES = {403, 408, 409, 425, 429}
_DEFAULT_MODEL = llm_config.get_model()
_DEFAULT_LONG_CONTEXT_MODEL = llm_config.get_long_context_model()
_SUPPORTED_MODELS = frozenset(
    set(llm_config.SUPPORTED_MODEL_PRESETS)
    | {_DEFAULT_MODEL, _DEFAULT_LONG_CONTEXT_MODEL, "claude-opus-5-thinking", "gpt-oss-120b", "minimax-m2.7", "deepseek-v3.2", "deepseek-v3.1", "Qwen3.6-35B-A3B"}
)
_MODEL_OUTPUT_LIMITS = dict(llm_config.KNOWN_MODEL_OUTPUT_LIMITS)
# General Compute per-key token budget. The client paces requests per key
# so a rolling one-minute window stays under this minus a safety headroom,
# avoiding 429s that a pure RPM backoff cannot prevent.
_TPM_WINDOW_SECONDS = 60.0

# Group-wide request pacer. General Compute publishes a per-minute request
# limit (60 RPM per credential), not a multi-hour request-count quota, so this
# window is one minute. Real pacing is per key (cooldowns + TPM headroom); this
# is only a pool-wide ceiling that stops a runaway worker pool. The old
# 300-minute window was an HCN SEC artifact and turned a transient limit into a
# multi-hour stall once the count was spent.
_REQ_WINDOW_SECONDS = 60.0
_request_times: list[float] = []
_request_times_lock = threading.Lock()
_http_local = threading.local()
_provider_circuit_lock = threading.Lock()
_provider_circuit_until = 0.0


class GeneralComputeError(RuntimeError):
    """Sanitized provider or local configuration error."""

    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class _ProviderCircuitOpen(GeneralComputeError):
    """Internal signal used to stop workers queued behind a known outage."""

    def __init__(self) -> None:
        super().__init__(
            "General Compute is temporarily unavailable after a recent "
            "transient failure; retry after the provider cooldown.",
            retryable=True,
        )


def _raise_if_provider_circuit_open() -> None:
    with _provider_circuit_lock:
        if time.monotonic() < _provider_circuit_until:
            raise _ProviderCircuitOpen()


def _open_provider_circuit(cooldown: float | None = None) -> None:
    cfg = (
        float(getattr(config, "GENERAL_COMPUTE_OUTAGE_COOLDOWN_SECONDS", 30.0))
        if cooldown is None
        else max(0.0, cooldown)
    )
    if cfg <= 0:
        return
    global _provider_circuit_until
    with _provider_circuit_lock:
        _provider_circuit_until = max(
            _provider_circuit_until, time.monotonic() + cfg
        )


def _reset_provider_circuit() -> None:
    """Close the outage circuit after success (also useful for isolated tests)."""
    global _provider_circuit_until
    with _provider_circuit_lock:
        _provider_circuit_until = 0.0


def _reserve_request_slot() -> None:
    """Atomically reserve one request in the group-wide per-minute window.

    The quota check and reservation happen under one lock, so concurrent
    workers cannot all pass the check before any request is recorded. Sleeps
    occur after releasing the lock and before any network request is sent.
    """
    max_requests = max(
        1,
        int(getattr(config, "GENERAL_COMPUTE_MAX_REQ_PER_WINDOW", 300)),
    )
    # Reserve a small headroom so we stop *before* the provider hard-stops us.
    budget = max(1, int(max_requests * 0.95))
    while True:
        now = time.monotonic()
        with _request_times_lock:
            cutoff = now - _REQ_WINDOW_SECONDS
            _request_times[:] = [t for t in _request_times if t > cutoff]
            if len(_request_times) < budget:
                _request_times.append(now)
                return
            oldest = min(_request_times)
        sleep_for = max(0.5, _REQ_WINDOW_SECONDS - (time.monotonic() - oldest))
        time.sleep(min(sleep_for, 60.0))


def _validate_model(model: str) -> str:
    candidate = model.strip()
    if candidate not in _SUPPORTED_MODELS:
        supported = ", ".join(sorted(_SUPPORTED_MODELS))
        raise GeneralComputeError(
            f"Unsupported General Compute model '{candidate}'. Supported models: {supported}."
        )
    return candidate


def _split_keys(raw: str) -> list[str]:
    """Split comma/newline/whitespace-separated credentials."""
    return [value.strip() for value in raw.replace(",", " ").split() if value.strip()]


def _configured_api_keys() -> list[str]:
    raw = (
        os.environ.get("LLM_API_KEYS")
        or os.environ.get("AEROLINK_API_KEYS")
        or os.environ.get("HCN_SEC_API_KEYS")
        or os.environ.get("GENERAL_COMPUTE_API_KEYS")
        or os.environ.get("GENERAL_COMPUTE_API_KEY")
        or ""
    )
    # Preserve order while preventing accidental duplicate slots.
    return list(dict.fromkeys(_split_keys(raw)))


def _get_general_compute_base_url() -> str:
    base_url = (
        os.environ.get("AEROLINK_BASE_URL")
        or os.environ.get("HCN_SEC_BASE_URL")
        or os.environ.get("GENERAL_COMPUTE_BASE_URL")
        or getattr(config, "GENERAL_COMPUTE_BASE_URL", None)
        or llm_config.get_base_url()
    ).strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def _resolve_model(model: Optional[str] = None) -> str:
    candidate = (
        model
        or os.environ.get("AEROLINK_MODEL")
        or os.environ.get("GENERAL_COMPUTE_MODEL")
        or getattr(config, "GENERAL_COMPUTE_MODEL", None)
        or getattr(config, "AI_MODEL", None)
        or llm_config.get_model()
    )
    return _validate_model(str(candidate))


def _resolve_long_context_model() -> str:
    candidate = (
        os.environ.get("AEROLINK_LONG_CONTEXT_MODEL")
        or os.environ.get("GENERAL_COMPUTE_LONG_CONTEXT_MODEL")
        or getattr(config, "GENERAL_COMPUTE_LONG_CONTEXT_MODEL", None)
        or llm_config.get_long_context_model()
    )
    return _validate_model(str(candidate))


def _get_http_session() -> requests.Session:
    """Return one connection-pooled HTTP session per worker thread."""
    session = getattr(_http_local, "session", None)
    if session is None:
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=0)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _http_local.session = session
    return session


def _reset_http_session() -> None:
    """Discard this worker's pool after DNS/socket/TLS transport failures."""
    session = getattr(_http_local, "session", None)
    if session is not None:
        try:
            session.close()
        finally:
            delattr(_http_local, "session")


def _config_value(config_obj: Any, key: str, default: Any = None) -> Any:
    if config_obj is None:
        return default
    if isinstance(config_obj, dict):
        return config_obj.get(key, default)
    return getattr(config_obj, key, default)


def _normalise_instruction(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (list, tuple)):
        text = "\n".join(str(item) for item in value if item is not None).strip()
        return text or None
    text = getattr(value, "text", None)
    return str(text if text is not None else value).strip() or None


def _encode_image_part(part: Any) -> Optional[dict[str, Any]]:
    if isinstance(part, dict):
        inline_data = part.get("inline_data") or part.get("inlineData")
    else:
        inline_data = getattr(part, "inline_data", None)
    if inline_data is None:
        return None

    if isinstance(inline_data, dict):
        mime_type = inline_data.get("mime_type") or inline_data.get("mimeType")
        data = inline_data.get("data")
    else:
        mime_type = getattr(inline_data, "mime_type", None)
        data = getattr(inline_data, "data", None)
    mime_type = str(mime_type or "image/png")
    if isinstance(data, str):
        encoded = data
    elif isinstance(data, (bytes, bytearray, memoryview)):
        encoded = base64.b64encode(bytes(data)).decode("ascii")
    else:
        return None
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
    }


def _convert_content_part(part: Any) -> dict[str, Any]:
    image_part = _encode_image_part(part)
    if image_part is not None:
        return image_part
    if isinstance(part, dict):
        if part.get("type") in {"text", "image_url"}:
            return dict(part)
        text = part.get("text")
        if text is not None:
            return {"type": "text", "text": str(text)}
    elif hasattr(part, "text"):
        return {"type": "text", "text": str(part.text)}
    return {"type": "text", "text": str(part)}


def _convert_to_openai_messages(
    contents: Any,
    system_instruction: Any = None,
) -> list[dict[str, Any]]:
    """Convert existing text/inline-data inputs to OpenAI chat messages."""
    messages: list[dict[str, Any]] = []
    instruction = _normalise_instruction(system_instruction)
    if instruction:
        messages.append({"role": "system", "content": instruction})

    if isinstance(contents, str):
        user_content: Any = contents
    elif isinstance(contents, (list, tuple)):
        user_content = [_convert_content_part(item) for item in contents]
    elif contents is None:
        user_content = ""
    else:
        user_content = str(getattr(contents, "text", contents))
    messages.append({"role": "user", "content": user_content})
    return messages


def _is_thinking_enabled(thinking: Any) -> bool:
    """Normalize bool and Gemini-style thinking configurations."""
    t_type = _config_value(thinking, "type")
    if t_type is not None:
        value = getattr(t_type, "value", t_type)
        normalized = str(value).strip().lower()
        if normalized == "enabled":
            return True
        if normalized == "disabled":
            return False
    enabled = _config_value(thinking, "enabled")
    return bool(enabled) if enabled is not None else bool(thinking)


def _apply_thinking_params(
    params: dict[str, Any],
    thinking: Any = None,
    chat_template_kwargs: Any = None,
) -> None:
    """Merge template options, then apply explicit thinking configuration."""
    merged = dict(params.get("chat_template_kwargs") or {})
    if chat_template_kwargs is not None:
        merged.update(dict(chat_template_kwargs))
    if thinking is not None:
        merged["enable_thinking"] = _is_thinking_enabled(thinking)
        params["thinking"] = thinking
    if merged or chat_template_kwargs is not None:
        params["chat_template_kwargs"] = merged


def _extract_params(config_obj: Any) -> dict[str, Any]:
    """Extract supported generation parameters from dicts or config objects."""
    params: dict[str, Any] = {}
    temperature = _config_value(config_obj, "temperature")
    top_p = _config_value(config_obj, "top_p")
    max_tokens = _config_value(config_obj, "max_tokens")
    if max_tokens is None:
        max_tokens = _config_value(config_obj, "max_output_tokens")
    response_format = _config_value(config_obj, "response_format")
    if (
        response_format is None
        and _config_value(config_obj, "response_mime_type") == "application/json"
    ):
        response_format = {"type": "json_object"}
    reasoning_split = _config_value(config_obj, "reasoning_split")
    thinking = _config_value(config_obj, "thinking")
    chat_template_kwargs = _config_value(config_obj, "chat_template_kwargs")

    if temperature is not None:
        params["temperature"] = float(temperature)
    if top_p is not None:
        params["top_p"] = float(top_p)
    if max_tokens is not None:
        params["max_tokens"] = int(max_tokens)
    if response_format is not None:
        params["response_format"] = response_format
    if reasoning_split is not None:
        params["reasoning_split"] = bool(reasoning_split)
    _apply_thinking_params(params, thinking, chat_template_kwargs)
    return params


class OpenAIResponseWrapper:
    """Compatibility response with optional sanitized generation metadata."""

    def __init__(
        self,
        text: str,
        *,
        reasoning: Optional[str] = None,
        usage: Optional[dict[str, Any]] = None,
    ):
        self._text = text
        self._reasoning = reasoning
        self._usage = dict(usage or {})

    @property
    def text(self) -> str:
        return self._text

    @property
    def reasoning(self) -> Optional[str]:
        """Provider-supplied reasoning, never logged by the client."""
        return self._reasoning

    @property
    def usage(self) -> dict[str, Any]:
        """Return a copy of non-secret token accounting metadata."""
        return dict(self._usage)


ResponseWrapper = OpenAIResponseWrapper


class RotatingOpenAIClient:
    """Thread-safe round-robin state for General Compute credentials."""

    def __init__(self, api_keys: Optional[list[str]] = None):
        self.api_keys = list(api_keys) if api_keys is not None else _configured_api_keys()
        self.keys = self.api_keys  # Compatibility with older diagnostics/tests.
        self.clients = self.api_keys
        self._cursor = 0
        self._disabled: set[int] = set()
        self._cooldown_until: dict[int, float] = {}
        # Per-key rolling token ledger: index -> list of (timestamp, tokens).
        self._token_ledger: dict[int, list[tuple[float, int]]] = {}
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self.api_keys)

    @property
    def current_index(self) -> int:
        with self._lock:
            return self._cursor % len(self.api_keys) if self.api_keys else 0

    def has_keys(self) -> bool:
        with self._lock:
            return any(i not in self._disabled for i in range(len(self.api_keys)))

    def record_usage(self, index: int, tokens: int) -> None:
        """Record tokens consumed by a completed request for TPM pacing."""
        if index < 0 or index >= len(self.api_keys) or tokens <= 0:
            return
        now = time.monotonic()
        with self._lock:
            ledger = self._token_ledger.setdefault(index, [])
            cutoff = now - _TPM_WINDOW_SECONDS
            ledger[:] = [entry for entry in ledger if entry[0] > cutoff]
            ledger.append((now, tokens))

    def tpm_used(self, index: int) -> int:
        """Sum of tokens recorded for this key in the rolling window."""
        if index < 0 or index >= len(self.api_keys):
            return 0
        now = time.monotonic()
        cutoff = now - _TPM_WINDOW_SECONDS
        with self._lock:
            ledger = self._token_ledger.setdefault(index, [])
            ledger[:] = [entry for entry in ledger if entry[0] > cutoff]
            return sum(tokens for _, tokens in ledger)

    def wait_for_tpm_headroom(self, index: int, max_tpm: int,
                              reserve: float = 0.0) -> None:
        """Sleep until this key's rolling TPM stays under the limit.

        ``reserve`` is a token allowance we expect the *next* request to
        consume, so pacing accounts for it before the request starts.
        """
        if index < 0 or index >= len(self.api_keys) or max_tpm <= 0:
            return
        if reserve <= 0:
            return
        while True:
            used = self.tpm_used(index)
            if used + reserve <= max_tpm:
                return
            # Space frees up when the oldest ledger entry ages out of the
            # rolling window. Sleep only until then; re-check afterwards.
            oldest = min(
                (ts for ts, _ in self._token_ledger.get(index, [])),
                default=None,
            )
            if oldest is None:
                return
            sleep_for = max(0.1, _TPM_WINDOW_SECONDS - (time.monotonic() - oldest))
            time.sleep(min(sleep_for, _TPM_WINDOW_SECONDS))

    def acquire_key(self) -> tuple[int, str]:
        """Reserve the next healthy key without ever exposing it in logs."""
        with self._lock:
            if not self.api_keys:
                raise GeneralComputeError(
                    "No General Compute API key configured. Set "
                    "GENERAL_COMPUTE_API_KEYS or GENERAL_COMPUTE_API_KEY."
                )
            now = time.monotonic()
            active: list[int] = []
            for offset in range(len(self.api_keys)):
                index = (self._cursor + offset) % len(self.api_keys)
                if index in self._disabled:
                    continue
                active.append(index)
                if self._cooldown_until.get(index, 0.0) <= now:
                    self._cursor = (index + 1) % len(self.api_keys)
                    return index, self.api_keys[index]
            if not active:
                raise GeneralComputeError("All configured General Compute API keys are unavailable.")
            # All active keys are cooling down. Select the one that becomes
            # available first; the transport retry delay is applied separately.
            index = min(active, key=lambda item: self._cooldown_until.get(item, now))
            self._cursor = (index + 1) % len(self.api_keys)
            return index, self.api_keys[index]

    def get_client(self) -> str:
        """Compatibility helper returning the next credential slot value."""
        return self.acquire_key()[1]

    def rotate_client(self) -> None:
        with self._lock:
            if self.api_keys:
                self._cursor = (self._cursor + 1) % len(self.api_keys)

    def mark_rate_limited(self, index: int, retry_after: float) -> None:
        with self._lock:
            if 0 <= index < len(self.api_keys):
                self._cooldown_until[index] = max(
                    self._cooldown_until.get(index, 0.0),
                    time.monotonic() + max(0.0, retry_after),
                )

    def cooldown_remaining(self, index: int) -> float:
        with self._lock:
            return max(
                0.0, self._cooldown_until.get(index, 0.0) - time.monotonic()
            )

    def disable_key(self, index: int) -> None:
        """Permanently disable the exact credential rejected by the provider."""
        with self._lock:
            if 0 <= index < len(self.api_keys):
                self._disabled.add(index)
                self._cooldown_until.pop(index, None)
                if self.api_keys and self._cursor == index:
                    self._cursor = (index + 1) % len(self.api_keys)

    # Compatibility names retained for older local diagnostics.
    kill_client = disable_key
    blacklist_key = disable_key


openai_rotating_client = RotatingOpenAIClient()


def _retry_after_seconds(response: Any, attempt: int) -> float:
    fallback = min(8.0, 0.5 * (2**attempt))
    if response is None:
        return fallback
    raw = getattr(response, "headers", {}).get("Retry-After")
    if not raw:
        return fallback
    try:
        return max(0.0, min(float(raw), 120.0))
    except (TypeError, ValueError):
        try:
            parsed = parsedate_to_datetime(raw)
            now = time.time()
            return max(0.0, min(parsed.timestamp() - now, 120.0))
        except (TypeError, ValueError, OverflowError):
            return fallback


def _is_context_error(response: Any) -> bool:
    body = str(getattr(response, "text", "") or "").lower()
    return any(marker in body for marker in _CONTEXT_ERROR_MARKERS)


def _is_rate_limit_error(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None)
    if status == 429:
        return True
    text = str(exc).lower()
    return (
        "429" in text
        or "rate limit" in text
        or "resource_exhausted" in text
        or "resource exhausted" in text
    )


def _is_openai_depletion_error(exc: BaseException) -> bool:
    """Compatibility classifier for exhausted/rate-limited provider slots."""
    status = getattr(exc, "status_code", None)
    return status in {401, 403, 429} or _is_rate_limit_error(exc)


def _response_text(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    choices = data.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return None
    message = choices[0].get("message") or {}
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces = []
        for part in content:
            if isinstance(part, dict) and part.get("text") is not None:
                pieces.append(str(part["text"]))
        return "".join(pieces) if pieces else None
    return str(content) if content is not None else None


def _response_reasoning(data: Any) -> Optional[str]:
    """Extract reasoning from General Compute or common compatible fields."""
    if not isinstance(data, dict):
        return None
    choices = data.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return None
    message = choices[0].get("message") or {}
    if not isinstance(message, dict):
        return None
    for key in ("reasoning", "reasoning_content"):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value
    details = message.get("reasoning_details") or []
    if isinstance(details, list):
        pieces = [
            str(item.get("text"))
            for item in details
            if isinstance(item, dict) and item.get("text") is not None
        ]
        if pieces:
            return "".join(pieces)
    return None


# Every caller in this process shares the same gate, including nested seed-page
# workers. This prevents outer PDF concurrency from multiplying into a burst of
# simultaneous provider requests.
_GENERAL_COMPUTE_GATE = threading.BoundedSemaphore(
    max(1, int(getattr(config, "GENERAL_COMPUTE_MAX_IN_FLIGHT", 1)))
)


def _timeout_tuple() -> tuple[float, float]:
    connect = float(
        getattr(config, "GENERAL_COMPUTE_CONNECT_TIMEOUT_SECONDS", 10.0)
    )
    read = float(getattr(config, "GENERAL_COMPUTE_READ_TIMEOUT_SECONDS", 120.0))
    return connect, read


def _bounded_attempts(retries: Any) -> int:
    configured_cap = max(1, int(getattr(config, "AI_MAX_TRANSPORT_ATTEMPTS", 5)))
    try:
        requested = max(1, int(retries))
    except (TypeError, ValueError):
        requested = configured_cap
    return min(requested, configured_cap)


def _retry_delay_seconds(response: Any, attempt: int) -> float:
    """Return Retry-After when supplied, otherwise configurable backoff."""
    if response is not None and getattr(response, "headers", {}).get("Retry-After"):
        return _retry_after_seconds(response, attempt)
    base = max(0.1, float(getattr(config, "GENERAL_COMPUTE_RETRY_BASE_SECONDS", 2.0)))
    cap = max(base, float(getattr(config, "GENERAL_COMPUTE_RETRY_MAX_SECONDS", 30.0)))
    return min(cap, base * (2**attempt))


def generate_content_with_retry(
    model: Optional[str],
    contents: Any,
    config_params: Any = None,
    retries: int = 5,
    system_instruction: Any = None,
    **kwargs: Any,
) -> OpenAIResponseWrapper:
    """Generate content through General Compute with bounded key rotation.

    Authentication rejections do not consume the transient transport budget,
    so every configured credential can be tried. Rate limits put only the
    rejected credential on cooldown. Once transient retries are exhausted, a
    short process-wide circuit stops workers already queued behind the outage.
    Provider bodies and credential values are never included in raised errors.
    """
    if config_params is None:
        config_params = kwargs.pop("config", None)
    if system_instruction is None:
        system_instruction = kwargs.pop("system_instruction", None)
    if system_instruction is None:
        system_instruction = _config_value(config_params, "system_instruction")

    params = _extract_params(config_params)
    for name in (
        "temperature",
        "top_p",
        "max_tokens",
        "max_output_tokens",
        "response_format",
        "reasoning_split",
    ):
        if name in kwargs and kwargs[name] is not None:
            target = "max_tokens" if name == "max_output_tokens" else name
            params[target] = kwargs[name]
    _apply_thinking_params(
        params,
        kwargs.get("thinking", params.get("thinking")),
        kwargs.get("chat_template_kwargs"),
    )
    if (
        "response_format" not in params
        and kwargs.get("response_mime_type") == "application/json"
    ):
        params["response_format"] = {"type": "json_object"}

    messages = _convert_to_openai_messages(contents, system_instruction)
    model_name = _resolve_model(model)
    long_context_model = _resolve_long_context_model()
    configured_output_limit = int(
        getattr(config, "GENERAL_COMPUTE_MAX_OUTPUT_TOKENS", 8192)
    )
    requested_output_limit = int(params.get("max_tokens", configured_output_limit))
    params["max_tokens"] = min(
        max(1, requested_output_limit), _MODEL_OUTPUT_LIMITS.get(model_name, llm_config.get_max_output_tokens(model_name))
    )

    # MiniMax M2.x always reasons. Keep that reasoning out of response.text so
    # JSON/Markdown consumers receive only the final answer while diagnostics
    # can inspect response.reasoning without logging it.
    if model_name == "minimax-m2.7":
        params.setdefault("reasoning_split", True)
    total_chars = len(str(contents)) + len(_normalise_instruction(system_instruction) or "")
    if total_chars > int(getattr(config, "GENERAL_COMPUTE_CONTEXT_GUARD_CHARS", 320_000)):
        model_name = long_context_model
        params["max_tokens"] = min(
            params["max_tokens"], _MODEL_OUTPUT_LIMITS.get(model_name, llm_config.get_max_output_tokens(model_name))
        )

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        **params,
    }
    # Per-key TPM pacing. Reserve an estimate of what this request will burn
    # (prompt chars /4 + max output tokens) so the key never breaches its
    # rolling one-minute budget and we avoid 429 storms.
    max_tpm = int(
        getattr(config, "GENERAL_COMPUTE_MAX_TPM_PER_KEY", 320_000)
    )
    prompt_chars = sum(
        len(str(m.get("content") or "")) for m in messages
    )
    reserve_tokens = int(prompt_chars / 4) + int(params.get("max_tokens", 8192))
    max_transient_attempts = _bounded_attempts(retries)
    transient_attempts = 0
    last_kind = "unknown error"
    context_switched = model_name == long_context_model
    # Auth and one context-model switch are separate from transport retries,
    # but this hard request budget keeps unexpected control flow bounded.
    request_budget = max_transient_attempts + len(openai_rotating_client) + 2

    for _request_number in range(request_budget):
        if transient_attempts >= max_transient_attempts:
            break
        _raise_if_provider_circuit_open()

        response = None
        key_index = -1
        delay = _retry_delay_seconds(None, transient_attempts)
        try:
            key_index, api_key = openai_rotating_client.acquire_key()
            _raise_if_provider_circuit_open()
            cooldown = openai_rotating_client.cooldown_remaining(key_index)
            if cooldown > 0:
                time.sleep(cooldown)
            # TPM pace: hold the request until this key's rolling token
            # window can absorb it. Prevents 429 storms under concurrency.
            openai_rotating_client.wait_for_tpm_headroom(
                key_index, max_tpm, reserve=reserve_tokens
            )
            # Group quota pace: atomically reserve one request before waiting
            # for an in-flight slot, so concurrent workers cannot oversubscribe
            # the shared 1500/300-minute budget.
            _reserve_request_slot()
            with _GENERAL_COMPUTE_GATE:
                # A different worker may have opened the circuit while this
                # worker was queued on the in-flight gate.
                _raise_if_provider_circuit_open()
                response = _get_http_session().post(
                    _get_general_compute_base_url(),
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    # Snapshot each attempt so later context-model escalation cannot
                    # mutate already-issued request records or instrumentation.
                    json=dict(payload),
                    timeout=_timeout_tuple(),
                )
            status = int(getattr(response, "status_code", 0))

            if status in {400, 401, 403, 404, 405, 413, 422}:
                if _is_context_error(response) and not context_switched:
                    context_switched = True
                    payload["model"] = long_context_model
                    payload["max_tokens"] = min(
                        payload["max_tokens"], _MODEL_OUTPUT_LIMITS.get(long_context_model, llm_config.get_max_output_tokens(long_context_model))
                    )
                    last_kind = "context limit"
                    continue
                if status in {401, 403}:
                    openai_rotating_client.disable_key(key_index)
                    last_kind = f"HTTP {status} authentication rejection"
                    continue
                raise GeneralComputeError(
                    f"General Compute request rejected with HTTP {status}.",
                    retryable=False,
                )
            if status in _RETRYABLE_STATUS_CODES or status >= 500:
                delay = _retry_delay_seconds(response, transient_attempts)
                if status == 429:
                    # General Compute rate limits are per key and transient
                    # ("Tokens reserved for in-flight requests count toward this
                    # limit and are released as those requests complete"). Cool
                    # down only the rejected credential and let the round-robin
                    # move to the next key. Treating a 429 as a pool-wide quota
                    # wipe-out would defer the whole batch for a limit that
                    # clears in seconds.
                    openai_rotating_client.mark_rate_limited(key_index, delay)
                last_kind = f"HTTP {status} service response"
            elif status >= 400:
                raise GeneralComputeError(
                    f"General Compute request failed with HTTP {status}.",
                    retryable=False,
                )
            else:
                try:
                    data = response.json()
                except (TypeError, ValueError):
                    last_kind = "invalid JSON response"
                else:
                    text = _response_text(data)
                    if text is not None and text.strip():
                        usage = data.get("usage") if isinstance(data, dict) else None
                        if isinstance(usage, dict):
                            tokens = (
                                usage.get("total_tokens")
                                or (
                                    int(usage.get("prompt_tokens") or 0)
                                    + int(usage.get("completion_tokens") or 0)
                                )
                                or (
                                    int(usage.get("input_tokens") or 0)
                                    + int(usage.get("output_tokens") or 0)
                                )
                            )
                            if tokens:
                                openai_rotating_client.record_usage(
                                    key_index, int(tokens)
                                )
                        _reset_provider_circuit()
                        return OpenAIResponseWrapper(
                            text,
                            reasoning=_response_reasoning(data),
                            usage=usage if isinstance(usage, dict) else None,
                        )
                    last_kind = "empty completion response"
        except _ProviderCircuitOpen:
            raise
        except GeneralComputeError as exc:
            if not exc.retryable:
                raise
            last_kind = type(exc).__name__
        except (requests.Timeout, requests.ConnectionError, requests.RequestException) as exc:
            # A stale keep-alive socket can make every retry fail identically.
            # Recreate this worker's Session before the next attempt.
            _reset_http_session()
            last_kind = f"transport error ({type(exc).__name__})"
        except (TypeError, ValueError):
            last_kind = "invalid response"

        transient_attempts += 1
        if transient_attempts < max_transient_attempts:
            time.sleep(delay)

    _open_provider_circuit()
    raise GeneralComputeError(
        f"General Compute request failed after {transient_attempts} attempts "
        f"({last_kind}).",
        retryable=True,
    )


class ModelsService:
    def generate_content(
        self,
        model: Optional[str] = None,
        contents: Any = None,
        config: Any = None,
        **kwargs: Any,
    ) -> OpenAIResponseWrapper:
        retries = kwargs.pop("retries", getattr(config_module(), "AI_MAX_TRANSPORT_ATTEMPTS", 5))
        return generate_content_with_retry(
            model=model,
            contents=contents,
            config_params=config,
            retries=retries,
            **kwargs,
        )


def config_module():
    """Return the imported config module without shadowing it in method signatures."""
    return globals()["config"]


class ClientWrapper:
    def __init__(self) -> None:
        self.models = ModelsService()


_client: Optional[ClientWrapper] = None
_client_lock = threading.Lock()


def get_llm_client() -> ClientWrapper:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = ClientWrapper()
    return _client


class LLMClientProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_llm_client(), name)


genai_client = LLMClientProxy()
get_genai_client = get_llm_client
model_config: dict[str, Any] = {}
if getattr(config, "SANDBOXED", False):
    model_config["system_instruction"] = (
        "You are running in a SANDBOXED environment. Execute tasks autonomously "
        "while respecting the configured security constraints."
    )


def get_ai_response(
    prompt: str,
    model: Optional[str] = None,
    raise_on_error: bool = False,
    **kwargs: Any,
) -> str:
    """Return response text while preserving the historical error contract."""
    try:
        response = generate_content_with_retry(
            model=_resolve_model(model),
            contents=prompt,
            config_params=kwargs.pop("config", model_config),
            **kwargs,
        )
        return response.text
    except Exception as exc:
        if raise_on_error:
            raise
        return f"AI Error: {exc}"


def _image_part(image_path: str) -> dict[str, Any]:
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
    return {"inline_data": {"mime_type": mime_type, "data": image_bytes}}


def analyze_image(image_path: str, context: str = "", retries: int = 5) -> str:
    """Analyze a scientific figure/image with context."""
    try:
        prompt = f"Describe this scientific figure/table/diagram in detail. Context: {context}"
        response = generate_content_with_retry(
            model=_resolve_model(getattr(config, "VISION_MODEL", None)),
            contents=[prompt, _image_part(image_path)],
            config_params={"temperature": 0, "top_p": 0.95},
            retries=retries,
        )
        return response.text
    except Exception as exc:
        return f"Vision Error: {exc}"


def is_valid_scientific_figure(image_path: str, retries: int = 5) -> str:
    """Filter out publisher logos, icons, and non-scientific images."""
    prompt = """
Classify this image into one of three categories:
- FIGURE: a scientific result figure (graph, gel, microscopy, phenotype, schematic, chart)
- UNCERTAIN: could be a figure or could be decorative/structural
- JUNK: logo, icon, banner, separator, publisher mark, header image

Reply with only one word: FIGURE, UNCERTAIN, or JUNK.
"""
    try:
        response = generate_content_with_retry(
            model=_resolve_model(getattr(config, "FILTER_MODEL", None)),
            contents=[prompt, _image_part(image_path)],
            config_params={"temperature": 0, "top_p": 0.95},
            retries=retries,
        )
        answer = response.text.strip().upper()
        if "FIGURE" in answer:
            return "FIGURE"
        if "JUNK" in answer:
            return "JUNK"
        return "UNCERTAIN"
    except Exception as exc:
        print(f"Filter Error: {exc}")
        return "UNCERTAIN"


def validate_structured_summary(summary_text: str) -> dict:
    """Lenient 5-section validator (backwards-compatible)."""
    from prompts import lenient_required_headers

    return _validate_against(summary_text, lenient_required_headers(), strict=False)


def validate_structured_summary_strict(summary_text: str, paper_type: Optional[str] = None) -> dict:
    """Strict 12-section validator with anchored regexes."""
    from prompts import headers_for, required_headers

    section_names = headers_for(paper_type) if paper_type else required_headers()
    return _validate_against(summary_text, section_names, strict=True)


_LENIENT_HEADING_TEMPLATE = (
    r"(?i)(?:^|\n)\s*(?:#{{1,6}})?\s*(?:\*\*)?\s*(?:\d+\.?\s*)?"
    r"{name}\s*(?:\*\*)?"
)


def _heading_regex(name: str, *, strict: bool) -> str:
    if strict:
        return rf"(?im)^##\s+{re.escape(name)}\s*$"
    pattern_name = re.escape(name).replace(r"\ &\ ", r"\s*(?:&|and)\s*")
    return _LENIENT_HEADING_TEMPLATE.format(name=pattern_name)


def _source_envelope_issues(summary_text: str) -> list[str]:
    """Return source-document envelope defects shared by both validators.

    Required headings alone are insufficient: conversational preambles, fenced
    documents, unclosed YAML, and wrong/missing source metadata must never be
    accepted for ``wiki/sources``.
    """
    if not isinstance(summary_text, str):
        return ["YAML frontmatter"]
    match = re.match(
        r"\A---\r?\n(?P<body>.*?)\r?\n---(?=\r?\n|\Z)",
        summary_text,
        re.DOTALL,
    )
    if match is None:
        return ["YAML frontmatter"]

    frontmatter = match.group("body")
    issues: list[str] = []
    type_match = re.search(r"(?im)^type:\s*(.+?)\s*$", frontmatter)
    if type_match is None or type_match.group(1).strip().strip("\"'").lower() != "source":
        issues.append("frontmatter.type")
    if re.search(r"(?im)^date_created:\s*\S+", frontmatter) is None:
        issues.append("frontmatter.date_created")
    return issues


#: Sections whose prompt rule states a hard wikilink minimum (prompts.py:
#: "MINIMUM: 3 wikilinked concepts" / "MINIMUM: 5 wikilinked entities total").
#: Nothing used to verify these, so a section could render with zero links and
#: still pass -- which orphaned it from the entity/concept graph.
_WIKILINK_MINIMUMS = {"Key Concepts & Theory": 3, "Important Entities": 5}
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:[#|][^\]]*)?\]\]")


def _section_wikilink_counts(summary_text: str, section_names: list[str]) -> dict[str, int]:
    """Count wikilinks inside each requested H2 section body."""
    counts: dict[str, int] = {}
    for name in section_names:
        match = re.search(rf"(?im)^##\s+{re.escape(name)}\s*$", summary_text)
        if match is None:
            continue
        rest = summary_text[match.end():]
        nxt = re.search(r"(?m)^##\s+", rest)
        body = rest[:nxt.start()] if nxt else rest
        counts[name] = len(_WIKILINK_RE.findall(body))
    return counts


def _validate_against(summary_text: str, section_names: list[str], *, strict: bool) -> dict:
    missing_sections = _source_envelope_issues(summary_text)
    for name in section_names:
        if re.search(_heading_regex(name, strict=strict), summary_text) is None:
            missing_sections.append(name)

    # A present-but-unlinked section is nearly as broken as a missing one: the
    # prompt mandates wikilinks and the wiki graph is built from them. This is
    # surfaced as a warning rather than a hard failure because a hard failure
    # would retry-loop on papers that genuinely mention few entities. The
    # structural guarantee lives in renderer._linkify_entity_bullets, which
    # makes zero-link entity sections impossible for the two-stage path.
    wikilink_warnings: list[str] = []
    if strict:
        counts = _section_wikilink_counts(summary_text, section_names)
        for name, minimum in _WIKILINK_MINIMUMS.items():
            if name not in counts or name in missing_sections:
                continue
            found = counts[name]
            if found == 0:
                wikilink_warnings.append(f"{name}: 0 wikilinks (prompt requires them)")
            elif found < minimum:
                wikilink_warnings.append(
                    f"{name}: {found} wikilinks, prompt states a minimum of {minimum}"
                )

    result = {"valid": not missing_sections, "missing_sections": missing_sections}
    if wikilink_warnings:
        result["wikilink_warnings"] = wikilink_warnings
    return result


def _local_fallback_embedding(texts: list[str]) -> list:
    """Deterministic compatibility embeddings for the otherwise-unused API."""
    fallback_embeddings = []
    for text in texts:
        hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
        vector = [(byte / 127.5) - 1.0 for byte in hash_bytes]
        fallback_embeddings.append((vector * 48)[:768])
    return fallback_embeddings


def get_embeddings(texts: list[str]) -> list:
    """Return local compatibility embeddings; use local_embeddings for search."""
    return _local_fallback_embedding([text[:8000] for text in texts])


def query_with_image(text_query: str, image_path: Optional[str] = None) -> str:
    """Query General Compute with optional image content."""
    try:
        contents: Any = [text_query, _image_part(image_path)] if image_path else text_query
        model = getattr(config, "VISION_MODEL" if image_path else "AI_MODEL", None)
        response = generate_content_with_retry(
            model=_resolve_model(model),
            contents=contents,
            config_params={"temperature": 0, "top_p": 0.95},
        )
        return response.text
    except Exception as exc:
        return f"Query Error: {exc}"
