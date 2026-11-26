"""Stage: narration. One WAV per shot via Gemini TTS. Cached by hash of (text, voice, style, model).
Usage: python pipeline/narration.py [--only s03]"""
import argparse, base64, time, wave, requests
from common import *

MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")  # change if AI Studio lists a newer TTS model

def synth(text, voice, style, key):
    body = {"contents": [{"parts": [{"text": f"{style}: {text}"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                      headers={"x-goog-api-key": key}, json=body, timeout=120)
    r.raise_for_status()
    part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
    return base64.b64decode(part["data"])  # raw 16-bit PCM, 24 kHz, mono

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only"); a = ap.parse_args()
    sb = load_storyboard(); key = need("GEMINI_API_KEY")
    (OUT / "narration").mkdir(parents=True, exist_ok=True)
    voice = sb.get("voice", "Kore"); style = sb.get("voice_style", "Speak calmly and warmly")
    for s in sb["shots"]:
        if a.only and s["id"] != a.only: continue
        path = OUT / "narration" / f"{s['id']}.wav"
        k = h(s["narration"], voice, style, MODEL)
        if is_cached(path, k):
            log_call("narration", MODEL, {}, shot=s["id"], cached=True); print(s["id"], "cached"); continue
        t = time.time()
        pcm = retry(lambda: synth(s["narration"], voice, style, key), stage="narration", shot=s["id"], model=MODEL)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
        mark_cached(path, k)
        log_call("narration", MODEL, {"voice": voice, "chars": len(s["narration"])}, latency_s=time.time() - t, shot=s["id"])
        print(s["id"], "generated"); time.sleep(2)  # be gentle with free-tier rate limits

if __name__ == "__main__":
    main()
