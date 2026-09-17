#!/usr/bin/env python3
"""Unified RAG Query CLI for Antigravity Research Wiki & Raw Papers.

Usage:
    python query.py "What is the function of TaMFT in wheat?"
    python query.py "CRISPR ribonucleoprotein delivery in potato" --mode evidence
    python query.py --verify "codA negative selection enables transgene-free editing"
    python query.py --backfill "heat treatment enhances Cas9 RNP editing"
    python query.py --interactive
    python query.py "seed dormancy in cereals" --save generated_content/seed_dormancy.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure paths are set
HERE = Path(__file__).resolve().parent
WORKSPACE_ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

try:
    import llm_config
except ImportError:
    llm_config = None

from rag_engine import (
    CitationBackfillResult,
    ClaimVerificationResult,
    RAGEngine,
    RAGResponse,
)


def _current_model_name() -> str:
    if llm_config is not None:
        return llm_config.get_model()
    return os.environ.get("RAG_MODEL", "claude-opus-5-thinking")


def print_banner(mode: str = "evidence"):
    print("=" * 70)
    print("🔬 ANTIGRAVITY RAG KNOWLEDGE BASE — ZERO-HALLUCINATION QUERY ENGINE")
    if mode == "evidence":
        print("   Mode: Local SQLite FTS5/BM25 (Direct Cognitive Execution)")
    else:
        print(f"   Backend: chat-completions ({_current_model_name()}) + Local SQLite FTS5/BM25")
    print("=" * 70)


def print_evidence_drawer(hits: list[dict]):
    print("\n" + "-" * 70)
    print(f"🔍 RETRIEVED EVIDENCE SOURCES ({len(hits)} distinct passages from {len(set(h['path'] for h in hits))} papers):")
    print("-" * 70)
    for h in hits:
        line_info = f" (lines {h['lines']})" if h.get("lines") else ""
        print(f"[{h['rank']}] {h['title']}")
        print(f"    Path: {h['path']}{line_info} | Section: {h['section']} | Score: {h['score']:.2f}" if isinstance(h['score'], (int, float)) else f"    Path: {h['path']}{line_info} | Section: {h['section']} | Score: {h['score']}")
        snippet_text = h.get("snippet", "")
        if len(snippet_text) > 300:
            snippet_text = snippet_text[:300] + "..."
        print(f"    Snippet: {snippet_text}\n")


def print_verification_report(res: ClaimVerificationResult):
    print("=" * 70)
    print("🔬 ANTIGRAVITY CLAIM VERIFICATION AUDIT")
    print("=" * 70)
    print(f"CLAIM: {res.claim!r}\n")
    print(f"VERDICT:          {res.verdict} (Confidence: {res.confidence:.2f})")
    if res.primary_source:
        print(f"PRIMARY SOURCE:   {res.primary_source}")
    if res.path:
        lines_info = f" (lines {res.line_start}-{res.line_end})" if res.line_start and res.line_end else ""
        print(f"PATH:             {res.path}{lines_info}")
    if res.section:
        print(f"SECTION:          {res.section}")
    if res.evidence_snippet:
        print("EVIDENCE SNIPPET:")
        for line in res.evidence_snippet.splitlines()[:8]:
            print(f"  {line}")
    if res.reason:
        print(f"REASON:           {res.reason}")
    print(f"\nPERFORMANCE:      Total: {res.total_ms:.1f}ms (Retrieval: {res.retrieval_ms:.1f}ms, Audit: {res.verification_ms:.1f}ms)")
    print("=" * 70)


def print_backfill_report(res: CitationBackfillResult):
    print("=" * 70)
    print("📚 ANTIGRAVITY CITATION BACKFILL")
    print("=" * 70)
    print(f"STATEMENT: {res.statement!r}\n")
    if res.markdown_citation:
        print(f"MARKDOWN CITATION: {res.markdown_citation}")
    if res.doi:
        print(f"DOI:               {res.doi}")
    if res.title:
        print(f"PAPER TITLE:       {res.title}")
    if res.authors:
        print(f"AUTHORS:           {res.authors}")
    if res.year:
        print(f"YEAR:              {res.year}")
    if res.path:
        lines_info = f" (lines {res.lines})" if res.lines else ""
        print(f"SOURCE PATH:       {res.path}{lines_info}")
    if res.section:
        print(f"SECTION:           {res.section}")
    if res.excerpt:
        print("SUPPORTING EXCERPT:")
        for line in res.excerpt.splitlines()[:8]:
            print(f"  {line}")
    print(f"\nPERFORMANCE:       Total: {res.total_ms:.1f}ms")
    print("=" * 70)


def interactive_loop(engine: RAGEngine, mode: str = "evidence", top_k: int = 10, model: str | None = None, stream: bool = True):
    model = model or _current_model_name()
    current_mode = mode
    current_top_k = top_k
    show_evidence = (current_mode == "evidence")
    print_banner(mode=current_mode)
    print("Type your question and press Enter. Type 'exit', 'quit', or 'q' to stop.")
    print("Commands: /verify <claim>, /backfill <statement>, /evidence, /mode <hybrid|evidence|summary>, /topk <n>\n")

    while True:
        try:
            user_input = input("\n🔎 Ask KB > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break
        if user_input.startswith(("/verify", ":verify")):
            parts = user_input.split(maxsplit=1)
            claim = parts[1] if len(parts) > 1 else ""
            res = engine.verify_claim(claim)
            print_verification_report(res)
            continue
        if user_input.startswith(("/backfill", ":backfill")):
            parts = user_input.split(maxsplit=1)
            stmt = parts[1] if len(parts) > 1 else ""
            res = engine.backfill_citation(stmt)
            print_backfill_report(res)
            continue
        if user_input.startswith("/evidence"):
            show_evidence = not show_evidence
            print(f"Evidence view: {'ENABLED' if show_evidence else 'DISABLED'}")
            continue
        if user_input.startswith("/mode"):
            parts = user_input.split()
            if len(parts) > 1 and parts[1] in {"hybrid", "evidence", "summary"}:
                current_mode = parts[1]
                if current_mode == "evidence":
                    show_evidence = True
                print(f"Retrieval mode set to: {current_mode}")
            else:
                print("Usage: /mode <hybrid|evidence|summary>")
            continue
        if user_input.startswith("/topk"):
            parts = user_input.split()
            if len(parts) > 1 and parts[1].isdigit():
                current_top_k = int(parts[1])
                print(f"Top-K set to: {current_top_k}")
            else:
                print("Usage: /topk <number>")
            continue

        print("\n" + "=" * 70)
        print(f"QUERY: {user_input}")
        print(f"MODEL: {model} | RETRIEVAL: {current_mode} | TOP-K: {current_top_k}")
        print("=" * 70 + "\n")

        if current_mode == "evidence":
            res = engine.query(
                user_input,
                top_k=current_top_k,
                mode=current_mode,
                model=model,
            )
            print(f"Retrieved {len(res.hits)} evidence passages in {res.retrieval_ms:.1f}ms.")
            print_evidence_drawer(res.hits)
        elif stream:
            def stream_cb(token: str):
                sys.stdout.write(token)
                sys.stdout.flush()

            res = engine.query(
                user_input,
                top_k=current_top_k,
                mode=current_mode,
                model=model,
                stream_callback=stream_cb,
            )
            print("\n")
        else:
            res = engine.query(
                user_input,
                top_k=current_top_k,
                mode=current_mode,
                model=model,
            )
            print(res.answer)

        if current_mode != "evidence":
            print("\n" + "-" * 70)
            status_icon = "✅ Grounded" if res.grounding_ok else "⚠️ Partially Verified"
            print(f"PERFORMANCE: Total: {res.total_ms:.1f}ms (Retrieval: {res.retrieval_ms:.1f}ms, Synthesis: {res.synthesis_ms:.1f}ms) | {status_icon} (Confidence: {res.grounding_confidence:.2f})")
            if res.verified_entities:
                print(f"VERIFIED ENTITIES: {', '.join(res.verified_entities[:8])}{'...' if len(res.verified_entities) > 8 else ''}")
            if res.unsupported_entities:
                print(f"UNSUPPORTED ENTITIES: {', '.join(res.unsupported_entities)}")
            print("-" * 70)

            if show_evidence:
                print_evidence_drawer(res.hits)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Query the Antigravity Research Wiki & Raw Papers (grounded RAG)"
    )
    parser.add_argument("query", nargs="*", help="Research query in natural language")
    parser.add_argument("--verify", type=str, default=None, metavar="CLAIM",
                        help="Audit claim against local corpus (SUPPORTED/CONTRADICTED/NOT_FOUND) in <1s")
    parser.add_argument("--backfill", type=str, default=None, metavar="STATEMENT",
                        help="Identify primary citation key, DOI, Markdown link, and excerpt for a statement")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive Q&A shell")
    parser.add_argument("--mode", default="evidence", choices=("hybrid", "evidence", "summary"), help="Retrieval mode (default: evidence)")
    parser.add_argument("--llm", action="store_true", help="Enable remote LLM synthesis (switches mode to hybrid)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of evidence chunks to retrieve (default: 10)")
    parser.add_argument("--model", default=None, help=f"Model name on the chat-completions backend (default: {_current_model_name()})")
    parser.add_argument("--no-stream", action="store_true", help="Disable token streaming output")
    parser.add_argument("--show-evidence", action="store_true", help="Print raw retrieved evidence snippets")
    parser.add_argument("--save", type=str, default=None, help="Optional path to save response markdown file")

    args = parser.parse_args(argv)
    if args.llm:
        args.mode = "hybrid"
    args.model = args.model or _current_model_name()
    engine = RAGEngine()

    # 1. Claim Verification Mode
    if args.verify is not None:
        claim_str = args.verify if args.verify else (" ".join(args.query) if args.query else "")
        res = engine.verify_claim(claim_str)
        if args.json:
            print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        else:
            print_verification_report(res)
        return 0

    # 2. Citation Backfill Mode
    if args.backfill is not None:
        stmt_str = args.backfill if args.backfill else (" ".join(args.query) if args.query else "")
        res = engine.backfill_citation(stmt_str)
        if args.json:
            print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        else:
            print_backfill_report(res)
        return 0

    # 3. Interactive Mode
    if args.interactive or not args.query:
        interactive_loop(engine, mode=args.mode, top_k=args.top_k, model=args.model, stream=not args.no_stream)
        return 0

    query_str = " ".join(args.query)

    if args.mode == "evidence":
        print_banner(mode="evidence")
        print(f"\nQUERY: {query_str}")
        print(f"RETRIEVAL: evidence (Direct Cognitive Execution) | TOP-K: {args.top_k}\n")
        res = engine.query(
            query_str,
            top_k=args.top_k,
            mode="evidence",
            model=args.model,
        )
        print(f"Retrieved {len(res.hits)} evidence passages in {res.retrieval_ms:.1f}ms.")
        print_evidence_drawer(res.hits)
    else:
        print_banner(mode=args.mode)
        print(f"\nQUERY: {query_str}")
        print(f"MODEL: {args.model} | RETRIEVAL: {args.mode} | TOP-K: {args.top_k}\n")

        if not args.no_stream:
            def stream_cb(token: str):
                sys.stdout.write(token)
                sys.stdout.flush()

            res = engine.query(
                query_str,
                top_k=args.top_k,
                mode=args.mode,
                model=args.model,
                stream_callback=stream_cb,
            )
            print("\n")
        else:
            res = engine.query(
                query_str,
                top_k=args.top_k,
                mode=args.mode,
                model=args.model,
            )
            print(res.answer)

        print("-" * 70)
        status_icon = "✅ Grounded" if res.grounding_ok else "⚠️ Partially Verified"
        print(f"PERFORMANCE: Total: {res.total_ms:.1f}ms (Retrieval: {res.retrieval_ms:.1f}ms, Synthesis: {res.synthesis_ms:.1f}ms) | {status_icon} (Confidence: {res.grounding_confidence:.2f})")
        if res.verified_entities:
            print(f"VERIFIED ENTITIES: {', '.join(res.verified_entities[:8])}{'...' if len(res.verified_entities) > 8 else ''}")
        if res.unsupported_entities:
            print(f"UNSUPPORTED ENTITIES: {', '.join(res.unsupported_entities)}")
        print("-" * 70)

        if args.show_evidence:
            print_evidence_drawer(res.hits)

    if args.save:
        save_path = Path(args.save)
        if not save_path.is_absolute():
            save_path = WORKSPACE_ROOT / save_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        if args.mode == "evidence":
            md_lines = [
                f"# Evidence Retrieval: {query_str}\n",
                f"- **Query:** {query_str}",
                f"- **Passages Retrieved:** {len(res.hits)}",
                f"- **Mode:** Local SQLite FTS5/BM25 Evidence Retrieval\n",
                "## Retrieved Evidence Passages\n",
            ]
            for h in res.hits:
                line_info = f" (lines {h['lines']})" if h.get("lines") else ""
                score_str = f"{h['score']:.2f}" if isinstance(h.get('score'), (int, float)) else str(h.get('score', ''))
                md_lines.append(f"### [{h.get('rank', 0)}] {h.get('title', '')}")
                md_lines.append(f"- **Path:** `{h.get('path', '')}`{line_info}")
                md_lines.append(f"- **Section:** {h.get('section', '')}")
                md_lines.append(f"- **Score:** {score_str}\n")
                md_lines.append("```markdown")
                md_lines.append(h.get("snippet", "").strip())
                md_lines.append("```\n")
            save_path.write_text("\n".join(md_lines), encoding="utf-8")
        else:
            save_path.write_text(res.answer, encoding="utf-8")
        print(f"\n💾 Saved response to: {save_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
