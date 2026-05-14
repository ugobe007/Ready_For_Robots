"""SCOUT Sales Console API."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.database import get_db
from app.models.crm import CrmAccount, TeamMember
from app.models.sales_agent import SalesAgentAction, SalesMessage, SalesOpportunity
from app.services.sales_agent import create_automated_next_action, execute_sales_agent_action

router = APIRouter()


class AutomationPatchIn(BaseModel):
    automation_level: str = Field("auto", max_length=32)


class AutomateActionIn(BaseModel):
    recipient: Optional[str] = Field(None, max_length=320)
    reply_to: Optional[str] = Field(None, max_length=320)
    force: bool = True


def _uid_uuid(user: dict) -> uuid.UUID:
    return uuid.UUID(str(user["uid"]))


def _db_uuid(db: Session, value: uuid.UUID | str | None):
    if value is None:
        return None
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _team_ids_for_user(db: Session, uid: uuid.UUID) -> list[Any]:
    rows = db.query(TeamMember.team_id).filter(TeamMember.user_id == uid).all()
    return [_db_uuid(db, row[0]) for row in rows]


def _opportunity_or_404(db: Session, opportunity_id: str, team_ids: list[Any]) -> SalesOpportunity:
    row = db.query(SalesOpportunity).filter(SalesOpportunity.id == _db_uuid(db, opportunity_id)).first()
    if not row or not row.team_id or row.team_id not in team_ids:
        raise HTTPException(status_code=404, detail="Sales opportunity not found")
    return row


def _latest_recipient(db: Session, opportunity: SalesOpportunity) -> str | None:
    inbound = (
        db.query(SalesMessage)
        .filter(
            SalesMessage.sales_opportunity_id == opportunity.id,
            SalesMessage.direction == "inbound",
            SalesMessage.from_email.isnot(None),
        )
        .order_by(desc(SalesMessage.created_at))
        .first()
    )
    if inbound and inbound.from_email:
        return inbound.from_email
    if opportunity.crm_account_id:
        account = db.query(CrmAccount).filter(CrmAccount.id == opportunity.crm_account_id).first()
        return account.contact_email if account else None
    return None


def _serialize_message(row: SalesMessage) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "direction": row.direction,
        "channel": row.channel,
        "source_type": row.source_type,
        "source_id": row.source_id,
        "from_email": row.from_email,
        "to_email": row.to_email,
        "subject": row.subject,
        "body_text": row.body_text,
        "detected_intent": row.detected_intent,
        "payload": row.payload or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _serialize_action(row: SalesAgentAction) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "action_type": row.action_type,
        "status": row.status,
        "risk_level": row.risk_level,
        "requires_approval": bool(row.requires_approval),
        "stage_before": row.stage_before,
        "stage_after": row.stage_after,
        "detected_intent": row.detected_intent,
        "recommendation": row.recommendation,
        "draft_subject": row.draft_subject,
        "draft_body": row.draft_body,
        "resend_id": row.resend_id,
        "error": row.error,
        "payload": row.payload or {},
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _serialize_opportunity(db: Session, row: SalesOpportunity, include_details: bool = False) -> dict[str, Any]:
    latest_message = (
        db.query(SalesMessage)
        .filter(SalesMessage.sales_opportunity_id == row.id)
        .order_by(desc(SalesMessage.created_at))
        .first()
    )
    payload = {
        "id": str(row.id),
        "opportunity_type": row.opportunity_type,
        "team_id": str(row.team_id) if row.team_id else None,
        "crm_account_id": str(row.crm_account_id) if row.crm_account_id else None,
        "company_id": row.company_id,
        "robot_company_id": row.robot_company_id,
        "owner_user_id": str(row.owner_user_id) if row.owner_user_id else None,
        "title": row.title,
        "current_stage": row.current_stage,
        "status": row.status,
        "automation_level": row.automation_level,
        "next_best_action": row.next_best_action or {},
        "last_inbound_at": row.last_inbound_at.isoformat() if row.last_inbound_at else None,
        "last_outbound_at": row.last_outbound_at.isoformat() if row.last_outbound_at else None,
        "latest_message": _serialize_message(latest_message) if latest_message else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
    if include_details:
        messages = (
            db.query(SalesMessage)
            .filter(SalesMessage.sales_opportunity_id == row.id)
            .order_by(desc(SalesMessage.created_at))
            .limit(25)
            .all()
        )
        actions = (
            db.query(SalesAgentAction)
            .filter(SalesAgentAction.sales_opportunity_id == row.id)
            .order_by(desc(SalesAgentAction.created_at))
            .limit(25)
            .all()
        )
        payload["messages"] = [_serialize_message(item) for item in messages]
        payload["actions"] = [_serialize_action(item) for item in actions]
    return payload


@router.get("/opportunities")
def list_sales_opportunities(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    uid = _uid_uuid(user)
    team_ids = _team_ids_for_user(db, uid)
    if not team_ids:
        return []
    query = db.query(SalesOpportunity).filter(SalesOpportunity.team_id.in_(team_ids))
    if team_id:
        requested = _db_uuid(db, team_id)
        if requested not in team_ids:
            raise HTTPException(status_code=404, detail="Team not found or access denied")
        query = query.filter(SalesOpportunity.team_id == requested)
    rows = query.order_by(desc(SalesOpportunity.updated_at)).limit(100).all()
    return [_serialize_opportunity(db, row) for row in rows]


@router.get("/opportunities/{opportunity_id}")
def get_sales_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    row = _opportunity_or_404(db, opportunity_id, _team_ids_for_user(db, _uid_uuid(user)))
    return _serialize_opportunity(db, row, include_details=True)


@router.patch("/opportunities/{opportunity_id}/automation")
def update_sales_automation(
    opportunity_id: str,
    payload: AutomationPatchIn,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    row = _opportunity_or_404(db, opportunity_id, _team_ids_for_user(db, _uid_uuid(user)))
    allowed = {"manual", "first_reply_auto", "auto", "full_auto"}
    if payload.automation_level not in allowed:
        raise HTTPException(status_code=400, detail=f"automation_level must be one of {sorted(allowed)}")
    row.automation_level = payload.automation_level
    db.commit()
    db.refresh(row)
    return _serialize_opportunity(db, row, include_details=True)


@router.post("/opportunities/{opportunity_id}/actions/automate-next")
def automate_next_sales_action(
    opportunity_id: str,
    payload: AutomateActionIn | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    row = _opportunity_or_404(db, opportunity_id, _team_ids_for_user(db, _uid_uuid(user)))
    if payload and payload.force:
        row.automation_level = "auto"
    recipient = payload.recipient if payload and payload.recipient else _latest_recipient(db, row)
    action = create_automated_next_action(
        db,
        row,
        recipient=recipient,
        reply_to=payload.reply_to if payload else None,
    )
    db.commit()
    db.refresh(action)
    return {"action": _serialize_action(action), "opportunity": _serialize_opportunity(db, row, include_details=True)}


@router.post("/actions/{action_id}/automate")
def automate_sales_action(
    action_id: str,
    payload: AutomateActionIn | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    team_ids = _team_ids_for_user(db, _uid_uuid(user))
    action = db.query(SalesAgentAction).filter(SalesAgentAction.id == _db_uuid(db, action_id)).first()
    if not action:
        raise HTTPException(status_code=404, detail="Sales action not found")
    opportunity = _opportunity_or_404(db, str(action.sales_opportunity_id), team_ids)
    if payload and payload.force:
        action.requires_approval = False
        opportunity.automation_level = "auto"
    recipient = payload.recipient if payload and payload.recipient else _latest_recipient(db, opportunity)
    execute_sales_agent_action(
        db,
        opportunity,
        action,
        recipient=recipient or "",
        reply_to=payload.reply_to if payload else None,
    )
    db.commit()
    db.refresh(action)
    return {"action": _serialize_action(action), "opportunity": _serialize_opportunity(db, opportunity, include_details=True)}
