"""
Content surfaces — pre-built public payloads (read-only GET, background refresh).

Every marketing / pipeline page should map to a surface here:
  • Built by refresh_* jobs (2h loop, deploy warm, cron, or Celery)
  • Served from pipeline_cache_store + in-process L1
  • GET handlers never run heavy DB/OpenAI/PDF work on the request path

Add new pages by registering a cache key + refresh function, then wire the API to read_public_cache only.
"""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Cache keys (pipeline_cache_store)
KEY_HOMEPAGE = "public:homepage:v1"
KEY_SUMMARY_EXCLUDE_JUNK = "public:summary:exclude_junk:true:v1"
KEY_SUMMARY_INCLUDE_JUNK = "public:summary:exclude_junk:false:v1"
KEY_LEADS_50 = "public:leads:list:50:score:v1"
KEY_LEADS_18 = "public:leads:list:18:score:v1"
KEY_LEADS_HOT_12 = "public:leads:list:12:hot:score:v1"
KEY_HUMANOID_BENCHMARK_REPORT = "public:humanoid:report:v1"
KEY_HUMANOID_INTELLIGENCE = "public:humanoid:intelligence:v1"
KEY_HUMANOID_INTELLIGENCE_PDF = "public:humanoid:intelligence_pdf:weasyprint:v2"
KEY_NEWSLETTER_EDITION = "public:newsletter:edition:v1"  # alias of newsletter durable key
KEY_SOCIAL_DAILY_POSTS = "public:social:daily_posts:v1"

RefreshFn = Callable[[Session], dict[str, Any]]


@dataclass(frozen=True)
class ContentSurface:
    id: str
    cache_key: str
    description: str
    refresh: RefreshFn
    ttl_minutes: int = 120
    ai_heavy: bool = False


def refresh_intelligence_surface(db: Session, *, top_n: int = 12) -> dict[str, Any]:
    """HEIR intelligence JSON + fast PDF — for /robots report UI and download."""
    from app.api.humanoid_benchmark import _fetch_scored_humanoids
    from app.services.humanoid_catalog_cleanup import is_junk_humanoid_row
    from app.services.humanoid_intelligence_report import build_humanoid_intelligence_report_payload
    from app.services.humanoid_intelligence_report_pdf import build_humanoid_intelligence_report_pdf
    from app.services.pipeline_cache_store import cache_write

    robots = _fetch_scored_humanoids(db)
    robots = [
        r for r in robots
        if not is_junk_humanoid_row(r["name"], r["vendor"], r["model_slug"])
    ]
    payload = build_humanoid_intelligence_report_payload(robots, top_n=top_n, db=db)
    cache_write(db, KEY_HUMANOID_INTELLIGENCE, payload, ttl_minutes=120)

    pdf_stats: dict[str, Any] = {}
    if payload.get("report"):
        try:
            pdf_bytes, filename = build_humanoid_intelligence_report_pdf(payload, renderer="fast")
            cache_write(
                db,
                KEY_HUMANOID_INTELLIGENCE_PDF,
                {
                    "filename": filename,
                    "bytes_b64": base64.standard_b64encode(pdf_bytes).decode("ascii"),
                    "generated_at": payload.get("generated_at"),
                    "renderer": "fast",
                },
                ttl_minutes=120,
            )
            pdf_stats = {"pdf_bytes": len(pdf_bytes), "filename": filename}
        except Exception as exc:
            logger.warning("intelligence PDF pre-render failed: %s", exc)

    stats = {
        "intelligence_top_n": top_n,
        "robots": payload.get("report", {}).get("total_robots") if payload.get("report") else 0,
        **pdf_stats,
    }
    logger.info("Intelligence surface refreshed: %s", stats)
    return stats


def list_surfaces() -> list[ContentSurface]:
    """Registry of all pre-built surfaces (for cron docs / admin)."""
    from app.services.public_surface_cache import (
        refresh_newsletter_surface_cache,
        refresh_pipeline_surface_caches,
        refresh_social_posts_surface_cache,
    )
    from app.services.newsletter_service import NEWSLETTER_PIPELINE_CACHE_KEY

    return [
        ContentSurface("homepage", KEY_HOMEPAGE, "Pipeline homepage hot leads", refresh_pipeline_surface_caches, ai_heavy=False),
        ContentSurface("newsletter", NEWSLETTER_PIPELINE_CACHE_KEY, "Daily newsletter edition", lambda db: refresh_newsletter_surface_cache(db, force=False), ai_heavy=True),
        ContentSurface("social", KEY_SOCIAL_DAILY_POSTS, "Content Studio daily posts", refresh_social_posts_surface_cache, ttl_minutes=240),
        ContentSurface("humanoid_benchmark", KEY_HUMANOID_BENCHMARK_REPORT, "Robots index HEIF table", refresh_pipeline_surface_caches),
        ContentSurface(
            "humanoid_intelligence",
            KEY_HUMANOID_INTELLIGENCE,
            "Strategic HEIR intelligence report JSON",
            refresh_intelligence_surface,
            ai_heavy=True,
        ),
    ]


def refresh_all_content_surfaces(db: Session, *, newsletter_force: bool = False) -> dict[str, Any]:
    """Full background rebuild — call from cron, deploy warm, or admin."""
    from app.services.public_surface_cache import (
        refresh_newsletter_surface_cache,
        refresh_pipeline_surface_caches,
        refresh_social_posts_surface_cache,
    )

    stats: dict[str, Any] = {}
    stats.update(refresh_pipeline_surface_caches(db))
    stats.update(refresh_newsletter_surface_cache(db, force=newsletter_force))
    stats.update(refresh_social_posts_surface_cache(db))
    stats.update(refresh_intelligence_surface(db))
    return stats
