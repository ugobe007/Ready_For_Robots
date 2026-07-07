"""Special projects — private admin GTM workflow + token-gated client portal.

Admin (auth required):  /api/admin/special-projects/...
Public (share token):   /api/special-projects/portal/{token}
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import csv
import io
from datetime import datetime, timezone

from fastapi.responses import Response

from app.api.auth_deps import require_admin
from app.database import get_db
from app.models.special_project import (
    SpecialProject,
    SpecialProjectTarget,
    SpecialProjectUpdate,
    _new_share_token,
)
from app.services.special_projects import (
    ALLOWED_STATUSES,
    CONTACT_STATUSES,
    DEFAULT_PIPELINE_STAGES,
    UPDATE_CATEGORIES,
    build_target_draft,
    enrich_target_email,
    project_to_admin_dict,
    project_to_public_dict,
    recompute_project_rollup,
    target_can_send,
    target_to_admin_dict,
    unique_slug,
)

# ── Admin router ──────────────────────────────────────────────────────────────
admin_router = APIRouter(prefix="/special-projects", dependencies=[Depends(require_admin)])


class ProjectCreate(BaseModel):
    name: str
    company_website: Optional[str] = None
    contact_email: Optional[str] = None
    robot_description: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    metrics: Optional[dict[str, Any]] = None
    pipeline: Optional[dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    company_website: Optional[str] = None
    contact_email: Optional[str] = None
    robot_description: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    metrics: Optional[dict[str, Any]] = None
    pipeline: Optional[dict[str, Any]] = None


class UpdateCreate(BaseModel):
    title: str
    body: Optional[str] = None
    category: Optional[str] = None


class TargetCreate(BaseModel):
    company: str
    website: Optional[str] = None
    segment: Optional[str] = None
    best_fit_task: Optional[str] = None
    persona: Optional[str] = None
    sequence: Optional[str] = None
    fit: Optional[str] = None
    signal: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_title: Optional[str] = None
    notes: Optional[str] = None


class TargetPatch(BaseModel):
    company: Optional[str] = None
    website: Optional[str] = None
    segment: Optional[str] = None
    best_fit_task: Optional[str] = None
    persona: Optional[str] = None
    sequence: Optional[str] = None
    fit: Optional[str] = None
    signal: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_title: Optional[str] = None
    contact_status: Optional[str] = None
    draft_subject: Optional[str] = None
    draft_body: Optional[str] = None
    notes: Optional[str] = None


class StagePatch(BaseModel):
    stage: str


def _get_or_404(db: Session, project_id: str) -> SpecialProject:
    p = db.query(SpecialProject).filter(SpecialProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Special project not found")
    return p


@admin_router.get("")
def list_projects(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.query(SpecialProject).order_by(SpecialProject.created_at.desc()).all()
    return [project_to_admin_dict(p, include_updates=False) for p in rows]


@admin_router.post("")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    status = (payload.status or "discovery").strip().lower()
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(ALLOWED_STATUSES)}")
    project = SpecialProject(
        slug=unique_slug(db, payload.name),
        share_token=_new_share_token(),
        name=payload.name.strip(),
        company_website=payload.company_website,
        contact_email=payload.contact_email,
        robot_description=payload.robot_description,
        summary=payload.summary,
        status=status,
        config=payload.config or {},
        metrics=payload.metrics or {},
        pipeline=payload.pipeline or {},
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_to_admin_dict(project)


@admin_router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    return project_to_admin_dict(_get_or_404(db, project_id))


@admin_router.patch("/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = _get_or_404(db, project_id)
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"]:
        status = str(data["status"]).strip().lower()
        if status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail=f"status must be one of {sorted(ALLOWED_STATUSES)}")
        data["status"] = status
    for field, value in data.items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return project_to_admin_dict(p)


@admin_router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = _get_or_404(db, project_id)
    db.delete(p)
    db.commit()
    return {"status": "deleted", "id": project_id}


@admin_router.post("/{project_id}/rotate-token")
def rotate_token(project_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = _get_or_404(db, project_id)
    p.share_token = _new_share_token()
    db.commit()
    db.refresh(p)
    return {"share_token": p.share_token, "portal_path": f"/p/{p.share_token}"}


@admin_router.post("/{project_id}/updates")
def add_update(project_id: str, payload: UpdateCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = _get_or_404(db, project_id)
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="title is required")
    category = (payload.category or "note").strip().lower()
    if category not in UPDATE_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"category must be one of {sorted(UPDATE_CATEGORIES)}")
    upd = SpecialProjectUpdate(
        project_id=p.id,
        title=payload.title.strip(),
        body=payload.body,
        category=category,
    )
    db.add(upd)
    db.commit()
    db.refresh(p)
    return project_to_admin_dict(p)


@admin_router.delete("/{project_id}/updates/{update_id}")
def delete_update(project_id: str, update_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    upd = (
        db.query(SpecialProjectUpdate)
        .filter(SpecialProjectUpdate.id == update_id, SpecialProjectUpdate.project_id == project_id)
        .first()
    )
    if not upd:
        raise HTTPException(status_code=404, detail="Update not found")
    db.delete(upd)
    db.commit()
    return {"status": "deleted", "id": update_id}


# ── Target queue (Cal's review-first outreach pipeline) ─────────────────────────

def _get_target_or_404(db: Session, project_id: str, target_id: str) -> SpecialProjectTarget:
    t = (
        db.query(SpecialProjectTarget)
        .filter(
            SpecialProjectTarget.id == target_id,
            SpecialProjectTarget.project_id == project_id,
        )
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Target not found")
    return t


@admin_router.get("/{project_id}/targets")
def list_targets(project_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = _get_or_404(db, project_id)
    targets = sorted(p.targets or [], key=lambda t: (t.sort_order, t.company or ""))
    return {
        "project_id": p.id,
        "targets": [target_to_admin_dict(t) for t in targets],
        "pipeline": p.pipeline or {},
        "metrics": p.metrics or {},
    }


_CSV_FIELDS = [
    "company",
    "segment",
    "best_fit_task",
    "fit",
    "contact_name",
    "contact_title",
    "contact_email",
    "email_status",
    "stage",
    "date_contacted",
    "outreach_sequence",
    "why_now_signal",
    "website",
    "outreach_subject",
]
_FIT_LABEL = {"H": "Hot", "W": "Warm", "C": "Cold"}


@admin_router.get("/{project_id}/targets.csv")
def export_targets_csv(
    project_id: str, contacted: bool = False, db: Session = Depends(get_db)
) -> Response:
    """Download the target accounts as CSV (all, or only those Cal has contacted)."""
    p = _get_or_404(db, project_id)
    rows = sorted(p.targets or [], key=lambda t: t.sort_order)
    if contacted:
        rows = [t for t in rows if t.sent_at is not None]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CSV_FIELDS)
    writer.writeheader()
    for t in rows:
        writer.writerow(
            {
                "company": t.company or "",
                "segment": t.segment or "",
                "best_fit_task": t.best_fit_task or "",
                "fit": _FIT_LABEL.get(t.fit or "", t.fit or ""),
                "contact_name": t.contact_name or "",
                "contact_title": t.contact_title or "",
                "contact_email": t.contact_email or "",
                "email_status": t.contact_status or "",
                "stage": t.stage or "",
                "date_contacted": t.sent_at.strftime("%Y-%m-%d") if t.sent_at else "",
                "outreach_sequence": t.sequence or "",
                "why_now_signal": t.signal or "",
                "website": t.website or "",
                "outreach_subject": (t.draft_subject or "").strip(),
            }
        )
    filename = f"{p.slug}-leads-{datetime.now(timezone.utc):%Y-%m-%d}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_router.post("/{project_id}/targets")
def create_target(project_id: str, payload: TargetCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = _get_or_404(db, project_id)
    if not payload.company.strip():
        raise HTTPException(status_code=400, detail="company is required")
    max_order = max((t.sort_order for t in (p.targets or [])), default=0)
    t = SpecialProjectTarget(
        company=payload.company.strip(),
        website=payload.website,
        segment=payload.segment,
        best_fit_task=payload.best_fit_task,
        persona=payload.persona,
        sequence=(payload.sequence or "A").strip().upper()[:1],
        fit=(payload.fit or "").strip().upper()[:1] or None,
        signal=payload.signal,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        contact_title=payload.contact_title,
        contact_status="guessed" if (payload.contact_email or "").strip() else "none",
        notes=payload.notes,
        sort_order=max_order + 1,
    )
    subject, body = build_target_draft(p, t)
    t.draft_subject, t.draft_body = subject, body
    # Append to the loaded collection so the rollup below counts the new row.
    p.targets.append(t)
    db.flush()
    recompute_project_rollup(p)
    db.commit()
    db.refresh(t)
    return target_to_admin_dict(t)


@admin_router.patch("/{project_id}/targets/{target_id}")
def patch_target(
    project_id: str, target_id: str, payload: TargetPatch, db: Session = Depends(get_db)
) -> dict[str, Any]:
    t = _get_target_or_404(db, project_id, target_id)
    data = payload.model_dump(exclude_unset=True)
    if "contact_status" in data and data["contact_status"]:
        cs = str(data["contact_status"]).strip().lower()
        if cs not in CONTACT_STATUSES:
            raise HTTPException(status_code=400, detail=f"contact_status must be one of {sorted(CONTACT_STATUSES)}")
        data["contact_status"] = cs
    if "sequence" in data and data["sequence"]:
        data["sequence"] = str(data["sequence"]).strip().upper()[:1]
    for field, value in data.items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return target_to_admin_dict(t)


@admin_router.delete("/{project_id}/targets/{target_id}")
def delete_target(project_id: str, target_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = _get_or_404(db, project_id)
    t = _get_target_or_404(db, project_id, target_id)
    db.delete(t)
    db.flush()
    recompute_project_rollup(p)
    db.commit()
    return {"status": "deleted", "id": target_id}


@admin_router.post("/{project_id}/targets/regenerate-drafts")
def regenerate_drafts(project_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Rebuild drafts for every target that hasn't been sent yet (review-first)."""
    p = _get_or_404(db, project_id)
    regenerated = 0
    for t in p.targets or []:
        if t.sent_at is not None:
            continue
        subject, body = build_target_draft(p, t)
        t.draft_subject, t.draft_body = subject, body
        regenerated += 1
    db.commit()
    return {"status": "ok", "regenerated": regenerated}


