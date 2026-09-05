"""Hermes lookups via the local lead/work inference engines (no paid LLM)."""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.hermes_job_evidence import humanize_overlay_rationale, is_real_vendor_name

logger = logging.getLogger(__name__)

_LABOR_HIGH = ("labor", "shortage", "staffing", "turnover", "hire", "overtime")
_FACILITY_HINTS = ("warehouse", "fulfillment", "distribution", "facility", "plant", "factory", "dc ")


def _signal_context(company) -> tuple[str, list[str], Optional[str]]:
    texts: list[str] = []
    types: list[str] = []
    article: Optional[str] = None
    for sig in list(getattr(company, "signals", None) or [])[:12]:
        chunk = (
            getattr(sig, "signal_text", None)
            or getattr(sig, "ingestion_raw_text", None)
            or ""
        )[:2000]
        if chunk:
            texts.append(chunk)
            types.append(getattr(sig, "signal_type", None) or "news")
        url = getattr(sig, "source_url", None)
        if url and not article:
            article = str(url)
    return "\n".join(texts)[:4000], types, article


def overlay_from_dossier(dossier: Any, *, work_summary: Optional[dict] = None) -> dict[str, Any]:
    """Map a lead-inference dossier onto a Hermes qualify overlay."""
    why = list(getattr(dossier, "why_lead", None) or [])
    problem = getattr(dossier, "specific_problem", None) or ""
    robots = list(getattr(dossier, "robot_categories", None) or [])
    blob = " ".join([problem, " ".join(why), " ".join(robots)]).lower()
    labor = "high" if any(w in blob for w in _LABOR_HIGH) else (
        "medium" if any(w in blob for w in ("throughput", "capacity", "warehouse")) else "unknown"
    )
    facility = "named_site" if any(w in blob for w in _FACILITY_HINTS) else "unspecified"
    intent = getattr(dossier, "intent_score", None)
    if intent is None:
        intent = getattr(dossier, "lead_value_score", 0) or 0
    try:
        fit = int(round(max(0.0, min(100.0, float(intent)))))
    except (TypeError, ValueError):
        fit = 0
    reasons = ([problem] if problem else []) + why[:4]
    family = (work_summary or {}).get("workflow_family")
    if family and str(family).strip().lower() != "unknown":
        reasons.append(f"work family: {family}")
    rationale = humanize_overlay_rationale("; ".join(r for r in reasons if r))
    vendors = [
        {"vendor": c, "model": None, "source": "lead_inference_engine"}
        for c in robots[:6]
        if is_real_vendor_name(str(c))
    ]
    blockers: list[str] = []
    if not getattr(dossier, "is_lead", True):
        blockers.append(getattr(dossier, "junk_reason", None) or "not_a_lead")
    return {
        "automation_fit": fit,
        "labor_intensity": labor,
        "facility_clarity": facility,
        "blockers": blockers,
        "rationale": rationale[:2000],
        "vendor_shortlist": vendors,
        "engine": "lead_inference_engine",
        "work": work_summary,
    }


def infer_qualify_for_company(
    db: Session,
    company,
    *,
    hermes_run_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Qualify one company with lead_inference_engine + work reconstruction."""
    from app.services.hermes_intelligence_ingest import apply_qualify_overlay
    from app.services.lead_inference_engine import evaluate_lead_candidate, persist_lead_inference
    from app.services.work_unit_reconstruct import reconstruct_work_from_text, work_unit_summary

    blob, sig_types, article = _signal_context(company)
    context = blob or (company.name or "")
    dossier = evaluate_lead_candidate(
        company_name=company.name or "",
        context_text=context,
        article_url=article,
        signal_types=sig_types or None,
        industry=getattr(company, "industry", None),
        employee_estimate=getattr(company, "employee_estimate", None),
        is_new_company=False,
    )
    work_summary = None
    try:
        work = reconstruct_work_from_text(context, job_title=None)
        work_summary = work_unit_summary(work)
    except Exception:
        logger.debug("work reconstruct skipped for company %s", getattr(company, "id", None), exc_info=True)

    overlay = overlay_from_dossier(dossier, work_summary=work_summary)
    if not dry_run:
        persist_lead_inference(
            company,
            dossier,
            db,
            signal_blob=blob,
            signal_types=sig_types or None,
        )
    applied = apply_qualify_overlay(
        db,
        company_id=int(company.id),
        automation_fit=overlay["automation_fit"],
        labor_intensity=overlay["labor_intensity"],
        facility_clarity=overlay["facility_clarity"],
        blockers=overlay["blockers"],
        rationale=overlay["rationale"],
        vendor_shortlist=overlay["vendor_shortlist"],
        hermes_run_id=hermes_run_id,
        dry_run=dry_run,
    )
    applied["engine"] = "lead_inference_engine"
    applied["work"] = work_summary
    applied["is_lead"] = bool(getattr(dossier, "is_lead", False))
    applied["tier"] = getattr(dossier, "tier", None)
    return applied


def infer_qualify_companies(
    db: Session,
    *,
    company_ids: Optional[list[int]] = None,
    limit: int = 12,
    hermes_run_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    from app.models.company import Company

    ids = [int(i) for i in (company_ids or []) if i is not None]
    if ids:
        rows = db.query(Company).filter(Company.id.in_(ids)).all()
    else:
        rows = db.query(Company).order_by(Company.id.desc()).limit(int(limit)).all()

    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for company in rows:
        try:
            results.append(
                infer_qualify_for_company(
                    db,
                    company,
                    hermes_run_id=hermes_run_id,
                    dry_run=dry_run,
                )
            )
        except Exception as exc:
            logger.warning("infer-qualify company %s failed: %s", company.id, exc)
            errors.append({"company_id": company.id, "error": str(exc)[:300]})
    return {
        "ok": len(errors) == 0,
        "engine": "lead_inference_engine",
        "paid_llm": False,
        "accepted": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "hermes_run_id": hermes_run_id,
        "dry_run": dry_run,
        "doc": "docs/hermes_intelligence_bridge.md",
    }
