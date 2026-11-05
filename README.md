# whiteboard-explainer (`wbx`)

Hand-drawn whiteboard explainer videos, timed word by word to a voiceover.
You write a script, record the voice, and choreograph SVG scenes on a timeline.
`wbx` handles transcription, pacing, layout previews and rendering to a vertical MP4.

Built for the *Backend Concepts* short-video series; configurable for any series.

## How it works

- Each episode is one HTML page holding an SVG canvas. Every element is a pure function of time `t`,
  set with data attributes (`data-draw`, `data-write`, `data-fade`, `data-wipe`, `data-pop`, `data-out`)
  plus an optional `window.extra(t)` for custom motion. The runtime (`wbx/runtime/wb.js`) applies them.
- A "boiling" turbulence filter gives the hand-drawn wobble; fonts are Caveat and Patrick Hand (Google Fonts, OFL).
- `faster-whisper` gives word timings, so scenes land on the exact spoken word.
- Headless Chrome (Playwright) screenshots every frame; ffmpeg encodes H.264 + AAC, loudness-normalised.

## Install

Needs Python 3.10+, ffmpeg, and Chrome or Chromium.

```sh
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/playwright install chromium   # only if you have no system Chrome
```

## Workflow

```sh
wbx init my-series --name "Backend Concepts"   # writes series.yaml (see examples/)
cd my-series
wbx new caching                                # 01-caching/ with a script.md template
# write the script, record it, drop the audio file into 01-caching/
wbx transcribe 01-caching                      # voice.wav, transcript.json/.txt, wpm; scaffolds ep01.html
wbx pace 01-caching --pause 0.3 --tempo 0.9    # optional: breathing room / speed (decide before timing scenes)
# choreograph scenes in ep01.html using the timings in transcript.txt
wbx stills 01-caching 2 8 15 30                # layout check -> 01-caching/stills/
wbx render 01-caching                          # final mp4 (voice + end-card padding)
wbx render 01-caching --start 10 --end 20      # quick partial preview
wbx info 01-caching                            # words, length, pace
```

## Configuration

`series.yaml` sets the header, palette, fonts, canvas size, captions on/off, loudness, end-card padding,
target pace, script rules and the output file name. See `wbx/templates/series.yaml` for every key and
`examples/backend-concepts/series.yaml` for a real series. `WBX_CHROME` overrides the browser path.

## Tests

```sh
.venv/bin/python -m pytest -q                                       # fast unit tests
.venv/bin/python tests/regress.py <series> --baseline <dir> [--update]   # pixel regression over real episodes
```

## Content stays out

Audio, video and episode folders belong in your own content folder, not this repo (`.gitignore` blocks media).
