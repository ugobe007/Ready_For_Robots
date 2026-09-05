"""DB helpers for SCOUT marketing chat (see rfr_cursor_package/server/scoutDb.ts)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.scout_chat import ScoutMessage, ScoutProfile, ScoutSession


def upsert_session(db: Session, fingerprint: str) -> Tuple[ScoutSession, bool]:
    fp = (fingerprint or "").strip()[:80]
    if not fp:
        raise ValueError("fingerprint required")

    row = db.query(ScoutSession).filter(ScoutSession.fingerprint == fp).first()
    if row:
        row.last_seen_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return row, False

    row = ScoutSession(fingerprint=fp, conversation_count=0)
    db.add(row)
    db.commit()
    db.refresh(row)
    prof = ScoutProfile(session_id=row.id)
    db.add(prof)
    db.commit()
    return row, True


def update_session_context(
    db: Session,
    session_id: int,
    *,
    robot_category: Optional[str] = None,
    vertical: Optional[str] = None,
    territory: Optional[str] = None,
    company_name: Optional[str] = None,
    company_url: Optional[str] = None,
) -> None:
    row = db.query(ScoutSession).filter(ScoutSession.id == session_id).first()
    if not row:
        return
    if robot_category is not None:
        row.robot_category = robot_category[:32] if robot_category else None
    if vertical is not None:
        row.vertical = vertical
    if territory is not None:
        row.territory = territory[:128] if territory else None
    if company_name is not None:
        row.company_name = company_name[:256] if company_name else None
    if company_url is not None:
        row.company_url = company_url[:512] if company_url else None
    db.commit()


def append_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    skill_invoked: Optional[str] = None,
    skill_data: Optional[Dict[str, Any]] = None,
) -> None:
    r = "scout" if role == "scout" else "user"
    m = ScoutMessage(
        session_id=session_id,
        role=r,
        content=content,
        skill_invoked=skill_invoked[:64] if skill_invoked else None,
        skill_data=skill_data,
    )
    db.add(m)
    sess = db.query(ScoutSession).filter(ScoutSession.id == session_id).first()
    if sess:
        sess.conversation_count = int(sess.conversation_count or 0) + 1
    db.commit()


def get_history(db: Session, session_id: int, limit: int = 40) -> List[ScoutMessage]:
    rows = (
        db.query(ScoutMessage)
        .filter(ScoutMessage.session_id == session_id)
        .order_by(desc(ScoutMessage.created_at))
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def get_profile_row(db: Session, session_id: int) -> Optional[ScoutProfile]:
    return db.query(ScoutProfile).filter(ScoutProfile.session_id == session_id).first()


def update_inferred_needs(db: Session, session_id: int, summary: str) -> None:
    prof = get_profile_row(db, session_id)
    if not prof:
        return
    prof.inferred_needs = summary[:4000]
    db.commit()
