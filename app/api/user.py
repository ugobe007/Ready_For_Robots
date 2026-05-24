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

  GET    /api/user/settings
  PUT    /api/user/settings
"""

import os
import uuid
from typing import Optional, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.database import get_db
from app.api.auth_deps import _is_admin, _require_user, _verify_jwt, _extract_email
from app.models.lead_research import UserNotification

router = APIRouter()


def _uid(user: dict) -> str:
    return user["uid"]


def _uid_uuid(user: dict):
    try:
        return uuid.UUID(str(_uid(user)))
    except (TypeError, ValueError):
        return _uid(user)


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


class UserSettingsOut(BaseModel):
    sender_name: Optional[str] = None
    sender_title: Optional[str] = None
    sender_company: Optional[str] = None
    sender_email: Optional[str] = None
    scout_automation_level: str = "assisted"
    reply_forwarding_enabled: bool = True
    reply_forward_email: Optional[str] = None
    scout_message_style: Optional[str] = None
    scout_preferred_channel: str = "email"
    scout_meeting_preference: Optional[str] = None
    scout_default_cc: Optional[str] = None
    scout_default_bcc: Optional[str] = None
    scout_persona_traits: Optional[str] = None
    scout_collateral_policy: str = "selective"
    scout_collateral_links: Optional[str] = None
    scout_background_briefing_enabled: bool = True


class UserSettingsUpdate(BaseModel):
    sender_name: Optional[str] = None
    sender_title: Optional[str] = None
    sender_company: Optional[str] = None
    sender_email: Optional[str] = None
    scout_automation_level: Optional[str] = None
    reply_forwarding_enabled: Optional[bool] = None
    reply_forward_email: Optional[str] = None
    scout_message_style: Optional[str] = None
    scout_preferred_channel: Optional[str] = None
    scout_meeting_preference: Optional[str] = None
    scout_default_cc: Optional[str] = None
    scout_default_bcc: Optional[str] = None
    scout_persona_traits: Optional[str] = None
    scout_collateral_policy: Optional[str] = None
    scout_collateral_links: Optional[str] = None
    scout_background_briefing_enabled: Optional[bool] = None


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


# ── /api/user/settings (proposal PDF / email footer) ─────────────────────────

@router.get("/settings", response_model=UserSettingsOut)
def get_user_settings(user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text("""
                SELECT sender_name, sender_title, sender_company, sender_email,
                       scout_automation_level, reply_forwarding_enabled, reply_forward_email,
                       scout_message_style, scout_preferred_channel, scout_meeting_preference,
                       scout_default_cc, scout_default_bcc, scout_persona_traits,
                       scout_collateral_policy, scout_collateral_links, scout_background_briefing_enabled
                FROM user_settings
                WHERE user_id = :uid
            """),
            {"uid": _uid(user)},
        ).fetchone()
    except (OperationalError, ProgrammingError) as e:
        _handle_db_schema_not_ready(e)
    if not row:
        return UserSettingsOut()
    return UserSettingsOut(
        sender_name=row.sender_name,
        sender_title=row.sender_title,
        sender_company=row.sender_company,
        sender_email=row.sender_email,
        scout_automation_level=row.scout_automation_level or "assisted",
        reply_forwarding_enabled=bool(row.reply_forwarding_enabled),
        reply_forward_email=row.reply_forward_email,
        scout_message_style=row.scout_message_style,
        scout_preferred_channel=row.scout_preferred_channel or "email",
        scout_meeting_preference=row.scout_meeting_preference,
        scout_default_cc=row.scout_default_cc,
        scout_default_bcc=row.scout_default_bcc,
        scout_persona_traits=row.scout_persona_traits,
        scout_collateral_policy=row.scout_collateral_policy or "selective",
        scout_collateral_links=row.scout_collateral_links,
        scout_background_briefing_enabled=bool(row.scout_background_briefing_enabled),
    )


@router.put("/settings", response_model=UserSettingsOut)
def put_user_settings(
    body: UserSettingsUpdate,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    _ensure_profile(db, _uid(user), user["email"])
    uid = _uid(user)
    try:
        row = db.execute(
            text("""
                SELECT sender_name, sender_title, sender_company, sender_email,
                       scout_automation_level, reply_forwarding_enabled, reply_forward_email,
                       scout_message_style, scout_preferred_channel, scout_meeting_preference,
                       scout_default_cc, scout_default_bcc, scout_persona_traits,
                       scout_collateral_policy, scout_collateral_links, scout_background_briefing_enabled
                FROM user_settings
                WHERE user_id = :uid
            """),
            {"uid": uid},
        ).fetchone()
    except (OperationalError, ProgrammingError) as e:
        _handle_db_schema_not_ready(e)

    cur: dict[str, Optional[str]] = {
        "sender_name": None,
        "sender_title": None,
        "sender_company": None,
        "sender_email": None,
        "scout_automation_level": "assisted",
        "reply_forwarding_enabled": True,
        "reply_forward_email": None,
        "scout_message_style": None,
        "scout_preferred_channel": "email",
        "scout_meeting_preference": None,
        "scout_default_cc": None,
        "scout_default_bcc": None,
        "scout_persona_traits": None,
        "scout_collateral_policy": "selective",
        "scout_collateral_links": None,
        "scout_background_briefing_enabled": True,
    }
    if row:
        cur.update(
            {
                "sender_name": row.sender_name,
                "sender_title": row.sender_title,
                "sender_company": row.sender_company,
                "sender_email": row.sender_email,
                "scout_automation_level": row.scout_automation_level or "assisted",
                "reply_forwarding_enabled": bool(row.reply_forwarding_enabled),
                "reply_forward_email": row.reply_forward_email,
                "scout_message_style": row.scout_message_style,
                "scout_preferred_channel": row.scout_preferred_channel or "email",
                "scout_meeting_preference": row.scout_meeting_preference,
                "scout_default_cc": row.scout_default_cc,
                "scout_default_bcc": row.scout_default_bcc,
                "scout_persona_traits": row.scout_persona_traits,
                "scout_collateral_policy": row.scout_collateral_policy or "selective",
                "scout_collateral_links": row.scout_collateral_links,
                "scout_background_briefing_enabled": bool(row.scout_background_briefing_enabled),
            }
        )
    patch = body.model_dump(exclude_unset=True)
    if "scout_automation_level" in patch and patch["scout_automation_level"] not in ("manual", "assisted", "auto"):
        raise HTTPException(status_code=400, detail="scout_automation_level must be manual, assisted, or auto")
    if "scout_preferred_channel" in patch and patch["scout_preferred_channel"] not in ("email", "phone", "meeting"):
        raise HTTPException(status_code=400, detail="scout_preferred_channel must be email, phone, or meeting")
    if "scout_collateral_policy" in patch and patch["scout_collateral_policy"] not in ("none", "selective", "all"):
        raise HTTPException(status_code=400, detail="scout_collateral_policy must be none, selective, or all")
    cur.update(patch)

    try:
        db.execute(
            text("""
                INSERT INTO user_settings
                    (user_id, sender_name, sender_title, sender_company, sender_email,
                     scout_automation_level, reply_forwarding_enabled, reply_forward_email,
                     scout_message_style, scout_preferred_channel, scout_meeting_preference,
                     scout_default_cc, scout_default_bcc, scout_persona_traits,
                     scout_collateral_policy, scout_collateral_links, scout_background_briefing_enabled, updated_at)
                VALUES
                    (:uid, :sn, :st, :sc, :se, :sal, :rfe, :rfe_email,
                     :sms, :spc, :smp, :scc, :sbcc, :spt, :scp, :scl, :sbbe, now())
                ON CONFLICT (user_id) DO UPDATE SET
                    sender_name    = EXCLUDED.sender_name,
                    sender_title   = EXCLUDED.sender_title,
                    sender_company = EXCLUDED.sender_company,
                    sender_email   = EXCLUDED.sender_email,
                    scout_automation_level = EXCLUDED.scout_automation_level,
                    reply_forwarding_enabled = EXCLUDED.reply_forwarding_enabled,
                    reply_forward_email = EXCLUDED.reply_forward_email,
                    scout_message_style = EXCLUDED.scout_message_style,
                    scout_preferred_channel = EXCLUDED.scout_preferred_channel,
                    scout_meeting_preference = EXCLUDED.scout_meeting_preference,
                    scout_default_cc = EXCLUDED.scout_default_cc,
                    scout_default_bcc = EXCLUDED.scout_default_bcc,
                    scout_persona_traits = EXCLUDED.scout_persona_traits,
                    scout_collateral_policy = EXCLUDED.scout_collateral_policy,
                    scout_collateral_links = EXCLUDED.scout_collateral_links,
                    scout_background_briefing_enabled = EXCLUDED.scout_background_briefing_enabled,
                    updated_at     = now()
            """),
            {
                "uid": uid,
                "sn": cur["sender_name"],
                "st": cur["sender_title"],
                "sc": cur["sender_company"],
                "se": cur["sender_email"],
                "sal": cur["scout_automation_level"],
                "rfe": cur["reply_forwarding_enabled"],
                "rfe_email": cur["reply_forward_email"],
                "sms": cur["scout_message_style"],
                "spc": cur["scout_preferred_channel"],
                "smp": cur["scout_meeting_preference"],
                "scc": cur["scout_default_cc"],
                "sbcc": cur["scout_default_bcc"],
                "spt": cur["scout_persona_traits"],
                "scp": cur["scout_collateral_policy"],
                "scl": cur["scout_collateral_links"],
                "sbbe": cur["scout_background_briefing_enabled"],
            },
        )
        db.commit()
        row = db.execute(
            text("""
                SELECT sender_name, sender_title, sender_company, sender_email,
                       scout_automation_level, reply_forwarding_enabled, reply_forward_email,
                       scout_message_style, scout_preferred_channel, scout_meeting_preference,
                       scout_default_cc, scout_default_bcc, scout_persona_traits,
                       scout_collateral_policy, scout_collateral_links, scout_background_briefing_enabled
                FROM user_settings
                WHERE user_id = :uid
            """),
            {"uid": uid},
        ).fetchone()
    except (OperationalError, ProgrammingError) as e:
        _handle_db_schema_not_ready(e)
    if not row:
        return UserSettingsOut()
    return UserSettingsOut(
        sender_name=row.sender_name,
        sender_title=row.sender_title,
        sender_company=row.sender_company,
        sender_email=row.sender_email,
        scout_automation_level=row.scout_automation_level or "assisted",
        reply_forwarding_enabled=bool(row.reply_forwarding_enabled),
        reply_forward_email=row.reply_forward_email,
        scout_message_style=row.scout_message_style,
        scout_preferred_channel=row.scout_preferred_channel or "email",
        scout_meeting_preference=row.scout_meeting_preference,
        scout_default_cc=row.scout_default_cc,
        scout_default_bcc=row.scout_default_bcc,
        scout_persona_traits=row.scout_persona_traits,
        scout_collateral_policy=row.scout_collateral_policy or "selective",
        scout_collateral_links=row.scout_collateral_links,
        scout_background_briefing_enabled=bool(row.scout_background_briefing_enabled),
    )


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


# ── /api/user/notifications ──────────────────────────────────────────────────

def _notification_payload(row: UserNotification) -> dict:
    return {
        "id": row.id,
        "company_id": row.company_id,
        "research_update_id": row.research_update_id,
        "notification_type": row.notification_type,
        "title": row.title,
        "body": row.body,
        "delivery_state": row.delivery_state,
        "payload": row.payload or {},
        "read_at": row.read_at.isoformat() if row.read_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/notifications")
def list_notifications(
    unread_only: bool = False,
    limit: int = 30,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    _ensure_profile(db, _uid(user), user["email"])
    query = db.query(UserNotification).filter(UserNotification.user_id == _uid_uuid(user))
    if unread_only:
        query = query.filter(UserNotification.read_at.is_(None))
    rows = query.order_by(UserNotification.created_at.desc()).limit(max(1, min(limit, 100))).all()
    unread_count = (
        db.query(UserNotification.id)
        .filter(UserNotification.user_id == _uid_uuid(user), UserNotification.read_at.is_(None))
        .count()
    )
    return {
        "notifications": [_notification_payload(row) for row in rows],
        "unread_count": unread_count,
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(UserNotification)
        .filter(UserNotification.id == notification_id, UserNotification.user_id == _uid_uuid(user))
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.read_at = datetime.now(timezone.utc)
    db.add(row)
    db.commit()
    return {"ok": True}


@router.post("/notifications/read-all")
def mark_all_notifications_read(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    db.query(UserNotification).filter(
        UserNotification.user_id == _uid_uuid(user),
        UserNotification.read_at.is_(None),
    ).update({"read_at": datetime.now(timezone.utc)}, synchronize_session=False)
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
            VALUES (:uid, :cid, :cname, :title, CAST(:rdata AS jsonb), CAST(:scard AS jsonb))
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
