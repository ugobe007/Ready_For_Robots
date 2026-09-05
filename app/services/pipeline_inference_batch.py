"""
Batch re-run lead inference for top pipeline companies (admin).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.signal import Signal
from app.services.lead_inference_engine import refresh_company_inference

logger = logging.getLogger(__name__)

DEFAULT_BATCH_LIMIT = 300
MAX_BATCH_LIMIT = 500


def select_pipeline_surface_company_ids(
    db: Session,
    *,
    limit: int = DEFAULT_BATCH_LIMIT,
    slots_multiplier: int = 4,
) -> List[int]:
    """
    Company IDs from the same HOT/WARM/COLD staging as GET /api/leads/pipeline.

    Uses a wider per-tier pool (``slots_multiplier``) for secondary pass / inference
    batches while preserving tier diversity and classify_lead gating.
    """
    from app.api.leads import (
        PIPELINE_HOT_SLOTS,
        PIPELINE_MONITOR_SLOTS,
        PIPELINE_WARM_SLOTS,
        _fetch_staged_by_tier,
    )

    lim = max(1, min(int(limit), MAX_BATCH_LIMIT))
    mult = max(2, int(slots_multiplier))
    hot_n = min(PIPELINE_HOT_SLOTS * mult, lim)
    warm_n = min(PIPELINE_WARM_SLOTS * mult, max(0, lim - hot_n))
    cold_n = min(PIPELINE_MONITOR_SLOTS * mult, max(0, lim - hot_n - warm_n))

    exclude: set[int] = set()
    ids: List[int] = []

    for tier, tier_lim in (
        ("HOT", hot_n),
        ("WARM", warm_n),
        ("COLD", cold_n),
    ):
        if tier_lim <= 0:
            continue
        staged = _fetch_staged_by_tier(db, tier, limit=tier_lim, exclude_ids=exclude)
        for company, *_rest in staged:
            cid = int(company.id)
            if cid in exclude:
                continue
            ids.append(cid)
            exclude.add(cid)
            if len(ids) >= lim:
                return ids[:lim]

    return ids[:lim]


def select_top_pipeline_company_ids(db: Session, *, limit: int = DEFAULT_BATCH_LIMIT) -> List[int]:
    """Pipeline-ranked company IDs — same HOT/WARM/COLD surface as /api/leads/pipeline."""
    return select_pipeline_surface_company_ids(db, limit=limit, slots_multiplier=2)


def run_pipeline_inference_batch(
    db: Session,
    *,
    limit: int = DEFAULT_BATCH_LIMIT,
    company_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Re-run inference + CRM merge for each company; returns run statistics."""
    ids = company_ids if company_ids is not None else select_top_pipeline_company_ids(db, limit=limit)
    refreshed = 0
    skipped_no_company = 0
    skipped_no_signals = 0
    skipped_not_lead = 0
    failed = 0
    errors: List[Dict[str, Any]] = []

    for cid in ids:
        company = db.query(Company).filter(Company.id == cid).first()
        if not company:
            skipped_no_company += 1
            continue

        signals = (
            db.query(Signal)
            .filter(Signal.company_id == company.id)
            .order_by(Signal.created_at.desc())
            .limit(20)
            .all()
        )
        if not signals:
            skipped_no_signals += 1
            continue

        try:
            dossier = refresh_company_inference(company, signals, db)
            if dossier.is_lead:
                refreshed += 1
            else:
                skipped_not_lead += 1
        except Exception as exc:
            failed += 1
            db.rollback()
            logger.warning(
                "Inference batch failed company_id=%s name=%r: %s",
                cid,
                getattr(company, "name", ""),
                exc,
            )
            if len(errors) < 25:
                errors.append({"company_id": cid, "name": company.name, "error": str(exc)[:200]})

    return {
        "requested": len(ids),
        "refreshed": refreshed,
        "failed": failed,
        "skipped_no_company": skipped_no_company,
        "skipped_no_signals": skipped_no_signals,
        "skipped_not_lead": skipped_not_lead,
    }


def run_pipeline_inference_batch_and_refresh_caches(*, limit: int = DEFAULT_BATCH_LIMIT) -> Dict[str, Any]:
    """Background job: batch inference then rebuild public pipeline caches."""
    from app.database import SessionLocal
    from app.services.public_surface_cache import (
        hydrate_public_surface_caches,
        refresh_all_public_surface_caches,
    )

    db = SessionLocal()
    try:
        stats = run_pipeline_inference_batch(db, limit=limit)
    finally:
        db.close()

    try:
        db2 = SessionLocal()
        try:
            refresh_all_public_surface_caches(db2)
            hydrate_public_surface_caches()
            stats["cache_refresh"] = "ok"
        finally:
            db2.close()
    except Exception as exc:
        logger.warning("Pipeline inference batch: cache refresh failed: %s", exc)
        stats["cache_refresh"] = f"failed: {exc}"

    logger.info("Pipeline inference batch complete: %s", stats)
    return stats
