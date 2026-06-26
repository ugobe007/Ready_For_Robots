"""Build and serve admin dashboard snapshot sections."""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.admin_snapshot_cache import (
    invalidate_admin_snapshot,
    read_admin_snapshot,
    write_admin_snapshot,
)
from app.db_timeout import run_db

logger = logging.getLogger(__name__)

SNAPSHOT_VERSION = 1
SECTION_NAMES = (
    "daily_brief",
    "cal",
    "stats",
    "scout",
    "user_stats",
    "workflow",
    "activity",
    "users",
    "targets",
    "analytics",
)

# Per-section staleness before a ?refresh=1 rebuild is worthwhile.
# Lightweight sections — build synchronously on first miss instead of 503 + empty UI.
_FAST_SYNC_SECTIONS = frozenset({"stats", "targets", "user_stats", "analytics"})

_SECTION_TTL_SEC: dict[str, int] = {
    "cal": 120,
    "daily_brief": 300,
    "stats": 600,
    "scout": 180,
    "user_stats": 600,
    "workflow": 300,
    "activity": 300,
    "users": 600,
    "targets": 900,
    "analytics": 600,
}

_rebuild_lock = threading.Lock()
_rebuilding: set[str] = set()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _section_age_sec(updated_at: Optional[str]) -> float:
    dt = _parse_iso(updated_at)
    if dt is None:
        return float("inf")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).total_seconds()


def _empty_snapshot() -> dict[str, Any]:
    return {"version": SNAPSHOT_VERSION, "built_at": _utcnow_iso(), "sections": {}}


def _merge_section(snapshot: dict[str, Any], name: str, data: Any) -> dict[str, Any]:
    sections = dict(snapshot.get("sections") or {})
    sections[name] = {"updated_at": _utcnow_iso(), "data": data}
    out = {
        "version": SNAPSHOT_VERSION,
        "built_at": _utcnow_iso(),
        "sections": sections,
    }
    return out


def _build_section(name: str, db: Session, *, analytics_range: str = "30d") -> Any:
    if name == "daily_brief":
        from app.api.admin import daily_brief

        return daily_brief(db=db)

    if name == "stats":
        from app.api.admin import get_stats

        return get_stats(db=db)

    if name == "workflow":
        from app.api.admin import workflow_actions

        return workflow_actions(limit=40, db=db)

    if name == "targets":
        from app.api.admin import list_scrape_targets

        return list_scrape_targets()

    if name == "user_stats":
        from app.api.admin_users import get_user_stats

        return get_user_stats(db=db)

    if name == "users":
        from app.api.admin_users import list_users

        return list_users(db=db)

    if name == "activity":
        from app.api.admin_users import list_recent_activity

        return list_recent_activity(limit=40, db=db)

    if name == "cal":
        from app.api.admin_extended import _build_cal_draft_status_payload

        return _build_cal_draft_status_payload(
            db,
            include_draft_bodies=False,
            include_prospects=True,
            prospect_limit=120,
        )

    if name == "scout":
        from app.api.admin_extended import scout_bulk_status

        admin_user = {"uid": "00000000-0000-0000-0000-000000000000", "email": "snapshot@system"}
        return scout_bulk_status(db=db, user=admin_user)

    if name == "analytics":
        from app.api.analytics import get_analytics

        return asyncio.run(get_analytics(range=analytics_range))

    raise ValueError(f"Unknown admin snapshot section: {name}")


def get_snapshot(*, stale_ok: bool = True) -> dict[str, Any]:
    cached = read_admin_snapshot(stale_ok=stale_ok)
    return cached if cached else _empty_snapshot()


