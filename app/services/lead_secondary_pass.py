"""
Secondary logic — decoupled rescue passes for missing sales-lead fields.

Primary ingestion (scrapers) writes companies + signals quickly. This module runs
afterward (scheduled batch) to backfill website, industry, contacts, CRM descriptors,
inference dossiers, and agent QA — analogous to Pythh's batch-platform-daily.yml.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.signal import Signal
from app.services.lead_gap_audit import (
    PASS_AGENT_QA,
    PASS_CONTACT,
    PASS_CRM,
    PASS_INFERENCE,
    PASS_INDUSTRY,
    PASS_RECTIFY,
    PASS_SIGNALS,
    PASS_WEBSITE,
    LeadGapReport,
    audit_company_gaps,
    ledger_cooldown_ok,
    select_gap_repair_candidates,
    stamp_ledger_entry,
)

logger = logging.getLogger(__name__)

DEFAULT_SECONDARY_LIMIT = 120
MAX_SECONDARY_LIMIT = 300


def _load_company_bundle(db: Session, company_id: int):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return None, [], []
    signals = (
        db.query(Signal)
        .filter(Signal.company_id == company.id)
        .order_by(Signal.created_at.desc())
        .limit(20)
        .all()
    )
    contacts = db.query(Contact).filter(Contact.company_id == company.id).limit(10).all()
    return company, signals, contacts


def _run_website_rescue(company: Company, db: Session) -> tuple[str, List[str]]:
    from app.services.lead_enrichment import enrich_company_website

    if company.website and str(company.website).strip():
        return "skipped", []
    found = enrich_company_website(company, sleep_s=0.5)
    db.add(company)
    db.commit()
    if found:
        return "filled", ["website"]
    return "failed", []


def _run_industry_rescue(company: Company, signals: List[Signal], db: Session) -> tuple[str, List[str]]:
    from app.services.industry_inference import infer_industry_from_text

    text = " ".join(
        filter(
            None,
            [company.name or ""]
            + [getattr(s, "signal_text", "") or "" for s in signals[:12]],
        )
    )
    inferred = infer_industry_from_text(text)
    if not inferred or inferred.lower() in ("unknown", "other"):
        return "failed", []
    if (company.industry or "").strip().lower() == inferred.lower():
        return "skipped", []
    company.industry = inferred
    db.add(company)
    db.commit()
    return "filled", ["industry"]


def _run_contact_rescue(company: Company, db: Session) -> tuple[str, List[str]]:
    from app.services.lead_enrichment import enrich_company_and_contact

    before = db.query(Contact).filter(Contact.company_id == company.id).count()
    enrich_company_and_contact(company, acct=None, sleep_s=0.4, use_apollo=True)
    db.add(company)
    db.commit()
    after = db.query(Contact).filter(Contact.company_id == company.id).count()
    if after > before:
        return "filled", ["contact"]
    if any(
        (c.email or "").strip()
        for c in db.query(Contact).filter(Contact.company_id == company.id).limit(5)
    ):
        return "skipped", []
    return "failed", []


def _run_crm_rescue(company: Company, signals: List[Signal], db: Session) -> tuple[str, List[str]]:
    from app.services.crm_extractor import build_crm_metadata_dict, extract

    descriptors = extract(company, signals, db)
    metadata = build_crm_metadata_dict(descriptors)
    existing = dict(company.crm_metadata or {})
    filled: List[str] = []
    for key in ("budget", "timing", "automation_requirements", "decision_makers"):
        if metadata.get(key) and not existing.get(key):
            filled.append(key)
    existing.update(metadata)
    company.crm_metadata = existing
    db.add(company)
    db.commit()
    return ("filled" if filled else "skipped"), filled


def _run_inference_rescue(company: Company, signals: List[Signal], db: Session) -> tuple[str, List[str]]:
    from app.services.lead_inference_engine import refresh_company_inference

    dossier = refresh_company_inference(company, signals, db)
    if dossier.is_lead and dossier.to_dict().get("specific_problem"):
        return "filled", ["lead_inference"]
    return "failed", []


def _run_signal_backfill(company: Company, db: Session) -> tuple[str, List[str]]:
    from app.scrapers.intelligence_news_scraper import IntelligenceNewsScraper

    scraper = IntelligenceNewsScraper(db=db)
    before = db.query(Signal).filter(Signal.company_id == company.id).count()
    scraper._enrich_company(company)
    after = db.query(Signal).filter(Signal.company_id == company.id).count()
    if after > before:
        return "filled", ["signals"]
    return "skipped", []


def _run_rectification(company: Company, signals: List[Signal], db: Session) -> tuple[str, List[str]]:
    from app.services.rectifier import quarantine, validate

    result = validate(company, signals)
    if not result.passed:
        quarantine(company, db, reason=result.reason)
        return "failed", []
    stamp_ledger_entry(company, PASS_RECTIFY, status="passed", detail=result.reason or "ok")
    db.add(company)
    db.commit()
    return "passed", ["rectification"]


def _run_agent_qa(company: Company, signals: List[Signal], db: Session, *, use_llm: bool) -> tuple[str, List[str]]:
    from app.services.lead_enrichment_agent import enrich_lead_with_agent

    row = enrich_lead_with_agent(company, signals, db, use_llm=use_llm, update_global_ontology=False)
    if row.inference_refreshed or row.rich_facts:
        return "filled", ["agent_enrichment"]
    return "skipped", []


def run_rescue_passes_for_company(
    db: Session,
    report: LeadGapReport,
    *,
    use_llm: bool = True,
    cooldown_hours: int = 24,
) -> Dict[str, Any]:
    """Execute applicable rescue passes for one lead; returns per-pass outcomes."""
    company, signals, contacts = _load_company_bundle(db, report.company_id)
    if not company or not signals:
        return {"company_id": report.company_id, "skipped": True, "reason": "missing company or signals"}

    outcomes: Dict[str, str] = {}
    fields_filled: List[str] = []

    pass_runners = {
        PASS_WEBSITE: lambda: _run_website_rescue(company, db),
        PASS_INDUSTRY: lambda: _run_industry_rescue(company, signals, db),
        PASS_CONTACT: lambda: _run_contact_rescue(company, db),
        PASS_CRM: lambda: _run_crm_rescue(company, signals, db),
        PASS_INFERENCE: lambda: _run_inference_rescue(company, signals, db),
        PASS_SIGNALS: lambda: _run_signal_backfill(company, db),
        PASS_RECTIFY: lambda: _run_rectification(company, signals, db),
        PASS_AGENT_QA: lambda: _run_agent_qa(company, signals, db, use_llm=use_llm),
    }

    for pass_name in report.passes:
        if pass_name not in pass_runners:
            continue
        if not ledger_cooldown_ok(company, pass_name, cooldown_hours=cooldown_hours):
            outcomes[pass_name] = "cooldown"
            continue
        try:
            status, filled = pass_runners[pass_name]()
            outcomes[pass_name] = status
            fields_filled.extend(filled)
            if pass_name != PASS_RECTIFY:
                stamp_ledger_entry(
                    company,
                    pass_name,
                    status=status,
                    fields_filled=filled,
                )
                db.add(company)
                db.commit()
            # Refresh bundle after mutating passes
            company, signals, contacts = _load_company_bundle(db, report.company_id)
            if not company:
                break
        except Exception as exc:
            db.rollback()
            logger.warning(
                "Secondary pass %s failed for company %s: %s",
                pass_name,
                report.company_id,
                exc,
            )
            stamp_ledger_entry(company, pass_name, status="failed", detail=str(exc)[:200])
            db.add(company)
            db.commit()
            outcomes[pass_name] = "error"

    refreshed = audit_company_gaps(
        company,
        signals,
        contacts,
        overall_score=report.overall_score,
    )
    return {
        "company_id": report.company_id,
        "company_name": report.company_name,
        "pass_outcomes": outcomes,
        "fields_filled": fields_filled,
        "gaps_before": report.gaps,
        "gaps_after": refreshed.gaps,
    }


def run_secondary_pass_batch(
    db: Session,
    *,
    limit: int = DEFAULT_SECONDARY_LIMIT,
    min_score: float = 15.0,
    use_llm: bool = True,
    rescore: bool = True,
    cooldown_hours: int = 24,
) -> Dict[str, Any]:
    """
    Nightly rescue batch: select gap-ranked leads, run decoupled passes, optional rescore.
    """
    lim = max(1, min(int(limit), MAX_SECONDARY_LIMIT))
    candidates = select_gap_repair_candidates(db, limit=lim, min_score=min_score)

    results: List[Dict[str, Any]] = []
    filled_total = 0
    errors = 0

    for report in candidates:
        try:
            row = run_rescue_passes_for_company(
                db,
                report,
                use_llm=use_llm,
                cooldown_hours=cooldown_hours,
            )
            results.append(row)
            filled_total += len(row.get("fields_filled") or [])
        except Exception as exc:
            errors += 1
            db.rollback()
            logger.warning("Secondary batch company %s failed: %s", report.company_id, exc)
            if len(results) < 30:
                results.append({"company_id": report.company_id, "error": str(exc)[:200]})

    rescored = 0
    if rescore and results:
        try:
            from worker.celery_worker import celery_app

            celery_app.send_task("worker.tasks.rescore_all_companies_task")
            rescored = -1  # queued
        except Exception as exc:
            logger.warning("Secondary batch rescore queue failed: %s", exc)

    return {
        "candidates": len(candidates),
        "processed": len(results),
        "fields_filled_total": filled_total,
        "errors": errors,
        "rescore_queued": rescored == -1,
        "sample": results[:15],
    }
