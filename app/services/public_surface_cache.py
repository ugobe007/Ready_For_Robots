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
from datetime import datetime, timezone
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

PIPELINE_FEED_MIN_LEADS = int(os.getenv("PIPELINE_FEED_MIN_LEADS", "24"))

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
# Deploy asks the worker to rebuild. The web process only writes this row.
PIPELINE_REFRESH_REQUEST_KEY = "pipeline:refresh_request"
PIPELINE_REFRESH_HANDLED_KEY = "pipeline:refresh_handled"

_refresh_lock = threading.Lock()
_refresh_in_progress = False
_last_refresh_monotonic: float = 0.0
_loop_started = False
_request_loop_started = False


def read_public_cache(cache_key: str, *, stale_ok: bool = True) -> Optional[Any]:
    return cache_read_safe(cache_key, stale_ok=stale_ok, timeout_sec=3.0)


def read_public_caches_many(cache_keys: list[str], *, stale_ok: bool = True) -> dict[str, Any]:
    """Single round-trip read for homepage/pipeline fallbacks."""
    from app.services.pipeline_cache_store import cache_read_many_safe

    return cache_read_many_safe(cache_keys, stale_ok=stale_ok, timeout_sec=3.0)


def write_public_cache(db: Session, cache_key: str, data: Any) -> None:
    cache_write(db, cache_key, data, ttl_minutes=PUBLIC_CACHE_TTL_MINUTES)


