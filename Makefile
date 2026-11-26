PY=python3
.PHONY: film setup smoke validate narration radio keyframes music draft clean
film: validate narration keyframes music   ## whole pipeline, one command
	$(PY) pipeline/assemble.py
setup:
	pip install -r requirements.txt
smoke:
	$(PY) pipeline/smoke_test.py
validate:
	$(PY) -c "import sys; sys.path.insert(0,'pipeline'); from common import load_storyboard; load_storyboard(); print('storyboard OK')"
narration: validate
	$(PY) pipeline/narration.py
radio: narration music
	$(PY) pipeline/assemble.py --radio
keyframes: validate
	$(PY) pipeline/keyframes.py
music:
	$(PY) pipeline/music.py
draft: validate narration keyframes music
	$(PY) pipeline/assemble.py --draft
clean:
	rm -rf outputs/segments outputs/audio outputs/final_*.mp4 outputs/radio_cut.mp4
