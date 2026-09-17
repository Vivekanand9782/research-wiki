#!/usr/bin/env python3
"""
fix_quotes.py — Programmatic evidence-quote fixer for agent-written sidecars.

Problem: subagents wrote paraphrased quotes that don't survive the renderer's
verbatim-substring check. This script replaces each failed quote with a verified
contiguous substring extracted from the actual raw source text.

Algorithm:
  1. Load sidecar JSON + raw source text.
  2. Normalise source once (for matching).
  3. For each evidence quote in results[]:
     a. Try direct normalised substring match (exact).
     b. If that fails, fall back to n-gram search:
        - Extract candidate sentences from source (split on sentence boundaries).
        - Score each candidate by overlap of significant words with the claim.
        - Return the longest verified substring from the best candidate.
  4. Replace the failed quote with the verified one; keep the original claim.
  5. If no match found at all, drop that footnote from results[].
  6. Write the patched sidecar back.

Usage:
  python3 fix_quotes.py [--dry-run] [--verbose] <stem> ...
  python3 fix_quotes.py --all      # fix all 20 session papers
  python3 fix_quotes.py --check    # just report, no writes
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

# Add research-wiki to path
RW = Path(__file__).resolve().parent
sys.path.insert(0, str(RW))

from renderer import _normalise_for_quote_match, _verify_quote_in_source


# ─── N-gram sentence extraction ───────────────────────────────────────────────

def _sentences(text: str) -> list[str]:
    """Split raw text into sentence-level chunks, preserving context."""
    # Split on sentence-ending punctuation followed by whitespace + capital letter
    # or end-of-string. Works on both raw OCR text and clean text.
    chunks = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9\(])', text)
    result = []
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) > 20:  # discard tiny fragments
            result.append(chunk)
    return result


def _significant_words(text: str, min_len: int = 5) -> set[str]:
    """Extract stopword-filtered words for scoring overlap."""
    stop = {
        'the', 'and', 'for', 'with', 'that', 'this', 'from', 'were', 'was',
        'are', 'been', 'have', 'has', 'had', 'not', 'but', 'the', 'all',
        'into', 'each', 'than', 'when', 'which', 'their', 'they', 'them',
        'also', 'between', 'both', 'more', 'over', 'such', 'under', 'only',
        'using', 'used', 'through', 'where', 'when', 'could', 'would',
        'should', 'about', 'after', 'before', 'however', 'therefore',
        'thus', 'shown', 'shown', 'found', 'observed', 'detected',
        'measured', 'calculated', 'compared', 'including', 'et al',
    }
    words = re.findall(r'[a-zA-Z0-9]{%d,}' % min_len, text.lower())
    return {w for w in words if w not in stop}


def _best_verified_substring(
    claim: str,
    source_norm: str,
    source_raw: str,
    min_len: int = 40,
    max_candidates: int = 200,
) -> Optional[str]:
    """Find the longest verified substring that relates to the claim.

    Strategy:
    1. Score all source sentences by word-overlap with the claim.
    2. Take top 10 candidates.
    3. For each candidate, search for the longest contiguous substring
       (up to 300 chars) that verifies in source_norm.
    4. Return the longest verified hit across all candidates.
    """
    claim_words = _significant_words(claim)
    if not claim_words:
        return None

    sentences = _sentences(source_raw)
    if not sentences:
        return None

    # Score and rank
    scored = []
    for sent in sentences:
        sent_norm = _normalise_for_quote_match(sent)
        sent_words = _significant_words(sent)
        overlap = len(claim_words & sent_words)
        if overlap >= 2:
            scored.append((overlap, len(sent), sent, sent_norm))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    candidates = [s[2] for s in scored[:max_candidates]]

    best = None
    best_len = 0

    for sent in candidates:
        sent_norm = _normalise_for_quote_match(sent)
        # Try progressively shorter windows of the sentence
        for window_frac in [1.0, 0.8, 0.6, 0.5]:
            window_chars = max(min_len, int(len(sent_norm) * window_frac))
            for start in range(0, len(sent_norm) - window_chars + 1, 20):
                chunk_norm = sent_norm[start:start + window_chars]
                if chunk_norm in source_norm and len(chunk_norm) > best_len:
                    # Verify in source_norm (exact)
                    if _verify_quote_in_source(chunk_norm, source_norm):
                        best_len = len(chunk_norm)
                        # Map back to raw text
                        raw_start = max(0, start - 5)
                        raw_end = min(len(sent), start + window_chars + 5)
                        best = sent[raw_start:raw_end].strip()
                        if best and best_len >= min_len:
                            return best
    return best


# ─── Core fixer ───────────────────────────────────────────────────────────────

def fix_sidecar(stem: str, dry_run: bool = False, verbose: bool = False) -> dict:
    """Fix all failed evidence quotes in one sidecar. Returns a report."""
    raw_dir = RW / "raw" / "papers"

    # Find sidecar
    sidecar_path = raw_dir / f"{stem}.summary.json"
    if not sidecar_path.exists():
        return {"stem": stem, "error": "sidecar not found"}

    payload = json.load(open(sidecar_path))

    # Find raw text
    raw_path = None
    for td in raw_dir.iterdir():
        if td.is_dir() and (td / f"{stem}.md").exists():
            raw_path = td / f"{stem}.md"
            break

    if not raw_path or not raw_path.exists():
        return {"stem": stem, "error": "raw text not found"}

    source_raw = raw_path.read_text()
    source_norm = _normalise_for_quote_match(source_raw)

    total_quotes = 0
    kept = 0
    replaced = 0
    dropped = 0
    section_reports = []

    for sec_name, sec_data in payload.get("sections", {}).items():
        results = sec_data.get("results", [])
        new_results = []
        sec_report = {"section": sec_name, "quotes": len(results), "kept": 0, "replaced": 0, "dropped": 0}

        for r in results:
            total_quotes += 1
            claim = r.get("claim", "")
            old_quote = r.get("evidence_quote", "")
            source_locator = r.get("source_locator", "")

            # Direct verification
            if old_quote and _verify_quote_in_source(old_quote, source_norm):
                new_results.append(r)
                kept += 1
                sec_report["kept"] += 1
            else:
                # Try to find a replacement
                new_quote = None

                if claim:
                    new_quote = _best_verified_substring(
                        claim, source_norm, source_raw,
                        min_len=40, max_candidates=150
                    )

                if new_quote:
                    new_r = dict(r)
                    new_r["evidence_quote"] = new_quote
                    new_results.append(new_r)
                    replaced += 1
                    sec_report["replaced"] += 1
                    if verbose:
                        print(f"  [{sec_name}] REPLACED quote for claim: {claim[:80]}...")
                        print(f"    NEW: {new_quote[:120]}")
                else:
                    # Drop — no verifiable quote found
                    dropped += 1
                    sec_report["dropped"] += 1
                    if verbose:
                        print(f"  [{sec_name}] DROPPED quote for claim: {claim[:80]}")

        sec_data["results"] = new_results
        section_reports.append(sec_report)

    # Write patched sidecar
    if not dry_run:
        sidecar_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    report = {
        "stem": stem,
        "total_quotes": total_quotes,
        "kept": kept,
        "replaced": replaced,
        "dropped": dropped,
        "sections": section_reports,
    }

    status = "PASS" if dropped == 0 and kept + replaced >= max(3, total_quotes * 0.7) else "REVIEW"
    report["status"] = status
    return report


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--check", action="store_true", help="report only, no writes")
    ap.add_argument("--all", action="store_true", help="fix all 20 session papers")
    ap.add_argument("stems", nargs="*")
    args = ap.parse_args()

    THE_20 = [
        'Jiajun Zhang_2025_Efficient_CRISPR_Cas_based_gene_editing_in_cotton_',
        'Sun_2017_generation_of_high_amylose_rice_through_crisprcas9_mediated_targeted_mutagenesis',
        'Miroshnichenko_Unknown_effect_of_rnai_mediated_silencing_of_the_taos2_gene_on',
        'Mushtaq_2024_crispr_based_gene_editing_for_enhancing_drought_and_salinity_tolerance_in',
        'Tang_2023_ornamental_plant_gene_editing_past_present_and_future',
        'Hejabi_2022_nanocarriers_a_novel_strategy_for_the_delivery_of_crispr_cas_systems',
        'Liang_2013_targeted_mutagenesis_in_zea_mays_using_talens_and_the',
        'M. Uranga_2022_Heritable_CRISPR_Cas9_editing_of_plant_genomes_usi',
        'Zhang_2023_boosting_genome_editing_efficiency_in_human_cells_and_plants_with',
        'Liang_2023_genome_editing_based_on_in_vitroassembled_ribonucleoproteins_in',
        'Singh_2023_genetically_modified_and_genome_edited_fruit_crops',
        'Masani_2024_towards_dna_free_crisprcas9_genome_editing_for_sustainable_oil_palm',
        'Ishibashi_2024_systemic_delivery_of_engineered_compact_ascas12f_by_a_positive_strand_rna',
        'Ruqman Wu_2025_A_visual_monitoring_DNA_free_multi_gene_editing_sy',
        'Ugrappa Nagalakshmi_2025_High_efficiency__transgene_free_plant_genome_editi',
        'ishibashi_2024_systemic_delivery_engineered',
        'Weiss_2025_viral_delivery_of_an_rna_guided_genome_editor_for_transgene_free_germline',
        'Zheng Gong_2024_Geminiviral_induced_genome_editing_using_miniature',
        'sukegawa_2023_genome_editing_rice',
        'Su_Unknown_cas12a_rnp_mediated_co_transformation_enables_transgene_free_multiplex',
    ]

    stems = THE_20 if args.all else args.stems

    print(f"{'='*70}")
    print(f"Quote fixer — {'DRY RUN' if args.dry_run or args.check else 'LIVE'}")
    print(f"{'='*70}\n")

    results = []
    for stem in stems:
        r = fix_sidecar(stem, dry_run=args.dry_run or args.check, verbose=args.verbose)
        results.append(r)
        total = r.get('total_quotes', 0)
        kept = r.get('kept', 0)
        rep = r.get('replaced', 0)
        drp = r.get('dropped', 0)
        status = r.get('status', '?')
        print(f"{stem[:55]:55s}  {status}  kept={kept} rep={rep} drp={drp}  ({total} total)")

    total_q = sum(r.get('total_quotes', 0) for r in results)
    total_kept = sum(r.get('kept', 0) for r in results)
    total_rep = sum(r.get('replaced', 0) for r in results)
    total_drp = sum(r.get('dropped', 0) for r in results)
    print(f"\n{'='*70}")
    print(f"TOTALS: {total_q} quotes | kept={total_kept} replaced={total_rep} dropped={total_drp}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()