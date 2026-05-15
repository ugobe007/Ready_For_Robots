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
from app.models.crm import Team, TeamMember, CrmAccount
from app.models.outreach import OutreachMessage
from app.services.agent_messaging import BUYER_SIGNAL_EXPLANATION, CAL_INTRO, cal_signature
from app.services.apollo_client import recommended_prospect_titles
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.sales_learning_agent import crm_workflow_intelligence, record_sales_experience

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
        orig = str(getattr(exc, "orig", None) or exc).lower()
        if "does not exist" in orig or "no such table" in orig:
            raise HTTPException(status_code=503, detail=CRM_MIGRATION_HINT) from exc
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


def _draft_subject(acct: CrmAccount) -> str:
    industry = (acct.industry or "operations").strip()
    return f"Robot automation ideas for {acct.name}'s {industry} team"


def _draft_body(acct: CrmAccount, settings: Any, traits: list[str], style_instruction: str, collateral_policy: str, collateral_links: str | None) -> str:
    industry = (acct.industry or "your operation").strip()
    selected_traits = set(traits)
    lines: list[str] = [
        "Hello,",
        "",
        CAL_INTRO,
        "",
        BUYER_SIGNAL_EXPLANATION,
        "",
        f"{acct.name} stood out because there may be an automation angle in {industry}.",
    ]
    if "insightful" in selected_traits:
        lines.append("I am not assuming there is a project already in motion. The useful question is whether repetitive work, staffing pressure, or service expectations are creating a real business case.")
    if "industry_refs" in selected_traits:
        lines.append(f"In {industry}, teams are increasingly looking at automation where it can reduce walking time, stabilize throughput, or protect service levels without adding headcount.")
    if "robot_examples" in selected_traits:
        lines.append(f"Relevant examples include cleaning robots, AMRs, delivery robots, inspection systems, and task-specific automation depending on the workflow.")
    if "humor" in selected_traits:
        lines.append("No one needs a robot science project wandering around the building; the goal is boringly useful automation that pays for itself.")
    if "inquisitive" in selected_traits:
        lines.append("I’m curious where your team is seeing the most pressure right now: labor coverage, turnaround time, consistency, safety, or something else?")
    if "whitepapers" in selected_traits:
        lines.append("If helpful, I can share third-party research or case studies that map the business case before any vendor conversation.")

    channel = getattr(settings, "scout_preferred_channel", "email") if settings else "email"
    meeting = getattr(settings, "scout_meeting_preference", None) if settings else None
    if channel in ("phone", "meeting"):
        lines.append(meeting or "Open to a quick 15-minute call next week?")
    else:
        lines.append("Worth a quick exchange to see whether there is a useful automation angle here?")
    # Style instructions guide generation; they should not be exposed to buyers.
    collateral = _collateral_note(collateral_policy, collateral_links)
    if collateral:
        lines.append(collateral)
    lines.extend(["", cal_signature()])
    return "\n".join(lines)


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
                "trigger": "Background SCOUT brief",
                "action": "Monitor replies, no-response timing, research updates, and tone; surface next-best-action ideas to the user.",
            "why": "SCOUT monitors the workflow while Cal handles communication.",
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
            db.commit()
            db.refresh(existing)
            row = existing
        else:
            row = CrmAccount(
            team_id=tid,
            company_id=body.company_id,
            name=name,
            website=website,
            industry=industry,
            owner_user_id=uid,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
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

        subject = _draft_subject(acct)
        draft = _draft_body(acct, settings, traits, style_instruction, collateral_policy, collateral_links)
        acct.contact_email = patch.get("contact_email") or acct.contact_email
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
        return {
            "subject": subject,
            "outreach_draft": draft,
            "outreach_stage": "draft_ready",
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
        contact_email = (patch.get("contact_email") or acct.contact_email or "").strip()
        outreach_draft = (patch.get("outreach_draft") or acct.outreach_draft or "").strip()

        if not contact_email or "@" not in contact_email:
            raise HTTPException(status_code=400, detail="No contact email on file for this account")
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
        cc = _email_list(patch.get("cc")) or _email_list(settings.scout_default_cc if settings else None)
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
        db.commit()

        return {
            "sent": True,
            "to": contact_email,
            "sent_at": now.isoformat(),
            "outreach_message_id": str(msg.id),
            "reply_to": reply_to,
            "reply_routing": "Replies return to SCOUT and notify/forward to the user.",
        }
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
        _raise_crm_db_error(e)
