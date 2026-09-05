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


def cache_read_many(
    db: Session,
    cache_keys: list[str],
    *,
    stale_ok: bool = True,
) -> dict[str, Any]:
    """Read multiple cache keys in one round trip."""
    if not cache_keys:
        return {}
    try:
        ensure_pipeline_cache_table(db)
        rows = db.execute(
            text(
                "SELECT cache_key, data, expires_at FROM pipeline_cache_store "
                "WHERE cache_key = ANY(:keys)"
            ),
            {"keys": list(cache_keys)},
        ).fetchall()
        now = datetime.now(timezone.utc)
        out: dict[str, Any] = {}
        for row in rows:
            if not stale_ok and row.expires_at and row.expires_at < now:
                continue
            raw = row.data
            out[str(row.cache_key)] = json.loads(raw) if isinstance(raw, str) else raw
        return out
    except Exception as exc:
        logger.warning("pipeline_cache_store read_many failed: %s", exc)
        db.rollback()
        return {}


def cache_read_many_safe(
    cache_keys: list[str],
    *,
    stale_ok: bool = True,
    timeout_sec: float = 3.0,
) -> dict[str, Any]:
    """Batch cache read — one DB session, bounded timeout."""
    if not cache_keys:
        return {}
    from app.database import SessionLocal
    from app.db_timeout import run_db

    def _read() -> dict[str, Any]:
        db = SessionLocal()
        try:
            return cache_read_many(db, cache_keys, stale_ok=stale_ok)
        finally:
            db.close()

    try:
        return (
            run_db(_read, timeout_sec=timeout_sec, label="cache-read-many")
            or {}
        )
    except TimeoutError:
        logger.warning("pipeline_cache_store read_many timed out (%d keys)", len(cache_keys))
        return {}
    except Exception as exc:
        logger.warning("pipeline_cache_store read_many failed: %s", exc)
        return {}


def cache_read_safe(cache_key: str, *, stale_ok: bool = True, timeout_sec: float = 3.0) -> Optional[Any]:
    """Read cache in a timeout-bound thread — never block the request on a hung pooler."""
    from app.database import SessionLocal
    from app.db_timeout import run_db

    def _read() -> Optional[Any]:
        db = SessionLocal()
        try:
            return cache_read(db, cache_key, stale_ok=stale_ok)
        finally:
            db.close()

    try:
        return run_db(_read, timeout_sec=timeout_sec, label=f"cache-read/{cache_key[:24]}")
    except TimeoutError:
        logger.warning("pipeline_cache_store read timed out (%s)", cache_key)
        return None
    except Exception as exc:
        logger.warning("pipeline_cache_store read failed (%s): %s", cache_key, exc)
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
            {"k": cache_key, "d": json.dumps(data, default=str), "e": expires.isoformat()},
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
