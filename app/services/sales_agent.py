"""SCOUT sales-agent planning and automated first replies."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.crm import CrmAccount
from app.models.outreach import OutreachMessage, OutreachReply
from app.models.robot_company import RobotCompany
from app.models.sales_agent import SalesAgentAction, SalesMessage, SalesOpportunity
from app.models.supply_outreach import SupplyOutreachMessage, SupplyOutreachReply
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.sales_learning_agent import capture_sales_action_experience


@dataclass(frozen=True)
class SalesAgentPlan:
    detected_intent: str
    stage_after: str
    action_type: str
    risk_level: str
    requires_approval: bool
    recommendation: str
    draft_subject: str
    draft_body: str


def classify_sales_intent(text: str, subject: str | None = None) -> str:
    blob = f"{subject or ''} {text or ''}".lower()
    if any(x in blob for x in ["price", "pricing", "cost", "budget", "quote", "how much"]):
        return "pricing_request"
    if any(x in blob for x in ["spec", "technical", "payload", "integration", "api", "safety"]):
        return "technical_specs_request"
    if any(x in blob for x in ["proposal", "rfp", "rfq", "rfi"]):
        return "proposal_requested"
    if any(x in blob for x in ["meeting", "call", "demo", "schedule", "calendar", "available"]):
        return "meeting_requested"
    if any(x in blob for x in ["po", "purchase order", "invoice", "procurement", "legal", "vendor setup"]):
        return "procurement_request"
    if any(x in blob for x in ["not interested", "no thanks", "unsubscribe", "remove me"]):
        return "negative"
    if any(x in blob for x in ["later", "next quarter", "not now", "circle back"]):
        return "nurture"
    return "general_interest"


def plan_sales_reply(
    *,
    opportunity_title: str,
    inbound_text: str,
    inbound_subject: str | None = None,
    sender_email: str | None = None,
) -> SalesAgentPlan:
    intent = classify_sales_intent(inbound_text, inbound_subject)
    subject = inbound_subject or f"Re: {opportunity_title}"
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    if intent == "pricing_request":
        stage = "quote_requested"
        recommendation = "Acknowledge pricing interest, avoid firm commitments, ask for scope, and offer a qualification call."
        body = _reply_body(
            sender_email,
            "Thanks for asking about pricing. Pricing depends on deployment scope, facility constraints, support expectations, and integration requirements.",
            [
                "facility or site count",
                "target workflow and operating hours",
                "timeline for pilot or rollout",
            ],
            "If helpful, we can set up a short call to confirm scope and route the right quote/proposal path.",
        )
    elif intent == "technical_specs_request":
        stage = "needs_info"
        recommendation = "Acknowledge the technical question and ask for constraints before sending final specs."
        body = _reply_body(
            sender_email,
            "Thanks. We can help map the technical requirements to the right robotics solution and supporting materials.",
            ["payload or throughput needs", "site constraints", "systems that need integration"],
            "Once we have those constraints, SCOUT can route the right specs and proposal materials.",
        )
    elif intent == "proposal_requested":
        stage = "proposal_requested"
        recommendation = "Confirm proposal interest and ask for decision criteria plus deadline."
        body = _reply_body(
            sender_email,
            "Thanks. We can help prepare a proposal package with buyer context, technical fit, and next steps.",
            ["proposal deadline", "decision criteria", "who should be included in review"],
            "We will prepare the next version for review before any commercial commitment is made.",
        )
    elif intent == "meeting_requested":
        stage = "meeting_requested"
        recommendation = "Move toward scheduling while keeping the reply light."
        body = _reply_body(
            sender_email,
            "Thanks. A short call is the right next step.",
            ["preferred time windows", "who should join", "main topic to cover first"],
            "Send over a couple of times that work and SCOUT will help coordinate the next step.",
        )
    elif intent == "procurement_request":
        stage = "procurement_review"
        recommendation = "Acknowledge procurement workflow and collect document requirements."
        body = _reply_body(
            sender_email,
            "Thanks. We can support the procurement path and organize the right quote, invoice, PO, or vendor setup materials.",
            ["required procurement documents", "PO or vendor onboarding process", "target approval timeline"],
            "SCOUT will keep the workflow organized so the right team sees the right documents at the right time.",
        )
    elif intent == "negative":
        stage = "lost"
        recommendation = "Respect the response and stop active outreach."
        body = "Thanks for letting us know. We will pause outreach here.\n\nBest,\nSCOUT"
    elif intent == "nurture":
        stage = "nurture"
        recommendation = "Respect timing and ask permission to follow up later."
        body = _reply_body(
            sender_email,
            "Thanks for the timing context. We can keep this light and revisit when the window is better.",
            ["preferred follow-up timeframe", "what would make this more relevant later"],
            "SCOUT can set a reminder and avoid crowding your inbox in the meantime.",
        )
    else:
        stage = "qualified"
        recommendation = "Acknowledge interest, ask two clarifying questions, and offer the next step."
        body = _reply_body(
            sender_email,
            "Thanks for the note. This sounds like it may be worth a closer look.",
            ["what outcome matters most", "timeline for evaluating options", "who else should be included"],
            "If useful, we can turn this into a short next-step plan and keep the process moving.",
        )

    return SalesAgentPlan(
        detected_intent=intent,
        stage_after=stage,
        action_type="automated_first_reply",
        risk_level="low" if intent not in {"pricing_request", "proposal_requested", "procurement_request"} else "medium",
        requires_approval=False,
        recommendation=recommendation,
        draft_subject=subject,
        draft_body=body,
    )


def _reply_body(sender_email: str | None, opener: str, questions: list[str], close: str) -> str:
    question_lines = "\n".join(f"- {q}" for q in questions)
    salutation = "Hi," if not sender_email else "Hi,"
    return f"""{salutation}

