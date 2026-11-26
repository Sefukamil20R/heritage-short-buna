"""Stage: assembly (FFmpeg only, deterministic). Ken Burns on keyframes (or a Wan clip if outputs/clips/<id>.mp4 exists),
per-shot narration padding, sidechain ducking, loudnorm -14 LUFS, burned English subtitles, AI end card, both aspect ratios.
Usage: python pipeline/assemble.py [--radio] [--draft]"""
import argparse, subprocess, time, textwrap
from common import *

SIZES = {"vertical": (1080, 1920), "horizontal": (1920, 1080)}
FPS = 24
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS)]

def ff(args, shot=None, note=""):
    t = time.time()
    p = subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + args, capture_output=True, text=True, cwd=OUT)
    log_call("assemble", "ffmpeg", {"args": " ".join(args)[:300]}, latency_s=time.time() - t, shot=shot,
             status="ok" if p.returncode == 0 else "error", note=note)
    if p.returncode: raise SystemExit("ffmpeg failed:\n" + p.stderr[-1500:])

def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

def plan(sb):
    """Narration sets the shot length: duration = max(planned, spoken + 1s breathing room)."""
    items, t = [], 0.0
    for s in sb["shots"]:
        wav = OUT / "narration" / f"{s['id']}.wav"
        nd = dur(wav) if wav.exists() else 0.0
        d = round(max(s["duration_s"], nd + 1.0), 2)
        items.append({"s": s, "start": t, "d": d, "nd": nd}); t += d
    return items, t

