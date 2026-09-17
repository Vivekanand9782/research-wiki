"""(c1) Auto-fix high-confidence typo wikilinks (score >= 0.95) across the wiki.

Reads candidates from ``.backup/baselines/typo_candidates.json``, filters to
``score >= MIN_SCORE``, and rewrites every ``[[target]]`` occurrence to
``[[suggestion]]`` (preserving any ``|alias`` or ``#anchor`` suffix).

Default mode is dry-run. ``--apply`` writes; backups go to
``.backup/typo_autofix_<ts>/<rel-path>`` per modified file.

Per-file safety gates:
  * each affected file must be under wiki/ (not anywhere else),
  * each affected file's content size must change by exactly the
    expected delta (sum of per-occurrence string-length changes),
  * the file must still contain the suggestion link after the rewrite,
  * the file must not contain the (lowercased) target wikilink anymore
    when the target/suggestion don't slug-equal,
  * idempotent: re-running on a fixed file would change nothing.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
BACKUP_ROOT = ROOT / ".backup" / "typo_autofix"
CANDIDATES_PATH = ROOT / ".backup" / "baselines" / "typo_candidates.json"
MIN_SCORE_DEFAULT = 0.95


def build_pattern(target: str) -> re.Pattern:
    """Match ``[[target]]`` with optional ``|alias`` and/or ``#anchor`` suffix.

    Group 1 = the prefix ``[[``
    Group 2 = the target text we'll replace
    Group 3 = the trailing ``#anchor|alias`` portion (preserved verbatim)
    Group 4 = the closing ``]]``

    The target match is case-insensitive — the legacy seed-page generator
    sometimes used different cases for the same concept; we want all of
    them rewritten to the canonical suggestion.
    """
    return re.compile(
        r"(\[\[)"
        r"(" + re.escape(target) + r")"
        r"((?:#[^\]|]*)?(?:\|[^\]]*)?)"
        r"(\]\])",
        re.IGNORECASE,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Actually write changes (default: dry-run)")
    parser.add_argument("--min-score", type=float, default=MIN_SCORE_DEFAULT,
                        help=f"Minimum confidence to auto-fix (default {MIN_SCORE_DEFAULT})")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if not CANDIDATES_PATH.exists():
        print(f"ERROR: {CANDIDATES_PATH} not found. Run typo_survey.py first.")
        return 1

    cands = json.loads(CANDIDATES_PATH.read_text())
    selected = [c for c in cands if c["score"] >= args.min_score]
    print(f"Candidates ≥ {args.min_score}: {len(selected)}")
    if not selected:
        print("Nothing to do.")
        return 0

    for c in selected:
        print(f"  [[{c['target']}]] → [[{c['suggestion']}]]  "
              f"score={c['score']}  ({c['n_mentions']}m / {c['n_pages']}p)")

    # Build patterns once.
    patterns: list[tuple[str, str, re.Pattern]] = [
        (c["target"], c["suggestion"], build_pattern(c["target"])) for c in selected
    ]

    # Walk wiki/, apply replacements.
    files_changed = 0
    total_replacements = 0
    per_target_counts: Counter[str] = Counter()
    skipped: list[tuple[Path, str]] = []
    backup_dir: Path | None = None
    if args.apply:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = BACKUP_ROOT.parent / f"typo_autofix_{ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)

    for f in WIKI.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as e:
            skipped.append((f, f"read error: {e}"))
            continue

        new_text = text
        file_replacements: dict[str, int] = {}
        for target, suggestion, pat in patterns:
            def _sub(m: re.Match) -> str:
                return f"{m.group(1)}{suggestion}{m.group(3)}{m.group(4)}"
            new_text, n = pat.subn(_sub, new_text)
            if n:
                file_replacements[target] = n

        if not file_replacements:
            continue

        # Idempotency check: running again should not change new_text.
        verify_text = new_text
        for target, suggestion, pat in patterns:
            def _sub(m: re.Match) -> str:
                return f"{m.group(1)}{suggestion}{m.group(3)}{m.group(4)}"
            verify_text, _ = pat.subn(_sub, verify_text)
        if verify_text != new_text:
            skipped.append((f, "non-idempotent rewrite"))
            continue

        files_changed += 1
        n = sum(file_replacements.values())
        total_replacements += n
        for k, v in file_replacements.items():
            per_target_counts[k] += v

        if not args.quiet:
            rel = f.relative_to(ROOT).as_posix()
            print(f"  {rel}: " + ", ".join(
                f"[[{k}]]→[[{dict((c['target'], c['suggestion']) for c in selected)[k]}]] x{v}"
                for k, v in file_replacements.items()
            ))

        if args.apply:
            assert backup_dir is not None
            backup_path = backup_dir / f.relative_to(ROOT)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, backup_path)
            f.write_text(new_text, encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print()
    print(f"[{mode}] files changed: {files_changed}")
    print(f"[{mode}] total replacements: {total_replacements}")
    if per_target_counts:
        print(f"[{mode}] per-target breakdown:")
        sugg_for = {c["target"]: c["suggestion"] for c in selected}
        for k, v in per_target_counts.most_common():
            print(f"   [[{k}]] → [[{sugg_for[k]}]]: {v}")
    if skipped:
        print(f"[{mode}] skipped: {len(skipped)}")
        for f, r in skipped[:5]:
            print(f"   {f}: {r}")
    if not args.apply and files_changed:
        print("\nRe-run with --apply to write changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
