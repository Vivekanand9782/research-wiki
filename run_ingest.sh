#!/usr/bin/env bash
# Run the offline ingest for a set of PDFs, then refresh the processed-papers
# manifest. Re-running this script is safe: ingest_parallel.py skips any paper
# whose fingerprint is already in wiki/.understand-anything/intermediate/
# pipeline_state.json (the "ingest" step), so no paper is processed twice.
#
# Usage:
#   ./run_ingest.sh                      # process all data/ PDFs (incremental)
#   ./run_ingest.sh path/to/a.pdf ...    # process specific PDFs only
#
# Env:
#   AI_MODEL        model id (default: ollama/ornith:9b)
#   WORKERS         concurrent AI workers (default: 1 — Ollama serializes anyway)
set -euo pipefail

cd "$(dirname "$0")"
export AI_MODEL="${AI_MODEL:-ollama/ornith:9b}"
WORKERS="${WORKERS:-1}"

echo ">> AI_MODEL=$AI_MODEL  WORKERS=$WORKERS"

if [ "$#" -gt 0 ]; then
  python3 ingest_parallel.py --skip-prepass --no-rollup --workers "$WORKERS" "$@"
else
  python3 ingest_parallel.py --skip-prepass --no-rollup --workers "$WORKERS"
fi

echo ">> refreshing processed-papers manifest"
python3 update_processed_manifest.py
echo ">> done. See wiki/processed_papers.json"
