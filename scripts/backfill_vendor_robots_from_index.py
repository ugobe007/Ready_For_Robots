#!/usr/bin/env python3
"""Scrape readyforrobots.com/robots and backfill vendor → robot lookup.

The public /robots page is served from GET /api/humanoid/robots. This script
pulls that list, drops press-host URLs, groups SKUs by OEM domain, builds a
lightweight profile from indexed specs, and writes
`app/data/vendor_robots_index.json`.

Jobs URL lookup reads that file so a manufacturer homepage returns stored
robots instead of guessing from a crawl.

  PYTHONPATH=. python scripts/backfill_vendor_robots_from_index.py
  PYTHONPATH=. python scripts/backfill_vendor_robots_from_index.py --apply

`--apply` upserts manufacturers + robot_models (ontology path for later
industrial / commercial lists). JSON is always written; lookup does not
require the SQL rows.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.vendor_robot_lookup import (
    INDEX_PATH,
    VENDOR_HOME_FALLBACK,
    host_from_url,
    is_junk_lookup_host,
    lookup_domain,
    profile_from_specs,
    slim_specs,
)


def _humanoid_catalog() -> list[dict[str, Any]]:
    """Optional seed URLs. Live /robots JSON is the source of truth."""
    try:
        from app.services.humanoid_vendor_catalog import HUMANOID_CATALOG

        return list(HUMANOID_CATALOG)
    except Exception:
        return []

DEFAULT_SOURCE = "https://ready-2-robot.fly.dev/api/humanoid/robots"
LIST_CATEGORY = "humanoid"


def _vendor_key(name: str) -> str:
    n = re.sub(r"\s+", " ", (name or "").strip().lower())
    n = n.split("/")[0].strip()
    if n.startswith("ubtech"):
        return "ubtech robotics"
    if n.startswith("agibot"):
        return "agibot"
    if n.startswith("engineai"):
        return "engineai"
    return n


def _get_json(url: str, timeout: float = 45.0) -> dict[str, Any]:
    req = Request(
        url,
        headers={
            "User-Agent": "ReadyForRobots-vendor-index/1.0 (+https://readyforrobots.com)",
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _catalog_by_slug() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in _humanoid_catalog():
        slug = (row.get("model_slug") or "").strip()
        if slug:
            out[slug] = row
    return out


def _catalog_vendor_home(vendor_name: str) -> str:
    raw = re.sub(r"\s+", " ", (vendor_name or "").strip().lower())
    key = _vendor_key(vendor_name)
    for lookup in (raw, key):
        if lookup in VENDOR_HOME_FALLBACK:
            return VENDOR_HOME_FALLBACK[lookup]
    for row in _humanoid_catalog():
        if _vendor_key(row.get("vendor") or "") != key:
            continue
        for field in ("vendor_url", "product_url"):
            url = (row.get(field) or "").strip()
            host = host_from_url(url)
            if url and host and not is_junk_lookup_host(host):
                return url if "://" in url else f"https://{url}"
    return ""


def _pick_vendor_url(row: dict[str, Any], catalog_row: dict[str, Any] | None) -> str:
    candidates = [
        row.get("vendor_url"),
        (catalog_row or {}).get("vendor_url"),
        row.get("product_url"),
        (catalog_row or {}).get("product_url"),
        _catalog_vendor_home(row.get("vendor") or ""),
    ]
    for raw in candidates:
        url = (raw or "").strip()
        if not url:
            continue
        if "://" not in url:
            url = "https://" + url
        if not is_junk_lookup_host(host_from_url(url)):
            return url
    return ""


def _pick_product_url(row: dict[str, Any], catalog_row: dict[str, Any] | None, vendor_url: str) -> str:
    for raw in (row.get("product_url"), (catalog_row or {}).get("product_url"), vendor_url):
        url = (raw or "").strip()
        if not url:
            continue
        if "://" not in url:
            url = "https://" + url
        if not is_junk_lookup_host(host_from_url(url)):
            return url
    return vendor_url


def build_index(robots: list[dict[str, Any]], *, source: str) -> dict[str, Any]:
    catalog = _catalog_by_slug()
    buckets: dict[str, dict[str, Any]] = {}
    skipped: list[str] = []

    for row in robots:
        name = (row.get("name") or "").strip()
        vendor = (row.get("vendor") or "").strip()
        slug = (row.get("model_slug") or "").strip()
        if not name or not vendor:
            skipped.append(slug or name or "?")
            continue
        cat = catalog.get(slug)
        vendor_url = _pick_vendor_url(row, cat)
        product_url = _pick_product_url(row, cat, vendor_url)
        domain = lookup_domain(vendor_url) or lookup_domain(product_url)
        if not domain:
            skipped.append(f"{vendor}/{name}")
            continue
        key = _vendor_key(vendor)
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {
                "vendor_name": vendor,
                "domains": [],
                "vendor_url": vendor_url,
                "list_category": LIST_CATEGORY,
                "robots": [],
            }
            buckets[key] = bucket
        else:
            current = bucket.get("vendor_name") or ""
            if "/" in current and "/" not in vendor:
                bucket["vendor_name"] = vendor
            elif len(vendor) > len(current) and "/" not in vendor:
                bucket["vendor_name"] = vendor
        for host in (
            lookup_domain(vendor_url),
            host_from_url(vendor_url),
            lookup_domain(product_url),
        ):
            if host and not is_junk_lookup_host(host) and host not in bucket["domains"]:
                bucket["domains"].append(host)
        specs = slim_specs(row.get("specs") if isinstance(row.get("specs"), dict) else None)
        robot = {
            "name": name,
            "model_slug": slug,
            "product_url": product_url,
            "vendor_url": vendor_url,
            "primary_class": LIST_CATEGORY,
            "status": row.get("status") or "research",
            "country": row.get("country"),
            "image_url": row.get("image_url"),
            "specs": specs,
            "profile": profile_from_specs(
                robot_name=name,
                vendor_name=vendor,
                domain=domain,
                product_url=product_url,
                specs=specs,
                list_category=LIST_CATEGORY,
            ),
        }
        existing = {r.get("model_slug") for r in bucket["robots"]}
        if slug and slug in existing:
            continue
        bucket["robots"].append(robot)

    vendors = sorted(buckets.values(), key=lambda v: v["vendor_name"].lower())
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": source,
        "list_category": LIST_CATEGORY,
        "vendor_count": len(vendors),
        "robot_count": sum(len(v["robots"]) for v in vendors),
        "skipped": skipped,
        "vendors": vendors,
    }


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return slug[:120] or f"vendor-{uuid.uuid4().hex[:8]}"


def apply_to_catalog(index: dict[str, Any]) -> dict[str, int]:
    """Upsert manufacturers + humanoid models for ontology lists."""
    from sqlalchemy.orm import Session

    from app.database import SessionLocal
    from app.models.robot_catalog import Manufacturer, RobotFamily, RobotModel

    stats = {"manufacturers": 0, "models": 0, "updated": 0}
    db: Session = SessionLocal()
    try:
        for vendor in index.get("vendors") or []:
            domain = (vendor.get("domains") or [None])[0]
            website = vendor.get("vendor_url") or (f"https://{domain}" if domain else None)
            slug = _slugify(vendor.get("vendor_name") or domain or "vendor")
            mfr = db.query(Manufacturer).filter(Manufacturer.slug == slug).one_or_none()
            if mfr is None and website:
                mfr = (
                db.query(Manufacturer)
                .filter(Manufacturer.website.ilike(f"%{domain}%"))
                .first()
                if domain
                else None
            )
            if mfr is None:
                mfr = Manufacturer(
                    slug=slug,
                    name=vendor["vendor_name"],
                    website=website,
                    vendor_role="robot_oem",
                    vendor_type="oem",
                    robot_categories=["humanoid"],
                    verification_status="indexed",
                    source_url=index.get("source"),
                    notes="Backfilled from readyforrobots.com/robots vendor index.",
                    external_refs={"vendor_robots_index": True, "domains": vendor.get("domains")},
                )
                db.add(mfr)
                db.flush()
                stats["manufacturers"] += 1
            else:
                if website and not mfr.website:
                    mfr.website = website
                stats["updated"] += 1

            family = (
                db.query(RobotFamily)
                .filter(
                    RobotFamily.manufacturer_id == mfr.id,
                    RobotFamily.slug == "humanoid",
                )
                .one_or_none()
            )
            if family is None:
                family = RobotFamily(
                    manufacturer_id=mfr.id,
                    slug="humanoid",
                    name="Humanoid",
                    primary_class="humanoid",
                )
                db.add(family)
                db.flush()

            for robot in vendor.get("robots") or []:
                model_slug = (robot.get("model_slug") or _slugify(robot["name"]))[:160]
                model = db.query(RobotModel).filter(RobotModel.slug == model_slug).one_or_none()
                payload = {
                    "name": robot["name"],
                    "primary_class": "humanoid",
                    "product_url": robot.get("product_url"),
                    "commercial_maturity": robot.get("status") or "unknown",
                    "external_refs": {
                        "vendor_robots_index": True,
                        "profile": robot.get("profile"),
                        "specs": robot.get("specs"),
                    },
                    "is_active": True,
                }
                if model is None:
                    model = RobotModel(
                        manufacturer_id=mfr.id,
                        family_id=family.id,
                        slug=model_slug,
                        **payload,
                    )
                    db.add(model)
                    stats["models"] += 1
                else:
                    for key, val in payload.items():
                        setattr(model, key, val)
                    stats["updated"] += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Robots list API URL")
    parser.add_argument("--out", default=str(INDEX_PATH), help="JSON index path")
    parser.add_argument("--apply", action="store_true", help="Upsert manufacturers + robot_models")
    args = parser.parse_args()

    payload = _get_json(args.source)
    robots = payload.get("robots") if isinstance(payload, dict) else payload
    if not isinstance(robots, list) or not robots:
        print("No robots returned from", args.source, file=sys.stderr)
        return 1

    index = build_index(robots, source=args.source)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Wrote {out_path} — {index['vendor_count']} vendors, "
        f"{index['robot_count']} robots, skipped {len(index['skipped'])}"
    )
    if index["skipped"]:
        print("Skipped (no OEM domain):", ", ".join(index["skipped"][:12]))

    if args.apply:
        stats = apply_to_catalog(index)
        print("DB apply", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
