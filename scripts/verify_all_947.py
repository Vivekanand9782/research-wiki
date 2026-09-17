"""Run the cleanup transform across ALL 947 candidate files in dry-run mode
and verify each one passes every safety gate. Prints aggregate stats and
the first few failures (if any). Writes nothing.
"""
from __future__ import annotations

import datetime
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from cleanup_wrong_sources_dryrun import (
    cleanup_page,
    SOURCE_STEMS,
    BULLET_LINK_RE,
    SOURCES_LABEL_RE,
    H2_RE,
)
from lint_wiki import (
    validate_page,
    check_source_link_in_related_pages,
    check_wrong_sources_heading,
)

PATHS = [
    Path(p) for p in
    Path("/tmp/wrong_sources_files.txt").read_text().splitlines() if p.strip()
]

today = datetime.date.today().isoformat()
fail: list[tuple[Path, list[str]]] = []
audit_totals = Counter()
audit_findings = 0
audit_legit = 0

for p in PATHS:
    try:
        original = p.read_text(encoding="utf-8")
        new_text, audit = cleanup_page(original, today_iso=today)
    except Exception as e:
        fail.append((p, [f"EXCEPTION: {e!r}"]))
        continue

    problems: list[str] = []
    if check_wrong_sources_heading(new_text):
        problems.append("still has '## Sources' heading")
    fmt_errs = validate_page(new_text)
    if fmt_errs:
        problems.append(f"format errors: {fmt_errs}")
    sl = check_source_link_in_related_pages(new_text, SOURCE_STEMS)
    if sl:
        problems.append(f"source link in related: {sl}")
    again, _ = cleanup_page(new_text, today_iso=today)
    if again != new_text:
        problems.append("transform NOT idempotent")

    # Strict source preservation
    orig_papers: set[str] = set()
    in_top, in_bot = False, False
    for ln in original.splitlines():
        if SOURCES_LABEL_RE.match(ln):
            in_top, in_bot = True, False
            continue
        h2m = H2_RE.match(ln)
        if h2m:
            title = h2m.group(1).strip().lower()
            in_top = False
            in_bot = (title == "sources")
            continue
        if in_top or in_bot:
            m = BULLET_LINK_RE.match(ln)
            if m and m.group(1).strip() in SOURCE_STEMS:
                orig_papers.add(m.group(1).strip())
            elif ln.strip() == "" and in_top:
                in_top = False
    for stem in orig_papers:
        if f"- [[{stem}]]" not in new_text:
            problems.append(f"lost [[{stem}]]")

    # Findings preservation
    orig_findings = re.findall(
        r"^###\s+Findings\s+from\s+\[\[([^\]]+)\]\]",
        original, re.MULTILINE,
    )
    new_findings = re.findall(
        r"^###\s+Findings\s+from\s+\[\[([^\]]+)\]\]",
        new_text, re.MULTILINE,
    )
    if sorted(orig_findings) != sorted(new_findings):
        problems.append(
            f"findings mismatch: {len(orig_findings)} → {len(new_findings)}"
        )

    if problems:
        fail.append((p, problems))
    else:
        audit_totals["files_ok"] += 1
        audit_totals["sources_merged"] += len(audit["merged_sources"])
        audit_findings += audit["moved_findings"]
        audit_legit += audit["preserved_legit_bullets"]

print(f"Dry-ran {len(PATHS)} files")
print(f"  passed all safety gates : {audit_totals['files_ok']}")
print(f"  failed                  : {len(fail)}")
print(f"  total sources merged    : {audit_totals['sources_merged']}")
print(f"  total findings moved    : {audit_findings}")
print(f"  total legit bullets kept: {audit_legit}")

if fail:
    print(f"\nFirst 10 failures:")
    for p, problems in fail[:10]:
        print(f"  {p}:")
        for pr in problems:
            print(f"    - {pr}")
    sys.exit(1)
else:
    print("\nALL 947 FILES PASS — transform is safe to apply.")
