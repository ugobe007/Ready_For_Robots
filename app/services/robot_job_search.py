"""Composed URL → profile → jobs search.

One server transaction. Cache grounded profiles. Instrument timings.
UI must still reveal atomically — this payload is the first-page result model.
"""
from __future__ import annotations

import copy
import logging
import time
from typing import Any

from app.services.robot_profile_cache import get_cached_profile, set_cached_profile
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.robot_understanding_v1 import build_robot_profile
from app.services.robot_url_safety import assert_public_http_url

logger = logging.getLogger(__name__)

TOP_JOBS = 5


def profile_is_research_complete(profile: dict[str, Any] | None) -> bool:
    """True when a cached profile is grounded enough to match jobs.

    Identity-only picker payloads (`needs_product_choice`) must not be reused
    as a match input — they have no facts/sources yet.
    """
    if not isinstance(profile, dict):
        return False
    if profile.get("needs_product_choice"):
        return False
    # A low-coverage C profile (payload + IP only) is not match-ready.
    # Reusing it for 6 hours is how 1X NEO stayed on insufficient evidence.
    if (profile.get("coverage_level") or "").lower() == "low":
        return False
    return bool(profile.get("facts") or profile.get("sources"))


def profile_is_worth_caching(profile: dict[str, Any] | None) -> bool:
    """Do not pin a 6-hour miss on a thin / low-coverage profile.

    1X NEO's first pass extracted payload + IP only. Caching that C/low
    profile made every retry return insufficient evidence until TTL expired.
    """
    if not profile_is_research_complete(profile):
        return False
    assert isinstance(profile, dict)
    if (profile.get("coverage_level") or "").lower() == "low":
        return False
    return True


def overlay_selected_product(profile: dict[str, Any], product: str) -> dict[str, Any]:
    """Stamp a SKU onto a grounded company profile without rebuilding sources."""
    out = copy.deepcopy(profile)
    want = (product or "").strip()
    products = list(out.get("products") or [])
    match = None
    if want:
        want_l = want.lower()
        for row in products:
            if isinstance(row, dict) and str(row.get("name") or "").strip().lower() == want_l:
                match = row
                break
    if match is None and want:
        match = {"name": want}
        products = [*products, match]
        out["products"] = products
    out["selected_product"] = match
    out["needs_product_choice"] = False
    return out


def resolve_cached_profile(url: str, product: str | None) -> dict[str, Any] | None:
    """SKU cache, then grounded company cache overlaid with the requested product."""
    hit = get_cached_profile(url, product)
    if hit:
        return hit
    if not product:
        return None
    base = get_cached_profile(url, None)
    if not profile_is_research_complete(base):
        return None
    return overlay_selected_product(base, product)


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


def _normalize_lookup_grain(raw: str | None) -> str:
    grain = (raw or "product").strip().lower().replace("-", "_")
    if grain in {"type", "class", "product_class", "robot_class", "robot_type"}:
        return "robot_type"
    return "product"


def _vendor_company_name(url: str) -> str | None:
    try:
        from app.services.vendor_robot_lookup import lookup_vendor_by_url

        hit = lookup_vendor_by_url(url)
    except Exception:
        return None
    if not isinstance(hit, dict):
        return None
    name = (hit.get("vendor_name") or "").strip()
    return name or None


_SKU_WORK_KIND_PREDICATES = frozenset(
    {
        "claims_weeding",
        "claims_combine_harvest",
        "claims_precision_spray",
        "claims_tractor_work",
        "claims_construction_print",
        "claims_construction_block",
        "claims_construction_layout",
    }
)


def _indexed_work_kind_product(url: str, product: str | None) -> str | None:
    """Named SKU with a work-kind claim — match the configuration, not the tile."""
    try:
        from app.services.vendor_robot_lookup import (
            catalog_claim_facts,
            index_robot_for_name,
            index_robot_names,
            lookup_vendor_by_url,
        )

        vendor = lookup_vendor_by_url(url)
    except Exception:
        return None
    if not isinstance(vendor, dict):
        return None
    robot = index_robot_for_name(vendor, product) if product else None
    if robot is None:
        names = index_robot_names(vendor)
        if len(names) == 1:
            robot = index_robot_for_name(vendor, names[0])
    if not robot:
        return None
    preds = {str(f.get("predicate") or "") for f in catalog_claim_facts(robot)}
    if preds & _SKU_WORK_KIND_PREDICATES:
        return str(robot.get("name") or product or "").strip() or None
    return None


