"""process_analyzer.py — extract experimental workflows or biochemical pathways.

Inspired by Understand-Anything's ``domain-analyzer`` agent, which builds a
horizontal flow graph of business domain → flow → step. The research equivalent
is two complementary views:

  * **workflow** — experimental protocol chains, e.g.
    *EMS mutagenesis → TILLING screen → SBEII identification → phenotyping*.
  * **pathway**  — biochemical cascades, e.g.
    *phenylpropanoid → monolignol → lignin → cell wall*.

Given a topic anchor (a concept or entity name), the script gathers the source
pages connected to it, asks the LLM to extract a structured chain, and writes
the result to ``wiki/processes/<slug>.md`` with full citations.

Usage::

    python3 process_analyzer.py --topic lignin --kind pathway
    python3 process_analyzer.py --topic CRISPR --kind workflow --max-sources 8
    python3 process_analyzer.py --auto                    # pick top-N anchors
    python3 process_analyzer.py --topic lignin --dry-run
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

import config  # noqa: F401
from genai_client import get_ai_response

WIKI = Path(__file__).resolve().parent / "wiki"
MANIFEST = WIKI / ".understand-anything" / "intermediate" / "scan-manifest.json"
PROCESSES_DIR = WIKI / "processes"
LOG_PATH = WIKI / ".understand-anything" / "intermediate" / "process_analyzer.jsonl"

PER_SOURCE_CHAR_LIMIT = 4000
MAX_SOURCES_DEFAULT = 6


PROMPT_TEMPLATE = """You are a research analyst building a structured process map for a plant-genetics wiki.

Anchor concept/entity: **{anchor}**
Mode: **{kind}** ({kind_help})

Read the {n} source-paper summaries below and extract a single chain of steps.
- For ``workflow`` mode: extract the dominant experimental protocol used across these papers \
(e.g. mutagenesis → screening → genotyping → phenotyping).
- For ``pathway`` mode: extract the biochemical or regulatory cascade these papers describe \
(e.g. phenylpropanoid pathway → monolignol synthesis → lignin polymerization).

Constraints:
1. Output **valid JSON** matching exactly this schema (no prose, no markdown fences):
   {{
     "title": "<short human title>",
     "kind": "{kind}",
     "anchor": "{anchor}",
     "steps": [
       {{"name": "<step name>", "summary": "<one-sentence what>", "sources": ["<source-stem>", ...]}},
       ...
     ],
     "notes": "<one short paragraph on caveats, contradictions, or branches>"
   }}
2. Every step's ``sources`` list must contain **at least one** source-stem from the input list.
3. ``source-stem`` is the filename without ``.md`` and without path, e.g. \
``Wang_2024_Knockout_ZmNST2_Bioethanol_Production_Co``.
4. Aim for 4–8 steps. Merge near-duplicate steps. Prefer concrete biochemical or experimental \
language over generic terms.
5. If the sources are too heterogeneous to support a single chain, return a JSON object with \
``"steps": []`` and explain why in ``notes``.

---

## Sources

