import json
import re
from pathlib import Path

from scripts.vercel_pack_static_output import (
    LEGAL_HTML_PATHS,
    SPA_SHELL_PATHS,
    pack_static_output,
)

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "readyforrobots-new" / "client" / "src" / "App.tsx"
PUBLIC = ROOT / "readyforrobots-new" / "client" / "public"


def test_pack_static_output_copies_index_and_routes(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text(
        '<script src="/assets/index-abc123.js"></script>\n', encoding="utf-8"
    )
    (dist / "assets").mkdir()
    (dist / "assets" / "index-abc123.js").write_text("console.log(1)\n", encoding="utf-8")
    output = tmp_path / "output"
    packed = pack_static_output(dist=dist, output=output)
    assert (packed / "static" / "index.html").is_file()
    assert (packed / "static" / "assets" / "index-abc123.js").is_file()
    config = json.loads((packed / "config.json").read_text())
    assert config["version"] == 3
    assert config.get("cleanUrls") is not True
    dests = [r.get("dest") for r in config["routes"] if "dest" in r]
    assert "https://ready-2-robot.fly.dev/api/$1" in dests
    assert dests.index("/legal/privacy.html") < dests.index("/index.html")
    assert "/legal/terms.html" in dests
    assert "/legal/support.html" in dests
    assert "/index.html" in dests
    handles = [i for i, r in enumerate(config["routes"]) if r.get("handle") == "filesystem"]
    spa = [i for i, r in enumerate(config["routes"]) if r.get("dest") == "/index.html"]
    assert handles and spa and handles[0] < spa[0]


def test_spa_shell_paths_are_not_static_html():
    """Jobs CRM / signup / About must use the app shell, not a missing .html file."""
    for href in SPA_SHELL_PATHS:
        path = href.split("?", 1)[0].rstrip("/")
        name = path.strip("/")
        assert not (PUBLIC / f"{name}.html").exists(), f"static {name}.html would 404-shadow SPA"
        assert name not in {"privacy", "terms", "support"}
    for href in LEGAL_HTML_PATHS:
        name = href.strip("/")
        assert (PUBLIC / "legal" / f"{name}.html").is_file()


def test_app_routes_except_legal_are_spa_shells():
    paths = re.findall(r'path="(/[^":]+)"', APP.read_text(encoding="utf-8"))
    legal = {p.rstrip("/") for p in LEGAL_HTML_PATHS}
    for path in paths:
        if path in legal:
            continue
        name = path.strip("/")
        if not name or "/" in name:
            continue
        assert not (PUBLIC / f"{name}.html").exists(), path
