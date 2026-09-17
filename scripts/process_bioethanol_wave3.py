"""Orchestration script to write all 15 Wave 3 bioethanol summaries, validate, and mark done."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from validation import SummaryValidator
import lint_wiki
from scripts.resummarize_queue import mark_done, load_state, print_status

from scripts.bioethanol_wave3_batch1 import W3_BATCH_1
from scripts.bioethanol_wave3_batch2 import W3_BATCH_2
from scripts.bioethanol_wave3_batch3 import W3_BATCH_3

WIKI_DIR = Path("wiki/sources/uncategorized")
WIKI_DIR.mkdir(parents=True, exist_ok=True)

ALL_SUMMARIES = {}
ALL_SUMMARIES.update(W3_BATCH_1)
ALL_SUMMARIES.update(W3_BATCH_2)
ALL_SUMMARIES.update(W3_BATCH_3)

print(f"Total Wave 3 summaries to process: {len(ALL_SUMMARIES)}")

validator = SummaryValidator()
results = {}

for stem, summary_text in ALL_SUMMARIES.items():
    # 1. Validate in-memory
    v_res = validator.validate(summary_text)
    l_res = lint_wiki.validate_source_page(summary_text)
    
    if not v_res.valid or v_res.score < 90 or len(l_res) > 0:
        print(f"FAILED validation for {stem}: Score={v_res.score}, Errors={v_res.errors}, Lint={l_res}")
        sys.exit(1)
        
    # 2. Write to wiki/sources/uncategorized/<stem>.md
    dest_path = WIKI_DIR / f"{stem}.md"
    dest_path.write_text(summary_text.strip() + "\n", encoding="utf-8")
    
    # 3. Read back and re-validate from disk
    disk_text = dest_path.read_text(encoding="utf-8")
    disk_v_res = validator.validate(disk_text)
    disk_l_res = lint_wiki.validate_source_page(disk_text)
    
    if not disk_v_res.valid or disk_v_res.score < 90 or len(disk_l_res) > 0:
        print(f"FAILED disk validation for {stem}: Score={disk_v_res.score}, Errors={disk_v_res.errors}, Lint={disk_l_res}")
        sys.exit(1)
        
    # 4. Mark done in resummarize_queue
    mark_done(stem, "worker_bioethanol", disk_v_res.score)
    results[stem] = {
        "score": disk_v_res.score,
        "valid": disk_v_res.valid,
        "lint_errors": len(disk_l_res),
        "path": str(dest_path)
    }
    print(f"Successfully processed & written: {stem}.md (Score: {disk_v_res.score}, Lint errors: 0)")

print("\n--- Summary Report ---")
for s, r in results.items():
    print(f"  - {s}: Score={r['score']}, Valid={r['valid']}, Path={r['path']}")

print("\n--- Queue State ---")
print_status()
