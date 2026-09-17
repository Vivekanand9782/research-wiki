"""paper_metadata.py — extract DOIs and resolve paper metadata without GenAI.

Resolution chain:
  1. OpenAlex API (free, no auth)
  2. Returns None if it fails
"""

from __future__ import annotations
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# DOI extraction
# ---------------------------------------------------------------------------

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)


def _clean_doi_candidate(value: str) -> str | None:
    """Extract one DOI and remove surrounding prose/markup punctuation."""
    match = DOI_RE.search(value or "")
    if not match:
        return None
    candidate = match.group(1).rstrip(".,;:!?]}>\"'")
    # Keep balanced parentheses that are part of a DOI, but discard unmatched
    # closing punctuation introduced by prose such as ``(doi: 10.x/y)``.
    while candidate.endswith(")") and candidate.count(")") > candidate.count("("):
        candidate = candidate[:-1]
    return candidate or None


def extract_doi_from_text(text: str) -> str | None:
    """Pull the first clean DOI from a block of text."""
    return _clean_doi_candidate(text)


def extract_doi_from_pdf(pdf_path: str | Path) -> str | None:
    """Extract DOI from a PDF — checks metadata dict first, then scans page text."""
    import pymupdf  # lazy import so the module can be imported without the dep

    doc = pymupdf.open(pdf_path)
    try:
        # 1. PDF info dict sometimes carries a DOI.
        meta = doc.metadata or {}
        doi = _clean_doi_candidate(meta.get("doi", "") or meta.get("subject", ""))
        if doi:
            return doi

        # 2. Scan first 3 pages for a DOI string.
        text = "".join(doc[i].get_text() for i in range(min(3, len(doc))))
        return _clean_doi_candidate(text)
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Metadata resolution
# ---------------------------------------------------------------------------

def _fetch_openalex(doi: str, max_retries: int = 3) -> dict | None:
    """Query OpenAlex with verified TLS and bounded transient retries."""
    doi_clean = _clean_doi_candidate(doi)
    if not doi_clean:
        return None
    encoded_doi = urllib.parse.quote(doi_clean, safe="/")
    url = f"https://api.openalex.org/works/https://doi.org/{encoded_doi}"
    email = os.environ.get("DEFAULT_EMAIL", "").strip()
    user_agent = "ResearchWiki/1.0"
    if email:
        user_agent += f" (mailto:{email})"

    data: dict[str, Any] | None = None
    for attempt in range(max(1, max_retries)):
        delay = min(8.0, 1.0 * (2**attempt))
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": user_agent},
            )
            # Do not pass an unverified SSL context: Python's default context
            # validates both the certificate chain and hostname.
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
            if not raw.strip():
                raise ValueError("empty OpenAlex response")
            decoded = json.loads(raw.decode("utf-8"))
            if not isinstance(decoded, dict):
                raise ValueError("OpenAlex response was not a JSON object")
            data = decoded
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                return None
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = min(30.0, max(0.0, float(retry_after)))
            except (TypeError, ValueError):
                pass
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError,
                json.JSONDecodeError, ValueError):
            pass

        if attempt < max(1, max_retries) - 1:
            time.sleep(delay)

    if data is None:
        return None

    authors: list[str] = []
    for authorship in data.get("authorships") or []:
        name = (authorship.get("author") or {}).get("display_name", "")
        if name:
            parts = name.split()
            if len(parts) > 1:
                authors.append(f"{parts[-1]}, {parts[0][0]}.")
            else:
                authors.append(name)

    location = data.get("primary_location") or {}
    source = location.get("source") or {}
    doi_out = _clean_doi_candidate(str(data.get("doi") or "")) or doi_clean

    return {
        "authors": authors,
        "year": data.get("publication_year"),
        "title": data.get("title"),
        "journal": source.get("display_name", ""),
        "doi": doi_out,
        "source": "openalex",
    }


def resolve_metadata(doi: str) -> dict | None:
    """Resolve paper metadata from OpenAlex."""
    return _fetch_openalex(doi)


# ---------------------------------------------------------------------------
# BibTeX fetching
# ---------------------------------------------------------------------------

BIBTEX_ACCEPT = "application/x-bibtex"

BIBTEX_FIELD_RE = re.compile(r"^\s*(\w+)\s*=\s*\{(.+?)\}", re.MULTILINE | re.DOTALL)
BIBTEX_TYPE_RE = re.compile(r"@(\w+)\{")

# Author-formatting rules for journal style
AUTHOR_LIMIT = 6  # 6+ → first 5 + et al.


