"""Record and aggregate marketing site analytics."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.newsletter_subscriber import NewsletterSubscriber
from app.models.robot_buyer_lead import RobotBuyerLead
from app.models.scout_chat import ScoutSession
from app.models.shared_calculation import SharedCalculation
from app.models.site_analytics_event import SiteAnalyticsEvent
from app.models.waitlist import WaitlistSignup

EVENT_VISIT = "visit"
EVENT_ROI = "roi_calculation"
EVENT_ROBOT_SEARCH = "robot_search"
EVENT_URL_SCAN = "url_scan"
EVENT_SUPPLY_SIGNUP_LANDING = "supply_signup_landing"
EVENT_SUPPLY_SIGNUP_COMPLETE = "supply_signup_complete"


def record_site_event(db: Session, event_type: str, payload: dict[str, Any] | None = None) -> None:
    if not _table_ready(db, SiteAnalyticsEvent.__tablename__):
        return
    try:
        db.add(
            SiteAnalyticsEvent(
                id=str(uuid.uuid4()),
                event_type=event_type,
                payload=payload or {},
            )
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()


def _count_events(db: Session, event_type: str, cutoff: datetime, prev_cutoff: datetime | None = None) -> tuple[int, int]:
    current = (
        db.query(func.count(SiteAnalyticsEvent.id))
        .filter(
            SiteAnalyticsEvent.event_type == event_type,
            SiteAnalyticsEvent.created_at >= cutoff,
        )
        .scalar()
        or 0
    )
    previous = 0
    if prev_cutoff is not None:
        previous = (
            db.query(func.count(SiteAnalyticsEvent.id))
            .filter(
                SiteAnalyticsEvent.event_type == event_type,
                SiteAnalyticsEvent.created_at >= prev_cutoff,
                SiteAnalyticsEvent.created_at < cutoff,
            )
            .scalar()
            or 0
        )
    return int(current), int(previous)


def _count_table_since(db: Session, model, cutoff: datetime, prev_cutoff: datetime | None = None) -> tuple[int, int]:
    current = (
        db.query(func.count(model.id))
        .filter(model.created_at >= cutoff)
        .scalar()
        or 0
    )
    previous = 0
    if prev_cutoff is not None:
        previous = (
            db.query(func.count(model.id))
            .filter(
                and_(model.created_at >= prev_cutoff, model.created_at < cutoff),
            )
            .scalar()
            or 0
        )
    return int(current), int(previous)


def _growth_pct(current: int, previous: int) -> int:
    if previous:
        return round(((current - previous) / previous) * 100)
    return 100 if current else 0


def _table_ready(db: Session, table_name: str) -> bool:
    try:
        return inspect(db.bind).has_table(table_name)
    except SQLAlchemyError:
        return False


def aggregate_site_metrics(
    db: Session,
    *,
    cutoff: datetime,
    prev_cutoff: datetime,
    in_memory_calcs: list[dict[str, Any]],
    in_memory_searches: list[dict[str, Any]],
    in_memory_visits: list[dict[str, Any]],
) -> dict[str, Any]:
    if not _table_ready(db, SiteAnalyticsEvent.__tablename__):
        visit_events = url_scans = roi_events = robot_events = 0
    else:
        visit_events, _ = _count_events(db, EVENT_VISIT, cutoff, prev_cutoff)
        url_scans, _ = _count_events(db, EVENT_URL_SCAN, cutoff, prev_cutoff)
        roi_events, _ = _count_events(db, EVENT_ROI, cutoff, prev_cutoff)
        robot_events, _ = _count_events(db, EVENT_ROBOT_SEARCH, cutoff, prev_cutoff)

    scout_sessions, _ = _count_table_since(db, ScoutSession, cutoff, prev_cutoff)
    site_visits = visit_events + scout_sessions + len(in_memory_visits)

    shared_calcs, prev_shared = _count_table_since(db, SharedCalculation, cutoff, prev_cutoff)
    in_memory_filtered = [
        c for c in in_memory_calcs if datetime.fromisoformat(c["timestamp"]) >= cutoff.replace(tzinfo=None)
    ]
    total_calculations = shared_calcs + url_scans + roi_events + len(in_memory_filtered)
    calculation_growth = _growth_pct(total_calculations, prev_shared + len(in_memory_filtered))

    buyer_leads, _ = _count_table_since(db, RobotBuyerLead, cutoff, prev_cutoff)
    in_memory_search_filtered = [
        s for s in in_memory_searches if datetime.fromisoformat(s["timestamp"]) >= cutoff.replace(tzinfo=None)
    ]
    robot_searches = buyer_leads + robot_events + len(in_memory_search_filtered)

    waitlist_emails, _ = _count_table_since(db, WaitlistSignup, cutoff, prev_cutoff)
    newsletter_emails, _ = _count_table_since(db, NewsletterSubscriber, cutoff, prev_cutoff)
    in_memory_emails = len([c for c in in_memory_filtered if c.get("email")])
    email_captures = waitlist_emails + newsletter_emails + buyer_leads + in_memory_emails

    avg_payback_months = 0.0
    avg_robot_cost = 0.0
    if in_memory_filtered:
        paybacks = [c.get("payback_months", 0) for c in in_memory_filtered if c.get("payback_months")]
        costs = [c.get("robot_cost", 0) for c in in_memory_filtered if c.get("robot_cost")]
        avg_payback_months = round(sum(paybacks) / len(paybacks), 1) if paybacks else 0.0
        avg_robot_cost = round(sum(costs) / len(costs)) if costs else 0

    funnel_denominator = max(site_visits, total_calculations + robot_searches, 1)
    conversion_rate = round((email_captures / funnel_denominator) * 100)

    return {
        "site_visits": site_visits,
        "total_calculations": total_calculations,
        "calculation_growth": calculation_growth,
        "robot_searches": robot_searches,
        "email_captures": email_captures,
        "conversion_rate": conversion_rate,
        "avg_payback_months": avg_payback_months,
        "avg_robot_cost": avg_robot_cost,
    }
