"""
HubSpot integration — outbound lead sync (roadmap).

Phase 1: push SCOUT-qualified leads to HubSpot contacts/companies with custom properties.
Requires HUBSPOT_PRIVATE_APP_TOKEN on the server.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.api.marketplace import _default_team, _uid_uuid
from app.database import get_db
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


@router.get("/status")
def hubspot_status(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    row = _find_connection(db, team.id, PROVIDER_HUBSPOT)
    entitled = resolve_plan_tier(user) == PLAN_PAID
    status = serialize_provider_status(
        PROVIDER_HUBSPOT,
        row=row,
        entitled=entitled,
        entitlement_message=None if entitled else "Upgrade to Pro or Premium to connect HubSpot.",
    )
    configured = bool(resolve_hubspot_token(db, team_id=team.id))
    status.update(
        {
            "configured": configured,
            "mode": "outbound_push",
            "message": (
                "HubSpot is connected for this workspace."
                if configured
                else "Connect HubSpot on the Integrations page to push SCOUT-qualified leads."
            ),
            "connect_url": "/integrations",
        }
    )
    return status


@router.post("/push-lead")
def hubspot_push_lead(
    body: HubSpotPushLeadIn,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    team = _default_team(db, _uid_uuid(user), user.get("email") or "")
    token = resolve_hubspot_token(db, team_id=team.id)
    if not token:
        raise HTTPException(
            status_code=501,
            detail={
                "code": "hubspot_not_configured",
                "message": "HubSpot outbound sync is on the roadmap. Token not configured on server.",
                "upgrade_url": "/pricing",
            },
        )
    # Phase 2: map company + SCOUT fields → HubSpot company/contact/deal create API.
    raise HTTPException(
        status_code=501,
        detail={
            "code": "hubspot_push_pending",
            "message": "HubSpot push handler is stubbed — wire CRM create in phase 2.",
            "company_id": body.company_id,
        },
    )
