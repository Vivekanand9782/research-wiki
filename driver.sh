#!/usr/bin/env bash
# driver.sh — runs summarize_pipeline.py in waves, renders after each,
# until all pending papers (min raw_words >= 2400) are written.
set -euo pipefail

cd "$(dirname "$0")"

: "${HCNSEC_KEYS:?set HCNSEC_KEYS env var with comma-separated keys}"

WAVE=16
CONC=4
MAX_WAVES=600

STATE=driver_progress.json
[[ -f "$STATE" ]] || echo '{"waves":0,"papers_written":0,"last_updated":"","failed_stems":[]}' > "$STATE"

log()  { echo "[$(date +'%H:%M:%S')] $*" | tee -a driver.log; }

render_new() {
    local count
    count=$(find raw/papers -maxdepth 1 -name '*.summary.json' \
              -newer driver_progress.json 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$count" -gt 0 ]]; then
        log "Rendering $count new sidecars..."
        python3 ingest_agent.py render --pending 2>&1 | tail -8 >> driver.log || true
    fi
    # Repair stage: deterministically fix any sidecars the render gate flagged
    # (verbatim-quote mining — no API calls), then re-render them.
    log "Repair pass: mechanical fix for flagged sidecars..."
    python3 repair_sidecars.py --from-report --repair-needed >> driver.log 2>&1 || true
    python3 ingest_agent.py render --pending 2>&1 | tail -5 >> driver.log || true
}

remaining_count() {
    python3 -c "
import json, os
wl=json.load(open('agent_worklist.json'))
seen=set()
if os.path.exists('agent_deep_summary_state.json'):
    s=json.load(open('agent_deep_summary_state.json'))
    seen=set(s.get('completed',[]))|set(s.get('failed',[]))
for f in os.listdir('raw/papers'):
    if f.endswith('.summary.json'):
        seen.add(f[:-len('.summary.json')])
n=0
for x in wl:
    rp = x.get('raw_path')
    if x.get('status')=='pending' and rp and os.path.exists(rp):
        rw = x.get('raw_words') or 0
        if rw>=500 and x.get('stem') not in seen:
            n+=1
print(n)
"
}

# Truncate log for this run
: > driver.log
log "=== driver started: wave=$WAVE conc=$CONC max_waves=$MAX_WAVES ==="

wave=0
while true; do
    remaining=$(remaining_count)
    if [[ "$remaining" -le 0 ]]; then
        log "Queue drained. Final render..."
        python3 ingest_agent.py render --pending 2>&1 | tail -15 >> driver.log || true
        log "=== ALL DONE ==="
        break
    fi
    if [[ "$wave" -ge "$MAX_WAVES" ]]; then
        log "Hit wave cap $MAX_WAVES. Manual inspection needed."
        break
    fi
    log "Wave $((wave+1)): $remaining remaining. Dispatching $WAVE @ concurrency $CONC."

    python3 summarize_pipeline.py --limit "$WAVE" --concurrency "$CONC" 2>&1 >> driver.log || {
        log "Pipeline errored. Pausing 60s and retrying."
        sleep 60
    }

    # Promote failed stems to 'failed' in the worklist so they stop blocking future waves.
    python3 - <<'PY'
import json, os
p = 'agent_worklist.json'
try:
    wl = json.load(open(p))
    state = json.load(open('agent_deep_summary_state.json'))
    failed = set(state.get('failed', []))
    changed = 0
    for item in wl:
        if item.get('status') == 'pending' and item.get('stem') in failed:
            item['status'] = 'failed'
            changed += 1
    if changed:
        json.dump(wl, open(p, 'w'), indent=2)
except Exception as e:
    print(f'worklist promote skipped: {e}')
PY

    render_new
    touch driver_progress.json

    NOW=$(date -Iseconds)
    python3 -c "
import json
p='driver_progress.json'
s=json.load(open(p))
s['waves']+=1
s['papers_written'] += $WAVE
s['last_updated']='$NOW'
json.dump(s, open(p,'w'), indent=2)
" 2>/dev/null || true

    wave=$((wave+1))
    sleep 5
done

log "Final render pass..."
python3 ingest_agent.py render --pending 2>&1 | tail -15 >> driver.log || true
python3 ingest_agent.py progress 2>&1 | head -15 >> driver.log || true
log "=== RUN COMPLETE ==="