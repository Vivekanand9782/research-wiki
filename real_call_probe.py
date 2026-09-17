"""real_call_probe.py — test real summary call with thinking disabled."""
import httpx, os, time, json, sys
sys.path.insert(0, '.')
import summarize_pipeline as sp
keys = os.environ.get('HCNSEC_KEYS','').split(',')
keys = [k.strip() for k in keys if k.strip()]
if not keys: sys.exit('no keys')
wl = json.load(open('agent_worklist.json'))
for x in wl:
    if x.get('status')=='pending' and x.get('raw_path') and 2400 <= (x.get('raw_words') or 0) <= 5000:
        rp = x.get('raw_path')
        if os.path.exists(rp):
            raw = open(rp).read()
            stem = x.get('stem')
            print(f'paper: {stem} ({len(raw)} chars, ~{len(raw.split())} words)')
            break
else:
    sys.exit('no paper')

def probe(label, extra_payload):
    c = httpx.Client(timeout=600)
    t0 = time.time()
    system = "Reply with ONLY a JSON object. No reasoning, no explanation, no chain of thought, no markdown fences, no prose."
    user = sp.USER_PROMPT_TEMPLATE + "\n" + raw
    payload = {
        "model": "sensenova-6.7-flash-lite",
        "max_tokens": 30000,
        "temperature": 0,
        "messages": [{"role":"system","content":system},{"role":"user","content":user}],
    }
    payload.update(extra_payload)
    tt = time.time()
    r = c.post("https://api.hcnsec.cn/v1/chat/completions",
               headers={"Authorization": f"Bearer {keys[0]}","Content-Type":"application/json"},
               json=payload, timeout=600)
    tttfb = time.time()-t0
    data = r.json()
    msg = data.get('choices',[{}])[0].get('message',{}) if 'error' not in data else {}
    content = msg.get('content','') or ''
    reasoning = msg.get('reasoning','') or ''
    usage = data.get('usage',{})
    total = time.time()-t0
    obj = sp.extract_json(content)
    if obj:
        secs = obj.get('sections',{})
        sec_len = len(secs) if isinstance(secs,dict) else len(secs)
        fn = 0
        if isinstance(secs,dict):
            for v in secs.values():
                if isinstance(v,dict) and 'results' in v:
                    fn += len(v['results']) if isinstance(v['results'],list) else 0
        print(f'{label}: ttft={tttfb:.0f}s total={total:.0f}s content={len(content)} reason={len(reasoning)} usage={usage} PARSED sec={sec_len} fn={fn}')
    else:
        print(f'{label}: ttft={tttfb:.0f}s total={total:.0f}s content={len(content)} reason={len(reasoning)} usage={usage} NOJSON')
    c.close()

# 1. Current config (no thinking, no response_format)
probe('default', {})
# 2. With thinking disabled
probe('thinking_disabled', {"thinking":{"type":"disabled"}})