def snapshot_meta(snapshot: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    snap = snapshot or get_snapshot(stale_ok=True)
    sections = snap.get("sections") or {}
    return {
        "version": snap.get("version", SNAPSHOT_VERSION),
        "built_at": snap.get("built_at"),
        "sections": {
            name: (sections.get(name) or {}).get("updated_at")
            for name in SECTION_NAMES
        },
    }


def section_is_fresh(name: str, updated_at: Optional[str]) -> bool:
    ttl = _SECTION_TTL_SEC.get(name, 300)
    return _section_age_sec(updated_at) < ttl


def get_section_payload(
    name: str,
    *,
    since: Optional[str] = None,
    refresh: bool = False,
    db: Session,
    analytics_range: str = "30d",
) -> tuple[int, dict[str, Any]]:
    """
    Return (status_code, body).
    Serves cached section data immediately (even if TTL-expired).
    Rebuilds synchronously only when refresh=True.
    """
    if name not in SECTION_NAMES:
        return 404, {"detail": f"Unknown section: {name}"}

    snapshot = get_snapshot(stale_ok=True)
    sections = snapshot.get("sections") or {}
    entry = sections.get(name)
    updated_at = entry.get("updated_at") if entry else None
    is_fresh = section_is_fresh(name, updated_at)

    if entry and since and updated_at and not refresh:
        client_dt = _parse_iso(since)
        server_dt = _parse_iso(updated_at)
        if client_dt and server_dt and server_dt <= client_dt:
            return 304, {}

    if refresh:
        try:
            def _do_build() -> Any:
                from app.database import SessionLocal

                with SessionLocal() as build_db:
                    return _build_section(name, build_db, analytics_range=analytics_range)

            data = run_db(_do_build, timeout_sec=30, label=f"snapshot/{name}")
            snapshot = _merge_section(snapshot, name, data)
            write_admin_snapshot(snapshot)
            entry = snapshot["sections"][name]
            is_fresh = True
        except TimeoutError as exc:
            logger.error("admin snapshot section rebuild timed out (%s)", name)
            if entry:
                return 200, {
                    "section": name,
                    "updated_at": entry["updated_at"],
                    "data": entry["data"],
                    "stale": True,
                }
            schedule_background_rebuild([name])
            return 503, {"detail": f"Section rebuild timed out: {name}"}
        except Exception as exc:
            logger.exception("admin snapshot section rebuild failed (%s): %s", name, exc)
            if entry:
                return 200, {
                    "section": name,
                    "updated_at": entry["updated_at"],
                    "data": entry["data"],
                    "stale": True,
                }
            schedule_background_rebuild([name])
            return 503, {"detail": f"Section rebuild failed: {name}"}
    elif entry is None:
        if name in _FAST_SYNC_SECTIONS:
            try:
                def _do_fast_build() -> Any:
                    from app.database import SessionLocal

                    with SessionLocal() as build_db:
                        return _build_section(name, build_db, analytics_range=analytics_range)

                data = run_db(_do_fast_build, timeout_sec=20, label=f"snapshot/{name}/fast")
                snapshot = _merge_section(snapshot, name, data)
                write_admin_snapshot(snapshot)
                entry = snapshot["sections"][name]
                is_fresh = True
            except Exception as exc:
                logger.warning("admin snapshot fast build failed (%s): %s", name, exc)
        if entry is None:
            schedule_background_rebuild([name])
            return 503, {"detail": f"Section not ready: {name}"}

    body: dict[str, Any] = {
        "section": name,
        "updated_at": entry["updated_at"],
        "data": entry["data"],
    }
    if not is_fresh:
        body["stale"] = True
        schedule_background_rebuild([name])
    return 200, body


def schedule_background_rebuild(section_names: Optional[list[str]] = None) -> None:
    """Rebuild snapshot sections one at a time in a daemon thread (no request storm)."""
    names = section_names or list(SECTION_NAMES)

    def _run() -> None:
        with _rebuild_lock:
            for name in names:
                if name in _rebuilding:
                    continue
                _rebuilding.add(name)
                try:
                    def _bg_build() -> None:
                        from app.database import SessionLocal

                        with SessionLocal() as bg_db:
                            get_section_payload(name, refresh=True, db=bg_db)

                    run_db(_bg_build, timeout_sec=45, label=f"snapshot-bg/{name}")
                except Exception as exc:
                    logger.warning("background admin snapshot rebuild failed (%s): %s", name, exc)
                finally:
                    _rebuilding.discard(name)

    threading.Thread(target=_run, daemon=True, name="admin-snapshot-rebuild").start()


def touch_invalidate() -> None:
    invalidate_admin_snapshot()


def warm_admin_snapshot_cache() -> None:
    """Rebuild core admin sections after boot — stats first so the dashboard is never empty."""
    import time

    def _delayed() -> None:
        time.sleep(8)
        snap = get_snapshot(stale_ok=True)
        stats_entry = (snap.get("sections") or {}).get("stats")
        stats_data = (stats_entry or {}).get("data") or {}
        totals = stats_data.get("totals") or {}
        if not stats_entry or int(totals.get("companies") or 0) == 0:
            invalidate_admin_snapshot()
        schedule_background_rebuild(["stats", "daily_brief", "cal"])

    threading.Thread(target=_delayed, daemon=True, name="admin-snapshot-warm-delayed").start()
