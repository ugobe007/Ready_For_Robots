"""
Pre-built newsletter API snapshots — serve instantly without DB rebuild on GET.

Daily publish (6am America/Los_Angeles) writes a slim API payload to durable cache
and in-process L1. Request handlers read snapshot → mem → seed only.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.services.newsletter_library import load_seed_edition
from app.services.newsletter_service import (
    NEWSLETTER_API_SNAPSHOT_KEY,
    NEWSLETTER_PIPELINE_CACHE_KEY,
    NEWSLETTER_SNAPSHOT_TTL_MINUTES,
    fallback_edition,
)
from app.services.public_surface_cache import read_public_cache

logger = logging.getLogger(__name__)

_edition_mem_cache: dict = {}

_STORY_API_KEYS = frozenset({
    "category", "company", "headline", "snippet", "summary", "roi", "economics",
    "impact", "signalStrength", "company_id", "tier", "industry",
})


def hydrate_newsletter_mem_cache(data: dict) -> None:
    if not (data.get("topStories") or []):
        return
    _edition_mem_cache["v1"] = {"ts": time.monotonic(), "data": data}


def get_newsletter_mem_cache() -> Optional[dict]:
    entry = _edition_mem_cache.get("v1")
    if entry:
        return entry["data"]
    return None


def _trim_edition(data: dict, limit: int) -> dict:
    stories = data.get("topStories") or []
    if len(stories) > limit:
        return {**data, "topStories": stories[:limit]}
    return data


def _slim_story(story: dict) -> dict:
    if not isinstance(story, dict):
        return story
    slim = {k: v for k, v in story.items() if k in _STORY_API_KEYS}
    for text_key in ("summary", "snippet", "headline"):
        val = slim.get(text_key)
        if isinstance(val, str) and len(val) > 1200:
            slim[text_key] = val[:1199].rstrip() + "…"
    full = story.get("fullText")
    if isinstance(full, str) and full.strip() and "summary" not in slim:
        slim["summary"] = full[:1200].rstrip() + ("…" if len(full) > 1200 else "")
    return slim


def slim_edition_for_api(data: dict, *, limit: int = 15) -> dict:
    trimmed = _trim_edition(data, limit)
    stories = [_slim_story(s) for s in (trimmed.get("topStories") or [])]
    out = {**trimmed, "topStories": stories}
    findings = trimmed.get("researchFindings") or []
    if isinstance(findings, list) and len(findings) > 8:
        out["researchFindings"] = findings[:8]
    brief = trimmed.get("industryBrief")
    if isinstance(brief, dict):
        out["industryBrief"] = {
            k: (v[:6] if isinstance(v, list) else v)
            for k, v in brief.items()
            if k in ("executive_take", "macro_trends", "strategic_implications", "risks_and_unknowns", "watch_next")
        }
    meta = dict(trimmed.get("_meta") or {})
    meta["api_snapshot"] = True
    meta["snapshot_limit"] = limit
    out["_meta"] = meta
    return out


def publish_api_snapshot(db: Session, edition: dict, *, limit: int = 15) -> dict:
    """Persist API-ready snapshot (24h TTL) and warm L1."""
    from app.services.pipeline_cache_store import cache_write

    snapshot = slim_edition_for_api(edition, limit=limit)
    cache_write(db, NEWSLETTER_API_SNAPSHOT_KEY, snapshot, ttl_minutes=NEWSLETTER_SNAPSHOT_TTL_MINUTES)
    cache_write(db, NEWSLETTER_PIPELINE_CACHE_KEY, edition, ttl_minutes=NEWSLETTER_SNAPSHOT_TTL_MINUTES)
    hydrate_newsletter_mem_cache(snapshot)
    logger.info(
        "Newsletter API snapshot published (%d stories, limit=%d)",
        len(snapshot.get("topStories") or []),
        limit,
    )
    return snapshot


def serve_api_snapshot(*, limit: int = 15) -> dict:
    """Read-only serve path — single cache read max, no DB generation."""
    mem = get_newsletter_mem_cache()
    if mem and len(mem.get("topStories") or []) >= 1:
        return _trim_edition(mem, limit)

    snap = read_public_cache(NEWSLETTER_API_SNAPSHOT_KEY, stale_ok=True)
    if snap and len(snap.get("topStories") or []) >= 1:
        hydrate_newsletter_mem_cache(snap)
        return _trim_edition(snap, limit)

    full = read_public_cache(NEWSLETTER_PIPELINE_CACHE_KEY, stale_ok=True)
    if full and len(full.get("topStories") or []) >= 1:
        out = slim_edition_for_api(full, limit=limit)
        hydrate_newsletter_mem_cache(out)
        return out

    seed = load_seed_edition()
    if seed and len(seed.get("topStories") or []) >= 1:
        out = slim_edition_for_api(seed, limit=limit)
        hydrate_newsletter_mem_cache(out)
        return out

    return slim_edition_for_api(fallback_edition(limit=limit), limit=limit)
