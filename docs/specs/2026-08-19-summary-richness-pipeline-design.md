# Summary Richness Pipeline — Design Spec

> Date: 2026-08-19 | Status: approved (user chose hybrid repair + full backfill incl. thin papers)

## Problem

Wiki pages under `wiki/sources/` modified before 2026-08-16 have thin, old-spec
summaries (~7 KB, no evidence footnotes, null metadata). Pages from 2026-08-16 on
are rich (~15–30 KB, 15 sections, 8+ verified footnotes) because they come from the
agent deep-summary campaign (`summarize_pipeline.py` → sidecar JSON → gated render).

Measured root causes:

- 318/666 sidecars (48%) have **zero** `results[]` footnotes — the model ignores the
  instruction; the render gate flags them and never writes the page.
- 299/666 sidecars are depth-short (<2,000 words vs 2,800 gate).
- Flagged/failed stems are never repaired or retried.
- `MIN_RAW_WORDS=2400` skips ~70 thin papers entirely.
- Driver stopped Aug 18; ~1,760 pending papers undrained.

## Design

### 1. Pipeline optimization (`summarize_pipeline.py`)

- Restructured prompt: footnote requirements first, explicit JSON skeleton with
  `results` arrays, per-section footnote minimums.
- Post-parse quality check (footnote count + word depth, adaptive to raw length);
  on shortfall, ONE corrective follow-up call in the same conversation handing the
  model its own JSON and demanding the missing `results[]` / expansion.
- Still-short sidecars are written with `"repair_needed": true` for the mechanical
  repair stage.
- `MIN_RAW_WORDS` lowered to 500; dynamic `date_created`/`date_updated`.

### 2. Mechanical repair fallback (`repair_sidecars.py`)

Generalizes `augment_depth.py`. For any gate-failing sidecar:

- Mine sentences verbatim from the raw paper text (keyword + numeric scoring),
  verify via `renderer._verify_quote_in_source` (quotes valid by construction).
- Inject verified `results[]` footnotes into Key Results & Data / Mechanistic
  Insights / Methods until the adaptive footnote minimum is met.
- Append verified relevant sentences to depth-short sections until the adaptive
  word minimum is met.
- Sources: `--from-report` (flagged in agent_render_report.json), `--repair-needed`
  (sidecar flag), `--all`, or explicit stems.

### 3. Gate proportionality (`ingest_agent.py`)

Depth floor never exceeds source length (prevents padding pressure on thin
papers): `min_words = min(2800, max(min(1200, raw_words), raw_words*0.5))`.

### 4. Backfill campaign (`driver.sh` + one-shot prep)

- One-shot: demote worklist `failed` → `pending`; clear `failed` set in
  `agent_deep_summary_state.json` (old failures happened under the old prompt).
- Driver loop: after each wave render, run `repair_sidecars.py --from-report`
  then re-render, so flagged sidecars are repaired in-cycle.
- Stage A: repair + re-render the ~330 existing stuck sidecars immediately.
- Stage B: restart detached daemon for all ~1,760 pending incl. thin papers.
- Stage C: census report (words/footnotes per page) for final verification.

## Verification

Pilot of ~15 papers (zero-footnote, depth-short, thin) must pass all gates;
quotes are substring-verified so fabrication is mechanically impossible.
Census script proves old-spec page count trends to zero.

## Non-goals

No model change (stays `sensenova-6.7-flash-lite`), no git writes, no changes to
the render spec section set.
