#!/usr/bin/env python3
"""Qualify a robot URL from manufacturer page photos + text.

Usage:
  python3 scripts/qualify_robot.py https://www.1x.tech/neo

Prints the morphological class Understanding would ground, the photos it
used, and the picker options the Jobs UI shows when class is still unknown.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.robot_class_qualify import public_class_options
from app.services.robot_understanding_v1.fetch import fetch_page
from app.services.robot_visual_class import classify_image_hints


def main(argv: list[str]) -> int:
    url = (argv[1] if len(argv) > 1 else "").strip()
    if not url:
        print("usage: qualify_robot.py <product-url>", file=sys.stderr)
        return 2
    page = fetch_page(url)
    images = list(page.image_alts or [])
    hit = classify_image_hints(images, page.text or "")
    out = {
        "url": page.final_url or url,
        "title": page.title,
        "photo_count": len(images),
        "photos": [{"url": u, "alt": a} for u, a in images[:8]],
        "class": hit[0] if hit else None,
        "evidence": hit[1] if hit else None,
        "humanoid_in_text": "humanoid" in (page.text or "").lower(),
        "picker_options": public_class_options(),
    }
    print(json.dumps(out, indent=2))
    return 0 if hit else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
