#!/usr/bin/env python3
"""Compile local FIND lineups from the merged vendor index.

Writes readyforrobots-new/client/src/lib/knownOemLineups.json.
Every named robot on the vendor is stored. FIND still surfaces three at a time.
Does not crawl OEM sites or invent SKUs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.jobs_oem_listing import (  # noqa: E402
    format_listing_blurb,
    host_from_website,
    listing_from_catalog,
)
from app.services.vendor_robot_lookup import (  # noqa: E402
    JUNK_LOOKUP_HOSTS,
    load_vendor_robots_index,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)

OUT = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "knownOemLineups.json"


def _hosts_for_vendor(vendor: dict) -> list[str]:
    hosts: list[str] = []
    seen: set[str] = set()
    url = (vendor.get("vendor_url") or "").strip()
    if url:
        host = host_from_website(url)
        if host and host not in seen:
            hosts.append(host)
            seen.add(host)
    for raw in vendor.get("domains") or []:
        host = str(raw or "").strip().lower().removeprefix("www.")
        if host and host not in seen and host not in JUNK_LOOKUP_HOSTS:
            hosts.append(host)
            seen.add(host)
    return hosts


def compile_lineups() -> dict:
    reload_vendor_robots_index()
    index = load_vendor_robots_index()
    out: dict[str, dict] = {}
    for vendor in index.get("vendors") or []:
        for host in _hosts_for_vendor(vendor):
            if host in out or host in JUNK_LOOKUP_HOSTS:
                continue
            hit = lookup_vendor_by_url(f"https://{host}/")
            if not hit or not (hit.get("robots") or []):
                continue
            robots = []
            for row in listing_from_catalog(hit):
                robots.append(
                    {
                        "name": row["name"],
                        "description": format_listing_blurb(row),
                        "display_class": row.get("display_class"),
                    }
                )
            if not robots:
                continue
            out[host] = {
                "vendor_name": (hit.get("vendor_name") or "").strip() or None,
                "robots": robots,
            }
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


def main() -> int:
    data = compile_lineups()
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    robot_count = sum(len(v["robots"]) for v in data.values())
    gt3 = sum(1 for v in data.values() if len(v["robots"]) > 3)
    print(
        f"wrote {OUT.relative_to(ROOT)} hosts={len(data)} robots={robot_count} hosts_gt3={gt3}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