def pipeline_feed_is_stale(feed: Optional[dict], *, ttl_minutes: Optional[int] = None) -> bool:
    """True when durable pipeline feed is missing built_at or older than TTL."""
    if not feed or not isinstance(feed, dict) or not (feed.get("leads") or []):
        return True
    built_at = feed.get("built_at")
    if not built_at:
        return True
    try:
        ts = datetime.fromisoformat(str(built_at).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return True
    ttl = ttl_minutes if ttl_minutes is not None else PUBLIC_CACHE_TTL_MINUTES
    age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
    return age_min > ttl


def refresh_pipeline_surface_caches(db: Session, *, include_humanoid_report: bool = True) -> dict[str, Any]:
    """Pipeline/homepage/summary/leads/humanoid — default every 30 minutes with lead rotation."""
    from datetime import datetime, timezone

    from app.api.humanoid_benchmark import build_humanoid_report_payload
    from app.api.leads import (
        PIPELINE_FEED_LIMIT,
        _build_homepage_payload,
        _compute_pipeline_summary,
        _current_rotation_slot,
        _summary_for_homepage,
        build_industry_search_leads_list,
        build_public_leads_list,
        build_public_pipeline_feed,
        hydrate_pipeline_feed_cache,
    )
    from app.services.content_surfaces import (
        KEY_CAL_LEAD_DROPS,
        KEY_PIPELINE_FEED,
        INDUSTRY_SEARCH_CACHE_QUERIES,
    )
    from app.services.phelan_lead_drops import build_phelan_lead_drops_preview

    from app.services.homepage_rotation import homepage_rotation_day, homepage_rotation_slot

    stats: dict[str, Any] = {}
    rotation_slot = _current_rotation_slot()
    homepage_day = homepage_rotation_day()
    homepage_slot = homepage_rotation_slot()

    homepage = _build_homepage_payload(db, resolve_llm_urls=False)
    write_public_cache(db, KEY_HOMEPAGE, homepage)
    stats["homepage_hot_leads"] = len(homepage.get("hotLeads") or [])
    stats["rotation_slot"] = rotation_slot
    stats["homepage_rotation_day"] = str(homepage_day)
    stats["homepage_rotation_slot"] = homepage_slot

    summary_exclude = _compute_pipeline_summary(db, True)
    write_public_cache(db, KEY_SUMMARY_EXCLUDE_JUNK, summary_exclude)
    write_public_cache(db, KEY_SUMMARY_INCLUDE_JUNK, _compute_pipeline_summary(db, False))

    leads_cache: dict[tuple[int, str], list] = {}
    for limit, tier, key in (
        (50, None, KEY_LEADS_50),
        (18, None, KEY_LEADS_18),
        (12, "HOT", KEY_LEADS_HOT_12),
    ):
        leads = build_public_leads_list(db, limit=limit, tier=tier)
        write_public_cache(db, key, leads)
        leads_cache[(limit, tier or "all")] = leads
        stats[f"leads_{limit}_{tier or 'all'}"] = len(leads)

    for search_q in INDUSTRY_SEARCH_CACHE_QUERIES:
        from app.api.leads import _industry_search_cache_key

        search_leads = build_industry_search_leads_list(db, search_q, limit=50)
        write_public_cache(db, _industry_search_cache_key(search_q), search_leads)
        stats[f"leads_search_{search_q.replace(' ', '_')}"] = len(search_leads)

    cal_drops = build_phelan_lead_drops_preview(db, limit=3)
    write_public_cache(db, KEY_CAL_LEAD_DROPS, cal_drops)
    stats["phelan_lead_drops"] = cal_drops.get("count", 0)

    try:
        pipeline_leads = build_public_pipeline_feed(db, limit=PIPELINE_FEED_LIMIT)
        stats["pipeline_feed_source"] = "fresh"

        min_target = min(max(int(PIPELINE_FEED_MIN_LEADS), 0), PIPELINE_FEED_LIMIT)
        if len(pipeline_leads) < min_target:
            fallback = (
                leads_cache.get((50, "all"))
                or leads_cache.get((18, "all"))
                or leads_cache.get((12, "HOT"))
                or []
            )
            existing_ids = {
                int(row.get("id"))
                for row in pipeline_leads
                if isinstance(row, dict) and row.get("id") is not None
            }
            for row in fallback:
                if not isinstance(row, dict):
                    continue
                rid = row.get("id")
                if rid is None:
                    continue
                try:
                    rid_i = int(rid)
                except (TypeError, ValueError):
                    continue
                if rid_i in existing_ids:
                    continue
                pipeline_leads.append(row)
                existing_ids.add(rid_i)
                if len(pipeline_leads) >= min_target:
                    break
            stats["pipeline_feed_backfilled_to"] = len(pipeline_leads)
    except Exception as exc:
        logger.warning("Pipeline feed build failed; using warmed lead-list fallback: %s", exc)
        fallback = (
            leads_cache.get((50, "all"))
            or leads_cache.get((18, "all"))
            or leads_cache.get((12, "HOT"))
            or []
        )
        pipeline_leads = list(fallback[:PIPELINE_FEED_LIMIT])
        stats["pipeline_feed_source"] = "fallback_lead_list"

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

    if include_humanoid_report:
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
        skip_openai_brief=True,
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


_PIPELINE_REBUILD_LOCK = 440355


def _try_pipeline_rebuild_lock(db) -> bool:
    """One rebuild across worker machines. SQLite tests do not lock."""
    bind = db.get_bind()
    if getattr(bind.dialect, "name", "") != "postgresql":
        return True
    from sqlalchemy import text

    return bool(db.execute(text(f"SELECT pg_try_advisory_lock({_PIPELINE_REBUILD_LOCK})")).scalar())


def _run_refresh(*, force: bool = False, pipeline_only: bool = False, include_newsletter: bool = True) -> bool | None:
    global _refresh_in_progress, _last_refresh_monotonic

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        if not _try_pipeline_rebuild_lock(db):
            logger.info("Pipeline rebuild already running on another worker; skipping")
            return None
        if pipeline_only:
            refresh_pipeline_surface_caches(db, include_humanoid_report=False)
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
        return True
    except Exception as exc:
        logger.warning("Public surface background refresh failed: %s", exc)
        return False
    finally:
        db.close()
        with _refresh_lock:
            _refresh_in_progress = False


def schedule_robots_page_cache_refresh(*, reason: str = "") -> None:
    """Background rebuild of /robots snapshots — never blocks HTTP."""
    from app.runtime_role import is_web_process

    if is_web_process():
        logger.debug("Robots cache refresh skipped on web process (%s)", reason or "scheduled")
        return

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
    requested_at: str = "",
) -> bool:
    """Single-flight background cache rebuild — never blocks HTTP.

    Returns True when a rebuild thread was started. The web process never starts one.
    """
    from app.runtime_role import is_web_process

    if is_web_process():
        logger.debug("Cache refresh skipped on web process (%s)", reason or "scheduled")
        return False

    global _refresh_in_progress

    with _refresh_lock:
        if _refresh_in_progress and not force:
            return False
        _refresh_in_progress = True

    label = reason or ("force" if force else "scheduled")

    def _job() -> None:
        logger.info("Public surface cache refresh started (%s)", label)
        ok = _run_refresh(force=force, pipeline_only=pipeline_only, include_newsletter=include_newsletter)
        if not requested_at or ok is None:
            return
        if ok:
            _write_pipeline_refresh_handled(requested_at)
        else:
            release_pipeline_refresh_claim(requested_at)

    threading.Thread(
        target=_job,
        daemon=True,
        name=f"public-cache-refresh-{label[:24]}",
    ).start()
    return True


def request_worker_pipeline_refresh(db: Session) -> dict[str, Any]:
    """Ask the worker to rebuild pipeline caches. Does not run the rebuild."""
    requested_at = datetime.now(timezone.utc).isoformat()
    write_public_cache(
        db,
        PIPELINE_REFRESH_REQUEST_KEY,
        {"requested_at": requested_at},
    )
    return {"requested_at": requested_at}


