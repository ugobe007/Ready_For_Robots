"""Google Calendar integration — OAuth connect and status."""
from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.api.marketplace import _default_team, _uid_uuid
from app.database import get_db
from app.services.google_calendar_oauth import (
    GoogleCalendarError,
    build_authorization_url,
    complete_oauth_callback,
    connection_status,
    is_configured,
    redirect_uri,
)
from app.services.integration_connections import PROVIDER_GOOGLE_CALENDAR, disconnect_provider, serialize_provider_status, _find_connection

router = APIRouter(prefix="/integrations/google-calendar", tags=["integrations"])


def _frontend_base() -> str:
    import os

    return (
        os.getenv("PUBLIC_SITE_URL")
        or os.getenv("NEXT_PUBLIC_SITE_URL")
        or "https://readyforrobots.com"
    ).rstrip("/")


@router.get("/status")
def google_calendar_status(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    row = _find_connection(db, team.id, PROVIDER_GOOGLE_CALENDAR)
    status = serialize_provider_status(PROVIDER_GOOGLE_CALENDAR, row=row, entitled=True)
    status.update(connection_status(db, team_id=team.id))
    status["configured"] = is_configured()
    return status


@router.get("/connect-url")
def google_calendar_connect_url(
    return_to: str = Query("/calendar", description="Frontend path after OAuth"),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not is_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "code": "google_calendar_not_configured",
                "message": "Google Calendar OAuth is not configured on the server yet.",
            },
        )
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    try:
        auth_url, _ = build_authorization_url(
            db,
            team_id=team.id,
            user_id=_uid_uuid(user),
            return_to=return_to,
        )
    except GoogleCalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"auth_url": auth_url, "provider": "google_calendar", "mode": "oauth", "redirect_uri": redirect_uri()}


@router.get("/callback")
def google_calendar_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    base = _frontend_base()
    if error:
        return RedirectResponse(url=f"{base}/calendar?error={error}", status_code=302)
    if not code or not state:
        return RedirectResponse(url=f"{base}/calendar?error=missing_code", status_code=302)
    try:
        result = complete_oauth_callback(db, code=code, state=state)
    except GoogleCalendarError as exc:
        return RedirectResponse(url=f"{base}/calendar?error={quote(str(exc))}", status_code=302)
    return_to = str(result.get("return_to") or "/calendar")
    if not return_to.startswith("/"):
        return_to = "/calendar"
    return RedirectResponse(url=f"{base}{return_to}?connected=google_calendar", status_code=302)


@router.delete("/disconnect")
def google_calendar_disconnect(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    disconnect_provider(db, team_id=team.id, provider=PROVIDER_GOOGLE_CALENDAR)
    return {"connected": False, "provider": PROVIDER_GOOGLE_CALENDAR}
