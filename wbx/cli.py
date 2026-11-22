"""wbx: hand-drawn whiteboard explainer videos, timed to a voiceover.

Typical episode:
    wbx init my-series --name "Backend Concepts"     # once per series
    wbx new caching                                 # inside the series folder
    (write script.md, record the voice, drop the audio file in the episode folder)
    wbx transcribe 06-caching                       # word timings + wpm, scaffolds epNN.html
    (choreograph the scenes in epNN.html)
    wbx stills 06-caching 2 8 15 30                 # layout check
    wbx render 06-caching                           # final mp4
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from . import __version__, audio, config

TEMPLATES = Path(__file__).parent / "templates"
DERIVED = {"voice.wav", "voice_raw.wav", "voice_final.wav"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


# ---------- episode helpers ----------

class Episode:
    def __init__(self, path: str | Path):
        self.dir = Path(path).resolve()
        if not self.dir.is_dir():
            raise SystemExit(f"not a folder: {self.dir}")
        self.cfg, self.root = config.load(self.dir)
        if (self.dir / "episode.yaml").exists():   # per-episode overrides, e.g. `style: chalk`
            import yaml
            self.cfg = config._merge(self.cfg, yaml.safe_load((self.dir / "episode.yaml").read_text()) or {})
        m = re.match(r"(\d+)-(.+)", self.dir.name)
        self.num, self.slug = (int(m[1]), m[2]) if m else (0, self.dir.name)

    @property
    def html(self) -> Path:
        pages = sorted(self.dir.glob("ep*.html")) or sorted(self.dir.glob("*.html"))
        if not pages:
            raise SystemExit(f"no episode page in {self.dir} (run `wbx transcribe` to scaffold one)")
        return pages[0]

    voice = property(lambda s: s.dir / "voice.wav")
    final = property(lambda s: s.dir / "voice_final.wav")
    transcript_path = property(lambda s: s.dir / "transcript.json")

    def transcript(self) -> list:
        if not self.transcript_path.exists():
            raise SystemExit(f"no transcript in {self.dir} (run `wbx transcribe` first)")
        return json.loads(self.transcript_path.read_text())

    def source_audio(self) -> Path:
        cands = [p for p in self.dir.iterdir()
                 if p.suffix.lower() in AUDIO_EXT and p.name not in DERIVED and not p.name.startswith("voice_")]
        if not cands:
            raise SystemExit(f"no audio file in {self.dir}")
        return max(cands, key=lambda p: p.stat().st_mtime)

    def title(self) -> str:
        """Title from the script.md heading ("# Series #NN — Title"), else from the folder name."""
        sm = self.dir / "script.md"
        if sm.exists():
            first = sm.read_text().splitlines()[0] if sm.read_text() else ""
            if "—" in first:
                return first.split("—", 1)[1].strip()
        return title_of(self.slug)

    def output(self) -> Path:
        name = self.cfg["episode"]["output"].format(
            series_slug=self.cfg["series_slug"], num=self.num, slug=self.slug)
        return self.dir / name


def fill(text: str, values: dict) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(values.get(m[1], m[0])), text)


def title_of(slug: str) -> str:
    return slug.replace("-", " ").title()


def report(tr: list, label: str = ""):
    ws = audio.words(tr)
    print(f"{label}{len(ws)} words, {ws[-1]['e']:.1f}s, {audio.wpm(tr):.0f} wpm")


# ---------- commands ----------

def cmd_init(a):
    d = Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    f = d / "series.yaml"
    if f.exists() and not a.force:
        raise SystemExit(f"{f} already exists (use --force to overwrite)")
    text = (TEMPLATES / "series.yaml").read_text()
    f.write_text(fill(text, {"NAME": a.name, "HEADER": a.name.upper()}))
    print(f"wrote {f}")


def cmd_new(a):
    cfg, root = config.load(Path(a.series))
    nums = [int(m[1]) for p in root.iterdir() if p.is_dir() and (m := re.match(r"(\d+)-", p.name))]
    num = a.num or (max(nums, default=0) + 1)
    slug = config.slugify(a.slug)
    d = root / f"{num:02d}-{slug}"
    if d.exists():
        raise SystemExit(f"{d} already exists")
    d.mkdir()
    sc = cfg["script"]
    (d / "script.md").write_text(fill((TEMPLATES / "script.md").read_text(), {
        "SERIES": cfg["name"], "NUM": f"{num:02d}", "TITLE": a.title or title_of(slug),
        "TARGET_WORDS": sc["target_words"], "TARGET_WPM": cfg["voice"]["target_wpm"],
        "TARGET_SECONDS": round(sc["target_words"] / cfg["voice"]["target_wpm"] * 60),
        "VOICE_NOTES": cfg["voice"].get("notes") or "-",
        "RULES": ("Rules:\n" + "\n".join(f"- {r}" for r in sc.get("rules") or [])) if sc.get("rules") else "", "CLOSING_LINE": sc.get("closing_line") or "",
    }))
    print(f"created {d}\n  next: write {d / 'script.md'}, record the voice, drop the audio file in the folder, "
          f"then `wbx transcribe {d.name}`")


def scaffold_html(ep: Episode, tr: list) -> Path:
    ws = audio.words(tr)
    cfg, cv, ec = ep.cfg, ep.cfg["canvas"], ep.cfg["end_card"]
    first = ec["line1"].split()[0].lower() if ec["line1"] else ""
    hits = [w for w in ws if first and w["w"].strip().lower().startswith(first)]
    T = round(hits[-1]["s"] - 0.05, 2) if hits else round(ws[-1]["e"], 2)
    hook = next((round(w["e"] + 0.3, 1) for w in ws if w["w"].strip()[-1:] in ".?!"), 5.0)
    js = lambda v: str(v).replace("\\", "\\\\").replace("'", "\\'")
    kit = config.style_theme(cfg) is not None
    collage = cfg["style"] == "collage"
    cap_top = cfg.get("caption_top", 1470)
    html = fill((TEMPLATES / ("episode-kit.html" if kit else "episode.html")).read_text(), {
        "TITLE_JS": js(ep.title()), "END_LINE1_JS": js(ec["line1"]), "END_LINE2_JS": js(ec["line2"]),
        "END_LINE3_JS": js(ec["line3"]),
        "TITLE": ep.title(), "HEADER": cfg["header"], "W": cv["width"], "H": cv["height"],
        "HOOK_OUT": hook, "END": T, "END_A": round(T + 0.05, 2), "END_B": round(T + 0.1, 2),
        "END_C": round(T + 0.65, 2), "END_D": round(T + 0.7, 2), "END_E": round(T + 1.1, 2),
        "COLLAGE_SCRIPT": '<script src="/_wbx/collage.js"></script>' if collage else "",
        "COLLAGE_INIT": "\nconst C = wbx.collage(K);" if collage else "",
        "COLLAGE_HELP": ("\n  Collage (C = wbx.collage(K)): C.paper, C.text, C.highlight, C.stamp, C.string, C.loop, C.mover,"
                         "\n    C.camera([[t, cx, cy, zoom], ...], {until: endCardTime}) pans/zooms over a board bigger than the screen."
                         if collage else ""),
        "CAMERA_HINT": (f"\nC.camera([[0, 540, 960, 1], [{T}, 540, 960, 1]], {{until: {T}}});   // pan/zoom keyframes"
                        if collage else ""),
        "HEADER_LINE": f"K.header('{js(cfg['header'])}', {hook});\n" if cfg["header"] else "",
        "CONTENT_BOTTOM": cap_top - 30 if cfg["captions"] else cv["height"] - 420,
        "CONTENT_NOTE": f"captions start at y={cap_top}" if cfg["captions"]
                        else "platform UI covers roughly the bottom 400 px",
        "END_LINE1": ec["line1"], "END_LINE2": ec["line2"].replace("&", "&amp;"), "END_LINE3": ec["line3"],
    })
    p = ep.dir / f"ep{ep.num:02d}.html"
    p.write_text(html)
    return p


def cmd_transcribe(a):
    ep = Episode(a.episode)
    src = Path(a.input).resolve() if a.input else ep.source_audio()
    print(f"source: {src.name}" + (f"  (tempo {a.tempo})" if a.tempo != 1.0 else ""))
    audio.to_wav(src, ep.voice, a.tempo)
    tr = audio.transcribe(ep.voice, ep.dir / "transcript", a.model)
    report(tr)
    target = ep.cfg["voice"]["target_wpm"]
    if target and abs(audio.wpm(tr) - target) / target > 0.1:
        print(f"  note: series target is ~{target} wpm; see `wbx pace --help` or re-record with a speed setting")
    if not list(ep.dir.glob("*.html")):
        print(f"scaffolded {scaffold_html(ep, tr).name}")
    print(f"word timings: {ep.dir / 'transcript.txt'}")


def cmd_pace(a):
    ep = Episode(a.episode)
    raw = ep.dir / "voice_raw.wav"
    if not raw.exists():
        shutil.copy(ep.voice, raw)
    raw_tr = ep.dir / "transcript_raw.json"
    if not raw_tr.exists():
        shutil.copy(ep.transcript_path, raw_tr)
    au = ep.cfg["audio"]
    n = audio.pace(raw, json.loads(raw_tr.read_text()), ep.voice, a.pause, a.tempo, a.fade,
                   au["loudness"], au["true_peak"])
    print(f"{n} pauses of {a.pause}s, tempo {a.tempo}; re-transcribing…")
    tr = audio.transcribe(ep.voice, ep.dir / "transcript", a.model)
    report(tr)
    print("listen to voice.wav before timing any animation: splices can sound off")


def cmd_info(a):
    ep = Episode(a.episode)
    print(f"{ep.cfg['name']} #{ep.num:02d} {ep.slug}")
    if ep.transcript_path.exists():
        report(ep.transcript(), "  voice: ")
    for p in (ep.voice, ep.final, ep.output()):
        print(f"  {p.name}: {'yes' if p.exists() else 'no'}")


def cmd_stills(a):
    from .render import stills
    ep = Episode(a.episode)
    times = a.times
    if not times:
        end = audio.duration(ep.voice) if ep.voice.exists() else 40
        times = [round(t * a.every, 1) for t in range(int(end / a.every) + 1)]
    out = Path(a.out) if a.out else ep.dir / "stills"
    for p in stills(ep.html, ep.root, ep.cfg, times, out):
        print(p)


def cmd_render(a):
    from .render import video
    ep = Episode(a.episode)
    tr = ep.transcript() if ep.transcript_path.exists() else []
    if a.silent:
        src, end = None, a.end
        if end is None:
            raise SystemExit("--silent needs --end")
    else:
        if not ep.final.exists() or ep.final.stat().st_mtime < ep.voice.stat().st_mtime:
            audio.final_mix(ep.voice, ep.final, ep.cfg["audio"]["end_pad"])
        src = ep.final
        end = a.end if a.end is not None else audio.duration(src)
    start = a.start or 0.0
    out = Path(a.out) if a.out else (ep.output() if a.start is None and a.end is None
                                     else ep.dir / f"preview_{start:g}-{end:g}.mp4")
    print(f"rendering {ep.html.name} {start:.1f}s–{end:.1f}s")
    video(ep.html, ep.root, ep.cfg, src, start, end, out, tr, crf=a.crf)
    print(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wbx", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"wbx {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create series.yaml in a folder")
    p.add_argument("dir", nargs="?", default=".")
    p.add_argument("--name", default="My Series")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("new", help="create the next episode folder with a script template")
    p.add_argument("slug")
    p.add_argument("--title")
    p.add_argument("--num", type=int)
    p.add_argument("--series", default=".", help="series folder (default: current)")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("transcribe", help="audio -> voice.wav + word-timed transcript (+ page scaffold)")
    p.add_argument("episode")
    p.add_argument("--input", help="audio file (default: newest audio in the folder)")
    p.add_argument("--tempo", type=float, default=1.0, help="speed change before transcribing, e.g. 1.15")
    p.add_argument("--model", default="small.en")
    p.set_defaults(fn=cmd_transcribe)

    p = sub.add_parser("pace", help="add pauses after sentences and/or change speed, then re-transcribe")
    p.add_argument("episode")
    p.add_argument("--pause", type=float, default=0.25)
    p.add_argument("--tempo", type=float, default=1.0)
    p.add_argument("--fade", type=float, default=0.025)
    p.add_argument("--model", default="small.en")
    p.set_defaults(fn=cmd_pace)

    p = sub.add_parser("info", help="word count, length and pace of an episode")
    p.add_argument("episode")
    p.set_defaults(fn=cmd_info)

    p = sub.add_parser("stills", help="screenshot the page at given times (layout check)")
    p.add_argument("episode")
    p.add_argument("times", nargs="*", type=float)
    p.add_argument("--every", type=float, default=4.0, help="interval when no times are given")
    p.add_argument("--out", help="output folder (default: <episode>/stills)")
    p.set_defaults(fn=cmd_stills)

    p = sub.add_parser("render", help="render the mp4")
    p.add_argument("episode")
    p.add_argument("--start", type=float)
    p.add_argument("--end", type=float)
    p.add_argument("--silent", action="store_true", help="no audio track (needs --end)")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_render)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main(sys.argv[1:])
