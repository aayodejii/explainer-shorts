"""Frame capture: render(t) for every frame, piped into ffmpeg."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .browser import open_page, warm_up


def caption_words(transcript: list, a: float, b: float) -> list:
    ws = []
    for s in transcript:
        for w in s["words"]:
            if a <= w["s"] < b:
                t = w["w"].strip()
                if t == "%" and ws:
                    ws[-1]["w"] += "%"
                    continue
                ws.append({"w": t, "s": round(w["s"], 3)})  # page timeline is absolute
    return ws


def video(html: Path, root: Path, cfg: dict, audio: Path | None, a: float, b: float, out: Path,
          transcript: list | None = None, quality: int = 92, crf: int = 18):
    fps, dur = cfg["canvas"]["fps"], b - a
    au = cfg["audio"]
    if audio is None:
        audio_in = ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anullsrc=r=48000:cl=stereo"]
        audio_fx = "anull"
    else:
        audio_in = ["-ss", str(a), "-t", f"{dur:.2f}", "-i", str(audio)]
        audio_fx = (f"afade=t=in:d=0.08,afade=t=out:st={dur - 0.15:.2f}:d=0.15,"
                    f"loudnorm=I={au['loudness']}:TP={au['true_peak']}:LRA=11,aresample=48000")
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
         *audio_in, "-af", audio_fx,
         "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    n = int(dur * fps)
    with open_page(html, root, cfg, caption_words(transcript or [], a, b)) as pg:
        warm_up(pg, dur)
        for i in range(n):
            if i % 90 == 0:
                print(f"\r  frame {i}/{n}", end="", file=sys.stderr, flush=True)
            pg.evaluate(f"render({a + i / fps})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=quality))
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed")
    print(f"\r  {n} frames -> {out}", file=sys.stderr)


def stills(html: Path, root: Path, cfg: dict, times: list[float], outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    with open_page(html, root, cfg) as pg:
        for t in times:
            pg.evaluate(f"render({t})")
            pg.wait_for_timeout(50)
            p = outdir / f"{t:05.1f}.png"
            pg.screenshot(path=str(p))
            paths.append(p)
    return paths
