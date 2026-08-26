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
