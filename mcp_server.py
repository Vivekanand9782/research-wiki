#!/usr/bin/env python3
"""
Research-Wiki MCP Server
Provides model context protocol tools to explore, search, and read 
the compiled Obsidian-style Plant Biology research wiki.
"""
import sys
import json
import os
import traceback

def log_debug(msg):
    """Log debugging messages to stderr (standard for MCP stdio)."""
    sys.stderr.write(f"[DEBUG] {msg}\n")
    sys.stderr.flush()

def send_response(req_id, result):
    """Send JSON-RPC result response."""
    response = {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result
    }
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def send_error(req_id, code, message, data=None):
    """Send JSON-RPC error response."""
    error_obj = {
        "code": code,
        "message": message
    }
    if data:
        error_obj["data"] = data
    response = {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": error_obj
    }
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

_search_engine = None

def get_search_engine(wiki_path):
    """Lazy-load and initialize the unified FullTextSearch engine."""
    global _search_engine
    if _search_engine is None:
        # Add script directory to sys.path to guarantee search import
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        from search import FullTextSearch
        _search_engine = FullTextSearch(wiki_folder=wiki_path)
        _search_engine.load_index()
    return _search_engine

def _within_wiki(wiki_path, candidate):
    """True when candidate resolves inside wiki_path (not merely prefixed by it)."""
    root = os.path.normpath(wiki_path)
    target = os.path.normpath(candidate)
    return target == root or target.startswith(root + os.sep)


def execute_tool(req_id, name, args, wiki_path):
    """Execute target MCP tool and return the output."""
    if name == "list_pages":
        category = args.get("category")
        limit = args.get("limit", 200)
        offset = args.get("offset", 0)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 2000:
            send_error(req_id, -32602, "'limit' must be an integer from 1 to 2000")
            return
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            send_error(req_id, -32602, "'offset' must be a non-negative integer")
            return
        pages = []

        target_dir = wiki_path
        if category:
            target_dir = os.path.join(wiki_path, category)
            if not os.path.exists(target_dir):
                send_response(req_id, {"content": [{"type": "text", "text": f"Category '{category}' does not exist."}]})
                return

        # Collect paths first: the corpus has 50k+ pages, so titles are only
        # read for the requested window instead of opening every file.
        relative_paths = []
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith(".md"):
                    relative_paths.append(
                        os.path.relpath(os.path.join(root, file), wiki_path)
                    )
        relative_paths.sort()
        window = relative_paths[offset : offset + limit]

        for rel_path in window:
            title = os.path.basename(rel_path)[:-3]
            try:
                with open(os.path.join(wiki_path, rel_path), "r", encoding="utf-8") as f:
                    for _ in range(15):
                        line = f.readline()
                        if not line:
                            break
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break
            except Exception:
                pass

            pages.append({
                "path": rel_path,
                "title": title,
                "category": rel_path.split(os.sep)[0] if os.sep in rel_path else "root"
            })

        send_response(req_id, {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "total_pages": len(relative_paths),
                            "offset": offset,
                            "limit": limit,
                            "returned": len(pages),
                            "truncated": offset + len(pages) < len(relative_paths),
                            "pages": pages,
                        },
                        indent=2,
                    ),
                }
            ]
        })
        return

    elif name == "read_page":
        rel_path = args.get("path")
        if not rel_path:
            send_error(req_id, -32602, "Missing parameter 'path'")
            return

        # Path traversal safety check
        safe_path = os.path.normpath(os.path.join(wiki_path, rel_path))
        if not _within_wiki(wiki_path, safe_path):
            send_error(req_id, -32602, "Access denied: Path is outside of wiki directory.")
            return
            
        if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
            send_response(req_id, {
                "isError": True,
                "content": [{"type": "text", "text": f"File not found at relative path: '{rel_path}'"}]
            })
            return
            
        try:
            with open(safe_path, "r", encoding="utf-8") as f:
                content = f.read()
            send_response(req_id, {
                "content": [
                    {
                        "type": "text",
                        "text": content
                    }
                ]
            })
        except Exception as e:
            send_error(req_id, -32603, f"Failed to read file: {str(e)}")
        return

    elif name == "search_wiki":
        query = args.get("query")
        if not isinstance(query, str) or not query.strip():
            send_error(req_id, -32602, "Missing parameter 'query'")
            return

        top_k = args.get("top_k", 15)
        mode = args.get("mode", "hybrid")
        doc_type = args.get("doc_type")
        include_stubs = args.get("include_stubs", False)
        exhaustive = args.get("exhaustive", False)
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 200:
            send_error(req_id, -32602, "'top_k' must be an integer from 1 to 200")
            return
        if mode not in {"summary", "hybrid", "evidence", "full_text"}:
            send_error(req_id, -32602, "'mode' must be summary, hybrid, or evidence")
            return
        if doc_type not in {None, "source", "paper", "entity", "concept", "synthesis"}:
            send_error(req_id, -32602, "Invalid 'doc_type' filter")
            return
        if not isinstance(include_stubs, bool) or not isinstance(exhaustive, bool):
            send_error(req_id, -32602, "'include_stubs' and 'exhaustive' must be booleans")
            return

        try:
            search_engine = get_search_engine(wiki_path)
            results = search_engine.search(
                query.strip(),
                top_k=top_k,
                mode=mode,
                doc_type=doc_type,
                include_stubs=include_stubs,
                exhaustive=exhaustive,
            )

            matches = []
            for result in results:
                metadata = search_engine.doc_metadata.get(result.paper, {})
                matches.append({
                    "document_id": result.paper,
                    "path": result.path or metadata.get("path", ""),
                    "file_name": metadata.get("legacy_stem", result.paper.rsplit("/", 1)[-1]),
                    "title": result.title,
                    "type": result.doc_type or metadata.get("type", ""),
                    "score": round(result.score, 6),
                    "section": result.section,
                    "source_path": result.source_path,
                    "line_start": result.line_start,
                    "line_end": result.line_end,
                    "evidence_quality": result.evidence_quality,
                    "quality_flags": result.quality_flags,
                    "matched_terms": result.matches,
                    "canonical_terms": result.canonical_terms,
                    # Preserve the historical snippets array while returning
                    # one explicitly provenance-linked best passage.
                    "snippets": [f"--- Evidence passage ---\n{result.snippet}"],
                })

            payload = {
                "query": query.strip(),
                "options": {
                    "top_k": top_k,
                    "mode": "evidence" if mode == "full_text" else mode,
                    "doc_type": doc_type,
                    "include_stubs": include_stubs,
                    "exhaustive": exhaustive,
                },
                "coverage": search_engine.last_search_report,
                "results": matches,
            }
            send_response(req_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(payload, indent=2),
                    }
                ]
            })
        except Exception as e:
            log_debug(f"Error in search_wiki tool: {e}\n{traceback.format_exc()}")
            send_error(req_id, -32603, f"Search failed: {str(e)}")
        return

    elif name == "get_wiki_summary":
        summary = {
            "total_pages": 0,
            "by_category": {}
        }
        
        categories = ["concepts", "entities", "sources", "synthesis"]
        for cat in categories:
            cat_dir = os.path.join(wiki_path, cat)
            if os.path.exists(cat_dir):
                count = 0
                for root, dirs, files in os.walk(cat_dir):
                    count += sum(1 for f in files if f.endswith(".md"))
                summary["by_category"][cat] = count
                summary["total_pages"] += count
            else:
                summary["by_category"][cat] = 0
                
        # Also check root-level index files
        summary["root_files"] = []
        if os.path.exists(wiki_path):
            for file in os.listdir(wiki_path):
                if os.path.isfile(os.path.join(wiki_path, file)) and file.endswith(".md"):
                    summary["root_files"].append(file)
                
        send_response(req_id, {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(summary, indent=2)
                }
            ]
        })
        return

    else:
        send_error(req_id, -32601, f"Tool execution failed: '{name}' not found")

