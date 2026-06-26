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

# Pro/Premium unlock full pipeline + research; Starter slug is billing-only until Stripe maps it.
PAID_PIPELINE_SLUGS = frozenset({"pro", "premium", "paid"})
BILLING_TIER_LABELS = {
    "free": "Free workspace",
    "starter": "Starter (billing pending)",
    "pro": "Pro",
    "premium": "Premium",
    "paid": "Pro",
}

PIPELINE_HOT_SLOTS = int(os.getenv("PIPELINE_HOT_SLOTS", "15"))
PIPELINE_WARM_SLOTS = int(os.getenv("PIPELINE_WARM_SLOTS", "20"))
PIPELINE_MONITOR_SLOTS = int(os.getenv("PIPELINE_MONITOR_SLOTS", "15"))
PIPELINE_TIERED_TOTAL = PIPELINE_HOT_SLOTS + PIPELINE_WARM_SLOTS + PIPELINE_MONITOR_SLOTS

# Anonymous preview shows every tier; signed-in free/paid get the full 15+20+15 mix.
PIPELINE_LIMIT_ANONYMOUS = 12
PIPELINE_ANON_HOT_SLOTS = 5
PIPELINE_ANON_WARM_SLOTS = 4
PIPELINE_ANON_MONITOR_SLOTS = 3

PIPELINE_LIMIT_FREE = PIPELINE_TIERED_TOTAL
PIPELINE_LIMIT_PAID = PIPELINE_TIERED_TOTAL
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


def resolve_billing_tier_slug(user: Optional[dict]) -> str:
    """JWT / env billing slug — may differ from effective workspace plan."""
    if not user:
        return "anonymous"
    email = (user.get("email") or "").strip()
    if email and _is_admin_email(email):
        return "pro"
    slug = (user.get("plan_tier") or user.get("plan") or "").strip().lower()
    return slug or "free"


def plan_feature_flags(plan: str) -> dict[str, bool]:
    """Feature gates exposed to UI — must match sanitize_lead_for_plan behavior."""
    if plan == PLAN_PAID:
        return {
            "research_updates": True,
            "hubspot_auto_sync": True,
            "unlimited_saves": True,
            "full_lead_intel": True,
        }
    if plan == PLAN_FREE:
        return {
            "research_updates": False,
            "hubspot_auto_sync": False,
            "unlimited_saves": False,
            "full_lead_intel": True,
        }
    return {
        "research_updates": False,
        "hubspot_auto_sync": False,
        "unlimited_saves": False,
        "full_lead_intel": False,
    }


def user_workspace_entitlements(user: Optional[dict], db=None) -> dict[str, Any]:
    """Workspace entitlements for /api/user/me and profile meters."""
    plan = resolve_plan_tier(user)
    billing = resolve_billing_tier_slug(user)
    saved_limit = saved_leads_limit_for_plan(plan)
    saved_count = 0
    if user and db is not None and plan != PLAN_ANONYMOUS:
        try:
            from uuid import UUID

            uid = user.get("uid")
            if uid:
                saved_count = count_workspace_leads(db, UUID(str(uid)))
        except Exception:
            saved_count = 0
    features = plan_feature_flags(plan)
    label = BILLING_TIER_LABELS.get(billing if plan == PLAN_PAID else "free", "Free workspace")
    if plan == PLAN_PAID and billing in BILLING_TIER_LABELS:
        label = BILLING_TIER_LABELS[billing]
    return {
        "plan": plan,
        "billing_tier": billing,
        "display_name": label,
        "pipeline_limit": pipeline_limit_for_plan(plan),
        "saved_limit": saved_limit,
        "saved_count": saved_count,
        "features": features,
        "upgrade_url": "/pricing",
    }


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


def _tier_slots_for_plan(plan: str) -> tuple[int, int, int]:
    if plan == PLAN_ANONYMOUS:
        return PIPELINE_ANON_HOT_SLOTS, PIPELINE_ANON_WARM_SLOTS, PIPELINE_ANON_MONITOR_SLOTS
    return PIPELINE_HOT_SLOTS, PIPELINE_WARM_SLOTS, PIPELINE_MONITOR_SLOTS


def _lead_tier_key(row: dict[str, Any]) -> str:
    tier = (row.get("priority_tier") or "").strip().upper()
    if tier in ("HOT", "WARM", "COLD"):
        return tier
    score = row.get("score")
    overall = 0.0
    if isinstance(score, dict):
        overall = float(score.get("overall_score") or 0)
    elif score is not None:
        overall = float(score)
    if overall >= 85:
        return "HOT"
    if overall >= 65:
        return "WARM"
    return "COLD"


def trim_pipeline_leads_by_tier(leads: list[dict[str, Any]], plan: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    """Preserve HOT/WARM/monitoring buckets instead of truncating a flat HOT-first list."""
    hot_n, warm_n, cold_n = _tier_slots_for_plan(plan)
    hot: list[dict[str, Any]] = []
    warm: list[dict[str, Any]] = []
    cold: list[dict[str, Any]] = []
    for row in leads:
        bucket = _lead_tier_key(row)
        if bucket == "HOT":
            hot.append(row)
        elif bucket == "WARM":
            warm.append(row)
        else:
            cold.append(row)
    trimmed_hot = hot[:hot_n]
    trimmed_warm = warm[:warm_n]
    trimmed_cold = cold[:cold_n]
    tier_mix = {
        "hot": {"shown": len(trimmed_hot), "cap": hot_n},
        "warm": {"shown": len(trimmed_warm), "cap": warm_n},
        "monitoring": {"shown": len(trimmed_cold), "cap": cold_n},
    }
    return trimmed_hot + trimmed_warm + trimmed_cold, tier_mix


def entitlements_payload(
    plan: str,
    *,
    visible_count: int,
    tier_mix: Optional[dict[str, dict[str, int]]] = None,
) -> dict[str, Any]:
    saved_limit = saved_leads_limit_for_plan(plan)
    payload: dict[str, Any] = {
        "plan": plan,
        "pipeline_limit": pipeline_limit_for_plan(plan),
        "visible_count": visible_count,
        "saved_limit": saved_limit,
        "upgrade_url": "/pricing",
        "features": plan_feature_flags(plan),
    }
    if tier_mix:
        payload["tier_mix"] = tier_mix
    return payload


def _truncate(text: Optional[str], max_len: int) -> Optional[str]:
    if not text:
        return text
    t = str(text).strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def _teaser_copy(value: Optional[str], max_len: int) -> Optional[str]:
    """Clip rep-facing copy at sentence boundaries — never mid-word."""
    from app.services.lead_sales_copy import preview_sentences

    text = (value or "").strip()
    if not text:
        return None
    clipped = preview_sentences(text, max_sentences=2, max_chars=max_len)
    if clipped:
        return clipped
    return _truncate(text, max_len)


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
    row["share_summary"] = _teaser_copy(row.get("share_summary"), 240)
    row["share_blurb"] = _teaser_copy(row.get("share_blurb"), 160)
    row["pipeline_action"] = _teaser_copy(row.get("pipeline_action"), 200)
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
    tiered, tier_mix = trim_pipeline_leads_by_tier(leads, plan)
    trimmed = [sanitize_lead_for_plan(row, plan) for row in tiered]
    out = dict(feed)
    out["leads"] = trimmed
    out["entitlements"] = entitlements_payload(plan, visible_count=len(trimmed), tier_mix=tier_mix)
    return out
