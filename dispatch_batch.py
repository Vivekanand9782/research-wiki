#!/usr/bin/env python3
"""
Helper script to dispatch graphify extraction chunks via subagents.
Usage: python3 dispatch_batch.py <start_chunk> <end_chunk>
Example: python3 dispatch_batch.py 0 9
"""
import sys
import json
from pathlib import Path

# Load extraction spec
spec_path = Path("/Users/vivekanandsirohi/.mirasim/skills/graphify/skills/kiro/references/extraction-spec.md")
extraction_spec = spec_path.read_text(encoding='utf-8')

# Extract the prompt template from the spec (between the ``` markers)
lines = extraction_spec.split('\n')
in_template = False
template_lines = []
for line in lines:
    if line.strip() == '```' and not in_template:
        in_template = True
        continue
    elif line.strip() == '```' and in_template:
        break
    elif in_template:
        template_lines.append(line)

prompt_template = '\n'.join(template_lines)

# Get chunk range from args
if len(sys.argv) != 3:
    print("Usage: python3 dispatch_batch.py <start_chunk> <end_chunk>")
    print("Example: python3 dispatch_batch.py 0 4")
    sys.exit(1)

start_chunk = int(sys.argv[1])
end_chunk = int(sys.argv[2])

project_root = Path("/Users/vivekanandsirohi/Desktop/antigravity/research-wiki")

print(f"\n=== Batch Dispatch: Chunks {start_chunk}-{end_chunk} ===\n")

for chunk_num in range(start_chunk, end_chunk + 1):
    chunk_file = project_root / f"graphify-out/.graphify_chunk_{chunk_num:02d}_files.txt"
    
    if not chunk_file.exists():
        print(f"❌ Chunk {chunk_num:02d}: file list not found")
        continue
    
    # Read file list
    file_list = chunk_file.read_text(encoding='utf-8').strip()
    
    # Build prompt - be careful with FILE_LIST to not replace it in the JSON schema
    # First replace in the "Files (" line only
    lines = prompt_template.split('\n')
    processed_lines = []
    for i, line in enumerate(lines):
        if line.startswith('Files (chunk CHUNK_NUM'):
            line = line.replace("CHUNK_NUM", str(chunk_num))
            line = line.replace("TOTAL_CHUNKS", "132")
            processed_lines.append(line)
            processed_lines.append(file_list)  # Add file list on next lines
        elif 'FILE_LIST' in line and i < 5:  # Only first few lines before the schema
            # This is in the instructions, replace it
            processed_lines.append(line.replace("FILE_LIST", file_list))
        elif line.startswith('- DEEP_MODE (if --mode deep)'):
            processed_lines.append('- DEEP_MODE: false')
        elif 'CHUNK_NUM' in line or 'TOTAL_CHUNKS' in line:
            line = line.replace("CHUNK_NUM", str(chunk_num))
            line = line.replace("TOTAL_CHUNKS", "132")
            processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    prompt = '\n'.join(processed_lines)
    
    # Add write instruction
    output_path = project_root / f"graphify-out/.graphify_chunk_{chunk_num:02d}.json"
    prompt += f"\n\nAfter extraction, write the result to:\n{output_path.absolute()}"
    
    # Save prompt for manual dispatch
    prompt_file = project_root / f"graphify-out/.graphify_chunk_{chunk_num:02d}_prompt.txt"
    prompt_file.write_text(prompt, encoding='utf-8')
    
    file_count = len([l for l in file_list.split('\n') if l.strip()])
    print(f"✅ Chunk {chunk_num:02d}: prepared prompt for {file_count} files")
    print(f"   Prompt saved to: {prompt_file.name}")

print(f"\n=== Next Steps ===")
print(f"1. Review prompts in graphify-out/.graphify_chunk_XX_prompt.txt")
print(f"2. Dispatch each as a subagent with subagent_type='general-purpose'")
print(f"3. Wait for all chunks to complete")
print(f"4. Run merge script to combine results")
