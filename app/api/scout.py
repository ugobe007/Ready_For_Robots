"""
Public SCOUT marketing chat API (anonymous fingerprint sessions).

Parity target: rfr_cursor_package `scout.getSession`, `scout.updateSession`,
`scout.saveMessage`, `scout.chat` — v1 implements session + chat + history.
Skill endpoints (scanCompany, …) can follow.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.company import Company
from app.models.scout_chat import ScoutSession
from app.models.signal import Signal
from app.services import scout_chat_service as scsvc
from app.services.company_domain import normalize_website_domain
from app.services.scout_llm import scout_chat_completion
from app.services.scout_scoring import normalize_domain, serialize_company_result

router = APIRouter()


class SessionInitBody(BaseModel):
    fingerprint: str = Field(..., min_length=8, max_length=80)


class SessionContextBody(BaseModel):
    fingerprint: str = Field(..., min_length=8, max_length=80)
    robot_category: Optional[str] = None
    vertical: Optional[str] = None
    territory: Optional[str] = None
    company_name: Optional[str] = None
    company_url: Optional[str] = None
    # Aliases for prototype / TS camelCase
    robotCategory: Optional[str] = None
    companyName: Optional[str] = None
    companyUrl: Optional[str] = None

    def normalized_updates(self) -> Dict[str, Optional[str]]:
        return {
            "robot_category": self.robot_category or self.robotCategory,
            "vertical": self.vertical,
            "territory": self.territory,
            "company_name": self.company_name or self.companyName,
            "company_url": self.company_url or self.companyUrl,
        }


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=12000)


class ChatBody(BaseModel):
    fingerprint: str = Field(..., min_length=8, max_length=80)
    messages: List[ChatTurn] = Field(..., min_length=1, max_length=50)
    session_context: Optional[Dict[str, Any]] = None
    sessionContext: Optional[Dict[str, Any]] = None  # camelCase alias (ScoutChat prototype)


class ScanForResultsBody(BaseModel):
    url: Optional[str] = None
    company_url: Optional[str] = None
    companyUrl: Optional[str] = None

    def primary_url(self) -> str:
        return (self.url or self.company_url or self.companyUrl or "").strip()


def _serialize_message(m: Any) -> Dict[str, Any]:
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "skillInvoked": m.skill_invoked,
        "skillData": m.skill_data,
        "createdAt": m.created_at.isoformat() if m.created_at else None,
    }


@router.post("/session")
def scout_init_session(body: SessionInitBody, db: Session = Depends(get_db)):
    sess, is_new = scsvc.upsert_session(db, body.fingerprint)
    prof = scsvc.get_profile_row(db, sess.id)
    history = [] if is_new else [_serialize_message(m) for m in scsvc.get_history(db, sess.id, limit=30)]
    return {
        "session": {"id": sess.id, "fingerprint": sess.fingerprint},
        "isNew": is_new,
        "history": history,
        "profile": {
            "inferredNeeds": prof.inferred_needs if prof else None,
            "companiesViewed": (prof.companies_viewed or []) if prof else [],
        },
    }


@router.patch("/session/context")
def scout_session_context(body: SessionContextBody, db: Session = Depends(get_db)):
    sess, _ = scsvc.upsert_session(db, body.fingerprint)
    u = body.normalized_updates()
    scsvc.update_session_context(
        db,
        sess.id,
        robot_category=u["robot_category"],
        vertical=u["vertical"],
        territory=u["territory"],
        company_name=u["company_name"],
        company_url=u["company_url"],
    )
    return {"success": True}


@router.get("/session/{fingerprint}/history")
def scout_history(fingerprint: str, db: Session = Depends(get_db), limit: int = 40):
    fp = (fingerprint or "").strip()[:80]
    row = db.query(ScoutSession).filter(ScoutSession.fingerprint == fp).first()
    if not row:
        return {"messages": []}
    msgs = scsvc.get_history(db, row.id, limit=min(limit, 80))
    return {"messages": [_serialize_message(m) for m in msgs]}


@router.post("/chat")
def scout_chat(body: ChatBody, db: Session = Depends(get_db)):
    sess, _ = scsvc.upsert_session(db, body.fingerprint)
    merged_ctx = {
        "robot_category": sess.robot_category,
        "vertical": sess.vertical,
        "territory": sess.territory,
        "company_name": sess.company_name,
    }
    raw_ctx = body.session_context or body.sessionContext or {}
    if raw_ctx:
        alias = {
            "robot_category": raw_ctx.get("robot_category") or raw_ctx.get("robotCategory"),
            "vertical": raw_ctx.get("vertical"),
            "territory": raw_ctx.get("territory"),
            "company_name": raw_ctx.get("company_name") or raw_ctx.get("companyName"),
        }
        for key, v in alias.items():
            if v is not None and str(v).strip() != "":
                merged_ctx[key] = v
    ctx_for_llm = {k: v for k, v in merged_ctx.items() if v} or None
    oa_msgs = [{"role": t.role, "content": t.content} for t in body.messages]
    try:
        reply = scout_chat_completion(oa_msgs, ctx_for_llm)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    last_user = None
    for t in reversed(body.messages):
        if t.role == "user":
            last_user = t
            break
    if last_user:
        scsvc.append_message(db, sess.id, "user", last_user.content)
    scsvc.append_message(db, sess.id, "scout", reply)

    return {"reply": reply, "sessionId": sess.id}


def _strength_fraction(raw: Union[float, int, None]) -> float:
    v = float(raw or 0)
    if v > 1.0:
        return max(0.0, min(1.0, v / 100.0))
    return max(0.0, min(1.0, v))


@router.get("/signal-update")
def scout_signal_update(limit: int = Query(24, ge=1, le=50), db: Session = Depends(get_db)):
    """Recent public signals for marketing /signals page (read-only)."""
    rows = (
        db.query(Signal)
        .options(joinedload(Signal.company))
        .order_by(desc(Signal.created_at))
        .limit(limit)
        .all()
    )
    signals = []
    for s in rows:
        c = s.company
        signals.append(
            {
                "companyId": c.id if c else None,
                "companyName": (c.name if c else None) or "Unknown company",
                "website": c.website if c else None,
                "type": s.signal_type,
                "strength": _strength_fraction(s.signal_strength),
                "text": s.signal_text or "",
                "sourceUrl": s.source_url,
            }
        )
    return {"signals": signals}


@router.post("/scan-for-results")
def scout_scan_for_results(body: ScanForResultsBody, db: Session = Depends(get_db)):
    """Resolve a URL to a company row (if present) and return SCOUT score + evidence."""
    raw = body.primary_url()
    if not raw:
        raise HTTPException(status_code=400, detail="url is required")
    dom = normalize_website_domain(raw) or normalize_domain(raw)
    company = None
    if dom:
        company = (
            db.query(Company)
            .options(joinedload(Company.signals), joinedload(Company.scores))
            .filter(Company.website_domain == dom)
            .first()
        )
        if company is None:
            escaped_dom = dom.replace("%", "\\%").replace("_", "\\_")
            company = (
                db.query(Company)
                .options(joinedload(Company.signals), joinedload(Company.scores))
                .filter(Company.website.ilike(f"%{escaped_dom}%"))
                .first()
            )
    payload = serialize_company_result(company, url=raw, name=None)
    # Frontend expects signal strength as a 0–1 fraction for percentage display.
    for sig in payload.get("signals") or []:
        if isinstance(sig, dict) and "strength" in sig:
            sig["strength"] = _strength_fraction(sig.get("strength"))
    return {"result": payload}

