"""CRM jobs-watch opt-in. Prefix: /api/crm (mounted in main)."""
from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.database import get_db
from app.models.jobs_watch import JobsWatch
from app.services.jobs_watch import upsert_watch, watch_status
from app.services.robot_url_safety import UrlSafetyError

logger = logging.getLogger(__name__)

router = APIRouter()


class JobsWatchUpdate(BaseModel):
    opted_in: bool = True
    robot_url: Optional[str] = Field(default=None, max_length=2000)
    product_name: Optional[str] = Field(default=None, max_length=240)
    seed_jobs: Optional[list[dict[str, Any]]] = None


def _watches_for_user(db: Session, uid: UUID) -> list[JobsWatch]:
    return (
        db.query(JobsWatch)
        .filter(JobsWatch.user_id == uid)
        .order_by(JobsWatch.created_at.asc())
        .all()
    )


@router.get("/jobs-watch")
def get_jobs_watch(user: dict = Depends(_require_user), db: Session = Depends(get_db)):
    uid = UUID(str(user["uid"]))
    return watch_status(db, user, _watches_for_user(db, uid))


@router.put("/jobs-watch")
def put_jobs_watch(
    body: JobsWatchUpdate,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    uid = UUID(str(user["uid"]))
    watches = _watches_for_user(db, uid)
    url = (body.robot_url or "").strip()
    if not url:
        primary = next((w for w in watches if w.opted_in), watches[0] if watches else None)
        url = (primary.robot_url if primary else "") or ""
    if body.opted_in and not url:
        raise HTTPException(
            status_code=400,
            detail="Paste a robot URL on Jobs first, then opt in so we can watch it.",
        )
    if not body.opted_in:
        for watch in watches:
            watch.opted_in = False
        db.commit()
        return watch_status(db, user, _watches_for_user(db, uid))
    try:
        upsert_watch(
            db,
            user=user,
            robot_url=url,
            product_name=body.product_name,
            seed_jobs=body.seed_jobs or [],
            opted_in=True,
        )
    except UrlSafetyError as exc:
        raise HTTPException(status_code=400, detail=str(exc) or "Need a public robot URL.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception:
        logger.exception("jobs_watch_upsert_failed")
        raise HTTPException(status_code=500, detail="Could not start the job watch.")
    return watch_status(db, user, _watches_for_user(db, uid))
