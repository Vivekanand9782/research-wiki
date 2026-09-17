#!/usr/bin/env python3
import argparse
import re
import os
import sys
import urllib.request
import urllib.error
import time
import ssl

# Pre-defined manual BibTeX entries for non-DOI references in this workspace
MANUAL_ENTRIES = {
    "bis_1995_foodgrains": """@techreport{bis_1995_foodgrains,
  author = {{Bureau of Indian Standards}},
  title = {Terminology for foodgrains (IS 2813: 1995)},
  institution = {Bureau of Indian Standards},
  year = {1995},
  address = {New Delhi, India}
}""",
    "dfpd_2024_wheat": """@techreport{dfpd_2024_wheat,
  author = {{Department of Food and Public Distribution}},
  title = {Uniform specifications of wheat for Rabi Marketing Season},
  institution = {Department of Food and Public Distribution, Ministry of Consumer Affairs, Food and Public Distribution, Government of India},
  year = {2024},
  address = {New Delhi, India}
}""",
    "fao_2024_faostat": """@misc{fao_2024_faostat,
  author = {{Food and Agriculture Organization}},
  title = {{FAOSTAT Production Crops Database}},
  howpublished = {Food and Agriculture Organization, Rome, Italy},
  year = {2024},
  url = {https://www.fao.org/faostat/}
}""",
    "fssai_2011_regulations": """@techreport{fssai_2011_regulations,
  author = {{Food Safety and Standards Authority of India}},
  title = {Food Safety and Standards (Food Product Standards and Food Additives) Regulations},
  institution = {Ministry of Health and Family Welfare, Government of India},
  year = {2011},
  address = {New Delhi, India}
}""",
    "hagberg_1960_rapid": """@article{hagberg_1960_rapid,
  author = {Hagberg, Sven},
  title = {A rapid method for determining alpha-amylase activity},
  journal = {Cereal Chemistry},
  volume = {37},
  number = {2},
  pages = {218--222},
  year = {1960}
}""",
    "icar_iiwbr_2023_progress": """@techreport{icar_iiwbr_2023_progress,
  author = {{ICAR-Indian Institute of Wheat and Barley Research}},
  title = {AICRP on Wheat and Barley Quality Progress Report},
  institution = {ICAR-Indian Institute of Wheat and Barley Research},
  year = {2023},
  address = {Karnal, India}
}""",
    "perten_1964_application": """@article{perten_1964_application,
  author = {Perten, Harald},
  title = {Application of the falling number method for evaluating alpha-amylase activity},
  journal = {Cereal Chemistry},
  volume = {41},
  number = {3},
  pages = {127--139},
  year = {1964}
}""",
    "rao_1986_test_baking": """@article{rao_1986_test_baking,
  author = {Rao, P. H. and Leelavathi, K. and Shurpalekar, S. R.},
  title = {Test baking of chapati---Development of a method},
  journal = {Cereal Chemistry},
  volume = {63},
  number = {4},
  pages = {297--303},
  year = {1986}
}""",
    "the_tribune_2023_unseasonal": """@article{the_tribune_2023_unseasonal,
  author = {{The Tribune}},
  title = {Unseasonal rains damage standing wheat crop in Punjab, Haryana},
  journal = {The Tribune India},
  year = {2023},
  month = {March},
  url = {https://www.tribuneindia.com/}
}""",
    "usda_fas_2024_world": """@techreport{usda_fas_2024_world,
  author = {{United States Department of Agriculture, Foreign Agricultural Service}},
  title = {World Agricultural Production Circular},
  institution = {USDA Foreign Agricultural Service},
  year = {2024}
}"""
}

# Known DOI typo corrections
DOI_CORRECTIONS = {
    "10.1266/ggs.83.18506": "10.1266/ggs.83.153"
}

def strip_rtf_tags(text):
    # Replace common RTF escapes
    text = text.replace("\\'85", "...")
    text = text.replace("\\'91", "'")
    text = text.replace("\\'92", "'")
    text = text.replace("\\uc0\\u8208 ", "-")
    text = text.replace("\\uc0\\u8226 ", "*")
    text = text.replace("\\uc0\\u8242 ", "'")
    text = text.replace("\\u8208 ", "-")
    text = text.replace("\\u8226 ", "*")
    text = text.replace("\\u8242 ", "'")
    text = text.replace("\\'d7", "x")
    text = text.replace("\\'f3", "o")
    text = text.replace("\\'f6", "o")
    text = text.replace("\\'fc", "u")
    text = text.replace("\\'fa", "u")
    text = text.replace("\\'e1", "a")
    text = text.replace("\\'e9", "e")
    text = text.replace("\\'ed", "i")
    text = text.replace("\\'f1", "n")
    text = text.replace("\\'a0", " ")
    
    # Remove control words and symbols
    text = re.sub(r'\\[a-zA-Z]+\d*', '', text)
    text = re.sub(r'\\\'[a-fA-F0-9]{2}', '', text)  # remove remaining hex escapes
    
    # Remove groups (curly braces)
    text = re.sub(r'\{[^\}]*\}', '', text)
    text = re.sub(r'[{}]', '', text)
    
    # Replace HTML tags
    text = text.replace("<i>", "").replace("</i>", "")
    text = text.replace("<sub>", "").replace("</sub>", "")
    text = text.replace("<sup>", "").replace("</sup>", "")
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip trailing RTF remnants (like \ -720)
    text = re.sub(r'\s*\\?\s*-?\d+\s*$', '', text)
    text = text.strip()
    if text.endswith('\\'):
        text = text[:-1].strip()
        
    return text.strip()

