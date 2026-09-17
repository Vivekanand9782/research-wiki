#!/usr/bin/env bash
# scripts/precommit.sh

# Exit immediately if a command exits with a non-zero status.
set -e

GIT_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep 'generated_content/.*\.md$' || true)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

echo "Running Generative Checks on staged generated_content files..."

for FILE in $STAGED_FILES; do
    ABS_FILE="$GIT_ROOT/$FILE"
    echo "----------------------------------------------------"
    echo "Checking: $ABS_FILE"
    
    # 1. Validator
    if python3 "$PROJECT_ROOT/scripts/validate_manifest.py" "$ABS_FILE"; then
        echo "[PASS] Manifest Validator"
    else
        echo "[FAIL] Manifest Validator"
        exit 1
    fi

    # 2. Auditor
    if python3 "$PROJECT_ROOT/scripts/audit_cited_doc.py" "$ABS_FILE" --strict; then
        echo "[PASS] Cited Document Auditor"
    else
        echo "[FAIL] Cited Document Auditor"
        exit 1
    fi
done

echo "----------------------------------------------------"
echo "All generative checks passed!"
exit 0
