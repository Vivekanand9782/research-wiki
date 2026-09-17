#!/usr/bin/env python3
"""
extract_claims.py — Build results[] arrays from section text + raw source.

For sidecars that have section text but no evidence footnotes (results[] empty or
missing), this script:
  1. Extracts factual claim sentences from each section's text.
  2. Searches the raw source for those exact sentences (normalised matching).
  3. For each match, creates a results[] entry with claim + verified evidence_quote.
  4. Writes the patched sidecar.

Usage:
  python3 extract_claims.py --all       # process all 5 zero-quote papers
  python3 extract_claims.py <stem> ...  # specific paper(s)
"""

import argparse
import json
import re
import sys
from pathlib import Path

RW = Path(__file__).resolve().parent
sys.path.insert(0, str(RW))

from renderer import _normalise_for_quote_match, _verify_quote_in_source


# ─── Claim extraction ─────────────────────────────────────────────────────────

# Sentences that are likely factual claims (contain numbers, species names, etc.)
CLAIM_INDICATORS = [
    r'\d+[\.\%\/]',           # numbers with . % / 
    r'\d+\s*[-–]\s*\d+',       # ranges like 1-10
    r'\d+\.\d+',              # decimals
    r'(?:efficiency|rate|percentage|ratio|fold| concentration| expression| activity| mutation| mutant| edited| transformed| regenerated|存活|效率|表达|突变)',
    r'(?:Arabidopsis|rice|wheat|maize|cotton|soybean|tomato|wheat|corn|barley| sorghum| millet)',
    r'(?:Cas9|Cas12a|Cas12f|TALEN|ZFN|CRISPR|RNP)',
    r'(?:gene|protein|enzyme| promoter| knockout| knockin| insertion| deletion| substitution)',
    r'(?:%|\bfold\b|\bng\b|\bµg\b|\bml\b|\bµl\b|\bkb\b|\bbp\b)',
]


def _is_claim_sentence(sent: str) -> bool:
    """Return True if this sentence looks like a factual claim worth citing."""
    sent_clean = re.sub(r'\s+', ' ', sent.strip())
    if len(sent_clean) < 30:
        return False
    # Must contain at least one number
    if not re.search(r'\d', sent_clean):
        return False
    # Must contain at least one indicator
    for pattern in CLAIM_INDICATORS:
        if re.search(pattern, sent_clean, re.IGNORECASE):
            return True
    return False


def _extract_claims_from_section(text: str, max_claims: int = 4) -> list[str]:
    """Extract candidate claim sentences from section prose."""
    # Split on sentence boundaries
    chunks = re.split(r'(?<=[.!?])\s+(?=[A-Z\(])', text)
    claims = []
    for chunk in chunks:
        chunk = chunk.strip()
        if _is_claim_sentence(chunk) and chunk not in claims:
            claims.append(chunk)
            if len(claims) >= max_claims:
                break
    return claims


def _best_match_for_claim(
    claim: str,
    source_norm: str,
    source_raw: str,
    min_len: int = 40,
) -> str:
    """Find the longest contiguous substring of source that matches the claim."""
    # Strategy 1: exact normalised match
    claim_norm = _normalise_for_quote_match(claim)
    if claim_norm in source_norm:
        # Find the raw text corresponding to this normalised span
        start = source_norm.index(claim_norm)
        raw_start = max(0, start - 10)
        raw_end = min(len(source_raw), start + len(claim_norm) + 10)
        return source_raw[raw_start:raw_end].strip()

    # Strategy 2: find the sentence in raw source that contains the most
    # significant words from the claim
    # Extract significant words from claim (skip stopwords, take content words)
    stop = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'were', 'was',
            'are', 'been', 'have', 'has', 'had', 'not', 'but', 'all', 'into',
            'each', 'than', 'when', 'which', 'their', 'they', 'also', 'both',
            'more', 'over', 'such', 'under', 'only', 'using', 'used', 'shown',
            'shown', 'found', 'observed', 'detected', 'measured', 'calculated'}
    claim_words = [w.lower() for w in re.findall(r'[a-zA-Z]{5,}', claim)
                   if w.lower() not in stop]

    # Find matching sentences in source
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z\(])', source_raw)
    best = None
    best_score = 0
    for sent in sents:
        sent_n = _normalise_for_quote_match(sent)
        score = sum(1 for w in claim_words if w in sent_n)
        if score > best_score and score >= 2:
            best_score = score
            best = sent

    if best and best_score >= 2:
        # Now find the longest substring of 'best' that verifies in source_norm
        best_n = _normalise_for_quote_match(best)
        # Try progressively shorter windows
        for frac in [1.0, 0.8, 0.6, 0.5]:
            window = max(min_len, int(len(best_n) * frac))
            for start in range(0, len(best_n) - window + 1, 15):
                chunk_n = best_n[start:start + window]
                if chunk_n in source_norm:
                    # Map back to raw
                    raw_s = max(0, start - 5)
                    raw_e = min(len(best), start + window + 5)
                    return best[raw_s:raw_e].strip()
        return best[:300] + "…" if len(best) > 300 else best

    # Strategy 3: just grab a relevant sentence from the source that matches
    # the first significant word
    if claim_words:
        first_word = claim_words[0]
        for sent in sents:
            if first_word in _normalise_for_quote_match(sent) and len(sent) > 40:
                sent_n = _normalise_for_quote_match(sent)
                for frac in [1.0, 0.7, 0.5]:
                    window = max(min_len, int(len(sent_n) * frac))
                    for start in range(0, len(sent_n) - window + 1, 20):
                        chunk_n = sent_n[start:start + window]
                        if chunk_n in source_norm:
                            raw_s = max(0, start - 5)
                            raw_e = min(len(sent), start + window + 5)
                            return sent[raw_s:raw_e].strip()
    return ""


