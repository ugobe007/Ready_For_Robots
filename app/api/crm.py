"""
CRM API — teams + accounts (Bearer JWT). Prefix: /api/crm

  GET    /api/crm/teams              — list teams for user (auto-creates default workspace if none)
  POST   /api/crm/teams              — create a team; caller becomes owner
  GET    /api/crm/accounts           — list CRM accounts for a team
  POST   /api/crm/accounts           — create account (optional company_id pre-fills from companies)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

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
    # Enriched when company_id links to pipeline companies
    signal_score: Optional[float] = None
    overall_intent_score: Optional[float] = None
    lead_value_score: Optional[float] = None
    pipeline_priority_tier: Optional[str] = None


class CreateAccountIn(BaseModel):
    team_id: Optional[uuid.UUID] = None
    company_id: Optional[int] = None
    name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None


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
    }


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
    return base


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
            out.append(_serialize_account_enriched(a, pl))
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
        return _serialize_account_enriched(row, pl)
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
