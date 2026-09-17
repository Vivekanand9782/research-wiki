"""resummarize_queue.py — Centralized state and queue manager for swarm summarization."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

STATE_FILE = Path(__file__).resolve().parent.parent / "resummarize_state.json"
RAW_DIR = Path(__file__).resolve().parent.parent / "raw" / "papers"
WIKI_DIR = Path(__file__).resolve().parent.parent / "wiki" / "sources" / "uncategorized"


def init_state() -> dict:
    all_raw = {}
    for p in RAW_DIR.rglob("*.md"):
        topic = p.parent.name if p.parent != RAW_DIR else "uncategorized"
        all_raw[p.stem] = {
            "stem": p.stem,
            "topic": topic,
            "raw_path": str(p.relative_to(RAW_DIR.parent.parent)),
            "status": "pending",
            "worker": None,
            "score": None,
            "error": None,
        }

    # Check already completed
    for stem, info in all_raw.items():
        dest = WIKI_DIR / f"{stem}.md"
        if dest.exists():
            try:
                txt = dest.read_text(encoding="utf-8", errors="ignore")
                if "date_created: 2026-08-16" in txt or "date_updated: 2026-08-16" in txt:
                    info["status"] = "done"
                    info["score"] = 100
            except Exception:
                pass

    state = {
        "total": len(all_raw),
        "papers": all_raw,
    }
    save_state(state)
    return state


def load_state() -> dict:
    if not STATE_FILE.exists():
        return init_state()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return init_state()


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_next_batch(worker_id: str, topic: Optional[str] = None, limit: int = 15) -> List[dict]:
    state = load_state()
    batch = []
    for stem, info in state["papers"].items():
        if info["status"] == "pending":
            if topic and info["topic"] != topic:
                continue
            info["status"] = "in_progress"
            info["worker"] = worker_id
            batch.append(info)
            if len(batch) >= limit:
                break
    save_state(state)
    return batch


def mark_done(stem: str, worker_id: str, score: int = 100) -> None:
    state = load_state()
    if stem in state["papers"]:
        state["papers"][stem]["status"] = "done"
        state["papers"][stem]["worker"] = worker_id
        state["papers"][stem]["score"] = score
        state["papers"][stem]["error"] = None
        save_state(state)


def mark_failed(stem: str, worker_id: str, error: str) -> None:
    state = load_state()
    if stem in state["papers"]:
        state["papers"][stem]["status"] = "failed"
        state["papers"][stem]["worker"] = worker_id
        state["papers"][stem]["error"] = error
        save_state(state)


def print_status() -> None:
    state = load_state()
    papers = state["papers"]
    done = sum(1 for p in papers.values() if p["status"] == "done")
    in_prog = sum(1 for p in papers.values() if p["status"] == "in_progress")
    pending = sum(1 for p in papers.values() if p["status"] == "pending")
    failed = sum(1 for p in papers.values() if p["status"] == "failed")
    
    topics = {}
    for p in papers.values():
        t = p["topic"]
        if t not in topics:
            topics[t] = {"total": 0, "done": 0}
        topics[t]["total"] += 1
        if p["status"] == "done":
            topics[t]["done"] += 1

    print(f"=== Swarm Re-summarization Progress ===")
    print(f"Total Papers : {len(papers)}")
    print(f"Completed    : {done} ({done / len(papers) * 100:.1f}%)")
    print(f"In Progress  : {in_prog}")
    print(f"Pending      : {pending}")
    print(f"Failed       : {failed}")
    print("\nTopic Breakdown:")
    for t, counts in sorted(topics.items()):
        pct = counts["done"] / counts["total"] * 100 if counts["total"] else 0
        print(f"  - {t:<30}: {counts['done']:>4}/{counts['total']:<4} ({pct:.1f}%)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_state()
    print_status()
