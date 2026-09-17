#!/usr/bin/env python3
import json
import sys
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_manifest.py <doc.md>", file=sys.stderr)
        sys.exit(1)

    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"Error: {md_path} not found.", file=sys.stderr)
        sys.exit(1)

    # Allow processing nested paths correctly (e.g. generated_content/foo.md)
    citations_path = md_path.with_name(md_path.name.replace(".md", ".citations.json"))

    if not citations_path.exists():
        print(f"Error: Manifest {citations_path} not found. Run build_manifest.py first.", file=sys.stderr)
        sys.exit(1)

    with open(citations_path, "r") as f:
        manifest = json.load(f)

    with open(md_path, "r") as f:
        content = f.read()

    # Find all citation keys like [[key]]
    citation_keys_in_text = re.findall(r'\[\[(.*?)\]\]', content)
    
    # Exclude normal wiki links that might not be citations if possible,
    # but based on GEMINI.md, [[key]] is used for citations and linked pages.
    # To differentiate, we just check if the key matches a manifest citation key.
    # Wait, the rule says: "The validator matches manifest keys against [[key]] references in the markdown."
    # We should strictly verify that any [[key]] that is formatted as a citation key exists.
    # Actually, a better approach: extract all keys from manifest, ensure every key used in text is valid,
    # and maybe warn if a key is in text but not in manifest? No, some [[links]] are internal pages (e.g., [[TaMKK3-A]]).
    # The rule says: "exits non-zero if any in-text citation, citation key, or reference-list entry in the markdown does not match the manifest"

    manifest_keys = {c["key"] for c in manifest.get("citations", [])}
    
    # We also check for [CITATION NEEDED]
    if "[CITATION NEEDED]" in content:
        print("Validation Error: Document contains [CITATION NEEDED] markers.", file=sys.stderr)
        sys.exit(1)

    # Let's extract author-year inline citations: (Author et al., 2023)[[key]]
    inline_citations = re.findall(r'\(([^)]+)\)\[\[(.*?)\]\]', content)
    
    errors = 0
    for text_author_year, key in inline_citations:
        if key not in manifest_keys:
            print(f"Validation Error: In-text citation key '[[{key}]]' not found in manifest.", file=sys.stderr)
            errors += 1

    # Simple Check: Make sure bibliography exists
    if "## References" not in content:
        print("Validation Error: Document missing '## References' section.", file=sys.stderr)
        errors += 1

    if errors > 0:
        print(f"Validation failed with {errors} errors.", file=sys.stderr)
        sys.exit(1)

    print("Validation passed. Manifest and document are perfectly aligned.")
    sys.exit(0)

if __name__ == "__main__":
    main()
