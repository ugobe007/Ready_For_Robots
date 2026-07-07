"""Serialization + helpers for special projects (admin workflow + client portal)."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.special_project import SpecialProject, SpecialProjectUpdate

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

ALLOWED_STATUSES = {"discovery", "outreach", "piloting", "active", "paused", "archived"}
UPDATE_CATEGORIES = {"milestone", "stat", "note", "outreach"}


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
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "updates": [_update_to_dict(u) for u in (p.updates or [])],
    }
