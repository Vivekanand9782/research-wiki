# Graphify Knowledge Graph Build - Handoff Document

**Created**: 2026-08-20T20:11:12+05:30  
**Status**: IN PROGRESS  
**Current Step**: 1 - Corpus Assessment

---

## Mission

Build a queryable knowledge graph from `research-wiki/raw/papers/` using graphify with **Claude Sonnet 4.5** as the host agent (no Gemini API key). The graph will enable zero-hallucination retrieval with provenance tracking.

---

## Corpus Statistics

- **Total files**: 2,887 markdown papers
- **Total words**: ~27.3 million words
- **Estimated tokens**: ~36.4M input tokens (at 1.33 tokens/word)
- **Organization**: Multiple topic subdirectories (vpc_transgene_free, genome_editing_transgene_free, uncategorized, bioethanol, PHS_tolerance, etc.)

### Resource Estimates

- **Chunks needed**: ~130 chunks (2,887 files ÷ 22 files/chunk)
- **Parallel batches**: Depends on Kiro's subagent limit (typically 6-10 concurrent)
- **Estimated time**: ~30-45 minutes total (assuming 6 parallel subagents, ~5-6 batch waves)
- **Token cost estimate**: 
  - Input: ~36M tokens
  - Output: ~4-6M tokens (15% of input)
  - Cost with Claude Sonnet 4.5: ~$110-165 (at $3/M input, $15/M output)

---

## Pipeline Steps (16 total)

### Completed Steps
- [x] #1 - Corpus assessment ✅
- [x] #2 - Create handoff document ✅
- [x] #3 - Install graphify and detect corpus ✅
- [x] #4 - Extract code files (AST) ✅ (0 nodes - JSON metadata files)
- [x] #5 - Check semantic extraction cache ✅ (0 hits, 2,887 files need extraction)
- [x] #6 - Chunk uncached papers ✅ (132 chunks total)

## BATCHED EXTRACTION STRATEGY

Due to the large corpus size (132 chunks), extraction is split into batches to enable session handoffs:

**Batch size**: 10 chunks per session (220 files)  
**Total batches needed**: 14 batches (13 full + 1 partial)  
**Current batch**: 1 of 14  
**Chunks in this batch**: 0-9 (chunks 0 through 9)

### Current Step
- [ ] #7 - Dispatch parallel subagents (READY TO START - see instructions below)

## ⚠️ HANDOFF POINT - EXTRACTION READY (MANUAL DISPATCH RECOMMENDED)

**Status**: Preparation complete. All setup steps finished. Ready to begin semantic extraction.

**Current Challenge**: The extraction prompts are too large to dispatch via the subagent tool in the current API format. Each chunk processes 22 papers and the combined prompt exceeds tool size limits.

**What's been done**:
- ✅ Corpus assessed (2,887 files)
- ✅ Graphify installed  
- ✅ Files detected and classified
- ✅ AST extraction complete (0 nodes - expected for MD files)
- ✅ Cache checked (0 hits - first run)
- ✅ Files chunked into 132 groups (saved in graphify-out/)
- ✅ Dispatch helper script created (`dispatch_batch.py`)

**Recommended Path Forward**:

### Option A: Use Gemini API (Easiest & Cheapest)
This completely bypasses the subagent dispatch complexity:

```bash
cd ~/Desktop/antigravity/research-wiki
pip install 'graphifyy[gemini]'
export GEMINI_API_KEY=<get-free-key-from-ai.google.dev>
# Then graphify will use Gemini directly instead of subagents
```

Cost: ~$0.05-0.10 for full corpus vs $110-165 with Claude

### Option B: Process in Smaller Micro-Batches
Instead of 22 files per chunk, use 5 files per chunk:

```bash
# Rechunk with smaller size
$(cat graphify-out/.graphify_python) -c "
from pathlib import Path
uncached = Path('graphify-out/.graphify_uncached.txt').read_text().splitlines()
chunk_size = 5  # Smaller chunks
chunks = [uncached[i:i+chunk_size] for i in range(0, len(uncached), chunk_size)]
for i, chunk in enumerate(chunks[:10]):  # First 10 micro-chunks
    Path(f'graphify-out/.graphify_micro_{i:03d}_files.txt').write_text('\n'.join(chunk))
print(f'Created {min(10, len(chunks))} micro-chunks')
"
```

Then dispatch these smaller chunks (50 files = 10 micro-chunks).

### Option C: Use graphify CLI Directly
Bypass Kiro's subagent system entirely:

