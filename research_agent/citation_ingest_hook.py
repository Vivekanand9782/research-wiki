"""Phase 6: Incremental citation ingest hook.

Called by the research-wiki ingest pipeline after a new paper is processed.
Extracts its "Key References" citations, matches them against the existing paper
index, and updates wiki/citation_network.json with new edges.

Usage (standalone):
    python3 citation_ingest_hook.py <paper_stem>

Usage (from ingest_parallel.py):
    from citation_ingest_hook import hook_new_paper
    hook_new_paper("zhang_2025_new_paper_stem")

Idempotent: safe to re-run on the same paper.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WIKI_DIR = Path("/Users/vivekanandsirohi/Desktop/antigravity/research-wiki/wiki")
GRAPH_PATH = WIKI_DIR / "citation_network.json"
INDEX_PATH = Path("/Users/vivekanandsirohi/Documents/OpenScience/sessions/2026-08-04-1715/phase1_paper_index.json")

_CITATION_RE = re.compile(
    r"([A-Z][a-z]+(?:\s+(?:and|[A-Z][a-z]+)|\s+et\s+al\.?)\s*"
    r"(?:\(?[12]\d{3}(?:\s*,\s*[12]\d{3})*\)?"
    r"|\((?:[12]\d{3}(?:\s*,\s*[12]\d{3})+|[12]\d{3})\)))"
)


def _load_graph():
    if GRAPH_PATH.exists():
        return json.loads(GRAPH_PATH.read_text())
    return {"version": 1, "papers": {}, "statistics": {}}


def _save_graph(graph):
    total = sum(len(p.get("cites", [])) for p in graph.get("papers", {}).values())
    graph["statistics"]["total_papers"] = len(graph.get("papers", {}))
    graph["statistics"]["total_edges"] = total
    GRAPH_PATH.write_text(json.dumps(graph, indent=2))


def _load_index():
    return json.loads(INDEX_PATH.read_text())


def _extract_refs_section(text: str) -> str | None:
    m = re.search(r"(?:^|\n)#{1,3}\s*Key References.*?\n", text)
    if not m:
        return None
    rest = text[m.end():]
    for pat in [r"\n#{1,3}\s+", r"\n---\s*\n", r"\*\*Source PDF:"]:
        em = re.search(pat, rest)
        if em:
            rest = rest[:em.start()]
    return rest.strip()


def _parse_citations(section: str) -> list[dict]:
    results = []
    for line in section.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^\d+[.)]\s*", "", line).lstrip("-•* ")
        if not line:
            continue
        am = re.match(r"([A-Z][a-z]+)", line)
        first_author = am.group(1) if am else "Unknown"
        years = sorted({int(y) for y in re.findall(r"[12]\d{3}", line[:80]) if 1900 <= int(y) <= 2030})
        doi_m = re.search(r"(10\.\d{4,9}/[^\s,)\"'\]]+)", line)
        doi = doi_m.group(1) if doi_m else None
        desc = line.split("—", 1)[1].strip()[:200] if "—" in line else ""
        results.append({"first_author": first_author, "years": years, "doi": doi, "raw": line[:300], "description": desc})
    return results


def _match_citation(cite: dict, index: dict) -> dict | None:
    """Match a citation against the paper index. Returns matched paper data or None."""
    papers = index.get("index", {})

    # Tier 1: DOI exact
    doi = cite.get("doi")
    if doi and doi != "null":
        for stem, paper in papers.items():
            if paper.get("doi") == doi:
                return paper

    # Build author+year index
    author = (cite.get("first_author") or "").lower()
    years = cite.get("years", [])
    if not author or not years:
        return None

    candidates = []
    for stem, paper in papers.items():
        pa = (paper.get("first_author") or "").lower().strip()
        py = paper.get("year")
        if pa == author and py in years:
            candidates.append(paper)

    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None

    # Disambiguate by title overlap
    raw_title = re.split(r"—|-", cite.get("raw", ""))[0]
    raw_tokens = set(re.sub(r"[^\w\s]", " ", raw_title.lower()).split())
    stopwords = {"the","a","an","of","in","on","for","and","to","with","by","at","from"}
    raw_tokens -= stopwords

    best, best_score = None, 0.0
    for cand in candidates:
        cand_tokens = set(cand.get("title_tokens", []))
        if not cand_tokens:
            cand_tokens = set(re.sub(r"[^\w\s]", " ", (cand.get("title") or "").lower()).split())
            cand_tokens -= stopwords
        overlap = len(raw_tokens & cand_tokens) / max(1, len(raw_tokens | cand_tokens))
        if overlap > best_score:
            best, best_score = cand, overlap
    return best if best_score > 0.3 else None


def hook_new_paper(stem: str) -> dict:
    """Process a single new paper and update the citation graph.

    Returns: {"stem": str, "outgoing": int, "incoming_updated": int, "errors": list}
    """
    paper_file = None
    for subdir in ["sources/uncategorized", "sources", "entities", "concepts"]:
        candidate = WIKI_DIR / subdir / f"{stem}.md"
        if candidate.exists():
            paper_file = candidate
            break

    if not paper_file:
        return {"stem": stem, "outgoing": 0, "incoming_updated": 0, "errors": [f"file not found for {stem}"]}

    text = paper_file.read_text(encoding="utf-8", errors="replace")
    section = _extract_refs_section(text)
    if not section:
        return {"stem": stem, "outgoing": 0, "incoming_updated": 0, "errors": ["no Key References section"]}

    citations = _parse_citations(section)
    index = _load_index()
    graph = _load_graph()
    papers = graph.setdefault("papers", {})

    # Ensure this paper is in the graph
    papers.setdefault(stem, {"cites": [], "cited_by": []})

    outgoing = 0
    incoming_updated = 0
    errors = []

    for cite in citations:
        matched = _match_citation(cite, index)
        if not matched:
            continue

        target_stem = matched.get("stem")
        if not target_stem or target_stem == stem:
            continue

        # Check for duplicates (idempotent)
        existing_targets = {c["target"] for c in papers[stem]["cites"]}
        if target_stem in existing_targets:
            continue

        papers[stem]["cites"].append({"target": target_stem, "confidence": 0.8, "tier": 2})
        outgoing += 1

        # Update reverse edge
        papers.setdefault(target_stem, {"cites": [], "cited_by": []})
        existing_sources = {c["source"] for c in papers[target_stem]["cited_by"]}
        if stem not in existing_sources:
            papers[target_stem]["cited_by"].append({"source": stem, "confidence": 0.8, "tier": 2})
            incoming_updated += 1

    _save_graph(graph)
    return {"stem": stem, "outgoing": outgoing, "incoming_updated": incoming_updated, "errors": errors}


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <paper_stem> [paper_stem2 ...]")
        sys.exit(1)

    stems = sys.argv[1:]
    for stem in stems:
        result = hook_new_paper(stem)
        print(f"  {stem}: +{result['outgoing']} outgoing, +{result['incoming_updated']} incoming updates")
        if result["errors"]:
            print(f"    errors: {result['errors']}")


if __name__ == "__main__":
    main()
