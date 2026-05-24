"""Persist admin dashboard snapshots in pipeline_cache_store (shared across Fly instances)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.services.pipeline_cache_store import cache_delete, cache_read_safe, cache_write

logger = logging.getLogger(__name__)

ADMIN_SNAPSHOT_KEY = "admin_snapshot_v1"
_FRESH_TTL_MINUTES = 24 * 60


def read_admin_snapshot(*, stale_ok: bool = True) -> Optional[dict[str, Any]]:
    try:
        payload = cache_read_safe(ADMIN_SNAPSHOT_KEY, stale_ok=stale_ok, timeout_sec=8.0)
        return payload if isinstance(payload, dict) else None
    except Exception as exc:
        logger.debug("admin snapshot read failed: %s", exc)
        return None


def write_admin_snapshot(data: dict[str, Any]) -> None:
    try:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            cache_write(db, ADMIN_SNAPSHOT_KEY, data, ttl_minutes=_FRESH_TTL_MINUTES)
        finally:
            db.close()
    except Exception as exc:
        logger.warning("admin snapshot write failed: %s", exc)


def invalidate_admin_snapshot() -> None:
    try:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            cache_delete(db, ADMIN_SNAPSHOT_KEY)
        finally:
            db.close()
    except Exception as exc:
        logger.debug("admin snapshot invalidate failed: %s", exc)
