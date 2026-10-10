import json
from pathlib import Path


def test_root_vercel_json_points_at_vite_output():
    data = json.loads(Path("vercel.json").read_text())
    assert data["outputDirectory"] == "readyforrobots-new/dist/public"
    assert data["framework"] is None
    cmd = data["ignoreCommand"]
    assert "VERCEL_ENV" in cmd
    assert "cursor/*" in cmd
    assert len(cmd) <= 256
    assert data.get("cleanUrls") is not True
    dests = [r.get("destination") for r in data.get("rewrites") or []]
    assert "/index.html" in dests
    privacy = next(d for d in dests if d and "privacy" in d)
    assert dests.index(privacy) < dests.index("/index.html")


def test_nested_vite_vercel_json_has_spa_fallback():
    data = json.loads(Path("readyforrobots-new/vercel.json").read_text())
    assert data.get("cleanUrls") is not True
    dests = [r.get("destination") for r in data.get("rewrites") or []]
    assert dests[-1] == "/index.html"
    assert "/legal/privacy.html" in dests
