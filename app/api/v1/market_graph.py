"""Market graph loop status + snapshot for product/admin surfaces."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.admin_auth import _reject_misleading_admin_key, get_admin_key, get_cron_token
from app.database import get_db
from app.services.market_graph_loop import (
    get_market_graph_loop_status,
    loop_health_from_snapshot,
    read_market_graph_snapshot,
    run_market_graph_loop,
)
from app.services.primitive_match import work_robot_match_score
from app.services.robot_primitives import primitives_from_vendor_text
from app.services.work_unit_reconstruct import (
    reconstruct_work_from_text,
    work_unit_summary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-graph", tags=["v1-market-graph"])


class ReconstructBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    job_title: Optional[str] = None
    robot_categories: list[str] = Field(default_factory=list)
    manufacturer_name: Optional[str] = None


class DeploymentClaimIn(BaseModel):
    """One public deployment claim from Hermes (or another crawler)."""

    text: str = Field(..., min_length=20, max_length=20000)
    source_url: Optional[str] = Field(None, max_length=2000)
    source_type: str = Field("oem_press_release", max_length=64)
    source_date: Optional[str] = Field(None, max_length=32)
    vendor_name: Optional[str] = Field(None, max_length=240)
    robot_model: Optional[str] = Field(None, max_length=240)
    customer_name: Optional[str] = Field(None, max_length=240)
    facility_name: Optional[str] = Field(None, max_length=240)
    industry: Optional[str] = Field(None, max_length=120)
    work_type: Optional[str] = Field(None, max_length=120)
    workflow: dict[str, Any] = Field(default_factory=dict)


class DeploymentIngestBody(BaseModel):
    claims: list[DeploymentClaimIn] = Field(..., min_length=1, max_length=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


class JobSignalIn(BaseModel):
    job_title: str = Field(..., min_length=2, max_length=240)
    employer: str = Field(..., min_length=1, max_length=240)
    excerpt: str = Field(..., min_length=20, max_length=20000)
    source_url: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=240)
    source_date: Optional[str] = Field(None, max_length=32)
    industry: Optional[str] = Field(None, max_length=120)


class JobSignalsIngestBody(BaseModel):
    jobs: list[JobSignalIn] = Field(..., min_length=1, max_length=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


class QualifyOverlayIn(BaseModel):
    company_id: Optional[int] = None
    signal_url: Optional[str] = Field(None, max_length=2000)
    automation_fit: int = Field(..., ge=0, le=100)
    labor_intensity: Optional[str] = Field(None, max_length=64)
    facility_clarity: Optional[str] = Field(None, max_length=64)
    blockers: list[str] = Field(default_factory=list)
    rationale: Optional[str] = Field(None, max_length=2000)
    vendor_shortlist: list[dict[str, Any]] = Field(default_factory=list)


class QualifyOverlayBody(BaseModel):
    overlays: list[QualifyOverlayIn] = Field(..., min_length=1, max_length=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


class ContactIn(BaseModel):
    company_id: int
    name: str = Field(..., min_length=2, max_length=240)
    title: Optional[str] = Field(None, max_length=240)
    linkedin_url: Optional[str] = Field(None, max_length=2000)
    email: Optional[str] = Field(None, max_length=320)
    source_url: Optional[str] = Field(None, max_length=2000)
    confidence: int = Field(50, ge=0, le=100)


class ContactsIngestBody(BaseModel):
    contacts: list[ContactIn] = Field(..., min_length=1, max_length=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


class VendorNewsIn(BaseModel):
    entity_name: str = Field(..., min_length=1, max_length=240)
    text: str = Field(..., min_length=20, max_length=20000)
    news_type: str = Field("product", max_length=64)
    entity_kind: str = Field("vendor", max_length=32)
    source_url: Optional[str] = Field(None, max_length=2000)
    source_date: Optional[str] = Field(None, max_length=32)
    title: Optional[str] = Field(None, max_length=480)
    company_id: Optional[int] = None
    confidence: float = Field(0.5, ge=0.0, le=1.0)


class VendorNewsIngestBody(BaseModel):
    items: list[VendorNewsIn] = Field(..., min_length=1, max_length=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


class BuyingWindowOverlayIn(BaseModel):
    company_id: int
    urgency_0_100: int = Field(..., ge=0, le=100)
    window_label: Optional[str] = Field(None, max_length=160)
    factors: list[dict[str, Any]] = Field(default_factory=list)
    cal_hint: Optional[str] = Field(None, max_length=280)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class BuyingWindowOverlayBody(BaseModel):
    overlays: list[BuyingWindowOverlayIn] = Field(..., min_length=1, max_length=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


class VideoEvidenceIn(BaseModel):
    company_id: Optional[int] = None
    company_name: Optional[str] = Field(None, max_length=240)
    source_url: str = Field(..., min_length=8, max_length=2000)
    platform: Optional[str] = Field(None, max_length=64)
    evidence_kind: Optional[str] = Field(None, max_length=64)
    title: Optional[str] = Field(None, max_length=240)
    excerpt: Optional[str] = Field(None, max_length=2000)
    workflow_hint: Optional[str] = Field(None, max_length=160)
    robot_visible: Optional[str] = Field(None, max_length=120)
    facility_hint: Optional[str] = Field(None, max_length=160)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    published_at: Optional[str] = Field(None, max_length=32)


class VideoEvidenceIngestBody(BaseModel):
    videos: list[VideoEvidenceIn] = Field(..., min_length=1, max_length=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


class VendorVideoEvidenceIn(BaseModel):
    vendor_name: str = Field(..., min_length=2, max_length=240)
    source_url: str = Field(..., min_length=8, max_length=2000)
    platform: Optional[str] = Field(None, max_length=64)
    evidence_kind: Optional[str] = Field(None, max_length=64)
    title: Optional[str] = Field(None, max_length=240)
    robot_model: Optional[str] = Field(None, max_length=120)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class VendorVideoEvidenceIngestBody(BaseModel):
    videos: list[VendorVideoEvidenceIn] = Field(..., min_length=1, max_length=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


HERMES_INGEST_RETIRED_DETAIL = (
    "Hermes ingest retired. Jobs uses POST /api/robot-job-match."
)


def hermes_ingest_enabled() -> bool:
    return os.getenv("HERMES_INGEST_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _require_ingest_auth(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    token: str = Query("", description="SCRAPER_CRON_TOKEN alternative"),
) -> dict[str, str]:
    admin = get_admin_key()
    cron = get_cron_token()
    ok_admin = bool(admin and x_admin_key and x_admin_key.strip() == admin)
    ok_cron = bool(cron and token.strip() == cron)
    if not ok_admin and not ok_cron:
        if x_admin_key:
            _reject_misleading_admin_key(x_admin_key)
        raise HTTPException(status_code=403, detail="Invalid X-Admin-Key or token")
    return {"auth": "admin_key" if ok_admin else "cron_token"}


def _require_hermes_ingest(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    token: str = Query("", description="SCRAPER_CRON_TOKEN alternative"),
) -> dict[str, str]:
    """Hermes ingest is retired. Refuse unless HERMES_INGEST_ENABLED=1."""
    if not hermes_ingest_enabled():
        raise HTTPException(status_code=410, detail=HERMES_INGEST_RETIRED_DETAIL)
    return _require_ingest_auth(x_admin_key, token)


@router.get("/status")
def market_graph_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    snap = read_market_graph_snapshot(db) or {}
    loop = loop_health_from_snapshot(snap)
    web_thread = get_market_graph_loop_status()
    return {
        "loop": loop,
        # web-process RAM only — do not treat running/last_run as the worker
        "scheduler": {
            **web_thread,
            "source": "serving_process_memory",
            "healthy": loop.get("healthy"),
            "last_completed_at": loop.get("last_completed_at"),
        },
        "snapshot": {
            "generated_at": snap.get("generated_at"),
            "status": snap.get("status"),
            "tension_count": snap.get("tension_count"),
            "match_count": snap.get("match_count"),
            "refresh_queue_count": snap.get("refresh_queue_count"),
            "demand_sampled": snap.get("demand_sampled"),
            "vendors_sampled": snap.get("vendors_sampled"),
        },
    }


@router.get("/tensions")
def market_graph_tensions(
    limit: int = Query(12, ge=1, le=40),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    snap = read_market_graph_snapshot(db) or {}
    tensions = list(snap.get("tensions") or [])[:limit]
    return {
        "generated_at": snap.get("generated_at"),
        "count": len(tensions),
        "tensions": tensions,
    }


@router.get("/matches")
def market_graph_matches(
    limit: int = Query(20, ge=1, le=80),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    snap = read_market_graph_snapshot(db) or {}
    matches = list(snap.get("matches") or [])[:limit]
    return {
        "generated_at": snap.get("generated_at"),
        "count": len(matches),
        "matches": matches,
    }


@router.get("/work-units")
def market_graph_work_units(
    limit: int = Query(20, ge=1, le=60),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Latest reconstructed WORK units from the market-graph snapshot."""
    snap = read_market_graph_snapshot(db) or {}
    units = list(snap.get("work_units") or [])[:limit]
    return {
        "generated_at": snap.get("generated_at"),
        "count": len(units),
        "spine": "ontology/primitives.v1.json",
        "work_units": units,
    }


