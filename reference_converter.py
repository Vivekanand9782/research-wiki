"""reference_converter.py — deterministic reference formatting (no GenAI).

Resolves metadata via Zotero local API or OpenAlex, then formats references
into either "Circular Agricultural Systems" journal style or RIS (Zotero).
"""

import argparse
import sys
import re
from paper_metadata import extract_doi_from_text, resolve_metadata, fetch_bibtex_from_doi, bibtex_to_ris, parse_bibtex_to_dict, format_journal_style

# ---------------------------------------------------------------------------
# Reference splitting
# ---------------------------------------------------------------------------

# Patterns that separate numbered/anonymous references
REF_SPLIT_RE = re.compile(r"(?:\n\s*(?:\d+[.)]\s*|\[?\d+\]?\s*))")


def _split_references(raw_text: str) -> list[str]:
    """Split a block of references into individual reference strings."""
    text = raw_text.strip()
    if not text:
        return []

    # Try splitting on numbered patterns first
    parts = REF_SPLIT_RE.split(text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) > 1:
        return parts

    # Fallback: split on blank lines
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if parts:
        return parts

    return [text]


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


def _raw_ref_to_ris(raw_ref: str) -> str:
    """Convert a single raw reference to RIS, trying BibTeX or resolved metadata."""
    doi = extract_doi_from_text(raw_ref)
    if doi:
        # Prefer BibTeX — it's the most complete format
        bibtex = fetch_bibtex_from_doi(doi)
        if bibtex:
            parsed = parse_bibtex_to_dict(bibtex)
            return bibtex_to_ris(parsed)

        # Fallback: resolve metadata from Zotero/OpenAlex
        meta = resolve_metadata(doi)
        if meta:
            return _metadata_to_ris(meta)

    # Last resort: minimal RIS from raw text
    return _fallback_ris(raw_ref)


def _metadata_to_ris(meta: dict) -> str:
    """Build RIS from resolved metadata dict."""
    lines = ["TY  - JOUR"]
    for a in meta.get("authors") or []:
        # "Last, F." → "Last, Firstname"
        lines.append(f"AU  - {a}")
    if meta.get("title"):
        lines.append(f"TI  - {meta['title']}")
    if meta.get("journal"):
        lines.append(f"T2  - {meta['journal']}")
    if meta.get("year"):
        lines.append(f"PY  - {meta['year']}")
    if meta.get("doi"):
        lines.append(f"DO  - {meta['doi']}")
    lines.append("ER  - ")
    return "\n".join(lines)


def _fallback_ris(raw_ref: str) -> str:
    """Minimal RIS from raw text when no DOI found."""
    lines = ["TY  - JOUR"]
    lines.append(f"TI  - {raw_ref}")
    lines.append("ER  - ")
    return "\n".join(lines)


def _raw_ref_to_text(raw_ref: str, index: int = 1) -> str:
    """Convert a single raw reference to journal-style text."""
    doi = extract_doi_from_text(raw_ref)
    if doi:
        meta = resolve_metadata(doi)
        if meta:
            return format_journal_style(meta, index=index)

    # No DOI resolved — return the raw text prefixed with a placeholder number
    return f"[{index}] {raw_ref}"


RAW_REF_TITLE_RE = re.compile(r"(?:^|\s)\d{4}[.)]\s*(.*)")

def convert_references(raw_text: str, mode: str) -> str:
    """Convert raw references to the target format."""
    refs = _split_references(raw_text)

    if mode == "ris":
        results = [_raw_ref_to_ris(r) for r in refs]
        return "\n\n".join(results)
    else:
        results = [_raw_ref_to_text(r, i + 1) for i, r in enumerate(refs)]
        return "\n".join(results)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Convert references to a specific journal style or RIS (offline)."
    )
    parser.add_argument(
        "input", nargs="?", help="A string containing the reference(s) to convert."
    )
    parser.add_argument(
        "-f", "--file", help="Path to a text file containing raw references."
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["text", "ris"],
        default="text",
        help="Output mode: 'text' for journal formatting, 'ris' for Zotero import.",
    )
    args = parser.parse_args()

    raw_text = ""
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                raw_text = f.read().strip()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.input:
        raw_text = args.input.strip()
    else:
        raw_text = sys.stdin.read().strip()

    if not raw_text:
        print("No input provided. Exiting.", file=sys.stderr)
        sys.exit(1)

    converted = convert_references(raw_text, args.mode)
    print(converted)


if __name__ == "__main__":
    main()