def srt_time(x):
    h, m, sec = int(x // 3600), int(x % 3600 // 60), x % 60
    return f"{h:02d}:{m:02d}:{int(sec):02d},{int(round((sec % 1) * 1000)):03d}"

def write_srt(sb, items, total):
    cues = []
    for i, it in enumerate(items):
        text = "\n".join(textwrap.wrap(it["s"]["subtitle_en"], 38)[:2])
        cues.append((it["start"] + 0.4, it["start"] + it["d"] - 0.2, text))
    cues.append((total + 0.2, total + sb["endcard"]["duration_s"] - 0.1, sb["endcard"]["text"]))
    (OUT / "subs.srt").write_text("\n".join(f"{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues)), encoding="utf-8")

def audio_mix(sb, items, total, radio=False):
    total_all = total + (0 if radio else sb["endcard"]["duration_s"])
    (OUT / "audio").mkdir(exist_ok=True)
    parts = []
    for it in items:
        sid = it["s"]["id"]; wav = OUT / "narration" / f"{sid}.wav"; out = f"audio/v_{sid}.wav"
        if wav.exists():
            ff(["-i", f"narration/{sid}.wav", "-af", "adelay=400:all=1,apad", "-t", str(it["d"]), "-ar", "48000", "-ac", "1", out], sid)
        else:
            ff(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(it["d"]), out], sid, "no narration file")
        parts.append(out)
    if not radio:
        ff(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(sb["endcard"]["duration_s"]), "audio/v_card.wav"])
        parts.append("audio/v_card.wav")
    (OUT / "audio" / "voice.txt").write_text("".join(f"file '{p.split('/')[-1]}'\n" for p in parts))
    ff(["-f", "concat", "-safe", "0", "-i", "audio/voice.txt", "-c", "copy", "audio/voice.wav"])
    music = next((p for ext in ("wav", "mp3", "flac") for p in [OUT / "music" / f"score.{ext}"] if p.exists()),
                 OUT / "music" / "placeholder.wav")
    if not music.exists(): raise SystemExit("No music file: run `make music` first.")
    fo = max(total_all - 3, 0)
    fc = ("[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[vsc][vmix];"
          f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=2,afade=t=out:st={fo}:d=3,volume=0.7[m];"
          "[m][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500[duck];"
          "[vmix][duck]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1:LRA=11[out]")
    ff(["-i", "audio/voice.wav", "-stream_loop", "-1", "-i", str(music.relative_to(OUT)), "-filter_complex", fc,
        "-map", "[out]", "-t", str(total_all), "-ar", "48000", "audio/mix.wav"], note=f"music={music.name}")
    return total_all

def segment(it, idx, aspect, W, H):
    sid = it["s"]["id"]; img = OUT / "keyframes" / f"{sid}.jpg"; clip = OUT / "clips" / f"{sid}.mp4"
    out = OUT / "segments" / aspect / f"{sid}.mp4"; out.parent.mkdir(parents=True, exist_ok=True)
    src = clip if clip.exists() else img
    if not src.exists(): raise SystemExit(f"Missing {src}. Run `make keyframes`.")
    key = h(file_hash(src), it["d"], aspect, W, H, idx % 2)
    if is_cached(out, key): log_call("assemble", "ffmpeg", {}, shot=sid, cached=True); return out
    N = int(it["d"] * FPS)
    if clip.exists():
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},tpad=stop_mode=clone:stop_duration=10,fps={FPS}"
        ff(["-i", f"clips/{sid}.mp4", "-vf", vf, "-t", str(it["d"]), "-an"] + ENC + [str(out.relative_to(OUT))], sid, "wan clip")
    else:  # Ken Burns: alternate zoom-in / zoom-out so consecutive shots don't feel the same
        z = f"1+0.16*on/{N}" if idx % 2 == 0 else f"1.16-0.16*on/{N}"
        vf = (f"scale={int(W*1.5)}:{int(H*1.5)}:force_original_aspect_ratio=increase,crop={int(W*1.5)}:{int(H*1.5)},"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={N}:s={W}x{H}:fps={FPS}")
        ff(["-i", f"keyframes/{sid}.jpg", "-vf", vf, "-frames:v", str(N), "-an"] + ENC + [str(out.relative_to(OUT))], sid, "ken burns")
    mark_cached(out, key); return out

def render(sb, items, total, total_all, aspect, draft):
    W, H = SIZES[aspect]
    if draft: W, H = W // 2, H // 2
    segs = [segment(it, i, aspect, W, H) for i, it in enumerate(items)]
    card = OUT / "segments" / aspect / "card.mp4"
    ff(["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d={sb['endcard']['duration_s']}:r={FPS}"] + ENC + [str(card.relative_to(OUT))], note="end card base")
    lst = OUT / "segments" / aspect / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in segs + [card]))
    cat = f"segments/{aspect}/concat.mp4"
    ff(["-f", "concat", "-safe", "0", "-i", f"segments/{aspect}/list.txt", "-c", "copy", cat])
    fs = "FontSize=16,MarginV=70" if aspect == "vertical" else "FontSize=14,MarginV=20"
    style = f"{fs},Alignment=2,Outline=2,Shadow=1,PrimaryColour=&H00FFFFFF&"
    final = f"final_{aspect}.mp4"
    ff(["-i", cat, "-i", "audio/mix.wav", "-vf", f"subtitles=subs.srt:force_style='{style}'", "-map", "0:v", "-map", "1:a"]
       + ENC + ["-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], note=aspect)
    print("wrote", OUT / final)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--radio", action="store_true"); ap.add_argument("--draft", action="store_true")
    a = ap.parse_args(); sb = load_storyboard(); items, total = plan(sb)
    if a.radio:
        tot = audio_mix(sb, items, total, radio=True)
        ff(["-f", "lavfi", "-i", f"color=c=black:s=640x360:d={tot}:r=24", "-i", "audio/mix.wav", "-shortest",
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", "radio_cut.mp4"])
        print("radio cut:", OUT / "radio_cut.mp4", f"({tot:.0f}s)"); return
    write_srt(sb, items, total); tot = audio_mix(sb, items, total)
    for aspect in SIZES: render(sb, items, total, tot, aspect, a.draft)
    print(f"total length {tot:.1f}s (target 60-90s)")

if __name__ == "__main__":
    main()
