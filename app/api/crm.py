"""
CRM API — teams + accounts (Bearer JWT). Prefix: /api/crm

  GET    /api/crm/teams              — list teams for user (auto-creates default workspace if none)
  POST   /api/crm/teams              — create a team; caller becomes owner
  GET    /api/crm/accounts           — list CRM accounts for a team
  POST   /api/crm/accounts           — create account (optional company_id pre-fills from companies)
  PATCH  /api/crm/accounts/{id}     — update outreach fields (team-scoped)
  POST   /api/crm/accounts/{id}/send-outreach — send draft via Resend (team-scoped)
"""

from __future__ import annotations

import logging
import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    ProgrammingError,
    SQLAlchemyError,
    StatementError,
)

from app.database import DATABASE_URL, get_db

logger = logging.getLogger(__name__)

# User-facing hints — the API often hit the wrong DB (Fly SQLite vs Supabase) even after SQL in the editor.
CRM_MIGRATION_HINT = (
    "Table `teams` is missing in the database THIS server uses. "
    "If you already ran SQL in Supabase, set Fly's DATABASE_URL to that same database: "
    "fly secrets set DATABASE_URL=\"postgresql://...\" (Transaction pooler port 6543). "
    "See DEPLOY_AND_ENV.md and GET /api/crm/db-status."
)
CRM_CONNECTION_HINT = (
    "Cannot connect to Postgres (connection refused, timeout, or SSL). "
    "Use Supabase Transaction pooler URI (port 6543, user postgres.PROJECT_REF) in fly secrets DATABASE_URL. "
    "See app/database.py comments and DEPLOY_AND_ENV.md."
)
CRM_GENERIC_DB_HINT = (
    "Database error in CRM. Check Fly logs. "
    "Confirm DATABASE_URL on Fly matches the Supabase project where you ran the migration."
)
from app.api.auth_deps import _require_user
from app.api.user import _ensure_profile
from app.models.company import Company
from app.models.crm import Team, TeamMember, CrmAccount, CrmEngagement, CrmTask, CrmNote
from app.models.outreach import OutreachMessage
from app.services.agent_messaging import REP_OUTREACH_CTA, cal_signature, rep_outreach_signature
from app.services.cal_insights import pick_cal_insight
from app.services.apollo_client import recommended_prospect_titles
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.sales_learning_agent import crm_workflow_intelligence, record_sales_experience
from app.services.deployment_conversion import (
    CONVERSION_STAGES,
    ensure_deployment_opportunity,
    record_conversion_transition,
)
from app.services.crm_engagement_sync import (
    serialize_engagement,
    sync_account_stage_to_engagement,
    sync_engagement_stage_to_account,
)
from app.services.sales_plan_agent import generate_sales_plan

router = APIRouter()


def _uid_uuid(user: dict) -> uuid.UUID:
    return uuid.UUID(str(user["uid"]))


def _team_rows_for_user(db: Session, uid: uuid.UUID) -> list[tuple[Team, str]]:
    q = (
        db.query(Team, TeamMember.role)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(TeamMember.user_id == uid)
        .order_by(Team.created_at.asc())
        .all()
    )
    return q


def _ensure_default_team(db: Session, uid: uuid.UUID, email: str) -> Team:
    """Create user_profiles row if needed, then a default team + membership if user has none."""
    _ensure_profile(db, str(uid), email)
    rows = _team_rows_for_user(db, uid)
    if rows:
        return rows[0][0]
    team = Team(name="My workspace", slug=None)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=uid, role="owner"))
    db.commit()
    db.refresh(team)
    return team


def _require_team_member(db: Session, uid: uuid.UUID, team_id: uuid.UUID) -> Team:
    m = (
        db.query(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(TeamMember.user_id == uid, Team.id == team_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Team not found or access denied")
    return m


# ── Schemas ──────────────────────────────────────────────────────────────────


class TeamOut(BaseModel):
    id: str
    name: str
    slug: Optional[str] = None
    role: str
    created_at: Optional[str] = None


class CreateTeamIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=120)


class CrmAccountOut(BaseModel):
    id: str
    team_id: str
    company_id: Optional[int] = None
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    owner_user_id: Optional[str] = None
    created_at: Optional[str] = None
    contact_email: Optional[str] = None
    outreach_draft: Optional[str] = None
    outreach_sent_at: Optional[str] = None
    outreach_stage: Optional[str] = None
    latest_outreach_message_id: Optional[str] = None
    # Enriched when company_id links to pipeline companies
    signal_score: Optional[float] = None
    overall_intent_score: Optional[float] = None
    lead_value_score: Optional[float] = None
    pipeline_priority_tier: Optional[str] = None
    workflow_intelligence: Optional[dict[str, Any]] = None
    prospect_search: Optional[dict[str, Any]] = None


class CreateAccountIn(BaseModel):
    team_id: Optional[uuid.UUID] = None
    company_id: Optional[int] = None
    name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None


class PatchCrmAccountIn(BaseModel):
    contact_email: Optional[str] = Field(None, max_length=320)
    outreach_draft: Optional[str] = None
    outreach_stage: Optional[str] = Field(None, max_length=64)
    account_type: Optional[str] = Field(None, pattern="^(buyer|vendor)$")


class SendOutreachIn(BaseModel):
    contact_email: Optional[str] = Field(None, max_length=320)
    outreach_draft: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=512)
    send_identity: str = "scout"
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    approved_style: Optional[str] = None


class DraftOutreachIn(BaseModel):
    contact_email: Optional[str] = Field(None, max_length=320)
    persona_traits: Optional[list[str]] = None
    collateral_policy: Optional[str] = None
    collateral_links: Optional[str] = None
    style_instruction: Optional[str] = None


class DeploymentTransitionIn(BaseModel):
    to_stage: str
    evidence_level: str
    contact_result: Optional[str] = None
    reason: Optional[str] = None
    evidence: Optional[list[dict[str, Any]]] = None
    facts_learned: Optional[dict[str, Any]] = None
    prediction_snapshot: Optional[dict[str, Any]] = None


def _serialize_team_row(team: Team, role: str) -> dict[str, Any]:
    return {
        "id": str(team.id),
        "name": team.name,
        "slug": team.slug,
        "role": role,
        "created_at": team.created_at.isoformat() if team.created_at else None,
    }


def _raise_crm_db_error(exc: Exception) -> None:
    """Map SQLAlchemy errors to actionable HTTP messages (not always 'run migration')."""
    logger.warning(
        "CRM DB error (%s): %s",
        type(exc).__name__,
        exc,
        exc_info=True,
    )
    if isinstance(exc, OperationalError):
        raise HTTPException(status_code=503, detail=CRM_CONNECTION_HINT) from exc
    if isinstance(exc, ProgrammingError):
        orig = str(getattr(exc, "orig", None) or exc)
        low = orig.lower()
        # Don't blame `teams` for every missing relation/column — surface the real object.
        if "undefinedcolumn" in low or ("column" in low and "does not exist" in low):
            raise HTTPException(
                status_code=503,
                detail=(
                    f"CRM schema mismatch (missing column). {orig[:220]} "
                    "Run pending Alembic migrations on Fly's DATABASE_URL, then retry."
                ),
            ) from exc
        if "undefinedtable" in low or ("relation" in low and "does not exist" in low) or "no such table" in low:
            if "teams" in low:
                raise HTTPException(status_code=503, detail=CRM_MIGRATION_HINT) from exc
            raise HTTPException(
                status_code=503,
                detail=(
                    f"CRM schema mismatch (missing table). {orig[:220]} "
                    "Confirm Fly DATABASE_URL and run migrations. See GET /api/crm/db-status."
                ),
            ) from exc
        if "does not exist" in low:
            raise HTTPException(
                status_code=503,
                detail=f"CRM schema mismatch: {orig[:240]}",
            ) from exc
        raise HTTPException(
            status_code=503,
            detail=f"SQL error: {str(getattr(exc, 'orig', exc))[:220]}",
        ) from exc
    if isinstance(exc, StatementError):
        orig = getattr(exc, "orig", None)
        msg = str(orig or exc)[:280]
        raise HTTPException(
            status_code=503,
            detail=f"Database error: {msg}",
        ) from exc
    if isinstance(exc, SQLAlchemyError):
        orig = getattr(exc, "orig", None)
        parts = [type(exc).__name__, str(exc).strip()]
        if orig is not None:
            parts.append(str(orig).strip())
        detail = " — ".join(p for p in parts if p)[:500]
        raise HTTPException(status_code=503, detail=f"Database error: {detail}") from exc
    raise exc


def _serialize_account(a: CrmAccount) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "team_id": str(a.team_id),
        "company_id": a.company_id,
        "name": a.name,
        "website": a.website,
        "industry": a.industry,
        "owner_user_id": str(a.owner_user_id) if a.owner_user_id else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "contact_email": getattr(a, "contact_email", None),
        "outreach_draft": getattr(a, "outreach_draft", None),
        "outreach_sent_at": a.outreach_sent_at.isoformat() if getattr(a, "outreach_sent_at", None) else None,
        "outreach_stage": getattr(a, "outreach_stage", None),
        "latest_outreach_message_id": None,
    }


