#!/usr/bin/env python3
import json
import sys
import re
import subprocess
from pathlib import Path

def print_warning(msg):
    print(f"\033[93m[WARNING] {msg}\033[0m", file=sys.stderr)

def print_error(msg):
    print(f"\033[91m[ERROR] {msg}\033[0m", file=sys.stderr)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Audit a generated cited document.")
    parser.add_argument("doc_path", type=str, help="Path to the generated markdown document")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    md_path = Path(args.doc_path)
    if not md_path.exists():
        print_error(f"File {md_path} not found.")
        sys.exit(1)

    citations_path = md_path.with_name(md_path.name.replace(".md", ".citations.json"))
    
    with open(md_path, "r") as f:
        content = f.read()

    errors = 0
    warnings = 0

    # 1. Validator passes
    script_dir = Path(__file__).parent
    validator_path = script_dir / "validate_manifest.py"
    if validator_path.exists():
        res = subprocess.run([sys.executable, str(validator_path), str(md_path)], capture_output=True, text=True)
        if res.returncode != 0:
            print_error(f"AUDIT-1: Validator failed.\n{res.stderr}")
            errors += 1
    else:
        print_warning("validate_manifest.py not found, skipping AUDIT-1")

    # 2. No [CITATION NEEDED] markers
    if "[CITATION NEEDED]" in content:
        print_error("AUDIT-2: Markdown contains [CITATION NEEDED] markers.")
        errors += 1

    # Manifest checks
    if citations_path.exists():
        with open(citations_path, "r") as f:
            manifest = json.load(f)

        # 3. Manifest researcher_pass_complete
        if not manifest.get("researcher_pass_complete", False):
            print_error("AUDIT-3: Manifest researcher_pass_complete is false.")
            errors += 1
        if len(manifest.get("failures", [])) > 0:
            print_error("AUDIT-3: Manifest has failures.")
            errors += 1

        citations = manifest.get("citations", [])
        for i, c in enumerate(citations):
            # 5. Non-empty claims_supported
            if not c.get("claims_supported") or len(c["claims_supported"]) == 0:
                print_warning(f"AUDIT-5: Citation {c.get('key', i)} missing claims_supported.")
                warnings += 1
            
            # 6. Includes source_api and verified_at
            if not c.get("source_api") or not c.get("verified_at"):
                print_warning(f"AUDIT-6: Citation {c.get('key', i)} missing source_api or verified_at.")
                warnings += 1
    else:
        print_error(f"Manifest {citations_path} not found.")
        errors += 1

    # 4. [NOT REPORTED] markers
    not_reported_count = content.count("[NOT REPORTED]")
    if not_reported_count > 0:
        print_warning(f"AUDIT-4: Found {not_reported_count} '[NOT REPORTED]' markers. Ensure these are genuinely absent from the source.")
        warnings += 1

    # 7. Gene-symbol-shaped tokens
    # Basic regex for things that look like TaXYZ-1A or similar
    gene_pattern = re.compile(r'\b(?:Ta|Os|Zm|At)[A-Z][A-Za-z0-9]+(?:-[A-Z0-9]+)?\b')
    found_genes = set(gene_pattern.findall(content))
    if found_genes:
        print_warning(f"AUDIT-7: Found gene-symbol-shaped tokens: {', '.join(found_genes)}. Cross-check against the primary database.")
        warnings += 1

    if args.strict and warnings > 0:
        print_error(f"Strict mode enabled. {warnings} warnings treated as errors.")
        errors += warnings

    if errors > 0:
        print_error(f"Audit failed with {errors} errors.")
        sys.exit(1)

    print(f"Audit passed with {warnings} warnings.")
    sys.exit(0)

if __name__ == "__main__":
    main()
