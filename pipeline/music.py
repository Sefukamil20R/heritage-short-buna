"""Stage: music. The real score is made with ACE-Step on Kaggle (see kaggle/ACESTEP_STEPS.md) and saved as
outputs/music/score.wav|mp3|flac. If it is missing, a clearly-labelled placeholder drone is made with FFmpeg
so the pipeline still runs end to end (and the radio cut has a temp track)."""
import subprocess, time
from common import *

def main():
    sb = load_storyboard(); d = (OUT / "music"); d.mkdir(parents=True, exist_ok=True)
    for ext in ("wav", "mp3", "flac"):
        if (d / f"score.{ext}").exists():
            log_call("music", "ace-step-1.5", {"file": f"score.{ext}"}, cached=True, note="score supplied from Kaggle run")
            print("using", d / f"score.{ext}"); return
    ph = d / "placeholder.wav"
    if ph.exists(): print("placeholder exists"); return
    t = time.time(); n = sb["music"]["duration_s"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=110:duration={n}",
        "-f", "lavfi", "-i", f"sine=frequency=165:duration={n}", "-filter_complex",
        "amix=inputs=2,tremolo=f=0.2:d=0.5,volume=0.25", str(ph)], check=True)
    log_call("music", "ffmpeg-placeholder", {"duration": n}, latency_s=time.time() - t, note="TEMP TRACK, not the score")
    print("made placeholder (replace with ACE-Step score)")

if __name__ == "__main__":
    main()
