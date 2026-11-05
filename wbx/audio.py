"""Audio: decode, transcribe (word timings), re-pace, and final mix."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

SR = 48000


def decode(src: Path, sr: int = SR) -> np.ndarray:
    """Mono float32 PCM via ffmpeg (avoids PyAV quirks with some mp3 metadata)."""
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32).copy()


def duration(src: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def to_wav(src: Path, out: Path, tempo: float = 1.0):
    """Convert any input to the working wav, optionally changing speed (atempo)."""
    af = ["-af", f"atempo={tempo}"] if tempo != 1.0 else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *af, "-ar", str(SR), "-ac", "1",
                    "-c:a", "pcm_s16le", str(out)], check=True)


def transcribe(src: Path, out_prefix: Path, model: str = "small.en") -> list:
    """Whisper transcript with word timings -> <prefix>.json and <prefix>.txt."""
    from faster_whisper import WhisperModel

    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(decode(src, 16000), word_timestamps=True, vad_filter=True)
    out = []
    with open(f"{out_prefix}.txt", "w") as t:
        for s in segs:
            out.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                        "words": [{"s": w.start, "e": w.end, "w": w.word} for w in s.words]})
            t.write(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}\n")
    Path(f"{out_prefix}.json").write_text(json.dumps(out))
    return out


def words(transcript: list) -> list:
    return [w for s in transcript for w in s["words"]]


def wpm(transcript: list) -> float:
    ws = words(transcript)
    span = ws[-1]["e"] - ws[0]["s"]
    return len(ws) / span * 60 if span > 0 else 0.0


def pace(src: Path, transcript: list, out: Path, pause: float = 0.25, tempo: float = 1.0,
         fade: float = 0.025, loudness: float = -14, true_peak: float = -1.5) -> int:
    """Add breathing room after each sentence, then change speed.

    Each pause is spliced at the quietest 20 ms of the natural gap after a
    sentence, with short fades either side, and filled with room tone matched to
    the recording's own noise floor, so it sounds like a breath, not a dropout.
    Returns the number of pauses added.
    """
    x = decode(src)
    ws = words(transcript)
    win = int(0.02 * SR)

    def quietest(lo, hi):
        i0, i1 = int(lo * SR), int(hi * SR)
        if i1 - i0 <= win:
            return (i0 + i1) // 2, None
        e = np.convolve(x[i0:i1] ** 2, np.ones(win) / win, mode="valid")
        k = int(np.argmin(e))
        return i0 + k + win // 2, float(np.sqrt(e[k]))

    cuts, floors = [], []
    for w, nxt in zip(ws, ws[1:]):
        if w["w"].strip()[-1:] in ".?!":
            i, rms = quietest(w["e"], nxt["s"])
            cuts.append(i)
            if rms is not None:
                floors.append(rms)
    floor = float(np.median(floors)) if floors else 0.0

    rng = np.random.default_rng(0)
    nf = int(fade * SR)
    ramp = np.linspace(0, 1, nf, dtype=np.float32)

    def room(n):
        r = (rng.standard_normal(n) * floor).astype(np.float32)
        r[:nf] *= ramp
        r[-nf:] *= ramp[::-1]
        return r

    parts, prev = [], 0
    for i in cuts:
        seg = x[prev:i].copy()
        if prev:
            seg[:nf] *= ramp
        seg[-nf:] *= ramp[::-1]
        parts += [seg, room(int(pause * SR))]
        prev = i
    tail = x[prev:].copy()
    tail[:nf] *= ramp
    parts.append(tail)
    y = np.concatenate(parts)

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", f"atempo={tempo},loudnorm=I={loudness}:TP={true_peak}:LRA=11",
                    "-ar", str(SR), "-c:a", "pcm_s16le", str(out)], input=y.tobytes(), check=True)
    return len(cuts)


def final_mix(src: Path, out: Path, end_pad: float):
    """Voice + trailing silence for the end card."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", f"apad=pad_dur={end_pad}",
                    "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(out)], check=True)
