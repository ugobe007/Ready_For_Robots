from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.api.auth_deps import _require_user
from app.api.crm import (
    _crm_account_for_user,
    _ensure_default_team,
    _pipeline_snapshot_for_company_row,
    _raise_crm_db_error,
    _require_team_member,
    _serialize_account_enriched,
    _uid_uuid,
)
from app.database import get_db
from app.models.company import Company
from app.models.crm import CrmAccount
from app.services.scout_scoring import scout_score_for_company

router = APIRouter()


class PipelineCreateIn(BaseModel):
    team_id: Optional[uuid.UUID] = None
    company_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=1000)
    industry: Optional[str] = Field(None, max_length=240)


class PipelinePatchIn(BaseModel):
    contact_email: Optional[str] = Field(None, max_length=320)
    outreach_draft: Optional[str] = None
    stage: Optional[str] = Field(None, max_length=64)


def _serialize_pipeline_item(account: CrmAccount, company: Company | None = None) -> dict[str, Any]:
    pipeline = None
    if company:
        try:
            pipeline = _pipeline_snapshot_for_company_row(company)
        except Exception:
            pipeline = None
    data = _serialize_account_enriched(account, pipeline)
    scout = scout_score_for_company(company, url=account.website, name=account.name)
    stage = data.get("outreach_stage") or "qualification"
    return {
        "id": data["id"],
        "teamId": data["team_id"],
        "companyId": data.get("company_id"),
        "name": data["name"],
        "website": data.get("website"),
        "industry": data.get("industry"),
        "stage": stage,
        "mode": "autopilot" if stage == "autopilot" else "copilot",
        "archived": stage == "archived",
        "contactEmail": data.get("contact_email"),
        "outreachDraft": data.get("outreach_draft"),
        "createdAt": data.get("created_at"),
        "signalScore": data.get("signal_score"),
        "intentScore": data.get("overall_intent_score"),
        "leadValueScore": data.get("lead_value_score"),
        "priorityTier": data.get("pipeline_priority_tier"),
        "scoutScore": scout,
    }