@router.post("/reconstruct")
def market_graph_reconstruct(body: ReconstructBody) -> dict[str, Any]:
    """
    Job→Robot dry-run: reconstruct WORK from text and optionally score vs robot categories.
    """
    work = reconstruct_work_from_text(body.text, job_title=body.job_title)
    caps = primitives_from_vendor_text(
        robot_categories=body.robot_categories,
        name=body.manufacturer_name,
    )
    score, detail = work_robot_match_score(
        required_primitives=work.required_primitives,
        supported_primitives=caps["supported_primitives"],
        workflow_family=work.workflow_family,
        industry_aligned=False,
        buyer_tier="HOT",
        buyer_score=80.0,
    )
    return {
        "traversal": "job_to_robot",
        "spine": "ontology/primitives.v1.json",
        "work": work_unit_summary(work),
        "robot_capability": caps,
        "match": {
            "match_score": score,
            **detail,
        },
    }


@router.get("/deployment-evidence")
def market_graph_deployment_evidence(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List public Deployment Evidence events (not live telemetry)."""
    try:
        from app.models.deployment_evidence import DeploymentEvent
        from app.services.deployment_evidence_engine import commercial_evidence_score

        rows = (
            db.query(DeploymentEvent)
            .order_by(DeploymentEvent.confidence.desc(), DeploymentEvent.updated_at.desc())
            .limit(limit)
            .all()
        )
        events = [
            {
                "deployment_id": r.deployment_id,
                "vendor": r.vendor_name,
                "robot": r.robot_model,
                "customer": r.customer_name,
                "facility": r.facility_name,
                "industry": r.industry,
                "work_type": r.work_type,
                "workflow": r.workflow,
                "deployment_stage": r.deployment_stage,
                "evidence_level": r.evidence_level,
                "confidence": r.confidence,
                "performed_primitives": r.performed_primitives,
                "robots_announced": r.robots_announced,
                "robots_live": r.robots_live,
            }
            for r in rows
        ]
        return {
            "count": len(events),
            "events": events,
            "commercial_evidence": commercial_evidence_score(events),
            "doc": "docs/deployment_evidence_engine.md",
        }
    except Exception as exc:
        return {"count": 0, "events": [], "error": str(exc)[:240]}


@router.post("/deployment-evidence/ingest")
def market_graph_deployment_evidence_ingest(
    body: DeploymentIngestBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """
    Hermes → RFR bridge: ingest public deployment claims into Deployment Evidence.

    Auth: header ``X-Admin-Key: <ADMIN_KEY>`` or ``?token=<SCRAPER_CRON_TOKEN>``.
    """
    from app.services.deployment_evidence_engine import (
        parse_deployment_claim,
        persist_deployment_event,
    )

    accepted: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, claim in enumerate(body.claims):
        try:
            parsed = parse_deployment_claim(
                claim.text,
                source_url=claim.source_url,
                source_type=claim.source_type,
                vendor_name=claim.vendor_name,
                robot_model=claim.robot_model,
                customer_name=claim.customer_name,
                facility_name=claim.facility_name,
                industry=claim.industry,
                work_type=claim.work_type,
                workflow=claim.workflow or {},
                source_date=claim.source_date,
            )
            if body.dry_run:
                accepted.append({"index": idx, "dry_run": True, **parsed})
                continue
            row = persist_deployment_event(db, parsed)
            accepted.append(
                {
                    "index": idx,
                    "deployment_id": parsed.get("deployment_id"),
                    "deployment_stage": parsed.get("deployment_stage"),
                    "evidence_level": parsed.get("evidence_level"),
                    "confidence": parsed.get("confidence"),
                    "db_id": str(row.id) if row is not None else None,
                }
            )
        except Exception as exc:
            logger.warning("deployment ingest claim %s failed: %s", idx, exc)
            errors.append({"index": idx, "error": str(exc)[:300]})

    if not body.dry_run and accepted:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc

    return {
        "ok": len(errors) == 0,
        "hermes_run_id": body.hermes_run_id,
        "accepted": len(accepted),
        "failed": len(errors),
        "results": accepted,
        "errors": errors,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_deployment_bridge.md",
    }


@router.post("/job-signals/ingest")
def market_graph_job_signals_ingest(
    body: JobSignalsIngestBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """Hermes → RFR: open job orders correlated to robot automation."""
    from app.services.hermes_intelligence_ingest import ingest_job_signal

    accepted: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, job in enumerate(body.jobs):
        try:
            result = ingest_job_signal(
                db,
                job_title=job.job_title,
                employer=job.employer,
                excerpt=job.excerpt,
                source_url=job.source_url,
                location=job.location,
                source_date=job.source_date,
                industry=job.industry,
                dry_run=body.dry_run,
            )
            accepted.append({"index": idx, **result})
        except Exception as exc:
            logger.warning("job-signal ingest %s failed: %s", idx, exc)
            errors.append({"index": idx, "error": str(exc)[:300]})

    if not body.dry_run and accepted:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc

    return {
        "ok": len(errors) == 0,
        "hermes_run_id": body.hermes_run_id,
        "accepted": len(accepted),
        "failed": len(errors),
        "results": accepted,
        "errors": errors,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_intelligence_bridge.md",
    }


@router.post("/qualify-overlay")
def market_graph_qualify_overlay(
    body: QualifyOverlayBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """Hermes qualification overlay (not customer-confirmed CRM truth)."""
    from app.services.hermes_intelligence_ingest import apply_qualify_overlay

    accepted: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, item in enumerate(body.overlays):
        try:
            if item.company_id is None and not item.signal_url:
                raise ValueError("company_id or signal_url required")
            result = apply_qualify_overlay(
                db,
                company_id=item.company_id,
                signal_url=item.signal_url,
                automation_fit=item.automation_fit,
                labor_intensity=item.labor_intensity,
                facility_clarity=item.facility_clarity,
                blockers=item.blockers,
                rationale=item.rationale,
                vendor_shortlist=item.vendor_shortlist,
                hermes_run_id=body.hermes_run_id,
                dry_run=body.dry_run,
            )
            accepted.append({"index": idx, **result})
        except Exception as exc:
            logger.warning("qualify-overlay %s failed: %s", idx, exc)
            errors.append({"index": idx, "error": str(exc)[:300]})

    if not body.dry_run and accepted:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc

    return {
        "ok": len(errors) == 0,
        "hermes_run_id": body.hermes_run_id,
        "accepted": len(accepted),
        "failed": len(errors),
        "results": accepted,
        "errors": errors,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_intelligence_bridge.md",
    }


class InferQualifyBody(BaseModel):
    company_ids: list[int] = Field(default_factory=list)
    limit: int = Field(12, ge=1, le=40)
    hermes_run_id: Optional[str] = Field(None, max_length=120)
    dry_run: bool = False


@router.post("/infer-qualify")
def market_graph_infer_qualify(
    body: InferQualifyBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """Qualify pipeline companies with the local inference engine (no OpenAI/Anthropic)."""
    from app.services.hermes_local_inference import infer_qualify_companies

    payload = infer_qualify_companies(
        db,
        company_ids=body.company_ids,
        limit=body.limit,
        hermes_run_id=body.hermes_run_id,
        dry_run=body.dry_run,
    )
    if not body.dry_run and payload.get("accepted"):
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc
    payload["auth"] = _auth.get("auth")
    return payload


class DailyDigestSendBody(BaseModel):
    force: bool = False
    period_hours: int = Field(24, ge=1, le=168)


@router.post("/daily-digest-send")
def market_graph_daily_digest_send(
    body: DailyDigestSendBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_ingest_auth),
) -> dict[str, Any]:
    """Send the operator daily digest via Resend. No paid LLM / AI Gateway."""
    from app.services.cal_daily_digest import send_cal_daily_digest

    result = send_cal_daily_digest(
        db, period_hours=body.period_hours, force=body.force
    )
    result["engine"] = "local_inference"
    result["paid_llm"] = False
    result["auth"] = _auth.get("auth")
    result["doc"] = "docs/skills/rfr-daily-email-digest.SKILL.md"
    return result


@router.post("/contacts/ingest")
def market_graph_contacts_ingest(
    body: ContactsIngestBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """Hermes → RFR: public-sourced decision-maker contacts."""
    from app.services.hermes_intelligence_ingest import ingest_contact

    accepted: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    skipped = 0
    for idx, c in enumerate(body.contacts):
        try:
            result = ingest_contact(
                db,
                company_id=c.company_id,
                name=c.name,
                title=c.title,
                linkedin_url=c.linkedin_url,
                email=c.email,
                source_url=c.source_url,
                confidence=c.confidence,
                dry_run=body.dry_run,
            )
            if result.get("skipped"):
                skipped += 1
            accepted.append({"index": idx, **result})
        except Exception as exc:
            logger.warning("contacts ingest %s failed: %s", idx, exc)
            errors.append({"index": idx, "error": str(exc)[:300]})

    if not body.dry_run and any(not r.get("skipped") for r in accepted):
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc

    return {
        "ok": len(errors) == 0,
        "hermes_run_id": body.hermes_run_id,
        "accepted": len(accepted) - skipped,
        "skipped": skipped,
        "failed": len(errors),
        "results": accepted,
        "errors": errors,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_intelligence_bridge.md",
    }


@router.post("/vendor-news/ingest")
def market_graph_vendor_news_ingest(
    body: VendorNewsIngestBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """Hermes → RFR: vendor capability/pricing/model news + customer signals."""
    from app.services.hermes_intelligence_ingest import ingest_vendor_news

    accepted: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, item in enumerate(body.items):
        try:
            result = ingest_vendor_news(
                db,
                entity_name=item.entity_name,
                text=item.text,
                news_type=item.news_type,
                entity_kind=item.entity_kind,
                source_url=item.source_url,
                source_date=item.source_date,
                title=item.title,
                company_id=item.company_id,
                confidence=item.confidence,
                hermes_run_id=body.hermes_run_id,
                dry_run=body.dry_run,
            )
            accepted.append({"index": idx, **result})
        except Exception as exc:
            logger.warning("vendor-news ingest %s failed: %s", idx, exc)
            errors.append({"index": idx, "error": str(exc)[:300]})

    if not body.dry_run and accepted:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc

    return {
        "ok": len(errors) == 0,
        "hermes_run_id": body.hermes_run_id,
        "accepted": len(accepted),
        "failed": len(errors),
        "results": accepted,
        "errors": errors,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_intelligence_bridge.md",
    }


@router.get("/vendor-news")
def market_graph_vendor_news_list(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        from app.models.vendor_news import VendorNewsItem

        rows = (
            db.query(VendorNewsItem)
            .order_by(VendorNewsItem.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "count": len(rows),
            "items": [
                {
                    "news_id": r.news_id,
                    "news_type": r.news_type,
                    "entity_kind": r.entity_kind,
                    "entity_name": r.entity_name,
                    "company_id": r.company_id,
                    "title": r.title,
                    "source_url": r.source_url,
                    "source_date": r.source_date,
                    "confidence": r.confidence,
                }
                for r in rows
            ],
            "doc": "docs/hermes_intelligence_bridge.md",
        }
    except Exception as exc:
        return {"count": 0, "items": [], "error": str(exc)[:240]}


@router.post("/buying-window-overlay")
def market_graph_buying_window_overlay(
    body: BuyingWindowOverlayBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """Hermes buying-window overlay (timing urgency ≠ automation fit)."""
    from app.services.hermes_intelligence_ingest import apply_buying_window_overlay

    accepted: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, item in enumerate(body.overlays):
        try:
            result = apply_buying_window_overlay(
                db,
                company_id=item.company_id,
                urgency_0_100=item.urgency_0_100,
                window_label=item.window_label,
                factors=item.factors,
                cal_hint=item.cal_hint,
                confidence=item.confidence,
                hermes_run_id=body.hermes_run_id,
                dry_run=body.dry_run,
            )
            accepted.append({"index": idx, **result})
        except Exception as exc:
            logger.warning("buying-window-overlay %s failed: %s", idx, exc)
            errors.append({"index": idx, "error": str(exc)[:300]})

    if not body.dry_run and accepted:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc

    return {
        "ok": len(errors) == 0,
        "hermes_run_id": body.hermes_run_id,
        "accepted": len(accepted),
        "failed": len(errors),
        "results": accepted,
        "errors": errors,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_intelligence_bridge.md",
    }


@router.post("/video-evidence/ingest")
def market_graph_video_evidence_ingest(
    body: VideoEvidenceIngestBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """Hermes customer use-case videos → crm_metadata.hermes_video_evidence."""
    from app.services.hermes_intelligence_ingest import ingest_video_evidence

    accepted: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, vid in enumerate(body.videos):
        try:
            if vid.company_id is None and not (vid.company_name or "").strip():
                raise ValueError("company_id or company_name required")
            result = ingest_video_evidence(
                db,
                company_id=vid.company_id,
                company_name=vid.company_name,
                source_url=vid.source_url,
                platform=vid.platform,
                evidence_kind=vid.evidence_kind,
                title=vid.title,
                excerpt=vid.excerpt,
                workflow_hint=vid.workflow_hint,
                robot_visible=vid.robot_visible,
                facility_hint=vid.facility_hint,
                confidence=vid.confidence,
                published_at=vid.published_at,
                dry_run=body.dry_run,
            )
            accepted.append({"index": idx, **result})
        except Exception as exc:
            logger.warning("video-evidence ingest %s failed: %s", idx, exc)
            errors.append({"index": idx, "error": str(exc)[:300]})

    if not body.dry_run and accepted:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc

    return {
        "ok": len(errors) == 0,
        "hermes_run_id": body.hermes_run_id,
        "accepted": len(accepted),
        "failed": len(errors),
        "results": accepted,
        "errors": errors,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_intelligence_bridge.md",
    }


@router.post("/vendor-video-evidence/ingest")
def market_graph_vendor_video_evidence_ingest(
    body: VendorVideoEvidenceIngestBody,
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """Hermes OEM demo / field videos → robot_companies.market_intelligence."""
    from app.services.hermes_intelligence_ingest import ingest_vendor_video_evidence

    accepted: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for idx, vid in enumerate(body.videos):
        try:
            result = ingest_vendor_video_evidence(
                db,
                vendor_name=vid.vendor_name,
                source_url=vid.source_url,
                platform=vid.platform,
                evidence_kind=vid.evidence_kind,
                title=vid.title,
                robot_model=vid.robot_model,
                confidence=vid.confidence,
                dry_run=body.dry_run,
            )
            accepted.append({"index": idx, **result})
        except Exception as exc:
            logger.warning("vendor-video-evidence ingest %s failed: %s", idx, exc)
            errors.append({"index": idx, "error": str(exc)[:300]})

    if not body.dry_run and accepted:
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"commit failed: {exc}") from exc

    return {
        "ok": len(errors) == 0,
        "hermes_run_id": body.hermes_run_id,
        "accepted": len(accepted),
        "failed": len(errors),
        "results": accepted,
        "errors": errors,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_intelligence_bridge.md",
    }


@router.get("/video-evidence/seed-targets")
def market_graph_video_evidence_seed_targets(
    kind: str = Query("both"),
    missing_only: bool = Query(True),
    limit: int = Query(40, ge=1, le=80),
    db: Session = Depends(get_db),
    _auth: dict = Depends(_require_hermes_ingest),
) -> dict[str, Any]:
    """RETIRED Hermes seed list. 410 unless HERMES_INGEST_ENABLED=1."""
    from app.services.hermes_intelligence_ingest import list_video_seed_targets

    try:
        payload = list_video_seed_targets(
            db, kind=kind, missing_only=missing_only, limit=limit
        )
    except Exception as exc:
        return {
            "count": 0,
            "customers": [],
            "vendors": [],
            "error": str(exc)[:240],
            "auth": _auth.get("auth"),
        }
    payload["auth"] = _auth.get("auth")
    payload["doc"] = "docs/hermes_intelligence_bridge.md"
    return payload


@router.get("/cal-status")
def market_graph_cal_status(
    _auth: dict = Depends(_require_ingest_auth),
) -> dict[str, Any]:
    """Hermes-readable Cal autonomy snapshot (Redis heartbeat + toggle). Auth: admin/cron."""
    try:
        from app.services.cal_autonomy import get_cal_autonomy_status

        status = get_cal_autonomy_status()
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:240], "auth": _auth.get("auth")}
    return {
        "ok": True,
        "cal": status,
        "auth": _auth.get("auth"),
        "doc": "docs/hermes_cal_bridge.md",
    }


@router.post("/run")
def market_graph_run(
    persist: bool = Query(True),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Manual trigger (admin/ops). Scheduler also runs this on the worker."""
    result = run_market_graph_loop(db, persist=persist)
    return {"ok": result.get("status") in {"completed", "skipped"}, "result": result}