def _reply_domain() -> str:
    raw = (
        os.getenv("SCOUT_REPLY_DOMAIN")
        or os.getenv("RESEND_REPLY_DOMAIN")
        or os.getenv("RESEND_FROM_EMAIL")
        or "readyforrobots.com"
    ).strip()
    if "<" in raw and ">" in raw:
        raw = raw.split("<", 1)[1].split(">", 1)[0]
    raw = raw.replace("mailto:", "").strip().strip("<>")
    if "://" in raw:
        raw = urlparse(raw).netloc or raw
    if "@" in raw:
        raw = raw.rsplit("@", 1)[1]
    raw = raw.strip().strip("/").lower()
    if not raw or " " in raw or "@" in raw:
        return "readyforrobots.com"
    return raw


def _reply_address(reply_token: str) -> str:
    local = (os.getenv("SCOUT_REPLY_LOCAL_PART") or "reply").strip().split("@", 1)[0] or "reply"
    return f"{local}+{reply_token}@{_reply_domain()}"


def _user_settings_row(db: Session, uid: uuid.UUID):
    return db.execute(
        text(
            """
            SELECT sender_name, sender_email, scout_automation_level,
                   reply_forwarding_enabled, reply_forward_email,
                   scout_message_style, scout_preferred_channel, scout_meeting_preference,
                   scout_default_cc, scout_default_bcc, scout_persona_traits,
                   scout_collateral_policy, scout_collateral_links, scout_background_briefing_enabled
            FROM user_settings
            WHERE user_id = :uid
            """
        ),
        {"uid": str(uid)},
    ).fetchone()


