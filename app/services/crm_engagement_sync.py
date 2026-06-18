"""Keep crm_engagements aligned with sales_opportunities (deal stage SSOT)."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.crm import CrmAccount, CrmEngagement
from app.models.sales_agent import SalesOpportunity

STAGE_MAP = {
    "new": "qualification",
    "intro_sent": "outreach",
    "nurture": "nurture",
    "qualified": "discovery",
    "meeting": "meeting",
    "proposal": "proposal",
    "negotiation": "negotiation",
    "closed_won": "closed_won",
    "closed_lost": "closed_lost",
    "replied": "discovery",
    "negative": "closed_lost",
}


def engagement_stage_for_opportunity(stage: str | None) -> str:
    key = (stage or "new").strip().lower()
    return STAGE_MAP.get(key, "qualification")


def ensure_engagement_for_opportunity(
    db: Session,
    opportunity: SalesOpportunity,
    *,
    account: CrmAccount | None = None,
) -> CrmEngagement | None:
    if not opportunity.crm_account_id or not opportunity.team_id:
        return None
    acct = account
    if not acct:
        acct = db.query(CrmAccount).filter(CrmAccount.id == opportunity.crm_account_id).first()
    if not acct:
        return None

    engagement = (
        db.query(CrmEngagement)
        .filter(
            CrmEngagement.crm_account_id == acct.id,
            CrmEngagement.team_id == opportunity.team_id,
            CrmEngagement.status == "open",
        )
        .order_by(CrmEngagement.created_at.desc())
        .first()
    )
    if not engagement:
        engagement = CrmEngagement(
            team_id=opportunity.team_id,
            crm_account_id=acct.id,
            name=f"{acct.name} — automation pursuit",
            stage=engagement_stage_for_opportunity(opportunity.current_stage),
            owner_user_id=opportunity.owner_user_id,
            status="open",
        )
        db.add(engagement)
        db.flush()
    return engagement


def sync_opportunity_stage_to_engagement(db: Session, opportunity: SalesOpportunity) -> CrmEngagement | None:
    engagement = ensure_engagement_for_opportunity(db, opportunity)
    if not engagement:
        return None
    engagement.stage = engagement_stage_for_opportunity(opportunity.current_stage)
    if opportunity.current_stage in ("closed_won", "closed_lost", "negative"):
        engagement.status = "closed"
    if opportunity.owner_user_id and not engagement.owner_user_id:
        engagement.owner_user_id = opportunity.owner_user_id
    db.add(engagement)
    return engagement


def sync_account_stage_to_engagement(db: Session, account: CrmAccount) -> CrmEngagement | None:
    stage = engagement_stage_for_opportunity(account.outreach_stage)
    engagement = (
        db.query(CrmEngagement)
        .filter(
            CrmEngagement.crm_account_id == account.id,
            CrmEngagement.team_id == account.team_id,
            CrmEngagement.status == "open",
        )
        .order_by(CrmEngagement.created_at.desc())
        .first()
    )
    if not engagement:
        engagement = CrmEngagement(
            team_id=account.team_id,
            crm_account_id=account.id,
            name=f"{account.name} — automation pursuit",
            stage=stage,
            owner_user_id=account.owner_user_id,
            status="open",
        )
        db.add(engagement)
    else:
        engagement.stage = stage
    db.flush()
    return engagement


def serialize_engagement(row: CrmEngagement) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "team_id": str(row.team_id),
        "crm_account_id": str(row.crm_account_id),
        "name": row.name,
        "stage": row.stage,
        "value_amount": float(row.value_amount) if row.value_amount is not None else None,
        "currency": row.currency,
        "owner_user_id": str(row.owner_user_id) if row.owner_user_id else None,
        "status": row.status,
        "opened_at": row.opened_at.isoformat() if row.opened_at else None,
        "closed_at": row.closed_at.isoformat() if row.closed_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
