"""Read/write pipeline_cache_store — safe SQL (no :param::type bind ambiguity)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_TABLE_READY = False


def ensure_pipeline_cache_table(db: Session) -> None:
    global _TABLE_READY
    if _TABLE_READY:
        return
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS pipeline_cache_store (
                cache_key   TEXT PRIMARY KEY,
                data        JSONB NOT NULL DEFAULT '{}'::jsonb,
                built_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
                expires_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_pipeline_cache_store_expires
            ON pipeline_cache_store (expires_at)
            """
        )
    )
    db.commit()
    _TABLE_READY = True


def cache_read(db: Session, cache_key: str, *, stale_ok: bool = True) -> Optional[Any]:
    """Return cached JSON payload or None if missing / expired."""
    try:
        ensure_pipeline_cache_table(db)
        row = db.execute(
            text(
                "SELECT data, expires_at FROM pipeline_cache_store "
                "WHERE cache_key = :k LIMIT 1"
            ),
            {"k": cache_key},
        ).fetchone()
        if not row:
            return None
        expires = row.expires_at
        if not stale_ok and expires and expires < datetime.now(timezone.utc):
            return None
        raw = row.data
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception as exc:
        logger.warning("pipeline_cache_store read failed (%s): %s", cache_key, exc)
        db.rollback()
        return None


def cache_write(db: Session, cache_key: str, data: Any, *, ttl_minutes: int = 15) -> None:
    try:
        ensure_pipeline_cache_table(db)
        expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        db.execute(
            text(
                """
                INSERT INTO pipeline_cache_store (cache_key, data, built_at, expires_at)
                VALUES (:k, CAST(:d AS jsonb), now(), CAST(:e AS timestamptz))
                ON CONFLICT (cache_key) DO UPDATE
                SET data = EXCLUDED.data,
                    built_at = now(),
                    expires_at = EXCLUDED.expires_at
                """
            ),
            {"k": cache_key, "d": json.dumps(data), "e": expires.isoformat()},
        )
        db.commit()
    except Exception as exc:
        logger.warning("pipeline_cache_store write failed (%s): %s", cache_key, exc)
        db.rollback()


def cache_delete(db: Session, cache_key: str) -> None:
    try:
        ensure_pipeline_cache_table(db)
        db.execute(
            text("DELETE FROM pipeline_cache_store WHERE cache_key = :k"),
            {"k": cache_key},
        )
        db.commit()
    except Exception as exc:
        logger.debug("pipeline_cache_store delete failed (%s): %s", cache_key, exc)
        db.rollback()
