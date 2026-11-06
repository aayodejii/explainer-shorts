"""Visual themes for kit-based episodes.

`style: whiteboard` (the default) is the original look: episodes draw their own
SVG and use the `theme:` colours in series.yaml. The styles below are used with
the building-block kit (runtime/kit.js): the episode asks for "a card at t=2",
and the theme decides how it looks and how it enters.

Each theme has:
  fonts       Google Fonts families (css2 `family=` values)
  css         extra rules (fonts per text class)
  background  SVG markup inserted behind everything (defs + paper)
  js          values handed to kit.js (kind, colours, stroke settings)
`style_options` in series.yaml is merged over `js`.
"""
from __future__ import annotations

SKETCH = {
    "fonts": ["Kalam:wght@400;700", "Gochi+Hand"],
    "css": """
text{font-family:'Kalam',cursive;font-weight:700}
text.title{font-family:'Gochi Hand',cursive;font-weight:400}
text.label{letter-spacing:3px}
""",
    "background": """
<defs><filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="4"/>
  <feColorMatrix values="0 0 0 0 .45  0 0 0 0 .38  0 0 0 0 .28  0 0 0 .55 -.18"/></filter></defs>
<rect width="100%" height="100%" fill="#FAF6EC"/><rect width="100%" height="100%" filter="url(#grain)"/>
""",
    "js": {
        "kind": "rough", "paper": "#FAF6EC", "ink": "#22252E", "muted": "#6B6F7B", "accent": "#E0412F",
        "blue": "#2563EB", "green": "#15803D", "red": "#DC2626", "orange": "#E8890C",
        "fills": {"blue": "#9CC2FF", "green": "#8FE0A6", "red": "#FFB4AA", "yellow": "#FFD65C", "orange": "#FFC98A"},
        "highlight": "#FFE680", "roughness": 1.5, "stroke": 4, "hatchGap": 12, "fillWeight": 2.2,
    },
}

CLEAN = {
    "fonts": ["Nunito:wght@600;800;900", "JetBrains+Mono:wght@600"],
    "css": """
text{font-family:'Nunito',sans-serif;font-weight:800}
text.title{font-weight:900}
text.data{font-family:'JetBrains Mono',monospace;font-weight:600}
text.label{font-weight:900;letter-spacing:4px}
""",
    "background": """
<defs>
  <filter id="sh" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#1B1F2A" flood-opacity=".12"/></filter>
  <pattern id="grid" width="54" height="54" patternUnits="userSpaceOnUse"><path d="M54 0H0V54" fill="none" stroke="#E7E3DA" stroke-width="2"/></pattern>
</defs>
<rect width="100%" height="100%" fill="#F5F3EE"/><rect width="100%" height="100%" fill="url(#grid)"/>
""",
    "js": {
        "kind": "clean", "paper": "#F5F3EE", "ink": "#1B1F2A", "muted": "#7A7F8C", "accent": "#2F6BFF",
        "blue": "#2F6BFF", "green": "#14974A", "red": "#D93A2B", "orange": "#E07A10",
        "tints": {"green": "#E3F8EA", "red": "#FDE8E6", "orange": "#FFF0DD", "blue": "#E8EFFF"},
        "highlight": "#FFE27A", "endSmall": 48,
    },
}

CHALK = {
    "fonts": ["Gaegu:wght@700", "Cabin+Sketch:wght@700"],
    "css": """
text{font-family:'Gaegu',cursive;font-weight:700}
text.title{font-family:'Cabin Sketch',cursive}
text.label{letter-spacing:3px}
""",
    "background": """
<defs>
  <filter id="chalk" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="2" seed="9" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -2.2 0 0 0 2.0" result="m"/>
    <feComposite in="SourceGraphic" in2="m" operator="in"/></filter>
  <radialGradient id="vig" cx=".5" cy=".45" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".45"/></radialGradient>
  <filter id="smudge"><feTurbulence type="fractalNoise" baseFrequency=".006" numOctaves="3" seed="2"/>
    <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .14 -.04"/></filter>
</defs>
<rect width="100%" height="100%" fill="#1E2A27"/><rect width="100%" height="100%" filter="url(#smudge)"/>
<rect width="100%" height="100%" fill="url(#vig)"/>
""",
    "js": {
        "kind": "rough", "rootFilter": "chalk", "paper": "#1E2A27", "ink": "#F1EFE6", "muted": "#A9B5AE",
        "accent": "#FFD95E", "blue": "#8CC8FF", "green": "#94E8A4", "red": "#FF8F8F", "orange": "#FFB86B",
        "fills": {"blue": "#8CC8FF", "green": "#94E8A4", "red": "#FF8F8F", "yellow": "#FFD95E", "orange": "#FFB86B"},
        "highlight": "rgba(255,217,94,.45)", "roughness": 1.8, "stroke": 5, "hatchGap": 16, "fillWeight": 2,
        "fillOpacity": 0.3,
    },
}

THEMES = {"sketch": SKETCH, "clean": CLEAN, "chalk": CHALK}
