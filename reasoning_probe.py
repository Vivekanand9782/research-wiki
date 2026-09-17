"""test_reasoning.py — check where sensenova emits tokens at various configs."""
import httpx, os, time, json, sys
keys = os.environ.get('HCNSEC_KEYS','').split(',')
keys = [k.strip() for k in keys if k.strip()]
if not keys: sys.exit('no keys')

def probe(name, messages, max_tokens, extra=None):
    payload = {"model":"sensenova-6.7-flash-lite","max_tokens":max_tokens,"temperature":0,"messages":messages}
    if extra: payload.update(extra)
    c = httpx.Client(timeout=120)
    t0 = time.time()
    r = c.post("https://api.hcnsec.cn/v1/chat/completions",
               headers={"Authorization": f"Bearer {keys[0]}","Content-Type":"application/json"},
               json=payload, timeout=120)
    tt = time.time()-t0
    data = r.json()
    msg = data.get('choices',[{}])[0].get('message',{}) if 'error' not in data else {}
    content = msg.get('content','') or ''
    reasoning = msg.get('reasoning','') or ''
    usage = data.get('usage',{})
    err = data.get('error')
    print(f'{name}: {tt:.1f}s content={len(content)} reason={len(reasoning)} err={err}')
    if content: print(f'  content[0:100]: {content[:100]}')
    if reasoning and not content: print(f'  reason[0:100]: {reasoning[:100]}')
    c.close()

# 1. Tiny prompt, small tokens
probe('tiny_low', [{"role":"user","content":"Say hello."}], 200)
# 2. Tiny prompt, high tokens
probe('tiny_high', [{"role":"user","content":"Say hello."}], 1500)
# 3. System prompt "JSON only" + 200 tokens
probe('system_json_low', [{"role":"system","content":"Reply with ONLY a JSON object."},{"role":"user","content":"Say hello."}], 200)
# 4. With thinking disabled
probe('thinking_disabled', [{"role":"user","content":"Say hello."}], 200, extra={"thinking":{"type":"disabled"}})
# 5. With response_format json_object
probe('json_object', [{"role":"user","content":"Return {\"a\":1}"}], 200, extra={"response_format":{"type":"json_object"}})