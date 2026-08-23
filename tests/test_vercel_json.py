import json
from pathlib import Path


def test_root_vercel_json_points_at_vite_output():
    data = json.loads(Path("vercel.json").read_text())
    assert data["outputDirectory"] == "readyforrobots-new/dist/public"
    assert data["framework"] is None
    assert "ignoreCommand" not in data