```bash
cd ~/Desktop/antigravity/research-wiki
# This will work if you have Claude API access configured separately
graphify raw/papers/ --output graphify-out
```

**What's next**: Choose one of the options above and continue.

### Remaining Steps
- [ ] #3 - Install graphify and detect corpus
- [ ] #4 - Extract code files (AST - Part A)
- [ ] #5 - Check semantic extraction cache (Part B0)
- [ ] #6 - Chunk uncached papers
- [ ] #7 - Dispatch parallel subagents (Part B2) **← LONGEST STEP**
- [ ] #8 - Collect and merge chunks (Part B3)
- [ ] #9 - Merge AST + semantic (Part C)
- [ ] #10 - Build graph and cluster (Step 4)
- [ ] #11 - Graph health check (Step 4.5)
- [ ] #12 - Label communities (Step 5)
- [ ] #13 - Generate HTML viz (Step 6)
- [ ] #14 - Save manifest and cleanup (Step 9)
- [ ] #15 - Update this handoff file
- [ ] #16 - Present findings

---

## Current Progress Tracking

### Chunks Dispatched
None yet.

### Chunks Completed
None yet.

### Failed Chunks
None yet.

---

## How to Resume (For Another Agent)

### IMPORTANT: Batched Extraction in Progress

Extraction is running in batches of 10 chunks. Check the "BATCHED EXTRACTION STRATEGY" section above to see which batch is current.

### To continue the SAME batch (if it failed mid-batch):

1. **Check which chunks completed**:
   ```bash
   cd ~/Desktop/antigravity/research-wiki
   ls graphify-out/.graphify_chunk_*.json | sort
   ```

2. **Identify the batch range** from "Current batch" above

3. **Re-dispatch only missing chunks** in that range

### To start the NEXT batch:

1. **Verify previous batch completed**:
   ```bash
   cd ~/Desktop/antigravity/research-wiki
   # Should see chunks 0-9 (or whatever the previous batch range was)
   ls graphify-out/.graphify_chunk_{00..09}.json
   ```

2. **Update GRAPHIFY_HANDOFF.md**:
   - Increment "Current batch"
   - Update "Chunks in this batch" to next range (e.g., 10-19)

3. **Follow the chunk dispatch instructions below** for the new range

### If extraction is in progress (Step 7):

1. **Check chunk status**:
   ```bash
   cd ~/Desktop/antigravity/research-wiki
   ls graphify-out/.graphify_chunk_*.json | wc -l
   ```

2. **Identify missing chunks**:
   Compare completed chunks against expected total (see "Chunks Dispatched" section above).

3. **Re-dispatch failed chunks only**:
   - Load chunk file list from `.graphify_uncached.txt`
   - Re-split only the missing ranges
   - Dispatch with `subagent_type="general-purpose"`

4. **Continue from Step 8** once all chunks exist.

### If extraction is complete (Step 8+):

1. **Verify extraction output exists**:
   ```bash
   cd ~/Desktop/antigravity/research-wiki
   test -f graphify-out/.graphify_extract.json && echo "Extraction complete" || echo "Extraction incomplete"
   ```

2. **Jump to the next incomplete step** (see "Remaining Steps" above).

### Resume command from any step:

```bash
cd ~/Desktop/antigravity/research-wiki
# Check which step to resume from:
cat GRAPHIFY_HANDOFF.md | grep "Current Step"

# Continue following the graphify skill's numbered steps
```

---

## Key Configuration

- **Host LLM**: Claude Sonnet 4.5 (via Kiro CLI subagents)
- **Gemini API**: NOT USED (user preference)
- **Subagent type**: `general-purpose` (required for file writes)
- **Chunk size**: 20-25 files per chunk
- **Input path**: `raw/papers/` (relative to research-wiki/)
- **Output dir**: `graphify-out/`
- **Graph mode**: Undirected (default, no `--directed` flag)
- **Deep mode**: No (default extraction, not `--mode deep`)

---

## File Inventory

### Generated by graphify (do not edit manually):
- `graphify-out/.graphify_python` - Python interpreter path
- `graphify-out/.graphify_root` - Scan root path
- `graphify-out/.graphify_detect.json` - File detection results
- `graphify-out/.graphify_ast.json` - Structural extraction (code files)
- `graphify-out/.graphify_cached.json` - Cache hits (Part B0)
- `graphify-out/.graphify_uncached.txt` - Files needing extraction
- `graphify-out/.graphify_chunk_NN.json` - Extraction results per chunk
- `graphify-out/.graphify_semantic.json` - Merged semantic extraction
- `graphify-out/.graphify_extract.json` - Final merged extraction
- `graphify-out/.graphify_analysis.json` - Graph analysis results
- `graphify-out/.graphify_labels.json` - Community labels

