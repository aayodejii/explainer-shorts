"""Series configuration.

A series is a folder containing `series.yaml`; each episode is a sub-folder
(`NN-slug/`). Anything left out of series.yaml falls back to DEFAULTS.
"""
from __future__ import annotations

import copy
from pathlib import Path
from urllib.parse import quote_plus

import yaml

DEFAULTS: dict = {
    "name": "My Series",
    "header": "",                       # small title shown on the hook scene only; "" = none
    "canvas": {"width": 1080, "height": 1920, "fps": 30},
    "theme": {
        "paper": "#FBFAF5", "ink": "#1F2430", "muted": "#6B7080", "dots": "#E6E3DA",
        "blue": "#2563EB", "red": "#E0412F", "green": "#16A34A", "orange": "#E8890C",
        "grey": "#9AA0AE", "highlight": "#FFE066",
        "font_display": "Caveat", "font_display_weights": "600;700",
        "font_body": "Patrick Hand",
    },
    "style": "whiteboard",              # whiteboard (original) | clean | sketch | chalk
    "style_options": {},                # overrides for the style's kit values (colours, stroke...)
    "captions": False,                  # burned-in word captions
    "caption_top": 1470,
    "fonts": None,                      # kit styles only: {title: "League Spartan", body: "Poppins", data: ...} overrides the style's fonts                # y of the caption block (TikTok covers roughly the bottom 400 px)
    "audio": {"loudness": -14, "true_peak": -1.5, "end_pad": 1.5},
    "voice": {"target_wpm": 228, "notes": ""},
    "script": {
        "target_words": 150,
        "closing_line": "",
        "rules": [],
    },
    "end_card": {"line1": "Save this", "line2": "& share it", "line3": ""},
    "episode": {"output": "{series_slug}-{num:02d}-{slug}.mp4"},
    "chrome": None,                     # path to a Chrome binary; None = auto-detect
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def find_series_root(start: Path) -> Path:
    """Walk up from `start` to the folder holding series.yaml."""
    p = start.resolve()
    if p.is_file():
        p = p.parent
    for d in [p, *p.parents]:
        if (d / "series.yaml").exists():
            return d
    raise SystemExit(f"no series.yaml found in {start} or any parent folder (run `wbx init` first)")


def load(start: Path) -> tuple[dict, Path]:
    root = find_series_root(start)
    user = yaml.safe_load((root / "series.yaml").read_text()) or {}
    cfg = _merge(DEFAULTS, user)
    cfg["series_slug"] = cfg.get("slug") or slugify(cfg["name"])
    return cfg, root


def slugify(s: str) -> str:
    return "-".join("".join(c.lower() if c.isalnum() else " " for c in s).split())


def style_theme(cfg: dict) -> dict | None:
    """The kit theme for the series' style, or None for the original whiteboard style."""
    from .themes import THEMES
    if cfg["style"] == "whiteboard":
        return None
    if cfg["style"] not in THEMES:
        raise SystemExit(f"unknown style {cfg['style']!r}; choose whiteboard, {', '.join(THEMES)}")
    return THEMES[cfg["style"]]


def kit_js_theme(cfg: dict) -> dict:
    st = style_theme(cfg) or THEMES_FALLBACK
    return {**st["js"], "background": st["background"], **(cfg.get("style_options") or {})}


THEMES_FALLBACK = {"js": {}, "background": ""}


def font_override(cfg: dict) -> dict | None:
    """`fonts:` from the config, filled out (title/body/data), or None. Kit styles only."""
    f = cfg.get("fonts")
    if not f or not style_theme(cfg):
        return None
    title = f.get("title") or f.get("body")
    body = f.get("body") or title
    data = f.get("data") or body
    return {"title": title, "body": body, "data": data, "families": list(dict.fromkeys([title, body, data]))}


def font_rules(cfg: dict) -> str:
    """CSS appended after the style's own rules, so `fonts:` wins."""
    fo = font_override(cfg)
    if not fo:
        return ""
    return (f"text{{font-family:'{fo['body']}',sans-serif;font-weight:600}}\n"
            f"text.title,text.label{{font-family:'{fo['title']}',sans-serif;font-weight:800;letter-spacing:0}}\n"
            f"text.label{{letter-spacing:3px}}\n"
            f"text.data{{font-family:'{fo['data']}',sans-serif;font-weight:500}}\n"
            f"#cap{{font-family:'{fo['title']}',sans-serif;font-weight:800}}\n")


def theme_css(cfg: dict) -> str:
    """CSS variables + font import for the runtime stylesheet (appended rules come after wb.css)."""
    st = style_theme(cfg)
    if st:
        cv, js = cfg["canvas"], {**st["js"], **(cfg.get("style_options") or {})}
        fams = "&".join(f"family={f}" for f in st["fonts"])
        first = st["fonts"][0].split(":")[0].replace("+", " ")
        vars_ = {"w": f"{cv['width']}px", "h": f"{cv['height']}px", "font-display": f"'{first}'", "font-body": f"'{first}'",
                 "captions": "block" if cfg["captions"] else "none", "dots": "transparent",
                 "cap-top": f"{cfg.get('caption_top', 1470)}px",
                 "cap-radius": f"{10 * js.get('round', 1)}px",
                 **{k: js[k] for k in ("paper", "ink", "muted", "blue", "red", "green", "orange") if k in js},
                 "grey": js.get("muted"), "highlight": js.get("highlight")}
        fo = font_override(cfg)
        if fo:
            fams += "&" + "&".join(f"family={quote_plus(f)}:wght@400;500;600;700;800;900" for f in fo["families"])
            vars_["font-display"] = vars_["font-body"] = f"'{fo['title']}'"
        body = ";".join(f"--{k}:{v}" for k, v in vars_.items() if v)
        return f"@import url('https://fonts.googleapis.com/css2?{fams}&display=block');\n:root{{{body}}}\n"
    th, cv = cfg["theme"], cfg["canvas"]
    fam = f"family={quote_plus(th['font_display'])}:wght@{th['font_display_weights']}"
    fam += f"&family={quote_plus(th['font_body'])}"
    vars_ = {
        "w": f"{cv['width']}px", "h": f"{cv['height']}px",
        "font-display": f"'{th['font_display']}'", "font-body": f"'{th['font_body']}'",
        "captions": "block" if cfg["captions"] else "none", "cap-top": f"{cfg.get('caption_top', 1470)}px",
        **{k: th[k] for k in ("paper", "ink", "muted", "dots", "blue", "red", "green", "orange", "grey", "highlight")},
    }
    body = ";".join(f"--{k}:{v}" for k, v in vars_.items())
    return f"@import url('https://fonts.googleapis.com/css2?{fam}&display=block');\n:root{{{body}}}\n"