def claim_pipeline_refresh_request(requested_at: str) -> bool:
    """One worker claims the request. The others do not start a second rebuild."""
    from sqlalchemy import text

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        claimed = db.execute(
            text(
                """
                UPDATE pipeline_cache_store
                SET data = jsonb_set(data, '{claimed_at}', to_jsonb(now()::text), true)
                WHERE cache_key = :key
                  AND data->>'requested_at' = :requested_at
                  AND COALESCE(data->>'claimed_at', '') = ''
                RETURNING cache_key
                """
            ),
            {"key": PIPELINE_REFRESH_REQUEST_KEY, "requested_at": requested_at},
        ).first()
        db.commit()
        return claimed is not None
    except Exception as exc:
        logger.warning("Pipeline refresh claim failed: %s", exc)
        db.rollback()
        return False
    finally:
        db.close()


def release_pipeline_refresh_claim(requested_at: str) -> None:
    """Clear this worker's claim when the rebuild did not start, so it is retried."""
    from sqlalchemy import text

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(
            text(
                """
                UPDATE pipeline_cache_store
                SET data = data - 'claimed_at'
                WHERE cache_key = :key
                  AND data->>'requested_at' = :requested_at
                """
            ),
            {"key": PIPELINE_REFRESH_REQUEST_KEY, "requested_at": requested_at},
        )
        db.commit()
    except Exception as exc:
        logger.warning("Pipeline refresh claim release failed: %s", exc)
        db.rollback()
    finally:
        db.close()


def consume_pipeline_refresh_request(handled_at: str) -> str:
    """Start one worker rebuild when a newer request is waiting.

    Returns the timestamp now being handled. An in-flight rebuild leaves the
    request pending so the next check runs it after this one finishes.
    A second worker sees the claim and does not start another rebuild.
    """
    if _refresh_in_progress:
        return handled_at
    payload = read_public_cache(PIPELINE_REFRESH_REQUEST_KEY, stale_ok=True)
    if not isinstance(payload, dict):
        return handled_at
    requested_at = str(payload.get("requested_at") or "")
    if not requested_at or requested_at == handled_at:
        return handled_at
    if payload.get("claimed_at"):
        if _claim_belongs_to_a_live_rebuild():
            return requested_at
        release_pipeline_refresh_claim(requested_at)
    if not claim_pipeline_refresh_request(requested_at):
        return handled_at
    started = schedule_public_cache_refresh(
        pipeline_only=True,
        reason="worker_request",
        requested_at=requested_at,
    )
    if not started:
        release_pipeline_refresh_claim(requested_at)
        return handled_at
    return requested_at


def _read_pipeline_refresh_handled() -> str:
    payload = read_public_cache(PIPELINE_REFRESH_HANDLED_KEY, stale_ok=True)
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("handled_at") or "")


def _claim_belongs_to_a_live_rebuild() -> bool:
    """True when some worker holds the rebuild lock. A leftover claim is not live."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        if not _try_pipeline_rebuild_lock(db):
            return True
        return False
    except Exception as exc:
        logger.warning("Pipeline rebuild lock check failed: %s", exc)
        return True
    finally:
        db.close()


def _write_pipeline_refresh_handled(handled_at: str) -> None:
    """Persist a finished request so a worker restart does not replay it."""
    from app.database import SessionLocal

    try:
        db = SessionLocal()
    except Exception as exc:
        logger.warning("Pipeline refresh handled marker skipped: %s", exc)
        return
    try:
        write_public_cache(db, PIPELINE_REFRESH_HANDLED_KEY, {"handled_at": handled_at})
    finally:
        db.close()


def start_pipeline_refresh_request_loop() -> None:
    """Worker-only poll for deploy refresh requests. Never runs on the web process."""
    from app.runtime_role import is_worker_process

    global _request_loop_started
    if not is_worker_process() or _request_loop_started:
        return
    _request_loop_started = True

    def _loop() -> None:
        try:
            handled = _read_pipeline_refresh_handled()
        except Exception as exc:
            logger.warning("Pipeline refresh handled marker read failed: %s", exc)
            handled = ""
        while True:
            time.sleep(15)
            try:
                handled = consume_pipeline_refresh_request(handled)
            except Exception as exc:
                logger.warning("Pipeline refresh request check failed: %s", exc)

    threading.Thread(target=_loop, daemon=True, name="pipeline-refresh-request").start()
    logger.info("Worker pipeline refresh request loop started")


def maybe_schedule_public_cache_refresh(*, force: bool = False) -> None:
    """Called from GET handlers — refresh in background when cache age exceeds revalidate window."""
    from app.runtime_role import is_web_process

    if is_web_process():
        return

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
        if isinstance(feed, dict) and (feed.get("leads") or []) and not pipeline_feed_is_stale(feed):
            global _last_refresh_monotonic
            _last_refresh_monotonic = time.monotonic()
            logger.info(
                "Startup pipeline refresh skipped — durable feed warm (%d leads, built_at=%s)",
                len(feed.get("leads") or []),
                feed.get("built_at"),
            )
        else:
            if isinstance(feed, dict) and feed.get("built_at"):
                logger.info(
                    "Startup pipeline refresh scheduled — stale feed built_at=%s",
                    feed.get("built_at"),
                )
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
