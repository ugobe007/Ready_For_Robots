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


def _step_event_counts(
    db: Session,
    *,
    cutoff: datetime,
    prev_cutoff: datetime | None,
    path: str,
) -> tuple[dict[str, int], dict[str, int]]:
    """Count /event step metrics by payload.step for current and previous windows."""
    steps = ("save_lead", "copy_draft", "send_outreach")
    path_expr = SiteAnalyticsEvent.payload.op("->>")("path")
    step_expr = SiteAnalyticsEvent.payload.op("->>")("step")

    rows = (
        db.query(step_expr.label("step"), func.count(SiteAnalyticsEvent.id).label("count"))
        .filter(
            SiteAnalyticsEvent.event_type == EVENT_VISIT,
            SiteAnalyticsEvent.created_at >= cutoff,
            path_expr == path,
            step_expr.in_(steps),
        )
        .group_by(step_expr)
        .all()
    )
    current = {step: 0 for step in steps}
    for row in rows:
        if row.step in current:
            current[str(row.step)] = int(row.count or 0)

    previous = {step: 0 for step in steps}
    if prev_cutoff is not None:
        prev_rows = (
            db.query(step_expr.label("step"), func.count(SiteAnalyticsEvent.id).label("count"))
            .filter(
                SiteAnalyticsEvent.event_type == EVENT_VISIT,
                SiteAnalyticsEvent.created_at >= prev_cutoff,
                SiteAnalyticsEvent.created_at < cutoff,
                path_expr == path,
                step_expr.in_(steps),
            )
            .group_by(step_expr)
            .all()
        )
        for row in prev_rows:
            if row.step in previous:
                previous[str(row.step)] = int(row.count or 0)
    return current, previous


