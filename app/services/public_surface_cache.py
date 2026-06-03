"""
Pre-built public page caches — background refresh every 2 hours, read-only on GET.

Policy:
  • GET handlers never run heavy DB/OpenAI work on the request path.
  • Durable Postgres cache (pipeline_cache_store) + in-process L1 always serve first.
  • Background workers refresh all pipeline/newsletter surfaces on a fixed interval
    and on deploy; stale payloads stay served while refresh runs.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.newsletter_service import NEWSLETTER_PIPELINE_CACHE_KEY
from app.services.pipeline_cache_store import cache_read_safe, cache_write

logger = logging.getLogger(__name__)

# Cache TTL and refresh cadence (default: 2 hours).
PUBLIC_CACHE_TTL_MINUTES = int(os.getenv("PUBLIC_CACHE_TTL_MINUTES", str(2 * 60)))
PUBLIC_CACHE_REFRESH_INTERVAL_SEC = int(
    os.getenv("PUBLIC_CACHE_REFRESH_INTERVAL_SEC", str(2 * 60 * 60))
)
# Start a background rebuild when the last successful refresh is older than this.
PUBLIC_CACHE_REVALIDATE_SEC = int(
    os.getenv(
        "PUBLIC_CACHE_REVALIDATE_SEC",
        str(max(PUBLIC_CACHE_REFRESH_INTERVAL_SEC - 300, PUBLIC_CACHE_REFRESH_INTERVAL_SEC * 9 // 10)),
    )
)

from app.services.content_surfaces import (
    KEY_HOMEPAGE,
    KEY_HUMANOID_BENCHMARK_REPORT,
    KEY_HUMANOID_INTELLIGENCE,
    KEY_HUMANOID_INTELLIGENCE_PDF,
    KEY_LEADS_18,
    KEY_LEADS_50,
    KEY_LEADS_HOT_12,
    KEY_SUMMARY_EXCLUDE_JUNK,
    KEY_SUMMARY_INCLUDE_JUNK,
    refresh_all_content_surfaces,
    refresh_intelligence_surface,
)

KEY_HUMANOID_REPORT = KEY_HUMANOID_BENCHMARK_REPORT  # backwards compatible alias

_refresh_lock = threading.Lock()
_refresh_in_progress = False
_last_refresh_monotonic: float = 0.0
_loop_started = False


def read_public_cache(cache_key: str, *, stale_ok: bool = True) -> Optional[Any]:
    return cache_read_safe(cache_key, stale_ok=stale_ok, timeout_sec=8.0)


def write_public_cache(db: Session, cache_key: str, data: Any) -> None:
    cache_write(db, cache_key, data, ttl_minutes=PUBLIC_CACHE_TTL_MINUTES)


def refresh_pipeline_surface_caches(db: Session) -> dict[str, Any]:
    """Pipeline/homepage/summary/leads/humanoid — runs every 2 hours."""
    from app.api.humanoid_benchmark import build_humanoid_report_payload
    from app.api.leads import (
        _build_homepage_payload,
        _compute_pipeline_summary,
        build_public_leads_list,
    )

    stats: dict[str, Any] = {}

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

    logger.info("Pipeline surface caches refreshed: %s", stats)
    return stats


def refresh_social_posts_surface_cache(db: Session) -> dict[str, Any]:
    """Content Studio — daily social queue (cached 4h in pipeline_cache_store)."""
    from app.services.social_posts_service import refresh_social_posts_cache

    stats = refresh_social_posts_cache(db)
    logger.info("Social posts surface cache refreshed: %s", stats)
    return stats


def refresh_newsletter_surface_cache(db: Session, *, force: bool = False) -> dict[str, Any]:
    """Newsletter edition — incremental unless force=True (morning full rebuild)."""
    from app.services.newsletter_library import build_daily_newsletter_edition
    from app.services.newsletter_service import write_cached_edition

    edition = build_daily_newsletter_edition(
        db,
        limit=15,
        force=force,
        skip_openai_brief=not force,
    )
    write_cached_edition(edition, db)
    write_public_cache(db, NEWSLETTER_PIPELINE_CACHE_KEY, edition)
    meta = edition.get("_meta") or {}
    stats = {
        "newsletter_stories": len(edition.get("topStories") or []),
        "newsletter_update_mode": meta.get("update_mode"),
    }
    logger.info("Newsletter surface cache refreshed: %s", stats)
    return stats


def refresh_all_public_surface_caches(db: Session) -> dict[str, Any]:
    """Full rebuild — all registered content surfaces (morning job / manual regen)."""
    return refresh_all_content_surfaces(db, newsletter_force=True)


def hydrate_public_surface_caches() -> None:
    """Load durable caches into in-process L1 — no DB rebuild."""
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

        library = load_library_latest()
        if library and (library.get("topStories") or []):
            hydrate_newsletter_mem_cache(library)
            hydrated += 1
        else:
            seed = load_seed_edition()
            if seed:
                hydrate_newsletter_mem_cache(seed)
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


def _run_refresh(*, force: bool = False, pipeline_only: bool = False, include_newsletter: bool = True) -> None:
    global _refresh_in_progress, _last_refresh_monotonic

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        if pipeline_only:
            refresh_pipeline_surface_caches(db)
        elif force:
            refresh_all_public_surface_caches(db)
        else:
            refresh_pipeline_surface_caches(db)
            if include_newsletter:
                refresh_newsletter_surface_cache(db, force=False)
            try:
                refresh_social_posts_surface_cache(db)
            except Exception as exc:
                logger.warning("Social posts refresh skipped: %s", exc)
            try:
                refresh_intelligence_surface(db)
            except Exception as exc:
                logger.warning("Intelligence surface refresh skipped: %s", exc)
        hydrate_public_surface_caches()
        _last_refresh_monotonic = time.monotonic()
    except Exception as exc:
        logger.warning("Public surface background refresh failed: %s", exc)
    finally:
        db.close()
        with _refresh_lock:
            _refresh_in_progress = False


def schedule_public_cache_refresh(
    *,
    force: bool = False,
    pipeline_only: bool = False,
    include_newsletter: bool = True,
    reason: str = "",
) -> None:
    """Single-flight background cache rebuild — never blocks HTTP."""
    global _refresh_in_progress

    with _refresh_lock:
        if _refresh_in_progress and not force:
            return
        _refresh_in_progress = True

    label = reason or ("force" if force else "scheduled")

    def _job() -> None:
        logger.info("Public surface cache refresh started (%s)", label)
        _run_refresh(force=force, pipeline_only=pipeline_only, include_newsletter=include_newsletter)

    threading.Thread(
        target=_job,
        daemon=True,
        name=f"public-cache-refresh-{label[:24]}",
    ).start()


def maybe_schedule_public_cache_refresh(*, force: bool = False) -> None:
    """Called from GET handlers — refresh in background when cache age exceeds revalidate window."""
    if force:
        schedule_public_cache_refresh(force=True, reason="forced")
        return
    age = time.monotonic() - _last_refresh_monotonic
    if _last_refresh_monotonic == 0.0 or age >= PUBLIC_CACHE_REVALIDATE_SEC:
        schedule_public_cache_refresh(reason="stale_revalidate")


def start_public_cache_refresh_loop() -> None:
    """In-app 2-hour refresh loop (Fly web machine when Celery Beat is absent)."""
    global _loop_started
    if _loop_started:
        return
    _loop_started = True

    def _loop() -> None:
        # Initial refresh shortly after deploy so L1/durable stay warm without blocking requests.
        time.sleep(int(os.getenv("PUBLIC_CACHE_STARTUP_DELAY_SEC", "45")))
        schedule_public_cache_refresh(force=False, reason="startup")
        while True:
            time.sleep(PUBLIC_CACHE_REFRESH_INTERVAL_SEC)
            schedule_public_cache_refresh(reason="interval")

    threading.Thread(target=_loop, daemon=True, name="public-cache-refresh-loop").start()
    logger.info(
        "Public cache refresh loop started (every %ds, TTL %dm)",
        PUBLIC_CACHE_REFRESH_INTERVAL_SEC,
        PUBLIC_CACHE_TTL_MINUTES,
    )
