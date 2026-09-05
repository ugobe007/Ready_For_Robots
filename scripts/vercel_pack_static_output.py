"""Pack Vite dist/public into Vercel Build Output API v3 for `vercel deploy --prebuilt`.

Cloud `vercel deploy` on a project-scoped token returns Ready before Vite finishes
and reuses a stale hashed bundle. Building in GitHub Actions and uploading
`.vercel/output` makes the production JS the one we just compiled.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
DIST = _root / "readyforrobots-new" / "dist" / "public"
OUTPUT = _root / ".vercel" / "output"

API = "https://ready-2-robot.fly.dev"

ROUTES = [
    {"src": "^/api(?:/(.*))$", "dest": f"{API}/api/$1"},
    {"src": "^/health$", "dest": f"{API}/health"},
    {"src": "^/health(?:/(.*))$", "dest": f"{API}/health/$1"},
    {"handle": "filesystem"},
    {"src": "/(.*)", "dest": "/index.html"},
]


def pack_static_output(*, dist: Path = DIST, output: Path = OUTPUT) -> Path:
    if not dist.is_dir() or not (dist / "index.html").is_file():
        raise FileNotFoundError(f"Vite output missing at {dist}")
    if output.exists():
        shutil.rmtree(output)
    static = output / "static"
    shutil.copytree(dist, static)
    (output / "config.json").write_text(
        json.dumps({"version": 3, "routes": ROUTES}, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    packed = pack_static_output()
    index = (packed / "static" / "index.html").read_text(encoding="utf-8")
    if "/assets/index-" not in index:
        raise SystemExit("Packed index.html has no hashed JS bundle")
    print(f"Packed {packed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
