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

# Buyer signup funnel (conversion board #20) — instrument the browse → signup →
# activate motion so we can see WHERE the funnel drops (signup friction vs
# activation friction) instead of only knowing "signups but no paid subs".
EVENT_SIGNUP_START = "signup_start"
EVENT_SIGNUP_COMPLETE = "signup_complete"
EVENT_FIRST_SAVE = "first_save"

SIGNUP_FUNNEL_STAGES = (EVENT_SIGNUP_START, EVENT_SIGNUP_COMPLETE, EVENT_FIRST_SAVE)


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


def _rate(numerator: int, denominator: int) -> float:
    """Percentage of numerator over denominator, 0.0 when denominator is 0."""
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def signup_funnel_metrics(
    db: Session,
    *,
    cutoff: datetime,
    prev_cutoff: datetime | None = None,
) -> dict[str, Any]:
    """Signup funnel counts + step conversion rates for conversion board #20.

    Stages: signup_start (intent) → signup_complete (account created) →
    first_save (activated: saved their first lead). Step rates reveal whether the
    drop-off is at signup friction (start→complete) or activation (complete→save).
    """
    if not _table_ready(db, SiteAnalyticsEvent.__tablename__):
        return {
            "available": False,
            "signup_start": 0,
            "signup_complete": 0,
            "first_save": 0,
            "start_to_complete_rate": 0.0,
            "complete_to_save_rate": 0.0,
            "start_to_save_rate": 0.0,
        }

    start, prev_start = _count_events(db, EVENT_SIGNUP_START, cutoff, prev_cutoff)
    complete, prev_complete = _count_events(db, EVENT_SIGNUP_COMPLETE, cutoff, prev_cutoff)
    first_save, prev_save = _count_events(db, EVENT_FIRST_SAVE, cutoff, prev_cutoff)

    return {
        "available": True,
        "signup_start": start,
        "signup_complete": complete,
        "first_save": first_save,
        "start_to_complete_rate": _rate(complete, start),
        "complete_to_save_rate": _rate(first_save, complete),
        "start_to_save_rate": _rate(first_save, start),
        "prev": {
            "signup_start": prev_start,
            "signup_complete": prev_complete,
            "first_save": prev_save,
        },
    }


def marketing_conversion_snapshot(
    db: Session,
    *,
    cutoff: datetime,
    prev_cutoff: datetime | None = None,
) -> dict[str, Any]:
    """Homepage conversion event snapshot from tracked marketing actions.

    We store these as EVENT_VISIT rows with payload.path="/event/<action>" so
    they can be analyzed without creating a new event table/schema.
    """
    if not _table_ready(db, SiteAnalyticsEvent.__tablename__):
        return {
            "available": False,
            "events": {},
            "rates": {
                "report_submit_rate": 0.0,
                "newsletter_submit_rate": 0.0,
            },
        }

    path_expr = SiteAnalyticsEvent.payload.op("->>")("path")
    rows = (
        db.query(path_expr.label("path"), func.count(SiteAnalyticsEvent.id).label("count"))
        .filter(
            SiteAnalyticsEvent.event_type == EVENT_VISIT,
            SiteAnalyticsEvent.created_at >= cutoff,
            path_expr.like("/event/%"),
        )
        .group_by(path_expr)
        .all()
    )

    events = {str(r.path): int(r.count or 0) for r in rows if r.path}

    prev_events: dict[str, int] = {}
    if prev_cutoff is not None:
        prev_rows = (
            db.query(path_expr.label("path"), func.count(SiteAnalyticsEvent.id).label("count"))
            .filter(
                SiteAnalyticsEvent.event_type == EVENT_VISIT,
                SiteAnalyticsEvent.created_at >= prev_cutoff,
                SiteAnalyticsEvent.created_at < cutoff,
                path_expr.like("/event/%"),
            )
            .group_by(path_expr)
            .all()
        )
        prev_events = {str(r.path): int(r.count or 0) for r in prev_rows if r.path}

    report_start = events.get("/event/home_report_submit_start", 0)
    report_success = events.get("/event/home_report_submit_success", 0)
    newsletter_start = events.get("/event/home_newsletter_submit_start", 0)
    newsletter_success = events.get("/event/home_newsletter_submit_success", 0)

    return {
        "available": True,
        "events": {
            "hero_pipeline_click": events.get("/event/home_cta_pipeline_click", 0),
            "hero_live_pipeline_anchor_click": events.get("/event/home_cta_live_pipeline_anchor_click", 0),
            "report_modal_open": events.get("/event/home_report_modal_open", 0),
            "report_submit_start": report_start,
            "report_submit_success": report_success,
            "newsletter_submit_start": newsletter_start,
            "newsletter_submit_success": newsletter_success,
        },
        "rates": {
            "report_submit_rate": _rate(report_success, report_start),
            "newsletter_submit_rate": _rate(newsletter_success, newsletter_start),
        },
        "prev_events": {
            "hero_pipeline_click": prev_events.get("/event/home_cta_pipeline_click", 0),
            "hero_live_pipeline_anchor_click": prev_events.get("/event/home_cta_live_pipeline_anchor_click", 0),
            "report_modal_open": prev_events.get("/event/home_report_modal_open", 0),
            "report_submit_start": prev_events.get("/event/home_report_submit_start", 0),
            "report_submit_success": prev_events.get("/event/home_report_submit_success", 0),
            "newsletter_submit_start": prev_events.get("/event/home_newsletter_submit_start", 0),
            "newsletter_submit_success": prev_events.get("/event/home_newsletter_submit_success", 0),
        },
    }
