"""
Public SCOUT marketing chat API (anonymous fingerprint sessions).

Parity target: rfr_cursor_package `scout.getSession`, `scout.updateSession`,
`scout.saveMessage`, `scout.chat` — v1 implements session + chat + history.
Skill endpoints: discover, develop-lead, scan-company, scan-for-results, run activation.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user, optional_user
from app.api.crm import _ensure_default_team
from app.api.user import _ensure_profile
from app.database import get_db
from app.models.crm import CrmAccount
from app.models.scout_chat import ScoutActivation, ScoutSession
from app.models.user_profile import UserProfile
from app.services import scout_chat_service as scsvc
from app.services.scout_llm import scout_chat_completion
from app.services import scout_discovery_agent as discovery

logger = logging.getLogger(__name__)

router = APIRouter()

ACTIVATION_STATUSES = [
    "queued",
    "evaluating",
    "drafted",
    "awaiting_approval",
    "paused",
    "sent",
    "replied",
    "meeting_booked",
]

ACTIVATION_STATUS_META = {
    "queued": "Queued for SIGNAL evaluation.",
    "evaluating": "SIGNAL is evaluating lead fit and sales angles.",
    "drafted": "Strategy and Cal outreach drafts are ready.",
    "awaiting_approval": "Drafts are waiting for user approval.",
    "paused": "User interrupted SIGNAL to adjust Cal's message, timing, or cadence.",
    "sent": "Cal has sent outreach and SIGNAL is watching for replies.",
    "replied": "A lead has replied and needs attention.",
    "meeting_booked": "A meeting has been booked.",
}


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


class ActivationControlBody(BaseModel):
    action: Literal["pause", "resume", "update_plan"]
    message_note: Optional[str] = Field(None, max_length=2000)
    timing_note: Optional[str] = Field(None, max_length=1000)
    cadence_note: Optional[str] = Field(None, max_length=1000)


class DiscoverBody(BaseModel):
    fingerprint: str = Field(..., min_length=8, max_length=80)
    category: Optional[str] = Field(None, max_length=120)
    robot_category: Optional[str] = Field(None, max_length=120)
    robotCategory: Optional[str] = Field(None, max_length=120)
    vertical: Optional[str] = Field(None, max_length=120)
    territory: Optional[str] = Field(None, max_length=120)
    limit: int = Field(8, ge=1, le=25)

    def category_value(self) -> Optional[str]:
        return self.category or self.robot_category or self.robotCategory


class DevelopLeadBody(BaseModel):
    fingerprint: Optional[str] = Field(None, min_length=8, max_length=80)
    company_id: int = Field(..., ge=1)
    refresh_inference: bool = True


class ScanCompanyBody(BaseModel):
    fingerprint: str = Field(..., min_length=8, max_length=80)
    url: Optional[str] = Field(None, max_length=512)
    company_name: Optional[str] = Field(None, max_length=240)
    companyName: Optional[str] = Field(None, max_length=240)
    robot_category: Optional[str] = Field(None, max_length=120)
    robotCategory: Optional[str] = Field(None, max_length=120)


class ScanForResultsBody(BaseModel):
    company_url: str = Field(..., min_length=4, max_length=512)
    companyUrl: Optional[str] = Field(None, max_length=512)
    fingerprint: Optional[str] = Field(None, min_length=8, max_length=80)
    robot_name: Optional[str] = Field(None, max_length=200)
    limit: int = Field(8, ge=1, le=25)

    def url_value(self) -> str:
        return (self.company_url or self.companyUrl or "").strip()


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
    plan = {
        "materials": {
            "choice": material,
            "next": {
                "upload": "Parse deck, extract proof points, and align Cal's messaging to selected leads.",
                "suggest": "Generate deck outline, ROI story, objection handling, and lead-specific talk track.",
                "skip": "Start with lead research and prepare Cal outreach using available signals.",
            }[material],
            "filename": body.filename(),
        },
        "steps": [
            "Evaluate each selected lead and confirm sales angle.",
            "Build lead-specific strategy, ROI thesis, and activity schedule.",
            "Prepare Cal's email and introduction sequence for review.",
            "Track replies and move responding leads to active pipeline.",
            "Ping user when a lead responds or meeting scheduling is needed.",
        ],
        "mode": mode,
        "sending_policy": {
            "manual": "Cal drafts only until user approves the next step.",
            "assisted": "Ask before Cal sends each message.",
            "autopilot": "Prepare work in the background, but keep Cal's outbound activity visible and interruptible.",
        }[mode],
        "safety_requirements": [
            {"key": "sender_identity", "label": "Verified sender identity", "required": mode in {"assisted", "autopilot"}},
            {"key": "approval_rules", "label": "Message approval required before every send", "required": True},
            {"key": "crm_capture", "label": "Leads saved to your CRM", "required": True},
            {"key": "interrupt_controls", "label": "User can pause or change message, timing, and cadence", "required": True},
            {"key": "unsubscribe", "label": "Unsubscribe and compliance footer", "required": mode in {"assisted", "autopilot"}},
            {"key": "daily_send_cap", "label": "Daily send cap", "required": mode in {"assisted", "autopilot"}},
            {"key": "suppression_list", "label": "Suppression list check", "required": mode in {"assisted", "autopilot"}},
        ],
        "notification_policy": {
            "reply": "Create an in-app alert when a lead replies and mark the activation as replied.",
            "meeting": "Create an in-app alert when scheduling is needed or a meeting is booked.",
            "email": "Email notifications stay off until sender identity and account notification settings are configured.",
        },
        "user_feedback_loop": {
            "next_checkpoint": "Review CRM accounts, approve or edit Cal drafts, then explicitly approve sending.",
            "interrupt": "Pause SIGNAL any time to change Cal's message, timing, or follow-up cadence.",
            "autopilot_guardrail": "Autopilot prepares work in the background, but Cal's outbound messages remain visible with interruption controls.",
        },
    }
    if material == "suggest":
        plan["deck_strategy"] = {
            "recommended_format": "Short sales narrative deck, 8-10 slides, built around operational pain and payback.",
            "sections": [
                "Lead-specific pain and why now",
                "Current workflow cost and staffing pressure",
                "Automation use case mapped to buyer operations",
                "ROI model with labor, throughput, safety, and service assumptions",
                "Proof points, implementation path, and next meeting ask",
            ],
            "positioning": "Lead with measurable operating pressure first, then introduce robotics as the practical response.",
            "next_output": "SIGNAL should prepare a deck outline and ROI assumptions before Cal outreach approval.",
        }
    return plan


def _serialize_activation(row: ScoutActivation) -> Dict[str, Any]:
    return {
        "id": row.id,
        "status": row.status,
        "statusFlow": [
            {
                "id": status,
                "label": status.replace("_", " ").title(),
                "description": ACTIVATION_STATUS_META[status],
                "active": status == row.status,
            }
            for status in ACTIVATION_STATUSES
        ],
        "sourceUrl": row.source_url,
        "material": row.material_choice,
        "materialFilename": row.material_filename,
        "scope": row.scope_choice,
        "mode": row.mode_choice,
        "leadCount": len(row.lead_ids or []),
        "leadIds": row.lead_ids or [],
        "leads": row.leads_snapshot or [],
        "workPlan": row.work_plan or {},
        "activityLog": row.activity_log or [],
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        "requiresAccount": row.user_id is None and row.mode_choice in {"assisted", "autopilot"},
    }


def _activation_for_user(db: Session, activation_id: int, user_id: UUID) -> ScoutActivation:
    row = (
        db.query(ScoutActivation)
        .filter(ScoutActivation.id == activation_id, ScoutActivation.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Activation not found")
    return row


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


@router.get("/activations")
def scout_list_activations(
    fingerprint: str = Query(..., min_length=8, max_length=80),
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(optional_user),
    limit: int = Query(8, ge=1, le=50),
):
    fp = (fingerprint or "").strip()[:80]
    session_row = db.query(ScoutSession).filter(ScoutSession.fingerprint == fp).first()
    filters = []
    if session_row:
        filters.append(ScoutActivation.session_id == session_row.id)
    if user and user.get("uid"):
        try:
            user_id = UUID(str(user["uid"]))
            filters.append(ScoutActivation.user_id == user_id)
        except (TypeError, ValueError):
            pass
    if not filters:
        return {"activations": []}
    rows = (
        db.query(ScoutActivation)
        .filter(or_(*filters))
        .order_by(ScoutActivation.created_at.desc(), ScoutActivation.id.desc())
        .limit(limit)
        .all()
    )
    return {"activations": [_serialize_activation(row) for row in rows]}


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
    user: dict = Depends(_require_user),
):
    sess, _ = scsvc.upsert_session(db, body.fingerprint)
    try:
        user_id = UUID(str(user["uid"]))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Sign in before activating SIGNAL") from None
    _ensure_profile(db, str(user_id), user.get("email") or "")
    team = _ensure_default_team(db, user_id, user.get("email") or "")
    sess.user_id = user_id
    if body.source():
        sess.company_url = body.source()

    leads = [lead.dict() for lead in body.leads]
    captured_accounts = []
    for lead in body.leads:
        company_id = None
        try:
            company_id = int(lead.id)
        except (TypeError, ValueError):
            company_id = None
        existing = None
        if company_id is not None:
            existing = (
                db.query(CrmAccount)
                .filter(CrmAccount.team_id == team.id, CrmAccount.company_id == company_id)
                .first()
            )
        account = existing
        if not account:
            account = CrmAccount(
                team_id=team.id,
                company_id=company_id,
                name=lead.company,
                owner_user_id=user_id,
                outreach_stage="review_required",
            )
            db.add(account)
            db.flush()
        captured_accounts.append({"crm_account_id": str(account.id), "company": lead.company, "company_id": company_id})
    activation = ScoutActivation(
        session_id=sess.id,
        user_id=user_id,
        source_url=body.source(),
        material_choice=body.material(),
        material_filename=body.filename(),
        scope_choice=body.scope(),
        mode_choice=body.mode(),
        status="evaluating",
        lead_ids=[lead["id"] for lead in leads],
        leads_snapshot=leads,
        work_plan=_activation_work_plan(body),
        activity_log=[
            {
                "type": "evaluating",
                "message": f"SIGNAL is developing {len(leads)} lead(s): inference, sales brief, and Cal drafts.",
            },
            {
                "type": "review_queue_created",
                "message": f"Review queue created for {len(leads)} lead(s). Leads saved to CRM; sends require approval.",
            },
            {
                "type": "crm_capture",
                "message": "Lead accounts captured in CRM for user review.",
                "accounts": captured_accounts,
            },
            {
                "type": "materials",
                "message": f"Material path: {body.material()}",
            },
            {
                "type": "mode",
                "message": f"Automation mode: {body.mode()}",
            },
            {
                "type": "status",
                "message": ACTIVATION_STATUS_META["awaiting_approval"],
            },
        ],
    )
    db.add(activation)
    db.flush()
    scsvc.append_message(
        db,
        sess.id,
        "scout",
        f"SIGNAL created an approval-gated review queue for {len(leads)} lead(s) in {body.mode()} mode.",
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

    discovery.schedule_activation_run(activation.id, user_id, team.id)

    return {
        "id": activation.id,
        "status": "evaluating",
        "leadCount": len(leads),
        "mode": activation.mode_choice,
        "scope": activation.scope_choice,
        "material": activation.material_choice,
        "workPlan": activation.work_plan,
        "activityLog": activation.activity_log,
        "requiresAccount": False,
        "automationStarted": True,
    }


@router.post("/discover")
def scout_discover_prospects(body: DiscoverBody, db: Session = Depends(get_db)):
    """findProspects — ranked HOT/WARM companies from the live pipeline."""
    sess, _ = scsvc.upsert_session(db, body.fingerprint)
    if body.vertical:
        scsvc.update_session_context(db, sess.id, vertical=body.vertical)
    if body.territory:
        scsvc.update_session_context(db, sess.id, territory=body.territory)
    cat = body.category_value()
    if cat:
        scsvc.update_session_context(db, sess.id, robot_category=cat)

    result = discovery.discover_prospects(
        db,
        robot_category=cat,
        vertical=body.vertical,
        territory=body.territory,
        limit=body.limit,
    )
    scsvc.append_message(
        db,
        sess.id,
        "scout",
        result.get("summary") or f"Found {result.get('count', 0)} prospects.",
        "findProspects",
        result,
    )
    db.commit()
    return result


@router.post("/develop-lead")
def scout_develop_lead(
    body: DevelopLeadBody,
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(optional_user),
):
    """Develop one pipeline lead: inference, brief, Cal draft preview."""
    if body.fingerprint:
        scsvc.upsert_session(db, body.fingerprint)
    try:
        payload = discovery.develop_lead_brief(
            db,
            body.company_id,
            refresh_inference=body.refresh_inference,
            include_draft=True,
        )
    except Exception as exc:
        logger.exception("develop-lead failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not payload.get("found"):
        raise HTTPException(status_code=404, detail=payload.get("error") or "Lead not found")
    if body.fingerprint and user is None:
        sess, _ = scsvc.upsert_session(db, body.fingerprint)
        scsvc.append_message(
            db,
            sess.id,
            "scout",
            f"Developed lead brief for company {body.company_id}.",
            "developLead",
            payload,
        )
        db.commit()
    return payload


@router.post("/scan-company")
def scout_scan_company(body: ScanCompanyBody, db: Session = Depends(get_db)):
    """scanCompany — match URL or name to pipeline company + development brief."""
    sess, _ = scsvc.upsert_session(db, body.fingerprint)
    url = (body.url or "").strip() or None
    name = body.company_name or body.companyName
    cat = body.robot_category or body.robotCategory
    if url:
        scsvc.update_session_context(db, sess.id, company_url=url)

    result = discovery.scan_company_in_pipeline(
        db, url=url, company_name=name, robot_category=cat
    )
    msg = (
        f"Scanned {url or name}: score {result.get('score')}/100"
        if result.get("found")
        else (result.get("message") or "Company not in pipeline.")
    )
    scsvc.append_message(db, sess.id, "scout", msg, "scanCompany", result)
    db.commit()
    return result


@router.post("/scan-for-results")
def scout_scan_for_results(body: ScanForResultsBody, db: Session = Depends(get_db)):
    """Results page: robot-ready match + SCOUT timing/relevance on each prospect."""
    if body.fingerprint:
        sess, _ = scsvc.upsert_session(db, body.fingerprint)
        scsvc.update_session_context(db, sess.id, company_url=body.url_value())

    try:
        result = discovery.scan_for_results(
            db,
            company_url=body.url_value(),
            robot_name=body.robot_name,
            limit=body.limit,
        )
    except Exception as exc:
        logger.exception("scan-for-results failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if body.fingerprint:
        scsvc.append_message(
            db,
            sess.id,
            "scout",
            f"Matched {len(result.get('prospects') or [])} prospects for {body.url_value()}.",
            "scanForResults",
            {"prospect_count": len(result.get("prospects") or [])},
        )
        db.commit()
    return result


@router.get("/discovery-digest")
def scout_discovery_digest(
    fingerprint: str = Query(..., min_length=8, max_length=80),
    robot_category: Optional[str] = Query(None),
    robotCategory: Optional[str] = Query(None),
    vertical: Optional[str] = Query(None),
    territory: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=12),
    db: Session = Depends(get_db),
):
    """Proactive digest of top matching pipeline prospects (real data)."""
    sess, _ = scsvc.upsert_session(db, fingerprint)
    cat = robot_category or robotCategory or sess.robot_category
    vert = vertical or sess.vertical
    terr = territory or sess.territory
    return discovery.discovery_digest(
        db,
        robot_category=cat,
        vertical=vert,
        territory=terr,
        limit=limit,
    )


@router.post("/activations/{activation_id}/run")
def scout_run_activation(
    activation_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    """Re-run discovery + development for an existing activation queue."""
    try:
        user_id = UUID(str(user["uid"]))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Sign in required") from None
    activation = _activation_for_user(db, activation_id, user_id)
    team = _ensure_default_team(db, user_id, user.get("email") or "")
    result = discovery.execute_activation(
        db, activation, team_id=team.id, owner_user_id=user_id
    )
    db.refresh(activation)
    return {"activation": _serialize_activation(activation), "run": result}


@router.patch("/activations/{activation_id}/control")
def scout_control_activation(
    activation_id: int,
    body: ActivationControlBody,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    try:
        user_id = UUID(str(user["uid"]))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Sign in required") from None
    activation = _activation_for_user(db, activation_id, user_id)
    log = list(activation.activity_log or [])
    if body.action == "pause":
        activation.status = "paused"
        log.append({"type": "paused", "message": "User interrupted SIGNAL automation for review."})
    elif body.action == "resume":
        activation.status = "awaiting_approval"
        log.append({"type": "resumed", "message": "User resumed SIGNAL review queue. Sends still require approval."})
    else:
        plan = dict(activation.work_plan or {})
        plan["user_adjustments"] = {
            "message_note": body.message_note,
            "timing_note": body.timing_note,
            "cadence_note": body.cadence_note,
        }
        activation.work_plan = plan
        activation.status = "awaiting_approval"
        log.append(
            {
                "type": "plan_updated",
                "message": "User adjusted Cal message, timing, or follow-up cadence.",
                "message_note": body.message_note,
                "timing_note": body.timing_note,
                "cadence_note": body.cadence_note,
            }
        )
    activation.activity_log = log
    db.commit()
    db.refresh(activation)
    return _serialize_activation(activation)

