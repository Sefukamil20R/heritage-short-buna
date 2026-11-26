# Heritage Short: "Buna" (Ethiopian coffee ceremony)
A 60-90 s AI short film, narrated in Amharic with English subtitles, made by a code pipeline.
`storyboard.json` is the single contract; each stage reads it and writes to `outputs/`.

## Run it (from a clean clone)
```bash
git clone <this repo> && cd heritage-short
cp .env.example .env        # fill in GEMINI_API_KEY, CF_ACCOUNT_ID, CF_API_TOKEN
make setup                  # pip install requests jsonschema   (FFmpeg must be installed)
make film                   # validate -> narration -> keyframes -> music -> assemble
```
Result: `outputs/final_vertical.mp4` (9:16) and `outputs/final_horizontal.mp4` (16:9).
Other commands: `make smoke` (test each API), `make radio` (voice-only cut for user test 1), `make draft` (half-resolution render).

## Change one shot and regenerate only it
Edit that shot's `image_prompt` or `narration` in `storyboard.json`, then `make film`. Stages hash their inputs
(see `outputs/.cache.json`), so only the changed shot calls a model; `runs.jsonl` shows `"cached": true` for the rest.

## Stages
| Stage | Script | Model | Cost |
|---|---|---|---|
| narration | pipeline/narration.py | Gemini TTS (free tier) | $0 |
| keyframes | pipeline/keyframes.py | FLUX.1 schnell on Cloudflare Workers AI (free allowance) | $0 |
| music | pipeline/music.py + kaggle/ACESTEP_STEPS.md | ACE-Step 1.5 on Kaggle (free GPU) | $0 |
| assemble | pipeline/assemble.py | FFmpeg (Ken Burns, ducking, loudnorm, subtitles, end card) | $0 |
Moving shots: this version animates keyframes with a Ken Burns pan/zoom. If a Wan 2.2 clip exists at `outputs/clips/<shot>.mp4`, assembly uses it automatically.
See ARCHITECTURE.md, DESIGN.md, EXPERIMENTS.md, FAILURES.md, COSTS.md, ETHICS.md.
