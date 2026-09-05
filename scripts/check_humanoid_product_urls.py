#!/usr/bin/env python3
"""Check HTTP status for humanoid catalog product URLs."""
from __future__ import annotations

import re
import ssl
import sys
import urllib.error
import urllib.request
from typing import Iterable, Tuple

import certifi

from app.services.humanoid_vendor_catalog import catalog_entries

UA = "Mozilla/5.0 (compatible; ReadyForRobotsLinkCheck/1.0)"


def _check(url: str) -> Tuple[int | str, bool]:
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            body = resp.read(8000).decode("utf-8", "ignore").lower()
            soft404 = any(x in body for x in ("page not found", "404 error", "could not be found"))
            return resp.status, soft404
    except urllib.error.HTTPError as exc:
        return exc.code, True
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__, True


def broken_urls(entries: Iterable[dict]) -> list[tuple[str, str, str, int | str]]:
    seen: set[str] = set()
    bad: list[tuple[str, str, str, int | str]] = []
    for entry in entries:
        url = entry.get("product_url")
        slug = entry.get("model_slug")
        if not url or url in seen:
            continue
        seen.add(url)
        status, soft404 = _check(url)
        if status in (403, 405):
            continue
        if status not in (200, 201, 202) or soft404:
            bad.append((slug or "?", entry.get("name") or "?", url, status))
    return bad


def main() -> int:
    bad = broken_urls(catalog_entries())
    if not bad:
        print("All catalog product URLs look OK.")
        return 0
    print(f"Broken/suspect URLs: {len(bad)}")
    for slug, name, url, status in bad:
        print(f"  [{status}] {slug}: {name}\n    {url}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
