"""
Pre-built /robots page snapshots — robots list + HEIR intelligence report.

Refreshed every 3 hours (Celery + optional bootstrap). GET handlers are read-only.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.humanoid_catalog_cleanup import is_junk_humanoid_row
from app.services.public_surface_cache import PUBLIC_CACHE_REVALIDATE_SEC, read_public_cache

logger = logging.getLogger(__name__)

KEY_HUMANOID_ROBOTS_LIST = "public:humanoid:robots:v1"
ROBOTS_PAGE_CACHE_TTL_MINUTES = int(
    __import__("os").getenv("ROBOTS_PAGE_CACHE_TTL_MINUTES", "180")
)

_robots_list_mem: dict = {}
_intelligence_mem: dict = {}


def hydrate_robots_list_mem_cache(payload: dict) -> None:
    robots = payload.get("robots") or []
    if not robots:
        return
    _robots_list_mem["v1"] = {"ts": time.monotonic(), "data": payload}


def get_robots_list_mem_cache() -> Optional[dict]:
    entry = _robots_list_mem.get("v1")
    if not entry:
        return None
    if time.monotonic() - float(entry.get("ts") or 0.0) >= PUBLIC_CACHE_REVALIDATE_SEC:
        _robots_list_mem.pop("v1", None)
        return None
    return entry["data"]


def hydrate_intelligence_mem_cache(payload: dict) -> None:
    if not (payload.get("report")):
        return
    _intelligence_mem["v1"] = {"ts": time.monotonic(), "data": payload}


def get_intelligence_mem_cache() -> Optional[dict]:
    entry = _intelligence_mem.get("v1")
    if not entry:
        return None
    if time.monotonic() - float(entry.get("ts") or 0.0) >= PUBLIC_CACHE_REVALIDATE_SEC:
        _intelligence_mem.pop("v1", None)
        return None
    return entry["data"]


def fetch_robots_list_rows(db: Session) -> List[dict]:
    """Full scored robot rows for list API (junk filtered)."""
    from app.api.humanoid_benchmark import _enrich_robot_scores, _slim_robot_for_list

    rows = db.execute(
        text("""
            SELECT id, name, vendor, model_slug, product_url, image_url, status,
                   country, vendor_name_cn, robot_name_cn, vendor_url,
                   humanoid_guide_url, github_url, verification_status,
                   vendor_aliases, robot_aliases,
                     created_at,
                   specs, score_mobility, score_manipulation, score_autonomy,
                   score_safety, score_endurance, score_market_readiness,
                   score_total,
                   heif_mobility, heif_manipulation, heif_cognition,
                   heif_safety, heif_data_pipeline, heif_production, heif_total,
                   last_scraped_at
            FROM humanoid_benchmarks
            ORDER BY score_total DESC NULLS LAST, name ASC
        """)
    ).mappings().all()
    robots = [
        _enrich_robot_scores(dict(r))
        for r in rows
        if not is_junk_humanoid_row(r["name"], r["vendor"], r["model_slug"])
    ]
    return [_slim_robot_for_list(r) for r in robots]


def publish_robots_list_snapshot(db: Session) -> dict[str, Any]:
    from app.services.pipeline_cache_store import cache_write

    robots = fetch_robots_list_rows(db)
    payload = {
        "robots": robots,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(robots),
    }
    cache_write(db, KEY_HUMANOID_ROBOTS_LIST, payload, ttl_minutes=ROBOTS_PAGE_CACHE_TTL_MINUTES)
    hydrate_robots_list_mem_cache(payload)
    logger.info("Humanoid robots list snapshot published (%d robots)", len(robots))
    return {"robots_list_count": len(robots)}


def serve_robots_list() -> dict:
    """Read-only — L1 → durable cache → bundled seed."""
    mem = get_robots_list_mem_cache()
    if mem and (mem.get("robots") or []):
        return {"robots": mem["robots"]}

    cached = read_public_cache(KEY_HUMANOID_ROBOTS_LIST, stale_ok=True)
    if cached and (cached.get("robots") or []):
        hydrate_robots_list_mem_cache(cached)
        out: dict = {"robots": cached["robots"]}
        if cached.get("generated_at"):
            out["generated_at"] = cached["generated_at"]
        return out

    from app.api.humanoid_benchmark import _seed_robots_payload, _slim_robot_for_list

    seed = [_slim_robot_for_list(r) for r in _seed_robots_payload()]
    hydrate_robots_list_mem_cache({"robots": seed})
    return {"robots": seed, "stale": True, "source": "seed"}


def serve_intelligence_report() -> dict:
    """Read-only — L1 → durable HEIR intelligence cache."""
    from app.services.content_surfaces import KEY_HUMANOID_INTELLIGENCE

    mem = get_intelligence_mem_cache()
    if mem and mem.get("report"):
        return mem

    cached = read_public_cache(KEY_HUMANOID_INTELLIGENCE, stale_ok=True)
    if cached and cached.get("report"):
        hydrate_intelligence_mem_cache(cached)
        return cached

    return {
        "report": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cache_pending": True,
        "message": "Intelligence report snapshot is building. Retry shortly.",
    }
