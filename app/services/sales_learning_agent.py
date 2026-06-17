"""Learning layer that turns SCOUT sales activity into workflow intelligence."""
from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.crm import CrmAccount
from app.models.sales_agent import SalesAgentAction, SalesOpportunity
from app.models.sales_learning import SalesExperienceEvent
from app.models.signal import Signal


POSITIVE_OUTCOMES = {"sent", "replied", "meeting_requested", "qualified", "won"}
NEGATIVE_OUTCOMES = {"failed", "blocked", "negative", "lost", "unsubscribed"}


@dataclass(frozen=True)
class WorkflowRecommendation:
    priority_score: float
    recommended_action: str
    rationale: list[str]
    automation_mode: str
    confidence: float


def record_sales_experience(
    db: Session,
    *,
    event_type: str,
    outcome: str = "observed",
    team_id=None,
    user_id=None,
    crm_account_id=None,
    sales_opportunity_id=None,
    sales_agent_action_id=None,
    company_id: int | None = None,
    robot_company_id: int | None = None,
    source_domain: str | None = None,
    signal_type: str | None = None,
    channel: str | None = None,
    score_delta: float | None = None,
    confidence: float | None = None,
    note: str | None = None,
    payload: dict[str, Any] | None = None,
) -> SalesExperienceEvent:
    event = SalesExperienceEvent(
        id=_new_uuid(db),
        team_id=_uuid_value(db, team_id),
        user_id=_uuid_value(db, user_id),
        crm_account_id=_uuid_value(db, crm_account_id),
        sales_opportunity_id=_uuid_value(db, sales_opportunity_id),
        sales_agent_action_id=_uuid_value(db, sales_agent_action_id),
        company_id=company_id,
        robot_company_id=robot_company_id,
        event_type=event_type,
        outcome=outcome,
        source_domain=source_domain,
        signal_type=signal_type,
        channel=channel,
        score_delta=score_delta,
        confidence=confidence,
        note=note,
        payload=payload or {},
    )
    db.add(event)
    return event


def capture_sales_action_experience(
    db: Session,
    *,
    opportunity: SalesOpportunity,
    action: SalesAgentAction,
    outcome: str,
    payload: dict[str, Any] | None = None,
) -> SalesExperienceEvent:
    return record_sales_experience(
        db,
        event_type=f"sales_action_{action.action_type}",
        outcome=outcome,
        team_id=opportunity.team_id,
        user_id=opportunity.owner_user_id,
        crm_account_id=opportunity.crm_account_id,
        sales_opportunity_id=opportunity.id,
        sales_agent_action_id=action.id,
        company_id=opportunity.company_id,
        robot_company_id=opportunity.robot_company_id,
        channel="email",
        confidence=_outcome_confidence(outcome),
        payload={
            "stage_before": action.stage_before,
            "stage_after": action.stage_after,
            "detected_intent": action.detected_intent,
            **(payload or {}),
        },
    )


def crm_workflow_intelligence(db: Session, account: CrmAccount) -> dict[str, Any]:
    events = (
        db.query(SalesExperienceEvent)
        .filter(SalesExperienceEvent.crm_account_id == _uuid_value(db, account.id))
        .order_by(desc(SalesExperienceEvent.created_at))
        .limit(50)
        .all()
    )
    positives = sum(1 for event in events if event.outcome in POSITIVE_OUTCOMES)
    negatives = sum(1 for event in events if event.outcome in NEGATIVE_OUTCOMES)
    sent = sum(1 for event in events if event.outcome == "sent")
    replied = sum(1 for event in events if event.outcome == "replied")
    last = events[0] if events else None
    rec = recommend_crm_next_action(db, account, events)
    return {
        "experience_count": len(events),
        "positive_outcomes": positives,
        "negative_outcomes": negatives,
        "sent_count": sent,
        "reply_count": replied,
        "last_outcome": last.outcome if last else None,
        "last_event_type": last.event_type if last else None,
        "priority_score": rec.priority_score,
        "recommended_action": rec.recommended_action,
        "automation_mode": rec.automation_mode,
        "confidence": rec.confidence,
        "rationale": rec.rationale,
    }