@admin_router.post("/{project_id}/targets/enrich")
def enrich_targets(project_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Resolve verified contact emails for targets missing one (best-effort, Hunter)."""
    p = _get_or_404(db, project_id)
    enriched = 0
    attempted = 0
    for t in p.targets or []:
        if (t.contact_email or "").strip():
            continue
        attempted += 1
        if enrich_target_email(t):
            enriched += 1
    db.commit()
    return {"status": "ok", "attempted": attempted, "enriched": enriched}


@admin_router.post("/{project_id}/targets/{target_id}/approve")
def approve_target(project_id: str, target_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    t = _get_target_or_404(db, project_id, target_id)
    t.approved = "yes"
    db.commit()
    db.refresh(t)
    return target_to_admin_dict(t)


@admin_router.post("/{project_id}/targets/{target_id}/unapprove")
def unapprove_target(project_id: str, target_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    t = _get_target_or_404(db, project_id, target_id)
    t.approved = "no"
    db.commit()
    db.refresh(t)
    return target_to_admin_dict(t)


@admin_router.post("/{project_id}/targets/{target_id}/stage")
def set_target_stage(
    project_id: str, target_id: str, payload: StagePatch, db: Session = Depends(get_db)
) -> dict[str, Any]:
    p = _get_or_404(db, project_id)
    t = _get_target_or_404(db, project_id, target_id)
    stage = (payload.stage or "").strip().lower()
    if stage not in DEFAULT_PIPELINE_STAGES:
        raise HTTPException(status_code=400, detail=f"stage must be one of {DEFAULT_PIPELINE_STAGES}")
    t.stage = stage
    t.last_activity_at = datetime.now(timezone.utc)
    db.flush()
    recompute_project_rollup(p)
    db.commit()
    db.refresh(t)
    return target_to_admin_dict(t)


@admin_router.post("/{project_id}/targets/{target_id}/send")
def send_target(project_id: str, target_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Send an approved draft via Resend. Review-first: refuses unapproved targets."""
    p = _get_or_404(db, project_id)
    t = _get_target_or_404(db, project_id, target_id)
    if not target_can_send(t):
        raise HTTPException(
            status_code=400,
            detail="Target must be approved, have a contact email, and not already be sent.",
        )
    subject = (t.draft_subject or "").strip()
    body = (t.draft_body or "").strip()
    if not subject or not body:
        raise HTTPException(status_code=400, detail="Draft subject and body are required before sending.")

    try:
        from app.services.cal_email_send import send_cal_email_via_resend

        send_cal_email_via_resend(
            to_email=t.contact_email.strip(),
            subject=subject,
            body_text=body,
            reply_to=p.contact_email or None,
            idempotency_key=f"special-project/{p.id}/target/{t.id}",
            include_demo=False,
        )
    except Exception as exc:  # keep the queue usable even if send fails
        raise HTTPException(status_code=502, detail=f"Send failed: {exc}") from exc

    now = datetime.now(timezone.utc)
    t.sent_at = now
    t.last_activity_at = now
    if t.stage == "targeted":
        t.stage = "contacted"
    db.add(
        SpecialProjectUpdate(
            project_id=p.id,
            title=f"Cal contacted {t.company}",
            body=f"Sent outreach to {t.contact_email} — subject: “{subject}”.",
            category="outreach",
        )
    )
    db.flush()
    recompute_project_rollup(p)
    db.commit()
    db.refresh(t)
    return target_to_admin_dict(t)


# ── Public router (token-gated, no auth) ────────────────────────────────────────
public_router = APIRouter(prefix="/special-projects")


@public_router.get("/portal/{token}")
def client_portal(token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = db.query(SpecialProject).filter(SpecialProject.share_token == token).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portal not found")
    return project_to_public_dict(p)
