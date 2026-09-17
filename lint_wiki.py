import sys
import re
import datetime
import shutil
from pathlib import Path

try:
    import yaml  # used for parsing aliases when present
except ImportError:
    yaml = None

WIKILINK_RE = re.compile(r'\[\[(.*?)\]\]')
REQUIRED_FRONTMATTER = ['tags:', 'type:', 'date_created:', 'date_updated:']
REQUIRED_SECTIONS = ['**Summary**:', '**Sources**:', '**Last updated**:', '## Related pages']

BACKUP_DIR = Path(__file__).resolve().parent / '.backup'


def _link_slug(name: str) -> str:
    """Mirror the seed-page generator's slugify rule:
    non-alnum runs become a single dash, lowercased, with leading/trailing
    dashes stripped. Used to detect case/punctuation-only link mismatches
    that Obsidian resolves automatically (e.g. ``[[Zea mays]]`` ↔ ``zea-mays.md``)."""
    return re.sub(r'[^a-zA-Z0-9]+', '-', name).strip('-').lower()

# --- Section / line patterns used by the deterministic structural checks ----
RELATED_HEADING_RE = re.compile(r'^\s*##\s+Related\s+pages\s*$', re.IGNORECASE | re.MULTILINE)
SOURCES_HEADING_RE = re.compile(r'^\s*##\s+Sources\s*$', re.IGNORECASE)
NEXT_HEADING_RE = re.compile(r'^\s*##\s+\S')
BULLET_LINK_RE = re.compile(
    r'^\s*[-*]\s*\[\[\s*([^\]|#]+?)\s*(?:#[^\]|]*)?(?:\|[^\]]*)?s*\]\]\s*$'
)


def extract_frontmatter(content: str) -> str | None:
    """Returns frontmatter body or None if not well-formed."""
    if not content.startswith('---'):
        return None
    end = content.find('\n---', 3)  # must be on its own line
    if end == -1:
        return None
    return content[3:end]


def extract_aliases(content: str) -> list[str]:
    """Return the YAML 'aliases' list from frontmatter, or [] if absent/unparseable."""
    fm = extract_frontmatter(content)
    if fm is None or yaml is None:
        return []
    try:
        data = yaml.safe_load(fm) or {}
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    aliases = data.get('aliases')
    if isinstance(aliases, str):
        return [aliases]
    if isinstance(aliases, list):
        return [a for a in aliases if isinstance(a, str)]
    return []

def _has_frontmatter_field(fm: str, field: str) -> bool:
    """Check if a frontmatter field exists at the start of a line, avoiding substring matches."""
    return bool(re.search(rf'^{re.escape(field)}\s', fm, re.MULTILINE))

def validate_page(content: str) -> list[str]:
    errors = []
    fm = extract_frontmatter(content)
    if fm is None:
        errors.append("Missing or unclosed YAML frontmatter")
    else:
        for field in REQUIRED_FRONTMATTER:
            if not _has_frontmatter_field(fm, field):
                errors.append(f"Missing '{field}' in frontmatter")

    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing '{section}' section")

    return errors


def _frontmatter_field(fm: str | None, key: str) -> str | None:
    """Return the (single-line) value of a frontmatter key, or None."""
    if not fm:
        return None
    m = re.search(rf'^{re.escape(key)}\s*:\s*(.+?)\s*$', fm, re.MULTILINE)
    return m.group(1).strip().strip('"').strip("'") if m else None


# Looser schemas for non-seed page types. Seed pages (concept/entity) use the
# strict REQUIRED_FRONTMATTER + REQUIRED_SECTIONS lists above.
SOURCE_REQUIRED_FRONTMATTER = ['type:', 'date_created:']
SOURCE_REQUIRED_SECTIONS = ['Title & Metadata']
SOURCE_ABSTRACT_SECTIONS = ('Abstract Summary', 'Abstract', 'Correction Summary')
SYNTHESIS_REQUIRED_FRONTMATTER = ['type:', 'date_created:']
SYNTHESIS_REQUIRED_SECTIONS: list[str] = []  # free-form sectioning allowed


