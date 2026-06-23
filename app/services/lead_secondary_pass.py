"""
Secondary logic — five-pillar second pass (decoupled from primary scrapers).

  1. Missing data    — lead_gap_audit selects candidates
  2. Optimize data   — rescue passes fill/normalize fields
  3. Quality gate    — rectification (junk vs sales lead)
  4. Additional data — agent QA, signal backfill, inference dossier
  5. Opportunity rank — lead_secondary_assessment stamps sales_opportunity_rank
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.signal import Signal
from app.services.lead_filter import pick_primary_score
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
from app.services.lead_secondary_assessment import (
    PASS_VALUE_ASSESSMENT,
    run_value_assessment_pass,
)

logger = logging.getLogger(__name__)

DEFAULT_SECONDARY_LIMIT = 120
MAX_SECONDARY_LIMIT = 300

# Full pillar sweep for brand-new scraper leads (before nightly gap batch).
ONBOARDING_PASSES = [
    PASS_RECTIFY,
    PASS_WEBSITE,
    PASS_INDUSTRY,
    PASS_CRM,
    PASS_INFERENCE,
    PASS_CONTACT,
    PASS_SIGNALS,
    PASS_AGENT_QA,
]


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
    from app.services.industry_inference import effective_industry_for_lead
    from app.services.signal_text_normalize import strip_signal_html

    class _Sig:
        __slots__ = ("signal_text",)

        def __init__(self, text: str) -> None:
            self.signal_text = text

    clean_signals = [
        _Sig(strip_signal_html(getattr(s, "signal_text", "") or "")) for s in signals[:12]
    ]
    inferred = effective_industry_for_lead(company.name, company.industry, clean_signals)
    if not inferred or inferred.lower() in ("unknown", "other", "new"):
        return "failed", []
    if (company.industry or "").strip().lower() == inferred.lower():
        return "skipped", []
    company.industry = inferred
    db.add(company)
    db.commit()
    return "filled", ["industry"]


def _run_contact_rescue(company: Company, db: Session, *, use_apollo: bool = True) -> tuple[str, List[str]]:
    from app.services.lead_enrichment import enrich_company_contact_with_fallback

    before_email = any(
        (c.email or "").strip()
        for c in db.query(Contact).filter(Contact.company_id == company.id).limit(10)
    )
    meta_before = (company.crm_metadata or {}).get("outreach_email")

    out = enrich_company_contact_with_fallback(
        company, db, sleep_s=0.4, use_apollo=use_apollo
    )
    email = out.get("email")
    source = out.get("email_source")

    if out.get("contact_persisted"):
        return "filled", ["contact"]
    if email and source == "domain_inferred":
        return "filled", ["contact", "outreach_email"]
    if email and not meta_before and not before_email:
        return "filled", ["outreach_email"]
    if email or before_email or meta_before:
        return "skipped", []
    return "failed", []


def _crm_metadata_field_has_content(key: str, metadata: dict) -> bool:
    if key == "budget":
        block = metadata.get("budget")
        return isinstance(block, dict) and bool(block.get("signals") or block.get("top_amount"))
    if key == "timing":
        block = metadata.get("timing")
        return isinstance(block, dict) and bool(block.get("signals") or block.get("top_window"))
    if key in ("automation_requirements", "decision_makers"):
        value = metadata.get(key)
        return bool(value) if isinstance(value, list) else bool(value)
    return bool(metadata.get(key))


def _run_crm_rescue(company: Company, signals: List[Signal], db: Session) -> tuple[str, List[str]]:
    from app.services.crm_extractor import build_crm_metadata_dict, extract

    descriptors = extract(company, signals, db)
    metadata = build_crm_metadata_dict(descriptors)
    existing = dict(company.crm_metadata or {})
    filled: List[str] = []
    for key in ("budget", "timing", "automation_requirements", "decision_makers"):
        if _crm_metadata_field_has_content(key, metadata) and not _crm_metadata_field_has_content(key, existing):
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


def _run_signal_backfill(company: Company, db: Session, *, max_queries: int = 4) -> tuple[str, List[str]]:
    from app.scrapers.intelligence_news_scraper import IntelligenceNewsScraper

    scraper = IntelligenceNewsScraper(db=db)
    before = db.query(Signal).filter(Signal.company_id == company.id).count()
    scraper._enrich_company(company, max_queries=max(1, int(max_queries)))
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
    use_apollo: bool = True,
    signal_backfill: bool = True,
    signal_backfill_queries: int = 1,
    cooldown_hours: int = 24,
) -> Dict[str, Any]:
    """Execute applicable rescue passes for one lead; returns per-pass outcomes."""
    company, signals, contacts = _load_company_bundle(db, report.company_id)
    if not company or not signals:
        return {"company_id": report.company_id, "skipped": True, "reason": "missing company or signals"}

    outcomes: Dict[str, str] = {}
    fields_filled: List[str] = []

    passes = list(report.passes)
    if not signal_backfill:
        passes = [p for p in passes if p != PASS_SIGNALS]

    pass_runners = {
        PASS_WEBSITE: lambda: _run_website_rescue(company, db),
        PASS_INDUSTRY: lambda: _run_industry_rescue(company, signals, db),
        PASS_CONTACT: lambda: _run_contact_rescue(company, db, use_apollo=use_apollo),
        PASS_CRM: lambda: _run_crm_rescue(company, signals, db),
        PASS_INFERENCE: lambda: _run_inference_rescue(company, signals, db),
        PASS_SIGNALS: lambda: _run_signal_backfill(
            company, db, max_queries=signal_backfill_queries
        ),
        PASS_RECTIFY: lambda: _run_rectification(company, signals, db),
        PASS_AGENT_QA: lambda: _run_agent_qa(company, signals, db, use_llm=use_llm),
    }

    for pass_name in passes:
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
            if pass_name == PASS_RECTIFY and status == "failed":
                return {
                    "company_id": report.company_id,
                    "company_name": report.company_name,
                    "quarantined": True,
                    "pass_outcomes": outcomes,
                    "fields_filled": fields_filled,
                    "gaps_before": report.gaps,
                    "quality_recommendation": "quarantine",
                }
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

    # Pillar 5 — always rank opportunity value after rescue + quality passes
    assessment, opportunity_rank = run_value_assessment_pass(
        company,
        signals,
        contacts,
        pass_outcomes=outcomes,
        fields_filled=fields_filled,
    )
    stamp_ledger_entry(
        company,
        PASS_VALUE_ASSESSMENT,
        status="filled",
        fields_filled=["secondary_assessment", "sales_opportunity_rank"],
    )
    db.add(company)
    db.commit()

    quality = assessment.get("pillars", {}).get("quality_gate", {})
    return {
        "company_id": report.company_id,
        "company_name": report.company_name,
        "pass_outcomes": outcomes,
        "fields_filled": fields_filled,
        "gaps_before": report.gaps,
        "gaps_after": refreshed.gaps,
        "is_sales_lead": quality.get("is_sales_lead"),
        "quality_recommendation": quality.get("recommendation"),
        "sales_opportunity_rank": opportunity_rank,
        "lead_value_score": assessment.get("pillars", {}).get("opportunity_rank", {}).get(
            "lead_value_score"
        ),
    }


def _merge_onboarding_passes(report: LeadGapReport, *, onboarding: bool) -> LeadGapReport:
    """Ensure new scraper leads get the full secondary pillar sweep."""
    if not onboarding:
        return report
    merged = list(dict.fromkeys([*report.passes, *ONBOARDING_PASSES]))
    report.passes = merged
    return report


def run_secondary_pass_for_company_ids(
    db: Session,
    company_ids: Sequence[int],
    *,
    use_llm: bool = True,
    rescore: bool = True,
    cooldown_hours: int = 0,
    onboarding: bool = True,
) -> Dict[str, Any]:
    """
    Run secondary logic on explicit company IDs (e.g. fresh scraper discoveries).
    Skips min_score gate; uses cooldown_hours=0 by default for first-pass completeness.
    """
    ids = [int(i) for i in company_ids if i]
    if not ids:
        return {
            "candidates": 0,
            "processed": 0,
            "fields_filled_total": 0,
            "errors": 0,
            "rescore_queued": False,
            "sample": [],
        }

    results: List[Dict[str, Any]] = []
    filled_total = 0
    errors = 0

    for cid in ids:
        company, signals, contacts = _load_company_bundle(db, cid)
        if not company or not signals:
            results.append({"company_id": cid, "skipped": True, "reason": "missing company or signals"})
            continue
        score_row = pick_primary_score(company.scores)
        overall = float(score_row.overall_intent_score or 0) if score_row else 0.0
        report = audit_company_gaps(company, signals, contacts, overall_score=overall)
        report = _merge_onboarding_passes(report, onboarding=onboarding)
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
            logger.warning("Secondary onboarding failed for company %s: %s", cid, exc)
            results.append({"company_id": cid, "error": str(exc)[:200]})

    rescore_info: Dict[str, Any] = {"mode": "none", "updated": 0}
    if rescore and results:
        from app.services.lead_rescore import queue_or_inline_rescore

        rescore_info = queue_or_inline_rescore(db, ids)

    return {
        "candidates": len(ids),
        "processed": len(results),
        "fields_filled_total": filled_total,
        "errors": errors,
        "rescore": rescore_info,
        "rescore_queued": rescore_info.get("mode") == "celery",
        "onboarding": onboarding,
        "sample": results[:15],
    }


def run_secondary_pass_batch(
    db: Session,
    *,
    limit: int = DEFAULT_SECONDARY_LIMIT,
    min_score: float = 15.0,
    use_llm: bool = True,
    use_apollo: bool = True,
    signal_backfill: bool = True,
    signal_backfill_queries: int = 1,
    rescore: bool = True,
    cooldown_hours: int = 24,
    progress: bool = False,
    sales_leads_only: bool = True,
    require_gaps: Optional[Iterable[str]] = None,
    priority_tiers: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """
    Nightly rescue batch: select gap-ranked leads, run decoupled passes, optional rescore.
    """
    lim = max(1, min(int(limit), MAX_SECONDARY_LIMIT))
    if progress:
        print(f"── Secondary pass — scanning up to {min(max(lim * 8, 500), 2500)} leads for gaps…", flush=True)
    candidates = select_gap_repair_candidates(
        db,
        limit=lim,
        min_score=min_score,
        require_gaps=require_gaps,
        priority_tiers=priority_tiers,
        progress=progress,
        sales_leads_only=sales_leads_only,
    )
    if progress:
        print(f"── Candidates: {len(candidates)} — processing…", flush=True)

    results: List[Dict[str, Any]] = []
    filled_total = 0
    errors = 0

    for n, report in enumerate(candidates, start=1):
        if progress:
            print(
                f"  [{n}/{len(candidates)}] id={report.company_id} {report.company_name[:40]!r}",
                flush=True,
            )
        try:
            row = run_rescue_passes_for_company(
                db,
                report,
                use_llm=use_llm,
                use_apollo=use_apollo,
                signal_backfill=signal_backfill,
                signal_backfill_queries=signal_backfill_queries,
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

    rescore_info: Dict[str, Any] = {"mode": "none", "updated": 0}
    if rescore and results:
        from app.services.lead_rescore import queue_or_inline_rescore

        ids = [r["company_id"] for r in results if r.get("company_id")]
        rescore_info = queue_or_inline_rescore(db, ids)

    return {
        "candidates": len(candidates),
        "processed": len(results),
        "fields_filled_total": filled_total,
        "errors": errors,
        "rescore": rescore_info,
        "rescore_queued": rescore_info.get("mode") == "celery",
        "sample": results[:15],
    }


def run_secondary_pass_batch_and_refresh_caches(
    *,
    limit: int = DEFAULT_SECONDARY_LIMIT,
    min_score: float = 15.0,
    use_llm: bool = True,
    rescore: bool = True,
    sales_leads_only: bool = True,
) -> Dict[str, Any]:
    """Background job: secondary rescue batch then full pipeline cache rebuild."""
    from app.database import SessionLocal
    from app.services.public_surface_cache import (
        hydrate_public_surface_caches,
        refresh_pipeline_surface_caches,
    )

    db = SessionLocal()
    try:
        stats = run_secondary_pass_batch(
            db,
            limit=limit,
            min_score=min_score,
            use_llm=use_llm,
            rescore=rescore,
            sales_leads_only=sales_leads_only,
        )
    finally:
        db.close()

    try:
        db2 = SessionLocal()
        try:
            refresh_pipeline_surface_caches(db2, include_humanoid_report=False)
            db2.commit()
            hydrate_public_surface_caches()
            stats["cache_refresh"] = "ok"
        finally:
            db2.close()
    except Exception as exc:
        logger.warning("Secondary pass pipeline cache refresh failed: %s", exc)
        stats["cache_refresh"] = f"failed: {exc}"

    logger.info("Secondary pass batch complete: %s", stats)
    return stats
