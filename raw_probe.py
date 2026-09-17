"""raw_probe.py — send a tiny prompt, measure TTFT, and dump raw response bytes."""
import httpx, os, time, json, sys
keys = os.environ.get('HCNSEC_KEYS','').split(',')
keys = [k.strip() for k in keys if k.strip()]
if not keys: sys.exit('no keys')
c = httpx.Client(timeout=300)
key = keys[0]

# Tiny paper — just the header + a paragraph
tiny = "Title: Test Paper. Authors: Author. Year: 2020. This is a short paper about rice grain dormancy genetics."

payloads = [
    {"name": "just_hello",
     "messages": [{"role":"user","content":"Say hello."}],
     "max_tokens": 50},
    {"name": "json_hello",
     "messages": [{"role":"user","content":"Return ONLY a JSON object: {\"a\":1}"}],
     "max_tokens": 50},
    {"name": "small_summary",
     "messages": [{"role":"system","content":"Reply with ONLY a JSON object."},{"role":"user","content":"Summarize this 1-paragraph paper in JSON. Paper: "+tiny}],
     "max_tokens": 500},
]
for p in payloads:
    t0 = time.time()
    r = c.post("https://api.hcnsec.cn/v1/chat/completions",
               headers={"Authorization": f"Bearer {key}","Content-Type":"application/json"},
               json={"model":"sensenova-6.7-flash-lite","temperature":0,**p}, timeout=120)
    tt = time.time()-t0
    data = r.json()
    msg = data.get('choices',[{}])[0].get('message',{}) if 'error' not in data else {}
    content = msg.get('content','') or ''
    reasoning = msg.get('reasoning','') or ''
    usage = data.get('usage',{})
    err = data.get('error')
    print(f"{p['name']}: {tt:.1f}s content={len(content)} reason={len(reasoning)} usage={usage} err={err}")
    if content[:50]:
        print(f"  first: {content[:80]}")
c.close()