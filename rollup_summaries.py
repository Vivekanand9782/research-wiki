#!/usr/bin/env python
"""Re-synthesise the **Summary** of entity/concept seed pages from their
accumulated, non-stub `### Findings from [[...]]` blocks.

Why: a seed page's **Summary** is written ONCE at creation (from the first
citing paper's snippet) and never refreshed — `_update_seed_page` only appends
findings. So a 22-source page keeps a one-paper summary. This pass reads every
real finding already on the page (cross-source) and rewrites the Summary to
reflect all of them, reconciling duplicates/contradictions. It needs no PDFs —
the findings are already on disk.

Safe by default: dry-run unless ``--apply``; modified files are backed up to
``.backup/rollup_<timestamp>/`` first.

Usage::

    python3 rollup_summaries.py                      # dry-run, both kinds
    python3 rollup_summaries.py --apply --limit 5    # write 5 pages
    python3 rollup_summaries.py --kind concepts --min-findings 3 --apply
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WIKI = ROOT / "wiki"

# Summary block sits between the **Summary**: label and the **Sources**: label.
_SUMMARY_RE = re.compile(r"(\*\*Summary\*\*:\n)(.*?)(\n\n\*\*Sources\*\*:)", re.DOTALL)
_FINDING_RE = re.compile(
    r"### Findings from \[\[(.*?)\]\]\n(.*?)(?=\n### Findings from |\n## Related pages|\Z)",
    re.DOTALL,
)
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def non_stub_findings(text: str) -> list[str]:
    """Return the finding bodies that are real content (not stub placeholders)."""
    out = []
    for m in _FINDING_RE.finditer(text):
        body = m.group(2).strip()
        if body and not body.startswith("_Stub:"):
            out.append(body)
    return out


_FP_RE = re.compile(r"^rollup_fp:\s*(\S+)\s*$", re.MULTILINE)


def _rollup_fingerprint(text: str) -> str:
    """12-char hash of the source names that contribute a real (non-stub)
    finding. Changes only when a new source adds a finding (or a stub finding
    is upgraded) — so a page is re-synthesised only when its inputs changed."""
    names = sorted(
        m.group(1).strip()
        for m in _FINDING_RE.finditer(text)
        if m.group(2).strip() and not m.group(2).strip().startswith("_Stub:")
    )
    return hashlib.md5("\n".join(names).encode("utf-8")).hexdigest()[:12]


def _stored_fp(text: str) -> str | None:
    m = _FP_RE.search(text)
    return m.group(1) if m else None


def _set_fp(text: str, fp: str) -> str:
    """Upsert ``rollup_fp:`` in frontmatter (replace, else insert after date_updated)."""
    if _FP_RE.search(text):
        return _FP_RE.sub(lambda m: f"rollup_fp: {fp}", text, count=1)
    return re.sub(r"(date_updated:.*\n)", lambda m: m.group(1) + f"rollup_fp: {fp}\n", text, count=1)


def synthesise(name: str, category: str, findings: list[str], get_ai_response, model) -> str:
    joined = "\n".join(f"- {f}" for f in findings)
    prompt = (
        f"You are writing the summary for a research-wiki {category} page "
        f'titled "{name}".\n'
        f'Below are factual findings about "{name}" extracted from multiple '
        "papers. Synthesise them into a neutral, factual 2-4 sentence overview. "
        "Merge duplicates; if findings genuinely conflict, state the "
        "disagreement briefly. Base the summary ONLY on the findings below. "
        "Plain prose only — no headings, lists, wikilinks, or citations.\n\n"
        f"Findings:\n{joined}\n"
    )
    return get_ai_response(
        prompt, model=model, raise_on_error=True, thinking=False
    ).strip()


def run_rollup(*, kind: str = "both", min_findings: int = 2, limit: int = 0,
               apply: bool = False, workers: int = 4,
               pages: list[Path] | None = None) -> dict:
    """Re-synthesise stale page summaries. A page is processed only when its
    finding fingerprint differs from the ``rollup_fp:`` stored in frontmatter,
    so an unchanged page is never re-synthesised. ``pages`` restricts the run
    to an explicit list (used by the ingest pipeline for just-touched pages)."""
    import config
    from genai_client import get_ai_response
    model = getattr(config, "AI_MODEL", None)

    today = datetime.date.today().isoformat()
    backup_dir = ROOT / ".backup" / f"rollup_{datetime.datetime.now():%Y%m%d_%H%M%S}"

    if pages is None:
        kinds = ["entities", "concepts"] if kind == "both" else [kind]
        pages = []
        for k in kinds:
            pages += sorted((WIKI / k).glob("*.md"))

    # Phase 1: select pages whose findings changed since their last rollup.
    todo: list[tuple[Path, str, list[str], str]] = []
    skipped = 0
    for path in pages:
        if limit and len(todo) >= limit:
            break
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        findings = non_stub_findings(text)
        if len(findings) < min_findings or not _SUMMARY_RE.search(text):
            skipped += 1
            continue
        fp = _rollup_fingerprint(text)
        if _stored_fp(text) == fp:  # summary already reflects these sources
            skipped += 1
            continue
        todo.append((path, text, findings, fp))

    # Phase 2: synthesise (the LLM-bound work) across a thread pool. The
    # genai_client rate-limiter bucket is thread-safe, so concurrent calls are
    # throttled correctly and back off together on 429s.
    done = failed = 0
    lock = threading.Lock()

    def process(item: tuple[Path, str, list[str], str]) -> None:
        nonlocal done, failed
        path, text, findings, fp = item
        h1 = _H1_RE.search(text)
        name = h1.group(1).strip() if h1 else path.stem
        category = "entity" if path.parent.name == "entities" else "concept"
        with lock:
            print(f"  [{'apply' if apply else 'dry '}] {path.relative_to(ROOT)}  ({len(findings)} findings)")
        if not apply:
            with lock:
                done += 1
            return
        try:
            new_summary = synthesise(name, category, findings, get_ai_response, model)
        except Exception as e:
            with lock:
                print(f"  [!] {path.name}: synthesis failed: {e}")
                failed += 1
            return
        if not new_summary:
            with lock:
                failed += 1
            return

        new_text = _SUMMARY_RE.sub(lambda m: m.group(1) + new_summary + m.group(3), text, count=1)
        new_text = re.sub(r"(date_updated:\s*)\S+", rf"\g<1>{today}", new_text, count=1)
        new_text = re.sub(r"(\*\*Last updated\*\*:\s*)\S+", rf"\g<1>{today}", new_text, count=1)
        new_text = _set_fp(new_text, fp)

        dest = backup_dir / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        path.write_text(new_text, encoding="utf-8")
        with lock:
            done += 1

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(process, todo))
    else:
        for item in todo:
            process(item)

    return {"done": done, "skipped": skipped, "failed": failed, "backup_dir": backup_dir}


def reindex_fingerprints(*, kind: str = "both", min_findings: int = 2,
                         apply: bool = False, pages: list[Path] | None = None) -> dict:
    """Stamp each qualifying page's CURRENT finding-fingerprint into frontmatter
    WITHOUT calling the LLM. Use once right after a full ``--apply`` so the
    just-synthesised pages are recognised as up-to-date and aren't redone.

    Only run this when you trust the on-page Summaries already reflect all
    findings (e.g. immediately after a full rollup), since it marks pages as
    current without verifying the Summary."""
    backup_dir = ROOT / ".backup" / f"reindex_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    if pages is None:
        kinds = ["entities", "concepts"] if kind == "both" else [kind]
        pages = []
        for k in kinds:
            pages += sorted((WIKI / k).glob("*.md"))

    stamped = skipped = 0
    for path in pages:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if len(non_stub_findings(text)) < min_findings or not _SUMMARY_RE.search(text):
            skipped += 1
            continue
        fp = _rollup_fingerprint(text)
        if _stored_fp(text) == fp:
            skipped += 1
            continue
        if apply:
            dest = backup_dir / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            path.write_text(_set_fp(text, fp), encoding="utf-8")
        stamped += 1

    return {"stamped": stamped, "skipped": skipped, "backup_dir": backup_dir}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kind", choices=["entities", "concepts", "both"], default="both")
    p.add_argument("--min-findings", type=int, default=2,
                   help="Only roll up pages with >= N non-stub findings (default 2).")
    p.add_argument("--limit", type=int, default=0, help="Process at most N pages (0 = all).")
    p.add_argument("--apply", action="store_true",
                   help="Write changes. Default is a dry-run preview.")
    p.add_argument("--workers", type=int, default=4,
                   help="Parallel synthesis workers (default 4; the genai rate-limiter is shared/thread-safe).")
    p.add_argument("--reindex", action="store_true",
                   help="Stamp current fingerprints WITHOUT calling the LLM (no re-synthesis). "
                        "Run once after a full --apply so freshly-synthesised pages aren't redone.")
    args = p.parse_args(argv)

    if args.reindex:
        r = reindex_fingerprints(kind=args.kind, min_findings=args.min_findings, apply=args.apply)
        verb = "Stamped" if args.apply else "Would stamp"
        print(f"\n{verb} {r['stamped']} pages; skipped {r['skipped']} (already current / too few findings).")
        if args.apply and r["stamped"]:
            print(f"Backups: {r['backup_dir']}")
        return 0

    r = run_rollup(kind=args.kind, min_findings=args.min_findings, limit=args.limit,
                   apply=args.apply, workers=args.workers)

    verb = "Updated" if args.apply else "Would update"
    print(f"\n{verb} {r['done']} pages; skipped {r['skipped']} (no new findings); failed {r['failed']}.")
    if args.apply and r["done"]:
        print(f"Backups: {r['backup_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