def fetch_bibtex_from_doi(doi: str, max_retries: int = 3) -> str | None:
    """Fetch BibTeX from doi.org."""
    doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    url = f"https://doi.org/{doi_clean}"

    req = urllib.request.Request(url)
    req.add_header("Accept", BIBTEX_ACCEPT)
    ctx = ssl._create_unverified_context()

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                return resp.read().decode("utf-8").strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep((attempt + 1) * 2)
                continue
            break
        except Exception:
            time.sleep(1)
    return None


def parse_bibtex_to_dict(bibtex: str) -> dict[str, Any]:
    """Minimal BibTeX parser — extracts entry type + field key-value pairs."""
    type_m = BIBTEX_TYPE_RE.search(bibtex)
    entry_type = type_m.group(1).lower() if type_m else "article"

    fields: dict[str, str] = {}
    for m in BIBTEX_FIELD_RE.finditer(bibtex):
        fields[m.group(1).lower()] = m.group(2).strip()

    return {"type": entry_type, **fields}


def bibtex_to_ris(bib: dict[str, Any]) -> str:
    """Convert parsed BibTeX dict to RIS format."""
    ty_map = {
        "article": "JOUR",
        "book": "BOOK",
        "inbook": "CHAP",
        "incollection": "CHAP",
        "inproceedings": "CONF",
        "proceedings": "CONF",
        "phdthesis": "THES",
        "mastersthesis": "THES",
        "techreport": "RPT",
        "misc": "GEN",
    }
    lines: list[str] = []
    lines.append(f"TY  - {ty_map.get(bib.get('type', ''), 'JOUR')}")

    author_str = bib.get("author", "")
    for a in _split_authors_bibtex(author_str):
        lines.append(f"AU  - {a}")

    if bib.get("title"):
        lines.append(f"TI  - {bib['title']}")
    if bib.get("journal"):
        lines.append(f"T2  - {bib['journal']}")
    if bib.get("booktitle"):
        lines.append(f"T2  - {bib['booktitle']}")
    if bib.get("year"):
        lines.append(f"PY  - {bib['year']}")
    if bib.get("volume"):
        lines.append(f"VL  - {bib['volume']}")
    if bib.get("number"):
        lines.append(f"IS  - {bib['number']}")
    pages = bib.get("pages", "")
    if pages:
        m = re.match(r"(\d+)\s*--?\s*(\d+)", pages)
        if m:
            lines.append(f"SP  - {m.group(1)}")
            lines.append(f"EP  - {m.group(2)}")
        else:
            lines.append(f"SP  - {pages}")
    if bib.get("publisher"):
        lines.append(f"PB  - {bib['publisher']}")
    if bib.get("address"):
        lines.append(f"CY  - {bib['address']}")
    if bib.get("doi"):
        lines.append(f"DO  - {bib['doi']}")
    elif bib.get("url"):
        lines.append(f"UR  - {bib['url']}")

    lines.append("ER  - ")
    return "\n".join(lines)


def _split_authors_bibtex(author_field: str) -> list[str]:
    """Parse BibTeX author field into list of 'Lastname, Firstname' strings."""
    if not author_field:
        return []

    # BibTeX authors separated by " and "
    parts = re.split(r"\s+and\s+", author_field)
    result: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue

        # Try "Last, First" or "Last, First Middle"
        if "," in p:
            last, first = p.split(",", 1)
            result.append(f"{last.strip()}, {first.strip()}")
        else:
            # Try "First Last"
            pieces = p.split()
            if len(pieces) >= 2:
                result.append(f"{pieces[-1]}, {' '.join(pieces[:-1])}")
            else:
                result.append(p)
    return result


# ---------------------------------------------------------------------------
# Journal-style formatting (Circular Agricultural Systems)
# ---------------------------------------------------------------------------

def format_journal_style(meta: dict, index: int = 1) -> str:
    """Format metadata into Circular Agricultural Systems journal style.

    - [1] Last F, Last F, …, et al. YYYY. Title. Journal. Volume:Pages. http://doi.org/xxxxx
    """
    authors = meta.get("authors") or []
    year = meta.get("year", "")
    title = meta.get("title", "")
    journal = meta.get("journal", "")
    doi = meta.get("doi", "")

    # Authors
    formatted_authors: list[str] = []
    for a in authors:
        # Already in "Last, F." format from resolvers
        formatted_authors.append(a)

    if len(formatted_authors) >= AUTHOR_LIMIT:
        author_str = ", ".join(formatted_authors[:5]) + ", et al."
    elif len(formatted_authors) > 1:
        author_str = ", ".join(formatted_authors[:-1]) + ", " + formatted_authors[-1]
    elif formatted_authors:
        author_str = formatted_authors[0]
    else:
        author_str = "Unknown"

    # DOI
    doi_str = ""
    if doi:
        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        doi_str = f" http://doi.org/{doi_clean}"

    return f"[{index}] {author_str.rstrip('.')}. {year}. {title}. {journal}.{doi_str}"
