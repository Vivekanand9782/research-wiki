#!/usr/bin/env python3
"""auto_improve_wiki.py — End-to-end automated research-wiki maintenance suite.

Combines:
  1. reconcile_wiki.py  — Auto-instantiates missing concept/entity seed pages from wikilinks.
  2. rollup_summaries.py --apply — Synthesizes multi-paper findings & resolves contradictions.
  3. lint_wiki.py --fix — Repairs structural syntax and format drift.
  4. lint_wiki_semantic.py — Audits knowledge graph for semantic contradictions & gaps.

Semantic Audit Modes (Step 4):
  --auto-discover      (DEFAULT) Finds the N most-recently-changed entities/concepts
                       and audits each one's complete sub-graph cluster iteratively.
                       This is the foolproof mode — every connected paper is included.
  --entity SLUG        Audit a single entity/concept's full sub-graph cluster.
  --pages N            Legacy fallback: audit N most-recently-modified pages (mtime-based,
                       NOT recommended — misses cross-page contradictions).

Usage:
    python3 auto_improve_wiki.py                        # full pipeline, auto-discover mode
    python3 auto_improve_wiki.py --entity nifa           # full pipeline, audit nifa sub-graph
    python3 auto_improve_wiki.py --skip-rollup           # skip LLM summary rollup pass
    python3 auto_improve_wiki.py --discover-top 10       # auto-discover top 10 changed entities
    python3 auto_improve_wiki.py --pages 50              # legacy mtime mode (not recommended)
    python3 auto_improve_wiki.py --skip-reconcile --skip-rollup --skip-lint  # semantic audit only
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import config  # noqa: F401 -- ensures env is loaded with override=True

WIKI_DIR = ROOT / "wiki"


# ---------------------------------------------------------------------------
# Auto-discovery: find recently-changed entities/concepts for sub-graph audit
# ---------------------------------------------------------------------------

def _discover_changed_entities(top_n: int = 5) -> list[str]:
    """Return slugs of the top_n most-recently-modified entity/concept pages.

    These are the pages most likely to have fresh data that may contradict
    older linked pages — exactly the clusters worth auditing.
    """
    candidates: list[tuple[float, str]] = []
    for subdir in ["entities", "concepts"]:
        d = WIKI_DIR / subdir
        if not d.exists():
            continue
        for md in d.glob("*.md"):
            try:
                mtime = md.stat().st_mtime
                slug = md.stem  # filename without .md
                candidates.append((mtime, slug))
            except Exception:
                pass

    # Sort newest-first, deduplicate slugs (entity and concept may share a name)
    candidates.sort(key=lambda t: t[0], reverse=True)
    seen: set[str] = set()
    result: list[str] = []
    for _, slug in candidates:
        if slug not in seen:
            seen.add(slug)
            result.append(slug)
        if len(result) >= top_n:
            break
    return result


def _run_step_1_reconcile(skip: bool) -> None:
    """Step 1: Reconcile wiki — create missing seed pages & rebuild search index."""
    if skip:
        print("\n[Step 1/4] ⏭️  Skipped reconciliation (--skip-reconcile set).")
        return

    print("\n[Step 1/4] 🧩 Reconciling wiki & creating missing seed pages...")
    try:
        from reconcile_wiki import main as reconcile_main
        try:
            reconcile_main()
        except SystemExit as e:
            if e.code == 0:
                print("  ✓ Step 1 complete: Seed pages reconciled and index updated.")
            else:
                print(f"  ⚠️  Step 1 finished with non-zero exit code: {e.code}")
    except Exception as e:
        print(f"  ❌ Step 1 encountered error: {e}")


def _run_step_2_rollup(skip: bool) -> None:
    """Step 2: Multi-paper LLM synthesis & contradiction resolution."""
    if skip:
        print("\n[Step 2/4] ⏭️  Skipped rollup summary pass (--skip-rollup set).")
        return

    print("\n[Step 2/4] 🔄 Rolling up multi-paper findings via LLM...")
    saved_argv = sys.argv[:]
    try:
        from rollup_summaries import main as rollup_main
        sys.argv = ["rollup_summaries.py", "--apply"]
        rollup_main()
        print("  ✓ Step 2 complete: Multi-paper findings synthesized.")
    except SystemExit as e:
        if e.code != 0:
            print(f"  ⚠️  Step 2 finished with exit code {e.code}")
    except Exception as e:
        print(f"  ❌ Step 2 encountered error: {e}")
    finally:
        sys.argv = saved_argv


def _run_step_3_lint(skip: bool) -> None:
    """Step 3: Deterministic structural lint & auto-repair."""
    if skip:
        print("\n[Step 3/4] ⏭️  Skipped structural lint (--skip-lint set).")
        return

    print("\n[Step 3/4] 📐 Running structural lint & auto-repair...")
    try:
        from lint_wiki import lint_wiki
        res = lint_wiki(fix=True)
        fmt = res.get("format_errors", 0)
        struct = res.get("structural_errors", 0)
        debt = res.get("content_debt", 0)
        repaired = res.get("repaired", 0)
        print(
            f"  ✓ Step 3 complete: {repaired} pages auto-repaired, "
            f"{fmt} format errors, {struct} structural errors, "
            f"{debt} content-debt pages remaining."
        )

    except Exception as e:
        print(f"  ❌ Step 3 encountered error: {e}")


def _run_step_4_semantic(
    entity: str | None,
    auto_discover: bool,
    discover_top: int,
    legacy_pages: int | None,
    fix: bool = True,
) -> None:
    """Step 4: Semantic graph audit via LLM + optional auto-repair.

    Three modes (in priority order):
      1. --entity SLUG       → audit one entity's full sub-graph
      2. --auto-discover      → find recently-changed entities, audit each sub-graph
      3. --pages N            → legacy mtime-based page selection (not recommended)
    """
    from lint_wiki_semantic import main as semantic_lint_main

    saved_argv = sys.argv[:]

    if entity:
        # ── Mode 1: Single entity sub-graph ──
        print(f"\n[Step 4/4] 🔍 Semantic audit: entity sub-graph cluster for '{entity}'...")
        sys.argv = ["lint_wiki_semantic.py", "--entity", entity] + (["--fix"] if fix else [])
        try:
            semantic_lint_main()
            print(f"  ✓ Step 4 complete: Sub-graph audit{' + repair' if fix else ''} for '{entity}' → wiki_lint_semantic_report.md")
        except SystemExit:
            pass
        except Exception as e:
            print(f"  ❌ Step 4 error: {e}")
        finally:
            sys.argv = saved_argv

    elif auto_discover:
        # ── Mode 2: Auto-discover recently-changed entities ──
        slugs = _discover_changed_entities(top_n=discover_top)
        if not slugs:
            print("\n[Step 4/4] ⚠️  No entity/concept pages found for auto-discovery.")
            return

        print(f"\n[Step 4/4] 🔍 Semantic audit: auto-discovering top {len(slugs)} recently-changed entities...")
        print(f"  Entities queued: {', '.join(slugs)}")

        success = 0
        errors = 0
        for i, slug in enumerate(slugs, 1):
            print(f"\n  [{i}/{len(slugs)}] Auditing sub-graph for '{slug}'...")
            # Each iteration appends to its own report section
            sys.argv = ["lint_wiki_semantic.py", "--entity", slug] + (["--fix"] if fix else [])
            try:
                semantic_lint_main()
                success += 1
                print(f"    ✓ '{slug}' audit complete.")
            except SystemExit:
                success += 1  # exit 0 from argparse
            except Exception as e:
                errors += 1
                print(f"    ❌ '{slug}' audit failed: {e}")
            finally:
                sys.argv = saved_argv

        print(f"\n  ✓ Step 4 complete: {success} entity sub-graphs audited, {errors} errors.")

    else:
        # ── Mode 3: Legacy mtime-based (fallback) ──
        pages = legacy_pages or 20
        print(f"\n[Step 4/4] 🔍 Semantic audit: legacy mtime mode ({pages} pages)...")
        print("  ⚠️  Consider using --auto-discover or --entity for better contradiction detection.")
        sys.argv = ["lint_wiki_semantic.py", "--pages", str(pages)] + (["--fix"] if fix else [])
        try:
            semantic_lint_main()
            print(f"  ✓ Step 4 complete: Semantic audit ({pages} pages) → wiki_lint_semantic_report.md")
        except SystemExit:
            pass
        except Exception as e:
            print(f"  ❌ Step 4 error: {e}")
        finally:
            sys.argv = saved_argv


def main():
    parser = argparse.ArgumentParser(
        description="Automated Research Wiki Improvement Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 auto_improve_wiki.py                          # full pipeline, auto-discover mode
  python3 auto_improve_wiki.py --entity nifa            # audit nifa sub-graph
  python3 auto_improve_wiki.py --discover-top 10        # auto-discover top 10 changed entities
  python3 auto_improve_wiki.py --pages 50               # legacy mtime mode (not recommended)
  python3 auto_improve_wiki.py --skip-reconcile --skip-rollup --skip-lint  # semantic audit only
        """,
    )

    # Step skip flags
    parser.add_argument("--skip-reconcile", action="store_true",
                        help="Skip Step 1 (reconcile wiki)")
    parser.add_argument("--skip-rollup", action="store_true",
                        help="Skip Step 2 (LLM rollup summary synthesis)")
    parser.add_argument("--skip-lint", action="store_true",
                        help="Skip Step 3 (structural lint & auto-repair)")
    parser.add_argument("--skip-semantic", action="store_true",
                        help="Skip Step 4 (semantic graph audit)")

    # Step 4 audit mode flags
    audit = parser.add_argument_group("Semantic Audit (Step 4)")
    audit.add_argument("--entity", default=None,
                       help="Audit a single entity/concept's full sub-graph cluster (e.g. 'nifa')")
    audit.add_argument("--auto-discover", action="store_true", default=True,
                       help="(DEFAULT) Auto-discover recently-changed entities and audit sub-graphs")
    audit.add_argument("--no-auto-discover", action="store_false", dest="auto_discover",
                       help="Disable auto-discover mode (use with --pages for legacy mode)")
    audit.add_argument("--discover-top", type=int, default=5,
                       help="Number of entities to auto-discover (default: 5)")
    audit.add_argument("--pages", type=int, default=None,
                       help="Legacy: audit N most-recently-modified pages by mtime (not recommended)")
    audit.add_argument("--no-semantic-fix", action="store_true",
                       help="Disable LLM auto-repair in Step 4 (report only)")

    args = parser.parse_args()

    # If --pages is explicitly set, disable auto-discover unless --entity is also set
    if args.pages is not None and not args.entity:
        args.auto_discover = False

    t0 = time.time()
    print("=" * 70)
    print("🚀 RESEARCH WIKI AUTOMATED IMPROVEMENT SUITE")
    print("=" * 70)

    # Determine audit mode label
    if args.skip_semantic:
        audit_label = "skipped"
    elif args.entity:
        audit_label = f"entity sub-graph: {args.entity}"
    elif args.auto_discover:
        audit_label = f"auto-discover top {args.discover_top}"
    else:
        audit_label = f"legacy mtime: {args.pages or 20} pages"
    if not args.skip_semantic and args.no_semantic_fix:
        audit_label += " (report-only)"
    print(f"  Semantic audit mode: {audit_label}")

    # ── Step 1 ──
    _run_step_1_reconcile(skip=args.skip_reconcile)

    # ── Step 2 ──
    _run_step_2_rollup(skip=args.skip_rollup)

    # ── Step 3 ──
    _run_step_3_lint(skip=args.skip_lint)

    # ── Step 4 ──
    if args.skip_semantic:
        print("\n[Step 4/4] ⏭️  Skipped semantic audit (--skip-semantic set).")
    else:
        _run_step_4_semantic(
            entity=args.entity,
            auto_discover=args.auto_discover,
            discover_top=args.discover_top,
            legacy_pages=args.pages,
            fix=not args.no_semantic_fix,
        )

    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print(f"🎉 WIKI AUTOMATED IMPROVEMENT COMPLETE ({elapsed:.1f}s)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