def handle_request(req, wiki_path):
    """Parse and dispatch JSON-RPC request."""
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if not method:
        send_error(req_id, -32600, "Invalid Request: missing method")
        return

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "research-wiki-mcp",
                "version": "1.0.0"
            }
        }
        send_response(req_id, result)
        return

    if method == "notifications/initialized":
        return

    if method == "ping":
        send_response(req_id, {})
        return

    if method == "tools/list":
        tools = [
            {
                "name": "list_pages",
                "description": (
                    "List compiled pages (concepts, entities, sources, synthesis) in the "
                    "plant research wiki. Paginated: the corpus holds 50k+ pages, so the "
                    "response reports total_pages and returns one limit/offset window."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["concepts", "entities", "sources", "synthesis"],
                            "description": "Optional category filter. If omitted, lists all pages."
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 2000,
                            "default": 200,
                            "description": "Maximum pages to return in this window."
                        },
                        "offset": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "Number of pages to skip, for paging through the corpus."
                        }
                    }
                }
            },
            {
                "name": "read_page",
                "description": "Read the complete Markdown content and YAML metadata of a specific wiki page.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path of the page from the wiki root (e.g., 'concepts/base-editing.md', 'sources/bioethanol/paper1.md')."
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "search_wiki",
                "description": (
                    "Search compiled ResearchWiki pages or source-linked raw-paper passages "
                    "with BM25 ranking, evidence-quality flags, exact section/line provenance, "
                    "canonical aliases, and measured corpus coverage."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Research question, entity name, or phrase."
                        },
                        "top_k": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 200,
                            "default": 15,
                            "description": "Maximum results unless exhaustive=true."
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["summary", "hybrid", "evidence"],
                            "default": "hybrid",
                            "description": (
                                "summary searches compiled pages; hybrid reranks linked raw text; "
                                "evidence scans every raw paper and returns its best passage."
                            )
                        },
                        "doc_type": {
                            "type": "string",
                            "enum": ["source", "paper", "entity", "concept", "synthesis"],
                            "description": "Optional document-type filter; source is an alias for paper."
                        },
                        "include_stubs": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include low-information/generated placeholders."
                        },
                        "exhaustive": {
                            "type": "boolean",
                            "default": False,
                            "description": (
                                "Return every positive match and remove candidate caps. In hybrid mode, "
                                "also scan raw papers missed by summary retrieval."
                            )
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_wiki_summary",
                "description": "Get a bird's-eye view of the entire wiki directory, including total page counts per category.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        send_response(req_id, {"tools": tools})
        return

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            send_error(req_id, -32602, "Invalid params: missing tool name")
            return

        try:
            execute_tool(req_id, tool_name, arguments, wiki_path)
        except Exception as e:
            send_error(req_id, -32603, f"Internal error executing tool '{tool_name}': {str(e)}", data=traceback.format_exc())
        return

    send_error(req_id, -32601, f"Method not found: '{method}'")

def main():
    log_debug("Starting Research-Wiki MCP Server...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wiki_path = os.path.join(script_dir, "wiki")
    log_debug(f"Wiki directory path: {wiki_path}")

    # Set binary translation modes for stdio to ensure clean JSON-RPC line endings across platforms
    if sys.platform == "win32":
        import msvcrt
        import os as win_os
        msvcrt.setmode(sys.stdin.fileno(), win_os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), win_os.O_BINARY)

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                send_error(None, -32700, f"Parse error: {str(e)}")
                continue

            handle_request(request, wiki_path)

        except KeyboardInterrupt:
            break
        except Exception as e:
            log_debug(f"Main loop exception: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
