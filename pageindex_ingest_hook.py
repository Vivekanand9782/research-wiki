#!/usr/bin/env python3
"""
PageIndex Ingestion Hook
========================
Provides seamless synchronization between Local RAG and PageIndex:
- Parses new PDFs or Markdown papers into hierarchical tree structures.
- Persists trees to `PageIndex/extracted_trees/<stem>.tree.json`.
- Synchronizes raw markdown to `PageIndex/extracted_mds/<stem>.md`.
- Atomically updates `PageIndex/indexed_manifest.json` with file-locking safety.
- 100% offline, zero-cloud dependency, fast PyMuPDF AST parsing.
- Safe failure isolation: errors never block or crash core Local RAG ingestion.

Usage:
    # Python API:
    from pageindex_ingest_hook import hook_pageindex_index
    result = hook_pageindex_index(pdf_path, md_path)

    # Standalone CLI:
    python3 pageindex_ingest_hook.py <path_to_pdf_or_md>
    python3 pageindex_ingest_hook.py --sync-all-raw
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


# Locate workspace root dynamically
def _get_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    if (current / "PageIndex").is_dir():
        return current
    if (current.parent / "PageIndex").is_dir():
        return current.parent
    # Fallback to current working directory
    cwd = Path.cwd().resolve()
    if (cwd / "PageIndex").is_dir():
        return cwd
    return current.parent


REPO_ROOT = _get_repo_root()
PAGEINDEX_DIR = REPO_ROOT / "PageIndex"
TREES_DIR = PAGEINDEX_DIR / "extracted_trees"
MDS_DIR = PAGEINDEX_DIR / "extracted_mds"
MANIFEST_FILE = PAGEINDEX_DIR / "indexed_manifest.json"
LOCK_FILE = PAGEINDEX_DIR / "indexed_manifest.json.lock"

# Ensure directories exist
TREES_DIR.mkdir(parents=True, exist_ok=True)
MDS_DIR.mkdir(parents=True, exist_ok=True)


class ManifestLock:
    """Process-safe file lock for manifest reading and writing."""
    def __init__(self):
        self.lock_path = LOCK_FILE
        self.f = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(self.lock_path, "w", encoding="utf-8")
        fcntl.flock(self.f, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.f:
                fcntl.flock(self.f, fcntl.LOCK_UN)
                self.f.close()
        except Exception:
            pass


def load_manifest() -> dict:
    """Load the manifest safely from disk."""
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"indexed": {}, "failed": {}}
    return {"indexed": {}, "failed": {}}


def save_manifest_atomic(manifest: dict) -> None:
    """Save the manifest atomically using a temp file and rename."""
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = MANIFEST_FILE.parent / f".tmp_{os.getpid()}_{int(time.time() * 1000)}.json"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, MANIFEST_FILE)
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


def is_valid_pdf(path: Path) -> bool:
    """Check if file has valid %PDF- header."""
    try:
        with open(path, "rb") as f:
            header = f.read(1024)
            return b"%PDF-" in header
    except Exception:
        return False


def _clean_title(title: str) -> str:
    cleaned = re.sub(r'[*_#`]+', '', title).strip()
    return re.sub(r'\s+', ' ', cleaned)


def parse_pdf_to_tree(pdf_path: Path) -> dict:
    """Parse a PDF into hierarchical section & page nodes and write tree JSON."""
    stem = pdf_path.stem
    name = pdf_path.name

    if not is_valid_pdf(pdf_path):
        return {
            "status": "failed",
            "name": name,
            "error": "File does not contain valid %PDF- header",
        }

    if fitz is None:
        return {
            "status": "failed",
            "name": name,
            "error": "PyMuPDF (fitz) is not installed",
        }

    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        if page_count == 0:
            return {
                "status": "failed",
                "name": name,
                "error": "Document contains 0 pages",
            }

        nodes = []
        node_counter = 0
        heading_re = re.compile(
            r"^(\d+(\.\d+)*\s+[A-Z][A-Za-z0-9\s,\-]{2,60}|[A-Z][A-Z\s,\-]{3,50})$",
            re.MULTILINE,
        )

        total_text_chars = 0

        for p_idx, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            total_text_chars += len(text)
            if not text:
                continue

            lines = text.split("\n")
            current_title = f"Page {p_idx}"
            node_text_buf = []

            for line in lines:
                line_str = line.strip()
                if heading_re.match(line_str) and len(line_str.split()) < 10:
                    if node_text_buf:
                        nodes.append({
                            "node_id": f"{node_counter:04d}",
                            "title": _clean_title(current_title),
                            "page_index": p_idx,
                            "text": "\n".join(node_text_buf)[:2500],
                        })
                        node_counter += 1
                        node_text_buf = []
                    current_title = line_str
                else:
                    node_text_buf.append(line_str)

            if node_text_buf:
                nodes.append({
                    "node_id": f"{node_counter:04d}",
                    "title": _clean_title(current_title),
                    "page_index": p_idx,
                    "text": "\n".join(node_text_buf)[:2500],
                })
                node_counter += 1

        # Fallback if no headings matched
        if not nodes:
            for p_idx, page in enumerate(doc, 1):
                t = page.get_text("text").strip()
                if t:
                    nodes.append({
                        "node_id": f"{p_idx-1:04d}",
                        "title": f"Page {p_idx}",
                        "page_index": p_idx,
                        "text": t[:2500],
                    })

        doc_id = f"pi-local-{stem[:32]}"
        tree_payload = {
            "doc_id": doc_id,
            "name": name,
            "pageNum": page_count,
            "char_count": total_text_chars,
            "status": "completed",
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tree": {
                "doc_id": doc_id,
                "status": "completed",
                "retrieval_ready": True,
                "result": nodes,
            },
        }

        # Write tree file
        out_file = TREES_DIR / f"{stem}.tree.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(tree_payload, f, indent=2, ensure_ascii=False)

        return {
            "status": "completed",
            "name": name,
            "doc_id": doc_id,
            "pages": page_count,
            "nodes": len(nodes),
            "chars": total_text_chars,
            "tree_file": str(out_file.relative_to(REPO_ROOT)),
        }

    except Exception as e:
        return {
            "status": "failed",
            "name": name,
            "error": str(e),
        }


def parse_markdown_to_tree(md_path: Path, doc_name: str | None = None) -> dict:
    """Parse a pure Markdown document into hierarchical section nodes and write tree JSON."""
    stem = md_path.stem
    name = doc_name or f"{stem}.md"

    try:
        content = md_path.read_text(encoding="utf-8")
        if not content or len(content.strip()) < 50:
            return {
                "status": "failed",
                "name": name,
                "error": "Markdown file is empty or trivially short",
            }

        lines = content.splitlines()
        header_re = re.compile(r"^(#{1,6})\s+(.+)$")
        code_block_re = re.compile(r"^```")

        nodes = []
        node_counter = 0
        in_code_block = False
        current_title = "Introduction"
        node_text_buf = []

        for line_idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if code_block_re.match(stripped):
                in_code_block = not in_code_block

            if not in_code_block and header_re.match(stripped):
                hm = header_re.match(stripped)
                title = _clean_title(hm.group(2))
                if node_text_buf:
                    nodes.append({
                        "node_id": f"{node_counter:04d}",
                        "title": current_title,
                        "page_index": max(1, (node_counter // 2) + 1),
                        "text": "\n".join(node_text_buf)[:2500],
                    })
                    node_counter += 1
                    node_text_buf = []
                current_title = title
            else:
                if stripped:
                    node_text_buf.append(stripped)

        if node_text_buf:
            nodes.append({
                "node_id": f"{node_counter:04d}",
                "title": current_title,
                "page_index": max(1, (node_counter // 2) + 1),
                "text": "\n".join(node_text_buf)[:2500],
            })
            node_counter += 1

        # Fallback if no headers were found
        if not nodes:
            chunk_size = 2000
            for i in range(0, len(content), chunk_size):
                chunk = content[i : i + chunk_size]
                nodes.append({
                    "node_id": f"{node_counter:04d}",
                    "title": f"Section {node_counter + 1}",
                    "page_index": node_counter + 1,
                    "text": chunk.strip(),
                })
                node_counter += 1

        doc_id = f"pi-local-{stem[:32]}"
        est_pages = max(1, (len(nodes) + 1) // 2)
        total_chars = len(content)

        tree_payload = {
            "doc_id": doc_id,
            "name": name,
            "pageNum": est_pages,
            "char_count": total_chars,
            "status": "completed",
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tree": {
                "doc_id": doc_id,
                "status": "completed",
                "retrieval_ready": True,
                "result": nodes,
            },
        }

        # Write tree file
        out_file = TREES_DIR / f"{stem}.tree.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(tree_payload, f, indent=2, ensure_ascii=False)

        return {
            "status": "completed",
            "name": name,
            "doc_id": doc_id,
            "pages": est_pages,
            "nodes": len(nodes),
            "chars": total_chars,
            "tree_file": str(out_file.relative_to(REPO_ROOT)),
        }

    except Exception as e:
        return {
            "status": "failed",
            "name": name,
            "error": str(e),
        }


def hook_pageindex_index(
    file_path: Path | str,
    md_path: Path | str | None = None,
    force: bool = False,
) -> dict:
    """
    Main hook function.
    Safely indexes a PDF or Markdown paper into PageIndex:
    - Generates PageIndex hierarchical tree JSON.
    - Synchronizes markdown into PageIndex/extracted_mds/.
    - Atomically updates PageIndex/indexed_manifest.json.
    - Never raises: catches all errors and records failures safely.
    """
    try:
        path = Path(file_path).resolve()
        stem = path.stem
        ext = path.suffix.lower()

        # Check if corresponding tree already exists
        tree_file = TREES_DIR / f"{stem}.tree.json"
        rel_tree = str(tree_file.relative_to(REPO_ROOT))

        # Check manifest under lock
        with ManifestLock():
            manifest = load_manifest()
            indexed_entry = manifest.get("indexed", {}).get(path.name) or manifest.get("indexed", {}).get(f"{stem}.pdf") or manifest.get("indexed", {}).get(f"{stem}.md")
            if not force and indexed_entry and tree_file.exists():
                return {
                    "status": "already_indexed",
                    "name": path.name,
                    "tree_file": rel_tree,
                    "doc_id": indexed_entry.get("doc_id"),
                }

        # Sync markdown file if present
        target_md = MDS_DIR / f"{stem}.md"
        source_md = Path(md_path).resolve() if md_path else None
        if source_md and source_md.exists() and not target_md.exists():
            try:
                import shutil
                shutil.copy2(source_md, target_md)
            except Exception:
                pass

        # Perform parsing based on file type
        if ext == ".pdf":
            result = parse_pdf_to_tree(path)
        elif ext in [".md", ".markdown", ".txt"]:
            result = parse_markdown_to_tree(path)
        elif source_md and source_md.exists():
            # If path was not PDF/MD but a valid markdown was provided
            result = parse_markdown_to_tree(source_md, doc_name=f"{stem}.md")
        else:
            return {
                "status": "failed",
                "name": path.name,
                "error": f"Unsupported file extension '{ext}' and no markdown provided",
            }

        # Atomically update manifest
        with ManifestLock():
            manifest = load_manifest()
            manifest_key = path.name

            if result.get("status") == "completed":
                manifest.setdefault("indexed", {})[manifest_key] = {
                    "doc_id": result["doc_id"],
                    "pages": result.get("pages", 1),
                    "nodes": result.get("nodes", 0),
                    "chars": result.get("chars", 0),
                    "tree_file": result["tree_file"],
                    "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                # Remove from failed if present
                manifest.get("failed", {}).pop(manifest_key, None)
                save_manifest_atomic(manifest)
            else:
                manifest.setdefault("failed", {})[manifest_key] = {
                    "error": result.get("error", "unknown error"),
                    "failed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                save_manifest_atomic(manifest)

        return result

    except Exception as e:
        # Ultimate fail-safe: never crash the caller
        err_msg = f"PageIndex hook exception: {e}"
        print(f"  └─ ⚠️  {err_msg}")
        return {
            "status": "failed",
            "name": str(file_path),
            "error": err_msg,
        }


def sync_all_raw_papers(limit: int | None = None) -> None:
    """Backfill PageIndex trees for any raw markdown papers that don't have trees yet."""
    raw_dir = REPO_ROOT / "research-wiki" / "raw" / "papers"
    if not raw_dir.is_dir():
        print(f"Raw papers directory not found: {raw_dir}")
        return

    md_files = sorted(raw_dir.rglob("*.md"))
    print(f"Found {len(md_files):,} raw markdown papers in {raw_dir}")

    manifest = load_manifest()
    indexed = manifest.get("indexed", {})

    to_process = []
    for md in md_files:
        stem = md.stem
        # Check if already indexed as .pdf or .md or tree exists
        tree_file = TREES_DIR / f"{stem}.tree.json"
        if not tree_file.exists():
            to_process.append(md)

    print(f"Papers without PageIndex trees: {len(to_process):,}")
    if limit:
        to_process = to_process[:limit]
        print(f"Limiting to first {limit} papers")

    success = 0
    fail = 0
    for idx, md in enumerate(to_process, 1):
        res = hook_pageindex_index(md)
        if res.get("status") in ["completed", "already_indexed"]:
            success += 1
            if idx % 100 == 0 or idx == len(to_process):
                print(f"  [{idx:>4}/{len(to_process)}] Indexed {md.name} (nodes: {res.get('nodes', 'N/A')})")
        else:
            fail += 1
            print(f"  [{idx:>4}/{len(to_process)}] Failed {md.name}: {res.get('error')}")

    print(f"\nSync complete. Successfully indexed: {success:,}, Failed: {fail:,}")


def main():
    parser = argparse.ArgumentParser(description="PageIndex Ingestion Hook")
    parser.add_argument("path", nargs="?", help="Path to PDF or Markdown file to index")
    parser.add_argument("--sync-all-raw", action="store_true", help="Sync all raw markdown papers without trees")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of papers for sync")
    parser.add_argument("--force", action="store_true", help="Force re-indexing even if already indexed")
    args = parser.parse_args()

    if args.sync_all_raw:
        sync_all_raw_papers(limit=args.limit)
    elif args.path:
        p = Path(args.path)
        if not p.exists():
            print(f"Error: File not found: {p}")
            sys.exit(1)
        res = hook_pageindex_index(p, force=args.force)
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
