"""Special projects — private admin GTM workflow + token-gated client portal.

Admin (auth required):  /api/admin/special-projects/...
Public (share token):   /api/special-projects/portal/{token}
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth_deps import require_admin
from app.database import get_db
from app.models.special_project import SpecialProject, SpecialProjectUpdate, _new_share_token
from app.services.special_projects import (
    ALLOWED_STATUSES,
    UPDATE_CATEGORIES,
    project_to_admin_dict,
    project_to_public_dict,
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


# ── Public router (token-gated, no auth) ────────────────────────────────────────
public_router = APIRouter(prefix="/special-projects")


@public_router.get("/portal/{token}")
def client_portal(token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    p = db.query(SpecialProject).filter(SpecialProject.share_token == token).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portal not found")
    return project_to_public_dict(p)
