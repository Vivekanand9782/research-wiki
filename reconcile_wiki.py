#!/usr/bin/env python3
"""Reconcile all research-wiki trackers & artifacts after new source pages are
hand-authored. Idempotent — safe to run repeatedly.

Steps:
 1. Create honest stub concept/entity pages for any wikilink in a source page
    that has no page yet (typed by which section it appears in). Never
    overwrites an existing page.
 2. Rebuild root processed_papers.json from disk (one entry per source page).
 3. Regenerate wiki/processed_papers.json via update_processed_manifest.py.
 4. Rebuild wiki/search_index.json via search.py.
 5. Rebuild wiki/index.md from disk.
 6. Mark pipeline_state 'ingest' for every source page's raw file.
 7. Print a consistency report and exit non-zero if anything mismatches.

Usage: python3 reconcile_wiki.py
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
import pathlib

RW = pathlib.Path(__file__).resolve().parent
SRC = RW / "wiki" / "sources" / "uncategorized"
SRC_ROOT = RW / "wiki" / "sources"
CONC = RW / "wiki" / "concepts"
ENT = RW / "wiki" / "entities"
TODAY = datetime.date.today().isoformat()


def slugify(s: str) -> str:
    s = s.strip().lower().replace("/", "-").replace(" ", "-")
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return re.sub(r"-+", "-", s).strip("-")


def section_block(txt: str, name: str) -> str:
    m = re.search(r"## " + re.escape(name) + r"\n(.*?)(?=\n## |\Z)", txt, re.S)
    return m.group(1) if m else ""


def all_source_files():
    return sorted(SRC_ROOT.rglob("*.md"))


def step1_stubs():
    link_type = {}  # slug -> (type, display)
    for p in all_source_files():
        txt = p.read_text()
        # 1. Scan entire text to catch all stray wikilinks as concepts by default
        for disp in re.findall(r"\[\[([^\]]+)\]\]", txt):
            target = disp.split("|")[0].strip()
            link_type.setdefault(slugify(target), ("concept", target))

        # 2. Refine using specific section mappings (entities win)
        for disp in re.findall(r"\[\[([^\]]+)\]\]", section_block(txt, "Key Concepts & Theory")):
            target = disp.split("|")[0].strip()
            link_type[slugify(target)] = ("concept", target)

        for disp in re.findall(r"\[\[([^\]]+)\]\]", section_block(txt, "Important Entities")):
            target = disp.split("|")[0].strip()
            link_type[slugify(target)] = ("entity", target)

    existing = {p.stem for p in CONC.rglob("*.md")} | {p.stem for p in ENT.rglob("*.md")}
    created = 0
    for s, (typ, disp) in sorted(link_type.items()):
        if not s or s in existing:
            continue
        d = CONC if typ == "concept" else ENT
        stub_path = d / f"{s}.md"
        stub_content = (
            f"---\ntags: [{typ}]\ntype: {typ}\ndate_created: {TODAY}\n"
            f"date_updated: {TODAY}\nsource_count: 1\n---\n\n# {disp}\n\n"
            f"**Summary**:\nStub page for **{disp}**. Referenced by ingested "
            f"source(s); to be expanded as more papers covering this {typ} are "
            f"processed.\n\n**Sources**:\n_None yet._\n\n"
            f"**Last updated**: {TODAY}\n\n## Related pages\n"
        )
        if not stub_path.exists():
            stub_path.write_text(stub_content, encoding="utf-8")
            created += 1
    return created


TOPICS = ["bioethanol", "genome_editing_transgene_free", "PHS_tolerance", "uncategorized"]


def _norm(stem: str) -> str:
    st = stem.strip().lower().replace(" ", "_")
    st = re.sub(r"[^a-z0-9._-]", "", st)
    return re.sub(r"_+", "_", st).strip("_")


def _fuzzy_match_raw(slug: str):
    """Best-effort (topic, raw_relpath) for a source-page slug, tolerant of
    accent/space loss. Matches on normalised stem, then on a prefix heuristic."""
    cand = []
    for topic in TOPICS:
        d = RW / "raw" / "papers" / topic
        if not d.exists():
            continue
        for p in d.glob("*.md"):
            cand.append((topic, p, _norm(p.stem)))
    # exact normalised match
    for topic, p, nst in cand:
        if nst == _norm(slug):
            return topic, str(p.relative_to(RW))
    # fallback: longest shared prefix on alnum-only
    def alnum(s):
        return re.sub(r"[^a-z0-9]", "", s)
    a = alnum(slug)
    best = None
    for topic, p, nst in cand:
        b = alnum(nst)
        k = 0
        for x, y in zip(a, b):
            if x == y:
                k += 1
            else:
                break
        if k >= 12 and (best is None or k > best[0]):
            best = (k, topic, str(p.relative_to(RW)))
    if best:
        return best[1], best[2]
    return "uncategorized", ""


def step2_root_tracker():
    """Preserve existing tracker entries, appending any new source page on
    disk. Skipped (off-topic/mis-filed) raw files live in a separate
    `skipped` list so they are excluded from counts and from the queue but
    still recorded. processed_count = number of real source pages."""
    p = RW / "processed_papers.json"
    prev = json.load(open(p)) if p.exists() else {"processed_papers": []}
    by_norm_slug = {e["slug"].strip().lower(): e for e in prev.get("processed_papers", [])}
    skipped = prev.get("skipped", [])

    new_by_slug = {}
    for src in all_source_files():
        slug = src.stem
        norm_slug = slug.strip().lower()
        if norm_slug in by_norm_slug:
            entry = by_norm_slug[norm_slug]
            entry["slug"] = slug  # update to match actual file case
            new_by_slug[slug] = entry
        else:
            topic, raw = _fuzzy_match_raw(slug)
            new_by_slug[slug] = {
                "slug": slug,
                "topic": topic,
                "raw_file": pathlib.Path(raw).name if raw else "",
                "raw_relpath": raw,
                "processed_date": TODAY,
                "method": "manual-hand-authored",
            }
    entries = sorted(new_by_slug.values(), key=lambda e: e["slug"])
    out = {
        "processed_count": len(entries),
        "processed_papers": entries,
        "skipped": skipped,
    }
    desired = json.dumps(out, indent=2, ensure_ascii=False)
    if not p.exists() or p.read_text(encoding="utf-8") != desired:
        p.write_text(desired, encoding="utf-8")


def _raw_for(slug: str) -> str:
    """Resolve raw relpath for a slug, preferring the tracker's stored mapping."""
    p = RW / "processed_papers.json"
    if p.exists():
        for e in json.load(open(p)).get("processed_papers", []):
            if e["slug"] == slug:
                if e.get("raw_relpath"):
                    return e["raw_relpath"]
                if e.get("raw_file"):
                    for topic in TOPICS:
                        c = RW / "raw" / "papers" / topic / e["raw_file"]
                        if c.exists():
                            return str(c.relative_to(RW))
    _, raw = _fuzzy_match_raw(slug)
    return raw