def recommend_crm_next_action(db: Session, account: CrmAccount, events: list[SalesExperienceEvent] | None = None) -> WorkflowRecommendation:
    events = events if events is not None else (
        db.query(SalesExperienceEvent)
        .filter(SalesExperienceEvent.crm_account_id == _uuid_value(db, account.id))
        .order_by(desc(SalesExperienceEvent.created_at))
        .limit(50)
        .all()
    )
    positives = sum(1 for event in events if event.outcome in POSITIVE_OUTCOMES)
    negatives = sum(1 for event in events if event.outcome in NEGATIVE_OUTCOMES)
    sent = sum(1 for event in events if event.outcome == "sent")
    replied = sum(1 for event in events if event.outcome == "replied")
    stage = (account.outreach_stage or "").lower()
    score = 45.0 + positives * 12.0 - negatives * 15.0
    rationale: list[str] = []
    if account.company_id:
        signal_count = db.query(func.count(Signal.id)).filter(Signal.company_id == account.company_id).scalar() or 0
        score += min(20.0, float(signal_count) * 3.0)
        if signal_count:
            rationale.append(f"{signal_count} buying signal(s) are connected to this account.")
    if sent and not replied:
        score += 8.0
        rationale.append("Cal has sent outreach but no reply is recorded yet.")
    if replied:
        score += 18.0
        rationale.append("A reply exists, so SIGNAL should keep momentum.")
    if stage in {"intro_sent", "supply_outreach_sent"}:
        rationale.append("The current stage is post-send; follow-up timing matters.")
    if not rationale:
        rationale.append("No workflow history yet; start with a researched first touch.")

    score = max(0.0, min(100.0, score))
    if replied:
        action = "Draft a context-aware reply and propose a meeting or qualification step."
        mode = "auto"
    elif sent:
        action = "Schedule an automated value-add follow-up if there is no reply after the cadence window."
        mode = "first_reply_auto"
    else:
        action = "Draft initial outreach from strongest signal and require operator review before send."
        mode = "manual"
    confidence = min(0.95, 0.45 + len(events) * 0.06 + (score / 250.0))
    return WorkflowRecommendation(round(score, 1), action, rationale[:4], mode, round(confidence, 2))


def scraper_learning_report(db: Session, limit: int = 8) -> dict[str, Any]:
    events = db.query(SalesExperienceEvent).order_by(desc(SalesExperienceEvent.created_at)).limit(500).all()
    domain_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0, "total": 0})
    signal_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0, "total": 0})
    for event in events:
        bucket = "positive" if event.outcome in POSITIVE_OUTCOMES else "negative" if event.outcome in NEGATIVE_OUTCOMES else None
        if event.source_domain:
            domain_stats[event.source_domain]["total"] += 1
            if bucket:
                domain_stats[event.source_domain][bucket] += 1
        if event.signal_type:
            signal_stats[event.signal_type]["total"] += 1
            if bucket:
                signal_stats[event.signal_type][bucket] += 1

    domain_priorities = _rank_learning_stats(domain_stats, limit)
    signal_priorities = _rank_learning_stats(signal_stats, limit)
    source_domains_from_signals = _source_domains_from_current_signals(db, limit)
    return {
        "experience_events": len(events),
        "source_domain_priorities": domain_priorities or source_domains_from_signals,
        "signal_type_priorities": signal_priorities,
        "scraper_guidance": _scraper_guidance(domain_priorities, signal_priorities, source_domains_from_signals),
    }


def _rank_learning_stats(stats: dict[str, dict[str, int]], limit: int) -> list[dict[str, Any]]:
    rows = []
    for key, values in stats.items():
        total = values["total"]
        if not total:
            continue
        positive = values["positive"]
        negative = values["negative"]
        score = (positive + 1.0) / (positive + negative + 2.0)
        rows.append({
            "key": key,
            "positive": positive,
            "negative": negative,
            "total": total,
            "learning_score": round(score, 3),
        })
    rows.sort(key=lambda row: (row["learning_score"], row["total"]), reverse=True)
    return rows[:limit]


def _source_domains_from_current_signals(db: Session, limit: int) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for (source_url,) in db.query(Signal.source_url).filter(Signal.source_url.isnot(None)).limit(1000).all():
        dom = _domain_from_url(source_url)
        if dom:
            counts[dom] += 1
    return [
        {"key": domain, "positive": 0, "negative": 0, "total": count, "learning_score": 0.5}
        for domain, count in counts.most_common(limit)
    ]


def _scraper_guidance(
    domains: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    fallback_domains: list[dict[str, Any]],
) -> list[str]:
    guidance: list[str] = []
    top_domain = (domains or fallback_domains or [None])[0]
    if top_domain:
        guidance.append(f"Prioritize sources like {top_domain['key']} because they are producing workflow evidence.")
    top_signal = (signals or [None])[0]
    if top_signal:
        guidance.append(f"Increase collection for `{top_signal['key']}` signals; they correlate with better sales progress.")
    if not guidance:
        guidance.append("Run more outreach and reply capture so SIGNAL can learn from actual sales outcomes.")
    return guidance


def _domain_from_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = parsed.netloc.lower().removeprefix("www.")
    return host or None


def _outcome_confidence(outcome: str) -> float:
    if outcome in POSITIVE_OUTCOMES:
        return 0.82
    if outcome in NEGATIVE_OUTCOMES:
        return 0.74
    return 0.5


def _uuid_value(db: Session, value):
    if value is None:
        return None
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _new_uuid(db: Session):
    value = uuid.uuid4()
    return str(value) if db.bind and db.bind.dialect.name == "sqlite" else value