@router.get("")
def list_pipeline(
    team_id: Optional[uuid.UUID] = Query(None),
    include_archived: bool = Query(False),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        default = _ensure_default_team(db, uid, user.get("email") or "")
        tid = team_id or default.id
        _require_team_member(db, uid, tid)
        accounts = (
            db.query(CrmAccount)
            .filter(CrmAccount.team_id == tid)
            .order_by(CrmAccount.created_at.desc())
            .all()
        )
        ids = [a.company_id for a in accounts if a.company_id]
        companies = {}
        if ids:
            rows = (
                db.query(Company)
                .options(joinedload(Company.signals), joinedload(Company.scores))
                .filter(Company.id.in_(ids))
                .all()
            )
            companies = {c.id: c for c in rows}
        items = [_serialize_pipeline_item(a, companies.get(a.company_id)) for a in accounts]
        if not include_archived:
            items = [item for item in items if not item["archived"]]
        return {"items": items, "teamId": str(tid)}
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as exc:
        _raise_crm_db_error(exc)


@router.post("")
def create_pipeline_item(
    body: PipelineCreateIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        default = _ensure_default_team(db, uid, user.get("email") or "")
        tid = body.team_id or default.id
        _require_team_member(db, uid, tid)
        company = db.get(Company, body.company_id) if body.company_id is not None else None
        if body.company_id is not None and company is None:
            raise HTTPException(status_code=404, detail="company_id not found")
        name = (body.name or getattr(company, "name", None) or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="name is required")
        account = CrmAccount(
            team_id=tid,
            company_id=body.company_id,
            name=name,
            website=body.website or getattr(company, "website", None),
            industry=body.industry or getattr(company, "industry", None),
            owner_user_id=uid,
            outreach_stage="qualification",
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        if account.company_id:
            company = (
                db.query(Company)
                .options(joinedload(Company.signals), joinedload(Company.scores))
                .filter(Company.id == account.company_id)
                .first()
            )
        return {"item": _serialize_pipeline_item(account, company)}
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as exc:
        _raise_crm_db_error(exc)


@router.post("/{item_id}/advance")
def advance_pipeline_item(
    item_id: str,
    body: Optional[PipelinePatchIn] = None,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        account_id = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pipeline id") from None
    account = _crm_account_for_user(db, uid, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Pipeline item not found or access denied")
    stages = ["qualification", "research", "drafted", "intro_sent", "proposal", "won"]
    current = account.outreach_stage or "qualification"
    next_stage = body.stage if body and body.stage else stages[min(len(stages) - 1, stages.index(current) + 1)] if current in stages else "research"
    account.outreach_stage = next_stage
    if body:
        if body.contact_email is not None:
            account.contact_email = body.contact_email
        if body.outreach_draft is not None:
            account.outreach_draft = body.outreach_draft
    db.commit()
    db.refresh(account)
    return {"item": _serialize_pipeline_item(account)}


@router.post("/{item_id}/toggle-mode")
def toggle_pipeline_mode(item_id: str, user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    uid = _uid_uuid(user)
    try:
        account_id = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pipeline id") from None
    account = _crm_account_for_user(db, uid, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Pipeline item not found or access denied")
    account.outreach_stage = "qualification" if account.outreach_stage == "autopilot" else "autopilot"
    db.commit()
    db.refresh(account)
    return {"item": _serialize_pipeline_item(account)}


@router.post("/{item_id}/archive")
def archive_pipeline_item(item_id: str, user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    uid = _uid_uuid(user)
    try:
        account_id = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pipeline id") from None
    account = _crm_account_for_user(db, uid, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Pipeline item not found or access denied")
    account.outreach_stage = "archived"
    db.commit()
    db.refresh(account)
    return {"archived": True, "item": _serialize_pipeline_item(account)}


@router.post("/{item_id}/generate-proposal")
def generate_pipeline_proposal(item_id: str, user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    uid = _uid_uuid(user)
    try:
        account_id = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pipeline id") from None
    account = _crm_account_for_user(db, uid, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Pipeline item not found or access denied")
    company = db.get(Company, account.company_id) if account.company_id else None
    scout = scout_score_for_company(company, url=account.website, name=account.name)
    proposal_text = "\n".join(
        [
            f"READY FOR ROBOTS PROPOSAL — {account.name}",
            "",
            "WHY NOW",
            scout["summary"],
            "",
            "RECOMMENDED MOTION",
            "Use SCOUT to validate buying triggers, prioritize the highest-value automation use case, and launch a focused outreach sequence.",
            "",
            "NEXT STEPS",
            "1. Confirm the operational pain with a buyer or public source.",
            "2. Package one automation use case with ROI assumptions.",
            "3. Send a concise intro tied to the current trigger event.",
        ]
    )
    row = db.execute(
        text("""
            INSERT INTO pipeline_proposals
                (id, user_id, company_id, company_name, proposal_text, contact_email, created_at, updated_at)
            VALUES
                (gen_random_uuid(), :uid, :cid, :cn, :pt, :em, now(), now())
            ON CONFLICT ON CONSTRAINT uq_pipeline_proposals_user_company_name
            DO UPDATE SET proposal_text = EXCLUDED.proposal_text, contact_email = EXCLUDED.contact_email, updated_at = now()
            RETURNING id, company_name, proposal_text, contact_email, created_at, updated_at
        """),
        {
            "uid": uid,
            "cid": account.company_id,
            "cn": account.name,
            "pt": proposal_text,
            "em": account.contact_email,
        },
    ).fetchone()
    account.outreach_stage = "proposal"
    db.commit()
    return {
        "proposal": {
            "id": str(row.id) if row else None,
            "companyName": account.name,
            "proposalText": proposal_text,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
    }
