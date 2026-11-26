"""Stage: keyframes via Cloudflare Workers AI (FLUX.1 schnell). Every prompt = style_block + prompt, same seed per shot.
Usage: python pipeline/keyframes.py [--only s03]"""
import argparse, base64, time, requests
from common import *

MODEL = "@cf/black-forest-labs/flux-1-schnell"
STEPS = 6  # schnell is distilled: 4-8 steps

def gen(prompt, seed, acc, tok):
    r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{MODEL}",
        headers={"Authorization": f"Bearer {tok}"}, json={"prompt": prompt, "steps": STEPS, "seed": seed}, timeout=180)
    r.raise_for_status()
    return base64.b64decode(r.json()["result"]["image"])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only"); a = ap.parse_args()
    sb = load_storyboard(); acc, tok = need("CF_ACCOUNT_ID"), need("CF_API_TOKEN")
    (OUT / "keyframes").mkdir(parents=True, exist_ok=True)
    for s in sb["shots"]:
        if a.only and s["id"] != a.only: continue
        prompt = s["image_prompt"].replace("{character}", sb["character"]) + ", " + sb["style_block"]
        path = OUT / "keyframes" / f"{s['id']}.jpg"
        k = h(prompt, s["seed"], STEPS, MODEL)
        if is_cached(path, k):
            log_call("keyframes", MODEL, {}, shot=s["id"], cached=True); print(s["id"], "cached"); continue
        t = time.time()
        img = retry(lambda: gen(prompt, s["seed"], acc, tok), stage="keyframes", shot=s["id"], model=MODEL)
        path.write_bytes(img); mark_cached(path, k)
        log_call("keyframes", MODEL, {"steps": STEPS, "prompt": prompt}, seed=s["seed"], latency_s=time.time() - t, shot=s["id"])
        print(s["id"], "generated"); time.sleep(1)

if __name__ == "__main__":
    main()
