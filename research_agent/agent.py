"""Research-wiki retrieval agent.

A model + tools + loop + memory agent that grounds every answer in the
Antigravity research-wiki corpus. If no LLM key is available or LLM synthesis
fails, it gracefully degrades to a deterministic tools-only hit list.

Usage:
    python3 -m research_agent.agent "preharvest sprouting in wheat"
    python3 -m research_agent.agent "What genes regulate seed dormancy?" --mode evidence
    python3 -m research_agent.agent "query" --no-llm --quiet
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from research_agent import llm, wiki_tools, verifier  # noqa: E402

_MAX_OBS_CHARS = 8000
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_BARE_JSON = re.compile(r"\{[^{}]*\"(tool|answer|query)\"[^{}]*\}", re.DOTALL)

SYSTEM_PROMPT = """You are a retrieval agent for the Antigravity research-wiki.

Corpus: ~2,870 paper summaries, ~33,600 entity pages, ~15,200 concept pages
covering plant genetics (especially seed/bud/tuber dormancy, germination,
transcription factors, and genome editing in vegetatively propagated crops).

Rules:
1. Ground every factual claim in retrieved evidence. Never fabricate
   authors, DOIs, numbers, or page content. Say "no evidence in wiki" if
   nothing is retrieved.
2. Every output must end with a References block listing, per claim,
   author-year title, path in the wiki, and section when known.
