"""
Pre-built public page caches — background refresh every 30 minutes (configurable), read-only on GET.

Policy:
  • GET handlers never run heavy DB/OpenAI work on the request path.
  • Durable Postgres cache (pipeline_cache_store) + in-process L1 always serve first.
  • Background workers refresh pipeline surfaces on a fixed interval (default 30m),
    rotating which sales leads appear in each build; stale payloads serve during rebuild.
  • Intelligence scraper completion also schedules a pipeline-only refresh.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.newsletter_service import NEWSLETTER_API_SNAPSHOT_KEY, NEWSLETTER_PIPELINE_CACHE_KEY
from app.services.pipeline_cache_store import cache_read_safe, cache_write

logger = logging.getLogger(__name__)

from app.services.pipeline_cache_policy import (
    PIPELINE_LEADS_ROTATION_SEC,
    PUBLIC_CACHE_REFRESH_INTERVAL_SEC,
    PUBLIC_CACHE_REVALIDATE_SEC,
    PUBLIC_CACHE_TTL_MINUTES,
)

from app.services.content_surfaces import (
    KEY_HOMEPAGE,
    KEY_HUMANOID_BENCHMARK_REPORT,
    KEY_HUMANOID_INTELLIGENCE,
    KEY_HUMANOID_INTELLIGENCE_PDF,
    KEY_LEADS_18,
    KEY_LEADS_50,
    KEY_LEADS_HOT_12,
    KEY_PIPELINE_FEED,
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
    return cache_read_safe(cache_key, stale_ok=stale_ok, timeout_sec=3.0)


def read_public_caches_many(cache_keys: list[str], *, stale_ok: bool = True) -> dict[str, Any]:
    """Single round-trip read for homepage/pipeline fallbacks."""
    from app.services.pipeline_cache_store import cache_read_many_safe

    return cache_read_many_safe(cache_keys, stale_ok=stale_ok, timeout_sec=3.0)


def write_public_cache(db: Session, cache_key: str, data: Any) -> None:
    cache_write(db, cache_key, data, ttl_minutes=PUBLIC_CACHE_TTL_MINUTES)


def refresh_pipeline_surface_caches(db: Session) -> dict[str, Any]:
    """Pipeline/homepage/summary/leads/humanoid — default every 30 minutes with lead rotation."""
    from datetime import datetime, timezone

    from app.api.humanoid_benchmark import build_humanoid_report_payload
    from app.api.leads import (
        PIPELINE_FEED_LIMIT,
        _build_homepage_payload,
        _compute_pipeline_summary,
        _current_rotation_slot,
        _summary_for_homepage,
        build_public_leads_list,
        build_public_pipeline_feed,
        hydrate_pipeline_feed_cache,
    )
    from app.services.content_surfaces import KEY_PIPELINE_FEED

    from app.services.homepage_rotation import homepage_rotation_day, homepage_rotation_slot

    stats: dict[str, Any] = {}
    rotation_slot = _current_rotation_slot()
    homepage_day = homepage_rotation_day()
    homepage_slot = homepage_rotation_slot()

    homepage = _build_homepage_payload(db)
    write_public_cache(db, KEY_HOMEPAGE, homepage)
    stats["homepage_hot_leads"] = len(homepage.get("hotLeads") or [])
    stats["rotation_slot"] = rotation_slot
    stats["homepage_rotation_day"] = str(homepage_day)
    stats["homepage_rotation_slot"] = homepage_slot

    summary_exclude = _compute_pipeline_summary(db, True)
    write_public_cache(db, KEY_SUMMARY_EXCLUDE_JUNK, summary_exclude)
    write_public_cache(db, KEY_SUMMARY_INCLUDE_JUNK, _compute_pipeline_summary(db, False))

    for limit, tier, key in (
        (50, None, KEY_LEADS_50),
        (18, None, KEY_LEADS_18),
        (12, "HOT", KEY_LEADS_HOT_12),
    ):
        leads = build_public_leads_list(db, limit=limit, tier=tier)
        write_public_cache(db, key, leads)
        stats[f"leads_{limit}_{tier or 'all'}"] = len(leads)

    pipeline_leads = build_public_pipeline_feed(db, limit=PIPELINE_FEED_LIMIT)
    pipeline_feed = {
        "leads": pipeline_leads,
        "summary": _summary_for_homepage(summary_exclude),
        "summary_raw": summary_exclude,
        "rotation_slot": rotation_slot,
        "rotation_period_sec": PIPELINE_LEADS_ROTATION_SEC,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    write_public_cache(db, KEY_PIPELINE_FEED, pipeline_feed)
    hydrate_pipeline_feed_cache(pipeline_feed)
    stats["pipeline_feed_leads"] = len(pipeline_leads)

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


def refresh_robots_page_surface_caches(db: Session) -> dict[str, Any]:
    """/robots page — humanoid list + HEIR intelligence + benchmark summary (3h TTL)."""
    from app.api.humanoid_benchmark import build_humanoid_report_payload, set_humanoid_report_mem_cache
    from app.services.content_surfaces import refresh_intelligence_surface
    from app.services.humanoid_robots_snapshot import publish_robots_list_snapshot

    stats = dict(publish_robots_list_snapshot(db))
    stats.update(refresh_intelligence_surface(db))
    from app.services.humanoid_robots_snapshot import ROBOTS_PAGE_CACHE_TTL_MINUTES
    from app.services.pipeline_cache_store import cache_write

    report = build_humanoid_report_payload(db)
    cache_write(db, KEY_HUMANOID_REPORT, report, ttl_minutes=ROBOTS_PAGE_CACHE_TTL_MINUTES)
    set_humanoid_report_mem_cache(report)
    stats["humanoid_report_robots"] = (report.get("report") or {}).get("total_robots", 0)
    logger.info("Robots page surface caches refreshed: %s", stats)
    return stats


def refresh_newsletter_surface_cache(db: Session, *, force: bool = False) -> dict[str, Any]:
    """Newsletter edition — incremental unless force=True (morning full rebuild)."""
    from app.services.newsletter_library import build_daily_newsletter_edition
    from app.services.newsletter_service import write_cached_edition
    from app.services.newsletter_snapshot import publish_api_snapshot

    edition = build_daily_newsletter_edition(
        db,
        limit=15,
        force=force,
        skip_openai_brief=not force,
    )
    write_cached_edition(edition, db)
    publish_api_snapshot(db, edition, limit=15)
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
    from app.services.newsletter_snapshot import (
        hydrate_newsletter_mem_cache,
        slim_edition_for_api,
    )

    hydrated = 0

    snapshot = read_public_cache(NEWSLETTER_API_SNAPSHOT_KEY)
    if snapshot and (snapshot.get("topStories") or []):
        hydrate_newsletter_mem_cache(snapshot)
        hydrated += 1
    else:
        newsletter = read_public_cache(NEWSLETTER_PIPELINE_CACHE_KEY)
        if newsletter and (newsletter.get("topStories") or []):
            hydrate_newsletter_mem_cache(slim_edition_for_api(newsletter, limit=15))
            hydrated += 1
        else:
            from app.services.newsletter_library import load_library_latest, load_seed_edition

            library = load_library_latest()
            if library and (library.get("topStories") or []):
                hydrate_newsletter_mem_cache(slim_edition_for_api(library, limit=15))
                hydrated += 1
            else:
                seed = load_seed_edition()
                if seed:
                    hydrate_newsletter_mem_cache(slim_edition_for_api(seed, limit=15))
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

    pipeline_feed = read_public_cache(KEY_PIPELINE_FEED)
    if pipeline_feed and isinstance(pipeline_feed, dict):
        from app.api.leads import hydrate_pipeline_feed_cache

        hydrate_pipeline_feed_cache(pipeline_feed)
        hydrated += 1

    report = read_public_cache(KEY_HUMANOID_REPORT)
    if report:
        set_humanoid_report_mem_cache(report)
        hydrated += 1

    from app.services.content_surfaces import KEY_HUMANOID_INTELLIGENCE, KEY_HUMANOID_ROBOTS_LIST
    from app.services.humanoid_robots_snapshot import (
        hydrate_intelligence_mem_cache,
        hydrate_robots_list_mem_cache,
    )

    robots_list = read_public_cache(KEY_HUMANOID_ROBOTS_LIST)
    if robots_list and (robots_list.get("robots") or []):
        hydrate_robots_list_mem_cache(robots_list)
        hydrated += 1

    intelligence = read_public_cache(KEY_HUMANOID_INTELLIGENCE)
    if intelligence and intelligence.get("report"):
        hydrate_intelligence_mem_cache(intelligence)
        hydrated += 1

    logger.info("Public surface L1 hydrated from durable cache (%d surfaces)", hydrated)
    global _last_refresh_monotonic
    if hydrated > 0:
        # Warm L1 exists — do not treat cache as cold on every GET during background rebuild.
        _last_refresh_monotonic = time.monotonic()


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
            if os.getenv("SKIP_SOCIAL_INTERVAL_REFRESH", "").strip().lower() not in ("1", "true", "yes"):
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


def schedule_robots_page_cache_refresh(*, reason: str = "") -> None:
    """Background rebuild of /robots snapshots — never blocks HTTP."""
    label = reason or "scheduled"

    def _job() -> None:
        from app.database import SessionLocal

        logger.info("Robots page cache refresh started (%s)", label)
        db = SessionLocal()
        try:
            refresh_robots_page_surface_caches(db)
            hydrate_public_surface_caches()
        except Exception as exc:
            logger.warning("Robots page cache refresh failed: %s", exc)
        finally:
            db.close()

    threading.Thread(
        target=_job,
        daemon=True,
        name=f"robots-cache-refresh-{label[:24]}",
    ).start()


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
        # Pipeline surfaces only — never stack newsletter/social/intelligence on user traffic.
        schedule_public_cache_refresh(pipeline_only=True, reason="stale_revalidate")


def start_public_cache_refresh_loop() -> None:
    """In-app pipeline refresh loop (default every 30 minutes on Fly)."""
    global _loop_started
    if _loop_started:
        return
    _loop_started = True

    def _loop() -> None:
        # Let health checks and read-only cache serves win first after deploy.
        delay = int(os.getenv("PUBLIC_CACHE_STARTUP_DELAY_SEC", "180"))
        time.sleep(delay)
        from app.services.content_surfaces import KEY_PIPELINE_FEED

        feed = read_public_cache(KEY_PIPELINE_FEED, stale_ok=True)
        if isinstance(feed, dict) and (feed.get("leads") or []):
            global _last_refresh_monotonic
            _last_refresh_monotonic = time.monotonic()
            logger.info(
                "Startup pipeline refresh skipped — durable feed warm (%d leads)",
                len(feed.get("leads") or []),
            )
        else:
            schedule_public_cache_refresh(pipeline_only=True, reason="startup")
        while True:
            time.sleep(PUBLIC_CACHE_REFRESH_INTERVAL_SEC)
            schedule_public_cache_refresh(pipeline_only=True, reason="interval")

    threading.Thread(target=_loop, daemon=True, name="public-cache-refresh-loop").start()
    logger.info(
        "Public cache refresh loop started (every %ds, TTL %dm)",
        PUBLIC_CACHE_REFRESH_INTERVAL_SEC,
        PUBLIC_CACHE_TTL_MINUTES,
    )
    start_homepage_daily_rotation_loop()


_homepage_daily_loop_started = False


def start_homepage_daily_rotation_loop() -> None:
    """Force a pipeline cache rebuild when the Pacific spotlight edition day rolls."""
    global _homepage_daily_loop_started
    if _homepage_daily_loop_started:
        return
    _homepage_daily_loop_started = True

    def _loop() -> None:
        from app.services.homepage_rotation import homepage_rotation_day

        time.sleep(90)
        last_day = None
        while True:
            try:
                today = homepage_rotation_day()
                if last_day is not None and today != last_day:
                    logger.info(
                        "Homepage spotlight edition day rolled %s → %s; refreshing caches",
                        last_day,
                        today,
                    )
                    schedule_public_cache_refresh(
                        force=True,
                        pipeline_only=True,
                        reason="homepage_daily_rotation",
                    )
                last_day = today
            except Exception as exc:
                logger.warning("Homepage daily rotation check failed: %s", exc)
            time.sleep(int(os.getenv("HOMEPAGE_DAILY_ROTATION_CHECK_SEC", "300")))

    threading.Thread(
        target=_loop,
        daemon=True,
        name="homepage-daily-rotation-loop",
    ).start()
    logger.info("Homepage daily rotation loop started (6am %s edition day)", os.getenv("HOMEPAGE_SPOTLIGHT_TZ", "America/Los_Angeles"))