def _reason_event_counts(
    db: Session,
    *,
    cutoff: datetime,
    prev_cutoff: datetime | None,
    path: str,
    reasons: tuple[str, ...],
) -> tuple[dict[str, int], dict[str, int]]:
    """Count /event rows grouped by payload.blocker_reason for windows."""
    path_expr = SiteAnalyticsEvent.payload.op("->>")("path")
    reason_expr = SiteAnalyticsEvent.payload.op("->>")("blocker_reason")

    rows = (
        db.query(reason_expr.label("reason"), func.count(SiteAnalyticsEvent.id).label("count"))
        .filter(
            SiteAnalyticsEvent.event_type == EVENT_VISIT,
            SiteAnalyticsEvent.created_at >= cutoff,
            path_expr == path,
            reason_expr.in_(reasons),
        )
        .group_by(reason_expr)
        .all()
    )
    current = {reason: 0 for reason in reasons}
    for row in rows:
        if row.reason in current:
            current[str(row.reason)] = int(row.count or 0)

    previous = {reason: 0 for reason in reasons}
    if prev_cutoff is not None:
        prev_rows = (
            db.query(reason_expr.label("reason"), func.count(SiteAnalyticsEvent.id).label("count"))
            .filter(
                SiteAnalyticsEvent.event_type == EVENT_VISIT,
                SiteAnalyticsEvent.created_at >= prev_cutoff,
                SiteAnalyticsEvent.created_at < cutoff,
                path_expr == path,
                reason_expr.in_(reasons),
            )
            .group_by(reason_expr)
            .all()
        )
        for row in prev_rows:
            if row.reason in previous:
                previous[str(row.reason)] = int(row.count or 0)
    return current, previous


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
                "outreach_after_save_rate": 0.0,
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
    pipeline_save_success = events.get("/event/pipeline_save_success", 0)
    pipeline_outreach_sent = events.get("/event/pipeline_outreach_sent", 0)
    contact_assist_submit = events.get("/event/pipeline_contact_assist_submit", 0)
    send_with_captured_contact = events.get("/event/pipeline_send_with_captured_contact", 0)
    send_checklist_view = events.get("/event/pipeline_send_checklist_view", 0)
    send_checklist_ready = events.get("/event/pipeline_send_checklist_ready", 0)
    send_checklist_variant_a_view = events.get("/event/pipeline_send_checklist_variant_a_view", 0)
    send_checklist_variant_b_view = events.get("/event/pipeline_send_checklist_variant_b_view", 0)
    send_checklist_variant_a_ready = events.get("/event/pipeline_send_checklist_variant_a_ready", 0)
    send_checklist_variant_b_ready = events.get("/event/pipeline_send_checklist_variant_b_ready", 0)
    pipeline_outreach_sent_variant_a = events.get("/event/pipeline_outreach_sent_variant_a", 0)
    pipeline_outreach_sent_variant_b = events.get("/event/pipeline_outreach_sent_variant_b", 0)
    first3_save_variant_a_entered = events.get("/event/pipeline_first3_save_variant_a_entered", 0)
    first3_save_variant_b_entered = events.get("/event/pipeline_first3_save_variant_b_entered", 0)
    first3_save_variant_a_completed = events.get("/event/pipeline_first3_save_variant_a_completed", 0)
    first3_save_variant_b_completed = events.get("/event/pipeline_first3_save_variant_b_completed", 0)
    step_entered, prev_step_entered = _step_event_counts(
        db,
        cutoff=cutoff,
        prev_cutoff=prev_cutoff,
        path="/event/pipeline_first3_step_entered",
    )
    step_completed, prev_step_completed = _step_event_counts(
        db,
        cutoff=cutoff,
        prev_cutoff=prev_cutoff,
        path="/event/pipeline_first3_step_completed",
    )
    step_abandoned, prev_step_abandoned = _step_event_counts(
        db,
        cutoff=cutoff,
        prev_cutoff=prev_cutoff,
        path="/event/pipeline_first3_step_abandoned",
    )
    step_coaching_click, prev_step_coaching_click = _step_event_counts(
        db,
        cutoff=cutoff,
        prev_cutoff=prev_cutoff,
        path="/event/pipeline_first3_coaching_click",
    )
    send_blockers, prev_send_blockers = _reason_event_counts(
        db,
        cutoff=cutoff,
        prev_cutoff=prev_cutoff,
        path="/event/pipeline_send_readiness_blocker",
        reasons=("missing_contact", "missing_draft", "already_sent", "not_authenticated", "unknown"),
    )

    entered_total = sum(step_entered.values())
    completed_total = sum(step_completed.values())
    abandoned_total = sum(step_abandoned.values())
    coaching_click_total = sum(step_coaching_click.values())
    send_blockers_total = sum(send_blockers.values())

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
            "pipeline_save_success": pipeline_save_success,
            "pipeline_outreach_sent": pipeline_outreach_sent,
            "pipeline_draft_copy": events.get("/event/pipeline_draft_copy", 0),
            "pipeline_contact_assist_open": events.get("/event/pipeline_contact_assist_open", 0),
            "pipeline_contact_assist_submit": contact_assist_submit,
            "pipeline_contact_assist_invalid": events.get("/event/pipeline_contact_assist_invalid", 0),
            "pipeline_send_with_captured_contact": send_with_captured_contact,
            "pipeline_send_checklist_view": send_checklist_view,
            "pipeline_send_checklist_ready": send_checklist_ready,
            "pipeline_send_checklist_variant_a_view": send_checklist_variant_a_view,
            "pipeline_send_checklist_variant_b_view": send_checklist_variant_b_view,
            "pipeline_send_checklist_variant_a_ready": send_checklist_variant_a_ready,
            "pipeline_send_checklist_variant_b_ready": send_checklist_variant_b_ready,
            "pipeline_outreach_sent_variant_a": pipeline_outreach_sent_variant_a,
            "pipeline_outreach_sent_variant_b": pipeline_outreach_sent_variant_b,
            "pipeline_first3_save_variant_a_entered": first3_save_variant_a_entered,
            "pipeline_first3_save_variant_b_entered": first3_save_variant_b_entered,
            "pipeline_first3_save_variant_a_completed": first3_save_variant_a_completed,
            "pipeline_first3_save_variant_b_completed": first3_save_variant_b_completed,
        },
        "first_three": {
            "entered": step_entered,
            "completed": step_completed,
            "abandoned": step_abandoned,
            "coaching_click": step_coaching_click,
            "send_blockers": send_blockers,
        },
        "rates": {
            "report_submit_rate": _rate(report_success, report_start),
            "newsletter_submit_rate": _rate(newsletter_success, newsletter_start),
            "outreach_after_save_rate": _rate(pipeline_outreach_sent, pipeline_save_success),
            "first3_save_completion_rate": _rate(step_completed["save_lead"], step_entered["save_lead"]),
            "first3_copy_completion_rate": _rate(step_completed["copy_draft"], step_entered["copy_draft"]),
            "first3_send_completion_rate": _rate(step_completed["send_outreach"], step_entered["send_outreach"]),
            "first3_save_to_copy_rate": _rate(step_completed["copy_draft"], step_completed["save_lead"]),
            "first3_copy_to_send_rate": _rate(step_completed["send_outreach"], step_completed["copy_draft"]),
            "first3_abandon_rate": _rate(abandoned_total, entered_total),
            "first3_completion_rate": _rate(completed_total, entered_total),
            "first3_coaching_click_rate": _rate(coaching_click_total, entered_total),
            "first3_save_coaching_click_rate": _rate(step_coaching_click["save_lead"], step_entered["save_lead"]),
            "first3_copy_coaching_click_rate": _rate(step_coaching_click["copy_draft"], step_entered["copy_draft"]),
            "first3_send_coaching_click_rate": _rate(step_coaching_click["send_outreach"], step_entered["send_outreach"]),
            "first3_send_blocker_rate": _rate(send_blockers_total, step_entered["send_outreach"]),
            "captured_contact_send_rate": _rate(send_with_captured_contact, contact_assist_submit),
            "send_checklist_ready_rate": _rate(send_checklist_ready, send_checklist_view),
            "send_after_checklist_rate": _rate(pipeline_outreach_sent, send_checklist_view),
            "send_checklist_variant_a_ready_rate": _rate(send_checklist_variant_a_ready, send_checklist_variant_a_view),
            "send_checklist_variant_b_ready_rate": _rate(send_checklist_variant_b_ready, send_checklist_variant_b_view),
            "send_after_checklist_variant_a_rate": _rate(pipeline_outreach_sent_variant_a, send_checklist_variant_a_view),
            "send_after_checklist_variant_b_rate": _rate(pipeline_outreach_sent_variant_b, send_checklist_variant_b_view),
            "first3_save_variant_a_completion_rate": _rate(first3_save_variant_a_completed, first3_save_variant_a_entered),
            "first3_save_variant_b_completion_rate": _rate(first3_save_variant_b_completed, first3_save_variant_b_entered),
        },
        "prev_events": {
            "hero_pipeline_click": prev_events.get("/event/home_cta_pipeline_click", 0),
            "hero_live_pipeline_anchor_click": prev_events.get("/event/home_cta_live_pipeline_anchor_click", 0),
            "report_modal_open": prev_events.get("/event/home_report_modal_open", 0),
            "report_submit_start": prev_events.get("/event/home_report_submit_start", 0),
            "report_submit_success": prev_events.get("/event/home_report_submit_success", 0),
            "newsletter_submit_start": prev_events.get("/event/home_newsletter_submit_start", 0),
            "newsletter_submit_success": prev_events.get("/event/home_newsletter_submit_success", 0),
            "pipeline_save_success": prev_events.get("/event/pipeline_save_success", 0),
            "pipeline_outreach_sent": prev_events.get("/event/pipeline_outreach_sent", 0),
            "pipeline_draft_copy": prev_events.get("/event/pipeline_draft_copy", 0),
            "pipeline_contact_assist_open": prev_events.get("/event/pipeline_contact_assist_open", 0),
            "pipeline_contact_assist_submit": prev_events.get("/event/pipeline_contact_assist_submit", 0),
            "pipeline_contact_assist_invalid": prev_events.get("/event/pipeline_contact_assist_invalid", 0),
            "pipeline_send_with_captured_contact": prev_events.get("/event/pipeline_send_with_captured_contact", 0),
            "pipeline_send_checklist_view": prev_events.get("/event/pipeline_send_checklist_view", 0),
            "pipeline_send_checklist_ready": prev_events.get("/event/pipeline_send_checklist_ready", 0),
            "pipeline_send_checklist_variant_a_view": prev_events.get("/event/pipeline_send_checklist_variant_a_view", 0),
            "pipeline_send_checklist_variant_b_view": prev_events.get("/event/pipeline_send_checklist_variant_b_view", 0),
            "pipeline_send_checklist_variant_a_ready": prev_events.get("/event/pipeline_send_checklist_variant_a_ready", 0),
            "pipeline_send_checklist_variant_b_ready": prev_events.get("/event/pipeline_send_checklist_variant_b_ready", 0),
            "pipeline_outreach_sent_variant_a": prev_events.get("/event/pipeline_outreach_sent_variant_a", 0),
            "pipeline_outreach_sent_variant_b": prev_events.get("/event/pipeline_outreach_sent_variant_b", 0),
            "pipeline_first3_save_variant_a_entered": prev_events.get("/event/pipeline_first3_save_variant_a_entered", 0),
            "pipeline_first3_save_variant_b_entered": prev_events.get("/event/pipeline_first3_save_variant_b_entered", 0),
            "pipeline_first3_save_variant_a_completed": prev_events.get("/event/pipeline_first3_save_variant_a_completed", 0),
            "pipeline_first3_save_variant_b_completed": prev_events.get("/event/pipeline_first3_save_variant_b_completed", 0),
        },
        "prev_first_three": {
            "entered": prev_step_entered,
            "completed": prev_step_completed,
            "abandoned": prev_step_abandoned,
            "coaching_click": prev_step_coaching_click,
            "send_blockers": prev_send_blockers,
        },
    }
