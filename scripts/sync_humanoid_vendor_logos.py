#!/usr/bin/env python3
"""Download vendor favicons and strip light backgrounds for dark UI panels."""
from __future__ import annotations

import re
import ssl
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import certifi
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "app/services/humanoid_vendor_catalog.py"
OUT_DIR = ROOT / "readyforrobots-new/client/public/logos/vendors"
SIMPLE_ICON_COLOR = "c4b5fd"  # violet-300 — matches site accent

SIMPLE_ICON_SLUGS: Dict[str, str] = {
    "tesla": "tesla",
    "toyota": "toyota",
    "honda": "honda",
    "xiaomi": "xiaomi",
    "nvidia": "nvidia",
    "hyundai": "hyundai",
    "samsung": "samsung",
    "intel": "intel",
    "amazon-robotics": "amazon",
    "apple-robotics": "apple",
    "google-deepmind": "google",
    "microsoft-robotics": "microsoft",
    "meta-ai": "meta",
    "byd-robotics": "byd",
    "xpeng-robotics": "xpeng",
}


def vendor_key(vendor: str) -> str:
    base = vendor.split("(")[0].strip().lower()
    base = re.sub(r"\brobotics?\b", "", base).strip()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def _parse_catalog() -> Dict[str, Optional[str]]:
    text = CATALOG.read_text(encoding="utf-8")
    vendors: Dict[str, Optional[str]] = {}
    for block in re.findall(r"\{[^{}]+\}", text):
        vm = re.search(r'"vendor": "([^"]+)"', block)
        pm = re.search(r'"product_url": "([^"]+)"', block)
        if not vm:
            continue
        v = vm.group(1)
        domain = None
        if pm:
            domain = urlparse(pm.group(1)).netloc.replace("www.", "") or None
        key = vendor_key(v)
        if key not in vendors or (domain and not vendors[key]):
            vendors[key] = domain
    return vendors


def _fetch(url: str) -> bytes:
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "ReadyForRobots/1.0 logo-sync"})
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        return resp.read()


def _strip_light_background(img: Image.Image, threshold: int = 235) -> Image.Image:
    rgba = img.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if r >= threshold and g >= threshold and b >= threshold:
                px[x, y] = (r, g, b, 0)
    return rgba


def _save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=True)


def _download_favicon(domain: str) -> Optional[Image.Image]:
    for url in (
        f"https://www.google.com/s2/favicons?domain={domain}&sz=128",
        f"https://icons.duckduckgo.com/ip3/{domain}.ico",
    ):
        try:
            raw = _fetch(url)
            if len(raw) < 80:
                continue
            from io import BytesIO

            img = Image.open(BytesIO(raw))
            return _strip_light_background(img)
        except Exception:
            continue
    return None


def _download_simple_icon(slug: str) -> Optional[Image.Image]:
    try:
        raw = _fetch(f"https://cdn.simpleicons.org/{slug}/{SIMPLE_ICON_COLOR}")
        from io import BytesIO

        img = Image.open(BytesIO(raw))
        return img.convert("RGBA")
    except Exception:
        return None


def sync() -> Tuple[int, int]:
    vendors = _parse_catalog()
    ok = 0
    for key, domain in sorted(vendors.items()):
        out = OUT_DIR / f"{key}.png"
        img: Optional[Image.Image] = None
        if key in SIMPLE_ICON_SLUGS:
            img = _download_simple_icon(SIMPLE_ICON_SLUGS[key])
        if img is None and domain:
            img = _download_favicon(domain)
        if img is None:
            continue
        # Normalize size
        img = img.convert("RGBA")
        img.thumbnail((128, 128), Image.Resampling.LANCZOS)
        _save_png(img, out)
        ok += 1
    return ok, len(vendors)


if __name__ == "__main__":
    saved, total = sync()
    print(f"Saved {saved}/{total} vendor logos to {OUT_DIR}")
