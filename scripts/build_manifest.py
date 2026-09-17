#!/usr/bin/env python3
import json
import sys
import os
import datetime
import urllib.request
import urllib.error
import re
from pathlib import Path

def get_current_model():
    """Attempt to get the current model via current_model.py, or default."""
    try:
        import subprocess
        script_dir = Path(__file__).parent
        model_script = script_dir / "current_model.py"
        if model_script.exists():
            result = subprocess.run(["python3", str(model_script)], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
    except Exception:
        pass
    return "minimax-m2.7"  # General Compute fallback

def fetch_openalex(identifier, id_type):
    """Fetch OpenAlex metadata without letting an optional lookup fail ingest."""
    import ssl
    import time
    from urllib.parse import quote

    if id_type == "doi":
        # Reuse the pipeline's bounded DOI grammar so HTML/Markdown suffixes
        # such as ``>``, ``</u>``, ``](...)``, and ``**`` never enter the URL.
        project_root = str(Path(__file__).resolve().parents[1])
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from paper_metadata import extract_doi_from_text
        clean_id = extract_doi_from_text(str(identifier))
        if not clean_id:
            return None
        encoded_id = quote(clean_id, safe="/()")
        url = f"https://api.openalex.org/works/https://doi.org/{encoded_id}"
    elif id_type == "pmid":
        clean_id = str(identifier).replace("PMID:", "").strip()
        if not clean_id.isdigit():
            return None
        url = f"https://api.openalex.org/works/pmid:{clean_id}"
    else:
        return None

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    email = os.environ.get("DEFAULT_EMAIL", "").strip()
    user_agent = "ResearchWiki/1.0"
    if email:
        user_agent += f" (mailto:{email})"

    data = None
    last_error = "unknown response"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": user_agent},
            )
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                raw = response.read().decode("utf-8")
            decoded = json.loads(raw)
            if not isinstance(decoded, dict):
                raise ValueError("OpenAlex response was not a JSON object")
            data = decoded
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            last_error = f"HTTP {exc.code}"
            if exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                break
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = min(30.0, max(0.0, float(retry_after)))
            except (TypeError, ValueError):
                delay = min(8.0, 1.0 * (2**attempt))
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = type(exc).__name__
            delay = min(8.0, 1.0 * (2**attempt))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            last_error = type(exc).__name__
            delay = min(8.0, 1.0 * (2**attempt))

        if attempt < 2:
            time.sleep(delay)

    if data is None:
        print(f"OpenAlex metadata unavailable ({last_error}); continuing without it", file=sys.stderr)
        return None

    authors = []
    for authorship in data.get("authorships", []):
        author_name = (authorship.get("author") or {}).get("display_name", "")
        if author_name:
            parts = author_name.split()
            authors.append(f"{parts[-1]}, {parts[0][0]}." if len(parts) > 1 else author_name)

    location = data.get("primary_location") or {}
    source = location.get("source") or {}
    doi_out = str(data.get("doi") or "").replace("https://doi.org/", "")
    ids = data.get("ids") or {}
    pmid_out = str(ids.get("pmid") or "").replace(
        "https://pubmed.ncbi.nlm.nih.gov/", ""
    )
    return {
        "authors": authors,
        "year": data.get("publication_year"),
        "title": data.get("title"),
        "journal": source.get("display_name", ""),
        "doi": doi_out,
        "pmid": pmid_out,
        "source_api": "openalex",
        "source_url": data.get("id", ""),
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build_manifest.py <seeds.json>", file=sys.stderr)
        sys.exit(1)

    seeds_path = Path(sys.argv[1])
    if not seeds_path.exists():
        print(f"Error: {seeds_path} not found.", file=sys.stderr)
        sys.exit(1)

    doc_name = seeds_path.name.replace(".seeds.json", ".md")
    citations_path = seeds_path.with_name(seeds_path.name.replace(".seeds.json", ".citations.json"))

    with open(seeds_path, "r") as f:
        seeds_data = json.load(f)

    # Validate seeds schema
    if not isinstance(seeds_data, dict) or "seeds" not in seeds_data:
        # Support simple list of seeds as fallback
        if isinstance(seeds_data, list):
            seeds_list = seeds_data
            model = "auto"
        else:
            print("Error: seeds.json must contain a 'seeds' array.", file=sys.stderr)
            sys.exit(1)
    else:
        seeds_list = seeds_data.get("seeds", [])
        model = seeds_data.get("model", "auto")

    if model == "auto":
        model = get_current_model()

    manifest = {
        "schema_version": "1.0",
        "document": doc_name,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": model,
        "researcher_pass_complete": True,
        "citations": [],
        "failures": []
    }

    for seed in seeds_list:
        identifier = seed.get("id")
        id_type = seed.get("type", "doi")
        provided_key = seed.get("key")
        
        if not identifier:
            continue

        print(f"Fetching metadata for {identifier} via OpenAlex...")
        metadata = fetch_openalex(identifier, id_type)

        if not metadata:
            print(f"Failed to fetch {identifier}", file=sys.stderr)
            manifest["failures"].append({"seed": seed, "reason": "API lookup failed"})
            manifest["researcher_pass_complete"] = False
            continue

        # Use provided key, or generate fallback
        if provided_key:
            key = provided_key
        else:
            last_name = metadata["authors"][0].split(",")[0].lower() if metadata["authors"] else "unknown"
            year = metadata["year"] or "nd"
            key = f"{last_name}_{year}_auto"

        citation = {
            "key": key,
            "authors": metadata["authors"],
            "year": metadata["year"],
            "title": metadata["title"],
            "journal": metadata["journal"],
            "doi": metadata["doi"],
            "pmid": metadata["pmid"],
            "source_api": metadata["source_api"],
            "source_url": metadata["source_url"],
            "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "verifier_notes": "Automatically fetched via OpenAlex",
            "claims_supported": seed.get("claims", ["Needs claims"])
        }
        manifest["citations"].append(citation)

    with open(citations_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest built: {citations_path}")
    if not manifest["researcher_pass_complete"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
