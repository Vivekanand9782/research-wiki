"""
Datalab PDF-to-Markdown converter with key rotation and parallelism.

Each API key: 25 req/min, 25 concurrent. Keys rotate on 429.
Uses requests + ThreadPoolExecutor — matches existing codebase patterns.
"""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

DATALAB_BASE = "https://www.datalab.to/api/v1"
DATALAB_CONVERT = f"{DATALAB_BASE}/convert"
MAX_PER_KEY = 25  # concurrent + req/min per key
POLL_INTERVAL = 1.0
MAX_POLLS = 300


def _load_keys() -> list[str]:
    raw = os.getenv("DATALAB_API_KEYS", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise RuntimeError("DATALAB_API_KEYS not set in .env")
    return keys


class KeyRotator:
    """Round-robin key pool with per-key rate limiting and 429 exhaustion."""

    def __init__(self):
        self._keys = _load_keys()
        self._lock = threading.Lock()
        self._idx = 0
        # Per-key: list of request timestamps (rolling 60s window)
        self._windows: dict[str, list[float]] = {k: [] for k in self._keys}
        self._depleted: set[str] = set()  # rate-limited (recoverable, 429)
        self._exhausted: set[str] = set()  # permanently dead keys (403 / invalid)

    @property
    def total_capacity(self) -> int:
        return len(self._keys) * MAX_PER_KEY

    def has_live_keys(self) -> bool:
        with self._lock:
            return any(k not in self._exhausted for k in self._keys)

    def acquire(self) -> str | None:
        """Return next available key, or None if all are rate-limited."""
        with self._lock:
            for _ in range(len(self._keys)):
                key = self._keys[self._idx]
                self._idx = (self._idx + 1) % len(self._keys)
                if key in self._depleted or key in self._exhausted:
                    continue
                now = time.monotonic()
                cutoff = now - 60.0
                win = [t for t in self._windows[key] if t > cutoff]
                if len(win) >= MAX_PER_KEY:
                    self._depleted.add(key)
                    continue
                win.append(now)
                self._windows[key] = win
                return key
            # All keys depleted — reset for next round
            self._depleted.clear()
            return None

    def mark_rate_limited(self, key: str):
        with self._lock:
            self._depleted.add(key)

    def mark_exhausted(self, key: str):
        with self._lock:
            self._exhausted.add(key)
            self._depleted.discard(key)

    def reset_if_all_depleted(self):
        with self._lock:
            live = [k for k in self._keys if k not in self._exhausted]
            if live and len(self._depleted) >= len(live):
                self._depleted.clear()


# Module-level singleton
_rotator: KeyRotator | None = None
_rotator_lock = threading.Lock()


def _get_rotator() -> KeyRotator:
    global _rotator
    if _rotator is None:
        with _rotator_lock:
            if _rotator is None:
                _rotator = KeyRotator()
    return _rotator


def _poll_result(request_id: str, api_key: str) -> dict:
    """Poll GET /convert/{request_id} until status == 'complete'."""
    url = f"{DATALAB_CONVERT}/{request_id}"
    for _ in range(MAX_POLLS):
        try:
            resp = requests.get(url, headers={"X-API-Key": api_key}, timeout=15)
            data = resp.json()
        except Exception:
            time.sleep(POLL_INTERVAL)
            continue

        status = data.get("status", "")
        if status == "complete":
            return data
        if data.get("error"):
            raise RuntimeError(f"Datalab error: {data['error']}")
        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Poll timed out for request {request_id}")


def convert_one(pdf_path: Path, text_path: Path | None = None,
                mode: str = "fast", max_retries: int = 3) -> str:
    """Convert a single PDF to markdown via Datalab.

    Returns the markdown text. Writes to text_path if provided.

    Key selection and transient-failure retries are decoupled: a dead key
    (HTTP 403) is dropped and the next live key is tried without consuming a
    retry. ``max_retries`` bounds only transient failures (429, poll timeout,
    empty markdown) on a key that actually accepted the request.
    """
    rotator = _get_rotator()
    # Bound the number of distinct live keys we'll try so a fully-dead key
    # pool fails fast instead of spinning forever.
    key_budget = len(rotator._keys)

    while key_budget > 0:
        # Acquire a working key, skipping dead (403-exhausted) keys. If every
        # key is momentarily rate-limited, wait and retry. If all keys are
        # permanently exhausted, fail fast.
        key = None
        while True:
            candidate = rotator.acquire()
            if candidate is not None:
                key = candidate
                break
            if not rotator.has_live_keys():
                raise RuntimeError("All Datalab API keys are exhausted (HTTP 403). "
                                   "Add a card or supply fresh keys in DATALAB_API_KEYS.")
            time.sleep(5)
            rotator.reset_if_all_depleted()

        try:
            with open(pdf_path, "rb") as f:
                resp = requests.post(
                    DATALAB_CONVERT,
                    headers={"X-API-Key": key},
                    files={"file": (pdf_path.name, f, "application/pdf")},
                    data={
                        "mode": mode,
                        "output_format": "markdown",
                        "disable_image_extraction": "true",
                        "disable_image_captions": "true",
                        "token_efficient_markdown": "true",
                    },
                    timeout=30,
                )

            if resp.status_code == 429:
                rotator.mark_rate_limited(key)
                continue

            if resp.status_code == 403:
                # Exhausted free allowance / invalid key — permanently drop it
                # and grab the next live key (does NOT consume a retry).
                rotator.mark_exhausted(key)
                key_budget -= 1
                continue

            submit = resp.json()

            if not submit.get("success"):
                err = submit.get("error", f"HTTP {resp.status_code}")
                raise RuntimeError(f"Datalab submit failed: {err}")

            request_id = submit.get("request_id")
            request_check_url = submit.get("request_check_url")
            if not request_id:
                raise RuntimeError("No request_id in Datalab response")

            result = _poll_result(request_id, key)

            if not result.get("success"):
                err = result.get("error", "unknown")
                raise RuntimeError(f"Datalab conversion failed: {err}")

            md = result.get("markdown") or ""
            if not md.strip():
                raise RuntimeError(f"Datalab returned empty markdown for {pdf_path.name}")

            if text_path is not None:
                text_path.parent.mkdir(parents=True, exist_ok=True)
                text_path.write_text(md, encoding="utf-8")

            return md

        except (requests.RequestException, RuntimeError) as e:
            key_budget -= 1
            if key_budget <= 0:
                raise
            time.sleep(min(2 ** (max_retries - key_budget), 10))

    raise RuntimeError(f"Failed to convert {pdf_path.name}")


def convert_batch(pdf_paths: list[tuple[Path, Path]],
                  mode: str = "fast",
                  max_workers: int | None = None) -> list[tuple[Path, Path, str, Exception | None]]:
    """Convert multiple PDFs in parallel.

    Args:
        pdf_paths: List of (pdf_path, text_path)
        mode: "fast"
        max_workers: Defaults to total key capacity (7 keys * 25 = 175)

    Returns:
        List of (pdf_path, text_path, markdown_or_empty, error_or_none)
    """
    if max_workers is None:
        max_workers = 12

    results: list[tuple[Path, Path, str, Exception | None]] = []

    def _worker(pdf_path: Path, text_path: Path):
        try:
            md = convert_one(pdf_path, text_path, mode=mode, max_retries=2)
            return (pdf_path, text_path, md, None)
        except Exception as e:
            return (pdf_path, text_path, "", e)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_worker, p, tp): (p, tp) for p, tp in pdf_paths}
        for f in as_completed(futures):
            results.append(f.result())

    return results
