"""Composed URL → profile → jobs search.

One server transaction. Cache grounded profiles. Instrument timings.
UI must still reveal atomically — this payload is the first-page result model.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.services.robot_profile_cache import get_cached_profile, set_cached_profile
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.robot_understanding_v1 import build_robot_profile
from app.services.robot_url_safety import assert_public_http_url

logger = logging.getLogger(__name__)

TOP_JOBS = 5


def _timings(
    *,
    resolve_ms: int = 0,
    profile_ms: int = 0,
    match_ms: int = 0,
    total_ms: int = 0,
    cached: bool = False,
    sources_ms: int = 0,
) -> dict[str, Any]:
    return {
        "resolve_ms": int(resolve_ms),
        "profile_ms": int(profile_ms),
        "sources_ms": int(sources_ms),
        "match_ms": int(match_ms),
        "total_ms": int(total_ms),
        "cached": bool(cached),
    }


def compose_robot_job_search(
    url: str,
    *,
    product: str | None = None,
    max_sources: int = 6,
    record_shadow=None,
) -> dict[str, Any]:
    """Build (or reuse) a Robot Profile and match jobs. Never streams partial jobs."""
    t0 = time.perf_counter()
    safe = assert_public_http_url(url)
    product_name = (product or "").strip() or None

    cached = get_cached_profile(safe, product_name)
    build_timings: dict[str, Any] = {"resolve_ms": 0, "profile_ms": 0}
    if cached:
        profile_dict = cached
        cached_hit = True
    else:
        cached_hit = False
        profile_obj = build_robot_profile(
            safe,
            product_name=product_name,
            max_sources=max_sources,
            timings=build_timings,
        )
        profile_dict = profile_obj.to_dict()
        set_cached_profile(safe, product_name, profile_dict)
        if record_shadow is not None:
            try:
                duration_ms = int((time.perf_counter() - t0) * 1000)
                record_shadow(profile_obj, duration_ms)
            except Exception:
                logger.exception("robot_job_search shadow failed")

    company = (profile_dict.get("company") or {}).get("name") or "your robot"
    selected = profile_dict.get("selected_product") or {}
    robot_name = selected.get("name") or company
    products = profile_dict.get("products") or []

    if profile_dict.get("needs_product_choice") and len(products) > 1 and not product_name:
        total_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "state": "select_product",
            "robot_name": company,
            "company_name": company,
            "capabilities": [],
            "families": [],
            "jobs": [],
            "top_jobs": [],
            "job_count": 0,
            "profile": profile_dict,
            "products": products,
            "needs_product_choice": True,
            "matcher": None,
            "robot_class": None,
            "source_url": safe,
            "timings": _timings(
                resolve_ms=build_timings.get("resolve_ms") or 0,
                profile_ms=build_timings.get("profile_ms") or 0,
                sources_ms=build_timings.get("sources_ms") or 0,
                match_ms=0,
                total_ms=total_ms,
                cached=cached_hit,
            ),
        }

    t_match = time.perf_counter()
    match = match_jobs_from_profile(profile_dict, limit=12)
    match_ms = int((time.perf_counter() - t_match) * 1000)
    jobs = list(match.get("jobs") or [])
    top_jobs = jobs[:TOP_JOBS]
    total_ms = int((time.perf_counter() - t0) * 1000)
    state = match.get("state") or ("matches" if jobs else "could_not_understand")
    zero_reason = None
    if not jobs:
        from app.services.zero_state import classify_zero_state, corpus_family_set

        zero_reason = classify_zero_state(match.get("capabilities") or [], corpus_family_set())
    return {
        "state": state,
        "robot_name": match.get("robot_name") or robot_name,
        "company_name": match.get("company_name") or company,
        "capabilities": match.get("capabilities") or [],
        "families": match.get("families") or [],
        "jobs": jobs,
        "top_jobs": top_jobs,
        "job_count": match.get("job_count") or len(jobs),
        "profile": profile_dict,
        "products": products,
        "needs_product_choice": False,
        "matcher": match.get("matcher"),
        "zero_reason": zero_reason,
        "robot_class": match.get("robot_class") or selected.get("display_class"),
        "source_url": safe,
        "timings": _timings(
            resolve_ms=0 if cached_hit else (build_timings.get("resolve_ms") or 0),
            profile_ms=0 if cached_hit else (build_timings.get("profile_ms") or 0),
            sources_ms=0 if cached_hit else (build_timings.get("sources_ms") or 0),
            match_ms=match_ms,
            total_ms=total_ms,
            cached=cached_hit,
        ),
    }
