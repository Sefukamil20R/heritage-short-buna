# Making the score with ACE-Step 1.5 on Kaggle (do this once, ~20 min)
1. kaggle.com -> New Notebook -> Settings: Accelerator = GPU T4, Internet = On (needs phone verification).
2. In a cell: `!git clone https://github.com/ACE-Step/ACE-Step-1.5 && cd ACE-Step-1.5 && pip install -e .`
3. Follow that repo's README for its current generate command (the interface changes between versions; I did not hard-code it).
4. Inputs, taken from storyboard.json -> "music":
   - caption: (copy `music.caption`)
   - instrumental / no lyrics
   - bpm 72, key A minor, duration 75 s (tempo + key go in the metadata fields, NOT the caption)
5. Generate 3 candidates (different seeds). Download them.
6. Listen to each quietly UNDER your narration. Pick one and write why in EXPERIMENTS.md (E7).
7. Save the winner as `outputs/music/score.wav` (or .mp3) in the repo, commit it, then run `make film`.
Log the GPU minutes used (Kaggle shows session time) in COSTS.md.
