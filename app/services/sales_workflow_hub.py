"""Aggregate ranked next actions, activity feed, and workflow summaries for CRM operators."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.crm import CrmAccount
from app.models.outreach import OutreachMessage, OutreachReply
from app.models.sales_agent import SalesAgentAction, SalesMessage, SalesOpportunity
from app.models.sales_learning import SalesExperienceEvent
from app.models.scout_chat import ScoutActivation
from app.services.sales_learning_agent import crm_workflow_intelligence


@dataclass
class WorkflowAction:
    id: str
    action_type: str
    label: str
    company_name: str
    priority: str
    route: str
    entity_type: str
    entity_id: str
    score: float
    meta: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type,
            "label": self.label,
            "companyName": self.company_name,
            "priority": self.priority,
            "route": self.route,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "score": round(self.score, 1),
            "meta": self.meta,
        }


def _priority_bucket(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _team_account_company_ids(db: Session, team_ids: list[Any]) -> set[int]:
    rows = (
        db.query(CrmAccount.company_id)
        .filter(CrmAccount.team_id.in_(team_ids), CrmAccount.company_id.isnot(None))
        .all()
    )
    return {int(row[0]) for row in rows if row[0]}


def collect_next_actions(
    db: Session,
    *,
    team_ids: list[Any],
    user_id: uuid.UUID | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    actions: list[WorkflowAction] = []
    now = datetime.now(timezone.utc)
    stale_cutoff = now - timedelta(days=2)
    followup_cutoff = now - timedelta(days=3)

    accounts = (
        db.query(CrmAccount)
        .filter(CrmAccount.team_id.in_(team_ids))
        .order_by(desc(CrmAccount.updated_at))
        .limit(200)
        .all()
    )
    for acct in accounts:
        intel = crm_workflow_intelligence(db, acct)
        base_score = float(intel.get("priority_score") or 40.0)
        stage = (acct.outreach_stage or "").lower()

        if acct.outreach_draft and not acct.outreach_sent_at:
            age_bonus = 10.0 if (acct.updated_at and acct.updated_at < stale_cutoff) else 0.0
            actions.append(
                WorkflowAction(
                    id=f"draft:{acct.id}",
                    action_type="approve_draft",
                    label="Review and send outreach draft",
                    company_name=acct.name,
                    priority=_priority_bucket(base_score + age_bonus + 8),
                    route="/crm",
                    entity_type="crm_account",
                    entity_id=str(acct.id),
                    score=base_score + age_bonus + 8,
                    meta={"outreach_stage": stage, "has_contact": bool(acct.contact_email)},
                )
            )
        elif acct.outreach_sent_at and not stage.startswith("replied"):
            sent_at = acct.outreach_sent_at
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=timezone.utc)
            reply_exists = (
                db.query(OutreachReply.id)
                .filter(OutreachReply.crm_account_id == acct.id)
                .limit(1)
                .first()
            )
            if not reply_exists and sent_at < followup_cutoff:
                actions.append(
                    WorkflowAction(
                        id=f"followup:{acct.id}",
                        action_type="follow_up",
                        label="Send follow-up — no reply yet",
                        company_name=acct.name,
                        priority=_priority_bucket(base_score + 12),
                        route="/crm",
                        entity_type="crm_account",
                        entity_id=str(acct.id),
                        score=base_score + 12,
                        meta={"sent_at": sent_at.isoformat()},
                    )
                )
        elif not acct.contact_email and acct.company_id:
            actions.append(
                WorkflowAction(
                    id=f"contact:{acct.id}",
                    action_type="resolve_contact",
                    label="Find contact email before outreach",
                    company_name=acct.name,
                    priority=_priority_bucket(base_score + 5),
                    route="/crm",
                    entity_type="crm_account",
                    entity_id=str(acct.id),
                    score=base_score + 5,
                    meta={"company_id": acct.company_id},
                )
            )

        rec = (intel.get("recommended_action") or "").strip()
        if rec and intel.get("reply_count"):
            actions.append(
                WorkflowAction(
                    id=f"reply:{acct.id}",
                    action_type="reply",
                    label=rec[:120],
                    company_name=acct.name,
                    priority=_priority_bucket(base_score + 20),
                    route="/inbox",
                    entity_type="crm_account",
                    entity_id=str(acct.id),
                    score=base_score + 20,
                    meta={"last_outcome": intel.get("last_outcome")},
                )
            )

    pending_actions = (
        db.query(SalesAgentAction, SalesOpportunity)
        .join(SalesOpportunity, SalesAgentAction.sales_opportunity_id == SalesOpportunity.id)
        .filter(
            SalesOpportunity.team_id.in_(team_ids),
            SalesAgentAction.status.in_(("pending", "drafted")),
            SalesAgentAction.requires_approval.is_(True),
        )
        .order_by(desc(SalesAgentAction.created_at))
        .limit(30)
        .all()
    )
    for action, opp in pending_actions:
        actions.append(
            WorkflowAction(
                id=f"agent:{action.id}",
                action_type="approve_agent_action",
                label=(action.recommendation or "Approve automated reply").strip()[:120],
                company_name=opp.title,
                priority="high",
                route="/sales-console",
                entity_type="sales_opportunity",
                entity_id=str(opp.id),
                score=85.0,
                meta={"action_id": str(action.id), "intent": action.detected_intent},
            )
        )

    activation_query = db.query(ScoutActivation).filter(
        ScoutActivation.status.in_(("awaiting_approval", "drafted", "evaluating"))
    )
    if user_id:
        activation_query = activation_query.filter(ScoutActivation.user_id == user_id)
    activations = activation_query.order_by(desc(ScoutActivation.updated_at)).limit(15).all()
    for act in activations:
        lead_count = len(act.leads_snapshot or [])
        actions.append(
            WorkflowAction(
                id=f"activation:{act.id}",
                action_type="review_activation",
                label=f"Review SCOUT queue ({lead_count} lead{'s' if lead_count != 1 else ''})",
                company_name=(act.source_url or "SCOUT activation")[:80],
                priority="high" if act.status == "awaiting_approval" else "medium",
                route="/pipeline",
                entity_type="scout_activation",
                entity_id=str(act.id),
                score=78.0 if act.status == "awaiting_approval" else 60.0,
                meta={"status": act.status, "mode": act.mode_choice, "lead_count": lead_count},
            )
        )

    try:
        from app.api.leads import build_public_leads_list

        hot_leads = build_public_leads_list(db, limit=30, tier="HOT", sort="score")
        saved_ids = _team_account_company_ids(db, team_ids)
        for lead in hot_leads:
            cid = lead.get("id")
            if not cid or int(cid) in saved_ids:
                continue
            score = float(lead.get("priority_score") or 0)
            actions.append(
                WorkflowAction(
                    id=f"hot:{cid}",
                    action_type="add_to_crm",
                    label="Add HOT lead to CRM workspace",
                    company_name=lead.get("company_name") or "Unknown",
                    priority=_priority_bucket(score),
                    route="/pipeline",
                    entity_type="company",
                    entity_id=str(cid),
                    score=score,
                    meta={"tier": lead.get("priority_tier"), "signal_count": lead.get("signal_count")},
                )
            )
    except Exception:
        pass

    actions.sort(key=lambda item: item.score, reverse=True)
    seen: set[str] = set()
    deduped: list[WorkflowAction] = []
    for item in actions:
        if item.id in seen:
            continue
        seen.add(item.id)
        deduped.append(item)
    return [item.as_dict() for item in deduped[:limit]]


def collect_activity_feed(
    db: Session,
    *,
    team_ids: list[Any],
    limit: int = 40,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    accounts = (
        db.query(CrmAccount)
        .filter(CrmAccount.team_id.in_(team_ids))
        .order_by(desc(CrmAccount.updated_at))
        .limit(80)
        .all()
    )
    for acct in accounts:
        if acct.outreach_draft and not acct.outreach_sent_at:
            items.append(
                {
                    "id": f"feed:draft:{acct.id}",
                    "companyName": acct.name,
                    "industry": acct.industry or "",
                    "signalType": "outreach",
                    "signalSummary": "Cal draft ready for review",
                    "robotUseCase": "",
                    "recommendedAction": "Approve and send outreach",
                    "status": "draft_ready",
                    "confidenceScore": 0.82,
                    "createdAt": (acct.updated_at or datetime.now(timezone.utc)).isoformat(),
                    "route": "/crm",
                    "entity_id": str(acct.id),
                }
            )

    messages = (
        db.query(OutreachMessage, CrmAccount)
        .join(CrmAccount, OutreachMessage.crm_account_id == CrmAccount.id)
        .filter(OutreachMessage.team_id.in_(team_ids), OutreachMessage.status == "sent")
        .order_by(desc(OutreachMessage.sent_at))
        .limit(30)
        .all()
    )
    for msg, acct in messages:
        items.append(
            {
                "id": f"feed:sent:{msg.id}",
                "companyName": acct.name,
                "industry": acct.industry or "",
                "signalType": "outreach",
                "signalSummary": f"Outreach sent to {msg.to_email}",
                "robotUseCase": "",
                "recommendedAction": "Monitor for reply",
                "status": "followup_sent",
                "confidenceScore": 0.7,
                "createdAt": (msg.sent_at or msg.created_at or datetime.now(timezone.utc)).isoformat(),
                "route": "/crm",
                "entity_id": str(acct.id),
            }
        )

    inbound = (
        db.query(SalesMessage, SalesOpportunity)
        .join(SalesOpportunity, SalesMessage.sales_opportunity_id == SalesOpportunity.id)
        .filter(SalesMessage.direction == "inbound", SalesOpportunity.team_id.in_(team_ids))
        .order_by(desc(SalesMessage.created_at))
        .limit(25)
        .all()
    )
    for msg, opp in inbound:
        items.append(
            {
                "id": f"feed:inbound:{msg.id}",
                "companyName": opp.title,
                "industry": "",
                "signalType": msg.detected_intent or "reply",
                "signalSummary": (msg.body_text or msg.subject or "Inbound reply")[:200],
                "robotUseCase": "",
                "recommendedAction": "Review and respond",
                "status": "qualified",
                "confidenceScore": 0.9,
                "createdAt": (msg.created_at or datetime.now(timezone.utc)).isoformat(),
                "route": "/inbox",
                "entity_id": str(opp.id),
            }
        )

    recent_signals = (
        db.query(Company)
        .join(CrmAccount, CrmAccount.company_id == Company.id)
        .filter(CrmAccount.team_id.in_(team_ids))
        .order_by(desc(Company.updated_at))
        .limit(20)
        .all()
    )
    for company in recent_signals:
        meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
        timing = meta.get("timing") or meta.get("procurement_timing")
        if not timing:
            continue
        items.append(
            {
                "id": f"feed:signal:{company.id}",
                "companyName": company.name,
                "industry": company.industry or "",
                "signalType": "timing",
                "signalSummary": str(timing)[:200],
                "robotUseCase": "",
                "recommendedAction": "Update outreach angle",
                "status": "new_signal",
                "confidenceScore": 0.75,
                "createdAt": (company.updated_at or datetime.now(timezone.utc)).isoformat(),
                "route": "/pipeline",
                "entity_id": str(company.id),
            }
        )

    items.sort(key=lambda row: row.get("createdAt") or "", reverse=True)
    return items[:limit]


def workflow_summary_since(
    db: Session,
    *,
    team_ids: list[Any],
    since: datetime,
) -> dict[str, int]:
    since_naive = since if since.tzinfo else since.replace(tzinfo=timezone.utc)

    events = (
        db.query(SalesExperienceEvent.outcome, func.count(SalesExperienceEvent.id))
        .filter(
            SalesExperienceEvent.team_id.in_(team_ids),
            SalesExperienceEvent.created_at >= since_naive,
        )
        .group_by(SalesExperienceEvent.outcome)
        .all()
    )
    outcome_counts = {row[0]: int(row[1]) for row in events}

    drafts = (
        db.query(func.count(CrmAccount.id))
        .filter(
            CrmAccount.team_id.in_(team_ids),
            CrmAccount.outreach_draft.isnot(None),
            CrmAccount.updated_at >= since_naive,
        )
        .scalar()
        or 0
    )
    sends = (
        db.query(func.count(OutreachMessage.id))
        .filter(OutreachMessage.team_id.in_(team_ids), OutreachMessage.sent_at >= since_naive)
        .scalar()
        or 0
    )
    replies = (
        db.query(func.count(OutreachReply.id))
        .filter(OutreachReply.team_id.in_(team_ids), OutreachReply.received_at >= since_naive)
        .scalar()
        or 0
    )
    advanced = (
        db.query(func.count(SalesOpportunity.id))
        .filter(
            SalesOpportunity.team_id.in_(team_ids),
            SalesOpportunity.updated_at >= since_naive,
            SalesOpportunity.current_stage.notin_(("new", "intro_sent")),
        )
        .scalar()
        or 0
    )

    return {
        "signalsDetected": int(outcome_counts.get("observed", 0)) + int(outcome_counts.get("signal", 0)),
        "companiesQualified": int(outcome_counts.get("qualified", 0)) + int(outcome_counts.get("positive", 0)),
        "outreachDraftsCreated": int(drafts),
        "followupsSent": int(sends),
        "opportunitiesAdvanced": int(advanced),
        "repliesReceived": int(replies),
    }
