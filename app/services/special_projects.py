"""Serialization + helpers for special projects (admin workflow + client portal)."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.special_project import (
    SpecialProject,
    SpecialProjectTarget,
    SpecialProjectUpdate,
)

# Ordered funnel stages for the beta/PoC motion — used for the portal funnel viz.
DEFAULT_PIPELINE_STAGES = [
    "targeted",
    "contacted",
    "replied",
    "discovery",
    "demo",
    "pilot_signed",
    "validated",
]
STAGE_INDEX = {stage: i for i, stage in enumerate(DEFAULT_PIPELINE_STAGES)}

ALLOWED_STATUSES = {"discovery", "outreach", "piloting", "active", "paused", "archived"}
UPDATE_CATEGORIES = {"milestone", "stat", "note", "outreach"}
CONTACT_STATUSES = {"none", "guessed", "verified"}


def slugify(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return base[:72] or "project"


def unique_slug(db: Session, name: str) -> str:
    base = slugify(name)
    slug = base
    n = 2
    while db.query(SpecialProject.id).filter(SpecialProject.slug == slug).first():
        slug = f"{base}-{n}"
        n += 1
    return slug


def _update_to_dict(u: SpecialProjectUpdate) -> dict[str, Any]:
    return {
        "id": u.id,
        "title": u.title,
        "body": u.body,
        "category": u.category,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


def project_to_admin_dict(p: SpecialProject, *, include_updates: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": p.id,
        "slug": p.slug,
        "share_token": p.share_token,
        "name": p.name,
        "company_website": p.company_website,
        "contact_email": p.contact_email,
        "robot_description": p.robot_description,
        "summary": p.summary,
        "status": p.status,
        "config": p.config or {},
        "metrics": p.metrics or {},
        "pipeline": p.pipeline or {},
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "portal_path": f"/p/{p.share_token}",
    }
    if include_updates:
        data["updates"] = [_update_to_dict(u) for u in (p.updates or [])]
        data["update_count"] = len(p.updates or [])
    return data


def project_to_public_dict(p: SpecialProject) -> dict[str, Any]:
    """Client-safe view — excludes internal fields (slug id, contact, share token)."""
    pipeline = p.pipeline or {}
    funnel = [
        {"stage": stage, "count": int(pipeline.get(stage) or 0)}
        for stage in DEFAULT_PIPELINE_STAGES
        if stage in pipeline
    ]
    # Include any custom stages the admin added beyond the defaults.
    for key, val in pipeline.items():
        if key not in DEFAULT_PIPELINE_STAGES:
            funnel.append({"stage": key, "count": int(val or 0)})
    return {
        "name": p.name,
        "company_website": p.company_website,
        "robot_description": p.robot_description,
        "summary": p.summary,
        "status": p.status,
        "metrics": p.metrics or {},
        "funnel": funnel,
        "accounts": [target_to_public_dict(t) for t in (p.targets or [])],
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "updates": [_update_to_dict(u) for u in (p.updates or [])],
    }


# ── Target queue (Cal's review-first outreach pipeline for a project) ────────────

def _stage_idx(stage: str | None) -> int:
    return STAGE_INDEX.get((stage or "targeted").strip().lower(), 0)


def target_can_send(t: SpecialProjectTarget) -> bool:
    """Review-first gate: only sendable once approved, with an email, pre-send."""
    return (
        (t.approved or "").strip().lower() == "yes"
        and bool((t.contact_email or "").strip())
        and t.sent_at is None
    )


def target_to_admin_dict(t: SpecialProjectTarget) -> dict[str, Any]:
    return {
        "id": t.id,
        "company": t.company,
        "website": t.website,
        "segment": t.segment,
        "best_fit_task": t.best_fit_task,
        "persona": t.persona,
        "sequence": t.sequence,
        "fit": t.fit,
        "signal": t.signal,
        "contact_name": t.contact_name,
        "contact_email": t.contact_email,
        "contact_title": t.contact_title,
        "contact_status": t.contact_status,
        "draft_subject": t.draft_subject,
        "draft_body": t.draft_body,
        "stage": t.stage,
        "approved": (t.approved or "no").strip().lower() == "yes",
        "can_send": target_can_send(t),
        "sent_at": t.sent_at.isoformat() if t.sent_at else None,
        "last_activity_at": t.last_activity_at.isoformat() if t.last_activity_at else None,
        "notes": t.notes,
        "sort_order": t.sort_order,
    }


def target_to_public_dict(t: SpecialProjectTarget) -> dict[str, Any]:
    """Client-safe target view — company + progress only, no third-party contact PII."""
    return {
        "company": t.company,
        "segment": t.segment,
        "best_fit_task": t.best_fit_task,
        "stage": t.stage,
        "contacted": t.sent_at is not None or _stage_idx(t.stage) >= _stage_idx("contacted"),
    }


def compute_funnel(targets: list[SpecialProjectTarget]) -> dict[str, int]:
    """Cumulative funnel — a target at stage k counts for every earlier stage."""
    counts = {stage: 0 for stage in DEFAULT_PIPELINE_STAGES}
    for t in targets:
        idx = _stage_idx(t.stage)
        for i in range(idx + 1):
            counts[DEFAULT_PIPELINE_STAGES[i]] += 1
    return counts


def compute_metrics(targets: list[SpecialProjectTarget]) -> dict[str, int]:
    funnel = compute_funnel(targets)
    return {
        "target_accounts": len(targets),
        "contacted": funnel["contacted"],
        "replies": funnel["replied"],
        "discovery_calls": funnel["discovery"],
        "beta_sites": funnel["pilot_signed"],
    }


def recompute_project_rollup(project: SpecialProject) -> None:
    """Sync the project funnel + KPIs from real target activity (not manual numbers)."""
    targets = list(project.targets or [])
    project.pipeline = compute_funnel(targets)
    metrics = dict(project.metrics or {})
    metrics.update(compute_metrics(targets))
    project.metrics = metrics


# ── NIMO outreach draft templates (T1 of each sequence in 03_cal_outreach_sequences.md) ──

NIMO_SENDER = "Bob Christopher, NIMO Technology"


def _first_name(contact_name: str | None) -> str:
    name = (contact_name or "").strip()
    if not name:
        return "there"
    return name.split()[0]


def _nimo_draft(t: SpecialProjectTarget) -> tuple[str, str]:
    """Return (subject, body) for a NIMO T1 draft based on the target's sequence."""
    first = _first_name(t.contact_name)
    company = (t.company or "your team").strip()
    task = (t.best_fit_task or "your signature workflow").strip()
    task_l = task[0].lower() + task[1:] if task else task
    signal = (t.signal or "your segment's labor and consistency pressure").strip().rstrip(".")
    seq = (t.sequence or "A").strip().upper()

    if seq == "B":
        subject = f"Co-developing the robot that does {task_l}"
        body = (
            f"Hi {first},\n\n"
            "Most kitchen \"robots\" are single-task rigs. Ours is a tactile foundation model — one "
            "backbone that transfers across cutting, portioning, and assembly, fine-tuned per task in "
            "days, and it feels contact force so it handles delicate and irregular items.\n\n"
            f"With {signal}, {company} is exactly who should help shape it. We're inviting a small group "
            f"of innovation partners to host a no-cost validation pilot on one workflow ({task_l}).\n\n"
            f"Could I show you the robot doing {task_l} on a 20-minute call?\n\n"
            f"— {NIMO_SENDER}"
        )
    elif seq == "C":
        subject = f"The labor math on {task_l}"
        body = (
            f"Hi {first},\n\n"
            f"{task} is repetitive, contact-heavy, and hard to staff — exactly where turnover and "
            "inconsistency cost you. We built a tactile humanoid that does it by feel, and we've proven "
            "7+ kitchen tasks on real hardware.\n\n"
            f"Given {signal}, I'd like to offer {company} a no-cost validation pilot: we install the "
            "robot and support it, you pick one site and one workflow, and we measure labor-hours "
            "displaced, throughput, and consistency together.\n\n"
            "20 minutes to see if it's worth testing?\n\n"
            f"— {NIMO_SENDER}"
        )
    else:  # Sequence A (default)
        subject = f"{task} at {company}, done by feel"
        body = (
            f"Hi {first},\n\n"
            "We built a humanoid that feels what it's handling — distributed touch sensors, sub-Newton "
            f"force control — so it does the contact-rich back-of-house work vision-only robots can't: "
            f"{task_l}, portioning by feel, multi-step assembly.\n\n"
            "We've demonstrated 7+ kitchen tasks on real hardware (not sim). Given "
            f"{signal}, {company}'s controlled kitchens are an ideal place to validate it.\n\n"
            "We're selecting a few beta sites to host a no-cost validation pilot — we bring the robot "
            "and engineering, you bring one real workflow. Worth a 20-minute call to see if it fits?\n\n"
            f"— {NIMO_SENDER}"
        )
    return subject, body


