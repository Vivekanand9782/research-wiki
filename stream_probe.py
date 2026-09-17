"""stream_probe.py — measure streaming performance of hcnsec sensenova."""
import httpx, os, time, json, sys
sys.path.insert(0, '.')
import summarize_pipeline as sp
keys = os.environ.get('HCNSEC_KEYS','').split(',')
keys = [k.strip() for k in keys if k.strip()]
if not keys:
    sys.exit('no keys')
c = httpx.Client(timeout=400)
key = keys[0]
wl = json.load(open('agent_worklist.json'))
for x in wl:
    if x.get('status')=='pending' and x.get('raw_path') and 800 <= (x.get('raw_words') or 0) <= 2500:
        rp = x.get('raw_path')
        if os.path.exists(rp):
            raw = open(rp).read()
            stem = x.get('stem')
            print(f'paper: {stem} ({len(raw)} chars)')
            break
else:
    sys.exit('no paper')

system = "Reply with ONLY a JSON object. No reasoning."
user = sp.USER_PROMPT_TEMPLATE + "\n" + raw
payload = {
    "model": "sensenova-6.7-flash-lite",
    "max_tokens": 15000,
    "temperature": 0,
    "stream": True,
    "messages": [{"role":"system","content":system},{"role":"user","content":user}],
}
t0 = time.time()
r = c.post("https://api.hcnsec.cn/v1/chat/completions",
           headers={"Authorization": f"Bearer {key}","Content-Type":"application/json"},
           json=payload, timeout=400)
tttfb = time.time() - t0
print(f'TTFT: {tttfb:.1f}s', flush=True)
content = ''
samples = []
chunks = 0
for raw_bytes in r.iter_bytes():
    now = time.time() - t0
    if now > 280:
        print(f'ABORT at {now:.0f}s', flush=True)
        break
    line = raw_bytes.decode('utf-8','replace').strip()
    if not line.startswith('data:'):
        continue
    data = line[5:].strip()
    if data == '[DONE]':
        break
    try:
        d = json.loads(data)
    except:
        continue
    tok = d.get('choices', [{}])[0].get('delta', {}).get('content') or ''
    if tok:
        content += tok
        chunks += 1
        if chunks in [1, 5, 10, 50, 100, 200, 500]:
            samples.append((chunks, round(now,1), len(content)))
            print(f'  chunk{chunks} at {now:.0f}s content={len(content)}', flush=True)
total = time.time() - t0
print(f'Total: {total:.1f}s, content={len(content)}, chunks={chunks}', flush=True)
obj = sp.extract_json(content)
if obj:
    secs = obj.get('sections', {})
    sec_len = len(secs) if isinstance(secs, dict) else len(secs)
    print(f'PARSE OK: {sec_len} sections', flush=True)
else:
    print('Not parseable yet', flush=True)
    print('Tail 400:', content[-400:], flush=True)
r.close()
c.close()