def validate_source_page(content: str) -> list[str]:
    """Looser schema for ``wiki/sources/`` pages — they use the 12-section
    paper-summary format produced by ``pdf_extractor.py``, not the seed-page
    schema. We require frontmatter and the two non-negotiable sections
    (Title & Metadata, Abstract); the rest is enforced by pdf_extractor."""
    errors = []
    fm = extract_frontmatter(content)
    if fm is None:
        errors.append("Missing or unclosed YAML frontmatter")
    else:
        for field in SOURCE_REQUIRED_FRONTMATTER:
            if not _has_frontmatter_field(fm, field):
                errors.append(f"Missing '{field}' in frontmatter")
    for section in SOURCE_REQUIRED_SECTIONS:
        if re.search(rf"(?im)^##\s+{re.escape(section)}\s*$", content) is None:
            errors.append(f"Missing '## {section}' section")
    if not any(
        re.search(rf"(?im)^##\s+{re.escape(section)}\s*$", content)
        for section in SOURCE_ABSTRACT_SECTIONS
    ):
        errors.append("Missing abstract or correction-summary section")
    return errors


def validate_synthesis_page(content: str) -> list[str]:
    """Lighter schema for ``type: synthesis`` pages (long-form essays,
    auto-generated indexes). They need frontmatter and an H1; sectioning
    is intentionally free-form."""
    errors = []
    fm = extract_frontmatter(content)
    if fm is None:
        errors.append("Missing or unclosed YAML frontmatter")
    else:
        for field in SYNTHESIS_REQUIRED_FRONTMATTER:
            if not _has_frontmatter_field(fm, field):
                errors.append(f"Missing '{field}' in frontmatter")
    if not re.search(r'^#\s+\S', content, re.MULTILINE):
        errors.append("Missing H1 title")
    return errors


def page_kind(filepath: Path, content: str) -> str:
    """Classify a page into one of: ``source``, ``synthesis``, ``seed``.

    Path-first detection (``wiki/sources/`` is canonical), falling back to
    the ``type:`` field in YAML frontmatter.
    """
    parts = filepath.parts
    if 'sources' in parts:
        idx = parts.index('sources')
        if idx > 0 and parts[idx - 1] == 'wiki':
            return 'source'
    fm = extract_frontmatter(content)
    t = _frontmatter_field(fm, 'type')
    if t == 'source':
        return 'source'
    if t == 'synthesis':
        return 'synthesis'
    return 'seed'


def validate_for_kind(kind: str, content: str) -> list[str]:
    if kind == 'source':
        return validate_source_page(content)
    if kind == 'synthesis':
        return validate_synthesis_page(content)
    return validate_page(content)


def _strip_frontmatter_and_first_heading(content: str) -> str:
    """Remove YAML frontmatter and the leading H1 so body checks don't trip on them."""
    if content.startswith('---'):
        end = content.find('\n---', 3)
        if end != -1:
            content = content[end + 4:]
    # Drop the leading "# Title" line if present.
    content = re.sub(r'^\s*#\s+[^\n]*\n+', '', content, count=1)
    return content


def _related_pages_block(content: str) -> tuple[int, int] | None:
    """Return (start_line_idx, end_line_idx_exclusive) of the ``## Related pages``
    section, or None if absent."""
    lines = content.splitlines()
    start = None
    for i, line in enumerate(lines):
        if RELATED_HEADING_RE.match(line):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if NEXT_HEADING_RE.match(lines[j]):
            end = j
            break
    return (start, end)


def check_source_link_in_related_pages(content: str, source_stems: set[str]) -> list[str]:
    """Bullets under ``## Related pages`` whose target is a source paper."""
    block = _related_pages_block(content)
    if block is None:
        return []
    start, end = block
    lines = content.splitlines()
    misplaced: list[str] = []
    for line in lines[start + 1:end]:
        m = BULLET_LINK_RE.match(line)
        if m and m.group(1).strip() in source_stems:
            misplaced.append(m.group(1).strip())
    if misplaced:
        return [
            f"Source-paper wikilink in '## Related pages': [[{stem}]] "
            f"(belongs in '**Sources**:' instead)"
            for stem in misplaced
        ]
    return []