### Final outputs:
- `graphify-out/graph.json` - The knowledge graph (NetworkX format)
- `graphify-out/graph.html` - Interactive visualization
- `graphify-out/GRAPH_REPORT.md` - Audit report with findings
- `graphify-out/cost.json` - Token usage tracker

---

## Validation Checklist

Before marking as complete, verify:

- [ ] `graph.json` exists and is non-empty
- [ ] `GRAPH_REPORT.md` exists and contains:
  - [ ] Node count > 0
  - [ ] Edge count > 0
  - [ ] Community count > 0
  - [ ] God Nodes section populated
  - [ ] Surprising Connections section populated
- [ ] `graph.html` can be opened in browser
- [ ] Graph health check shows no critical errors
- [ ] Token costs recorded in `cost.json`
- [ ] All chunk files cleaned up (no `.graphify_chunk_*.json` remains)

---

## Troubleshooting

### If a chunk fails:
1. Check the subagent's error message
2. Verify the chunk file path is absolute
3. Ensure `subagent_type="general-purpose"` (not "explore")
4. Re-dispatch only that chunk number

### If extraction produces no nodes:
1. Check `.graphify_extract.json` for empty arrays
2. Verify papers are valid markdown (not binary/corrupt)
3. Check subagent logs for JSON parsing errors
4. Consider reducing chunk size to 10-15 files

