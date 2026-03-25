"""
User API
========
All endpoints require a valid Supabase JWT (Bearer token).
JWT is verified against SUPABASE_JWT_SECRET env var.

  GET    /api/user/me
  PUT    /api/user/me

  GET    /api/user/saved
  POST   /api/user/saved
  DELETE /api/user/saved/{company_id}

  GET    /api/user/lists
  POST   /api/user/lists
  PUT    /api/user/lists/{list_id}
  DELETE /api/user/lists/{list_id}
  POST   /api/user/lists/{list_id}/companies
  DELETE /api/user/lists/{list_id}/companies/{company_id}

  GET    /api/user/reports
  POST   /api/user/reports
  GET    /api/user/reports/{report_id}
  DELETE /api/user/reports/{report_id}
"""

import os
from typing import Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.database import get_db
from app.api.auth_deps import _is_admin, _require_user, _verify_jwt, _extract_email

router = APIRouter()


def _uid(user: dict) -> str:
    return user["uid"]


# ── Helpers: ensure profile exists ────────────────────────────────────────────

def _ensure_profile(db: Session, uid: str, email: str):
    """Upsert the user_profiles row — keep email in sync with JWT (OAuth can update it)."""
    db.execute(
        text("""
            INSERT INTO user_profiles (id, email)
            VALUES (:uid, :email)
            ON CONFLICT (id) DO UPDATE SET email = COALESCE(NULLIF(:email, ''), user_profiles.email)
        """),
        {"uid": uid, "email": email},
    )
    db.commit()


# ── Summary card generator ─────────────────────────────────────────────────────

def _build_summary_card(report_data: dict) -> dict:
    strat   = report_data.get("strategy") or {}
    scores  = report_data.get("scores")   or {}
    company = report_data.get("company")  or {}
    robots  = report_data.get("robot_match") or []
    signals = report_data.get("signals")  or []

    overall = scores.get("overall_score", 0) or 0
    tier = "HOT" if overall >= 75 else "WARM" if overall >= 45 else "COLD"

    top_robot  = robots[0].get("name")  if robots  else None
    top_signal = signals[0].get("text") if signals else None

    return {
        "tier":                tier,
        "score":               round(float(overall), 1),
        "industry":            company.get("industry"),
        "location":            f"{company.get('location_city', '')} {company.get('location_state', '')}".strip(),
        "employee_estimate":   company.get("employee_estimate"),
        "website":             company.get("website"),
        "urgency":             strat.get("urgency"),
        "contact_role":        strat.get("contact_role"),
        "pitch_angle":         strat.get("pitch_angle"),
        "talking_points":      (strat.get("talking_points") or [])[:3],
        "best_channel":        strat.get("best_channel"),
        "timing_note":         strat.get("timing_note"),
        "confidence":          strat.get("confidence"),
        "top_robot":           top_robot,
        "top_signal_text":     (top_signal or "")[:140],
        "signal_count":        report_data.get("signal_count", len(signals)),
        "talking_points_count": len(strat.get("talking_points") or []),
    }


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None

class SaveCompanyIn(BaseModel):
    company_id:   int
    company_name: str
    industry:     Optional[str] = None
    tier:         Optional[str] = None
    score:        Optional[float] = None
    website:      Optional[str] = None
    notes:        Optional[str] = None

class CreateListIn(BaseModel):
    name:        str
    description: Optional[str] = None