def _email_list(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        values = raw.replace(";", ",").split(",")
    elif isinstance(raw, list):
        values = raw
    else:
        return []
    return [str(x).strip() for x in values if str(x).strip() and "@" in str(x)]


def _infer_default_outreach_emails(acct: CrmAccount) -> tuple[str | None, list[str]]:
    """Return (primary@domain, cc list) inferred from website + industry when no contact is set."""
    from app.services.company_domain import normalize_website_domain
    from app.services.outreach_email_inference import infer_cc_outreach_emails, infer_primary_outreach_email

    domain = normalize_website_domain(getattr(acct, "website", None))
    if not domain:
        return None, []
    industry = getattr(acct, "industry", None)
    primary = infer_primary_outreach_email(domain, industry)
    cc = infer_cc_outreach_emails(domain, industry, primary=primary)
    return primary, cc


def _style_note(settings: Any) -> str:
    if not settings:
        return ""
    pieces: list[str] = []
    if getattr(settings, "scout_message_style", None):
        pieces.append(f"Style: {settings.scout_message_style}")
    channel = getattr(settings, "scout_preferred_channel", None)
    if channel and channel != "email":
        pieces.append(f"Preferred next step: move conversation toward {channel}.")
    if getattr(settings, "scout_meeting_preference", None):
        pieces.append(f"Meeting preference: {settings.scout_meeting_preference}")
    if getattr(settings, "scout_persona_traits", None):
        pieces.append(f"Persona traits: {settings.scout_persona_traits}")
    if getattr(settings, "scout_collateral_policy", None):
        pieces.append(f"Collateral policy: {settings.scout_collateral_policy}")
    if getattr(settings, "scout_collateral_links", None):
        pieces.append(f"Collateral links: {settings.scout_collateral_links}")
    return "\n".join(pieces)


def _line_items(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return [x.strip() for x in str(raw).replace(";", ",").split(",") if x.strip()]


def _collateral_note(policy: str, links: str | None) -> str:
    clean_links = [x for x in _line_items(links) if x.startswith(("http://", "https://"))]
    if policy == "none" or not clean_links:
        return ""
    label = "I can also send over a relevant case study" if policy == "selective" else "I’m including a few useful resources"
    return f"\n\n{label}: " + ", ".join(clean_links[:3])


def _draft_subject(acct: CrmAccount, variant_id: str | None = None) -> str:
    """Short, curiosity-driving subject. Buyer vs vendor aware.

    When a trust-first `variant_id` is supplied for a buyer, the subject matches
    that angle's tone (humble/question-led) instead of the legacy pitch subjects.
    """
    name = (acct.name or "your team").strip()
    industry = (acct.industry or "").strip().lower()
    account_type = getattr(acct, "account_type", "buyer") or "buyer"

    if account_type == "buyer" and variant_id:
        from app.services.agent_messaging import buyer_variant_subject

        return buyer_variant_subject(name, acct.industry or "", variant_id)

    if account_type == "vendor":
        # Vendor = robot company — subject is about the buyer lead we found them
        if industry in ("hospitality", "hotels", "casinos & gaming"):
            return f"hospitality buyer looking for automation"
        if industry in ("logistics", "warehousing"):
            return f"logistics lead — active buyer signal"
        if industry in ("healthcare", "medical technology"):
            return f"healthcare operator — automation interest"
        return f"buyer lead for {name}"

    # Buyer = company seeking automation — value-first subject, matches the shortlist CTA
    if industry in ("hospitality", "hotels", "casinos & gaming"):
        return f"{name}: robots worth a pilot (and which to skip)"
    if industry in ("food service", "food processing & manufacturing"):
        return f"{name}: the automation math"
    if industry in ("healthcare", "medical technology"):
        return f"robotics that actually fit {name}"
    # Logistics, warehousing, and everything else land on the shortlist framing.
    return f"a robotics shortlist for {name}"


def _draft_buyer_body(acct: CrmAccount, settings: Any, traits: list[str], collateral_policy: str, collateral_links: str | None) -> str:
    """Email from robot sales rep to buyer ops — first person, no platform branding."""
    def _display_account_name(raw: str | None) -> str:
        name = (raw or "your team").strip()
        # Some upstream flows can accidentally append recommended-action text to
        # account names (for example: "Americold -- contact new executive...").
        # Keep the buyer-facing draft anchored to the clean company name.
        for sep in (" -- ", " — ", " - "):
            if sep in name:
                head, tail = name.split(sep, 1)
                low_tail = tail.strip().lower()
                if any(
                    token in low_tail
                    for token in (
                        "contact ",
                        "pitch",
                        "budget",
                        "build-out",
                        "reach out",
                        "new executive",
                    )
                ):
                    name = head.strip() or name
                    break
        return name

    industry = (acct.industry or "your industry").strip()
    name = _display_account_name(acct.name)
    industry_lower = industry.lower()
    closing_line = f"If helpful, I'll send a short, vendor-neutral recommendation for {name} before we discuss anything live."

    lines: list[str] = [f"Hi {name},", ""]

    if industry_lower in ("logistics", "warehousing"):
        lines.append(
            "I work with logistics teams on one thing: picking the first workflow where automation "
            "actually pays back in live operations."
        )
        lines.extend(
            [
                "",
                "The best first project is usually receiving, replenishment, or exception handling "
                "rather than the most visible robot demo.",
            ]
        )
    elif industry_lower in ("hospitality", "hotels", "casinos & gaming"):
        closing_line = (
            f"If helpful, I'll send a short, vendor-neutral housekeeping and turnover workflow "
            f"recommendation for {name} before we discuss anything live."
        )
        lines.append(
            "I work with hospitality teams on one thing: choosing service and cleaning workflows "
            "that still perform under real weekend occupancy."
        )
        lines.extend(
            [
                "",
                "The win is usually one constrained workflow with clear housekeeping turnover or overnight "
                "coverage gaps, not a broad rollout.",
            ]
        )
    elif industry_lower in ("healthcare", "medical technology"):
        closing_line = (
            f"If helpful, I'll send a short, vendor-neutral EVS and transport workflow "
            f"recommendation for {name} before we discuss anything live."
        )
        lines.append(
            "I work with healthcare ops teams on one thing: selecting transport and internal logistics "
            "workflows where AMRs reduce staff miles without adding operational friction."
        )
        lines.extend(
            [
                "",
                "The highest-payback cases tend to be repetitive EVS, meds/supplies, and lab movement "
                "routes with clean handoffs and elevator access.",
            ]
        )
    elif industry_lower in ("food service", "food processing & manufacturing"):
        closing_line = (
            f"If helpful, I'll send a short, vendor-neutral changeover and OEE-focused workflow "
            f"recommendation for {name} before we discuss anything live."
        )
        lines.append(
            "I work with food teams on one thing: picking back-of-house and line workflows where automation "
            "relieves throughput pressure without creating changeover headaches."
        )
        lines.extend(
            [
                "",
                "The projects that last usually start with one repeatable bottleneck, with changeover time "
                "and OEE tracked before expanding.",
            ]
        )
    else:
        lines.append(
            "I help operations teams scope where automation is likely to pay back quickly and where "
            "it is better to wait."
        )
        lines.extend(
            [
                "",
                f"If useful, I can send a brief view of which workflow at {name} is most likely to deliver early ROI.",
            ]
        )

    lines.append("")
    lines.append(closing_line)
    lines.append("")
    lines.append(REP_OUTREACH_CTA)

    collateral = _collateral_note(collateral_policy, collateral_links)
    if collateral:
        lines.extend(["", collateral.replace("I can also send", "Happy to send").replace("I’m including", "I can include")])

    lines.extend(["", rep_outreach_signature()])
    return "\n".join(lines)


def _draft_vendor_body(acct: CrmAccount, settings: Any, traits: list[str], collateral_policy: str, collateral_links: str | None) -> str:
    """Email to a robot company — Cal as veteran sherpa, not a sales blast."""
    from app.services.agent_messaging import (
        CAL_VENDOR_BUYER_MATCH_CTA,
        CAL_VENDOR_STRATEGY_CALL_CTA,
        cal_vendor_match_paragraph,
        cal_signature,
    )

    industry = (acct.industry or "your space").strip()
    name = (acct.name or "your team").strip()
    selected_traits = set(traits)
    allow_humor = "humor" in selected_traits

    lines: list[str] = ["Hi,", ""]

    lines.append(cal_vendor_match_paragraph(name, industry=industry))
    lines.append("")
    lines.append(pick_cal_insight(company_name=name, allow_humor=allow_humor, audience="vendor"))
    lines.append("")
    lines.append(
        f"We're tracking active buyer signals in {industry} — labor pressure, expansion, CapEx — "
        f"accounts with real purchase intent, not list noise."
    )
    lines.append("")

    if "inquisitive" in selected_traits:
        lines.append(
            "What does your ideal buyer look like right now — industry, size, use case? "
            "I'll match against what we're seeing and be straight about fit."
        )
    else:
        channel = getattr(settings, "scout_preferred_channel", "email") if settings else "email"
        meeting = getattr(settings, "scout_meeting_preference", None) if settings else None
        if channel in ("phone", "meeting"):
            lines.append(meeting or CAL_VENDOR_STRATEGY_CALL_CTA)
        else:
            lines.append(CAL_VENDOR_BUYER_MATCH_CTA)

    collateral = _collateral_note(collateral_policy, collateral_links)
    if collateral:
        lines.extend(["", collateral])

    lines.extend(["", cal_signature()])
    return "\n".join(lines)


def _draft_body(acct: CrmAccount, settings: Any, traits: list[str], style_instruction: str, collateral_policy: str, collateral_links: str | None, company: Optional[Any] = None) -> str:
    """Route to buyer, vendor, or StageGate draft based on account_type and pipeline."""
    if company is not None:
        from app.services.stagegate_crm_bridge import cal_draft_for_stagegate_company, is_stagegate_company

        if is_stagegate_company(company):
            return cal_draft_for_stagegate_company(company)["body"]

    account_type = getattr(acct, "account_type", "buyer") or "buyer"
    if account_type == "vendor":
        return _draft_vendor_body(acct, settings, traits, collateral_policy, collateral_links)
    return _draft_buyer_body(acct, settings, traits, collateral_policy, collateral_links)


def _draft_subject_for_account(acct: CrmAccount, company: Optional[Any] = None) -> str:
    if company is not None:
        from app.services.stagegate_crm_bridge import cal_draft_for_stagegate_company, is_stagegate_company

        if is_stagegate_company(company):
            return cal_draft_for_stagegate_company(company)["subject"]
    return _draft_subject(acct)


def _response_suggestions(acct: CrmAccount, settings: Any) -> list[dict[str, str]]:
    industry = acct.industry or "this industry"
    suggestions = [
        {
            "trigger": "Positive reply",
            "action": "Ask one qualification question, then offer a short call or meeting.",
            "why": f"Keep momentum while the lead is engaged in {industry}.",
        },
        {
            "trigger": "No response after 3-5 business days",
            "action": "Send one concise follow-up with a fresh signal or relevant example.",
            "why": "Cal should add new value, not just bump the same email.",
        },
        {
            "trigger": "Short or annoyed reply",
            "action": "Acknowledge directly, reduce pressure, and ask permission before sending anything else.",
            "why": "Tone of voice matters; Cal should preserve the relationship.",
        },
        {
            "trigger": "New research/news signal",
            "action": "Suggest an updated note referencing the new fact before the next touch.",
            "why": "Fresh context makes outreach feel informed instead of automated.",
        },
    ]
    if settings and getattr(settings, "scout_background_briefing_enabled", True):
        suggestions.append(
            {
                "trigger": "Background SIGNAL brief",
                "action": "Monitor replies, no-response timing, research updates, and tone; surface next-best-action ideas to the user.",
            "why": "SIGNAL monitors the workflow while Cal handles communication.",
            }
        )
    return suggestions


def _crm_account_for_user(db: Session, uid: uuid.UUID, account_id: uuid.UUID) -> Optional[CrmAccount]:
    return (
        db.query(CrmAccount)
        .join(TeamMember, TeamMember.team_id == CrmAccount.team_id)
        .filter(TeamMember.user_id == uid, CrmAccount.id == account_id)
        .first()
    )


def _pipeline_snapshot_for_company_row(c: Company) -> dict[str, Any]:
    """Compute signal / intent / value / tier for a loaded Company (signals + scores)."""
    from app.services.automation_profile import get_automation_profile_for_response
    from app.services.lead_filter import classify_lead, pick_primary_score
    from app.services.lead_value import compute_lead_value
    from app.services.signal_ranker import compute_lead_aggregate_signal_score

    sigs = c.signals or []
    ss = compute_lead_aggregate_signal_score(sigs)
    sc = pick_primary_score(c.scores)
    intent = float(sc.overall_intent_score) if sc else 0.0
    _, _, pri = classify_lead(c, c.scores, sigs)
    ap = get_automation_profile_for_response(c)
    lv = compute_lead_value(intent, c.employee_estimate, ap, sigs)
    return {
        "signal_score": ss,
        "overall_intent_score": round(intent, 1),
        "lead_value_score": lv["lead_value_score"],
        "pipeline_priority_tier": pri.tier,
    }


def _serialize_account_enriched(a: CrmAccount, pipeline: Optional[dict[str, Any]]) -> dict[str, Any]:
    base = _serialize_account(a)
    if not pipeline:
        base.update(
            {
                "signal_score": None,
                "overall_intent_score": None,
                "lead_value_score": None,
                "pipeline_priority_tier": None,
            }
        )
    else:
        base.update(pipeline)
    base["workflow_intelligence"] = None
    return base


def _attach_workflow_intelligence(db: Session, account: CrmAccount, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        payload["workflow_intelligence"] = crm_workflow_intelligence(db, account)
    except Exception:
        logger.warning("CRM workflow intelligence failed for account=%s", account.id, exc_info=True)
        payload["workflow_intelligence"] = None
    payload["prospect_search"] = {
        "provider": "apollo",
        "organization_name": account.name,
        "organization_domain": _domain_from_url(account.website),
        "recommended_titles": recommended_prospect_titles(account.industry, account.outreach_stage),
    }
    return payload


def _domain_from_url(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip().lower()
    raw = raw.removeprefix("https://").removeprefix("http://").removeprefix("www.")
    return raw.split("/", 1)[0] or None


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/db-status")
def crm_db_status(user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    """
    Quick check: does this API process use Postgres vs SQLite, and does public.teams exist?
    Use when CRM says tables are missing — usually DATABASE_URL on Fly ≠ DB where you ran SQL.
    """
    url = (DATABASE_URL or "").lower()
    if "sqlite" in url:
        kind = "sqlite"
    elif "postgresql" in url:
        kind = "postgresql"
    else:
        kind = "unknown"

    teams = False
    err: Optional[str] = None
    try:
        if kind == "postgresql":
            teams = bool(db.execute(text("SELECT to_regclass('public.teams') IS NOT NULL")).scalar())
        elif kind == "sqlite":
            teams = (
                db.execute(
                    text("SELECT 1 FROM sqlite_master WHERE type='table' AND name='teams' LIMIT 1")
                ).first()
                is not None
            )
    except Exception as e:
        err = str(e)[:400]
        logger.warning("crm db-status: %s", e)

    hints: list[str] = []
    if kind == "sqlite":
        hints.append(
            "Server is on SQLite — production CRM needs Postgres. "
            "Set DATABASE_URL via: fly secrets set DATABASE_URL=\"postgresql://...\" "
            "(copy Transaction pooler string from Supabase → Database)."
        )
    elif kind == "postgresql" and not teams and not err:
        hints.append(
            "Postgres is connected but public.teams is missing. "
            "Run migrations/sql/c7d8e9f0a1b2_add_crm_teams_core.sql on this same database (or fix DATABASE_URL)."
        )
    elif kind == "postgresql" and teams:
        hints.append("public.teams exists — if CRM still fails, check logs for another error.")
    if err:
        hints.append(f"Check failed: {err}")

    return {
        "database_driver": kind,
        "public_teams_table_exists": teams,
        "hints": hints,
    }


@router.get("/teams", response_model=list[TeamOut])
def list_teams(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        _ensure_default_team(db, uid, user.get("email") or "")
        rows = _team_rows_for_user(db, uid)
        return [_serialize_team_row(t, role) for t, role in rows]
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)


@router.post("/teams", response_model=TeamOut)
def create_team(
    body: CreateTeamIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        _ensure_profile(db, str(uid), user.get("email") or "")
        team = Team(name=body.name.strip(), slug=body.slug.strip() if body.slug else None)
        db.add(team)
        db.flush()
        db.add(TeamMember(team_id=team.id, user_id=uid, role="owner"))
        db.commit()
        db.refresh(team)
        return _serialize_team_row(team, "owner")
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.warning("CRM create_team integrity: %s", e)
        raise HTTPException(status_code=409, detail="Slug already in use or conflict") from e
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)


@router.get("/accounts", response_model=list[CrmAccountOut])
def list_accounts(
    team_id: Optional[uuid.UUID] = Query(None, description="Defaults to your first team"),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        default = _ensure_default_team(db, uid, user.get("email") or "")
        tid = team_id or default.id
        _require_team_member(db, uid, tid)
        accounts = (
            db.query(CrmAccount)
            .filter(CrmAccount.team_id == tid)
            .order_by(CrmAccount.created_at.desc())
            .all()
        )
        ids = list({a.company_id for a in accounts if a.company_id})
        by_id: dict[int, Company] = {}
        if ids:
            rows = (
                db.query(Company)
                .options(joinedload(Company.signals), joinedload(Company.scores))
                .filter(Company.id.in_(ids))
                .all()
            )
            by_id = {c.id: c for c in rows}
        out: list[dict[str, Any]] = []
        for a in accounts:
            pl = None
            if a.company_id and a.company_id in by_id:
                try:
                    pl = _pipeline_snapshot_for_company_row(by_id[a.company_id])
                except Exception:
                    logger.warning("CRM pipeline snapshot failed for company_id=%s", a.company_id, exc_info=True)
            out.append(_attach_workflow_intelligence(db, a, _serialize_account_enriched(a, pl)))
        return out
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)


@router.post("/accounts", response_model=CrmAccountOut)
def create_account(
    body: CreateAccountIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        _ensure_profile(db, str(uid), user.get("email") or "")
        default = _ensure_default_team(db, uid, user.get("email") or "")
        tid = body.team_id or default.id
        _require_team_member(db, uid, tid)

        name = (body.name or "").strip() or None
        website = body.website
        industry = body.industry

        if body.company_id is not None:
            co = db.get(Company, body.company_id)
            if not co:
                raise HTTPException(status_code=404, detail="company_id not found")
            name = name or (co.name or "Account")
            if website is None:
                website = co.website
            if industry is None:
                industry = co.industry
        if not name:
            raise HTTPException(status_code=400, detail="name is required when company_id is omitted")

        existing = None
        created = False
        if body.company_id is not None:
            existing = (
                db.query(CrmAccount)
                .filter(CrmAccount.team_id == tid, CrmAccount.company_id == body.company_id)
                .first()
            )
        if existing:
            if name:
                existing.name = name
            if website is not None:
                existing.website = website
            if industry is not None:
                existing.industry = industry
            existing.owner_user_id = existing.owner_user_id or uid
            if not existing.outreach_stage:
                existing.outreach_stage = "new"
            sync_account_stage_to_engagement(db, existing)
            db.commit()
            db.refresh(existing)
            row = existing
        else:
            from app.services.plan_entitlements import (
                assert_can_save_lead,
                count_workspace_leads,
                resolve_plan_tier,
            )

            plan = resolve_plan_tier(user)
            assert_can_save_lead(plan, count_workspace_leads(db, uid))
            row = CrmAccount(
            team_id=tid,
            company_id=body.company_id,
            name=name,
            website=website,
            industry=industry,
            owner_user_id=uid,
            outreach_stage="new",
            )
            db.add(row)
            db.flush()
            created = True
            sync_account_stage_to_engagement(db, row)
        # Conversion opportunity is best-effort — never block saving the CRM lead on schema drift.
        opportunity = None
        try:
            with db.begin_nested():
                opportunity = ensure_deployment_opportunity(db, account=row, owner_user_id=uid)
        except Exception:
            logger.warning(
                "CRM ensure_deployment_opportunity failed for account %s — lead still saved",
                getattr(row, "id", None),
                exc_info=True,
            )
            opportunity = None
        if created:
            try:
                with db.begin_nested():
                    record_sales_experience(
                        db,
                        event_type="crm_lead_saved",
                        outcome="observed",
                        team_id=row.team_id,
                        user_id=uid,
                        crm_account_id=row.id,
                        sales_opportunity_id=opportunity.id if opportunity is not None else None,
                        company_id=row.company_id,
                        channel="crm",
                        confidence=0.85,
                        payload={
                            "source": "crm_create_account",
                            "deployment_opportunity_id": (
                                opportunity.payload.get("public_id")
                                if opportunity is not None
                                and isinstance(getattr(opportunity, "payload", None), dict)
                                else None
                            ),
                        },
                    )
            except Exception:
                logger.warning(
                    "CRM record_sales_experience failed for account %s — lead still saved",
                    getattr(row, "id", None),
                    exc_info=True,
                )
        db.commit()
        db.refresh(row)
        # Best-effort named contact fill on save (Hunter → Apollo waterfall).
        if row.company_id and not (row.contact_email or "").strip():
            try:
                from app.services.lead_enrichment import enrich_company_and_contact

                co_enrich = db.get(Company, row.company_id)
                if co_enrich:
                    enrich_company_and_contact(
                        co_enrich,
                        row,
                        sleep_s=0,
                        use_apollo=True,
                        db=db,
                        persist_contact=True,
                    )
                    db.commit()
                    db.refresh(row)
            except Exception:
                logger.info(
                    "CRM save-time contact enrichment skipped for account %s",
                    row.id,
                    exc_info=True,
                )
                try:
                    db.rollback()
                except Exception:
                    pass
        pl = None
        if row.company_id:
            co = (
                db.query(Company)
                .options(joinedload(Company.signals), joinedload(Company.scores))
                .filter(Company.id == row.company_id)
                .first()
            )
            if co:
                try:
                    pl = _pipeline_snapshot_for_company_row(co)
                except Exception:
                    logger.warning(
                        "CRM pipeline snapshot failed for new account company_id=%s",
                        row.company_id,
                        exc_info=True,
                    )
        return _attach_workflow_intelligence(db, row, _serialize_account_enriched(row, pl))
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.warning("CRM create_account integrity: %s", e)
        raise HTTPException(
            status_code=409,
            detail="An account for this company already exists in this team",
        ) from e
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)


@router.post("/accounts/{account_id}/deployment-transition")
def transition_account_deployment(
    account_id: str,
    body: DeploymentTransitionIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        aid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account id") from None
    acct = _crm_account_for_user(db, uid, aid)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found or access denied")
    try:
        opportunity = ensure_deployment_opportunity(db, account=acct, owner_user_id=uid)
        event = record_conversion_transition(
            db,
            opportunity=opportunity,
            to_stage=body.to_stage,
            actor="seller",
            occurred_at=datetime.now(timezone.utc).isoformat(),
            evidence_level=body.evidence_level,
            prediction_snapshot=body.prediction_snapshot,
            contact_result=body.contact_result,
            reason=body.reason,
            evidence=body.evidence,
            facts_learned=body.facts_learned,
        )
        db.commit()
        return {
            "opportunity_id": opportunity.payload.get("public_id"),
            "stage": opportunity.current_stage,
            "disposition": getattr(opportunity, "disposition", None)
            or (opportunity.payload or {}).get("disposition", "active"),
            "event_id": str(event.id),
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OperationalError, ProgrammingError, SQLAlchemyError) as exc:
        db.rollback()
        _raise_crm_db_error(exc)


@router.patch("/accounts/{account_id}", response_model=CrmAccountOut)
def patch_account(
    account_id: str,
    body: PatchCrmAccountIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        try:
            aid = uuid.UUID(account_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid account id") from None
        acct = _crm_account_for_user(db, uid, aid)
        if not acct:
            raise HTTPException(status_code=404, detail="Account not found or access denied")
        patch = body.model_dump(exclude_unset=True)
        if "contact_email" in patch:
            acct.contact_email = patch["contact_email"]
        if "outreach_draft" in patch:
            acct.outreach_draft = patch["outreach_draft"]
        if "outreach_stage" in patch:
            acct.outreach_stage = patch["outreach_stage"]
        if "account_type" in patch:
            acct.account_type = patch["account_type"]
        if "outreach_stage" in patch:
            sync_account_stage_to_engagement(db, acct)
        db.commit()
        db.refresh(acct)
        pl = None
        if acct.company_id:
            co = (
                db.query(Company)
                .options(joinedload(Company.signals), joinedload(Company.scores))
                .filter(Company.id == acct.company_id)
                .first()
            )
            if co:
                try:
                    pl = _pipeline_snapshot_for_company_row(co)
                except Exception:
                    logger.warning(
                        "CRM pipeline snapshot failed on patch company_id=%s",
                        acct.company_id,
                        exc_info=True,
                    )
        return _attach_workflow_intelligence(db, acct, _serialize_account_enriched(acct, pl))
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)


def _serialize_note(row: CrmNote) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "crm_account_id": str(row.crm_account_id),
        "engagement_id": str(row.engagement_id) if row.engagement_id else None,
        "body": row.body,
        "source": row.source,
        "author_user_id": str(row.author_user_id) if row.author_user_id else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _serialize_outreach_message(row: OutreachMessage) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "to_email": row.to_email,
        "subject": row.subject,
        "status": row.status,
        "send_identity": row.send_identity,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/accounts/{account_id}")
def get_account_detail(
    account_id: str,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        try:
            aid = uuid.UUID(account_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid account id") from None
        acct = _crm_account_for_user(db, uid, aid)
        if not acct:
            raise HTTPException(status_code=404, detail="Account not found or access denied")

        pl = None
        if acct.company_id:
            co = (
                db.query(Company)
                .options(joinedload(Company.signals), joinedload(Company.scores))
                .filter(Company.id == acct.company_id)
                .first()
            )
            if co:
                try:
                    pl = _pipeline_snapshot_for_company_row(co)
                except Exception:
                    logger.warning("CRM detail pipeline snapshot failed company_id=%s", acct.company_id, exc_info=True)

        engagements = (
            db.query(CrmEngagement)
            .filter(CrmEngagement.crm_account_id == acct.id)
            .order_by(CrmEngagement.updated_at.desc())
            .limit(20)
            .all()
        )
        tasks = (
            db.query(CrmTask)
            .filter(CrmTask.crm_account_id == acct.id)
            .order_by(CrmTask.due_at.asc().nullslast(), CrmTask.created_at.desc())
            .limit(50)
            .all()
        )
        notes = (
            db.query(CrmNote)
            .filter(CrmNote.crm_account_id == acct.id)
            .order_by(CrmNote.created_at.desc())
            .limit(50)
            .all()
        )
        outreach = (
            db.query(OutreachMessage)
            .filter(OutreachMessage.crm_account_id == acct.id)
            .order_by(OutreachMessage.sent_at.desc().nullslast(), OutreachMessage.created_at.desc())
            .limit(25)
            .all()
        )

        timeline: list[dict[str, Any]] = []
        if acct.created_at:
            timeline.append(
                {
                    "type": "account_created",
                    "label": "Saved to CRM",
                    "at": acct.created_at.isoformat(),
                }
            )
        for msg in outreach:
            timeline.append(
                {
                    "type": "outreach_sent",
                    "label": f"Outreach sent to {msg.to_email}",
                    "at": (msg.sent_at or msg.created_at).isoformat() if (msg.sent_at or msg.created_at) else None,
                    "meta": {"subject": msg.subject, "status": msg.status},
                }
            )
        for note in notes:
            timeline.append(
                {
                    "type": "note",
                    "label": note.body[:120],
                    "at": note.created_at.isoformat() if note.created_at else None,
                    "meta": {"source": note.source},
                }
            )
        for task in tasks:
            if task.status == "done":
                timeline.append(
                    {
                        "type": "task_done",
                        "label": task.title,
                        "at": task.updated_at.isoformat() if task.updated_at else None,
                    }
                )
        timeline.sort(key=lambda item: item.get("at") or "", reverse=True)

        open_engagement = next((e for e in engagements if e.status == "open"), None)
        if not open_engagement and acct.outreach_stage:
            open_engagement = sync_account_stage_to_engagement(db, acct)
            db.commit()
            if open_engagement:
                engagements = [open_engagement, *[e for e in engagements if e.id != open_engagement.id]]

        account_payload = _attach_workflow_intelligence(db, acct, _serialize_account_enriched(acct, pl))
        return {
            "account": account_payload,
            "engagement": serialize_engagement(open_engagement) if open_engagement else None,
            "engagements": [serialize_engagement(e) for e in engagements],
            "tasks": [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "body": row.body,
                    "status": row.status,
                    "priority": row.priority,
                    "due_at": row.due_at.isoformat() if row.due_at else None,
                    "source": row.source,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in tasks
            ],
            "notes": [_serialize_note(row) for row in notes],
            "outreach_history": [_serialize_outreach_message(row) for row in outreach],
            "timeline": timeline[:40],
        }
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)


@router.get("/accounts/{account_id}/notes")
def list_account_notes(
    account_id: str,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        aid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account id") from None
    acct = _crm_account_for_user(db, uid, aid)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found or access denied")
    rows = (
        db.query(CrmNote)
        .filter(CrmNote.crm_account_id == acct.id)
        .order_by(CrmNote.created_at.desc())
        .limit(100)
        .all()
    )
    return [_serialize_note(row) for row in rows]


@router.post("/accounts/{account_id}/notes")
def create_account_note(
    account_id: str,
    body: NoteCreateIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        aid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account id") from None
    acct = _crm_account_for_user(db, uid, aid)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found or access denied")
    engagement_id = None
    if body.engagement_id:
        try:
            engagement_id = uuid.UUID(body.engagement_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid engagement id") from None
    note = CrmNote(
        team_id=acct.team_id,
        crm_account_id=acct.id,
        engagement_id=engagement_id,
        author_user_id=uid,
        body=body.body.strip(),
        source="user",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return _serialize_note(note)


@router.post("/accounts/{account_id}/draft-outreach")
def draft_account_outreach(
    account_id: str,
    body: DraftOutreachIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        try:
            aid = uuid.UUID(account_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid account id") from None
        acct = _crm_account_for_user(db, uid, aid)
        if not acct:
            raise HTTPException(status_code=404, detail="Account not found or access denied")
        settings = _user_settings_row(db, uid)
        patch = body.model_dump(exclude_unset=True)
        traits = _line_items(patch.get("persona_traits")) or _line_items(settings.scout_persona_traits if settings else None)
        collateral_policy = (patch.get("collateral_policy") or (settings.scout_collateral_policy if settings else "selective") or "selective").strip()
        if collateral_policy not in ("none", "selective", "all"):
            collateral_policy = "selective"
        collateral_links = patch.get("collateral_links")
        if collateral_links is None and settings:
            collateral_links = settings.scout_collateral_links
        style_instruction = (patch.get("style_instruction") or (settings.scout_message_style if settings else "") or "").strip()

        company = None
        if acct.company_id:
            company = db.query(Company).filter(Company.id == acct.company_id).first()

        subject = _draft_subject_for_account(acct, company)
        draft = _draft_body(acct, settings, traits, style_instruction, collateral_policy, collateral_links, company)
        explicit_contact = patch.get("contact_email") or acct.contact_email
        inferred_primary, inferred_cc = (None, []) if explicit_contact else _infer_default_outreach_emails(acct)
        acct.contact_email = explicit_contact or inferred_primary
        acct.outreach_draft = draft
        acct.outreach_stage = "draft_ready"

        db.execute(
            text(
                """
                INSERT INTO user_settings
                    (user_id, scout_message_style, scout_persona_traits, scout_collateral_policy,
                     scout_collateral_links, updated_at)
                VALUES
                    (:uid, :style, :traits, :policy, :links, now())
                ON CONFLICT (user_id) DO UPDATE SET
                    scout_message_style = EXCLUDED.scout_message_style,
                    scout_persona_traits = EXCLUDED.scout_persona_traits,
                    scout_collateral_policy = EXCLUDED.scout_collateral_policy,
                    scout_collateral_links = EXCLUDED.scout_collateral_links,
                    updated_at = now()
                """
            ),
            {
                "uid": str(uid),
                "style": style_instruction or None,
                "traits": ", ".join(traits) or None,
                "policy": collateral_policy,
                "links": collateral_links,
            },
        )
        db.commit()
        record_sales_experience(
            db,
            event_type="crm_draft_created",
            outcome="observed",
            team_id=acct.team_id,
            user_id=uid,
            crm_account_id=acct.id,
            company_id=acct.company_id,
            channel="email",
            confidence=0.78,
            payload={"subject": subject, "stage": "draft_ready"},
        )
        default_to = acct.contact_email
        default_cc = inferred_cc if not explicit_contact else []
        return {
            "subject": subject,
            "outreach_draft": draft,
            "outreach_stage": "draft_ready",
            "contact_email": default_to,
            "default_cc": default_cc,
            "persona_traits": traits,
            "collateral_policy": collateral_policy,
            "collateral_links": collateral_links,
            "suggestions": _response_suggestions(acct, settings),
            "checkpoint": "Cal drafted this for review. Edit it, then approve before sending.",
        }
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)


@router.post("/accounts/{account_id}/send-outreach")
def send_account_outreach(
    account_id: str,
    body: SendOutreachIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    try:
        uid = _uid_uuid(user)
        try:
            aid = uuid.UUID(account_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid account id") from None
        acct = _crm_account_for_user(db, uid, aid)
        if not acct:
            raise HTTPException(status_code=404, detail="Account not found or access denied")

        patch = body.model_dump(exclude_unset=True)
        explicit_contact = (patch.get("contact_email") or acct.contact_email or "").strip()
        outreach_draft = (patch.get("outreach_draft") or acct.outreach_draft or "").strip()

        inferred_primary, inferred_cc = (None, []) if explicit_contact else _infer_default_outreach_emails(acct)
        contact_email = explicit_contact or inferred_primary or ""
        if not contact_email or "@" not in contact_email:
            raise HTTPException(status_code=400, detail="No contact email on file for this account. Add one or ensure the account has a website domain.")
        if not outreach_draft:
            raise HTTPException(status_code=400, detail="No outreach draft on file for this account")

        settings = _user_settings_row(db, uid)
        sender_name = (settings.sender_name if settings else None) or "Cal"
        subject = (patch.get("subject") or f"Automation opportunity — {acct.name}").strip()
        reply_token = secrets.token_urlsafe(18)
        reply_to = _reply_address(reply_token)
        send_identity = (patch.get("send_identity") or "scout").strip().lower()
        if send_identity != "scout":
            raise HTTPException(status_code=400, detail="Only Ready For Robots domain sending is available right now")
        explicit_cc = _email_list(patch.get("cc")) or _email_list(settings.scout_default_cc if settings else None)
        cc = explicit_cc or inferred_cc
        bcc = _email_list(patch.get("bcc")) or _email_list(settings.scout_default_bcc if settings else None)
        approved_style = (patch.get("approved_style") or "").strip()
        if approved_style:
            db.execute(
                text(
                    """
                    INSERT INTO user_settings (user_id, scout_message_style, updated_at)
                    VALUES (:uid, :style, now())
                    ON CONFLICT (user_id) DO UPDATE SET
                        scout_message_style = EXCLUDED.scout_message_style,
                        updated_at = now()
                    """
                ),
                {"uid": str(uid), "style": approved_style},
            )

        _inbound_missing = False
        try:
            send_result = send_email_via_resend(
                to_email=contact_email,
                subject=subject,
                body_text=outreach_draft,
                from_display_name=sender_name.strip() if sender_name else None,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
                idempotency_key=f"scout-outreach/{acct.id}/{contact_email}",
            )
        except ResendEmailError as e:
            # Resend rejects sends when inbound reply routing is not yet configured
            # in the dashboard. Retry without the reply_to so Cal emails still go out.
            err_text = str(e).lower()
            if any(kw in err_text for kw in ("notification service", "notification_service", "notification url", "notification_url", "inbound", "not set", "not configured")):
                _inbound_missing = True
                try:
                    send_result = send_email_via_resend(
                        to_email=contact_email,
                        subject=subject,
                        body_text=outreach_draft,
                        from_display_name=sender_name.strip() if sender_name else None,
                        reply_to=None,
                        cc=cc,
                        bcc=bcc,
                        idempotency_key=f"scout-outreach/{acct.id}/{contact_email}/no-inbound",
                    )
                except ResendEmailError as e2:
                    raise HTTPException(status_code=502, detail=str(e2)) from e2
            else:
                raise HTTPException(status_code=502, detail=str(e)) from e

        now = datetime.now(timezone.utc)
        msg = OutreachMessage(
            team_id=acct.team_id,
            crm_account_id=acct.id,
            company_id=acct.company_id,
            sender_user_id=uid,
            to_email=contact_email,
            from_email=send_result.get("from_email"),
            reply_to=reply_to,
            reply_token=reply_token,
            subject=subject,
            body_text=outreach_draft,
            send_identity="scout",
            resend_id=send_result.get("resend_id"),
            status="sent",
            payload={
                "reply_forwarding_enabled": bool(settings.reply_forwarding_enabled) if settings else True,
                "reply_forward_email": (settings.reply_forward_email if settings else None) or user.get("email"),
                "cc": cc,
                "bcc": bcc,
                "approved_style": approved_style or (settings.scout_message_style if settings else None),
                "style_note": _style_note(settings),
                "preferred_channel": settings.scout_preferred_channel if settings else "email",
                "meeting_preference": settings.scout_meeting_preference if settings else None,
                "persona_traits": settings.scout_persona_traits if settings else None,
                "collateral_policy": settings.scout_collateral_policy if settings else None,
                "collateral_links": settings.scout_collateral_links if settings else None,
                "background_briefing_enabled": bool(settings.scout_background_briefing_enabled) if settings else True,
                "response_suggestions": _response_suggestions(acct, settings),
            },
            sent_at=now,
        )
        db.add(msg)
        acct.contact_email = contact_email
        acct.outreach_draft = outreach_draft
        acct.outreach_sent_at = now
        acct.outreach_stage = "intro_sent"
        sync_account_stage_to_engagement(db, acct)
        from app.services.sequence_runner import enroll_account

        enroll_account(db, team_id=acct.team_id, crm_account_id=acct.id)
        opportunity = ensure_deployment_opportunity(db, account=acct, owner_user_id=uid)
        record_sales_experience(
            db,
            event_type="crm_outreach_sent",
            outcome="sent",
            team_id=acct.team_id,
            user_id=uid,
            crm_account_id=acct.id,
            company_id=acct.company_id,
            channel="email",
            confidence=0.82,
            payload={
                "outreach_message_id": str(msg.id),
                "subject": subject,
                "cc": cc,
                "bcc": bcc,
            },
        )
        current_stage = (opportunity.current_stage or "new").lower()
        if current_stage != "lost" and (
            current_stage == "new"
            or current_stage not in CONVERSION_STAGES
            or CONVERSION_STAGES.index(current_stage) < CONVERSION_STAGES.index("contacted")
        ):
            record_conversion_transition(
                db,
                opportunity=opportunity,
                to_stage="contacted",
                actor="seller",
                occurred_at=now.isoformat(),
                evidence_level="e1_observed",
                contact_result="no_response",
                evidence=[{"type": "outreach_message", "id": str(msg.id)}],
            )
        db.commit()

        effective_reply_to = None if _inbound_missing else reply_to
        result: dict = {
            "sent": True,
            "to": contact_email,
            "sent_at": now.isoformat(),
            "outreach_message_id": str(msg.id),
            "reply_to": effective_reply_to,
            "reply_routing": "Replies return to SIGNAL and notify/forward to the user." if not _inbound_missing else None,
        }
        if _inbound_missing:
            result["warning"] = (
                "Email sent without reply tracking. "
                "To enable reply routing, configure the Resend inbound webhook URL in your Resend dashboard: "
                "Domains → your domain → Inbound → set Notification URL to "
                "https://ready-2-robot.fly.dev/api/webhooks/resend/inbound"
            )
        return result
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)


class SetContactIn(BaseModel):
    contact_email: str = Field(..., max_length=320)
    contact_name: Optional[str] = Field(None, max_length=240)
    contact_title: Optional[str] = Field(None, max_length=240)
    source: Optional[str] = Field("apollo", max_length=32)


class EngagementPatchIn(BaseModel):
    stage: Optional[str] = Field(None, max_length=64)
    status: Optional[str] = Field(None, max_length=32)
    name: Optional[str] = Field(None, max_length=240)
    value_amount: Optional[float] = None


class TaskCreateIn(BaseModel):
    title: str = Field(..., max_length=240)
    body: Optional[str] = None
    priority: Optional[str] = Field("normal", max_length=32)
    due_at: Optional[str] = None
    engagement_id: Optional[str] = None


class TaskPatchIn(BaseModel):
    status: Optional[str] = Field(None, max_length=32)
    title: Optional[str] = Field(None, max_length=240)
    body: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=32)
    due_at: Optional[str] = None


class NoteCreateIn(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)
    engagement_id: Optional[str] = None


class PlanCommitIn(BaseModel):
    commit_tasks: bool = True


@router.post("/accounts/{account_id}/set-contact")
def set_account_contact(
    account_id: str,
    body: SetContactIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        aid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account id") from None
    acct = _crm_account_for_user(db, uid, aid)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found or access denied")
    email = body.contact_email.strip()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid contact email")
    acct.contact_email = email
    if body.contact_name or body.contact_title:
        note_bits = [bit for bit in (body.contact_name, body.contact_title) if bit]
        db.add(
            CrmNote(
                team_id=acct.team_id,
                crm_account_id=acct.id,
                author_user_id=uid,
                body=f"Contact set from {body.source or 'prospect'}: {' — '.join(note_bits)} ({email})",
                source=body.source or "apollo",
            )
        )
    db.commit()
    db.refresh(acct)
    pl = _pipeline_lead_for_account(db, acct)
    return _attach_workflow_intelligence(db, acct, _serialize_account_enriched(acct, pl))


@router.get("/engagements")
def list_engagements(
    team_id: str = Query(...),
    account_id: Optional[str] = Query(None),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        tid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team id") from None
    _require_team_member(db, uid, tid)
    query = db.query(CrmEngagement).filter(CrmEngagement.team_id == tid)
    if account_id:
        try:
            query = query.filter(CrmEngagement.crm_account_id == uuid.UUID(account_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid account id") from None
    rows = query.order_by(CrmEngagement.updated_at.desc()).limit(100).all()
    return [serialize_engagement(row) for row in rows]


@router.patch("/engagements/{engagement_id}")
def patch_engagement(
    engagement_id: str,
    body: EngagementPatchIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        eid = uuid.UUID(engagement_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid engagement id") from None
    row = db.query(CrmEngagement).filter(CrmEngagement.id == eid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Engagement not found")
    _require_team_member(db, uid, row.team_id)
    patch = body.model_dump(exclude_unset=True)
    if "stage" in patch and patch["stage"]:
        row.stage = patch["stage"]
    if "status" in patch and patch["status"]:
        row.status = patch["status"]
    if "name" in patch and patch["name"]:
        row.name = patch["name"]
    if "value_amount" in patch:
        row.value_amount = patch["value_amount"]
    if "stage" in patch and patch["stage"]:
        sync_engagement_stage_to_account(db, row)
    db.commit()
    db.refresh(row)
    return serialize_engagement(row)


@router.get("/tasks")
def list_tasks(
    team_id: str = Query(...),
    account_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        tid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid team id") from None
    _require_team_member(db, uid, tid)
    query = db.query(CrmTask).filter(CrmTask.team_id == tid)
    if account_id:
        try:
            query = query.filter(CrmTask.crm_account_id == uuid.UUID(account_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid account id") from None
    if status:
        query = query.filter(CrmTask.status == status)
    rows = query.order_by(CrmTask.due_at.asc().nullslast(), CrmTask.created_at.desc()).limit(100).all()
    return [
        {
            "id": str(row.id),
            "crm_account_id": str(row.crm_account_id),
            "engagement_id": str(row.engagement_id) if row.engagement_id else None,
            "title": row.title,
            "body": row.body,
            "status": row.status,
            "priority": row.priority,
            "due_at": row.due_at.isoformat() if row.due_at else None,
            "source": row.source,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.post("/accounts/{account_id}/tasks")
def create_task(
    account_id: str,
    body: TaskCreateIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        aid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account id") from None
    acct = _crm_account_for_user(db, uid, aid)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found or access denied")
    due_at = None
    if body.due_at:
        try:
            due_at = datetime.fromisoformat(body.due_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due_at") from None
    engagement_id = None
    if body.engagement_id:
        try:
            engagement_id = uuid.UUID(body.engagement_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid engagement id") from None
    task = CrmTask(
        team_id=acct.team_id,
        crm_account_id=acct.id,
        engagement_id=engagement_id,
        title=body.title.strip(),
        body=body.body,
        status="todo",
        priority=body.priority or "normal",
        due_at=due_at,
        assignee_user_id=uid,
        source="user",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {
        "id": str(task.id),
        "title": task.title,
        "status": task.status,
        "due_at": task.due_at.isoformat() if task.due_at else None,
    }


@router.patch("/tasks/{task_id}")
def patch_task(
    task_id: str,
    body: TaskPatchIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task id") from None
    task = db.query(CrmTask).filter(CrmTask.id == tid).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_team_member(db, uid, task.team_id)
    patch = body.model_dump(exclude_unset=True)
    if "due_at" in patch:
        if patch["due_at"]:
            try:
                task.due_at = datetime.fromisoformat(patch["due_at"].replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_at") from None
        else:
            task.due_at = None
        patch.pop("due_at")
    for key, value in patch.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return {
        "id": str(task.id),
        "title": task.title,
        "status": task.status,
        "due_at": task.due_at.isoformat() if task.due_at else None,
    }


@router.post("/accounts/{account_id}/generate-plan")
def generate_account_plan(
    account_id: str,
    body: PlanCommitIn | None = None,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    try:
        aid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account id") from None
    acct = _crm_account_for_user(db, uid, aid)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found or access denied")
    commit = body.commit_tasks if body else True
    result = generate_sales_plan(db, account=acct, user_id=uid, commit_tasks=commit)
    db.commit()
    return result
