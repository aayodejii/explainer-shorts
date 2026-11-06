"""Fast tests (no browser, no Whisper). Run: .venv/bin/python -m pytest -q"""
import json

from wbx import audio, cli, config


def test_defaults_merge(tmp_path):
    (tmp_path / "series.yaml").write_text("name: Test Show\ntheme: {blue: '#000000'}\n")
    cfg, root = config.load(tmp_path)
    assert root == tmp_path
    assert cfg["theme"]["blue"] == "#000000"
    assert cfg["theme"]["red"] == config.DEFAULTS["theme"]["red"]   # untouched keys keep defaults
    assert cfg["series_slug"] == "test-show"


def test_theme_css_has_vars_and_fonts():
    css = config.theme_css(config._merge(config.DEFAULTS, {}))
    assert "family=Caveat:wght@600;700&family=Patrick+Hand" in css
    assert "--paper:#FBFAF5" in css and "--captions:none" in css


def test_wpm():
    tr = [{"words": [{"s": 0.0, "e": 0.5, "w": "a"}, {"s": 59.5, "e": 60.0, "w": "b"}]}]
    assert round(audio.wpm(tr)) == 2


def test_new_and_scaffold(tmp_path):
    (tmp_path / "series.yaml").write_text("name: Test Show\nheader: TEST\n")
    cli.main(["new", "n+1 queries", "--title", "The N+1 Problem", "--series", str(tmp_path)])
    ep_dir = tmp_path / "01-n-1-queries"
    assert (ep_dir / "script.md").exists()
    words = [{"s": i * 0.3, "e": i * 0.3 + 0.25, "w": w} for i, w in
             enumerate("One query. Then many more. Save this and share it.".split())]
    (ep_dir / "transcript.json").write_text(json.dumps([{"words": words}]))
    ep = cli.Episode(ep_dir)
    html = cli.scaffold_html(ep, ep.transcript()).read_text()
    assert "The N+1 Problem" in html and "TEST" in html
    assert "{{" not in html                        # every placeholder filled
    save_t = next(w["s"] for w in words if w["w"] == "Save")
    assert f'data-draw="{round(save_t, 2)},0.45"' in html   # end card starts on "Save"
    assert ep.output().name == "test-show-01-n-1-queries.mp4"


def test_kit_scaffold_and_themes(tmp_path):
    from wbx.themes import THEMES
    (tmp_path / "series.yaml").write_text("name: Test Show\nheader: TEST\nstyle: clean\n")
    cli.main(["new", "caching", "--series", str(tmp_path)])
    ep_dir = tmp_path / "01-caching"
    words = [{"s": i * 0.3, "e": i * 0.3 + 0.25, "w": w} for i, w in enumerate("Hi there. Save this.".split())]
    (ep_dir / "transcript.json").write_text(json.dumps([{"words": words}]))
    html = cli.scaffold_html(cli.Episode(ep_dir), json.loads((ep_dir / "transcript.json").read_text())).read_text()
    assert "wbx.kit()" in html and "{{" not in html and "& share it" in html
    (ep_dir / "episode.yaml").write_text("style: chalk\n")      # per-episode override
    assert cli.Episode(ep_dir).cfg["style"] == "chalk"
    for name in THEMES:                                          # every theme builds css + kit values
        cfg = config._merge(config.DEFAULTS, {"style": name})
        assert "@import" in config.theme_css(cfg) and config.kit_js_theme(cfg)["kind"] in ("rough", "clean")
