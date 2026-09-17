#!/usr/bin/env python3
"""Comprehensive Adversarial Empirical Stress Harness for Milestones 3, 4, and 5.

This harness executes deterministic, parameterized boundary stress tests,
latency benchmarks, entity preservation checks, and CLI verification.
"""

from __future__ import annotations

import collections
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Setup sys.path
HERE = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from rag_engine import (
    DOMAIN_SYNONYM_CLUSTERS,
    CitationBackfillResult,
    ClaimVerificationResult,
    RAGEngine,
    _GENE_QTL_RE,
    _NUMERIC_MEASURE_RE,
    _PERCENTAGE_RE,
    _compute_adaptive_window,
)


def log_test(title: str):
    print(f"\n{'='*70}\n[TEST] {title}\n{'='*70}")


def run_stress_test_adaptive_proximity():
    log_test("1. ADAPTIVE PROXIMITY WINDOWS (2 to 25 Tokens & 240-800 Char Scaling)")
    
    # 1.1 Mathematical formula verification across 0 to 30 tokens
    expected_windows = {
        0: 240, 1: 240, 2: 240,
        3: 380, 4: 520, 5: 660, 6: 800,
        7: 800, 10: 800, 15: 800, 20: 800, 25: 800, 30: 800
    }
    for n_tok, expected in expected_windows.items():
        w = _compute_adaptive_window(n_tok)
        assert w == expected, f"Token count {n_tok} expected {expected}, got {w}"
    print("  ✓ Mathematical formula verified across all token counts (0..30 tokens).")

    # 1.2 Boundary distance verification
    tokens_6 = ["tokenA", "tokenB", "tokenC", "tokenD", "tokenE", "tokenF"]
    # Case A: Tokens separated by filler such that span between first and last needed token is ~750 chars (inside 800)
    filler_140 = " " + ("x" * 135) + " "
    text_inside = (
        "tokenA" + filler_140 +
        "tokenB" + filler_140 +
        "tokenC" + filler_140 +
        "tokenD" + filler_140 +
        "tokenE" + filler_140 +
        "tokenF"
    )
    assert RAGEngine._phrase_or_proximity(text_inside, tokens_6) is True
    print("  ✓ 6-token query spanning multi-sentence text within 800 chars PASSES.")

    # Case B: All tokens separated by 900 chars -> any 2 tokens are > 900 chars apart -> should fail
    filler_900 = " " + ("y" * 900) + " "
    text_outside = (
        "tokenA" + filler_900 +
        "tokenB" + filler_900 +
        "tokenC" + filler_900 +
        "tokenD" + filler_900 +
        "tokenE" + filler_900 +
        "tokenF"
    )
    assert RAGEngine._phrase_or_proximity(text_outside, tokens_6) is False
    print("  ✓ 6-token query with tokens separated beyond 800 chars FAILS correctly.")

    # 1.3 Extreme 25-token query
    tokens_25 = [f"gene{i}" for i in range(1, 26)]
    # Needed = (25+1)//2 = 13 tokens.
    text_cluster_13 = " ".join(tokens_25[:13]) + " " + ("z" * 600) + " " + " ".join(tokens_25[13:])
    assert RAGEngine._phrase_or_proximity(text_cluster_13, tokens_25) is True
    print("  ✓ 25-token query with needed quorum clustered within 800 chars PASSES.")

    # 1.4 Worst-Case O(N) Complexity Stress Test
    large_filler = ("The quick brown fox jumps over the lazy dog. " * 500)  # ~22,500 chars
    text_dense = (
        large_filler +
        " Cas9 RNP delivery into Solanum tuberosum protoplasts enables marker-free editing. " +
        large_filler +
        " Cas9 RNP delivery into Solanum tuberosum protoplasts enables marker-free editing. " +
        large_filler
    )  # ~68,000 chars
    tokens_dense = ["cas9", "rnp", "solanum", "tuberosum", "protoplasts", "marker-free"]

    t0 = time.perf_counter()
    for _ in range(50):
        res = RAGEngine._phrase_or_proximity(text_dense.lower(), tokens_dense)
        assert res is True
    elapsed_ms = (time.perf_counter() - t0) * 1000
    print(f"  ✓ O(N) Sliding Window Stress Test: 50 iterations over 68KB dense text in {elapsed_ms:.2f}ms ({elapsed_ms/50:.2f}ms/op).")


