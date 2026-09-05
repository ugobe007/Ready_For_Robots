"""
Newsletter library — durable archive of daily editions.

The morning agent writes here first; GET /api/newsletter/edition always serves
from the library when the live cache is empty. Incremental updates skip full
regeneration when lead/signal fingerprints are unchanged.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.score import Score
from app.models.signal import Signal
from app.services.pipeline_cache_store import cache_read, cache_read_safe, cache_write

logger = logging.getLogger(__name__)

LIBRARY_LATEST_KEY = "newsletter:library:latest:v1"
LIBRARY_FINGERPRINT_KEY = "newsletter:library:fingerprint:v1"
LIBRARY_INDEX_KEY = "newsletter:library:index:v1"
LIBRARY_TTL_MINUTES = 60 * 24 * 90  # 90 days

_SEED_LOADED = False
_SEED_EDITION: Optional[Dict[str, Any]] = None


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def library_dir() -> Path:
    env_path = os.getenv("NEWSLETTER_LIBRARY_DIR")
    if env_path:
        p = Path(env_path)
        return p if p.is_absolute() else _project_root() / env_path
    return _project_root() / "data" / "newsletter_library"


def seed_edition_path() -> Path:
    return _project_root() / "resources" / "newsletter_library" / "latest.json"


def _read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else None
    except Exception as exc:
        logger.debug("newsletter library read failed (%s): %s", path, exc)
        return None


def load_seed_edition() -> Optional[Dict[str, Any]]:
    """Bundled fallback shipped with the repo — instant on cold deploy."""
    global _SEED_LOADED, _SEED_EDITION
    if _SEED_LOADED:
        return _SEED_EDITION
    _SEED_LOADED = True
    data = _read_json_file(seed_edition_path())
    if data and (data.get("topStories") or []):
        _SEED_EDITION = data
        logger.info(
            "Newsletter seed library loaded (%d stories)",
            len(data.get("topStories") or []),
        )
    return _SEED_EDITION


def compute_content_fingerprint(db: Session) -> str:
    """
    Fingerprint the top in-market lead signal set. When unchanged, the morning
    agent only refreshes edition metadata instead of rebuilding every story.
    """
    rows = (
        db.query(
            Company.id.label("company_id"),
            func.max(Signal.id).label("max_signal_id"),
            func.max(Signal.created_at).label("latest_signal_at"),
        )
        .join(Signal, Signal.company_id == Company.id)
        .outerjoin(Score, Score.company_id == Company.id)
        .filter(func.coalesce(Score.overall_intent_score, 0) >= 40)
        .group_by(Company.id)
        .order_by(func.coalesce(func.max(Score.overall_intent_score), 0).desc())
        .limit(48)
        .all()
    )
    parts: List[str] = []
    for row in rows:
        ts = row.latest_signal_at.isoformat() if row.latest_signal_at else "0"
        parts.append(f"{row.company_id}:{row.max_signal_id}:{ts}")
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def read_stored_fingerprint(db: Optional[Session] = None) -> Optional[str]:
    if db is not None:
        try:
            fp = cache_read(db, LIBRARY_FINGERPRINT_KEY, stale_ok=True)
            if isinstance(fp, str):
                return fp
            if isinstance(fp, dict):
                return fp.get("fingerprint")
        except Exception:
            pass
    fp_safe = cache_read_safe(LIBRARY_FINGERPRINT_KEY, stale_ok=True, timeout_sec=4.0)
    if isinstance(fp_safe, str):
        return fp_safe
    if isinstance(fp_safe, dict):
        return fp_safe.get("fingerprint")
    meta_path = library_dir() / "fingerprint.txt"
    if meta_path.exists():
        return meta_path.read_text().strip() or None
    return None


def _write_library_file(edition: Dict[str, Any], fingerprint: str) -> None:
    lib = library_dir()
    lib.mkdir(parents=True, exist_ok=True)
    dated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (lib / "latest.json").write_text(json.dumps(edition, indent=2))
    (lib / f"{dated}.json").write_text(json.dumps(edition, indent=2))
    (lib / "fingerprint.txt").write_text(fingerprint)


def save_to_library(db: Session, edition: Dict[str, Any], fingerprint: str) -> None:
    stories = edition.get("topStories") or []
    if not stories:
        logger.warning("Refusing to save empty newsletter edition to library")
        return

    meta = edition.setdefault("_meta", {})
    meta.update(
        {
            "fingerprint": fingerprint,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "story_count": len(stories),
        }
    )

    cache_write(db, LIBRARY_LATEST_KEY, edition, ttl_minutes=LIBRARY_TTL_MINUTES)
    cache_write(db, LIBRARY_FINGERPRINT_KEY, {"fingerprint": fingerprint}, ttl_minutes=LIBRARY_TTL_MINUTES)

    dated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    index = cache_read(db, LIBRARY_INDEX_KEY, stale_ok=True) or []
    if not isinstance(index, list):
        index = []
    if dated not in index:
        index.insert(0, dated)
    cache_write(db, LIBRARY_INDEX_KEY, index[:90], ttl_minutes=LIBRARY_TTL_MINUTES)

    try:
        _write_library_file(edition, fingerprint)
    except Exception as exc:
        logger.warning("Newsletter library file write failed: %s", exc)


def load_library_latest(db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """Latest archived edition — Postgres, local files, then bundled seed."""
    if db is not None:
        try:
            data = cache_read(db, LIBRARY_LATEST_KEY, stale_ok=True)
            if data and (data.get("topStories") or []):
                return data
        except Exception:
            pass

    cached = cache_read_safe(LIBRARY_LATEST_KEY, stale_ok=True, timeout_sec=5.0)
    if cached and (cached.get("topStories") or []):
        return cached

    lib = library_dir()
    for path in (lib / "latest.json",):
        data = _read_json_file(path)
        if data and (data.get("topStories") or []):
            return data

    dated_files = sorted(lib.glob("20*.json"), reverse=True)
    for path in dated_files[:14]:
        data = _read_json_file(path)
        if data and (data.get("topStories") or []):
            return data

    return load_seed_edition()


def refresh_edition_metadata(edition: Dict[str, Any]) -> Dict[str, Any]:
    """Roll forward dates/edition number without rebuilding story bodies."""
    now = datetime.now(timezone.utc)
    updated = dict(edition)
    updated["latestEdition"] = {
        **(edition.get("latestEdition") or {}),
        "date": now.strftime("%B %d, %Y"),
        "edition": f"#{now.strftime('%j')}",
    }
    summary = dict(edition.get("summary") or {})
    summary["generated_at"] = now.isoformat()
    summary["total_leads"] = len(edition.get("topStories") or [])
    summary["update_mode"] = "metadata_only"
    updated["summary"] = summary
    meta = dict(edition.get("_meta") or {})
    meta["metadata_refreshed_at"] = now.isoformat()
    updated["_meta"] = meta
    return updated


def merge_with_library(
    new_edition: Dict[str, Any],
    library_edition: Dict[str, Any],
) -> Dict[str, Any]:
    """Keep prior stories when a rebuild returns too few rows."""
    merged = dict(library_edition)
    if new_edition.get("latestEdition"):
        merged["latestEdition"] = new_edition["latestEdition"]
    if new_edition.get("industryBrief"):
        merged["industryBrief"] = new_edition["industryBrief"]
    if new_edition.get("researchFindings") is not None:
        merged["researchFindings"] = new_edition["researchFindings"]
    now = datetime.now(timezone.utc)
    merged["summary"] = {
        **(library_edition.get("summary") or {}),
        "generated_at": now.isoformat(),
        "total_leads": len(merged.get("topStories") or []),
        "update_mode": "preserved_library_stories",
    }
    return merged


def build_daily_newsletter_edition(
    db: Session,
    *,
    limit: int = 15,
    force: bool = False,
    skip_openai_brief: bool = False,
) -> Dict[str, Any]:
    """
    Morning agent entry point.

    - fingerprint unchanged → metadata refresh only (fast)
    - fingerprint changed → full generate_edition + library save
    - generate returns too few stories → preserve library stories
    """
    from app.services.newsletter_service import generate_edition

    fingerprint = compute_content_fingerprint(db)
    stored_fp = read_stored_fingerprint(db)
    library_latest = load_library_latest(db)

    if (
        not force
        and library_latest
        and stored_fp
        and stored_fp == fingerprint
        and len(library_latest.get("topStories") or []) >= 8
    ):
        edition = refresh_edition_metadata(library_latest)
        edition["_meta"] = {
            **(edition.get("_meta") or {}),
            "fingerprint": fingerprint,
            "update_mode": "metadata_only",
        }
        logger.info("Newsletter library unchanged — metadata refresh only")
        return edition

    if force and not skip_openai_brief:
        from app.services.industry_brief_service import build_industry_brief_payload

        try:
            days = max(1, int(os.getenv("NEWSLETTER_STRATEGIC_BRIEF_DAYS", "7")))
        except ValueError:
            days = 7
        build_industry_brief_payload(
            db,
            days=days,
            analytics=None,
            use_cache=True,
            force_refresh=True,
        )

    edition = generate_edition(db, limit=limit, skip_openai_brief=skip_openai_brief)
    stories = edition.get("topStories") or []

    if len(stories) < 8 and library_latest and (library_latest.get("topStories") or []):
        edition = merge_with_library(edition, library_latest)
        edition["_meta"] = {
            **(edition.get("_meta") or {}),
            "fingerprint": stored_fp or fingerprint,
            "update_mode": "preserved_library_stories",
        }
        logger.info("Newsletter rebuild sparse — preserved %d library stories", len(edition.get("topStories") or []))
        return edition

    if len(stories) < 1 and library_latest:
        edition = refresh_edition_metadata(library_latest)
        edition["_meta"] = {
            **(edition.get("_meta") or {}),
            "fingerprint": stored_fp or fingerprint,
            "update_mode": "library_fallback",
        }
        return edition

    edition["_meta"] = {
        **(edition.get("_meta") or {}),
        "fingerprint": fingerprint,
        "update_mode": "full_rebuild",
    }
    save_to_library(db, edition, fingerprint)
    return edition


def resolve_edition_for_serving(
    db: Optional[Session] = None,
    *,
    limit: int = 15,
) -> Dict[str, Any]:
    """
    Read path: never return an empty story list if any library layer has content.
    """
    from app.services.newsletter_service import (
        NEWSLETTER_PIPELINE_CACHE_KEY,
        fallback_edition,
        read_cached_edition_stale,
    )

    def _trim(data: dict) -> dict:
        stories = data.get("topStories") or []
        if len(stories) > limit:
            return {**data, "topStories": stories[:limit]}
        return data

    for loader_name, loader in (
        ("pipeline_cache", lambda: cache_read_safe(NEWSLETTER_PIPELINE_CACHE_KEY, stale_ok=True, timeout_sec=5.0)),
        ("library", lambda: load_library_latest(db)),
        ("file_stale", read_cached_edition_stale),
        ("seed", load_seed_edition),
    ):
        try:
            data = loader()
        except Exception:
            data = None
        if data and len(data.get("topStories") or []) >= 1:
            meta = data.setdefault("_meta", {})
            meta["served_from"] = loader_name
            return _trim(data)

    fb = fallback_edition(limit=limit)
    fb.setdefault("_meta", {})["served_from"] = "fallback"
    return _trim(fb)
