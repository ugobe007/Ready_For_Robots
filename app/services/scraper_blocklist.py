"""
Scraper Blocklist
=================
Stores names of companies that were manually deleted as junk so the scraper
doesn't re-ingest them on the next run.

The blocklist is persisted to the database via the `ScraperBlocklist` table.
Falls back to an in-memory set if the DB is unavailable.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory cache: populated on first call to is_blocklisted()
_BLOCKLIST_CACHE: set[str] | None = None


def _load_from_db() -> set[str]:
    """Load all blocked names from the database."""
    try:
        from app.database import SessionLocal
        from app.models.scraper_blocklist import ScraperBlocklist
        db = SessionLocal()
        try:
            rows = db.query(ScraperBlocklist.name_lower).all()
            return {r[0] for r in rows}
        finally:
            db.close()
    except Exception as e:
        logger.warning("Could not load scraper blocklist from DB: %s", e)
        return set()


def _get_cache() -> set[str]:
    global _BLOCKLIST_CACHE
    if _BLOCKLIST_CACHE is None:
        _BLOCKLIST_CACHE = _load_from_db()
        logger.debug("Scraper blocklist loaded: %d entries", len(_BLOCKLIST_CACHE))
    return _BLOCKLIST_CACHE


def is_blocklisted(name: str) -> bool:
    """Return True if this company name was previously deleted as junk."""
    if not name:
        return False
    return name.strip().lower() in _get_cache()


def add_to_blocklist(name: str, reason: str = "manual_delete") -> None:
    """
    Permanently block a name from being re-ingested.
    Call this whenever a company is deleted via admin purge.
    """
    global _BLOCKLIST_CACHE
    if not name or not name.strip():
        return
    key = name.strip().lower()
    try:
        from app.database import SessionLocal
        from app.models.scraper_blocklist import ScraperBlocklist
        db = SessionLocal()
        try:
            exists = db.query(ScraperBlocklist).filter(ScraperBlocklist.name_lower == key).first()
            if not exists:
                db.add(ScraperBlocklist(name_lower=key, original_name=name.strip(), reason=reason))
                db.commit()
                logger.debug("Blocklisted: %r (%s)", name, reason)
        finally:
            db.close()
    except Exception as e:
        logger.warning("Could not persist blocklist entry for %r: %s", name, e)
    # Always update in-memory cache
    if _BLOCKLIST_CACHE is not None:
        _BLOCKLIST_CACHE.add(key)


def add_bulk_to_blocklist(names: list[str], reason: str = "bulk_purge") -> int:
    """Add multiple names to the blocklist. Returns count added."""
    added = 0
    for name in names:
        if name and name.strip():
            add_to_blocklist(name, reason)
            added += 1
    return added


def invalidate_cache() -> None:
    """Force reload from DB on next call."""
    global _BLOCKLIST_CACHE
    _BLOCKLIST_CACHE = None