{sources_block}
"""

KIND_HELP = {
    "workflow": "experimental protocol chain",
    "pathway":  "biochemical or regulatory cascade",
}


# ─────────────────────────────────────────────────────────────────────────────
# Graph loading (shared shape with tour_builder)
# ─────────────────────────────────────────────────────────────────────────────
def _read_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    try:
        data = yaml.safe_load(text[3:end]) or {}
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "process"


def load_graph() -> tuple[dict, list[tuple[str, str]]]:
    """Returns (nodes_by_filePath, edges) — edges have .md suffix on both ends."""
    if not MANIFEST.exists():
        print(f"ERROR: scan-manifest.json missing — run UA's parse-knowledge-base.py first", file=sys.stderr)
        sys.exit(2)
    manifest = json.loads(MANIFEST.read_text())
    nodes: dict[str, dict] = {}
    for n in manifest.get("nodes", []):
        fp = n.get("filePath", "")
        if not fp:
            continue
        kind = "concept" if fp.startswith("concepts/") else \
               "entity"  if fp.startswith("entities/") else \
               "source"  if fp.startswith("sources/")  else \
               "synthesis" if fp.startswith("synthesis/") else "other"
        nodes[fp] = {
            "filePath": fp, "name": n.get("name", Path(fp).stem),
            "type": kind, "summary": n.get("summary", ""),
        }
    edges: list[tuple[str, str]] = []
    for e in manifest.get("edges", []):
        s, t = e.get("source", ""), e.get("target", "")
        if s.startswith("article:") and t.startswith("article:"):
            edges.append((s[len("article:"):] + ".md", t[len("article:"):] + ".md"))
    return nodes, edges


def find_anchor(nodes: dict, topic: str) -> str | None:
    """Look up an anchor by exact stem, exact name, or case-insensitive name match."""
    norm = topic.strip().lower().replace(" ", "-")
    for fp, n in nodes.items():
        if n["type"] not in {"concept", "entity"}:
            continue
        stem = Path(fp).stem.lower()
        name = (n["name"] or "").lower()
        if stem == norm or name == topic.lower() or stem == topic.lower():
            return fp
    # Fallback: substring
    for fp, n in nodes.items():
        if n["type"] not in {"concept", "entity"}:
            continue
        if norm in Path(fp).stem.lower():
            return fp
    return None


def select_sources_for(anchor_fp: str, nodes: dict, edges: list, limit: int) -> list[dict]:
    """Sources connected to the anchor (concept/entity) via outbound edges."""
    outbound = defaultdict(set)
    for src, tgt in edges:
        outbound[src].add(tgt)
    related = [t for t in outbound.get(anchor_fp, set()) if nodes.get(t, {}).get("type") == "source"]
    out = []
    for sfp in related[:limit]:
        full = WIKI / sfp
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        # Strip frontmatter for the prompt body
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end > 0:
                text = text[end + 4:]
        out.append({
            "stem": Path(sfp).stem,
            "filePath": sfp,
            "name": nodes[sfp]["name"],
            "body": text[:PER_SOURCE_CHAR_LIMIT],
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────
# LLM call + page rendering
# ─────────────────────────────────────────────────────────────────────────────
JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _parse_llm_json(raw: str) -> dict | None:
    """Try direct json, then fenced extraction, then first-{...}-block heuristic."""
    raw = raw.strip()
    for candidate in (raw, *(m.group(1) for m in JSON_FENCE_RE.finditer(raw))):
        try:
            return json.loads(candidate)
        except (ValueError, TypeError):
            continue
    # Last resort: grab from first { to last }
    if "{" in raw and "}" in raw:
        try:
            return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
        except (ValueError, TypeError):
            return None
    return None


def render_process_page(parsed: dict, anchor_fp: str, sources: list[dict]) -> str:
    today = datetime.date.today().isoformat()
    title = parsed.get("title") or f"Process: {Path(anchor_fp).stem}"
    kind = parsed.get("kind") or "process"
    notes = parsed.get("notes") or ""
    valid_stems = {s["stem"] for s in sources}

    lines = [
        "---",
        f"tags: [process, {kind}, auto-generated]",
        "type: synthesis",
        f"date_created: {today}",
        f"date_updated: {today}",
        f"source_count: {len(sources)}",
        "---",
        "",
        f"# {title}",
        "",
        f"**Summary**: Auto-generated {kind} for `[[{Path(anchor_fp).stem}]]`, "
        f"derived from {len(sources)} source papers.",
        "",
        f"**Sources**: see citations against each step below.",
        "",
        f"**Last updated**: {today}",
        "",
        "---",
        "",
        "## Steps",
        "",
    ]
    for i, step in enumerate(parsed.get("steps") or [], 1):
        sname = step.get("name", f"Step {i}")
        ssum = step.get("summary", "")
        # Keep only valid source stems; drop hallucinated ones
        srcs = [s for s in (step.get("sources") or []) if s in valid_stems]
        cite = " ".join(f"[[{s}]]" for s in srcs) if srcs else "_(no source attributed)_"
        lines.append(f"### {i}. {sname}")
        lines.append("")
        lines.append(f"{ssum}  {cite}")
        lines.append("")

    if notes:
        lines += ["## Notes", "", notes, ""]

    lines += [
        "## Related pages",
        "",
        f"- [[{Path(anchor_fp).stem}]]",
        "",
        "_Generated by `process_analyzer.py`. Manual edits below this line are preserved on regeneration "
        "if you remove the ``auto-generated`` tag from the frontmatter._",
    ]
    return "\n".join(lines) + "\n"


AUTO_TAG_MARKER = "auto-generated"


def write_process(parsed: dict, anchor_fp: str, sources: list[dict], kind: str) -> Path:
    PROCESSES_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slugify(f"{kind}-{Path(anchor_fp).stem}")
    out = PROCESSES_DIR / f"{slug}.md"
    if out.exists():
        existing = out.read_text(encoding="utf-8", errors="replace")
        if AUTO_TAG_MARKER not in existing[:300]:
            print(f"  · skipping {out.name}: file has manual edits")
            return out
    out.write_text(render_process_page(parsed, anchor_fp, sources), encoding="utf-8")
    return out


def log_run(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Top-level orchestration
# ─────────────────────────────────────────────────────────────────────────────
def analyze_one(topic: str, kind: str, max_sources: int, model: str | None,
                dry_run: bool, nodes: dict, edges: list) -> int:
    anchor_fp = find_anchor(nodes, topic)
    if not anchor_fp:
        print(f"ERROR: no concept/entity matched topic '{topic}'", file=sys.stderr)
        return 1

    sources = select_sources_for(anchor_fp, nodes, edges, max_sources)
    if len(sources) < 2:
        print(f"ERROR: only {len(sources)} sources connected to '{anchor_fp}' — need ≥2 to extract a process",
              file=sys.stderr)
        return 1

    sources_block = "\n\n".join(
        f"### [{i + 1}] `{s['stem']}` ({s['name']})\n\n{s['body']}"
        for i, s in enumerate(sources)
    )
    prompt = PROMPT_TEMPLATE.format(
        anchor=Path(anchor_fp).stem, kind=kind, kind_help=KIND_HELP[kind],
        n=len(sources), sources_block=sources_block,
    )

    print(f"  Anchor : {anchor_fp}  ({len(sources)} sources)")
    if dry_run:
        print(f"  (dry run — prompt is {len(prompt)} chars)")
        return 0

    chosen_model = model or getattr(config, "AI_MODEL", "claude-opus-5-thinking")
    print(f"  Calling {chosen_model}…")
    try:
        raw = get_ai_response(prompt, model=chosen_model, raise_on_error=True)
    except Exception as e:
        print(f"  ERROR: LLM call failed: {e}", file=sys.stderr)
        return 1

    parsed = _parse_llm_json(raw)
    if not parsed or not isinstance(parsed.get("steps"), list):
        print(f"  ERROR: could not parse LLM output as the expected JSON schema", file=sys.stderr)
        debug_path = LOG_PATH.parent / f"process_analyzer_failed_{_slugify(topic)}.txt"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(raw, encoding="utf-8")
        print(f"  raw response saved to {debug_path}")
        return 1

    out = write_process(parsed, anchor_fp, sources, kind)
    log_run({
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "topic": topic, "anchor": anchor_fp, "kind": kind,
        "model": chosen_model, "sources": [s["stem"] for s in sources],
        "n_steps": len(parsed.get("steps") or []), "output": str(out.relative_to(WIKI)),
    })
    print(f"  ✓ Wrote {out.relative_to(WIKI)}  ({len(parsed.get('steps') or [])} steps)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", help="Concept/entity name to anchor the process on")
    parser.add_argument("--kind", choices=["workflow", "pathway"], default="pathway",
                        help="What to extract: experimental workflow or biochemical pathway (default pathway)")
    parser.add_argument("--max-sources", type=int, default=MAX_SOURCES_DEFAULT,
                        help=f"Cap on source papers per process (default {MAX_SOURCES_DEFAULT})")
    parser.add_argument("--auto", type=int, metavar="N", default=0,
                        help="Auto-pick the top-N most-connected anchors instead of supplying --topic")
    parser.add_argument("--model", default=None, help="Override the AI model")
    parser.add_argument("--dry-run", action="store_true", help="Don't call the LLM; just print plans")
    args = parser.parse_args(argv)

    if not args.topic and not args.auto:
        parser.error("supply --topic <name> or --auto N")

    nodes, edges = load_graph()

    if args.auto:
        # Pick top-N anchors by outbound source count
        outbound = defaultdict(set)
        for s, t in edges:
            outbound[s].add(t)
        ranked = sorted(
            (fp for fp, n in nodes.items() if n["type"] in {"concept", "entity"}),
            key=lambda fp: -sum(1 for t in outbound.get(fp, set())
                                if nodes.get(t, {}).get("type") == "source"),
        )
        topics = [Path(fp).stem for fp in ranked[:args.auto]]
        print(f"Auto-selected {len(topics)} topics: {topics}")
        rc = 0
        for t in topics:
            print(f"\n--- {t} ---")
            rc |= analyze_one(t, args.kind, args.max_sources, args.model, args.dry_run, nodes, edges)
        return rc

    return analyze_one(args.topic, args.kind, args.max_sources, args.model, args.dry_run, nodes, edges)


if __name__ == "__main__":
    sys.exit(main())
