# Architecture
**Contract:** `storyboard.json`, validated against `schema/storyboard.schema.json` at the start of every stage (`common.load_storyboard`).
Each shot carries its own reason, prompts, narration, English subtitle and seed.

**Stages** (each is a standalone script; a stage only reads the storyboard and the previous stage's files):
narration -> `outputs/narration/<id>.wav`; keyframes -> `outputs/keyframes/<id>.jpg`; music -> `outputs/music/score.*`; assemble -> `outputs/final_*.mp4`.

**Caching:** every output is keyed by a hash of its inputs (`common.h`). Narration: text+voice+style+model. Keyframe: full prompt+seed+steps+model.
Segment: hash of the source image/clip bytes + duration + aspect. Keys are stored in `outputs/.cache.json`. Change one shot, only that shot regenerates.

**Failure handling:** `common.retry` does exponential backoff (4 tries) and logs every failed attempt to `runs.jsonl`. Free-tier limits are handled by a short sleep between calls
and by re-running `make film` (cached shots are skipped, so a quota failure on shot 6 loses nothing). If video generation is unavailable, assembly falls back to Ken Burns on stills.

**Timing:** narration length sets shot length: `duration = max(planned, spoken + 1 s)`.

**Audio:** voice padded per shot -> concat -> sidechaincompress (thr 0.02, ratio 6, attack 300 ms, release 1500 ms) over music -> loudnorm to -14 LUFS, TP -1 dB (single pass).

**Secrets:** read from `.env` (git-ignored) or environment; never in code.
**Logging:** `runs.jsonl`, one line per call: timestamp, stage, model, shot, params, seed, latency, cost, status, cached.
