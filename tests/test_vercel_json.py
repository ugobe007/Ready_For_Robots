import json
from pathlib import Path


def test_root_vercel_json_skips_git_builds_on_main():
    data = json.loads(Path("vercel.json").read_text())
    assert data["outputDirectory"] == "readyforrobots-new/dist/public"
    ignore = data["ignoreCommand"]
    assert "VERCEL_GIT_COMMIT_REF" in ignore
    assert "exit 0" in ignore
    assert "main" in ignore