{opener}

To make the next step useful, could you share:
{question_lines}

{close}

Best,
SCOUT"""


def handle_crm_reply_first_response(db: Session, msg: OutreachMessage, reply: OutreachReply, account: CrmAccount | None) -> SalesAgentAction:
    title = account.name if account else f"CRM account {msg.crm_account_id}"
    opportunity = _get_or_create_opportunity(
        db,
        opportunity_type="crm",
        title=title,
        team_id=msg.team_id,
        crm_account_id=msg.crm_account_id,
        company_id=msg.company_id,
        owner_user_id=msg.sender_user_id,
    )
    return _handle_first_response(
        db,
        opportunity,
        source_type="outreach_reply",
        source_id=str(reply.id),
        from_email=reply.from_email,
        to_email=reply.to_email,
        subject=reply.subject,
        body_text=reply.body_text,
        reply_to=msg.reply_to,
        recipient=reply.from_email,
        idempotency_key=f"sales-agent-first-reply/crm/{reply.id}",
    )


def handle_supply_reply_first_response(
    db: Session,
    msg: SupplyOutreachMessage,
    reply: SupplyOutreachReply,
    robot_company: Optional[RobotCompany] = None,
) -> SalesAgentAction:
    title = robot_company.company_name if robot_company else f"Robot company {msg.robot_company_id}"
    opportunity = _get_or_create_opportunity(
        db,
        opportunity_type="supply",
        title=title,
        robot_company_id=msg.robot_company_id,
    )
    return _handle_first_response(
        db,
        opportunity,
        source_type="supply_outreach_reply",
        source_id=str(reply.id),
        from_email=reply.from_email,
        to_email=reply.to_email,
        subject=reply.subject,
        body_text=reply.body_text,
        reply_to=msg.reply_to,
        recipient=reply.from_email,
        idempotency_key=f"sales-agent-first-reply/supply/{reply.id}",
    )


def create_automated_next_action(
    db: Session,
    opportunity: SalesOpportunity,
    *,
    action_type: str = "automated_follow_up",
    recipient: str | None = None,
    reply_to: str | None = None,
) -> SalesAgentAction:
    next_action = opportunity.next_best_action or {}
    intent = str(next_action.get("intent") or "general_interest")
    recommendation = str(
        next_action.get("recommendation")
        or "Advance the opportunity with a short, useful next step."
    )
    subject = f"Next step: {opportunity.title}"
    body = f"""Hi,

SCOUT is keeping this opportunity moving.

Recommended next step:
{recommendation}

Suggested action:
Please share the best next detail or time window so we can keep the process moving without unnecessary back-and-forth.

