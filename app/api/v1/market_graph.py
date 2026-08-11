"""Market graph loop status + snapshot for product/admin surfaces."""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.admin_auth import get_admin_key, get_cron_token
from app.database import get_db
from app.services.market_graph_loop import (
    get_market_graph_loop_status,
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


def _require_ingest_auth(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    token: str = Query("", description="SCRAPER_CRON_TOKEN alternative"),
) -> dict[str, str]:
    admin = get_admin_key()
    cron = get_cron_token()
    ok_admin = bool(admin and x_admin_key and x_admin_key.strip() == admin)
    ok_cron = bool(cron and token.strip() == cron)
    if not ok_admin and not ok_cron:
        raise HTTPException(status_code=403, detail="Invalid X-Admin-Key or token")
    return {"auth": "admin_key" if ok_admin else "cron_token"}


@router.get("/status")
def market_graph_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    snap = read_market_graph_snapshot(db) or {}
    return {
        "scheduler": get_market_graph_loop_status(),
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
        "spine": "docs/ontology/primitives.v1.json",
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
        "spine": "docs/ontology/primitives.v1.json",
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
    _auth: dict = Depends(_require_ingest_auth),
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


@router.post("/run")
def market_graph_run(
    persist: bool = Query(True),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Manual trigger (admin/ops). Scheduler also runs this on the worker."""
    result = run_market_graph_loop(db, persist=persist)
    return {"ok": result.get("status") in {"completed", "skipped"}, "result": result}
