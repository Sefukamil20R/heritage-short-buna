# EXPERIMENTS

## E1: Does caching avoid regenerating narration?
- **Hypothesis:** a second run of narration.py with no storyboard change makes no new TTS calls.
- **Change:** ran `python pipeline/narration.py` twice.
- **Result:** run 1 printed "generated" for s01 to s08. Run 2 printed "cached" for all 8. Confirmed.

## E2: Can the image stage be swapped without changing other stages?
- **Hypothesis:** because storyboard.json is the contract, replacing the image source should not break narration, music or assembly.
- **Change:** the hosted image API (Cloudflare) failed at account signup. I generated 8 keyframes in Gemini from the same storyboard prompts and converted them from WebP to JPG.
- **Result:** assemble.py ran with no code changes once the files were s01.jpg to s08.jpg. Confirmed. Cost: the image stage is now manual.

## E3: How well does Gemini TTS handle Amharic?
- **Hypothesis:** a TTS model supporting 130+ languages will read my Amharic correctly.
- **Change:** generated narration for all 8 shots and played it to 3 Amharic-speaking family members.
- **Result:** mostly good, but words whose meaning depends on pronunciation that the script does not show (e.g. "silala") were read in ways that changed the meaning. The voice was judged to sound fully AI. Partly confirmed.

## E4: Does refining the wording fix the meaning problems?
- **Hypothesis:** rewording the affected lines will make the TTS output carry the intended meaning.
- **Change:** refined the Amharic text of the affected lines and regenerated only those shots.
- **Result:** family said the new version was better. Not fully solved, the voice is still obviously AI. Partly confirmed.

## E5: Is the end card truthful?
- **Hypothesis:** the default end card credits match the tools I actually used.
- **Change:** inspected the rendered end card.
- **Result:** it credited FLUX.1 schnell and ACE-Step, which I did not use, and the text was cut off at the edges. I changed the text in storyboard.json to the real tools. Fixed.