def compose_robot_job_search(
    url: str,
    *,
    product: str | None = None,
    max_sources: int = 6,
    record_shadow=None,
    asserted_class: str | None = None,
    lookup_grain: str | None = None,
) -> dict[str, Any]:
    """Build (or reuse) a Robot Profile and match jobs. Never streams partial jobs.

    `lookup_grain=robot_type` matches from product_class (the group) without
    scraping a SKU page. `product` still researches one robot.
    """
    t0 = time.perf_counter()
    safe = assert_public_http_url(url)
    product_name = (product or "").strip() or None
    grain = _normalize_lookup_grain(lookup_grain)
    build_timings: dict[str, Any] = {"resolve_ms": 0, "profile_ms": 0}
    cached_hit = False
    type_first = False
    profile_dict: dict[str, Any] | None = None

    if grain == "robot_type":
        from app.services.robot_class_qualify import lookup_class_id, thin_class_profile

        sku_name = _indexed_work_kind_product(safe, product_name)
        if sku_name:
            # LaserWeeder / Vulcan / combine: MATCH the SKU work-kind, not the
            # FIND-tile union (and not CNC leftover from the tile).
            product_name = sku_name
        else:
            class_id = lookup_class_id(asserted_class)
            if class_id:
                company_name = _vendor_company_name(safe) or "your robot"
                profile_dict = thin_class_profile(company_name, class_id, source_url=safe)
                type_first = True

    if not type_first:
        cached = resolve_cached_profile(safe, product_name)
        if cached:
            profile_dict = cached
            cached_hit = True
            if product_name and get_cached_profile(safe, product_name) is None:
                if profile_is_worth_caching(profile_dict):
                    set_cached_profile(safe, product_name, profile_dict)
        else:
            cached_hit = False
            profile_obj = build_robot_profile(
                safe,
                product_name=product_name,
                max_sources=max_sources,
                timings=build_timings,
            )
            profile_dict = profile_obj.to_dict()
            if profile_is_worth_caching(profile_dict):
                set_cached_profile(safe, product_name, profile_dict)
            if record_shadow is not None:
                try:
                    duration_ms = int((time.perf_counter() - t0) * 1000)
                    record_shadow(profile_obj, duration_ms)
                except Exception:
                    logger.exception("robot_job_search shadow failed")

        if asserted_class and not _indexed_work_kind_product(safe, product_name):
            from app.services.robot_class_qualify import apply_asserted_class

            profile_dict = apply_asserted_class(profile_dict, asserted_class)

    assert profile_dict is not None
    company = (profile_dict.get("company") or {}).get("name") or "your robot"
    selected = profile_dict.get("selected_product") or {}
    robot_name = selected.get("name") or company
    products = profile_dict.get("products") or []

    if (
        not type_first
        and profile_dict.get("needs_product_choice")
        and len(products) > 1
        and not product_name
    ):
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

    from app.services.robot_class_qualify import public_class_options
    from app.services.zero_state import INSUFFICIENT_PROFILE_EVIDENCE

    needs_class_choice = False
    if not jobs and zero_reason == INSUFFICIENT_PROFILE_EVIDENCE:
        # Never a dead-end: ask the operator to name the morphology so we can match.
        needs_class_choice = True
        state = "qualify_robot"
        zero_reason = None
    preview = None
    for url in profile_dict.get("preview_images") or []:
        if isinstance(url, str) and url.strip():
            preview = url.strip()
            break
    if preview is None:
        for src in profile_dict.get("sources") or []:
            if isinstance(src, dict) and (src.get("url") or "").lower().endswith(
                (".png", ".jpg", ".jpeg", ".webp", ".gif")
            ):
                preview = src.get("url")
                break

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
        "needs_class_choice": needs_class_choice,
        "class_options": public_class_options() if needs_class_choice else [],
        "preview_image_url": preview,
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
