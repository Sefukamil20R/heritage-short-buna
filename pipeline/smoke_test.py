"""Call each provider once and log latency to runs.jsonl. Run: make smoke"""
import base64, time, requests
from common import need, log_call

def gemini():
    key = need("GEMINI_API_KEY"); model = "gemini-2.5-flash"  # any text model your key allows
    t = time.time()
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": key}, json={"contents": [{"parts": [{"text": "Say hi in Amharic."}]}]}, timeout=60)
    log_call("smoke", model, {}, latency_s=time.time() - t, status=str(r.status_code)); print("gemini", r.status_code)

def cloudflare():
    acc, tok = need("CF_ACCOUNT_ID"), need("CF_API_TOKEN")
    t = time.time()
    r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/black-forest-labs/flux-1-schnell",
        headers={"Authorization": f"Bearer {tok}"}, json={"prompt": "a cup of coffee", "steps": 4}, timeout=120)
    log_call("smoke", "flux-1-schnell", {"steps": 4}, latency_s=time.time() - t, status=str(r.status_code)); print("cloudflare", r.status_code)

if __name__ == "__main__":
    gemini(); cloudflare()
