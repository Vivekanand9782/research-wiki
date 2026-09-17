#!/usr/bin/env python3
"""
summarize_pipeline.py — high-throughput hcnsec API summarization.

Replaces subagent-driven sidecar generation with direct OpenAI-compatible
API calls to the workspace chat-completions backend (default https://api.generalcompute.com/v1), using
sensenova-6.7-flash-lite with round-robin rotation across multiple API
keys.  `thinking: disabled` is set so the model's budget goes to the JSON
output, not to a chain-of-thought blob.

Usage:
    # 1) Set keys in env (comma-separated):
    export HCNSEC_KEYS="sk-1,sk-2,sk-3,sk-4"

    # 2) Run a dry-run wave on 3 papers:
    python3 summarize_pipeline.py --limit 3 --dry-run

    # 3) Run for real:
    python3 summarize_pipeline.py --limit 50 [--topic uncategorized] [--concurrency 4]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import traceback
from datetime import date
from pathlib import Path
from typing import Any

import httpx

RW = Path(__file__).resolve().parent  # research-wiki/
WORKSPACE_ROOT = RW.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

try:
    import llm_config
except ImportError:
    llm_config = None

WORKLIST_PATH = RW / "agent_worklist.json"
RAW_PAPERS = RW / "raw" / "papers"
SPEC_PATH = RW / "agent_summary_spec.md"
STATE_PATH = RW / "agent_deep_summary_state.json"

MIN_RAW_WORDS = 500  # include thin papers; render gates scale adaptively
MAX_ATTEMPTS_PER_PAPER = 3
DEFAULT_CONCURRENCY = 4


def quality_targets(paper_text: str) -> tuple[int, int]:
    """(min_total_words, min_footnotes) adaptive to source length. Mirrors
    ingest_agent._depth_targets so what we generate passes the render gate."""
    raw_words = len(paper_text.split())
    if raw_words <= 0:
        return 2800, 8
    min_words = min(2800, max(min(1200, raw_words), raw_words // 2))
    min_fns = min(8, max(3, raw_words // 400))
    return min_words, min_fns


def footnote_count(obj: dict) -> int:
    n = 0
    for sec in obj.get("sections", {}).values():
        if isinstance(sec, dict):
            r = sec.get("results")
            if isinstance(r, list):
                n += len(r)
    return n


def section_word_count(obj: dict) -> int:
    n = 0
    for sec in obj.get("sections", {}).values():
        if isinstance(sec, dict):
            t = sec.get("text")
            if isinstance(t, str):
                n += len(t.split())
        elif isinstance(sec, str):
            n += len(sec.split())
    return n

# ------------------------------------------------------------------
# Prompt: compact but covers every rule the validator cares about
# ------------------------------------------------------------------
# Prompt: minimal system + full spec in user, so the model's budget
# goes to the JSON output, not to a chain-of-thought reasoning blob.
# ------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a research-paper summarizer. Reply with ONLY a single "
    "well-formed JSON object. No markdown fences, no prose, no "
    "chain-of-thought, no preamble, no postamble. Emit the JSON and "
    "nothing else."
)

from prompts import REQUIRED_SECTIONS


def _build_sections_spec() -> str:
    lines = []
    for i, s in enumerate(REQUIRED_SECTIONS, 1):
        words = f" ~{s.max_words} words." if s.max_words else ""
        rule = f" — {s.rule}" if s.rule else ""
        lines.append(f'   {i:2d}. "{s.name}"{rule}{words}')
    return "\n".join(lines)


USER_PROMPT_TEMPLATE = f"""Produce a JSON sidecar for ONE paper.

