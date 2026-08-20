"""
Plan entitlements for public pipeline surfaces and workspace saves.

Tiers:
  anonymous — no auth
  free      — signed in, default
  paid      — ADMIN_EMAILS, PAID_PLAN_EMAILS, or billing_tier / JWT plan in pro|premium|paid
"""
from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Optional


PLAN_ANONYMOUS = "anonymous"
PLAN_FREE = "free"
PLAN_PAID = "paid"

# Pro/Premium unlock full pipeline + research. Legacy "starter" maps to free until purchased as Pro.
PAID_PIPELINE_SLUGS = frozenset({"pro", "premium", "paid"})
BILLING_TIER_LABELS = {
    "free": "Free workspace",
    "starter": "Free workspace",
    "pro": "Pro",
    "premium": "Premium",
    "paid": "Pro",
}

PIPELINE_HOT_SLOTS = int(os.getenv("PIPELINE_HOT_SLOTS", "40"))
PIPELINE_WARM_SLOTS = int(os.getenv("PIPELINE_WARM_SLOTS", "30"))
PIPELINE_MONITOR_SLOTS = int(os.getenv("PIPELINE_MONITOR_SLOTS", "20"))
PIPELINE_TIERED_TOTAL = PIPELINE_HOT_SLOTS + PIPELINE_WARM_SLOTS + PIPELINE_MONITOR_SLOTS

# Signed-in free workspaces see 15 customer opportunities. Pro unlocks the full 90-lead feed.
PIPELINE_PREVIEW_HOT_SLOTS = 8
PIPELINE_PREVIEW_WARM_SLOTS = 5
PIPELINE_PREVIEW_MONITOR_SLOTS = 2
PIPELINE_LIMIT_PREVIEW = (
    PIPELINE_PREVIEW_HOT_SLOTS + PIPELINE_PREVIEW_WARM_SLOTS + PIPELINE_PREVIEW_MONITOR_SLOTS
)

# Anonymous URL submit / pipeline preview: 5 leads. Signup unlocks the 15-lead free feed.
PIPELINE_ANON_HOT_SLOTS = 3
PIPELINE_ANON_WARM_SLOTS = 2
PIPELINE_ANON_MONITOR_SLOTS = 0
PIPELINE_LIMIT_ANONYMOUS = (
    PIPELINE_ANON_HOT_SLOTS + PIPELINE_ANON_WARM_SLOTS + PIPELINE_ANON_MONITOR_SLOTS
)

PIPELINE_LIMIT_FREE = PIPELINE_LIMIT_PREVIEW
PIPELINE_FREE_HOT_SLOTS = PIPELINE_PREVIEW_HOT_SLOTS
PIPELINE_FREE_WARM_SLOTS = PIPELINE_PREVIEW_WARM_SLOTS
PIPELINE_FREE_MONITOR_SLOTS = PIPELINE_PREVIEW_MONITOR_SLOTS

PIPELINE_LIMIT_PAID = PIPELINE_TIERED_TOTAL
SAVED_LEADS_LIMIT_FREE = 5


def _is_admin_email(email: str) -> bool:
    from app.api.auth_deps import _is_admin

    return _is_admin(email)


def _billing_tier_from_db(db, uid: str) -> Optional[str]:
    if db is None or not uid:
        return None
    try:
        from sqlalchemy import text

        row = db.execute(
            text("SELECT billing_tier FROM user_profiles WHERE id = :uid"),
            {"uid": str(uid)},
        ).fetchone()
        if row and (row.billing_tier or "").strip():
            return str(row.billing_tier).strip().lower()
    except Exception:
        return None
    return None


def resolve_plan_tier(user: Optional[dict], db=None) -> str:
    if not user:
        return PLAN_ANONYMOUS
    slug = resolve_billing_tier_slug(user, db=db)
    if slug in PAID_PIPELINE_SLUGS:
        return PLAN_PAID
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
    return PLAN_FREE


def resolve_billing_tier_slug(user: Optional[dict], db=None) -> str:
    """JWT / DB / env billing slug — may differ from effective workspace plan."""
    if not user:
        return "anonymous"
    db_tier = _billing_tier_from_db(db, user.get("uid") or "")
    if db_tier and db_tier in PAID_PIPELINE_SLUGS:
        return db_tier
    email = (user.get("email") or "").strip()
    if email and _is_admin_email(email):
        return "pro"
    slug = (user.get("plan_tier") or user.get("plan") or "").strip().lower()
    if slug in PAID_PIPELINE_SLUGS:
        return slug
    if db_tier:
        return db_tier
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
    plan = resolve_plan_tier(user, db=db)
    billing = resolve_billing_tier_slug(user, db=db)
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
    if plan == PLAN_FREE:
        return PIPELINE_FREE_HOT_SLOTS, PIPELINE_FREE_WARM_SLOTS, PIPELINE_FREE_MONITOR_SLOTS
    return PIPELINE_HOT_SLOTS, PIPELINE_WARM_SLOTS, PIPELINE_MONITOR_SLOTS