def run_stress_test_entity_protection_and_synonyms():
    log_test("2. GENE SYMBOL, QTL, MEASUREMENT PRESERVATION & SYNONYM EXPANSION")
    engine = RAGEngine()

    test_cases = [
        {
            "name": "Standard Gene Symbols",
            "query": "TaMFT codA Cas9 ZmNST2",
            "expected_protected": ["TaMFT", "codA", "Cas9", "ZmNST2"],
        },
        {
            "name": "QTLs and Complex Alleles",
            "query": "QPhs.ocs-3A.1 qPHS-3A TaMFT-A1 OsDMR6_1 DMR6-2",
            "expected_protected": ["QPhs.ocs-3A.1", "qPHS-3A", "TaMFT-A1", "OsDMR6_1", "DMR6-2"],
        },
        {
            "name": "Percentages and Ranges",
            "query": "45.5% 12.5 - 87.3% 0.01% >95% 100%",
            "expected_protected": ["45.5%", "12.5 - 87.3%", "0.01%", "100%"],
        },
        {
            "name": "Discrete Percentage Pairs",
            "query": "12.5% - 87.3%",
            "expected_protected": ["12.5%", "87.3%"],
        },
        {
            "name": "Measurements and Temperatures",
            "query": "10 mM 500 bp 37°C 2.5 mg/L 100 μM 50 nM",
            "expected_protected": ["10 mM", "500 bp", "37°C", "2.5 mg/L", "100 μM", "50 nM"],
        },
        {
            "name": "Single Synonym Cluster with Entities",
            "query": "TaMFT Cas9 in transgene-free crops",
            "expected_protected": ["TaMFT", "Cas9"],
            "expected_synonyms": ["dna-free", "marker-free", "rnp"],
        },
        {
            "name": "Multi-Concept Query with Prepositions and Synonyms",
            "query": "TaMFT and Cas9 in vegetatively propagated crops using viral vector",
            "expected_protected": ["TaMFT", "Cas9"],
            "expected_synonyms": ["clonal", "tuber", "potato", "vige", "geminivirus", "trv"],
        },
    ]

    for tc in test_cases:
        clauses = engine._decompose_and_expand_clauses(tc["query"])
        all_tokens = [tok for _, tokens in clauses for tok in tokens]
        all_tokens_lower = [tok.lower() for tok in all_tokens]

        # Check protected entities
        for exp in tc["expected_protected"]:
            assert exp in all_tokens or exp.lower() in all_tokens_lower, f"Failed in {tc['name']}: {exp} missing from {all_tokens}"
        
        # Check synonyms if present
        if "expected_synonyms" in tc:
            for syn in tc["expected_synonyms"]:
                assert syn.lower() in all_tokens_lower, f"Failed in {tc['name']}: synonym {syn} missing"

        print(f"  ✓ {tc['name']}: {len(tc['expected_protected'])} entities verified without mutation.")

    # Substring isolation check
    negative_checks = [
        ("vegetation cover ecology", ["potato", "banana", "clonal"]),
        ("commercial propagation", ["potato", "cassava"]),
        ("protoplastic pressure", ["single cell", "peg transfection"]),
    ]
    for q, forbidden in negative_checks:
        clauses = engine._decompose_and_expand_clauses(q)
        all_toks = [tok.lower() for _, tokens in clauses for tok in tokens]
        for f in forbidden:
            assert f not in all_toks, f"False positive expansion for query '{q}': found '{f}'"
    print("  ✓ Word-boundary negative checks passed: no false-positive expansions.")

    # Adversarial Edge-Case Discovery: Multi-cluster queries without prepositions
    edge_query = "TaMFT Cas9 vegetatively propagated transgene-free"
    edge_clauses = engine._decompose_and_expand_clauses(edge_query)
    edge_tokens = [tok for _, toks in edge_clauses for tok in toks]
    print(f"\n  [Adversarial Edge-Case Finding]:")
    print(f"  Query: '{edge_query}'")
    print(f"  Decomposed clauses: {[lbl for lbl, _ in edge_clauses]}")
    has_tamft = "TaMFT" in edge_tokens or "tamft" in [t.lower() for t in edge_tokens]
    if not has_tamft:
        print(f"  ⚠️ Vulnerability Confirmed: When a query contains multiple synonym clusters without prepositions (e.g. 'vegetatively propagated' AND 'transgene-free'), `clauses = matched_clusters` replaces the query clauses with ONLY the cluster names, dropping non-cluster entities like TaMFT.")
    else:
        print(f"  TaMFT was preserved.")


