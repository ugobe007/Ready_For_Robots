"""
CRM API — teams + accounts (Bearer JWT). Prefix: /api/crm

  GET    /api/crm/teams              — list teams for user (auto-creates default workspace if none)
  POST   /api/crm/teams              — create a team; caller becomes owner
  GET    /api/crm/accounts           — list CRM accounts for a team
  POST   /api/crm/accounts           — create account (optional company_id pre-fills from companies)
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
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


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/teams", response_model=list[TeamOut])
def list_teams(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    _ensure_default_team(db, uid, user.get("email") or "")
    rows = _team_rows_for_user(db, uid)
    return [_serialize_team_row(t, role) for t, role in rows]


@router.post("/teams", response_model=TeamOut)
def create_team(
    body: CreateTeamIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    _ensure_profile(db, str(uid), user.get("email") or "")
    team = Team(name=body.name.strip(), slug=body.slug.strip() if body.slug else None)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=uid, role="owner"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slug already in use or conflict")
    db.refresh(team)
    return _serialize_team_row(team, "owner")


@router.get("/accounts", response_model=list[CrmAccountOut])
def list_accounts(
    team_id: Optional[uuid.UUID] = Query(None, description="Defaults to your first team"),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = _uid_uuid(user)
    default = _ensure_default_team(db, uid, user.get("email") or "")
    tid = team_id or default.id
    _require_team_member(db, uid, tid)
    accounts = db.query(CrmAccount).filter(CrmAccount.team_id == tid).order_by(CrmAccount.created_at.desc()).all()
    return [_serialize_account(a) for a in accounts]


@router.post("/accounts", response_model=CrmAccountOut)
def create_account(
    body: CreateAccountIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account for this company already exists in this team",
        )
    db.refresh(row)
    return _serialize_account(row)
