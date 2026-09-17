"""Standalone smoke test: does rotating NVIDIA NIM keys beat the per-key 40 RPM cap?

Each key gets its own fixed token bucket (--rpm-per-key, default 40). Every
request is routed to whichever key currently has capacity, so the achievable
aggregate throughput is ~ (#keys * rpm-per-key). The headline number is the
achieved aggregate RPM: run with all keys vs `--use-keys 1` to see the
single-key 40 RPM ceiling for contrast.

Keys come from the NIM_API_KEYS env var (comma/space/newline separated) so they
never touch disk and are only printed masked. Model from --model or NIM_MODEL.
Uses only the stdlib (NIM is OpenAI-compatible), so no extra install needed.

    export NIM_API_KEYS="k1,k2,k3,k4"
    python3 scripts/nim_key_rotation_smoketest.py --model zai-org/glm-4.6 --requests 80
    python3 scripts/nim_key_rotation_smoketest.py --model zai-org/glm-4.6 --use-keys 1   # contrast
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

BASE = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")


class Bucket:
    """Fixed-rate token bucket, ~rpm requests/min, burst of 1 (no adaptation)."""

    def __init__(self, rpm: float):
        self.rate = rpm / 60.0
        self.tokens = 1.0
        self.t = time.monotonic()
        self.lock = threading.Lock()

    def try_acquire(self) -> bool:
        with self.lock:
            now = time.monotonic()
            self.tokens = min(1.0, self.tokens + (now - self.t) * self.rate)
            self.t = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False


def call(client: OpenAI, model: str, prompt: str, timeout: float) -> str:
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=16,
            temperature=0,
            stream=True,
            timeout=timeout,
        )
        for _ in stream:
            pass
        return "ok"
    except Exception as e:
        return "429" if "429" in str(e) or "rate limit" in str(e).lower() else "other"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=os.environ.get("NIM_MODEL", "z-ai/glm-5.1"))
    ap.add_argument("--requests", type=int, default=80)
    ap.add_argument("--rpm-per-key", type=int, default=40)
    ap.add_argument("--use-keys", type=int, default=0, help="limit #keys (0 = all)")
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--prompt", default="Reply with the single word: ok")
    args = ap.parse_args()

    keys = [k.strip() for k in os.environ.get("NIM_API_KEYS", "").replace(",", " ").split() if k.strip()]
    if args.use_keys:
        keys = keys[:args.use_keys]
    if not keys:
        sys.exit("No keys found. Set NIM_API_KEYS='k1,k2,k3,k4'")
    if not args.model:
        sys.exit("No model. Pass --model or set NIM_MODEL (e.g. zai-org/glm-4.6)")

    buckets = [Bucket(args.rpm_per_key) for _ in keys]
    clients = [OpenAI(base_url=BASE, api_key=k) for k in keys]
    counts = [{"ok": 0, "429": 0, "other": 0} for _ in keys]
    lock = threading.Lock()
    rr = {"i": 0}

    def pick() -> int:
        """Spin until some key has a free token; round-robin start each time."""
        while True:
            with lock:
                for off in range(len(keys)):
                    j = (rr["i"] + off) % len(keys)
                    if buckets[j].try_acquire():
                        rr["i"] = (j + 1) % len(keys)
                        return j
            time.sleep(0.02)

    def worker(_) -> None:
        j = pick()
        res = call(clients[j], args.model, args.prompt, args.timeout)
        with lock:
            counts[j][res if res in ("ok", "429") else "other"] += 1

    print(f"keys={len(keys)} model={args.model} rpm/key={args.rpm_per_key} "
          f"requests={args.requests} → theoretical ceiling ~{len(keys) * args.rpm_per_key} RPM")
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=max(8, len(keys) * 4)) as ex:
        list(ex.map(worker, range(args.requests)))
    dt = time.monotonic() - t0

    ok = sum(c["ok"] for c in counts)
    e429 = sum(c["429"] for c in counts)
    other = sum(c["other"] for c in counts)
    print(f"done in {dt:.1f}s  ok={ok} 429={e429} other={other}")
    print(f"achieved aggregate RPM (successful) = {ok / dt * 60:.1f}")
    for k, c in zip(keys, counts):
        print(f"  key …{k[-4:]}: ok={c['ok']} 429={c['429']} other={c['other']}")
    if e429:
        print("\n429s seen → lower --rpm-per-key a few points (rolling-window slack).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
