import os
import urllib.request
import json
import re
from pathlib import Path

RAW_DIR = Path("raw/papers/uncategorized")
metadata_file = Path("raw/ten_papers_metadata.json")

files = sorted(f for f in os.listdir(RAW_DIR) if f.endswith(".md"))[:10]

results = {}

for f in files:
    path = RAW_DIR / f
    text = path.read_text(encoding="utf-8")
    
    # Extract year
    year_match = re.search(r"\b(19|20)\d{2}\b", text[:3000])
    year = int(year_match.group(1)) if year_match else None
    
    # Extract title candidates
    title = f.replace(".md", "")
    # Remove leading spaces and characters
    title_clean = title.strip()
    
    # Try searching OpenAlex
    query = urllib.parse.quote(title_clean[:100])
    url = f"https://api.openalex.org/works?filter=title.search:{query}"
    
    print(f"Searching: {title_clean}")
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mailto:research-wiki@example.com"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            results_list = data.get("results", [])
            if results_list:
                best = results_list[0]
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
                    "title": title_clean,
                    "doi": None,
                    "authors": [],
                    "year": year,
                    "journal": None,
                    "paper_slug": re.sub(r"[^a-zA-Z0-9]+", "-", f.replace(".md", "")).strip("-").lower()
                }
    except Exception as e:
        print(f"  Error: {e}")
        results[f] = {
            "title": title_clean,
            "doi": None,
            "authors": [],
            "year": year,
            "journal": None,
            "paper_slug": re.sub(r"[^a-zA-Z0-9]+", "-", f.replace(".md", "")).strip("-").lower()
        }

metadata_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
print("\nSaved metadata to raw/ten_papers_metadata.json")
