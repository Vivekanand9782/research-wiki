"""Local retrieval tools over the Antigravity research-wiki.

Wraps the wiki's own quality-aware BM25-style engine
(`research_retrieval.FullTextSearch`) plus page-reading and wikilink-graph
helpers. Everything is deterministic and local — no API calls, no cost.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path

ANTIGRAVITY_ROOT = Path(
    os.environ.get("ANTIGRAVITY_ROOT", Path.home() / "Desktop" / "antigravity")
)
WIKI_DIR = ANTIGRAVITY_ROOT / "research-wiki" / "wiki"

if str(ANTIGRAVITY_ROOT / "research-wiki") not in sys.path:
    sys.path.insert(0, str(ANTIGRAVITY_ROOT / "research-wiki"))

_SEARCH = None
_CITATION_GRAPH = None
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:[#|][^\]]*)?\]\]")


def _engine():
    global _SEARCH
    if _SEARCH is None:
        from research_retrieval import FullTextSearch

        _SEARCH = FullTextSearch(wiki_folder=str(WIKI_DIR))
    return _SEARCH


def _citation_graph():
    global _CITATION_GRAPH
    if _CITATION_GRAPH is None:
        path = WIKI_DIR / "citation_network.json"
        if path.exists():
            _CITATION_GRAPH = json.loads(path.read_text())
        else:
            _CITATION_GRAPH = {"papers": {}}
    return _CITATION_GRAPH


def _safe_path(rel: str) -> Path:
    root = WIKI_DIR.parent.resolve()
    candidate = (root / rel).resolve() if not str(rel).startswith("/") else Path(rel).resolve()
    # relative_to, not startswith: a sibling such as research-wiki-scratch/
    # shares the string prefix but is outside the root.
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"path escapes research-wiki root: {rel}")
    if not candidate.exists():
        raise FileNotFoundError(rel)
    return candidate


def wiki_search(
    query: str,
    top_k: int = 8,
    mode: str = "hybrid",
    doc_type: str | None = None,
    include_stubs: bool = False,
) -> list[dict]:
    results = _engine().search(
        query,
        top_k=top_k,
        mode=mode,
        doc_type=doc_type,
        include_stubs=include_stubs,
    )
    hits = []
    for rank, r in enumerate(results, start=1):
        hits.append(
            {
                "rank": rank,
                "doc_type": r.doc_type,
                "title": r.title,
                "paper": r.paper,
                "score": round(float(r.score), 3),
                "evidence_quality": getattr(r, "evidence_quality", None),
                "section": r.section,
                "path": r.source_path or r.path,
                "lines": (
                    f"{r.line_start}-{r.line_end}" if getattr(r, "line_start", None) else None
                ),
                "snippet": (r.snippet or "").strip()[:400],
            }
        )
    return hits


def read_page(path: str, max_chars: int = 6000) -> str:
    text = _safe_path(path).read_text(encoding="utf-8", errors="replace")
    return text[:max_chars] + ("\n…[truncated]" if len(text) > max_chars else "")


def read_lines(path: str, start: int, end: int) -> str:
    lines = _safe_path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    start, end = max(1, start), min(len(lines), end)
    return "\n".join(lines[start - 1 : end])


def extract_links(text: str) -> list[str]:
    seen, links = set(), []
    for match in _WIKILINK_RE.finditer(text):
        name = match.group(1).strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            links.append(name)
    return links


def related_pages(page_path: str) -> list[str]:
    text = _safe_path(page_path).read_text(encoding="utf-8", errors="replace")
    return extract_links(text)


def wiki_stats() -> dict:
    counts = {}
    for folder in ("sources", "entities", "concepts", "synthesis"):
        target = WIKI_DIR / folder
        if target.exists():
            counts[folder] = sum(1 for p in target.rglob("*.md"))
    return {"wiki_root": str(WIKI_DIR), "pages": counts}


def papers_i_cite(paper: str) -> list[dict]:
    graph = _citation_graph()
    paper_data = graph.get("papers", {}).get(paper, {})
    return [{"target": c["target"], "confidence": c["confidence"]}
            for c in paper_data.get("cites", [])]


def papers_citing(paper: str) -> list[dict]:
    graph = _citation_graph()
    paper_data = graph.get("papers", {}).get(paper, {})
    return [{"source": c["source"], "confidence": c["confidence"]}
            for c in paper_data.get("cited_by", [])]


def related_papers(paper: str, max: int = 6) -> list[dict]:
    graph = _citation_graph()
    papers = graph.get("papers", {})
    if paper not in papers:
        return []
    my_cites = {c["target"] for c in papers[paper].get("cites", [])}
    my_cited_by = {c["source"] for c in papers[paper].get("cited_by", [])}
    my_set = my_cites | my_cited_by
    if not my_set:
        return []
    scored = []
    for other_stem, other_data in papers.items():
        if other_stem == paper:
            continue
        other_cites = {c["target"] for c in other_data.get("cites", [])}
        other_cited_by = {c["source"] for c in other_data.get("cited_by", [])}
        other_set = other_cites | other_cited_by
        intersection_len = len(my_set & other_set)
        if intersection_len:
            union_len = len(my_set) + len(other_set) - intersection_len
            scored.append({
                "paper": other_stem,
                "shared_citations": intersection_len,
                "jaccard": round(intersection_len / union_len, 3)
            })
    scored.sort(key=lambda x: x["shared_citations"], reverse=True)
    return scored[:max]


def citation_chain(paper_a: str, paper_b: str, max_depth: int = 3) -> list:
    graph = _citation_graph()
    papers = graph.get("papers", {})
    if paper_a not in papers or paper_b not in papers:
        return {"path": None, "error": "One or both papers not in graph"}
    from collections import deque
    queue = deque([(paper_a, [paper_a])])
    visited = {paper_a}
    while queue:
        current, path = queue.popleft()
        if len(path) - 1 >= max_depth:
            continue
        neighbors = set()
        for c in papers.get(current, {}).get("cites", []):
            neighbors.add(c["target"])
        for c in papers.get(current, {}).get("cited_by", []):
            neighbors.add(c["source"])
        for neighbor in neighbors:
            if neighbor == paper_b:
                return {"path": path + [neighbor], "length": len(path)}
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return {"path": None, "error": f"No path within depth {max_depth}"}


TOOLS = {
    "wiki_search": {
        "fn": wiki_search,
        "description": (
            "Search the wiki corpus. Args: query (required), top_k=8, "
            "mode=summary|hybrid|evidence, doc_type=paper|entity|concept|synthesis. "
            "Returns ranked hits with path, section, line range and snippet."
        ),
    },
    "read_page": {
        "fn": read_page,
        "description": "Read a wiki page by relative path, up to 6000 chars. Args: path.",
    },
    "read_lines": {
        "fn": read_lines,
        "description": "Read exact evidence lines from a hit. Args: path, start, end.",
    },
    "related_pages": {
        "fn": related_pages,
        "description": "List [[wikilinks]] reachable from a page. Args: path.",
    },
    "wiki_stats": {
        "fn": wiki_stats,
        "description": "Corpus page counts. Args: none.",
    },
    "papers_i_cite": {
        "fn": papers_i_cite,
        "description": (
            "List papers this paper cites (outgoing citations). "
            "Args: paper (stem name, e.g. 'zhang_2014_cloning_seed_dormancy'). "
            "Returns list of {target, confidence}."
        ),
    },
    "papers_citing": {
        "fn": papers_citing,
        "description": (
            "List papers that cite this paper (incoming citations). "
            "Args: paper (stem name). Returns list of {source, confidence}."
        ),
    },
    "related_papers": {
        "fn": related_papers,
        "description": (
            "Find papers sharing citations with this one (Jaccard similarity). "
            "Args: paper (stem name), max=6. Returns list of {paper, shared_citations, jaccard}."
        ),
    },
    "citation_chain": {
        "fn": citation_chain,
        "description": (
            "Find shortest citation path between two papers. "
            "Args: paper_a, paper_b, max_depth=3. Returns {path: [stems...], length}."
        ),
    },
}


def dispatch(name: str, args: dict | None):
    tool = TOOLS.get(name)
    if tool is None:
        raise ValueError(f"unknown tool: {name}; available: {sorted(TOOLS)}")
    return tool["fn"](**(args or {}))


def tool_manifest() -> str:
    return json.dumps(
        {name: spec["description"] for name, spec in TOOLS.items()}, indent=2
    )