def run_stress_test_claim_verification():
    log_test("3. CLAIM VERIFICATION (--verify) ACCURACY & LATENCY BENCHMARK")
    engine = RAGEngine()

    # 3.1 Real-world supported claims against production index
    supported_claims = [
        "codA negative selection enables transgene-free editing",
        "TaMFT regulates seed dormancy in wheat",
        "heat treatment enhances Cas9 RNP editing",
    ]
    for claim in supported_claims:
        t0 = time.perf_counter()
        res = engine.verify_claim(claim)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  • Supported Claim: '{claim}' -> Verdict: {res.verdict} (Conf: {res.confidence:.2f}, Latency: {elapsed:.1f}ms, Source: {res.primary_source})")
        assert res.verdict in ("SUPPORTED", "CONTRADICTED"), f"Unexpected verdict for {claim}: {res.verdict}"
        assert elapsed < 1500.0, f"Latency exceeded 1.5s: {elapsed:.1f}ms"

    # 3.2 Contradicted claims
    contradicted_claims = [
        "Cas9 guarantees 100% editing efficiency without off-targets in all plant species",
        "codA negative selection always eliminates all transgenic tissue in all plant species",
    ]
    for claim in contradicted_claims:
        t0 = time.perf_counter()
        res = engine.verify_claim(claim)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  • Contradicted Claim: '{claim}' -> Verdict: {res.verdict} (Conf: {res.confidence:.2f}, Latency: {elapsed:.1f}ms, Reason: {res.reason[:60]}...)")
        assert res.verdict == "CONTRADICTED", f"Expected CONTRADICTED for {claim}, got {res.verdict}"
        assert res.confidence >= 0.80

    # 3.3 Out-of-domain claims & False Positive Audit
    print("\n  Auditing Out-of-Domain and Fabricated Claims against Live Corpus:")
    ood_claims = [
        ("bovine somatotropin increases milk production in dairy cattle", "Unindexed Animal Physiology"),
        ("metformin induces pluripotency in wheat shoot apical meristem", "Fabricated Drug Action"),
        ("zebrafish fin regeneration through oct4 reprogramming", "Unindexed Vertebrate Biology"),
        ("aspirin inhibits prostaglandin synthesis in human platelets", "Human Pharmacology"),
        ("asdfghjk zxcvbnm completely fabricated nonexistent query 123456789", "Random Gibberish"),
        ("   ", "Empty String"),
    ]
    for claim, category in ood_claims:
        t0 = time.perf_counter()
        res = engine.verify_claim(claim)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  • [{category}] Claim: '{claim.strip() or '<EMPTY>'}'")
        print(f"    Verdict: {res.verdict} (Conf: {res.confidence:.2f}, Latency: {elapsed:.1f}ms)")
        if res.primary_source:
            print(f"    Primary Source: {res.primary_source}")
        if res.verdict == "SUPPORTED" and category not in ("Supported",):
            print(f"    ⚠️ False Positive Finding: Claim '{claim}' was returned as SUPPORTED ({res.confidence:.2f}) because of low lexical threshold (word_ratio >= 0.35 with generic word overlap).")

    # 3.4 50-Run Latency Benchmark
    print("\n  Benchmarking 50 consecutive verify_claim executions...")
    latencies = []
    bench_claim = "codA negative selection enables transgene-free editing"
    for _ in range(50):
        t0 = time.perf_counter()
        res = engine.verify_claim(bench_claim)
        latencies.append((time.perf_counter() - t0) * 1000)

    mean_lat = sum(latencies) / len(latencies)
    latencies.sort()
    p50_lat = latencies[len(latencies) // 2]
    p95_lat = latencies[int(len(latencies) * 0.95)]
    p99_lat = latencies[int(len(latencies) * 0.99)]
    max_lat = max(latencies)

    print(f"  ✓ Claim Verification Latency (50 runs): Mean={mean_lat:.2f}ms | P50={p50_lat:.2f}ms | P95={p95_lat:.2f}ms | P99={p99_lat:.2f}ms | Max={max_lat:.2f}ms")
    assert mean_lat < 1000.0, f"Mean latency exceeded 1.0s target: {mean_lat:.2f}ms"
    assert p95_lat < 1500.0, f"P95 latency exceeded 1.5s ceiling: {p95_lat:.2f}ms"


def run_stress_test_citation_backfill():
    log_test("4. CITATION BACKFILL (--backfill) ACCURACY & CITATION FORMAT")
    engine = RAGEngine()

    statements = [
        {
            "statement": "heat treatment enhances Cas9 RNP editing",
            "expected_slug_contains": "poddar",
            "expected_author": "Poddar",
            "expected_year": 2023,
        },
        {
            "statement": "TaMFT seed dormancy in wheat",
            "expected_slug_contains": "tamft",
        },
        {
            "statement": "codA negative selection transgene-free potato",
            "expected_slug_contains": "banfalvi",
        },
    ]

    for tc in statements:
        t0 = time.perf_counter()
        res = engine.backfill_citation(tc["statement"])
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  • Statement: '{tc['statement']}'")
        print(f"    Citation: {res.markdown_citation}")
        print(f"    Slug:     {res.slug}")
        print(f"    DOI:      {res.doi}")
        print(f"    Authors:  {res.authors}")
        print(f"    Year:     {res.year}")
        print(f"    Excerpt:  {res.excerpt[:120]}...")
        print(f"    Latency:  {elapsed:.1f}ms")

        assert isinstance(res, CitationBackfillResult)
        assert len(res.markdown_citation) > 0
        assert re.match(r"^\([A-Za-z]+(?:\s+et\s+al\.)?,\s+\d{4}\)\[\[[a-z0-9_-]+\]\]$", res.markdown_citation), f"Invalid markdown citation format: {res.markdown_citation}"
        assert res.total_ms < 1500.0

    # Degenerate input
    empty_res = engine.backfill_citation("   ")
    assert empty_res.markdown_citation == ""
    assert empty_res.slug == ""
    assert empty_res.year == 0
    print("  ✓ Empty input backfill handled gracefully.")


def run_stress_test_cli_commands():
    log_test("5. CLI SUBPROCESS EXECUTION & BENCHMARKING (scripts/rag_query.py)")
    python_bin = sys.executable
    script_path = str(WORKSPACE_ROOT / "scripts" / "rag_query.py")

    cli_tests = [
        [python_bin, script_path, "--verify", "codA negative selection enables transgene-free editing"],
        [python_bin, script_path, "--verify", "codA negative selection enables transgene-free editing", "--json"],
        [python_bin, script_path, "--backfill", "heat treatment enhances Cas9 RNP editing"],
        [python_bin, script_path, "--backfill", "heat treatment enhances Cas9 RNP editing", "--json"],
        [python_bin, script_path, "vegetatively propagated crops transgene-free", "--mode", "evidence"],
    ]

    for cmd in cli_tests:
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        elapsed = (time.perf_counter() - t0) * 1000
        assert proc.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {proc.stderr}"
        
        if "--json" in cmd:
            # Verify JSON validity
            parsed = json.loads(proc.stdout)
            assert isinstance(parsed, dict)
            assert "total_ms" in parsed or "verdict" in parsed or "markdown_citation" in parsed
            print(f"  ✓ CLI JSON command succeeded in {elapsed:.1f}ms: {' '.join(cmd[-2:])}")
        else:
            assert len(proc.stdout) > 0
            print(f"  ✓ CLI Human-readable command succeeded in {elapsed:.1f}ms: {' '.join(cmd[2:4])}")


def main():
    print("=" * 70)
    print("🚀 STARTING ADVERSARIAL EMPIRICAL STRESS TEST SUITE")
    print("=" * 70)

    t_start = time.perf_counter()
    run_stress_test_adaptive_proximity()
    run_stress_test_entity_protection_and_synonyms()
    run_stress_test_claim_verification()
    run_stress_test_citation_backfill()
    run_stress_test_cli_commands()
    total_time = time.perf_counter() - t_start

    print("\n" + "=" * 70)
    print(f"🎉 ALL ADVERSARIAL STRESS TESTS COMPLETED IN {total_time:.2f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