class UpdateListIn(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None

class AddToListIn(BaseModel):
    company_id:   int
    company_name: str

class SaveReportIn(BaseModel):
    company_id:   int
    company_name: str
    title:        Optional[str] = None
    report_data:  dict          # full profile payload from /api/agent/profile/{id}


# ── /api/user/me ──────────────────────────────────────────────────────────────

def _handle_db_schema_not_ready(ex: Exception):
    """Raise 503 when user tables are missing (migrations not run yet)."""
    raise HTTPException(
        status_code=503,
        detail="Database initializing. Please retry in a moment.",
    )


@router.get("/me")
def get_me(user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    try:
        _ensure_profile(db, _uid(user), user["email"])
        row = db.execute(
            text("SELECT id, email, display_name, created_at FROM user_profiles WHERE id = :uid"),
            {"uid": _uid(user)},
        ).fetchone()
    except (OperationalError, ProgrammingError) as e:
        _handle_db_schema_not_ready(e)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    # Prefer JWT email for admin check (source of truth at login); fallback to DB
    email_for_admin = (user.get("email") or "").strip() or (row.email or "").strip()
    return {
        "id":           str(row.id),
        "email":        row.email,
        "display_name": row.display_name,
        "created_at":   row.created_at.isoformat() if row.created_at else None,
        "is_admin":     _is_admin(email_for_admin),
    }


@router.get("/auth-debug")
def auth_debug(authorization: Optional[str] = Header(None)):
    """
    Debug endpoint: returns what the server sees for your token.
    Helps troubleshoot admin redirect. Call from browser console when logged in:
      fetch('/api/user/auth-debug', {headers: {Authorization: 'Bearer '+session.access_token}}).then(r=>r.json()).then(console.log)
    """
    if not authorization or not authorization.startswith("Bearer "):
        return {"ok": False, "error": "No Authorization header or missing Bearer prefix"}
    token = authorization.split(" ", 1)[1]
    try:
        payload = _verify_jwt(token)
        email = _extract_email(payload) or ""
        return {
            "ok": True,
            "email": email,
            "email_preview": f"{email[:3]}***{email[email.find('@'):]}" if email and "@" in email else "(empty)",
            "is_admin": _is_admin(email),
            "uid": payload.get("sub", "")[:8] + "...",
        }
    except HTTPException as e:
        return {"ok": False, "error": e.detail, "status": e.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.put("/me")
def update_me(
    body: ProfileUpdate,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    _ensure_profile(db, _uid(user), user["email"])
    db.execute(
        text("""
            UPDATE user_profiles
            SET display_name = COALESCE(:dn, display_name),
                updated_at   = now()
            WHERE id = :uid
        """),
        {"dn": body.display_name, "uid": _uid(user)},
    )
    db.commit()
    return {"ok": True}


# ── /api/user/saved ───────────────────────────────────────────────────────────

@router.get("/saved")
def list_saved(user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    try:
        _ensure_profile(db, _uid(user), user["email"])
        rows = db.execute(
        text("""
            SELECT id, company_id, company_name, industry, tier, score,
                   website, notes, saved_at
            FROM user_saved_companies
            WHERE user_id = :uid
            ORDER BY saved_at DESC
        """),
        {"uid": _uid(user)},
    ).fetchall()
    except (OperationalError, ProgrammingError):
        _handle_db_schema_not_ready(None)
    return [
        {
            "id":           r.id,
            "company_id":   r.company_id,
            "company_name": r.company_name,
            "industry":     r.industry,
            "tier":         r.tier,
            "score":        float(r.score) if r.score is not None else None,
            "website":      r.website,
            "notes":        r.notes,
            "saved_at":     r.saved_at.isoformat() if r.saved_at else None,
        }
        for r in rows
    ]


@router.post("/saved", status_code=201)
def save_company(
    body: SaveCompanyIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    _ensure_profile(db, _uid(user), user["email"])
    db.execute(
        text("""
            INSERT INTO user_saved_companies
                (user_id, company_id, company_name, industry, tier, score, website, notes)
            VALUES (:uid, :cid, :cname, :ind, :tier, :score, :web, :notes)
            ON CONFLICT (user_id, company_id) DO UPDATE SET
                company_name = EXCLUDED.company_name,
                industry     = EXCLUDED.industry,
                tier         = EXCLUDED.tier,
                score        = EXCLUDED.score,
                website      = EXCLUDED.website,
                notes        = COALESCE(EXCLUDED.notes, user_saved_companies.notes),
                saved_at     = now()
        """),
        {
            "uid":   _uid(user),
            "cid":   body.company_id,
            "cname": body.company_name,
            "ind":   body.industry,
            "tier":  body.tier,
            "score": body.score,
            "web":   body.website,
            "notes": body.notes,
        },
    )
    db.commit()
    return {"ok": True}


@router.delete("/saved/{company_id}")
def unsave_company(
    company_id: int,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    db.execute(
        text("DELETE FROM user_saved_companies WHERE user_id = :uid AND company_id = :cid"),
        {"uid": _uid(user), "cid": company_id},
    )
    db.commit()
    return {"ok": True}


# ── /api/user/lists ───────────────────────────────────────────────────────────

@router.get("/lists")
def get_lists(user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    try:
        _ensure_profile(db, _uid(user), user["email"])
        rows = db.execute(
        text("""
            SELECT l.id, l.name, l.description, l.created_at,
                   count(lc.company_id) as company_count
            FROM user_lists l
            LEFT JOIN user_list_companies lc ON lc.list_id = l.id
            WHERE l.user_id = :uid
            GROUP BY l.id
            ORDER BY l.created_at DESC
        """),
        {"uid": _uid(user)},
    ).fetchall()
    except (OperationalError, ProgrammingError):
        _handle_db_schema_not_ready(None)

    result = []
    for r in rows:
        # fetch companies for each list
        companies = db.execute(
            text("""
                SELECT company_id, company_name, added_at
                FROM user_list_companies
                WHERE list_id = :lid
                ORDER BY added_at
            """),
            {"lid": str(r.id)},
        ).fetchall()
        result.append({
            "id":            str(r.id),
            "name":          r.name,
            "description":   r.description,
            "created_at":    r.created_at.isoformat() if r.created_at else None,
            "company_count": int(r.company_count),
            "companies": [
                {
                    "company_id":   c.company_id,
                    "company_name": c.company_name,
                    "added_at":     c.added_at.isoformat() if c.added_at else None,
                }
                for c in companies
            ],
        })
    return result


@router.post("/lists", status_code=201)
def create_list(
    body: CreateListIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    _ensure_profile(db, _uid(user), user["email"])
    row = db.execute(
        text("""
            INSERT INTO user_lists (user_id, name, description)
            VALUES (:uid, :name, :desc)
            RETURNING id, name, description, created_at
        """),
        {"uid": _uid(user), "name": body.name.strip(), "desc": body.description},
    ).fetchone()
    db.commit()
    return {
        "id":          str(row.id),
        "name":        row.name,
        "description": row.description,
        "created_at":  row.created_at.isoformat() if row.created_at else None,
        "companies":   [],
    }


@router.put("/lists/{list_id}")
def update_list(
    list_id: str,
    body: UpdateListIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    result = db.execute(
        text("""
            UPDATE user_lists
            SET name        = COALESCE(:name, name),
                description = COALESCE(:desc, description),
                updated_at  = now()
            WHERE id = :lid AND user_id = :uid
        """),
        {"name": body.name, "desc": body.description, "lid": list_id, "uid": _uid(user)},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="List not found")
    return {"ok": True}


@router.delete("/lists/{list_id}")
def delete_list(
    list_id: str,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    db.execute(
        text("DELETE FROM user_lists WHERE id = :lid AND user_id = :uid"),
        {"lid": list_id, "uid": _uid(user)},
    )
    db.commit()
    return {"ok": True}


@router.post("/lists/{list_id}/companies", status_code=201)
def add_to_list(
    list_id: str,
    body: AddToListIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    # verify list ownership
    row = db.execute(
        text("SELECT id FROM user_lists WHERE id = :lid AND user_id = :uid"),
        {"lid": list_id, "uid": _uid(user)},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="List not found")
    db.execute(
        text("""
            INSERT INTO user_list_companies (list_id, company_id, company_name)
            VALUES (:lid, :cid, :cname)
            ON CONFLICT (list_id, company_id) DO NOTHING
        """),
        {"lid": list_id, "cid": body.company_id, "cname": body.company_name},
    )
    db.commit()
    return {"ok": True}


@router.delete("/lists/{list_id}/companies/{company_id}")
def remove_from_list(
    list_id: str,
    company_id: int,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    db.execute(
        text("""
            DELETE FROM user_list_companies
            WHERE list_id = :lid AND company_id = :cid
              AND EXISTS (
                SELECT 1 FROM user_lists WHERE id = :lid AND user_id = :uid
              )
        """),
        {"lid": list_id, "cid": company_id, "uid": _uid(user)},
    )
    db.commit()
    return {"ok": True}


# ── /api/user/reports ─────────────────────────────────────────────────────────

@router.get("/reports")
def list_reports(user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    try:
        _ensure_profile(db, _uid(user), user["email"])
        rows = db.execute(
        text("""
            SELECT id, company_id, company_name, title, summary_card, created_at, updated_at
            FROM ai_reports
            WHERE user_id = :uid
            ORDER BY created_at DESC
        """),
        {"uid": _uid(user)},
    ).fetchall()
    except (OperationalError, ProgrammingError):
        _handle_db_schema_not_ready(None)
    return [
        {
            "id":           str(r.id),
            "company_id":   r.company_id,
            "company_name": r.company_name,
            "title":        r.title,
            "summary_card": r.summary_card,
            "created_at":   r.created_at.isoformat() if r.created_at else None,
            "updated_at":   r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]


@router.post("/reports", status_code=201)
def save_report(
    body: SaveReportIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    _ensure_profile(db, _uid(user), user["email"])

    # Enrich report_data with save timestamp
    enriched = {**body.report_data, "saved_at": datetime.utcnow().isoformat()}
    summary  = _build_summary_card(body.report_data)

    import json
    row = db.execute(
        text("""
            INSERT INTO ai_reports (user_id, company_id, company_name, title, report_data, summary_card)
            VALUES (:uid, :cid, :cname, :title, :rdata::jsonb, :scard::jsonb)
            RETURNING id, created_at
        """),
        {
            "uid":   _uid(user),
            "cid":   body.company_id,
            "cname": body.company_name,
            "title": body.title or f"{body.company_name} — AI Analysis",
            "rdata": json.dumps(enriched),
            "scard": json.dumps(summary),
        },
    ).fetchone()
    db.commit()
    return {"id": str(row.id), "created_at": row.created_at.isoformat()}


@router.get("/reports/{report_id}")
def get_report(
    report_id: str,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("""
            SELECT id, company_id, company_name, title, report_data, summary_card,
                   created_at, updated_at
            FROM ai_reports
            WHERE id = :rid AND user_id = :uid
        """),
        {"rid": report_id, "uid": _uid(user)},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id":           str(row.id),
        "company_id":   row.company_id,
        "company_name": row.company_name,
        "title":        row.title,
        "report_data":  row.report_data,
        "summary_card": row.summary_card,
        "created_at":   row.created_at.isoformat() if row.created_at else None,
        "updated_at":   row.updated_at.isoformat() if row.updated_at else None,
    }


@router.delete("/reports/{report_id}")
def delete_report(
    report_id: str,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    db.execute(
        text("DELETE FROM ai_reports WHERE id = :rid AND user_id = :uid"),
        {"rid": report_id, "uid": _uid(user)},
    )
    db.commit()
    return {"ok": True}
