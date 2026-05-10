"""
Public SCOUT marketing chat API (anonymous fingerprint sessions).

Parity target: rfr_cursor_package `scout.getSession`, `scout.updateSession`,
`scout.saveMessage`, `scout.chat` — v1 implements session + chat + history.
Skill endpoints (scanCompany, …) can follow.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_deps import optional_user
from app.database import get_db
from app.models.scout_chat import ScoutActivation, ScoutSession
from app.models.user_profile import UserProfile
from app.services import scout_chat_service as scsvc
from app.services.scout_llm import scout_chat_completion

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


class ActivationLead(BaseModel):
    id: str = Field(..., min_length=1, max_length=120)
    company: str = Field(..., min_length=1, max_length=240)
    score: Optional[int] = None
    signal: Optional[str] = Field(None, max_length=1200)
    signalType: Optional[str] = Field(None, max_length=120)
    action: Optional[str] = Field(None, max_length=800)
    timing: Optional[str] = Field(None, max_length=160)
    relevance: Optional[str] = Field(None, max_length=1600)


class ActivationBody(BaseModel):
    fingerprint: str = Field(..., min_length=8, max_length=80)
    source_url: Optional[str] = Field(None, max_length=512)
    sourceUrl: Optional[str] = Field(None, max_length=512)
    material_choice: Optional[Literal["upload", "suggest", "skip"]] = None
    materialChoice: Optional[Literal["upload", "suggest", "skip"]] = None
    material_filename: Optional[str] = Field(None, max_length=512)
    materialFilename: Optional[str] = Field(None, max_length=512)
    scope_choice: Optional[Literal["all", "selected", "top"]] = None
    scopeChoice: Optional[Literal["all", "selected", "top"]] = None
    mode_choice: Optional[Literal["manual", "assisted", "autopilot"]] = None
    modeChoice: Optional[Literal["manual", "assisted", "autopilot"]] = None
    leads: List[ActivationLead] = Field(..., min_length=1, max_length=50)

    def source(self) -> Optional[str]:
        return self.source_url or self.sourceUrl

    def material(self) -> str:
        return self.material_choice or self.materialChoice or "suggest"

    def filename(self) -> Optional[str]:
        return self.material_filename or self.materialFilename

    def scope(self) -> str:
        return self.scope_choice or self.scopeChoice or "top"

    def mode(self) -> str:
        return self.mode_choice or self.modeChoice or "manual"


def _serialize_message(m: Any) -> Dict[str, Any]:
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "skillInvoked": m.skill_invoked,
        "skillData": m.skill_data,
        "createdAt": m.created_at.isoformat() if m.created_at else None,
    }


def _activation_work_plan(body: ActivationBody) -> Dict[str, Any]:
    material = body.material()
    mode = body.mode()
    return {
        "materials": {
            "choice": material,
            "next": {
                "upload": "Parse deck, extract proof points, and align messaging to selected leads.",
                "suggest": "Generate deck outline, ROI story, objection handling, and lead-specific talk track.",
                "skip": "Start with lead research and draft outreach using available signals.",
            }[material],
            "filename": body.filename(),
        },
        "steps": [
            "Evaluate each selected lead and confirm sales angle.",
            "Build lead-specific strategy, ROI thesis, and activity schedule.",
            "Draft email and introduction sequence for review.",
            "Track replies and move responding leads to active pipeline.",
            "Ping user when a lead responds or meeting scheduling is needed.",
        ],
        "mode": mode,
        "sending_policy": {
            "manual": "Drafts only until user takes action.",
            "assisted": "Ask before sending each message.",
            "autopilot": "Send and reply within account guardrails.",
        }[mode],
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


@router.post("/activations")
def scout_create_activation(
    body: ActivationBody,
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(optional_user),
):
    sess, _ = scsvc.upsert_session(db, body.fingerprint)
    user_id = None
    if user and user.get("uid"):
        try:
            candidate_user_id = UUID(str(user["uid"]))
            if db.query(UserProfile.id).filter(UserProfile.id == candidate_user_id).first():
                user_id = candidate_user_id
                sess.user_id = user_id
        except (TypeError, ValueError):
            user_id = None
    if body.source():
        sess.company_url = body.source()
    db.commit()

    leads = [lead.dict() for lead in body.leads]
    activation = ScoutActivation(
        session_id=sess.id,
        user_id=user_id,
        source_url=body.source(),
        material_choice=body.material(),
        material_filename=body.filename(),
        scope_choice=body.scope(),
        mode_choice=body.mode(),
        status="queued" if body.mode() == "manual" else "preview" if user_id is None else "queued",
        lead_ids=[lead["id"] for lead in leads],
        leads_snapshot=leads,
        work_plan=_activation_work_plan(body),
        activity_log=[
            {
                "type": "activation_created",
                "message": f"SCOUT activation created for {len(leads)} lead(s).",
            },
            {
                "type": "materials",
                "message": f"Material path: {body.material()}",
            },
            {
                "type": "mode",
                "message": f"Automation mode: {body.mode()}",
            },
        ],
    )
    db.add(activation)
    db.flush()
    scsvc.append_message(
        db,
        sess.id,
        "scout",
        f"SCOUT activation queued for {len(leads)} lead(s) in {body.mode()} mode.",
        "activateScout",
        {
            "activationId": activation.id,
            "leadCount": len(leads),
            "mode": body.mode(),
            "scope": body.scope(),
            "material": body.material(),
        },
    )
    db.commit()
    db.refresh(activation)
    return {
        "id": activation.id,
        "status": activation.status,
        "leadCount": len(leads),
        "mode": activation.mode_choice,
        "scope": activation.scope_choice,
        "material": activation.material_choice,
        "workPlan": activation.work_plan,
        "activityLog": activation.activity_log,
        "requiresAccount": activation.status == "preview",
    }

