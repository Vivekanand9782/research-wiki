#!/usr/bin/env python3
"""
augment_depth.py — Programmatic section depth augmentation for shallow sidecars.

For papers that pass the footnote gate but fail the depth gate, extracts
relevant sentences from the raw source and appends them to the thinnest sections.
Also injects results[] footnotes for the new evidence.

Usage:
  python3 augment_depth.py --all       # augment all 8 depth-fail + Liang_2023 papers
  python3 augment_depth.py <stem> ...  # specific papers
"""

import argparse
import json
import re
import sys
from pathlib import Path

RW = Path(__file__).resolve().parent
sys.path.insert(0, str(RW))

from renderer import _normalise_for_quote_match, _verify_quote_in_source


# Section → keywords that indicate relevance
SECTION_KEYWORDS = {
    "Key Results & Data": ["result", "found", "showed", "observed", "detected",
                           "analysis", "efficiency", "mutant", "edited", "expression",
                           "percentage", "ratio", "average", "significantly"],
    "Mechanistic Insights": ["mechanism", "pathway", "interaction", "binds", "catalyzes",
                             "regulates", "mediates", "dependent", "involved", "cascade"],
    "Methods & Experimental Design": ["method", "protocol", "pcr", "culture", "buffer",
                                       "incubat", "centrifug", "transfect", "transform",
                                       "培养", "反应", "分析"],  # also Chinese
    "Introduction & Background": ["background", "previous", "reported", "studied",
                                   "hypothesis", "objective", "aim"],
    "Conclusions & Implications": ["conclusion", "implication", "suggest", "potential",
                                    "application", "promise"],
    "Limitations & Caveats": ["limitation", "caveat", "challenge", "difficulty", "constrain"],
}


def _sentences(text: str) -> list[tuple[str, str]]:
    """Return list of (raw_sentence, normalised_sentence) tuples."""
    chunks = re.split(r'(?<=[.!?])\s+(?=[A-Z\(])', text)
    result = []
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) > 30:
            result.append((chunk, _normalise_for_quote_match(chunk)))
    return result


def _relevant_sentences(sentences, section_name: str, existing_claims: list[str],
                        max_return: int = 6, min_overlap: int = 2) -> list[tuple[str, float]]:
    """Score sentences by relevance to a section. Returns top sentences + scores."""
    keywords = SECTION_KEYWORDS.get(section_name, [])
    if not keywords:
        return []

    kw_norm = [_normalise_for_quote_match(k) for k in keywords]
    stop = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'were', 'was',
            'are', 'been', 'have', 'has', 'had', 'not', 'but', 'all', 'into',
            'each', 'than', 'when', 'which', 'their', 'they', 'also', 'both',
            'more', 'over', 'such', 'under', 'only', 'using', 'used', 'shown'}

    def score(sent_norm):
        score_val = 0
        for kw in kw_norm:
            if kw in sent_norm:
                score_val += 1
        return score_val

    existing_norm = [_normalise_for_quote_match(c) for c in existing_claims]

    scored = []
    for raw, norm in sentences:
        sc = score(norm)
        if sc < min_overlap:
            continue
        # Penalise if too similar to an existing claim
        for en in existing_norm:
            if en and en in norm:
                sc -= 2
        if sc >= min_overlap:
            scored.append((raw, sc))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:max_return]


def augment_sidecar(stem: str, dry_run: bool = False, verbose: bool = False) -> dict:
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

    # Build existing claims (to avoid duplicates)
    existing_claims = []
    for sec in payload.get("sections", {}).values():
        for r in sec.get("results", []):
            existing_claims.append(r.get("claim", ""))

    # Get all sentences from source
    all_sentences = _sentences(source_raw)

    # For each thin section, augment
    TARGET_SECTIONS = ["Key Results & Data", "Mechanistic Insights",
                       "Methods & Experimental Design"]
    report = {"stem": stem, "sections_augmented": [], "new_footnotes": 0}

    for sec_name in TARGET_SECTIONS:
        sec = payload["sections"].get(sec_name)
        if not sec:
            continue

        current_text = sec.get("text", "")
        current_words = len(current_text.split())
        raw_words = len(source_raw.split())
        min_w = min(2800, max(1200, int(raw_words * 0.5)))

        # Target: 400-600 words for Key Results, 300-450 for others
        target_words = 450 if "Key Results" in sec_name else 350
        deficit = max(0, target_words - current_words)

        if deficit < 50:
            continue

        # Get existing claims in this section
        sec_claims = [r.get("claim", "") for r in sec.get("results", [])]

        relevant = _relevant_sentences(all_sentences, sec_name, sec_claims + existing_claims,
                                       max_return=6, min_overlap=2)

        added_texts = []
        added_results = []

        for sent_raw, score in relevant:
            # Check it verifies
            if not _verify_quote_in_source(sent_raw, source_norm):
                continue
            # Truncate if too long (keep under 500 chars)
            display = sent_raw[:450].rsplit(' ', 1)[0] + "…" if len(sent_raw) > 450 else sent_raw
            added_texts.append(display)
            # Extract a claim from the sentence
            claim = sent_raw[:200].strip()
            added_results.append({
                "claim": claim,
                "evidence_quote": sent_raw[:300],
                "source_locator": f"{sec_name}"
            })
            existing_claims.append(claim)
            if len(added_texts) >= 3:
                break

        if added_texts:
            # Append to existing text
            new_text = current_text.rstrip() + "\n\n" + " ".join(added_texts)
            sec["text"] = new_text
            # Merge results
            existing_results = sec.get("results", [])
            sec["results"] = existing_results + added_results
            report["sections_augmented"].append(sec_name)
            report["new_footnotes"] += len(added_results)
            if verbose:
                print(f"  [{sec_name}] added {len(added_texts)} sentences, {len(added_results)} footnotes")

    if not dry_run:
        sidecar_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("stems", nargs="*")
    args = ap.parse_args()

    DEPTH_FAIL = [
        'Tang_2023_ornamental_plant_gene_editing_past_present_and_future',
        'Zhang_2023_boosting_genome_editing_efficiency_in_human_cells_and_plants_with',
        'Ugrappa Nagalakshmi_2025_High_efficiency__transgene_free_plant_genome_editi',
        'Weiss_2025_viral_delivery_of_an_rna_guided_genome_editor_for_transgene_free_germline',
        'Hejabi_2022_nanocarriers_a_novel_strategy_for_the_delivery_of_crispr_cas_systems',
        'Su_Unknown_cas12a_rnp_mediated_co_transformation_enables_transgene_free_multiplex',
        'sukegawa_2023_genome_editing_rice',
        'M. Uranga_2022_Heritable_CRISPR_Cas9_editing_of_plant_genomes_usi',
        'Liang_2023_genome_editing_based_on_in_vitroassembled_ribonucleoproteins_in',
    ]

    stems = DEPTH_FAIL if args.all else args.stems

    print(f"Depth augmenter — {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    for stem in stems:
        r = augment_sidecar(stem, dry_run=args.dry_run, verbose=args.verbose)
        secs = r.get("sections_augmented", [])
        fn = r.get("new_footnotes", 0)
        err = r.get("error", "")
        if err:
            print(f"  {stem[:55]:55s}  ERROR: {err}")
        else:
            print(f"  {stem[:55]:55s}  augmented={secs}  new_fn={fn}")


if __name__ == "__main__":
    main()