"""Serve a series folder over local HTTP and drive it with headless Chrome.

Episode pages load the runtime from `/_wbx/wb.css` and `/_wbx/wb.js`. Those
paths are answered from the package (with the series theme prepended to the
CSS), so episodes don't depend on where the tool is installed.
"""
from __future__ import annotations

import contextlib
import functools
import http.server
import json
import os
import shutil
import sys
import threading
from pathlib import Path

from .config import kit_js_theme, style_theme, theme_css

RUNTIME = Path(__file__).parent / "runtime"


class _Handler(http.server.SimpleHTTPRequestHandler):
    cfg: dict = {}

    def log_message(self, *a):  # keep the console quiet
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/_wbx/"):
            name = path[len("/_wbx/"):]
            if name == "wb.css":
                st = style_theme(self.cfg)
                body = (theme_css(self.cfg) + (RUNTIME / "wb.css").read_text() + (st["css"] if st else "")).encode()
                ctype = "text/css"
            elif name == "kit.js":
                body = ((RUNTIME / "vendor" / "rough.js").read_text() + "\n"
                        + f"window.WBX_THEME={json.dumps(kit_js_theme(self.cfg))};\n"
                        + (RUNTIME / "kit.js").read_text()).encode()
                ctype = "application/javascript"
            elif name == "wb.js":
                body, ctype = (RUNTIME / "wb.js").read_bytes(), "application/javascript"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


@contextlib.contextmanager
def serve(root: Path, cfg: dict):
    handler = type("H", (_Handler,), {"cfg": cfg})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(handler, directory=str(root)))
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()


def chrome_path(cfg: dict) -> str | None:
    """Explicit config/env path, else system Chrome, else Playwright's bundled Chromium (None)."""
    for p in (os.environ.get("WBX_CHROME"), cfg.get("chrome")):
        if p:
            return p
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if (p := shutil.which(name)):
            return p
    return None


@contextlib.contextmanager
def open_page(html: Path, root: Path, cfg: dict, words: list | None = None):
    """Yield a Playwright page with the episode loaded and fonts ready."""
    from playwright.sync_api import sync_playwright

    cv = cfg["canvas"]
    with serve(root, cfg) as base, sync_playwright() as p:
        br = p.chromium.launch(executable_path=chrome_path(cfg), args=["--disable-dev-shm-usage"])
        pg = br.new_page(viewport={"width": cv["width"], "height": cv["height"]})
        pg.set_default_timeout(120000)
        pg.on("pageerror", lambda e: print(f"page error: {e}", file=sys.stderr))
        pg.add_init_script(f"window.WORDS={json.dumps(words or [])}")
        rel = html.resolve().relative_to(root.resolve()).as_posix()
        pg.goto(f"{base}/{rel}")
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        try:
            yield pg
        finally:
            br.close()


def warm_up(pg, duration: float):
    """Visit every scene once so all fonts/glyph subsets load before capture."""
    for k in range(int(duration * 4) + 1):
        pg.evaluate(f"render({k / 4})")
    pg.evaluate("document.fonts.ready")
    pg.screenshot(type="jpeg")
    pg.evaluate("render(0)")
