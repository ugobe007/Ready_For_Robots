"""Persist admin dashboard snapshots in pipeline_cache_store (shared across Fly instances)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)

ADMIN_SNAPSHOT_KEY = "admin_snapshot_v1"
_FRESH_TTL_MINUTES = 15


def read_admin_snapshot(*, stale_ok: bool = True) -> Optional[dict[str, Any]]:
    """Read snapshot from Supabase. Returns None only when missing (or stale if stale_ok=False)."""
    try:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            row = db.execute(
                text(
                    "SELECT data, built_at, expires_at FROM pipeline_cache_store "
                    "WHERE cache_key = :k LIMIT 1"
                ),
                {"k": ADMIN_SNAPSHOT_KEY},
            ).fetchone()
            if not row:
                return None
            expires = row.expires_at
            if not stale_ok and expires and expires < datetime.now(timezone.utc):
                return None
            raw = row.data
            payload = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(payload, dict):
                payload.setdefault("_cache_built_at", row.built_at.isoformat() if row.built_at else None)
            return payload
        finally:
            db.close()
    except Exception as exc:
        logger.debug("admin snapshot read failed: %s", exc)
        return None


def write_admin_snapshot(data: dict[str, Any]) -> None:
    try:
        from app.database import SessionLocal

        expires = (datetime.now(timezone.utc) + timedelta(minutes=_FRESH_TTL_MINUTES)).isoformat()
        db = SessionLocal()
        try:
            db.execute(
                text(
                    "INSERT INTO pipeline_cache_store (cache_key, data, built_at, expires_at) "
                    "VALUES (:k, :d::jsonb, now(), :e) "
                    "ON CONFLICT (cache_key) DO UPDATE "
                    "SET data = EXCLUDED.data, built_at = now(), expires_at = EXCLUDED.expires_at"
                ),
                {"k": ADMIN_SNAPSHOT_KEY, "d": json.dumps(data), "e": expires},
            )
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.warning("admin snapshot write failed: %s", exc)


def invalidate_admin_snapshot() -> None:
    try:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(
                text("DELETE FROM pipeline_cache_store WHERE cache_key = :k"),
                {"k": ADMIN_SNAPSHOT_KEY},
            )
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.debug("admin snapshot invalidate failed: %s", exc)