def check_empty_related_pages(content: str) -> list[str]:
    """``## Related pages`` heading with no bullet content under it."""
    block = _related_pages_block(content)
    if block is None:
        return []
    start, end = block
    lines = content.splitlines()
    for line in lines[start + 1:end]:
        if BULLET_LINK_RE.match(line):
            return []
    return ["'## Related pages' section is empty"]


def check_wrong_sources_heading(content: str) -> list[str]:
    """Catches `## Sources` (heading) used instead of `**Sources**:` (bold label)."""
    for line in content.splitlines():
        if SOURCES_HEADING_RE.match(line):
            return [
                "Uses '## Sources' heading instead of the schema's '**Sources**:' label "
                "(creates a duplicate sources section)"
            ]
    return []


def check_unsourced_body_paragraphs(content: str) -> list[str]:
    """Flag body paragraphs that contain no ``[[wikilink]]`` citations.

    Heuristic: split the body (after frontmatter / H1) into paragraphs.
    Skip paragraphs that:
      * are headings, list markers, or empty,
      * are part of the ``**Summary**:`` / ``**Sources**:`` / ``**Last updated**:``
        metadata block (the schema doesn't require citations there),
      * already contain at least one ``[[...]]`` wikilink.
    Return one finding per offending paragraph (capped to 3 to avoid noise).
    """
    body = _strip_frontmatter_and_first_heading(content)
    # Drop everything from the ``## Related pages`` heading onward — it's a
    # link list, not prose.
    body = re.split(r'(?im)^\s*##\s+Related\s+pages\s*$', body, maxsplit=1)[0]

    paragraphs = re.split(r'\n\s*\n', body)
    findings: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Skip schema-metadata blocks (they own their own citations elsewhere).
        if para.startswith(('**Summary**', '**Sources**', '**Last updated**')):
            continue
        # Skip pure heading paragraphs.
        if all(line.lstrip().startswith('#') for line in para.splitlines() if line.strip()):
            continue
        # Skip horizontal rules.
        if re.fullmatch(r'-{3,}', para):
            continue
        # Skip pure bullet lists (links/short labels — checked elsewhere).
        non_blank = [line for line in para.splitlines() if line.strip()]
        if non_blank and all(re.match(r'^\s*[-*]\s', line) for line in non_blank):
            continue
        if WIKILINK_RE.search(para):
            continue
        # Build a short identifying snippet.
        snippet = re.sub(r'\s+', ' ', para)[:80]
        findings.append(f"Unsourced body paragraph: \"{snippet}…\"")
        if len(findings) >= 3:
            break
    return findings


def classify_page_findings(
    content: str, *, is_source: bool, source_stems: set[str]
) -> tuple[list[str], list[str]]:
    """Return ``(structural_errors, content_debt)`` for one wiki page.

    Structural errors are deterministic schema or placement defects that can
    make tooling interpret a page incorrectly. Content debt is valid but
    incomplete material that benefits from later, source-grounded curation.
    Keeping these categories separate prevents generated stubs from masking
    genuine regressions or making the read-only linter fail every run.
    """
    structural = check_wrong_sources_heading(content)
    debt: list[str] = []
    if not is_source:
        structural.extend(
            check_source_link_in_related_pages(content, source_stems)
        )
        debt.extend(check_empty_related_pages(content))
        debt.extend(check_unsourced_body_paragraphs(content))
    return structural, debt


def _write_findings_report(
    output, *, heading: str, findings: dict[Path, list[str]], intro: str
) -> None:
    """Write one deterministic finding category to the lint report."""
    output.write(f"\n{heading}\n")
    if not findings:
        output.write("None found. Great!\n")
        return

    output.write(intro + "\n\n")
    tally: dict[str, int] = {}
    for errors in findings.values():
        for error in errors:
            key = error.split(':', 1)[0]
            tally[key] = tally.get(key, 0) + 1
    output.write("**Issue counts:**\n\n")
    for key, count in sorted(tally.items(), key=lambda item: -item[1]):
        output.write(f"- {key}: {count}\n")
    output.write("\n**Per-file breakdown:**\n\n")
    for filepath in sorted(findings, key=lambda path: path.as_posix()):
        output.write(f"- `{filepath.as_posix()}`\n")
        for error in findings[filepath]:
            output.write(f"  - {error}\n")


