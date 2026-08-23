import json
from pathlib import Path

from scripts.vercel_pack_static_output import pack_static_output


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
    dests = [r.get("dest") for r in config["routes"] if "dest" in r]
    assert "https://ready-2-robot.fly.dev/api/$1" in dests
    assert "/index.html" in dests