def build_target_draft(project: SpecialProject, t: SpecialProjectTarget) -> tuple[str, str]:
    """Compose a review-first outreach draft for a target.

    Currently NIMO-specific (the only special project). Keyed off the target's
    ``sequence`` so persona routing matches the GTM playbook.
    """
    return _nimo_draft(t)


def enrich_target_email(t: SpecialProjectTarget) -> bool:
    """Best-effort verified-contact lookup via Hunter domain search.

    Returns True when a new contact email was found. Fails soft (returns False)
    when Hunter is disabled, the target already has an email, or the API errors.
    """
    if (t.contact_email or "").strip():
        return False
    try:
        from app.services.hunter_client import (
            HunterClient,
            hunter_contact_enabled,
            pick_best_domain_email,
        )
    except Exception:
        return False
    if not hunter_contact_enabled():
        return False
    if not (t.website or "").strip() and not (t.company or "").strip():
        return False
    try:
        client = HunterClient()
        result = client.domain_search(domain=t.website, company=t.company)
    except Exception:
        return False
    best = pick_best_domain_email(result.get("emails") or [])
    if not best or not (best.get("email") or "").strip():
        return False
    t.contact_email = best["email"].strip()
    if best.get("name"):
        t.contact_name = best["name"]
    if best.get("title"):
        t.contact_title = best["title"]
    status = (best.get("verification_status") or "").strip().lower()
    t.contact_status = "verified" if status == "valid" else "guessed"
    return True