Best,
SCOUT"""
    action = SalesAgentAction(
        id=_new_uuid(db),
        sales_opportunity_id=_uuid_value(db, opportunity.id),
        action_type=action_type,
        status="planned",
        risk_level="low",
        requires_approval=False,
        stage_before=opportunity.current_stage,
        stage_after=opportunity.current_stage,
        detected_intent=intent,
        recommendation=recommendation,
        draft_subject=subject,
        draft_body=body,
        payload={"auto_policy": opportunity.automation_level, "generated_from": "sales_console"},
    )
    db.add(action)
    db.flush()
    if recipient:
        execute_sales_agent_action(db, opportunity, action, recipient=recipient, reply_to=reply_to)
    return action


def execute_sales_agent_action(
    db: Session,
    opportunity: SalesOpportunity,
    action: SalesAgentAction,
    *,
    recipient: str,
    reply_to: str | None = None,
) -> SalesAgentAction:
    if action.status == "sent":
        return action
    if not recipient or "@" not in recipient:
        action.status = "blocked"
        action.error = "No recipient email available"
        return action
    if action.requires_approval and opportunity.automation_level not in {"auto", "full_auto"}:
        action.status = "awaiting_approval"
        action.error = "Approval required by automation policy"
        return action
    try:
        send_result = send_email_via_resend(
            to_email=recipient,
            subject=action.draft_subject or f"Re: {opportunity.title}",
            body_text=action.draft_body or action.recommendation or "SCOUT is following up on this opportunity.",
            from_display_name="SCOUT",
            reply_to=reply_to,
            idempotency_key=f"sales-agent-action/{action.id}",
        )
        action.status = "sent"
        action.resend_id = send_result.get("resend_id")
        action.sent_at = datetime.now(timezone.utc)
        opportunity.last_outbound_at = action.sent_at
        db.add(
            SalesMessage(
                id=_new_uuid(db),
                sales_opportunity_id=_uuid_value(db, opportunity.id),
                direction="outbound",
                source_type="sales_agent_action",
                source_id=str(action.id),
                from_email=send_result.get("from_email"),
                to_email=recipient,
                subject=action.draft_subject,
                body_text=action.draft_body,
                detected_intent=action.detected_intent,
                payload={"reply_to": reply_to, "automation_level": opportunity.automation_level},
            )
        )
        capture_sales_action_experience(
            db,
            opportunity=opportunity,
            action=action,
            outcome="sent",
            payload={"recipient": recipient, "reply_to": reply_to},
        )
    except ResendEmailError as exc:
        action.status = "failed"
        action.error = str(exc)
        capture_sales_action_experience(
            db,
            opportunity=opportunity,
            action=action,
            outcome="failed",
            payload={"recipient": recipient, "error": str(exc)},
        )
    return action


def _get_or_create_opportunity(
    db: Session,
    *,
    opportunity_type: str,
    title: str,
    team_id=None,
    crm_account_id=None,
    company_id=None,
    robot_company_id=None,
    owner_user_id=None,
) -> SalesOpportunity:
    team_id = _uuid_value(db, team_id)
    crm_account_id = _uuid_value(db, crm_account_id)
    owner_user_id = _uuid_value(db, owner_user_id)
    query = db.query(SalesOpportunity).filter(SalesOpportunity.opportunity_type == opportunity_type)
    if opportunity_type == "crm":
        query = query.filter(SalesOpportunity.crm_account_id == crm_account_id)
    else:
        query = query.filter(SalesOpportunity.robot_company_id == robot_company_id)
    row = query.first()
    if row:
        return row
    row = SalesOpportunity(
        id=_new_uuid(db),
        opportunity_type=opportunity_type,
        title=title[:240],
        team_id=team_id,
        crm_account_id=crm_account_id,
        company_id=company_id,
        robot_company_id=robot_company_id,
        owner_user_id=owner_user_id,
        current_stage="new",
        automation_level="first_reply_auto",
        payload={"created_by": "sales_agent_first_reply"},
    )
    db.add(row)
    db.flush()
    return row


def _uuid_value(db: Session, value):
    if value is None:
        return None
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value


def _already_sent_first_reply(db: Session, opportunity: SalesOpportunity) -> bool:
    return (
        db.query(SalesAgentAction)
        .filter(
            SalesAgentAction.sales_opportunity_id == opportunity.id,
            SalesAgentAction.action_type == "automated_first_reply",
            SalesAgentAction.status == "sent",
        )
        .first()
        is not None
    )


def _handle_first_response(
    db: Session,
    opportunity: SalesOpportunity,
    *,
    source_type: str,
    source_id: str,
    from_email: str | None,
    to_email: str | None,
    subject: str | None,
    body_text: str | None,
    reply_to: str | None,
    recipient: str | None,
    idempotency_key: str,
) -> SalesAgentAction:
    plan = plan_sales_reply(
        opportunity_title=opportunity.title,
        inbound_text=body_text or "",
        inbound_subject=subject,
        sender_email=from_email,
    )
    inbound = SalesMessage(
        id=_new_uuid(db),
        sales_opportunity_id=_uuid_value(db, opportunity.id),
        direction="inbound",
        source_type=source_type,
        source_id=source_id,
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        detected_intent=plan.detected_intent,
    )
    db.add(inbound)
    stage_before = opportunity.current_stage
    opportunity.current_stage = plan.stage_after
    opportunity.last_inbound_at = datetime.now(timezone.utc)
    opportunity.next_best_action = {
        "intent": plan.detected_intent,
        "recommendation": plan.recommendation,
        "stage_after": plan.stage_after,
    }
    action = SalesAgentAction(
        id=_new_uuid(db),
        sales_opportunity_id=_uuid_value(db, opportunity.id),
        action_type=plan.action_type,
        status="skipped" if _already_sent_first_reply(db, opportunity) else "planned",
        risk_level=plan.risk_level,
        requires_approval=plan.requires_approval,
        stage_before=stage_before,
        stage_after=plan.stage_after,
        detected_intent=plan.detected_intent,
        recommendation=plan.recommendation,
        draft_subject=plan.draft_subject,
        draft_body=plan.draft_body,
        payload={"source_type": source_type, "source_id": source_id, "auto_policy": "first_reply_only"},
    )
    db.add(action)
    db.flush()
    if action.status == "skipped":
        return action
    if not recipient or "@" not in recipient:
        action.status = "blocked"
        action.error = "No reply recipient email"
        return action
    try:
        execute_sales_agent_action(
            db,
            opportunity,
            action,
            recipient=recipient,
            reply_to=reply_to,
        )
    except ResendEmailError as exc:
        action.status = "failed"
        action.error = str(exc)
    return action


def _new_uuid(db: Session):
    value = uuid.uuid4()
    return str(value) if db.bind and db.bind.dialect.name == "sqlite" else value