def _lead_tier_key(row: dict[str, Any]) -> str:
    if row.get("monitoring_source") == "synthetic_warm_tail":
        return "COLD"
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
    """Preserve HOT/WARM/monitoring buckets instead of truncating a flat HOT-first list.

    For anonymous preview, also diversify HOT by industry so the first viewport
    is not five hospitality rows.
    """
    from app.services.lead_filter import is_junk
    from app.services.robot_vendor_names import is_known_robotics_vendor_name

    hot_n, warm_n, cold_n = _tier_slots_for_plan(plan)
    hot: list[dict[str, Any]] = []
    warm: list[dict[str, Any]] = []
    cold: list[dict[str, Any]] = []
    for row in leads:
        name = (row.get("company_name") or row.get("name") or "").strip()
        if name and is_known_robotics_vendor_name(name):
            continue  # never surface OEMs as buyer opportunities
        if name and is_junk(name, mode="buyer")[0]:
            continue  # runtime safety net for legacy headline rows that escaped ingest filtering
        bucket = _lead_tier_key(row)
        if bucket == "HOT":
            hot.append(row)
        elif bucket == "WARM":
            warm.append(row)
        else:
            cold.append(row)

    if plan == PLAN_ANONYMOUS:
        trimmed_hot = _diversify_by_industry(hot, hot_n)
    else:
        trimmed_hot = hot[:hot_n]
    trimmed_warm = warm[:warm_n]
    trimmed_cold = cold[:cold_n]

    trimmed = trimmed_hot + trimmed_warm + trimmed_cold

    # Preview/free feeds should not collapse when one bucket (often monitoring) is sparse.
    # Backfill remaining slots from highest-priority leftovers while preserving cap.
    preview_cap = pipeline_limit_for_plan(plan)
    if plan != PLAN_PAID and len(trimmed) < preview_cap:
        picked_ids = {
            row.get("id")
            for row in trimmed
            if isinstance(row, dict) and row.get("id") is not None
        }
        leftovers: list[dict[str, Any]] = []
        for bucket in (hot, warm, cold):
            for row in bucket:
                rid = row.get("id") if isinstance(row, dict) else None
                if rid in picked_ids:
                    continue
                leftovers.append(row)
        for row in leftovers:
            if len(trimmed) >= preview_cap:
                break
            trimmed.append(row)

    tier_mix = {
        "hot": {"shown": len(trimmed_hot), "cap": hot_n},
        "warm": {"shown": len(trimmed_warm), "cap": warm_n},
        "monitoring": {"shown": len(trimmed_cold), "cap": cold_n},
    }
    return trimmed, tier_mix


def _diversify_by_industry(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Round-robin distinct industries, then fill remaining slots by score order."""
    if limit <= 0 or not rows:
        return []
    seen_industries: set[str] = set()
    picked: list[dict[str, Any]] = []
    rest: list[dict[str, Any]] = []
    for row in rows:
        ind = (row.get("industry") or "").strip().lower() or "_unknown"
        if ind not in seen_industries and len(picked) < limit:
            seen_industries.add(ind)
            picked.append(row)
        else:
            rest.append(row)
    for row in rest:
        if len(picked) >= limit:
            break
        picked.append(row)
    return picked[:limit]


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

    evidence = row.get("crm_evidence")
    if isinstance(evidence, dict):
        teaser_evidence: dict[str, Any] = {}
        friction = _truncate(evidence.get("friction_point"), 180)
        if friction:
            teaser_evidence["friction_point"] = friction
        workflow = evidence.get("workflow_scope") if isinstance(evidence.get("workflow_scope"), dict) else {}
        if workflow:
            teaser_evidence["workflow_scope"] = {
                "count": workflow.get("count"),
                "label": _truncate(workflow.get("label"), 40),
                "items": [str(item) for item in (workflow.get("items") or [])[:3] if item],
            }
        timing = evidence.get("timing") if isinstance(evidence.get("timing"), dict) else {}
        if timing:
            teaser_evidence["timing"] = {
                "label": _truncate(timing.get("label"), 80),
                "source": _truncate(timing.get("source"), 30),
            }
        robot = evidence.get("robot_type") if isinstance(evidence.get("robot_type"), dict) else {}
        if robot:
            teaser_evidence["robot_type"] = {
                "label": _truncate(robot.get("label"), 80),
                "items": [str(item) for item in (robot.get("items") or [])[:3] if item],
            }
        budget = evidence.get("budget") if isinstance(evidence.get("budget"), dict) else {}
        if budget:
            teaser_evidence["budget"] = {
                "top_amount": _truncate(budget.get("top_amount"), 24),
                "has_budget": bool(budget.get("has_budget")),
            }
        dms = evidence.get("decision_makers") if isinstance(evidence.get("decision_makers"), list) else []
        if dms:
            teaser_evidence["decision_makers"] = [
                {
                    "name": _truncate((dm or {}).get("name"), 60),
                    "title": _truncate((dm or {}).get("title"), 80),
                }
                for dm in dms[:2]
                if isinstance(dm, dict)
            ]
        examples = evidence.get("similar_deployments") if isinstance(evidence.get("similar_deployments"), list) else []
        if examples:
            teaser_evidence["similar_deployments"] = [
                {
                    "title": _truncate((item or {}).get("title"), 100),
                    "summary": _truncate((item or {}).get("summary"), 140),
                }
                for item in examples[:2]
                if isinstance(item, dict)
            ]
        missing_fields = evidence.get("missing_fields") if isinstance(evidence.get("missing_fields"), list) else []
        if missing_fields:
            teaser_evidence["missing_fields"] = [
                {
                    "key": _truncate((item or {}).get("key"), 40),
                    "label": _truncate((item or {}).get("label"), 60),
                    "status": _truncate((item or {}).get("status"), 20),
                }
                for item in missing_fields[:8]
                if isinstance(item, dict)
            ]
        research_status = evidence.get("research_status") if isinstance(evidence.get("research_status"), dict) else {}
        if research_status:
            teaser_evidence["research_status"] = {
                "needs_research": bool(research_status.get("needs_research")),
                "state": _truncate(research_status.get("state"), 20),
                "missing_count": int(research_status.get("missing_count") or 0),
            }
        if teaser_evidence:
            row["crm_evidence"] = teaser_evidence
        else:
            row.pop("crm_evidence", None)
    else:
        row.pop("crm_evidence", None)

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