def step3_manifest():
    subprocess.run([sys.executable, "update_processed_manifest.py"], cwd=RW, check=True,
                   capture_output=True)


def step4_search():
    """Rebuild the search index through the current retrieval API.

    The historical CLI required a positional query, so invoking ``search.py``
    without arguments made reconciliation abort before manifest/state updates.
    """
    from research_retrieval import FullTextSearch

    FullTextSearch(wiki_folder=str(RW / "wiki")).build_index()


def step5_index():
    rows = []
    for p in all_source_files():
        txt = p.read_text()
        m = re.search(r"^# (.+)$", txt, re.M)
        title = m.group(1) if m else p.stem
        yr = re.search(r"^year:\s*(.+)$", txt, re.M)
        rows.append((p.stem, title, yr.group(1).strip() if yr else "?"))
    lines = ["# Research Wiki Index", "", "## Ingested Sources", ""]
    for slug, title, yr in rows:
        lines.append(f"- [[{slug}]] — {title} ({yr})")
    lines += ["", f"\n_Total ingested sources: {len(rows)}_"]
    desired = "\n".join(lines)
    index_path = RW / "wiki" / "index.md"
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != desired:
        index_path.write_text(desired, encoding="utf-8")


def step6_pipeline_state():
    import pipeline_state as ps
    p = RW / "wiki" / ".understand-anything" / "intermediate" / "pipeline_state.json"
    st = ps.PipelineState(str(p))
    n = 0
    for src in all_source_files():
        raw = _raw_for(src.stem)
        if not raw:
            continue
        fp = ps.fingerprint_file(raw, "extractor:v1", "summary-prompt:v1")
        if not st.is_done("ingest", fp):
            st.mark_done("ingest", fp, {"slug": src.stem, "raw": raw})
            n += 1
    st.save()
    return len(st._data.get("ingest", {}))


def report():
    root = json.load(open(RW / "processed_papers.json"))["processed_count"]
    mani = json.load(open(RW / "wiki" / "processed_papers.json"))["count"]
    srcn = len(list(SRC_ROOT.rglob("*.md")))
    idx = (RW / "wiki" / "index.md").read_text().count("- [[")
    st = json.load(open(RW / "wiki" / ".understand-anything" / "intermediate" / "pipeline_state.json"))
    ing = len(st.get("ingest", {}))
    docs = json.load(open(RW / "wiki" / "search_index_docs.json"))
    # broken wikilinks
    pages = ({p.stem for p in SRC_ROOT.rglob("*.md")}
             | {p.stem for p in CONC.rglob("*.md")}
             | {p.stem for p in ENT.rglob("*.md")})
    broken = set()
    for p in all_source_files():
        for disp in re.findall(r"\[\[([^\]]+)\]\]", p.read_text()):
            target = disp.split("|")[0].strip()
            if slugify(target) not in pages:
                broken.add(disp)
    ok = (root == mani == srcn == idx) and not broken
    print(f"root={root} manifest={mani} sources={srcn} index={idx} "
          f"ingest={ing} search_docs={len(docs)} "
          f"concepts={len(list(CONC.rglob('*.md')))} entities={len(list(ENT.rglob('*.md')))}")
    print("broken_wikilinks:", sorted(broken) if broken else "NONE")
    print("CONSISTENT" if ok else "MISMATCH")
    return ok


def main():
    c = step1_stubs()
    print(f"stub pages created: {c}")
    step2_root_tracker()
    step3_manifest()
    step4_search()
    step5_index()
    step6_pipeline_state()
    ok = report()
    sys.exit(0 if ok else 1)


def _cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    main()


if __name__ == "__main__":
    _cli()
