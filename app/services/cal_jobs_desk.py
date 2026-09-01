"""Cal on the Jobs CRM desk after Open CRM.

Job: ask missing apply facts on kept jobs, then prepare the employer draft.
The operator reviews and sends. Cal does not sit on FIND. He does not send
buyer mail. Production CAL_AUTONOMY_ENABLED stays off.

Persona is job + tools + loop, not a warmer name.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.cal_persona import (
    CAL_JOBS_DESK_JOB,
    CAL_JOBS_DESK_TOOLS,
    CAL_JOBS_FORBIDDEN_TOOLS,
    CAL_NAME,
    CAL_TITLE,
)
from app.services.jobs_apply_draft import employer_contacts_from_job
from app.services.jobs_crm import (
    WORK_TASK_MODEL_SOURCE_REQUIRED,
    apply_to_job,
    catalog_skus_for_oem,
    list_kept_jobs,
    set_kept_job_task_model,
)
from app.services.pstack_protocol import wrap_site_agent

SURFACE = "jobs_crm_cal"
OWNER = "app/services/cal_jobs_desk.py"

FACT_TASK_MODEL = "task_model"
FACT_SKU = "selected_models"
FACT_RENTAL = "monthly_price"
FACT_POC = "poc"
PREPARED_STATUSES = frozenset({"prepared", "sent", "not_sent_no_email"})

ASK_TASK_MODEL = "Do you have a model for this work?"
ASK_SKU = "Which catalogued SKU goes on this apply? I will not invent one."
ASK_RENTAL = "What monthly price will you charge this employer?"
ASK_POC = "Any proof of concept? Employers prefer it. Skip is fine."
READY_TO_PREPARE = "I have enough to prepare the draft. Review it. You send."
ALL_READY = "Drafts are ready. Review them. You send. I do not email employers."
EMPTY_DESK = (
    "Keep jobs from FIND, then Open CRM. I work the list here. I do not hunt on FIND."
)
NO_CONTACTS = (
    "No employer email on this Job Card or stored public page. I will not invent one."
)
REFUSE_SEND = "You send. I prepare the draft. I do not email the employer."
REFUSE_BUYER = "I do not send buyer mail. Buyer sales stay frozen."
REFUSE_FIND = "FIND stays on /. I work kept jobs on this desk."
REFUSE_UNKNOWN = "I only run desk tools: read the list, save the task model, prepare the draft."


def cal_jobs_desk_intent() -> dict[str, Any]:
    """How-check: Cal on CRM is not the matcher, not FIND chat, not buyer mail."""
    return {
        "ok": True,
        "role": "act",
        "surface": SURFACE,
        "owner": OWNER,
        "not_the_matcher": True,
        "not_find_chat": True,
        "not_buyer_mail": True,
        "autonomy_enabled": False,
        "tools": list(CAL_JOBS_DESK_TOOLS),
        "forbidden_tools": list(CAL_JOBS_FORBIDDEN_TOOLS),
        "job": CAL_JOBS_DESK_JOB,
        "wrap": wrap_site_agent(role="act", surface=SURFACE),
    }


def _kind(row: dict[str, Any]) -> str:
    kind = str(row.get("work_task_model_kind") or "unknown").strip().lower()
    if kind in {"source", "self_train"}:
        return kind
    return "unknown"


def _app_status(row: dict[str, Any]) -> str | None:
    app = row.get("application") if isinstance(row.get("application"), dict) else None
    if not app:
        return None
    return str(app.get("send_status") or app.get("status") or "").strip().lower() or None


def _snapshot(row: dict[str, Any]) -> dict[str, Any]:
    app = row.get("application") if isinstance(row.get("application"), dict) else None
    if not app:
        return {}
    snap = app.get("offer_snapshot")
    if isinstance(snap, dict):
        return snap
    return app


def _models_on_file(row: dict[str, Any]) -> list[str]:
    app = row.get("application") if isinstance(row.get("application"), dict) else None
    snap = _snapshot(row)
    raw = []
    if app:
        raw = app.get("selected_models") or []
    if not raw:
        raw = snap.get("selected_models") or []
    return [str(m).strip() for m in raw if str(m).strip()]


def _price_on_file(row: dict[str, Any]) -> str:
    app = row.get("application") if isinstance(row.get("application"), dict) else None
    snap = _snapshot(row)
    if app and app.get("monthly_price"):
        return str(app.get("monthly_price") or "").strip()
    return str(snap.get("monthly_price") or "").strip()


def _poc_on_file(row: dict[str, Any]) -> dict[str, Any]:
    app = row.get("application") if isinstance(row.get("application"), dict) else None
    snap = _snapshot(row)
    evidence = ""
    video = ""
    skipped = False
    if app:
        evidence = str(app.get("poc_evidence") or "").strip()
        video = str(app.get("poc_video_url") or "").strip()
        skipped = bool(app.get("poc_skipped"))
    if not evidence:
        evidence = str(snap.get("poc_evidence") or "").strip()
    if not video:
        video = str(snap.get("poc_video_url") or "").strip()
    if not skipped:
        skipped = bool(snap.get("poc_skipped"))
    return {"evidence": evidence, "video": video, "skipped": skipped}


def _contacts(row: dict[str, Any]) -> list[dict[str, str]]:
    job = row.get("job") if isinstance(row.get("job"), dict) else {}
    people = employer_contacts_from_job(job)
    stored = str(row.get("employer_email") or "").strip()
    if stored and not any(c.get("email") == stored for c in people):
        people.append({"email": stored, "source": "job_card"})
    return people


def missing_apply_facts(row: dict[str, Any]) -> list[str]:
    """Facts Cal still needs before prepare. PoC is last and skippable."""
    status = _app_status(row)
    if status in PREPARED_STATUSES:
        return []
    missing: list[str] = []
    if _kind(row) == "unknown":
        missing.append(FACT_TASK_MODEL)
    if not _models_on_file(row):
        missing.append(FACT_SKU)
    if not _price_on_file(row):
        missing.append(FACT_RENTAL)
    poc = _poc_on_file(row)
    if not poc["evidence"] and not poc["video"] and not poc["skipped"]:
        missing.append(FACT_POC)
    return missing


def _ask_for(fact: str, employer: str) -> str:
    shop = (employer or "this employer").strip() or "this employer"
    if fact == FACT_TASK_MODEL:
        return f"{ASK_TASK_MODEL} This one is {shop}."
    if fact == FACT_SKU:
        return ASK_SKU
    if fact == FACT_RENTAL:
        return f"{ASK_RENTAL} Employer: {shop}."
    if fact == FACT_POC:
        return ASK_POC
    return READY_TO_PREPARE


def _job_card(row: dict[str, Any]) -> dict[str, Any]:
    missing = missing_apply_facts(row)
    contacts = _contacts(row)
    employer = str(row.get("employer_name") or "").strip()
    work = str(row.get("work_title") or "").strip()
    robot = str(row.get("robot_name") or "").strip() or None
    skus = catalog_skus_for_oem(url=row.get("robot_url"), company_name=robot)
    status = _app_status(row)
    next_fact = missing[0] if missing else None
    if status in PREPARED_STATUSES:
        prompt = ALL_READY if not missing else _ask_for(missing[0], employer)
    elif not missing:
        prompt = READY_TO_PREPARE
        next_fact = "prepare_apply"
    else:
        prompt = _ask_for(missing[0], employer)
    return {
        "job_key": row.get("job_key"),
        "employer_name": employer,
        "work_title": work,
        "workplace": row.get("workplace"),
        "robot_name": robot,
        "robot_url": row.get("robot_url"),
        "work_task_model_kind": _kind(row),
        "work_task_model_source": row.get("work_task_model_source"),
        "contacts": contacts,
        "contacts_note": None if contacts else NO_CONTACTS,
        "selected_models": _models_on_file(row),
        "catalog_skus": skus,
        "monthly_price": _price_on_file(row) or None,
        "poc": _poc_on_file(row),
        "application_status": status,
        "application": row.get("application"),
        "missing": missing,
        "next_fact": next_fact,
        "prompt": prompt,
    }


def read_desk(db: Session, user: dict) -> dict[str, Any]:
    """Kept jobs + robot identity + the next fact Cal should ask."""
    rows = list_kept_jobs(db, user)
    jobs = [_job_card(row) for row in rows]
    focus = next((job for job in jobs if job["missing"] or job["next_fact"] == "prepare_apply"), None)
    if not jobs:
        greeting = EMPTY_DESK
        next_question = None
    elif focus and focus["next_fact"] == "prepare_apply":
        greeting = (
            f"I'm {CAL_NAME}. {len(jobs)} kept job"
            f"{'' if len(jobs) == 1 else 's'} on this desk. {READY_TO_PREPARE}"
        )
        next_question = {
            "job_key": focus["job_key"],
            "fact": "prepare_apply",
            "prompt": focus["prompt"],
        }
    elif focus:
        greeting = (
            f"I'm {CAL_NAME}. I work these kept jobs with you. "
            f"I ask what's missing, prepare the apply draft, and you send."
        )
        next_question = {
            "job_key": focus["job_key"],
            "fact": focus["next_fact"],
            "prompt": focus["prompt"],
        }
    else:
        greeting = ALL_READY
        next_question = None
    return {
        "ok": True,
        "name": CAL_NAME,
        "title": CAL_TITLE,
        "job": CAL_JOBS_DESK_JOB,
        "surface": SURFACE,
        "tools": list(CAL_JOBS_DESK_TOOLS),
        "forbidden_tools": list(CAL_JOBS_FORBIDDEN_TOOLS),
        "operator_sends": True,
        "autonomy_enabled": False,
        "greeting": greeting,
        "next_question": next_question,
        "jobs": jobs,
        "intent": cal_jobs_desk_intent(),
    }


def _refuse(tool: str) -> dict[str, Any]:
    name = (tool or "").strip().lower()
    if name in {"send", "send_application", "send_employer"}:
        detail = REFUSE_SEND
    elif name in {"send_buyer_intro", "buyer_mail", "signal_hop", "generate_plan"}:
        detail = REFUSE_BUYER
    elif name in {"find_jobs", "find", "match_jobs"}:
        detail = REFUSE_FIND
    else:
        detail = REFUSE_UNKNOWN
    return {
        "ok": False,
        "refused": True,
        "tool": name or "unknown",
        "detail": detail,
    }


def _resolve_models(
    *,
    selected: list[str] | None,
    robot_name: str | None,
    catalog: list[dict[str, str]],
) -> list[str]:
    names = [str(m).strip() for m in (selected or []) if str(m).strip()]
    catalog_names = [str(s.get("name") or "").strip() for s in catalog if s.get("name")]
    catalog_keys = {n.lower() for n in catalog_names}
    if catalog_names:
        ok = [n for n in names if n.lower() in catalog_keys]
        if not ok:
            raise ValueError("Pick a catalogued SKU. I will not invent one.")
        return ok
    if names:
        return names
    robot = (robot_name or "").strip()
    if robot:
        return [robot]
    raise ValueError("Select at least one catalogued model you will use. We do not invent SKUs.")


def run_desk_tool(
    db: Session,
    user: dict,
    *,
    tool: str,
    job_key: str | None = None,
    kind: str | None = None,
    source: str | None = None,
    robot_name: str | None = None,
    selected_models: list[str] | None = None,
    monthly_price: str | None = None,
    poc_evidence: str | None = None,
    poc_video_url: str | None = None,
    poc_skipped: bool = False,
    why: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Run one Jobs-desk tool. Never invent emails, SKUs, employers, or models."""
    name = (tool or "read_desk").strip().lower()
    if name in CAL_JOBS_FORBIDDEN_TOOLS or name not in set(CAL_JOBS_DESK_TOOLS):
        out = _refuse(name)
        out["desk"] = read_desk(db, user)
        return out

    result: dict[str, Any] | None = None
    if name == "save_task_model":
        if _kind({"work_task_model_kind": kind}) == "source" and not (source or "").strip():
            raise ValueError(WORK_TASK_MODEL_SOURCE_REQUIRED)
        result = set_kept_job_task_model(
            db, user, job_key=job_key or "", kind=kind, source=source
        )
    elif name == "prepare_apply":
        rows = {row.get("job_key"): row for row in list_kept_jobs(db, user)}
        row = rows.get(job_key)
        if not row:
            raise KeyError("kept_job")
        if _kind(row) == "unknown":
            raise ValueError(ASK_TASK_MODEL)
        robot = (robot_name or row.get("robot_name") or "this robot").strip()
        catalog = catalog_skus_for_oem(url=row.get("robot_url"), company_name=robot)
        models = _resolve_models(
            selected=selected_models or _models_on_file(row),
            robot_name=robot,
            catalog=catalog,
        )
        price = (monthly_price or _price_on_file(row) or "").strip()
        poc = _poc_on_file(row)
        result = apply_to_job(
            db,
            user,
            job_key=str(job_key),
            robot_name=robot,
            selected_models=models,
            monthly_price=price,
            poc_evidence=poc_evidence if poc_evidence is not None else poc["evidence"],
            poc_video_url=poc_video_url if poc_video_url is not None else poc["video"],
            poc_skipped=bool(poc_skipped or poc["skipped"]),
            why=why or "",
            company_name=company_name,
            job=row.get("job") if isinstance(row.get("job"), dict) else None,
            send=False,
        )

    desk = read_desk(db, user)
    return {
        "ok": True,
        "tool": name,
        "result": result,
        "desk": desk,
        "next_question": desk.get("next_question"),
    }