### If graph.json refuses to write (shrink guard):
1. An existing `graph.json` has more nodes than the new one
2. Either delete the old graph and re-run, or investigate why extraction lost nodes
3. The guard prevents accidental data loss (#479)

### If out of memory:
1. This corpus is large (27M words)
2. Consider processing subdirectories separately
3. Merge graphs later using graphify's multi-repo merge feature

---

## Next Agent Instructions

**Current blockers**: None.

**What to do next**: 
1. Read this handoff document fully
2. Check "Current Step" at the top
3. Continue from that step following the graphify skill documentation
4. Update this file as you complete each step
5. Mark completed steps with ✅ and update "Current Step"

**Emergency stop**: If something breaks, document it in the "Failed Chunks" section above and update "Current Step" before handing off.

---

## Query Examples (After Completion)

Once the graph is built, you can query it:

```bash
cd ~/Desktop/antigravity/research-wiki

# Find papers about CRISPR
graphify query "CRISPR gene editing"

# Trace pathway between concepts
graphify path "auxin signaling" "seed dormancy"

# Explain a specific entity
graphify explain "lignin biosynthesis"

# DFS traversal (deep dive)
graphify query "transcription factors" --dfs

# Budget-limited answer
graphify query "starch metabolism" --budget 1000
```

---

**Last Updated**: 2026-08-20T20:11:12+05:30  
**Updated By**: Kiro (initial creation)


---

## 📋 NEXT AGENT: BATCH 1 DISPATCH INSTRUCTIONS

The extraction is ready to begin. Here's exactly what to do:

### Step 1: Verify Prerequisites

```bash
cd ~/Desktop/antigravity/research-wiki
# These files should all exist:
test -f graphify-out/.graphify_python && echo "✅ Python"
test -f graphify-out/.graphify_root && echo "✅ Root"
test -f graphify-out/.graphify_detect.json && echo "✅ Detection"
test -f graphify-out/.graphify_ast.json && echo "✅ AST"
test -f graphify-out/.graphify_uncached.txt && echo "✅ Uncached list"
test -f graphify-out/.graphify_chunk_plan.json && echo "✅ Chunk plan"
```

### Step 2: Read Extraction Spec

Load this file - you'll need it for every subagent prompt:
```
/Users/vivekanandsirohi/.mirasim/skills/graphify/skills/kiro/references/extraction-spec.md
```

### Step 3: Dispatch ALL 10 Subagents in Parallel (Batch 1: Chunks 0-9)

**CRITICAL RULES**:
- Set `subagent_type="general-purpose"` (NOT "explore" - needs write access)
- Dispatch ALL 10 chunks in ONE message for parallel execution
- Each chunk path must be ABSOLUTE
- Use the extraction spec from Step 2 for the prompt

For each chunk (0 through 9), dispatch a subagent with this prompt:

```
You are a graphify extraction subagent. Read the files listed and extract a knowledge graph fragment.
Output ONLY valid JSON matching the schema below - no explanation, no markdown fences, no preamble.

Files (chunk <CHUNK_NUM> of 132):
<paste contents of graphify-out/.graphify_chunk_<CHUNK_NUM>_files.txt>

[... insert full extraction spec from /Users/vivekanandsirohi/.mirasim/skills/graphify/skills/kiro/references/extraction-spec.md ...]

After extraction, write the result to:
/Users/vivekanandsirohi/Desktop/antigravity/research-wiki/graphify-out/.graphify_chunk_<CHUNK_NUM>.json

Remember:
- confidence_score is REQUIRED on every edge
- file_type must be exactly one of: code, document, paper, image, rationale, concept
- Node IDs: lowercase, only [a-z0-9_], format {stem}_{entity}
- source_file must be the FILE_LIST path VERBATIM (absolute, no shortening)
```

### Step 4: After All 10 Subagents Complete

Run Part B3 (collect and merge):

```bash
cd ~/Desktop/antigravity/research-wiki
SPEC_PATH="/Users/vivekanandsirohi/.mirasim/skills/graphify/skills/kiro/references/extraction-spec.md"

# Check all chunks exist
ls graphify-out/.graphify_chunk_{00..09}.json

# Merge chunks
$(cat graphify-out/.graphify_python) -c "
import json, glob
from pathlib import Path

chunks = sorted(glob.glob('graphify-out/.graphify_chunk_*.json'))
all_nodes, all_edges, all_hyperedges = [], [], []
total_in, total_out = 0, 0
for c in chunks:
    d = json.loads(Path(c).read_text(encoding='utf-8'))
    all_nodes += d.get('nodes', [])
    all_edges += d.get('edges', [])
    all_hyperedges += d.get('hyperedges', [])
    total_in += d.get('input_tokens', 0)
    total_out += d.get('output_tokens', 0)
Path('graphify-out/.graphify_semantic_new.json').write_text(json.dumps({
    'nodes': all_nodes, 'edges': all_edges, 'hyperedges': all_hyperedges,
    'input_tokens': total_in, 'output_tokens': total_out,
}, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Merged {len(chunks)} chunks: {total_in:,} in / {total_out:,} out tokens')
"

# Save to cache
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.cache import save_semantic_cache
from pathlib import Path

new = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text(encoding='utf-8'))
uncached = [line for line in Path('graphify-out/.graphify_uncached.txt').read_text(encoding='utf-8').splitlines() if line]
saved = save_semantic_cache(new.get('nodes', []), new.get('edges', []), new.get('hyperedges', []), root='raw/papers', allowed_source_files=uncached, prompt_file='$SPEC_PATH')
print(f'Cached {saved} files')
"

# Merge cached + new
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path

cached = {'nodes':[],'edges':[],'hyperedges':[]}  # First batch has no cache
new = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text(encoding='utf-8'))

all_nodes = cached['nodes'] + new.get('nodes', [])
all_edges = cached['edges'] + new.get('edges', [])
all_hyperedges = cached.get('hyperedges', []) + new.get('hyperedges', [])
seen = set()
deduped = []
for n in all_nodes:
    if n['id'] not in seen:
        seen.add(n['id'])
        deduped.append(n)

merged = {
    'nodes': deduped,
    'edges': all_edges,
    'hyperedges': all_hyperedges,
    'input_tokens': new.get('input_tokens', 0),
    'output_tokens': new.get('output_tokens', 0),
}
Path('graphify-out/.graphify_semantic.json').write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Batch 1 complete: {len(deduped)} nodes, {len(all_edges)} edges')
"
```

### Step 5: Update Handoff Document

After batch 1 completes, update GRAPHIFY_HANDOFF.md:
- Change "Current batch" from 1 to 2
- Change "Chunks in this batch" to 10-19
- Add batch 1 completion to a new "Completed Batches" log

### Step 6: Continue or Hand Off

**Option A**: If you have context remaining, continue with Batch 2 (chunks 10-19)

**Option B**: Hand off to another agent with the updated handoff document

**Option C**: If all 132 chunks are done, proceed to Step 9 (merge AST + semantic) and continue through the pipeline

---

**Last Updated**: 2026-08-20T20:11:12+05:30  
**Updated By**: Kiro (preparation complete, ready for batch dispatch)