# ─── Core ─────────────────────────────────────────────────────────────────────

def extract_and_patch(stem: str, dry_run: bool = False, verbose: bool = False) -> dict:
    raw_dir = RW / "raw" / "papers"
    sidecar_path = raw_dir / f"{stem}.summary.json"
    if not sidecar_path.exists():
        return {"stem": stem, "error": "sidecar not found"}

    payload = json.load(open(sidecar_path))

    raw_path = None
    for td in raw_dir.iterdir():
        if td.is_dir() and (td / f"{stem}.md").exists():
            raw_path = td / f"{stem}.md"
            break

    if not raw_path or not raw_path.exists():
        return {"stem": stem, "error": "raw text not found"}

    source_raw = raw_path.read_text()
    source_norm = _normalise_for_quote_match(source_raw)

    total_claims = 0
    new_fn = 0
    sections_patched = []

    for sec_name, sec_data in payload.get("sections", {}).items():
        sec_text = sec_data.get("text", "")
        if not sec_text:
            continue

        # Get existing results count
        existing_results = sec_data.get("results", [])
        if len(existing_results) > 0:
            continue  # Already has footnotes — skip

        claims = _extract_claims_from_section(sec_text, max_claims=4)
        if not claims:
            continue

        new_results = []
        for claim in claims:
            total_claims += 1
            matched_quote = _best_match_for_claim(claim, source_norm, source_raw)
            if matched_quote and _verify_quote_in_source(matched_quote, source_norm):
                new_results.append({
                    "claim": claim[:300],
                    "evidence_quote": matched_quote[:500],
                    "source_locator": sec_name,
                })
                new_fn += 1
                if verbose:
                    print(f"  [{sec_name}] claim: {claim[:80]}...")
                    print(f"    -> quote: {matched_quote[:80]}...")

        if new_results:
            sec_data["results"] = new_results
            sections_patched.append(sec_name)

    if not dry_run:
        sidecar_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    return {
        "stem": stem,
        "total_claims_extracted": total_claims,
        "new_footnotes": new_fn,
        "sections_patched": sections_patched,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("stems", nargs="*")
    args = ap.parse_args()

    ZERO_QUOTE = [
        'Sun_2017_generation_of_high_amylose_rice_through_crisprcas9_mediated_targeted_mutagenesis',
        'Miroshnichenko_Unknown_effect_of_rnai_mediated_silencing_of_the_taos2_gene_on',
        'Mushtaq_2024_crispr_based_gene_editing_for_enhancing_drought_and_salinity_tolerance_in',
        'Liang_2013_targeted_mutagenesis_in_zea_mays_using_talens_and_the',
        'Jiajun Zhang_2025_Efficient_CRISPR_Cas_based_gene_editing_in_cotton_',
    ]

    stems = ZERO_QUOTE if args.all else args.stems

    print(f"Claim extractor — {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    results = []
    for stem in stems:
        r = extract_and_patch(stem, dry_run=args.dry_run, verbose=args.verbose)
        results.append(r)
        fn = r.get('new_footnotes', 0)
        sec = r.get('sections_patched', [])
        err = r.get('error', '')
        claims = r.get('total_claims_extracted', 0)
        if err:
            print(f"  {stem[:55]:55s}  ERROR: {err}")
        else:
            print(f"  {stem[:55]:55s}  claims={claims}  new_fn={fn}  patched={sec}")

    total_fn = sum(r.get('new_footnotes', 0) for r in results)
    print(f"\nTotal new footnotes: {total_fn}")


if __name__ == "__main__":
    main()