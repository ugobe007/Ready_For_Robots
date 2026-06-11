"""
Plan entitlements for public pipeline surfaces and workspace saves.

Tiers (until Stripe wiring lands):
  anonymous — no auth
  free      — signed in, default
  paid      — ADMIN_EMAILS, PAID_PLAN_EMAILS, or JWT app_metadata plan_tier in starter|pro|premium
"""
from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Optional


PLAN_ANONYMOUS = "anonymous"
PLAN_FREE = "free"
PLAN_PAID = "paid"

# Pro/Premium unlock full pipeline + research; Starter is paid billing but free-tier caps until upgraded.
PAID_PIPELINE_SLUGS = frozenset({"pro", "premium", "paid"})

PIPELINE_LIMIT_ANONYMOUS = 12
PIPELINE_LIMIT_FREE = 35
PIPELINE_LIMIT_PAID = 50
SAVED_LEADS_LIMIT_FREE = 5


def _is_admin_email(email: str) -> bool:
    from app.api.auth_deps import _is_admin

    return _is_admin(email)


def resolve_plan_tier(user: Optional[dict]) -> str:
    if not user:
        return PLAN_ANONYMOUS
    email = (user.get("email") or "").strip()
    if email and _is_admin_email(email):
        return PLAN_PAID
    paid_emails = {
        e.strip().lower()
        for e in (os.getenv("PAID_PLAN_EMAILS") or "").split(",")
        if e.strip()
    }
    if email.lower() in paid_emails:
        return PLAN_PAID
    slug = (user.get("plan_tier") or user.get("plan") or "").strip().lower()
    if slug in PAID_PIPELINE_SLUGS:
        return PLAN_PAID
    return PLAN_FREE


def pipeline_limit_for_plan(plan: str) -> int:
    if plan == PLAN_PAID:
        return PIPELINE_LIMIT_PAID
    if plan == PLAN_FREE:
        return PIPELINE_LIMIT_FREE
    return PIPELINE_LIMIT_ANONYMOUS


def saved_leads_limit_for_plan(plan: str) -> Optional[int]:
    if plan == PLAN_ANONYMOUS:
        return 0
    if plan == PLAN_FREE:
        return SAVED_LEADS_LIMIT_FREE
    return None


def entitlements_payload(plan: str, *, visible_count: int) -> dict[str, Any]:
    saved_limit = saved_leads_limit_for_plan(plan)
    return {
        "plan": plan,
        "pipeline_limit": pipeline_limit_for_plan(plan),
        "visible_count": visible_count,
        "saved_limit": saved_limit,
        "upgrade_url": "/pricing",
    }


def _truncate(text: Optional[str], max_len: int) -> Optional[str]:
    if not text:
        return text
    t = str(text).strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def sanitize_lead_for_plan(lead: dict[str, Any], plan: str) -> dict[str, Any]:
    """Return a copy of a pipeline lead row appropriate for the caller's plan."""
    row = deepcopy(lead)
    if plan == PLAN_PAID:
        return row

    if plan == PLAN_FREE:
        row.pop("research_updates", None)
        row.pop("last_researched_at", None)
        row.pop("latest_material_update", None)
        return row

    # Anonymous preview — enough SCOUT context to excite signup without full workspace depth.
    row["share_summary"] = _truncate(row.get("share_summary"), 240)
    row["share_blurb"] = _truncate(row.get("share_blurb"), 160)
    highlights = row.get("lead_highlights")
    if isinstance(highlights, dict):
        teaser: dict[str, Any] = {}
        if highlights.get("specific_problem"):
            teaser["specific_problem"] = _truncate(highlights.get("specific_problem"), 220)
        why = highlights.get("why_lead")
        if isinstance(why, list):
            teaser["why_lead"] = [_truncate(str(item), 140) for item in why[:2] if item]
        robots = highlights.get("robot_categories") or highlights.get("application_areas")
        if isinstance(robots, list):
            teaser["robot_categories"] = [str(item) for item in robots[:3] if item]
        if teaser:
            row["lead_highlights"] = teaser
        else:
            row.pop("lead_highlights", None)
    else:
        row.pop("lead_highlights", None)

    robots_needed = row.get("robot_types_needed")
    if isinstance(robots_needed, list):
        row["robot_types_needed"] = [str(item) for item in robots_needed[:3] if item]

    for key in (
        "lead_inference",
        "research_updates",
        "last_researched_at",
        "latest_material_update",
        "automation_profile",
        "gtm",
        "procurement_hints",
        "inferred_contact_email",
        "inferred_contact_cc",
        "inferred_contact_role",
        "priority_reasons",
        "lead_value_components",
        "lead_value_weights",
    ):
        row.pop(key, None)

    signals = row.get("signals")
    if isinstance(signals, list) and signals:
        first = deepcopy(signals[0])
        first["display_text"] = _truncate(first.get("display_text"), 200)
        first["raw_text"] = _truncate(first.get("raw_text"), 200)
        first.pop("source_url", None)
        row["signals"] = [first]
    row["signal_count"] = min(int(row.get("signal_count") or 1), 1)
    if isinstance(row.get("score"), dict):
        score = row["score"]
        row["score"] = {
            "overall_score": score.get("overall_score"),
            "lead_value_score": score.get("lead_value_score"),
        }
    return row


def assert_can_save_lead(plan: str, current_saved_count: int) -> None:
    """Raise HTTPException when workspace save limit is exceeded."""
    from fastapi import HTTPException

    limit = saved_leads_limit_for_plan(plan)
    if limit is None:
        return
    if current_saved_count >= limit:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "saved_leads_limit",
                "message": f"Free workspace includes {limit} saved leads. Upgrade for more.",
                "saved_limit": limit,
                "upgrade_url": "/pricing",
            },
        )


def count_workspace_leads(db, user_id) -> int:
    """Distinct pipeline companies saved to any team the user belongs to."""
    from uuid import UUID

    from sqlalchemy import func

    from app.models.crm import CrmAccount, TeamMember

    uid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
    row = (
        db.query(func.count(func.distinct(CrmAccount.company_id)))
        .join(TeamMember, TeamMember.team_id == CrmAccount.team_id)
        .filter(TeamMember.user_id == uid, CrmAccount.company_id.isnot(None))
        .scalar()
    )
    return int(row or 0)


def apply_pipeline_entitlements(
    feed: dict[str, Any],
    plan: str,
) -> dict[str, Any]:
    leads = list(feed.get("leads") or [])
    limit = pipeline_limit_for_plan(plan)
    trimmed = [sanitize_lead_for_plan(row, plan) for row in leads[:limit]]
    out = dict(feed)
    out["leads"] = trimmed
    out["entitlements"] = entitlements_payload(plan, visible_count=len(trimmed))
    if plan == PLAN_ANONYMOUS and isinstance(out.get("summary"), dict):
        summary = dict(out["summary"])
        for key in ("warm", "cold", "watching"):
            summary.pop(key, None)
        out["summary"] = summary
    return out
