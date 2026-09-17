"""pipeline_state.py — content-fingerprint cache for the ingest pipeline.

Inspired by Understand-Anything's incremental-update model. Each step records
a *fingerprint* derived from the input content (not the file path) plus any
relevant version markers (extractor version, prompt version). Re-running the
pipeline skips work whose fingerprint matches the last successful run.

Why content-hash instead of path:
  * a re-OCR'd PDF at the same path *should* invalidate the entry,
  * an improved extractor or prompt *should* invalidate the entry,
  * a renamed PDF *should not*.

Storage: a single JSON file at
``wiki/.understand-anything/intermediate/pipeline_state.json``. Atomic on
write (temp file + rename). Designed for single-process use; not concurrency-safe.

Public API
==========

>>> from pipeline_state import PipelineState, fingerprint_file
>>> state = PipelineState()
>>> fp = fingerprint_file(pdf_path, "extractor:v3", "prompt:summary-v2")
>>> if state.is_done("extract", fp):
...     pass  # skip
>>> else:
...     result = run_extract(pdf_path)
...     state.mark_done("extract", fp, payload={"output": str(out)})
>>> state.save()
"""
from __future__ import annotations

import datetime
import functools
import hashlib
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

DEFAULT_STATE_PATH = (
    Path(__file__).resolve().parent / "wiki" / ".understand-anything"
    / "intermediate" / "pipeline_state.json"
)


def fingerprint_bytes(*chunks: bytes | str) -> str:
    """Return ``sha256`` hex digest over the concatenation of ``chunks``.

    String chunks are encoded as UTF-8. Useful for deriving fingerprints from
    file content + version tokens::

        fp = fingerprint_bytes(pdf_path.read_bytes(), "extractor:v3")
    """
    h = hashlib.sha256()
    for c in chunks:
        if isinstance(c, str):
            c = c.encode("utf-8")
        h.update(c)
    return h.hexdigest()


@functools.lru_cache(maxsize=256)
def _cached_file_hasher(
    resolved_path: str, size: int, mtime_ns: int, ctime_ns: int, chunk_size: int
):
    """Return a reusable SHA-256 state for unchanged file content."""
    del size, mtime_ns, ctime_ns  # values intentionally participate in cache key
    h = hashlib.sha256()
    with open(resolved_path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h


def fingerprint_file(path: str | os.PathLike, *version_tokens: str,
                      chunk_size: int = 1024 * 1024) -> str:
    """Hash file content plus version tokens, reusing unchanged file reads.

    The resulting digest is byte-for-byte compatible with the previous
    implementation; only the base SHA-256 state is cached. This avoids reading
    every PDF again for the raw-prepass and ingest fingerprints.
    """
    resolved = Path(path).expanduser().resolve()
    stat = resolved.stat()
    h = _cached_file_hasher(
        str(resolved), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, chunk_size
    ).copy()
    for tok in version_tokens:
        h.update(b"\x00")
        h.update(tok.encode("utf-8"))
    return h.hexdigest()


class PipelineState:
    """In-memory + on-disk record of completed pipeline steps.

    ``state[step_name][fingerprint] = {"timestamp": "...", "payload": {...}}``
    """

    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path) if path is not None else DEFAULT_STATE_PATH
        self._lock = threading.RLock()
        self._data: dict[str, dict[str, dict]] = self._load()

    # ─── disk I/O ──────────────────────────────────────────────────────────
    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8")) or {}
        except (json.JSONDecodeError, OSError):
            # Corrupt / unreadable — start fresh while preserving every bad
            # snapshot for diagnosis instead of overwriting one fixed backup.
            stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y%m%dT%H%M%S_%fZ"
            )
            backup = self.path.with_name(
                f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}"
            )
            try:
                self.path.replace(backup)
            except OSError:
                pass
            return {}

    def save(self) -> None:
        """Persist atomically from a lock-protected in-memory snapshot."""
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=str(self.path.parent),
                    prefix=".pipeline_state.", suffix=".tmp", delete=False
                ) as tmp:
                    json.dump(self._data, tmp, indent=2, sort_keys=True)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                    tmp_path = Path(tmp.name)
                os.replace(tmp_path, self.path)
                tmp_path = None
            finally:
                if tmp_path is not None:
                    tmp_path.unlink(missing_ok=True)

    # ─── core API ──────────────────────────────────────────────────────────
    def is_done(self, step: str, fp: str) -> bool:
        with self._lock:
            return fp in self._data.get(step, {})

    def mark_done(self, step: str, fp: str, payload: Any = None) -> None:
        with self._lock:
            bucket = self._data.setdefault(step, {})
            bucket[fp] = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                "payload": payload,
            }

    def get(self, step: str, fp: str) -> dict | None:
        with self._lock:
            return self._data.get(step, {}).get(fp)

    def clear(self, step: str | None = None, fp: str | None = None) -> int:
        """Remove entries. Returns number of entries removed.

        - ``clear()`` wipes everything.
        - ``clear(step="X")`` wipes step X.
        - ``clear(step="X", fp="...")`` wipes one entry.
        """
        with self._lock:
            if step is None:
                n = sum(len(v) for v in self._data.values())
                self._data.clear()
                return n
            bucket = self._data.get(step, {})
            if fp is None:
                n = len(bucket)
                self._data.pop(step, None)
                return n
            if fp in bucket:
                del bucket[fp]
                return 1
            return 0

    def steps(self) -> list[str]:
        with self._lock:
            return sorted(self._data.keys())

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                step: len(entries)
                for step, entries in sorted(self._data.items())
            }

    # ─── context manager ──────────────────────────────────────────────────
    def __enter__(self) -> "PipelineState":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # Persist on clean exit; on exception, leave state alone so the caller
        # can decide whether to retry.
        if exc_type is None:
            self.save()


# ─────────────────────────────────────────────────────────────────────────────
# Tiny CLI for ad-hoc inspection / cache busting
# ─────────────────────────────────────────────────────────────────────────────
def _cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Inspect or clear the pipeline state cache")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("show", help="Print step → entry counts")
    sub.add_parser("path", help="Print where the state file lives")

    p_clear = sub.add_parser("clear", help="Remove cache entries")
    p_clear.add_argument("--step", help="Only clear this step (default: clear everything)")
    p_clear.add_argument("--yes", action="store_true", help="Skip confirmation")

    args = parser.parse_args()
    state = PipelineState()

    if args.cmd in (None, "show"):
        s = state.stats()
        if not s:
            print("(empty cache)")
        else:
            print(f"State file: {state.path}")
            for step, n in s.items():
                print(f"  {step:30s} {n} entries")
        return 0

    if args.cmd == "path":
        print(state.path)
        return 0

    if args.cmd == "clear":
        if not args.yes:
            scope = args.step or "ALL STEPS"
            print(f"This will clear {scope}. Re-run with --yes to confirm.")
            return 1
        n = state.clear(step=args.step)
        state.save()
        print(f"Cleared {n} entries from {args.step or 'all steps'}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
