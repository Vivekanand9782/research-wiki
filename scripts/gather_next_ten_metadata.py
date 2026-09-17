import os
import urllib.request
import json
import re
import urllib.parse
from pathlib import Path

RAW_DIR = Path("raw/papers/uncategorized")
metadata_file = Path("raw/next_ten_papers_metadata.json")

# Slice from 10 to 20
files = sorted(f for f in os.listdir(RAW_DIR) if f.endswith(".md") and not f.startswith("."))[10:20]

results = {}

def get_actual_title(text):
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()
        if len(line) > 30 and not line.startswith("Can.") and not line.startswith("Received"):
            return line
    return None

def extract_doi_from_text(text):
    m = re.search(r"\b(10\.\d{4,9}/[^\s\)\]>,]+)", text, re.IGNORECASE)
    if m:
        return m.group(1).rstrip(".,;()[]")
    return None

for f in files:
    path = RAW_DIR / f
    text = path.read_text(encoding="utf-8")
    
    title = get_actual_title(text) or f.replace(".md", "")
    doi = extract_doi_from_text(text[:2000])
    
    # Try searching OpenAlex with title or DOI
    if doi:
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    else:
        query = urllib.parse.quote(title[:120])
        url = f"https://api.openalex.org/works?filter=title.search:{query}"
        
    print(f"Searching: {title} | DOI: {doi}")
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mailto:research-wiki@example.com"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            
            if doi:
                best = data
            else:
                results_list = data.get("results", [])
                best = results_list[0] if results_list else None
                
            if best:
                authors = []
                for a in best.get("authorships", []):
                    name = a.get("author", {}).get("display_name", "")
                    if name:
                        authors.append(name)
                
                results[f] = {
                    "title": best.get("title"),
                    "doi": best.get("doi", "").replace("https://doi.org/", ""),
                    "authors": authors,
                    "year": best.get("publication_year"),
                    "journal": (best.get("primary_location") or {}).get("source", {}).get("display_name"),
                    "paper_slug": re.sub(r"[^a-zA-Z0-9]+", "-", f.replace(".md", "")).strip("-").lower()
                }
                print(f"  Found: {best.get('title')} ({best.get('doi')})")
            else:
                results[f] = {
                    "title": title,
                    "doi": doi,
                    "authors": [],
                    "year": 1980, # default/guess
                    "journal": None,
                    "paper_slug": re.sub(r"[^a-zA-Z0-9]+", "-", f.replace(".md", "")).strip("-").lower()
                }
    except Exception as e:
        print(f"  Error: {e}")
        results[f] = {
            "title": title,
            "doi": doi,
            "authors": [],
            "year": 1980,
            "journal": None,
            "paper_slug": re.sub(r"[^a-zA-Z0-9]+", "-", f.replace(".md", "")).strip("-").lower()
        }

metadata_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
print("\nSaved metadata to raw/next_ten_papers_metadata.json")
