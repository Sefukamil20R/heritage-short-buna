# FAILURES

## F1: Cloudflare Workers AI signup failed
- **Problem:** could not create or authenticate a Cloudflare account ("failed to authenticate"), so FLUX.1 schnell keyframes could not run.
- **Tried:** incognito window, a different sign-in method, retrying.
- **Resolution:** generated 8 keyframes in Gemini from the same storyboard prompts, converted WebP to JPG, kept the pipeline unchanged.
- **Cost:** about 45  minutes lost. The image stage is manual.

## F2: Amharic words read with the wrong meaning
- **Problem:** Gemini TTS sometimes pronounced words differently from the intended reading (e.g. "silala": lightly vs hardly), which changed the meaning.
- **Evidence:** all 3 family listeners noticed.
- **Resolution:** refined the wording of the affected lines. Better, not fully solved. A native speaker recording would fix it.

## F3: Voice sounds like AI
- **Problem:** all 3 listeners said the voice sounded 100% AI.
- **Resolution:** not solved. A limit of the model. Next step: a real voice recording with consent.

## F4: Windows setup errors
- **Problems:** `make` not installed, `charmap` encoding error on UTF-8 Amharic text, missing Python packages, assemble.py expecting .jpg files.
- **Resolution:** ran the scripts directly, set UTF-8 encoding, installed packages with pip, converted images to JPG.

## F5: Wrong end card credits
- **Problem:** the end card named FLUX.1 and ACE-Step, which I did not use, and the credit line was cut off.
- **Resolution:** edited the end card text to the tools actually used.