# ---------------------------------------------------------------------------
# Auto-repair engine
# ---------------------------------------------------------------------------

def _backup_file(filepath: Path) -> None:
    """Create a collision-safe timestamped backup before modifying a page."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    relative = filepath.relative_to(Path(__file__).resolve().parent / "wiki")
    safe_name = "__".join(relative.with_suffix("").parts)
    dest = BACKUP_DIR / f"{safe_name}_{ts}.md"
    shutil.copy2(filepath, dest)


def _infer_page_type(filepath: Path) -> str:
    """Infer page type from directory structure."""
    parts = filepath.parts
    if 'entities' in parts:
        return 'entity'
    if 'concepts' in parts:
        return 'concept'
    if 'sources' in parts:
        return 'source'
    if 'synthesis' in parts:
        return 'synthesis'
    return 'entity'


def autofix_page(filepath: Path, content: str, kind: str) -> tuple[str, list[str]]:
    """Apply deterministic structural repairs to a seed page.

    Returns (new_content, list_of_repairs_applied).
    Only applies to seed pages (entities/concepts). Source and synthesis pages
    use different schemas and are not auto-repaired.
    """
    if kind != 'seed':
        return content, []

    repairs: list[str] = []
    today = datetime.date.today().isoformat()
    page_type = _infer_page_type(filepath)
    page_name = filepath.stem

    # ── Fix 1: Missing or unclosed YAML frontmatter ──
    fm = extract_frontmatter(content)
    if fm is None:
        # No frontmatter at all — prepend a complete block
        frontmatter = (
            f"---\n"
            f"tags: [{page_type}]\n"
            f"type: {page_type}\n"
            f"date_created: {today}\n"
            f"date_updated: {today}\n"
            f"---\n\n"
        )
        content = frontmatter + content
        repairs.append("Added missing YAML frontmatter")
        fm = extract_frontmatter(content)  # re-parse for subsequent fixes

    # ── Fix 2: Missing frontmatter fields ──
    if fm is not None:
        field_defaults = {
            'tags:': f'tags: [{page_type}]',
            'type:': f'type: {page_type}',
            'date_created:': f'date_created: {today}',
            'date_updated:': f'date_updated: {today}',
        }
        for field, default_line in field_defaults.items():
            if not _has_frontmatter_field(fm, field):
                # Insert before the closing ---
                content = content.replace('\n---', f'\n{default_line}\n---', 1)
                repairs.append(f"Added missing '{field}' to frontmatter")
                fm = extract_frontmatter(content)  # re-parse

    # ── Fix 3: Missing **Summary**: section ──
    if '**Summary**:' not in content:
        # Insert after the H1 heading (or after frontmatter if no H1)
        h1_match = re.search(r'^#\s+.+$', content, re.MULTILINE)
        if h1_match:
            insert_pos = h1_match.end()
            content = content[:insert_pos] + '\n\n**Summary**:\n_No summary yet._\n' + content[insert_pos:]
        else:
            # Append after frontmatter closing ---
            end_fm = content.find('\n---', 3)
            if end_fm != -1:
                insert_pos = end_fm + 4
                content = content[:insert_pos] + f'\n\n# {page_name}\n\n**Summary**:\n_No summary yet._\n' + content[insert_pos:]
        repairs.append("Added missing '**Summary**:' section")

    # ── Fix 4: Missing **Sources**: section ──
    if '**Sources**:' not in content:
        # Insert after **Summary** block (find next blank line after summary)
        summary_match = re.search(r'\*\*Summary\*\*:', content)
        if summary_match:
            # Find the next double newline after summary
            rest = content[summary_match.start():]
            double_nl = rest.find('\n\n')
            if double_nl != -1:
                insert_pos = summary_match.start() + double_nl
                content = content[:insert_pos] + '\n\n**Sources**:\n_None yet._\n' + content[insert_pos:]
            else:
                content += '\n\n**Sources**:\n_None yet._\n'
        else:
            content += '\n\n**Sources**:\n_None yet._\n'
        repairs.append("Added missing '**Sources**:' section")

    # ── Fix 5: Missing **Last updated**: section ──
    if '**Last updated**:' not in content:
        # Insert after **Sources** block
        sources_match = re.search(r'\*\*Sources\*\*:', content)
        if sources_match:
            rest = content[sources_match.start():]
            double_nl = rest.find('\n\n')
            if double_nl != -1:
                insert_pos = sources_match.start() + double_nl
                content = content[:insert_pos] + f'\n\n**Last updated**: {today}\n' + content[insert_pos:]
            else:
                content += f'\n\n**Last updated**: {today}\n'
        else:
            content += f'\n\n**Last updated**: {today}\n'
        repairs.append("Added missing '**Last updated**:' section")

    # ── Fix 6: Missing ## Related pages section ──
    if not RELATED_HEADING_RE.search(content):
        # Append at the end of the file
        content = content.rstrip('\n') + '\n\n## Related pages\n'
        repairs.append("Added missing '## Related pages' section")

    # ── Fix 7: ## Sources heading → **Sources**: ──
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if SOURCES_HEADING_RE.match(line):
            new_lines.append('**Sources**:')
            repairs.append("Fixed '## Sources' heading → '**Sources**:' label")
        else:
            new_lines.append(line)
    if repairs and repairs[-1].startswith("Fixed '## Sources'"):
        content = '\n'.join(new_lines)

    # ── Fix 8: Deduplicate ## Related pages headings ──
    lines = content.splitlines()
    related_indices = [i for i, line in enumerate(lines) if RELATED_HEADING_RE.match(line)]
    if len(related_indices) > 1:
        # Keep the first occurrence, remove all subsequent ones
        to_remove = set(related_indices[1:])
        content = '\n'.join(line for i, line in enumerate(lines) if i not in to_remove)
        repairs.append(f"Removed {len(to_remove)} duplicate '## Related pages' heading(s)")

    return content, repairs


def lint_wiki(fix: bool = False):
    # Use absolute path relative to this script to ensure it works regardless of CWD
    script_dir = Path(__file__).resolve().parent
    wiki_dir = script_dir / 'wiki'
    md_files = list(wiki_dir.rglob('*.md'))
    special_files = {wiki_dir / 'index.md', wiki_dir / 'log.md'}

    file_contents: dict[Path, str] = {}

    # Read each file only once
    for f in md_files:
        try:
            with open(f, encoding='utf-8') as fh:
                file_contents[f] = fh.read()
        except OSError as e:
            print(f"Warning: could not read {f}: {e}")

    # Build the set of stems for everything under ``wiki/sources/`` so we can
    # detect source-paper wikilinks that have leaked into ``## Related pages``.
    sources_dir = wiki_dir / 'sources'
    source_stems: set[str] = set()
    for f in file_contents:
        try:
            f.relative_to(sources_dir)
            source_stems.add(f.stem)
        except ValueError:
            continue

    # ── Auto-repair pass (before validation, so repaired pages pass cleanly) ──
    total_repaired = 0
    all_repairs: dict[Path, list[str]] = {}

    if fix:
        for filepath, content in list(file_contents.items()):
            if filepath in special_files:
                continue
            kind = page_kind(filepath, content)
            new_content, repairs = autofix_page(filepath, content, kind)
            if repairs and new_content != content:
                _backup_file(filepath)
                filepath.write_text(new_content, encoding='utf-8')
                file_contents[filepath] = new_content  # update in-memory copy
                all_repairs[filepath] = repairs
                total_repaired += 1

        if total_repaired:
            print(f"  🔧 Auto-repaired {total_repaired} pages ({sum(len(r) for r in all_repairs.values())} fixes applied, backups in .backup/)")
        else:
            print(f"  ✓ No auto-repairable issues found.")

    # Build all_pages set with bare names, relative paths, AND YAML aliases.
    # We also build a parallel set of slug-normalized names so we can detect
    # case/punctuation-only mismatches that Obsidian resolves automatically.
    all_pages = set()
    all_pages_normalized: set[str] = set()
    for f, content in file_contents.items():
        page_name = f.stem  # e.g. "foo" from "foo.md"
        rel_path = f.relative_to(wiki_dir).with_suffix('').as_posix()  # e.g. "concepts/foo"
        all_pages.add(page_name)
        all_pages.add(rel_path)
        all_pages_normalized.add(_link_slug(page_name))
        all_pages_normalized.add(_link_slug(rel_path))
        for alias in extract_aliases(content):
            all_pages.add(alias)
            all_pages_normalized.add(_link_slug(alias))

    format_errors: dict[Path, list[str]] = {}
    structural_errors: dict[Path, list[str]] = {}
    content_debt: dict[Path, list[str]] = {}
    broken_links = set()
    links_to: dict[str, set[Path]] = {}

    for filepath, content in file_contents.items():
        is_special = filepath in special_files
        try:
            filepath.relative_to(sources_dir)
            is_source = True
        except ValueError:
            is_source = False

        if not is_special:
            kind = page_kind(filepath, content)
            errors = validate_for_kind(kind, content)
            if errors:
                format_errors[filepath] = errors

            # Separate actionable schema/placement defects from advisory
            # incompleteness so stub debt does not hide real regressions.
            page_structural, page_debt = classify_page_findings(
                content, is_source=is_source, source_stems=source_stems
            )
            if page_structural:
                structural_errors[filepath] = page_structural
            if page_debt:
                content_debt[filepath] = page_debt

        # Extract links
        links = WIKILINK_RE.findall(content)
        for link_content in links:
            target = link_content.split('|')[0].strip()

            if target not in links_to:
                links_to[target] = set()
            links_to[target].add(filepath)

            if target not in all_pages and _link_slug(target) not in all_pages_normalized:
                broken_links.add((filepath, target))

    orphans = []
    # Pre-bucket links_to by slug-normalized key so orphan detection picks up
    # references that use different case/punctuation (e.g. ``[[KNOX]]`` →
    # ``knox.md``) — the same Obsidian-default semantics applied to the
    # broken-link check above.
    links_to_normalized: dict[str, set[Path]] = {}
    for k, srcs in links_to.items():
        norm = _link_slug(k)
        links_to_normalized.setdefault(norm, set()).update(srcs)

    for f in file_contents.keys():
        if f in special_files:
            continue

        page_name = f.stem
        rel_path = f.relative_to(wiki_dir).with_suffix('').as_posix()

        inbound_links = set()
        inbound_links.update(links_to.get(page_name, set()))
        inbound_links.update(links_to.get(rel_path, set()))
        # Slug-normalized lookup catches links written in a different case/form.
        inbound_links.update(links_to_normalized.get(_link_slug(page_name), set()))
        inbound_links.update(links_to_normalized.get(_link_slug(rel_path), set()))

        # Real inbound links are those that don't come from the page itself
        real_inbound = [p for p in inbound_links if p != f]

        if not real_inbound:
            orphans.append(rel_path)

    missing_targets = {}
    for src, target in broken_links:
        if target not in missing_targets:
            missing_targets[target] = []
        missing_targets[target].append(src)

    report_path = script_dir / 'wiki_lint_report.md'
    with open(report_path, 'w', encoding='utf-8') as f_out:
        f_out.write("# Wiki Lint Report\n\n")

        f_out.write(f"**Total markdown files checked:** {len(file_contents)}\n")
        f_out.write(f"**Total orphans found:** {len(orphans)}\n")
        f_out.write(f"**Total missing pages (broken links):** {len(missing_targets)}\n")
        f_out.write(f"**Total files with format errors:** {len(format_errors)}\n")
        f_out.write(f"**Total files with structural errors:** {len(structural_errors)}\n")
        f_out.write(f"**Total files with content debt:** {len(content_debt)}\n")
        if fix:
            f_out.write(f"**Total files auto-repaired:** {total_repaired}\n")
        f_out.write("\n")

        # ── Section 0: Auto-repair summary (when --fix was used) ──
        if fix and all_repairs:
            f_out.write("## 0. Auto-Repairs Applied\n\n")
            f_out.write(f"**{total_repaired}** pages were automatically repaired "
                        f"({sum(len(r) for r in all_repairs.values())} total fixes). "
                        f"Backups saved to `.backup/`.\n\n")
            for filepath in sorted(all_repairs.keys(), key=lambda p: p.as_posix()):
                rel = filepath.relative_to(wiki_dir).as_posix()
                f_out.write(f"- `{rel}`\n")
                for repair in all_repairs[filepath]:
                    f_out.write(f"  - ✅ {repair}\n")
            f_out.write("\n")

        f_out.write("## 1. Orphan Pages (No inbound links)\n")
        if not orphans:
            f_out.write("None found. Great!\n")
        else:
            f_out.write("Pages that are not linked from any other page in the wiki. **Fix:** Add links from `index.md` or related concept pages.\n\n")
            for o in sorted(orphans):
                f_out.write(f"- `{o}`\n")

        f_out.write("\n## 2. Concepts Mentioned but Lack Their Own Page\n")
        if not missing_targets:
            f_out.write("None found. Great!\n")
        else:
            f_out.write("Wikilinks pointing to a file that doesn't exist. **Fix:** Create these pages in `wiki/concepts/` or remove the brackets.\n\n")
            for t in sorted(missing_targets.keys()):
                srcs = missing_targets[t]
                f_out.write(f"- **[[{t}]]** (mentioned in {len(srcs)} files: ")
                f_out.write(", ".join([f"`{s.as_posix()}`" for s in srcs[:3]]))
                if len(srcs) > 3:
                    f_out.write(f" and {len(srcs)-3} more")
                f_out.write(")\n")

        f_out.write("\n## 3. Format Errors\n")
        if not format_errors:
            f_out.write("None found. Great!\n")
        else:
            f_out.write("Pages that do not follow the required schema in `GEMINI.md`. **Fix:** Add the required YAML frontmatter and/or markdown sections.\n\n")
            for filepath in sorted(format_errors.keys(), key=lambda p: p.as_posix()):
                f_out.write(f"- `{filepath.as_posix()}`\n")
                for err in format_errors[filepath]:
                    f_out.write(f"  - {err}\n")

        _write_findings_report(
            f_out,
            heading="## 4. Structural Errors (actionable)",
            findings=structural_errors,
            intro=(
                "Deterministic schema or section-placement defects that can "
                "make wiki tooling interpret a page incorrectly."
            ),
        )
        _write_findings_report(
            f_out,
            heading="## 5. Content Debt (advisory)",
            findings=content_debt,
            intro=(
                "Valid but incomplete seed-page content. Empty relationships "
                "and unsourced prose remain visible for source-grounded "
                "curation, but do not make the linter fail."
            ),
        )

    return {
        'format_errors': len(format_errors),
        'structural_errors': len(structural_errors),
        'content_debt': len(content_debt),
        'broken_links': len(missing_targets),
        'orphans': len(orphans),
        'repaired': total_repaired,
    }

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Wiki schema, link, and content-debt linter")
    parser.add_argument('--fix', action='store_true',
                        help='Auto-repair deterministic schema issues (backups saved to .backup/)')
    args = parser.parse_args()

    results = lint_wiki(fix=args.fix)
    print(
        f"Lint complete: {results['format_errors']} format errors, "
        f"{results['structural_errors']} structural errors, "
        f"{results['content_debt']} content-debt pages, "
        f"{results['broken_links']} missing pages, "
        f"{results['orphans']} orphans"
        + (f", {results['repaired']} auto-repaired." if args.fix else ".")
    )
    if results['format_errors'] or results['structural_errors']:
        sys.exit(1)
