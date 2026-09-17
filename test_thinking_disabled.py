"""test_thinking_disabled.py — apply thinking disabled to the real pipeline path."""
import httpx, os, time, json, sys
sys.path.insert(0, '.')
import summarize_pipeline as sp
keys = os.environ.get('HCNSEC_KEYS','').split(',')
keys = [k.strip() for k in keys if k.strip()]
if not keys: sys.exit('no keys')
wl = json.load(open('agent_worklist.json'))
# pick a short-ish paper
for x in wl:
    if x.get('status')=='pending' and x.get('raw_path') and 1500 <= (x.get('raw_words') or 0) <= 3000:
        rp = x.get('raw_path')
        if os.path.exists(rp):
            raw = open(rp).read()
            stem = x.get('stem')
            print(f'paper: {stem} ({len(raw)} chars, ~{len(raw.split())} words)')
            break
else:
    # any pending
    for x in wl:
        if x.get('status')=='pending' and x.get('raw_path'):
            rp = x.get('raw_path')
            raw = open(rp).read()
            stem = x.get('stem')
            print(f'paper: {stem} ({len(raw)} chars, ~{len(raw.split())} words)')
            break

c = httpx.Client(timeout=600)
key = keys[0]
system = "Reply with ONLY a JSON object. No reasoning, no explanation."
user = sp.USER_PROMPT_TEMPLATE + "\n" + raw
payload = {
    "model": "sensenova-6.7-flash-lite",
    "max_tokens": 30000,
    "temperature": 0,
    "messages": [{"role":"system","content":system},{"role":"user","content":user}],
}
extra = {"thinking": {"type": "disabled"}}
payload.update(extra)
t0 = time.time()
print('POSTING...')
r = c.post("https://api.hcnsec.cn/v1/chat/completions",
           headers={"Authorization": f"Bearer {key}","Content-Type":"application/json"},
           json=payload, timeout=600)
tt = time.time() - t0
data = r.json()
msg = data.get('choices',[{}])[0].get('message',{}) if 'error' not in data else {}
content = msg.get('content','') or ''
reasoning = msg.get('reasoning','') or ''
usage = data.get('usage',{})
err = data.get('error')
obj = sp.extract_json(content)
if obj:
    secs = obj.get('sections',{})
    sec_len = len(secs) if isinstance(secs,dict) else len(secs)
    fn = 0
    if isinstance(secs,dict):
        for k2,v2 in secs.items():
            if isinstance(v2,dict) and 'results' in v2:
                fn += len(v2['results']) if isinstance(v2['results'],list) else 0
    print(f'RESULT: total={tt:.1f}s content={len(content)} reason={len(reasoning)} usage={usage} PARSED sections={sec_len} footnotes={fn}')
else:
    print(f'RESULT: total={tt:.1f}s content={len(content)} reason={len(reasoning)} usage={usage} NOJSON')
c.close()