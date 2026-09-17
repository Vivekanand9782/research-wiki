#!/usr/bin/env python3
"""Measure General Compute reliability and rate limiting across configured models.

This is an explicit live diagnostic; normal automated tests do not invoke it.
Examples:
  python3 scripts/test_genai_quota.py
  python3 scripts/test_genai_quota.py --models gpt-oss-120b minimax-m2.7
  python3 scripts/test_genai_quota.py --serial 12 --parallel-workers 4 --parallel-requests 24
"""

from __future__ import annotations

import argparse
import concurrent.futures
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import config  # noqa: E402
from genai_client import generate_content_with_retry  # noqa: E402


@dataclass
class CallResult:
    ok: bool
    status: str  # ok | rate_limited | error
    elapsed_s: float
    error: str = ""


def is_rate_limited(exc: Exception) -> bool:
    message = str(exc).lower()
    return "429" in message or "rate limit" in message or "resource exhausted" in message


def one_call(model: str, prompt: str) -> CallResult:
    started = time.monotonic()
    try:
        response = generate_content_with_retry(
            model=model,
            contents=prompt,
            config_params={"max_output_tokens": 40, "temperature": 0},
            retries=1,
        )
        _ = response.text.strip()
        return CallResult(ok=True, status="ok", elapsed_s=time.monotonic() - started)
    except Exception as exc:
        status = "rate_limited" if is_rate_limited(exc) else "error"
        return CallResult(
            ok=False,
            status=status,
            elapsed_s=time.monotonic() - started,
            # genai_client errors are sanitized and contain no keys/provider body.
            error=str(exc)[:500],
        )


def run_serial(model: str, prompt: str, count: int) -> list[CallResult]:
    return [one_call(model, prompt) for _ in range(count)]


def run_parallel(
    model: str,
    prompt: str,
    workers: int,
    request_count: int,
) -> list[CallResult]:
    output: list[CallResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one_call, model, prompt) for _ in range(request_count)]
        for future in concurrent.futures.as_completed(futures):
            output.append(future.result())
    return output


def summarize(results: list[CallResult]) -> dict:
    ok_times = sorted(result.elapsed_s for result in results if result.ok)

    def percentile(values: list[float], fraction: float) -> float:
        if not values:
            return 0.0
        index = max(0, min(len(values) - 1, round((len(values) - 1) * fraction)))
        return values[index]

    return {
        "total": len(results),
        "ok": sum(result.status == "ok" for result in results),
        "rate_limited": sum(result.status == "rate_limited" for result in results),
        "error": sum(result.status == "error" for result in results),
        "ok_p50": percentile(ok_times, 0.50),
        "ok_p95": percentile(ok_times, 0.95),
    }


def print_block(title: str, stats: dict) -> None:
    print(f"  {title}")
    print(
        "    total={total} ok={ok} 429={rate_limited} error={error} "
        "ok_p50={ok_p50:.2f}s ok_p95={ok_p95:.2f}s".format(**stats)
    )


def recommendation(serial_stats: dict, parallel_stats: dict) -> str:
    if serial_stats["rate_limited"] == 0 and parallel_stats["rate_limited"] > 0:
        return "Likely concurrency/RPM pressure. Lower workers or increase backoff."
    if serial_stats["rate_limited"] > 0:
        return "The configured General Compute key pool is rate-limited in serial mode."
    if serial_stats["error"] or parallel_stats["error"]:
        return "Non-429 transport/service errors occurred. Inspect the sanitized sample."
    return "No immediate rate-limit pressure observed in this test window."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    defaults = list(
        dict.fromkeys(
            [
                getattr(config, "GENERAL_COMPUTE_MODEL", "minimax-m2.7"),
                getattr(config, "GENERAL_COMPUTE_LONG_CONTEXT_MODEL", "minimax-m2.7"),
            ]
        )
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=("gpt-oss-120b", "minimax-m2.7"),
        default=defaults,
        help="General Compute models to test",
    )
    parser.add_argument("--serial", type=int, default=8, help="Serial requests per model")
    parser.add_argument("--parallel-workers", type=int, default=3, help="Parallel workers")
    parser.add_argument("--parallel-requests", type=int, default=12, help="Parallel requests per model")
    parser.add_argument("--timeout", type=float, default=60, help="Read timeout seconds")
    parser.add_argument("--prompt", default="Reply with exactly: OK")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config.GENERAL_COMPUTE_READ_TIMEOUT_SECONDS = max(1.0, args.timeout)

    print("=" * 72)
    print("General Compute Model/Rate-Limit Diagnostic")
    print("=" * 72)
    print(f"models={', '.join(args.models)}")
    print(
        "serial_calls/model={s}, parallel_workers={w}, parallel_requests/model={p}".format(
            s=args.serial,
            w=args.parallel_workers,
            p=args.parallel_requests,
        )
    )

    for model in args.models:
        print(f"\nModel: {model}")
        serial_results = run_serial(model, args.prompt, args.serial)
        parallel_results = run_parallel(
            model,
            args.prompt,
            args.parallel_workers,
            args.parallel_requests,
        )
        serial_stats = summarize(serial_results)
        parallel_stats = summarize(parallel_results)
        print_block("Serial", serial_stats)
        print_block("Parallel", parallel_stats)
        print(f"  Assessment: {recommendation(serial_stats, parallel_stats)}")
        errors = [
            result.error
            for result in serial_results + parallel_results
            if result.error
        ]
        if errors:
            print(f"  Sample error: {errors[0]}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