=== NON-NEGOTIABLE REQUIREMENT — read this first (the #1 rejection reason) ===
Your JSON MUST contain evidence footnotes. A footnote is an object inside a
"results" array on a section. Outputs without them are REJECTED by the gate:
- "Key Results & Data" MUST have a "results" array with 5-6 footnotes.
- "Mechanistic Insights" MUST have a "results" array with 2-3 footnotes.
- "Methods & Experimental Design" SHOULD have a "results" array with 1-2 footnotes.
Footnote object shape:
    {{"claim": "your 1-line paraphrase of one factual claim",
     "evidence_quote": "EXACT contiguous substring copied character-for-character from the paper text",
     "source_locator": "Results section, Figure 3B"}}
HOW TO PICK QUOTES:
- Scan the paper text for factual/numerical claims (numbers, %, units, p-values).
- Copy the sentence VERBATIM (including italics underscores, ×, ±, etc.).
- Do NOT edit, truncate, or reformat the quote. Never paraphrase inside
  "evidence_quote" — if unsure, pick a different sentence.
- TARGET: 8-15 footnotes TOTAL across the paper.

=== JSON SHAPE ===
Return ONLY a single JSON object with these top-level keys:

1) "frontmatter" — object with exactly:
    - "tags": array of 4-6 lowercase kebab-case strings
    - "type": "source"
    - "date_created": "__TODAY__"
    - "date_updated": "__TODAY__"
    - "source_count": 1
    - "doi": string (as it appears in the raw text, exact) or null
    - "authors": "LastName1 et al." (first author surname + "et al.") or null
    - "year": integer (4-digit) or null
    - "journal": full journal name or null

2) "paper_type": ONE of: "primary_research", "review", "methods_paper",
   "perspective", "correction_notice", "conference_proceedings", "other"

3) "sections" — object. Each value is {{"text": "<markdown>", "results": [...]}}.
   EVERY substantive section gets a "results" array (see the requirement above).
   Use this section set
   (swap "Methods & Experimental Design" for "Reviewed Literature & Inclusion Criteria" if paper_type is review):
{_build_sections_spec()}

4) "entities" — array of objects. Include every gene/protein/organism mentioned. Shape:
    {{
      "text": "GeneSymbol",
      "molecular_role": "<one of: sequence_specific_transcription_factor, transcriptional_coregulator, chromatin_regulator, signaling_regulator, enzyme, receptor_or_kinase, noncoding_rna, locus_or_uncharacterized_protein>",
      "evidence_directness": "<one of: direct, indirect, review_summary, unclear>",
      "role_evidence_quote": "<verbatim contiguous substring from the paper text>",
      "source_section": "Introduction & Background"
    }}
    Overrides: MFT/TaMFT/TaPHS1 -> signaling_regulator; DELLA/GAI/RGA/RGL1-3 -> transcriptional_coregulator.
    Include 5-20 entities.

Wikilink style: [[CRISPR-Cas9]], [[Root Nodule Symbiosis]], [[Triticum aestivum]].

Null policy: if the paper text lacks DOI/author/year/journal, set that field to JSON null. Do not guess.

Safety: every claim must come from the paper text; every quote must be verbatim. Do NOT use # or ## inside section text.

