"""Visual regression: render stills of every episode in a series and compare them
with a saved baseline, byte for byte (rendering is deterministic for a given t).

  python tests/regress.py <series-folder> --baseline <dir> --update   # save baseline
  python tests/regress.py <series-folder> --baseline <dir>            # compare after a change

The baseline lives outside this repo, next to your content, since it shows your episodes.
"""
import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

from wbx import cli
from wbx.render import stills

TIMES = [1, 8, 16, 24, 32, 41.5]

ap = argparse.ArgumentParser()
ap.add_argument("series")
ap.add_argument("--baseline", required=True)
ap.add_argument("--update", action="store_true")
a = ap.parse_args()

base = Path(a.baseline)
eps = sorted(p for p in Path(a.series).iterdir() if p.is_dir() and p.name[:2].isdigit())
failed = 0
with tempfile.TemporaryDirectory() as tmp:
    for d in eps:
        ep = cli.Episode(d)
        out = base / d.name if a.update else Path(tmp) / d.name
        for p in stills(ep.html, ep.root, ep.cfg, TIMES, out):
            if a.update:
                continue
            ref = base / d.name / p.name
            same = ref.exists() and hashlib.sha1(ref.read_bytes()).digest() == hashlib.sha1(p.read_bytes()).digest()
            if not same:
                failed += 1
                keep = Path(a.baseline + "_diff") / d.name
                keep.mkdir(parents=True, exist_ok=True)
                (keep / p.name).write_bytes(p.read_bytes())
            print(f"{'ok  ' if same else 'DIFF'} {d.name} t={p.stem}")
print("baseline saved" if a.update else f"{failed} differing frame(s)")
sys.exit(1 if failed else 0)
