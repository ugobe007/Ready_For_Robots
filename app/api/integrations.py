"""Workspace integrations — HubSpot, GitHub, and future CRM/dev connectors."""
from __future__ import annotations

from typing import Any, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.api.marketplace import _default_team, _uid_uuid
from app.database import get_db
from app.services.integration_connections import (
    PROVIDER_GITHUB,
    PROVIDER_HUBSPOT,
    IntegrationError,
    connect_provider,
    disconnect_provider,
    serialize_provider_status,
    _find_connection,
)
from app.services.plan_entitlements import PLAN_PAID, resolve_plan_tier

router = APIRouter(prefix="/integrations", tags=["integrations"])

ProviderSlug = Literal["hubspot", "github"]
SUPPORTED_PROVIDERS = (PROVIDER_HUBSPOT, PROVIDER_GITHUB)


class ConnectIntegrationIn(BaseModel):
    token: str = Field(..., min_length=8, max_length=512)


def _hubspot_entitled(user: dict) -> tuple[bool, Optional[str]]:
    """HubSpot OAuth connect is available to all signed-in workspaces; bulk sync is Pro+."""
    plan = resolve_plan_tier(user)
    if plan == PLAN_PAID:
        return True, None
    return True, "Connect free — auto-sync all saved leads requires Pro or Premium."


@router.get("")
def list_integrations(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    hubspot_ok, hubspot_msg = _hubspot_entitled(user)
    integrations = []
    for provider in SUPPORTED_PROVIDERS:
        row = _find_connection(db, team.id, provider)
        entitled = True
        msg = None
        if provider == PROVIDER_HUBSPOT:
            entitled, msg = hubspot_ok, hubspot_msg
        integrations.append(
            serialize_provider_status(
                provider,
                row=row,
                entitled=entitled,
                entitlement_message=msg,
            )
        )
    return {
        "integrations": integrations,
        "workspace_id": str(team.id),
    }


@router.post("/{provider}/connect")
def connect_integration(
    provider: ProviderSlug,
    body: ConnectIntegrationIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if provider == PROVIDER_HUBSPOT:
        entitled, msg = _hubspot_entitled(user)
        if not entitled:
            raise HTTPException(
                status_code=403,
                detail={"code": "upgrade_required", "message": msg, "upgrade_url": "/pricing"},
            )
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    try:
        row = connect_provider(
            db,
            team_id=team.id,
            user_id=_uid_uuid(user),
            provider=provider,
            token=body.token,
        )
    except IntegrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    entitled = True
    entitlement_message = None
    if provider == PROVIDER_HUBSPOT:
        entitled, entitlement_message = _hubspot_entitled(user)
    return serialize_provider_status(
        provider,
        row=row,
        entitled=entitled,
        entitlement_message=entitlement_message,
    )


@router.delete("/{provider}/disconnect")
def disconnect_integration(
    provider: ProviderSlug,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    disconnect_provider(db, team_id=team.id, provider=provider)
    entitled = True
    entitlement_message = None
    if provider == PROVIDER_HUBSPOT:
        entitled, entitlement_message = _hubspot_entitled(user)
    return serialize_provider_status(
        provider,
        row=None,
        entitled=entitled,
        entitlement_message=entitlement_message,
    )
