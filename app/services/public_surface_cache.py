"""
Pre-built public page caches — rebuilt once each morning by Celery, served read-only on GET.

Policy: newsletter, pipeline/homepage, summary, and similar public endpoints must never
run heavy generation (OpenAI, full-table scans) on page load. Request handlers hydrate
from Postgres pipeline_cache_store (+ in-process L1) and return immediately.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.newsletter_service import NEWSLETTER_PIPELINE_CACHE_KEY
from app.services.pipeline_cache_store import cache_read_safe, cache_write

logger = logging.getLogger(__name__)

# ~26 hours — survives a missed beat run; refreshed daily at 6:15 UTC (+ 10:00 incremental).
PUBLIC_CACHE_TTL_MINUTES = 26 * 60

KEY_HOMEPAGE = "public:homepage:v1"
KEY_SUMMARY_EXCLUDE_JUNK = "public:summary:exclude_junk:true:v1"
KEY_SUMMARY_INCLUDE_JUNK = "public:summary:exclude_junk:false:v1"
KEY_LEADS_50 = "public:leads:list:50:score:v1"
KEY_LEADS_18 = "public:leads:list:18:score:v1"
KEY_LEADS_HOT_12 = "public:leads:list:12:hot:score:v1"
KEY_HUMANOID_REPORT = "public:humanoid:report:v1"


def read_public_cache(cache_key: str, *, stale_ok: bool = True) -> Optional[Any]:
    return cache_read_safe(cache_key, stale_ok=stale_ok, timeout_sec=8.0)


def write_public_cache(db: Session, cache_key: str, data: Any) -> None:
    cache_write(db, cache_key, data, ttl_minutes=PUBLIC_CACHE_TTL_MINUTES)


def refresh_all_public_surface_caches(db: Session) -> dict[str, Any]:
    """
    Full morning rebuild — newsletter (with OpenAI brief), homepage, summaries,
    pipeline lead lists, and humanoid benchmark report.
    """
    from app.api.humanoid_benchmark import build_humanoid_report_payload
    from app.api.leads import (
        _build_homepage_payload,
        _compute_pipeline_summary,
        build_public_leads_list,
    )
    from app.services.industry_brief_service import build_industry_brief_payload
    from app.services.newsletter_library import build_daily_newsletter_edition
    from app.services.newsletter_service import write_cached_edition

    stats: dict[str, Any] = {}

    newsletter = build_daily_newsletter_edition(
        db,
        limit=15,
        force=True,
        skip_openai_brief=False,
    )
    write_cached_edition(newsletter, db)
    write_public_cache(db, NEWSLETTER_PIPELINE_CACHE_KEY, newsletter)
    stats["newsletter_stories"] = len(newsletter.get("topStories") or [])
    stats["newsletter_update_mode"] = (newsletter.get("_meta") or {}).get("update_mode")

    homepage = _build_homepage_payload(db)
    write_public_cache(db, KEY_HOMEPAGE, homepage)
    stats["homepage_hot_leads"] = len(homepage.get("hotLeads") or [])

    for exclude_junk, key in (
        (True, KEY_SUMMARY_EXCLUDE_JUNK),
        (False, KEY_SUMMARY_INCLUDE_JUNK),
    ):
        summary = _compute_pipeline_summary(db, exclude_junk)
        write_public_cache(db, key, summary)

    for limit, tier, key in (
        (50, None, KEY_LEADS_50),
        (18, None, KEY_LEADS_18),
        (12, "HOT", KEY_LEADS_HOT_12),
    ):
        leads = build_public_leads_list(db, limit=limit, tier=tier)
        write_public_cache(db, key, leads)
        stats[f"leads_{limit}_{tier or 'all'}"] = len(leads)

    report = build_humanoid_report_payload(db)
    write_public_cache(db, KEY_HUMANOID_REPORT, report)
    stats["humanoid_robots"] = (report.get("report") or {}).get("total_robots", 0)

    logger.info("Public surface caches refreshed: %s", stats)
    return stats


def hydrate_public_surface_caches() -> None:
    """Load durable caches into in-process L1 — no DB rebuild on startup."""
    from app.api.humanoid_benchmark import set_humanoid_report_mem_cache
    from app.api.leads import hydrate_leads_public_caches
    from app.api.newsletter import hydrate_newsletter_mem_cache

    hydrated = 0

    newsletter = read_public_cache(NEWSLETTER_PIPELINE_CACHE_KEY)
    if newsletter and (newsletter.get("topStories") or []):
        hydrate_newsletter_mem_cache(newsletter)
        hydrated += 1
    else:
        from app.services.newsletter_library import load_library_latest, load_seed_edition
        from app.api.newsletter import hydrate_newsletter_mem_cache as _hydrate_nl

        library = load_library_latest()
        if library and (library.get("topStories") or []):
            _hydrate_nl(library)
            hydrated += 1
        else:
            seed = load_seed_edition()
            if seed:
                _hydrate_nl(seed)
                hydrated += 1

    homepage = read_public_cache(KEY_HOMEPAGE)
    if homepage:
        hydrate_leads_public_caches(homepage=homepage)
        hydrated += 1

    for exclude_junk, key in (
        (True, KEY_SUMMARY_EXCLUDE_JUNK),
        (False, KEY_SUMMARY_INCLUDE_JUNK),
    ):
        summary = read_public_cache(key)
        if summary:
            hydrate_leads_public_caches(summary=summary, exclude_junk=exclude_junk)
            hydrated += 1

    for limit, tier, key in (
        (50, None, KEY_LEADS_50),
        (18, None, KEY_LEADS_18),
        (12, "HOT", KEY_LEADS_HOT_12),
    ):
        leads = read_public_cache(key)
        if leads:
            hydrate_leads_public_caches(leads=leads, limit=limit, tier=tier)
            hydrated += 1

    report = read_public_cache(KEY_HUMANOID_REPORT)
    if report:
        set_humanoid_report_mem_cache(report)
        hydrated += 1

    logger.info("Public surface L1 hydrated from durable cache (%d surfaces)", hydrated)
