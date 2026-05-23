"""Admin dashboard snapshot API — instant cached payload + sequential section refresh."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.auth_deps import require_admin
from app.database import get_db
from app.services.admin_snapshot import (
    SECTION_NAMES,
    get_section_payload,
    get_snapshot,
    schedule_background_rebuild,
    snapshot_meta,
)

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/snapshot")
def admin_snapshot(response: Response):
    """
    Return the full persisted admin snapshot (DB cache).
    Always serves stale data when available — never blocks on rebuild.
    """
    payload = get_snapshot(stale_ok=True)
    sections = payload.get("sections") or {}
    if not sections:
        schedule_background_rebuild(["daily_brief", "cal", "stats"])
    response.headers["Cache-Control"] = "private, max-age=0"
    return payload


@router.get("/snapshot/meta")
def admin_snapshot_meta():
    """Lightweight section timestamps for delta refresh."""
    return snapshot_meta()


@router.get("/snapshot/section/{section}")
def admin_snapshot_section(
    section: str,
    response: Response,
    since: Optional[str] = Query(None, description="ISO timestamp — 304 if section unchanged"),
    refresh: bool = Query(False, description="Force rebuild this section (use one at a time)"),
    analytics_range: str = Query("30d", pattern="^(7d|30d|90d|all)$"),
    db: Session = Depends(get_db),
):
    """Return one snapshot section. Client should call sections sequentially, not in parallel."""
    status, body = get_section_payload(
        section,
        since=since,
        refresh=refresh,
        db=db,
        analytics_range=analytics_range,
    )
    if status == 304:
        return Response(status_code=304)
    response.status_code = status
    return body


@router.get("/snapshot/sections")
def admin_snapshot_section_list():
    return {"sections": list(SECTION_NAMES)}
