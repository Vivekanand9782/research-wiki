import sys
from pathlib import Path

sys.path.insert(0, '.')
import validation
import lint_wiki
from scripts.resummarize_queue import mark_done

from scripts.summaries_wave5_part1 import wave5_part1
from scripts.summaries_wave5_part2 import wave5_part2
from scripts.bioethanol_wave5_batch1 import W5_BATCH_1

all_wave5 = {}
all_wave5.update(wave5_part1)
all_wave5.update(wave5_part2)
for stem, content in W5_BATCH_1.items():
    filename = f"{stem}.md" if not stem.endswith(".md") else stem
    all_wave5[filename] = content

print(f"Total Wave 5 summaries to write & validate: {len(all_wave5)}")

val = validation.SummaryValidator()
results = []

target_dir = Path("wiki/sources/uncategorized")
target_dir.mkdir(parents=True, exist_ok=True)

for filename, content in all_wave5.items():
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
    mark_done(stem, "worker_wave5", int(res.score))
    
    results.append({
        "filename": filename,
        "valid": res.valid,
        "score": res.score,
        "missing": res.missing_sections,
        "warnings": res.warnings,
        "lint_errors": lint_res
    })
    print(f"✓ [{res.score}/100] Successfully processed and saved: {filename}")

print("\n--- Wave 5 Summary Validation Report ---")
for r in results:
    print(f"- {r['filename']}: Valid={r['valid']}, Score={r['score']}, Warnings={len(r['warnings'])}, LintErrors={len(r['lint_errors'])}")

print(f"\nAll {len(results)} Wave 5 papers processed successfully!")