def get_manual_key(cleaned_text):
    text_lower = cleaned_text.lower()
    for key in MANUAL_ENTRIES.keys():
        # Match tokens from the manual key in the text
        tokens = key.split('_')
        # If year and author prefix/name matches
        if all(token in text_lower for token in tokens[:2]):
            return key
    return None

def fetch_bibtex_from_doi(doi, max_retries=3):
    # Apply corrections
    if doi in DOI_CORRECTIONS:
        doi = DOI_CORRECTIONS[doi]
        
    url = f"https://doi.org/{doi}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/x-bibtex")
    
    # Create unverified SSL context to bypass local certificate verification errors
    context = ssl._create_unverified_context()
    
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                content = response.read().decode('utf-8')
                return content.strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = (attempt + 1) * 2
                print(f"  [!] Rate limited (429) for DOI {doi}. Retrying in {wait}s...", file=sys.stderr, flush=True)
                time.sleep(wait)
            else:
                print(f"  [!] HTTP Error {e.code} for DOI {doi}: {e.reason}", file=sys.stderr, flush=True)
                break
        except Exception as e:
            print(f"  [!] Error fetching DOI {doi}: {e}", file=sys.stderr, flush=True)
            time.sleep(1)
            
    return None

def extract_doi(text):
    # Match something like DOI: https://doi.org/10.1007/s00122-016-2793-0
    # or DOI: 10.1007/s00122-016-2793-0
    match = re.search(r'(?:doi:\s*(?:https?://doi\.org/)?)((?:10\.\d{4,9}/[-._;()/:A-Z0-9]+)|(?:manual/[-._;()/:A-Z0-9]+))', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def main():
    parser = argparse.ArgumentParser(description="Clean references file and fetch BibTeX from doi.org with local manual fallbacks.")
    parser.add_argument("input_file", help="Path to input .rtf or .txt file containing the reference list")
    parser.add_argument("output_file", help="Path to output .bib file")
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Reading and cleaning {args.input_file}...", flush=True)
    with open(args.input_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    # Check if RTF file or raw text
    if "{\\rtf" in content:
        parts = content.split("\\ls1\\ilvl0")
        if len(parts) <= 1:
            # Fallback if RTF list structure differs
            parts = content.split("\\par")
        raw_refs = parts[1:] if len(parts) > 1 else [content]
    else:
        # Simple line split for txt files
        raw_refs = content.splitlines()
        
    cleaned_refs = []
    for part in raw_refs:
        cleaned = strip_rtf_tags(part) if "{\\rtf" in content else part.strip()
        if cleaned:
            # Clean list bullets or numbering
            cleaned = re.sub(r'^\s*[\u8226\*\-\d\.\s\t]+', '', cleaned)
            if cleaned:
                cleaned_refs.append(cleaned)
            
    total_refs = len(cleaned_refs)
    print(f"Found {total_refs} references to convert.", flush=True)
    
    bib_entries = []
    failed_dois = []
    
    for idx, ref in enumerate(cleaned_refs):
        print(f"[{idx+1}/{total_refs}] Processing: {ref[:60]}...", flush=True)
        
        # Check if it has a DOI
        doi = extract_doi(ref)
        if doi:
            print(f"  -> Found DOI: {doi}", flush=True)
            bib_entry = fetch_bibtex_from_doi(doi)
            if bib_entry:
                bib_entries.append(bib_entry)
                print("  -> Successfully resolved BibTeX", flush=True)
            else:
                print(f"  -> Failed to resolve DOI: {doi}", flush=True)
                failed_dois.append((ref, doi))
            time.sleep(0.5)
        else:
            # Check manual mapping
            manual_key = get_manual_key(ref)
            if manual_key and manual_key in MANUAL_ENTRIES:
                print(f"  -> Found manual entry key: {manual_key}", flush=True)
                bib_entries.append(MANUAL_ENTRIES[manual_key])
            else:
                print(f"  -> WARNING: No DOI and no manual entry found for reference: {ref}", flush=True)
                
    print(f"\nWriting {len(bib_entries)} entries to {args.output_file}...", flush=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(bib_entries) + "\n")
        
    if failed_dois:
        print("\nFailed to resolve DOIs for the following references:")
        for ref, doi in failed_dois:
            print(f"- DOI: {doi} in reference: {ref}")
            
    print("\nConversion complete!", flush=True)

if __name__ == "__main__":
    main()
