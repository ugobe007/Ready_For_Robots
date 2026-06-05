"""
HubSpot integration — OAuth connect, MCP bridge, outbound lead sync.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.api.marketplace import _default_team, _uid_uuid
from app.database import get_db
from app.services.hubspot_oauth import (
    HubSpotError,
    build_authorization_url,
    complete_oauth_callback,
    get_sync_settings,
    is_configured,
    update_sync_settings,
)
from app.services.integration_connections import (
    PROVIDER_HUBSPOT,
    _find_connection,
    resolve_hubspot_token,
    serialize_provider_status,
)
from app.services.plan_entitlements import PLAN_PAID, resolve_plan_tier

router = APIRouter(prefix="/integrations/hubspot", tags=["integrations"])


class HubSpotPushLeadIn(BaseModel):
    company_id: int = Field(..., ge=1)
    deal_name: Optional[str] = None


class HubSpotSyncSettingsIn(BaseModel):
    sync_mode: Literal["auto_all", "manual_select"] = "auto_all"
    sync_lead_ids: list[int] = Field(default_factory=list, max_length=200)


def _frontend_base() -> str:
    import os

    return (
        os.getenv("PUBLIC_SITE_URL")
        or os.getenv("NEXT_PUBLIC_SITE_URL")
        or "https://readyforrobots.com"
    ).rstrip("/")


@router.get("/setup")
def hubspot_setup(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Wizard state for /integrations/hubspot."""
    uid = _uid_uuid(user)
    team = _default_team(db, uid, user.get("email") or "")
    row = db.execute(
        text("SELECT display_name, email FROM user_profiles WHERE id = :uid"),
        {"uid": str(uid)},
    ).fetchone()
    sync = get_sync_settings(db, team_id=team.id)
    status = serialize_provider_status(PROVIDER_HUBSPOT, row=_find_connection(db, team.id, PROVIDER_HUBSPOT), entitled=True)
    saved = db.execute(
        text("""
            SELECT company_id, company_name, industry, tier
            FROM user_saved_companies
            WHERE user_id = :uid
            ORDER BY saved_at DESC
            LIMIT 100
        """),
        {"uid": str(uid)},
    ).fetchall()
    return {
        "oauth_configured": is_configured(),
        "profile_complete": bool((row.display_name or "").strip() if row else False),
        "display_name": (row.display_name if row else None),
        "email": (row.email if row else user.get("email")),
        "sync_entitled": resolve_plan_tier(user) == PLAN_PAID,
        "connection": status,
        "sync": sync,
        "saved_leads": [
            {
                "company_id": r.company_id,
                "company_name": r.company_name,
                "industry": r.industry,
                "tier": r.tier,
            }
            for r in saved
        ],
    }


@router.get("/connect-url")
def hubspot_connect_url(
    return_to: str = Query("/integrations/hubspot", description="Frontend path after OAuth"),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return HubSpot OAuth URL — SCOUT provisions MCP link after authorize."""
    if not is_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "code": "hubspot_oauth_not_configured",
                "message": "HubSpot OAuth is being enabled on the server. Try again shortly.",
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
    except HubSpotError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"auth_url": auth_url, "provider": "hubspot", "mode": "oauth"}


@router.get("/callback")
def hubspot_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """HubSpot OAuth redirect — stores token and MCP bridge for the workspace."""
    base = _frontend_base()
    if error:
        return RedirectResponse(
            url=f"{base}/integrations/hubspot?error={error}",
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(url=f"{base}/integrations/hubspot?error=missing_code", status_code=302)
    try:
        result = complete_oauth_callback(db, code=code, state=state)
    except HubSpotError as exc:
        from urllib.parse import quote

        return RedirectResponse(
            url=f"{base}/integrations/hubspot?error={quote(str(exc))}",
            status_code=302,
        )
    return_to = str(result.get("return_to") or "/integrations/hubspot")
    if not return_to.startswith("/"):
        return_to = "/integrations/hubspot"
    return RedirectResponse(url=f"{base}{return_to}?connected=1", status_code=302)


@router.get("/sync-settings")
def hubspot_get_sync_settings(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    return get_sync_settings(db, team_id=team.id)


@router.put("/sync-settings")
def hubspot_put_sync_settings(
    body: HubSpotSyncSettingsIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    try:
        return update_sync_settings(
            db,
            team_id=team.id,
            sync_mode=body.sync_mode,
            sync_lead_ids=body.sync_lead_ids,
        )
    except HubSpotError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status")
def hubspot_status(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    row = _find_connection(db, team.id, PROVIDER_HUBSPOT)
    sync_entitled = resolve_plan_tier(user) == PLAN_PAID
    status = serialize_provider_status(
        PROVIDER_HUBSPOT,
        row=row,
        entitled=True,
        entitlement_message=None if sync_entitled else "Upgrade to Pro for unlimited HubSpot auto-sync.",
    )
    configured = bool(resolve_hubspot_token(db, team_id=team.id))
    sync = get_sync_settings(db, team_id=team.id)
    status.update(
        {
            "configured": configured,
            "mode": "outbound_push",
            "sync_entitled": sync_entitled,
            "sync": sync,
            "message": (
                "HubSpot is connected for this workspace."
                if configured
                else "Connect HubSpot to push SCOUT-qualified leads automatically."
            ),
            "connect_url": "/integrations/hubspot",
        }
    )
    return status


@router.post("/push-lead")
def hubspot_push_lead(
    body: HubSpotPushLeadIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if resolve_plan_tier(user) != PLAN_PAID:
        raise HTTPException(
            status_code=403,
            detail={"code": "upgrade_required", "message": "HubSpot push sync requires Pro or Premium.", "upgrade_url": "/pricing"},
        )
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    token = resolve_hubspot_token(db, team_id=team.id)
    if not token:
        raise HTTPException(
            status_code=501,
            detail={
                "code": "hubspot_not_configured",
                "message": "Connect HubSpot first at /integrations/hubspot.",
                "connect_url": "/integrations/hubspot",
            },
        )
    raise HTTPException(
        status_code=501,
        detail={
            "code": "hubspot_push_pending",
            "message": "HubSpot push handler is stubbed — wire CRM create in phase 2.",
            "company_id": body.company_id,
        },
    )