=== PAPER TEXT (verbatim) ===
"""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def extract_json(text: str) -> dict | None:
    """Best-effort JSON parse from LLM output. Model often wraps JSON in
    thinking tags, markdown fences, or trailing prose.
    Strategy: try full text, then strip fences/thinking, then try
    incremental suffix repair, then scan for balanced braces.
    """
    if not text:
        return None

    def _try(t: str) -> dict | None:
        try:
            obj = json.loads(t)
            if isinstance(obj, dict) and "sections" in obj and "frontmatter" in obj:
                return obj
        except Exception:
            pass
        # Suffix-repair: strip trailing chars that may be unbalanced
        for cut in range(1, min(200, len(t))):
            try:
                obj = json.loads(t[: len(t) - cut])
                if isinstance(obj, dict) and "sections" in obj:
                    return obj
            except Exception:
                continue
        return None

    t = text.strip()
    r = _try(t)
    if r:
        return r

    # Strip ```json ... ``` fences (both flavors)
    t2 = re.sub(r"```[a-zA-Z]*\s*", "", t, flags=re.I)
    t2 = re.sub(r"```\s*$", "", t2, flags=re.I)
    for tag in ("</thinking>", "</thought>", "<|end_of_thinking|>"):
        t2 = t2.split(tag)[-1]
    t2 = t2.strip()
    r = _try(t2)
    if r:
        return r

    # Find outermost balanced brace pair respecting strings/escapes
    start = None
    depth = 0
    in_str = False
    esc = False
    span_end = None
    for i, ch in enumerate(t2):
        if esc:
            esc = False
            continue
        if ch == "\\" and in_str:
            esc = True
            continue
        if ch == '"' and not esc:
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                span_end = i
                candidate = t2[start : i + 1]
                r = _try(candidate)
                if r:
                    return r
                start = None
                span_end = None

    # Last resort: any { ... } with json.loads
    for m in re.finditer(r"\{[\s\S]{200,}\}", t2):
        r = _try(m.group())
        if r:
            return r

    return None


def read_raw_words(raw_path: Path) -> int:
    try:
        txt = raw_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    return len(txt.split())


def pick_topic_order() -> list[str]:
    # Prioritize by topic tier so high-value topics finish first
    return [
        "genome_editing_transgene_free",
        "PHS_tolerance",
        "bioethanol",
        "uncategorized",
        "vpc_transgene_free",
        "downloads",
        "tmp",
    ]


def build_queue(wl: list[dict], topics: list[str] | None = None) -> list[dict]:
    pending = [
        x for x in wl
        if x.get("status") == "pending"
        and x.get("raw_path")
        and Path(x.get("raw_path")).exists()
        and read_raw_words(Path(x["raw_path"])) >= MIN_RAW_WORDS
    ]
    if topics:
        topic_set = set(topics)
        pending = [x for x in pending if x.get("topic") in topic_set]
    # Sort by topic tier then by raw_words ascending (thin first -> cheap + quick)
    def key(x):
        ti = (pick_topic_order().index(x.get("topic",""))
              if x.get("topic") in pick_topic_order() else 999)
        return (ti, x.get("raw_words") or 10000)
    pending.sort(key=key)
    return pending


def summarize_call(client: httpx.Client, key: str, paper_text: str,
                   extra_messages: list[dict] | None = None) -> dict | None:
    # Put the spec in the user message and the strict-output directive in system.
    # This leaves the largest possible budget for the actual JSON.
    system = (
        "Reply with ONLY a JSON object. No reasoning, no explanation, "
        "no chain of thought, no markdown fences, no prose. "
        "Emit the JSON and nothing else."
    )
    user = USER_PROMPT_TEMPLATE.replace("__TODAY__", date.today().isoformat()) + "\n" + paper_text
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    if extra_messages:
        messages.extend(extra_messages)
    chosen_model = os.environ.get("SUMMARIZE_PIPELINE_MODEL") or (llm_config.get_model() if llm_config else "minimax-m2.7")
    max_output = llm_config.get_max_output_tokens(chosen_model) if llm_config else 128000
    endpoint_url = llm_config.get_chat_completions_url() if llm_config else (os.environ.get("GENERAL_COMPUTE_BASE_URL", "https://api.generalcompute.com/v1").rstrip("/") + "/chat/completions")
    payload = {
        "model": chosen_model,
        "max_tokens": max_output,
        "temperature": 0,
        # NOTE: do NOT set response_format: json_object — on hcnsec sensenova
        # always dumps into the `reasoning` field (infinite chain-of-thought)
        # when that flag is set. Instead we rely on the system prompt to get
        # raw JSON in the `content` field.
        # CRITICAL: add thinking disabled to eliminate chain-of-thought budget
        "thinking": {"type": "disabled"},
        "messages": messages,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    r = client.post(
        endpoint_url,
        headers=headers,
        json=payload,
        timeout=120.0,
    )
    data = r.json()
    # hcnsec may return 200 with an error body (rpm exhausted)
    if "error" in data:
        raise RuntimeError(f"API error: {data['error']}")
    if r.status_code != 200:
        raise RuntimeError(f"API {r.status_code}: {r.text[:300]}")
    msg = data.get("choices", [{}])[0].get("message", {})
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning") or ""
    # Combine — some models put the answer inside reasoning when chain-of-thought is active
    combined = content
    if reasoning and not combined:
        combined = reasoning
    elif reasoning:
        combined = content + "\n" + reasoning
    obj = extract_json(combined)
    if obj is None:
        raise ValueError(
            f"LLM did not return parseable JSON (content_len={len(content)}, "
            f"reasoning_len={len(reasoning)})"
        )
    return obj


def corrective_call(client: httpx.Client, key: str, paper_text: str, obj: dict,
                    fn_count: int, words: int, min_fns: int, min_words: int) -> dict | None:
    """One follow-up turn handing the model its own JSON and demanding the
    missing footnotes / depth. Returns the corrected object or None."""
    fix_msg = (
        "Your JSON was REJECTED by the quality gate:\n"
        f"- evidence footnotes: {fn_count} found, need >= {min_fns}\n"
        f"- section word total: {words}, need >= {min_words}\n"
        "Revise and return the COMPLETE corrected JSON object (all keys) with:\n"
        '1. A "results" array of verbatim-quote footnotes added to '
        '"Key Results & Data" (5-6), "Mechanistic Insights" (2-3) and '
        '"Methods & Experimental Design" (1-2). Each evidence_quote must be '
        "copied character-for-character from the paper text above.\n"
        "2. Thin sections expanded with facts from the paper text to reach "
        "the word minimums.\n"
        "Reply with ONLY the corrected JSON object."
    )
    extra = [
        {"role": "assistant", "content": json.dumps(obj, ensure_ascii=False)},
        {"role": "user", "content": fix_msg},
    ]
    return summarize_call(client, key, paper_text, extra_messages=extra)


# ------------------------------------------------------------------
# Worker
# ------------------------------------------------------------------
def worker(papers: list[dict], keys: list[str], idx_offset: int, barrier: list[int]) -> list[dict]:
    """Process an ordered slice of papers. Returns list of results dicts."""
    results: list[dict] = []
    client = httpx.Client(timeout=httpx.Timeout(120.0, connect=15.0))
    # Stagger thread starts so keys are not hammered simultaneously
    time.sleep(idx_offset * 5.0)
    for i, paper in enumerate(papers):
        stem = paper["stem"]
        raw_path = Path(paper["raw_path"])
        sidecar_path = Path(paper["sidecar_path"])
        barrier[0] += 1
        ok = False
        last_err = ""
        paper_text = raw_path.read_text(encoding="utf-8", errors="ignore")
        for attempt in range(1, MAX_ATTEMPTS_PER_PAPER + 1):
            try:
                # Key rotation: distribute load across keys, with attempt offset
                key = keys[(i + idx_offset * 7 + attempt * 2) % len(keys)]
                obj = summarize_call(client, key, paper_text)
                if not isinstance(obj, dict) or "sections" not in obj or "frontmatter" not in obj:
                    raise ValueError("missing sections/frontmatter")
                # Quality gate before write: one corrective follow-up if short
                fn_count = footnote_count(obj)
                words = section_word_count(obj)
                min_words, min_fns = quality_targets(paper_text)
                if fn_count < min_fns or words < min_words:
                    try:
                        fixed = corrective_call(client, key, paper_text, obj,
                                                fn_count, words, min_fns, min_words)
                        if isinstance(fixed, dict) and "sections" in fixed and "frontmatter" in fixed:
                            obj = fixed
                            fn_count = footnote_count(obj)
                            words = section_word_count(obj)
                    except Exception:
                        pass  # keep original; mechanical repair stage will fix
                if fn_count < min_fns or words < min_words:
                    obj["repair_needed"] = True
                sidecar_path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
                results.append({"stem": stem, "status": "written", "path": str(sidecar_path)})
                ok = True
                break
            except Exception as e:
                last_err = f"attempt {attempt}: {e}"
                err = str(e)
                if "rpm exhausted" in err or "429" in err or "rate_limit" in err.lower():
                    base = 30 * attempt
                    j = random.uniform(0, 8)
                    time.sleep(base + j)
                elif "5" in err[:6]:
                    time.sleep(10 + 5 * attempt)
                else:
                    time.sleep(5)
        if not ok:
            results.append({"stem": stem, "status": "failed", "error": last_err[:300]})
    client.close()
    return results


def run_batch(args: argparse.Namespace) -> dict:
    """Main orchestrator: build queue, dispatch to threads, return summary."""
    wl = json.loads(WORKLIST_PATH.read_text())
    queue = build_queue(wl, args.topic)

    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}
    seen = set(state.get("completed", [])) | set(state.get("failed", []))
    # Filter to not-done
    queue = [p for p in queue if p["stem"] not in seen]
    if queue:
        queue = queue[: args.limit]

    if not queue:
        print("No pending papers to process.")
        return {"papers": 0, "written": 0, "failed": 0}

    if "HCNSEC_KEYS" in os.environ and os.environ["HCNSEC_KEYS"].strip():
        keys = [k.strip() for k in os.environ["HCNSEC_KEYS"].split(",") if k.strip()]
    elif llm_config and llm_config.get_api_keys():
        keys = llm_config.get_api_keys()
    else:
        raise RuntimeError("No API keys found in environment (set LLM_API_KEYS, GENERAL_COMPUTE_API_KEYS, or HCNSEC_KEYS)")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    batch_size = max(1, len(queue) // args.concurrency)
    chunks = [queue[i:i + batch_size] for i in range(0, len(queue), batch_size)]
    if not chunks:
        chunks = [queue]

    all_results: list[dict] = []
    start = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(worker, ch, keys, i * batch_size, [0]) for i, ch in enumerate(chunks)]
        for f in as_completed(futs):
            all_results.extend(f.result())

    written = sum(1 for r in all_results if r["status"] == "written")
    failed = len(all_results) - written
    elapsed = time.time() - start

    # Update state
    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {"completed": [], "failed": []}
    state["completed"] = list(set(state.get("completed", [])) |
                              {r["stem"] for r in all_results if r["status"] == "written"})
    state["failed"] = list(set(state.get("failed", [])) |
                           {r["stem"] for r in all_results if r["status"] == "failed"})
    state["last_run_at"] = date.today().isoformat()
    state["last_run_keys"] = len(keys)
    STATE_PATH.write_text(json.dumps(state, indent=2))

    print(f"\n=== BATCH SUMMARY ===")
    print(f"papers: {len(all_results)}, written: {written}, failed: {failed}")
    print(f"elapsed: {elapsed:.1f}s  ({elapsed/max(1,len(all_results)):.1f}s per paper)")
    if failed:
        print("Failed stems:")
        for r in all_results:
            if r["status"] == "failed":
                print(f"  - {r['stem']}: {r['error'][:100]}")
    return {"papers": len(all_results), "written": written, "failed": failed}


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="hcnsec API summarization pipeline")
    p.add_argument("--limit", type=int, default=50, help="max papers to summarize this run")
    p.add_argument("--topic", nargs="+", help="restrict to these topic folders")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                   help="parallel API workers")
    p.add_argument("--dry-run", action="store_true",
                   help="print queue but do not call API")
    p.add_argument("--status", action="store_true", help="print run status only")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    has_keys = bool(os.environ.get("HCNSEC_KEYS")) or bool(llm_config and llm_config.get_api_keys())
    if not has_keys:
        print("ERROR: set LLM_API_KEYS, GENERAL_COMPUTE_API_KEYS, or HCNSEC_KEYS env var with comma-separated keys.", file=sys.stderr)
        sys.exit(2)

    if args.status:
        if not STATE_PATH.exists():
            print("no prior runs")
            return
        state = json.loads(STATE_PATH.read_text())
        print(f"completed: {len(state.get('completed',[]))}")
        print(f"failed: {len(state.get('failed',[]))}")
        print(f"last_run_at: {state.get('last_run_at')}")
        print(f"last_run_keys: {state.get('last_run_keys')}")
        return

    wl = json.loads(WORKLIST_PATH.read_text())
    queue = build_queue(wl, args.topic)
    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {"completed": [], "failed": []}
    seen = set(state.get("completed", [])) | set(state.get("failed", []))
    queue = [p for p in queue if p["stem"] not in seen][: args.limit]

    if not queue:
        print("No pending papers to process.")
        return

    if args.dry_run:
        from collections import Counter
        topics = Counter(p.get("topic") for p in queue)
        print(f"Queue ({len(queue)} papers):")
        for t, n in topics.most_common():
            print(f"  {t}: {n}")
        return

    run_batch(args)


if __name__ == "__main__":
    main()