3. Cite inline as (Author Year, path#section) when you can.
4. When the first search is insufficient, follow up with additional tool
   calls (read_page for detail, related_pages to follow the graph, or a
   second wiki_search with different or expanded terms) before answering.
5. Prefer evidence over entity pages because entities aggregate claims;
   both are acceptable.
6. When you find a key paper, use citation tools to trace the research:
   - papers_i_cite(paper) to see what it builds on
   - papers_citing(paper) to see later work that references it
   - related_papers(paper) to find papers sharing citations
   - citation_chain(paper_a, paper_b) to connect two papers

You MUST reply with EXACTLY one JSON object inside ```json ... ```. Two shapes:

To call a tool:
```json
{"tool": "wiki_search", "args": {"query": "seed dormancy genes", "top_k": 8}}
```

To give the final answer:
```json
{"answer": "Your grounded synthesis here, with citations and References block."}
```

Available tools:
"""


def _format_manifest() -> str:
    return wiki_tools.tool_manifest()


def _parse_response(text: str) -> dict:
    """Parse the agent's reply into a tool-call or answer dict.
    
    Handles both:
    - {"tool": "wiki_search", "args": {...}}
    - {"query": "...", ...} (bare tool args, infer wiki_search)
    """
    m = _JSON_FENCE.search(text)
    if not m:
        m = _BARE_JSON.search(text)
    if not m:
        raise ValueError(f"no JSON found in LLM reply:\n{text[:400]}")
    try:
        parsed = json.loads(m.group(1))
    except json.JSONDecodeError:
        start, end = m.start(1), m.end(1)
        parsed = json.loads(text[start:end])
    
    # If LLM output bare tool args (e.g., {"query": ...}), wrap as tool call
    if "tool" not in parsed and "answer" not in parsed:
        if "query" in parsed or "top_k" in parsed or "mode" in parsed:
            parsed = {"tool": "wiki_search", "args": parsed}
        elif "path" in parsed:
            if "start" in parsed and "end" in parsed:
                parsed = {"tool": "read_lines", "args": parsed}
            else:
                parsed = {"tool": "read_page", "args": parsed}
        elif "page" in parsed or "page_path" in parsed:
            parsed = {"tool": "related_pages", "args": parsed}
    
    return parsed


def _truncate(text: str, n: int = _MAX_OBS_CHARS) -> str:
    if len(text) <= n:
        return text
    return text[:n] + f"\n…[truncated, {len(text) - n} chars omitted]"


def _path_exists(canon: str) -> bool:
    """True when a canonical ``<kind>/….md`` path exists under the wiki root."""
    try:
        return (wiki_tools.WIKI_DIR / canon).exists()
    except Exception:  # noqa: BLE001
        return False


def _slug(query: str) -> str:
    keep = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    return keep[:60] or "query"


def _save_session(slug: str, transcript: list[dict], answer: str) -> Path:
    out = HERE / "output" / f"{int(time.time())}-{slug}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "transcript.json").write_text(json.dumps(transcript, indent=2, default=str))
    (out / "answer.md").write_text(answer)
    return out


def _is_valid_grounded_answer(ans: str) -> bool:
    """Check that the answer is non-empty, grounded, and not a raw JSON/tool call."""
    if not ans or not isinstance(ans, str) or not ans.strip():
        return False
    stripped = ans.strip()
    if "[max turns reached]" in stripped:
        return False
    # Reject raw JSON tool calls and dictionaries
    if stripped.startswith("{") and (
        '"tool"' in stripped or '"query"' in stripped or '"args"' in stripped or '"answer"' in stripped
    ):
        return False
    if _JSON_FENCE.search(stripped) and ('"tool"' in stripped or '"args"' in stripped):
        return False
    return True


def _deterministic_hit_list(
    query: str,
    top_k: int = 8,
    mode: str = "hybrid",
    gathered_hits: list[dict] | None = None,
    reason: str = "tools-only; LLM not available",
) -> str:
    """Generate a clean, deterministic markdown hit list from gathered hits or fresh search."""
    hits: list[dict] = []
    seen: set[tuple[str | None, str | None]] = set()

    if gathered_hits:
        for h in gathered_hits:
            if not isinstance(h, dict):
                continue
            key = (h.get("path"), h.get("title"))
            if key not in seen and (h.get("path") or h.get("title")):
                seen.add(key)
                hits.append(h)

    if not hits:
        fresh_hits = wiki_tools.wiki_search(query, top_k=top_k, mode=mode)
        for h in fresh_hits:
            key = (h.get("path"), h.get("title"))
            if key not in seen:
                seen.add(key)
                hits.append(h)

    lines = [
        f"# Results for: {query}\n",
        f"Mode: {mode} ({reason})\n",
    ]

    display_hits = hits[:top_k] if top_k else hits
    if not display_hits:
        lines.append("No results found in wiki corpus.\n")
        return "\n".join(lines)

    for rank, h in enumerate(display_hits, start=1):
        title = h.get("title") or "Untitled Document"
        doc_type = h.get("doc_type", "doc")
        score = h.get("score", 0.0)
        quality = h.get("evidence_quality")
        path = h.get("path")
        lines_info = h.get("lines")
        snippet = (h.get("snippet") or "").strip()

        lines.append(f"## {rank}. {title}")
        meta = f"   [{doc_type}] score={score}"
        if quality is not None:
            meta += f" quality={quality}"
        lines.append(meta)
        if path:
            lines.append(f"   path: {path}" + (f" ({lines_info})" if lines_info else ""))
        if snippet:
            lines.append(f"   {snippet}")
        lines.append("")

    return "\n".join(lines)


def _tools_only_listing(query: str, top_k: int, mode: str) -> str:
    return _deterministic_hit_list(query, top_k=top_k, mode=mode, reason="tools-only; LLM not available")


def run(query: str, *, top_k: int = 8, mode: str = "hybrid", max_turns: int = 10,
        use_llm: bool = True, quiet: bool = False) -> str:
    stats = wiki_tools.wiki_stats()
    if not quiet:
        print(f"Wiki: {stats['pages']}")
        print(f"LLM available: {llm.has_key()}")
        print(f"Query: {query!r}\n")

    transcript: list[dict] = [{"system": SYSTEM_PROMPT, "user": query}]
    all_gathered_hits: list[dict] = []
    evidence_chunks: list[str] = []
    retrieved_paths: set[str] = set()

    if not use_llm or not llm.has_key():
        answer = _deterministic_hit_list(
            query, top_k=top_k, mode=mode, reason="tools-only; LLM not available"
        )
        out = _save_session(_slug(query), transcript, answer)
        if not quiet:
            print(answer)
            print(f"\nsession: {out}")
        return answer

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT + _format_manifest()},
        {"role": "user", "content": query},
    ]

    answer = ""
    grounding_retries = 0
    try:
        from config import (
            RETRIEVAL_GROUNDING_THRESHOLD as _GROUND_THRESHOLD,
            RETRIEVAL_GROUNDING_MAX_RETRIES as _GROUND_MAX_RETRIES,
        )
    except Exception:  # noqa: BLE001
        _GROUND_THRESHOLD, _GROUND_MAX_RETRIES = 0.75, 2

    def _finalize(candidate: str) -> tuple[str, "verifier.GroundingReport"]:
        """Verify a candidate answer against retrieved evidence; abstain if empty."""
        report = verifier.verify_answer(
            candidate, evidence_chunks, retrieved_paths,
            threshold=_GROUND_THRESHOLD, path_exists=_path_exists,
        )
        final = candidate
        if not report.ok and report.evidence_empty:
            final = verifier.ABSTENTION
        return final, report

    for turn in range(1, max_turns + 1):
        try:
            reply = llm.chat(messages, temperature=max(0.0, (0.1 if turn > 1 else 0.2)))
        except (llm.LLMUnavailable, Exception) as e:
            if not quiet:
                print(f"[warning] LLM chat failed on turn {turn}: {e}")
            transcript.append({"turn": turn, "llm_error": str(e), "error_type": type(e).__name__})
            break

        transcript.append({"turn": turn, "assistant": reply})
        if not quiet:
            print(f"[turn {turn}] {reply[:300]!r}")

        try:
            parsed = _parse_response(reply)
        except ValueError as e:
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user",
                            "content": f"Your reply was not valid JSON: {e}. Reply with a JSON block."})
            continue

        if "answer" in parsed:
            candidate = parsed["answer"]
            final, report = _finalize(candidate)
            if report.ok or grounding_retries >= _GROUND_MAX_RETRIES:
                if _is_valid_grounded_answer(final):
                    answer = final
                    transcript.append({"answer": answer, "grounding": report.as_dict()})
                    if not quiet:
                        print(f"  grounding: confidence={report.confidence:.2f} "
                              f"ok={report.ok} invalid_citations={len(report.invalid_citations)}"
                              + (" [abstained]" if final == verifier.ABSTENTION else ""))
                    break
            grounding_retries += 1
            if not quiet:
                print(f"  [grounding] failed (confidence={report.confidence:.2f}, "
                      f"unsupported={len(report.unsupported)}, "
                      f"invalid_citations={len(report.invalid_citations)}); "
                      f"repair {grounding_retries}/{_GROUND_MAX_RETRIES}")
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": verifier.build_repair_message(report)})
            transcript.append({"grounding_repair": report.as_dict(), "attempt": grounding_retries})
            continue

        tool_name = parsed.get("tool")
        tool_args = parsed.get("args") or {}
        try:
            result = wiki_tools.dispatch(tool_name, tool_args)
        except Exception as e:  # noqa: BLE001
            observation = f"ERROR calling {tool_name}: {type(e).__name__}: {e}"
            result_data = {"error": str(e), "error_type": type(e).__name__}
        else:
            observation = json.dumps(result, default=str, ensure_ascii=False)
            result_data = result
            if tool_name == "wiki_search" and isinstance(result, list):
                all_gathered_hits.extend(result)

        observation = _truncate(observation, _MAX_OBS_CHARS)
        # Track the evidence the agent actually saw so the final answer can be
        # verified against it, and record which wiki paths were retrieved.
        evidence_chunks.append(observation)
        for _p in verifier.extract_cited_paths(observation):
            retrieved_paths.add(_p)
        if isinstance(tool_args, dict) and isinstance(tool_args.get("path"), str):
            retrieved_paths.add(verifier._canon(tool_args["path"]))
        if not quiet:
            print(f"  → {tool_name}({json.dumps(tool_args, default=str)})")
            print(f"  observation ({len(observation)} chars)")

        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Observation from {tool_name}:\n{observation}"})
        transcript.append(
            {
                "tool": tool_name,
                "args": tool_args,
                "observation": result_data,
                "observation_text": observation,
                "observation_len": len(observation),
            }
        )
        
        # If we're at max_turns and the last reply was a tool call, force synthesis
        if turn == max_turns:
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", 
                            "content": "You have gathered enough evidence. Now synthesize a final grounded answer with citations and a References block. Output as JSON: {\"answer\": \"...\"}"})
            try:
                final_reply = llm.chat(messages, temperature=0.2)
                final_parsed = _parse_response(final_reply)
                if "answer" in final_parsed:
                    candidate_ans = final_parsed["answer"]
                    final_cand, report = _finalize(candidate_ans)
                    if _is_valid_grounded_answer(final_cand):
                        answer = final_cand
                        transcript.append({"turn": "final", "assistant": final_reply,
                                           "grounding": report.as_dict()})
                        if not quiet:
                            print(f"[final] synthesized answer "
                                  f"(grounding confidence={report.confidence:.2f}, ok={report.ok})")
            except Exception as e:
                if not quiet:
                    print(f"[warning] final synthesis failed: {e}")
                transcript.append({"turn": "final", "synthesis_error": str(e), "error_type": type(e).__name__})

    if not _is_valid_grounded_answer(answer):
        answer = _deterministic_hit_list(
            query,
            top_k=top_k,
            mode=mode,
            gathered_hits=all_gathered_hits,
            reason="deterministic fallback; LLM synthesis unavailable",
        )
        transcript.append({
            "fallback": "deterministic_hit_list",
            "gathered_hits_count": len(all_gathered_hits),
            "retrieved_paths_count": len(retrieved_paths),
        })

    out = _save_session(_slug(query), transcript, answer)
    if not quiet:
        print(f"\n---ANSWER---\n{answer}")
        print(f"\nsession: {out}")
    return answer


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="research_agent", description="Query-retrieval agent for the research-wiki")
    p.add_argument("query", help="Research query in natural language")
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--mode", default="hybrid", choices=("summary", "hybrid", "evidence"))
    p.add_argument("--turns", type=int, default=10)
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)
    run(query=args.query, top_k=args.top_k, mode=args.mode,
        max_turns=args.turns, use_llm=not args.no_llm, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
