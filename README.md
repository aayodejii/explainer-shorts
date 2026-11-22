# explainer-shorts (`wbx`)

`wbx` makes animated explainer shorts, timed word by word to a voiceover, in themeable styles: clean, collage, sketch, chalk, or the original hand-drawn whiteboard.
You write the script, record the voiceover (your own voice or a generated one), and lay out SVG scenes on a timeline.
`wbx` does the rest: transcription, pacing, layout previews and the final render to a vertical MP4.

I built it for the _Backend Concepts_ short-video series, but you can configure it for any series.

## How it works

- An episode is a single HTML page with an SVG canvas inside. Every element is a pure function of time `t`.
  You control it with data attributes (`data-draw`, `data-write`, `data-fade`, `data-wipe`, `data-pop`, `data-out`),
  and you can add a `window.extra(t)` if you need custom motion. That's for the whiteboard style. The kit styles use `K.onFrame` instead.
  The runtime (`wbx/runtime/wb.js`) applies all of it.
- The hand-drawn wobble comes from a "boiling" turbulence filter. The fonts are Caveat and Patrick Hand (Google Fonts, OFL).
- `faster-whisper` provides the word timings, so a scene lands on the exact word you say.
- Playwright drives headless Chrome to screenshot every frame. Then ffmpeg encodes H.264 + AAC and normalises loudness.

## Styles

Pick a style with `style:` in `series.yaml`. To change it for one episode only, put `style:` in that episode's `episode.yaml`:

| style                  | look                                                                                                                                    | how things enter                                                               |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `whiteboard` (default) | the original: Caveat + Patrick Hand, dotted paper, wobble                                                                               | the episode draws its own SVG                                                  |
| `clean`                | Nunito + JetBrains Mono, rounded cards, soft shadows, grid paper                                                                        | cards pop, rows slide, text fades up                                           |
| `sketch`               | rough.js strokes, hatch fills, Kalam + Gochi Hand, paper grain                                                                          | outlines draw on, fills get scribbled in, text writes itself                   |
| `chalk`                | dark board, chalk texture, Gaegu + Cabin Sketch                                                                                         | same as `sketch`                                                               |
| `collage`              | documentary-style paper collage with torn cut-outs, tape, stamps, red string, highlighter, handwritten notes, grain and a moving camera | cards pop, papers slap or slide in, stamps slam down, string runs through pins |

The last four use the kit (`wbx/runtime/kit.js`). An episode only describes what appears and when
(`K.card(...)`, `K.text(...)`, `K.arrow(...)`). The theme picks the look and the entrance, which means the same
episode code renders in any of the four. Use `style_options:` to override a theme's colours or stroke settings.
If you want motion past the entrance, `K.fly(from, to, t0, t1)` sends a dot across, `K.mover(keys, show, build)` moves any
group along keyframes, and `K.onFrame(fn)` runs your code on every frame. The kit owns `window.extra`, so use `K.onFrame` instead.
The themes are in `wbx/themes.py`. rough.js (MIT) is vendored in `wbx/runtime/vendor/`.

`collage` has extra building blocks on top of the kit. Load `/_wbx/collage.js` after `kit.js`, then call
`const C = wbx.collage(K)` to get `C.paper`, `C.stamp`, `C.string`, `C.highlight`, `C.loop`, `C.mover` and
`C.camera`. That last one does keyframed pan and zoom over a board larger than the screen. The comment at the top of the file explains how.

## Install

You need Python 3.10+, ffmpeg, and Chrome or Chromium.

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

`series.yaml` controls the header, palette, fonts, canvas size, whether captions are on, loudness, end-card padding,
target pace, script rules and the output file name. These are the ones you'll most likely touch:

- `captions: true` burns word-by-word captions into the video. `caption_top: 1230` pushes them higher, which matters because TikTok and
  Shorts cover roughly the bottom 400 px and the right edge.
- `fonts: {title: League Spartan, body: Poppins}` replaces a kit style's fonts with any Google Fonts.
  Titles, labels and captions use `title`. Everything else uses `body`, or `data` if you set it.
- `style_options: {round: 0}` makes corners and line ends square. `1` brings back the style's own rounding.
  For rect corners you draw yourself in episode code, use `K.rx(n)` so they respect this setting too.

You can set any of these per episode in `episode.yaml`. That's how a series changes its look without
older episodes coming out different on a re-render: pin the old value in their `episode.yaml`. Every key is listed in `wbx/templates/series.yaml`,
and `examples/backend-concepts/series.yaml` is a real series you can copy from. Set `WBX_CHROME` to point at a different browser.

## Fonts

`wbx` downloads Google Fonts once and caches them in `~/.cache/wbx/fonts`. Set `WBX_FONT_CACHE` to move that folder. Because of the cache, renders
are repeatable and work offline after the first run. If a font fails to load, you get a warning.

## Tests

```sh
.venv/bin/python -m pytest -q                                       # fast unit tests
.venv/bin/python tests/regress.py <series> --baseline <dir> [--update]   # pixel regression over real episodes
```

## Keep content out of this repo

Put audio, video and episode folders in your own content folder. `.gitignore` blocks media here anyway.
