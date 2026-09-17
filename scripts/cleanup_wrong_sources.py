"""cleanup_wrong_sources.py — bulk-fix the 947 wrong-`## Sources` pages.

The legacy ``_update_seed_page`` function in ``pdf_extractor.py`` (now patched)
appended new findings under a duplicate ``## Sources`` heading at the bottom
of seed pages, instead of merging them into the schema-correct
``**Sources**:`` list. It also dumped ``### Findings from [[paper]]`` blocks
under ``## Related pages``. This script restores schema compliance:

  1. Take the union of paper bullets from the top ``**Sources**:`` label and
     the bottom ``## Sources`` heading, deduplicated. Re-emit as the new
     top ``**Sources**:`` list.
  2. Move every ``### Findings from [[paper]]`` block out of
     ``## Related pages`` into the body proper, before the heading.
     Order is preserved.
  3. Legitimate non-source bullets that already lived under
     ``## Related pages`` are kept under the heading.
  4. The bottom ``## Sources`` heading and its bullets are removed.
  5. ``source_count`` in frontmatter is set to the deduped count.
  6. ``date_updated`` and ``**Last updated**:`` are bumped to today.

The transform was verified against ALL 947 affected files in dry-run before
this script was written: every file passes schema-validation, idempotency,
and strict paper/finding preservation checks. See
``scripts/verify_all_947.py`` for the verification harness.

Default mode is **dry-run** — nothing is written until ``--apply`` is passed.
When applying, every original is copied to a timestamped backup directory
**before** being overwritten, so the operation is reversible.
"""
from __future__ import annotations

import argparse
import datetime
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup so we can import lint helpers regardless of cwd.
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lint_wiki import (  # noqa: E402
    validate_page,
    check_source_link_in_related_pages,
    check_wrong_sources_heading,
)

WIKI = ROOT / "wiki"
SOURCES_DIR = WIKI / "sources"
BACKUP_ROOT = ROOT / ".backup" / "wrong_sources_cleanup"

SOURCE_STEMS: set[str] = (
    {p.stem for p in SOURCES_DIR.rglob("*.md")} if SOURCES_DIR.exists() else set()
)

# ---------------------------------------------------------------------------
# Pure transform — vetted by scripts/verify_all_947.py against every affected
# file. Do NOT modify without re-running that harness.
# ---------------------------------------------------------------------------
H2_RE = re.compile(r"^##\s+(\S.*?)\s*$")
BULLET_LINK_RE = re.compile(
    r"^\s*[-*]\s*\[\[\s*([^\]|#]+?)\s*(?:#[^\]|]*)?(?:\|[^\]]*)?\s*\]\]\s*$"
)
FINDINGS_H3_RE = re.compile(
    r"^###\s+Findings\s+from\s+\[\[([^\]]+)\]\]", re.IGNORECASE
)
SOURCES_LABEL_RE = re.compile(r"^\s*\*\*Sources\*\*\s*:\s*$")


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end < 0:
        return "", text
    return text[: end + 4], text[end + 4 :]


