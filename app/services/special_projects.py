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

NIMO_SENDER = "Cal, NIMO Technology"


def _nimo_greeting(contact_name: str | None, company: str) -> str:
    """A greeting that never opens with the weak, impersonal 'Hi there,'."""
    name = (contact_name or "").strip()
    if name:
        return f"Hi {name.split()[0]},"
    if company and company != "your team":
        return f"Hi {company} team,"
    return "Hello,"


def _nimo_draft(t: SpecialProjectTarget) -> tuple[str, str]:
    """Return (subject, body) for a NIMO T1 draft based on the target's sequence."""
    company = (t.company or "your team").strip()
    greeting = _nimo_greeting(t.contact_name, company)
    task = (t.best_fit_task or "your signature workflow").strip()
    task_l = task[0].lower() + task[1:] if task else task
    task_cap = task[0].upper() + task[1:] if task else task
    signal = (t.signal or "your labor and consistency pressure").strip().rstrip(".")
    # Signal is a description of the account (e.g. "Largest contract caterer…"),
    # so weave it as an appositive ("{company} — {signal} — …") instead of the
    # clumsy "Given {Signal}," which reads with a stray capital mid-sentence.
    signal_l = signal[0].lower() + signal[1:] if signal else signal
    seq = (t.sequence or "A").strip().upper()

    if seq == "B":
        # Innovation / co-development angle.
        subject = f"Help shape the robot that does {task_l}"
        body = (
            f"{greeting}\n\n"
            f"Quick idea for {company}. Most kitchen \"robots\" are single-task rigs bolted to one "
            "station. Ours is one robot that moves across cutting, portioning, and assembly — retrained "
            "for a new task in days — and because it senses touch and pressure, it handles the "
            "delicate, irregular items camera-only machines drop.\n\n"
            f"{company} stood out to us — {signal_l} — as exactly the kind of operator we want shaping "
            f"it. We're inviting a few partners to help build it through a no-cost pilot on one workflow "
            f"({task_l}) — your input steers what we build next.\n\n"
            f"Could I show you the robot doing {task_l} on a 20-minute call?\n\n"
            f"— {NIMO_SENDER}"
        )
    elif seq == "C":
        # ROI / labor-math angle.
        subject = f"The labor math on {task_l}"
        body = (
            f"{greeting}\n\n"
            f"{task_cap} is repetitive, hands-on, and hard to keep staffed — so turnover and inconsistency "
            "quietly eat into margin. We built a robot that does it by feel, and it already runs "
            "more than seven real kitchen jobs on working hardware today.\n\n"
            f"For {company} — {signal_l} — here's the offer: a no-cost pilot. We install the robot and "
            "support it, you pick one site and one workflow, and we measure labor-hours saved, "
            "throughput, and consistency together — real numbers, on your floor.\n\n"
            "20 minutes to see if it's worth a test?\n\n"
            f"— {NIMO_SENDER}"
        )
    else:  # Sequence A (default) — problem-first, tactile differentiator.
        subject = f"A robot that can actually do {task_l}"
        body = (
            f"{greeting}\n\n"
            "Nice to meet you. I work with restaurant owners and operators to improve their workflows "
            "through automation. For most restaurants, that has meant robots that run on cameras alone, "
            "so they fumble anything they have to touch. Our robot is uniquely different in important "
            "ways. It feels what it's handling — touch sensors and fine pressure control — so it does "
            f"the work labor can't or won't: {task_l}, portioning by feel, delicate multi-step "
            "handling. It already runs more than seven real kitchen jobs on working hardware today.\n\n"
            f"{company} stood out to me — {signal_l} — as a place the robot could learn and earn its "
            "keep. We're placing select robots in no-cost pilots: we bring the robot and the engineers, "
            "you pick one workflow, and we measure labor-hours saved and consistency of product side by "
            "side.\n\n"
            f"Would you be open to a 20-minute demo? I'll show it doing {task_l} live.\n\n"
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
