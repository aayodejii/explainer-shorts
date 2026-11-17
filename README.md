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

## Styles

Set `style:` in `series.yaml` (or in an episode's own `episode.yaml` to override one episode):

| style | look | how things enter |
|---|---|---|
| `whiteboard` (default) | original: Caveat + Patrick Hand, dotted paper, wobble | episode draws its own SVG |
| `clean` | Nunito + JetBrains Mono, rounded cards, soft shadows, grid paper | cards pop, rows slide, text fades up |
| `sketch` | rough.js strokes, hatch fills, Kalam + Gochi Hand, paper grain | outlines draw on, fills scribble in, text writes on |
| `chalk` | dark board, chalk texture, Gaegu + Cabin Sketch | same as sketch |
| `collage` | documentary paper collage: torn cut-outs, tape, stamps, red string, highlighter, handwritten notes, grain, moving camera | cards pop, papers slap or slide in, stamps slam, string draws through pins |

The last three use the **kit** (`wbx/runtime/kit.js`): an episode says *what* appears and *when*
(`K.card(...)`, `K.text(...)`, `K.arrow(...)`), and the theme decides the look and the entrance, so the same
episode code renders in any of them. `style_options:` overrides a theme's colours or stroke settings.
Themes live in `wbx/themes.py`. rough.js (MIT) is vendored in `wbx/runtime/vendor/`.

`collage` adds its own blocks on top of the kit: load `/_wbx/collage.js` after `kit.js`, then
`const C = wbx.collage(K)` gives `C.paper`, `C.stamp`, `C.string`, `C.highlight`, `C.loop`, `C.mover` and
`C.camera` (keyframed pan and zoom over a board bigger than the screen; see the comment at the top of the file).

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
target pace, script rules and the output file name. A few keys worth knowing:

- `captions: true` burns in word-by-word captions; `caption_top: 1230` moves them up (TikTok and
  Shorts cover roughly the bottom 400 px and the right edge).
- `fonts: {title: League Spartan, body: Poppins}` swaps a kit style's fonts for any Google Fonts
  (titles, labels and captions use `title`; everything else uses `body`, or `data` if given).
- `style_options: {round: 0}` gives square corners and square line ends (`1` = the style's own rounding).
  In episode code, use `K.rx(n)` for your own rect corners so they follow this setting.

Any of these can be set per episode in `episode.yaml`, which is how a series changes its look without
re-rendering older episodes differently (pin the old value in their `episode.yaml`). See `wbx/templates/series.yaml` for every key and
`examples/backend-concepts/series.yaml` for a real series. `WBX_CHROME` overrides the browser path.

## Tests

```sh
.venv/bin/python -m pytest -q                                       # fast unit tests
.venv/bin/python tests/regress.py <series> --baseline <dir> [--update]   # pixel regression over real episodes
```

## Content stays out

Audio, video and episode folders belong in your own content folder, not this repo (`.gitignore` blocks media).
