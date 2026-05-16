"""SCOUT Sales Console API."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session
from urllib.parse import urlparse

from app.api.auth_deps import _require_user
from app.database import get_db
from app.models.crm import CrmAccount, TeamMember
from app.models.sales_agent import SalesAgentAction, SalesMessage, SalesOpportunity
from app.services.apollo_client import (
    ApolloAPIError,
    ApolloConfigError,
    ApolloProspectClient,
    recommended_prospect_titles,
)
from app.services.sales_learning_agent import scraper_learning_report
from app.services.sales_agent import create_automated_next_action, execute_sales_agent_action

router = APIRouter()


class AutomationPatchIn(BaseModel):
    automation_level: str = Field("auto", max_length=32)


class AutomateActionIn(BaseModel):
    recipient: Optional[str] = Field(None, max_length=320)
    reply_to: Optional[str] = Field(None, max_length=320)
    force: bool = True


class ProspectSearchIn(BaseModel):
    organization_name: Optional[str] = Field(None, max_length=240)
    organization_domain: Optional[str] = Field(None, max_length=240)
    industry: Optional[str] = Field(None, max_length=120)
    titles: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    per_page: int = Field(10, ge=1, le=25)


def _uid_uuid(user: dict) -> uuid.UUID:
    return uuid.UUID(str(user["uid"]))


def _db_uuid(db: Session, value: uuid.UUID | str | None):
    if value is None:
        return None
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _crm_uuid(value: uuid.UUID | str | None) -> uuid.UUID | None:
    if value is None:
        return None
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


def _domain_from_url(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    return parsed.netloc.lower().removeprefix("www.") or None


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


def _serialize_inbox_item(db: Session, message: SalesMessage, opportunity: SalesOpportunity) -> dict[str, Any]:
    action = (
        db.query(SalesAgentAction)
        .filter(SalesAgentAction.sales_opportunity_id == opportunity.id)
        .order_by(desc(SalesAgentAction.created_at))
        .first()
    )
    return {
        "id": str(message.id),
        "thread_id": str(opportunity.id),
        "opportunity_type": opportunity.opportunity_type,
        "title": opportunity.title,
        "current_stage": opportunity.current_stage,
        "status": opportunity.status,
        "from_email": message.from_email,
        "to_email": message.to_email,
        "subject": message.subject,
        "body_text": message.body_text,
        "detected_intent": message.detected_intent,
        "received_at": message.created_at.isoformat() if message.created_at else None,
        "source_type": message.source_type,
        "source_id": message.source_id,
        "crm_account_id": str(opportunity.crm_account_id) if opportunity.crm_account_id else None,
        "robot_company_id": opportunity.robot_company_id,
        "next_best_action": opportunity.next_best_action or {},
        "latest_action": _serialize_action(action) if action else None,
    }


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


@router.get("/inbox")
def list_sales_inbox(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    team_ids = _team_ids_for_user(db, _uid_uuid(user))
    if not team_ids:
        return []
    query = (
        db.query(SalesMessage, SalesOpportunity)
        .join(SalesOpportunity, SalesMessage.sales_opportunity_id == SalesOpportunity.id)
        .filter(SalesMessage.direction == "inbound", SalesOpportunity.team_id.in_(team_ids))
    )
    if team_id:
        requested = _db_uuid(db, team_id)
        if requested not in team_ids:
            raise HTTPException(status_code=404, detail="Team not found or access denied")
        query = query.filter(SalesOpportunity.team_id == requested)
    rows = query.order_by(desc(SalesMessage.created_at)).limit(100).all()
    return [_serialize_inbox_item(db, message, opportunity) for message, opportunity in rows]


@router.get("/learning")
def get_sales_learning_report(
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    team_ids = _team_ids_for_user(db, _uid_uuid(user))
    if not team_ids:
        return {"experience_events": 0, "source_domain_priorities": [], "signal_type_priorities": [], "scraper_guidance": []}
    return scraper_learning_report(db)


@router.post("/prospects/search")
def search_sales_prospects(
    payload: ProspectSearchIn,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    team_ids = _team_ids_for_user(db, _uid_uuid(user))
    if not team_ids:
        raise HTTPException(status_code=404, detail="No workspace found for user")
    titles = payload.titles or recommended_prospect_titles(payload.industry)
    try:
        result = ApolloProspectClient().search_people(
            organization_name=payload.organization_name,
            organization_domain=payload.organization_domain,
            titles=titles,
            locations=payload.locations,
            per_page=payload.per_page,
        )
    except ApolloConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ApolloAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "prospects": result["prospects"],
        "pagination": result["pagination"],
        "request": result["request"],
        "recommended_titles": titles,
    }


@router.get("/opportunities/{opportunity_id}/prospects")
def prospects_for_sales_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    opportunity = _opportunity_or_404(db, opportunity_id, _team_ids_for_user(db, _uid_uuid(user)))
    account = db.query(CrmAccount).filter(CrmAccount.id == _crm_uuid(opportunity.crm_account_id)).first() if opportunity.crm_account_id else None
    organization_name = account.name if account else opportunity.title
    domain = _domain_from_url(account.website if account else None)
    industry = account.industry if account else None
    titles = recommended_prospect_titles(industry, opportunity.current_stage)
    try:
        result = ApolloProspectClient().search_people(
            organization_name=organization_name,
            organization_domain=domain,
            titles=titles,
            per_page=10,
        )
    except ApolloConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ApolloAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "opportunity_id": str(opportunity.id),
        "organization_name": organization_name,
        "organization_domain": domain,
        "prospects": result["prospects"],
        "pagination": result["pagination"],
        "recommended_titles": titles,
    }


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