def _patch_frontmatter(fm: str, source_count: int, today_iso: str) -> str:
    fm = re.sub(
        r"^date_updated:.*$",
        f"date_updated: {today_iso}",
        fm,
        count=1,
        flags=re.MULTILINE,
    )
    if re.search(r"^source_count:", fm, re.MULTILINE):
        fm = re.sub(
            r"^source_count:\s*\d+",
            f"source_count: {source_count}",
            fm,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        fm = fm.rstrip() + f"\nsource_count: {source_count}\n"
    return fm


def cleanup_page(text: str, today_iso: str) -> tuple[str, dict]:
    """Apply the cleanup transform. Idempotent.

    Returns ``(new_text, audit_info)``. If the file has no ``## Sources``
    heading we return the input unchanged and the caller treats it as a
    no-op.
    """
    audit: dict = {
        "had_h2_sources": False,
        "merged_sources": [],
        "moved_findings": 0,
        "preserved_legit_bullets": 0,
    }
    if "\n## Sources" not in text and not text.startswith("## Sources"):
        return text, audit

    fm, body = _split_frontmatter(text)
    body_lines = body.splitlines()

    h2: dict[str, int] = {}
    for i, ln in enumerate(body_lines):
        m = H2_RE.match(ln)
        if m:
            t = m.group(1).strip().lower()
            h2.setdefault(t, i)

    related_idx = h2.get("related pages")
    sources_idx = h2.get("sources")
    if sources_idx is None:
        return text, audit
    audit["had_h2_sources"] = True

    label_idx = next(
        (i for i, ln in enumerate(body_lines) if SOURCES_LABEL_RE.match(ln)),
        None,
    )

    top_bullets: list[str] = []
    last_top_bullet_idx = label_idx
    if label_idx is not None:
        j = label_idx + 1
        while j < len(body_lines):
            ln = body_lines[j]
            m = BULLET_LINK_RE.match(ln)
            if m:
                top_bullets.append(m.group(1).strip())
                last_top_bullet_idx = j
                j += 1
            else:
                break

    next_h2_after_sources = len(body_lines)
    for i in range(sources_idx + 1, len(body_lines)):
        if H2_RE.match(body_lines[i]):
            next_h2_after_sources = i
            break

    # A findings heading is direct structural evidence that its target is
    # a paper source, even when the corresponding generated source page has
    # been moved or deleted since this cleanup script was imported.
    finding_source_stems = {
        match.group(1).strip()
        for line in body_lines
        if (match := FINDINGS_H3_RE.match(line))
    }
    bottom_paper_links: list[str] = []
    for ln in body_lines[sources_idx + 1 : next_h2_after_sources]:
        m = BULLET_LINK_RE.match(ln)
        if m:
            target = m.group(1).strip()
            if target in SOURCE_STEMS or target in finding_source_stems:
                bottom_paper_links.append(target)
            elif target not in bottom_paper_links and target not in top_bullets:
                # Conservative: refuse to silently drop unexpected content.
                raise RuntimeError(
                    f"Unexpected non-source bullet under ## Sources: [[{target}]]"
                )

    seen: dict[str, None] = {}
    for s in top_bullets + bottom_paper_links:
        seen.setdefault(s, None)
    merged_sources = list(seen.keys())
    audit["merged_sources"] = merged_sources

    legit_related_bullets: list[str] = []
    findings_lines: list[str] = []
    if related_idx is not None and related_idx < sources_idx:
        related_block = body_lines[related_idx + 1 : sources_idx]
        first_finding = next(
            (k for k, ln in enumerate(related_block) if FINDINGS_H3_RE.match(ln)),
            None,
        )
        if first_finding is None:
            legit_related_bullets = [
                ln for ln in related_block if BULLET_LINK_RE.match(ln)
            ]
        else:
            head_block = related_block[:first_finding]
            findings_block = related_block[first_finding:]
            legit_related_bullets = [
                ln for ln in head_block if BULLET_LINK_RE.match(ln)
            ]
            findings_lines = list(findings_block)
    audit["preserved_legit_bullets"] = len(legit_related_bullets)
    audit["moved_findings"] = sum(
        1 for ln in findings_lines if FINDINGS_H3_RE.match(ln)
    )

    while findings_lines and findings_lines[-1].strip() == "":
        findings_lines.pop()

    out: list[str] = []
    if label_idx is not None:
        out.extend(body_lines[: label_idx + 1])
    else:
        first_h2 = next(
            (i for i, ln in enumerate(body_lines) if H2_RE.match(ln)),
            len(body_lines),
        )
        out.extend(body_lines[:first_h2])
        out.append("**Sources**:")
        last_top_bullet_idx = len(out) - 1

    for stem in merged_sources:
        out.append(f"- [[{stem}]]")

    middle_start = (last_top_bullet_idx if last_top_bullet_idx is not None else len(out)) + 1
    middle_end = related_idx if related_idx is not None else next_h2_after_sources
    middle = body_lines[middle_start:middle_end]
    middle = [
        re.sub(r"(\*\*Last updated\*\*:\s*)\S+", lambda m: m.group(1) + today_iso, ln)
        for ln in middle
    ]
    while middle and middle[-1].strip() == "":
        middle.pop()
    if middle:
        out.append("")
        out.extend(middle)

    if findings_lines:
        out.append("")
        out.extend(findings_lines)

    if related_idx is not None:
        out.append("")
        out.append("## Related pages")
        for ln in legit_related_bullets:
            out.append(ln)

    tail = body_lines[next_h2_after_sources:]
    if tail:
        out.append("")
        out.extend(tail)

    new_body = "\n".join(out).rstrip() + "\n"
    new_fm = _patch_frontmatter(fm, source_count=len(merged_sources), today_iso=today_iso)
    if new_fm and not new_fm.endswith("\n"):
        new_fm += "\n"
    new_text = (new_fm + new_body) if new_fm else new_body
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    if not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, audit


# ---------------------------------------------------------------------------
# Per-file safety gates — re-run on each file before we write to disk.
# ---------------------------------------------------------------------------
def _strict_paper_preservation(original: str, new_text: str) -> list[str]:
    """Return the list of paper stems that were in the ORIGINAL (under either
    the top ``**Sources**:`` block or the bottom ``## Sources`` block) but
    are NOT present as bullets in ``new_text``."""
    orig_papers: set[str] = set()
    in_top, in_bot = False, False
    for ln in original.splitlines():
        if SOURCES_LABEL_RE.match(ln):
            in_top, in_bot = True, False
            continue
        h2m = H2_RE.match(ln)
        if h2m:
            t = h2m.group(1).strip().lower()
            in_top = False
            in_bot = (t == "sources")
            continue
        if in_top or in_bot:
            m = BULLET_LINK_RE.match(ln)
            if m and m.group(1).strip() in SOURCE_STEMS:
                orig_papers.add(m.group(1).strip())
            elif ln.strip() == "" and in_top:
                in_top = False
    return [p for p in orig_papers if f"- [[{p}]]" not in new_text]


def _strict_finding_preservation(original: str, new_text: str) -> tuple[int, int]:
    pat = re.compile(r"^###\s+Findings\s+from\s+\[\[([^\]]+)\]\]", re.MULTILINE)
    return (len(pat.findall(original)), len(pat.findall(new_text)))


def safety_gate(original: str, new_text: str, today_iso: str) -> list[str]:
    """All-or-nothing: returns an empty list if every gate passes."""
    problems: list[str] = []
    if check_wrong_sources_heading(new_text):
        problems.append("still has '## Sources' heading after cleanup")
    fmt_errs = validate_page(new_text)
    if fmt_errs:
        problems.append(f"format errors: {fmt_errs}")
    sl = check_source_link_in_related_pages(new_text, SOURCE_STEMS)
    if sl:
        problems.append(f"source link in related pages: {sl}")
    again, _ = cleanup_page(new_text, today_iso=today_iso)
    if again != new_text:
        problems.append("transform NOT idempotent")
    lost = _strict_paper_preservation(original, new_text)
    if lost:
        problems.append(f"lost source papers: {lost}")
    o, n = _strict_finding_preservation(original, new_text)
    if o != n:
        problems.append(f"finding count changed: {o} -> {n}")
    return problems


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def discover_targets() -> list[Path]:
    """Walk wiki/ outside wiki/sources/ and return every .md file that still
    contains a ``## Sources`` heading. Re-discovered each run so we never
    rely on a stale list."""
    out: list[Path] = []
    for f in WIKI.rglob("*.md"):
        try:
            f.relative_to(SOURCES_DIR)
            continue
        except ValueError:
            pass
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if line.strip().lower() == "## sources":
                out.append(f)
                break
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Actually write changes (default: dry-run)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N files (canary)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-file output")
    args = parser.parse_args()

    today = datetime.date.today().isoformat()
    targets = discover_targets()
    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("No files contain a '## Sources' heading. Nothing to do.")
        return 0

    print(f"Targets: {len(targets)} files")
    if args.apply:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = BACKUP_ROOT / ts
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"Backups → {backup_dir.relative_to(ROOT)}")
    else:
        print("(dry-run — pass --apply to write)")
        backup_dir = None

    rewritten = 0
    skipped: list[tuple[Path, list[str]]] = []
    audit_totals = Counter()
    audit_findings = 0
    audit_legit = 0

    for path in targets:
        try:
            original = path.read_text(encoding="utf-8")
        except OSError as e:
            skipped.append((path, [f"read error: {e}"]))
            continue
        try:
            new_text, audit = cleanup_page(original, today_iso=today)
        except Exception as e:
            skipped.append((path, [f"transform raised: {e!r}"]))
            continue
        if new_text == original:
            continue  # nothing to do

        problems = safety_gate(original, new_text, today_iso=today)
        if problems:
            skipped.append((path, problems))
            continue

        if not args.quiet:
            rel = path.relative_to(ROOT).as_posix()
            print(f"  {rel}  "
                  f"(merged {len(audit['merged_sources'])} src, "
                  f"moved {audit['moved_findings']} findings, "
                  f"kept {audit['preserved_legit_bullets']} bullets)")

        if args.apply:
            assert backup_dir is not None
            rel_under_root = path.relative_to(ROOT)
            backup_path = backup_dir / rel_under_root
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path)
            path.write_text(new_text, encoding="utf-8")

        rewritten += 1
        audit_totals["merged_sources"] += len(audit["merged_sources"])
        audit_findings += audit["moved_findings"]
        audit_legit += audit["preserved_legit_bullets"]

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print()
    print(f"[{mode}] processed {len(targets)} files")
    print(f"[{mode}] rewritten          : {rewritten}")
    print(f"[{mode}] sources merged     : {audit_totals['merged_sources']}")
    print(f"[{mode}] findings relocated : {audit_findings}")
    print(f"[{mode}] legit bullets kept : {audit_legit}")
    print(f"[{mode}] skipped (gates)    : {len(skipped)}")
    for p, reasons in skipped[:10]:
        print(f"    {p.relative_to(ROOT)}")
        for r in reasons:
            print(f"      - {r}")
    if len(skipped) > 10:
        print(f"    … {len(skipped) - 10} more skips")

    if args.apply and rewritten:
        print("\nRunning lint_wiki.py to confirm the structural fix landed…")
        subprocess.run(
            [sys.executable, "lint_wiki.py"],
            cwd=ROOT,
            check=False,
        )
        # Re-grep the lint report for the bug pattern.
        report = (ROOT / "wiki_lint_report.md").read_text(encoding="utf-8")
        m = re.search(r"Uses '## Sources' heading.*?: (\d+)", report)
        if m:
            print(f"Post-fix '## Sources' count in lint report: {m.group(1)}")
        else:
            print("Post-fix '## Sources' issue NOT present in lint report (good).")

    return 0 if not skipped else 1


if __name__ == "__main__":
    sys.exit(main())
