import sys
from pathlib import Path

sys.path.insert(0, '.')
import validation
import lint_wiki
from scripts.resummarize_queue import mark_done

from scripts.summaries_wave3_part1 import wave3_part1
from scripts.summaries_wave3_part2 import wave3_part2
from scripts.summaries_wave3_part3 import wave3_part3

all_wave3 = {}
all_wave3.update(wave3_part1)
all_wave3.update(wave3_part2)
all_wave3.update(wave3_part3)

print(f"Total Wave 3 summaries to write & validate: {len(all_wave3)}")

val = validation.SummaryValidator()
results = []

target_dir = Path("wiki/sources/uncategorized")
target_dir.mkdir(parents=True, exist_ok=True)

for filename, content in all_wave3.items():
    # 1. Validate
    res = val.validate(content)
    lint_res = lint_wiki.validate_source_page(content)
    
    assert res.valid, f"Validation failed for {filename}: {res.errors}"
    assert res.score >= 90, f"Score too low for {filename}: {res.score}"
    assert len(lint_res) == 0, f"Lint errors for {filename}: {lint_res}"
    
    # 2. Write atomically
    target_path = target_dir / filename
    target_path.write_text(content.strip() + "\n", encoding="utf-8")
    
    # 3. Mark done in queue
    stem = Path(filename).stem
    mark_done(stem, "worker_vpc", int(res.score))
    
    results.append({
        "filename": filename,
        "valid": res.valid,
        "score": res.score,
        "missing": res.missing_sections,
        "warnings": res.warnings,
        "lint_errors": lint_res
    })
    print(f"✓ [{res.score}/100] Successfully processed and saved: {filename}")

print("\n--- Wave 3 Summary Validation Report ---")
for r in results:
    print(f"- {r['filename']}: Valid={r['valid']}, Score={r['score']}, Warnings={len(r['warnings'])}, LintErrors={len(r['lint_errors'])}")

print("\nAll 15 Wave 3 papers processed successfully!")
