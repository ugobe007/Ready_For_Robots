"""HubSpot OAuth — automatic CRM link after SCOUT workspace signup."""
from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlencode
from uuid import UUID

import requests
from sqlalchemy.orm import Session

from app.services.integration_connections import (
    PROVIDER_HUBSPOT,
    connect_provider,
    _find_connection,
)
from app.services.pipeline_cache_store import cache_read, cache_write

logger = logging.getLogger(__name__)

HUBSPOT_OAUTH_STATE_KEY = "hubspot:oauth:state:"
HUBSPOT_AUTH_URL = "https://app.hubspot.com/oauth/authorize"
HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
HUBSPOT_SCOPES = "crm.objects.contacts.read crm.objects.contacts.write crm.objects.companies.write oauth"


class HubSpotError(Exception):
    """HubSpot OAuth or API failure."""


def client_id() -> str:
    return (os.getenv("HUBSPOT_CLIENT_ID") or "").strip()


def client_secret() -> str:
    return (os.getenv("HUBSPOT_CLIENT_SECRET") or "").strip()


def redirect_uri() -> str:
    explicit = (os.getenv("HUBSPOT_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit
    api_base = (
        os.getenv("PUBLIC_API_URL")
        or os.getenv("NEXT_PUBLIC_API_URL")
        or "https://ready-2-robot.fly.dev"
    ).rstrip("/")
    return f"{api_base}/api/integrations/hubspot/callback"


def mcp_server_url() -> str:
    return (os.getenv("R4R_MCP_BASE") or os.getenv("R4R_API_BASE") or "https://ready-2-robot.fly.dev").rstrip("/") + "/mcp/"


def is_configured() -> bool:
    return bool(client_id() and client_secret())


def build_authorization_url(
    db: Session,
    *,
    team_id: UUID,
    user_id: UUID,
    return_to: str = "",
) -> tuple[str, str]:
    if not is_configured():
        raise HubSpotError("HUBSPOT_CLIENT_ID and HUBSPOT_CLIENT_SECRET must be set on the API server")

    state = secrets.token_urlsafe(24)
    cache_write(
        db,
        f"{HUBSPOT_OAUTH_STATE_KEY}{state}",
        {
            "team_id": str(team_id),
            "user_id": str(user_id),
            "return_to": return_to[:500],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        ttl_minutes=15,
    )
    params = {
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "scope": HUBSPOT_SCOPES,
        "state": state,
    }
    return f"{HUBSPOT_AUTH_URL}?{urlencode(params)}", state


def _consume_oauth_state(db: Session, state: str) -> dict[str, Any]:
    payload = cache_read(db, f"{HUBSPOT_OAUTH_STATE_KEY}{state}", stale_ok=False)
    if not payload or not isinstance(payload, dict):
        raise HubSpotError("Invalid or expired OAuth state — restart HubSpot connect from SIGNAL")
    return payload


def _exchange_code(code: str) -> dict[str, Any]:
    resp = requests.post(
        HUBSPOT_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id(),
            "client_secret": client_secret(),
            "redirect_uri": redirect_uri(),
            "code": code,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise HubSpotError(f"HubSpot token exchange failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()


def _token_metadata(access_token: str) -> dict[str, Any]:
    resp = requests.get(
        f"https://api.hubapi.com/oauth/v1/access-tokens/{access_token}",
        timeout=20,
    )
    if resp.status_code >= 400:
        return {"verified": True}
    body = resp.json()
    return {
        "verified": True,
        "hub_id": body.get("hub_id"),
        "hub_domain": body.get("hub_domain"),
        "user": body.get("user"),
        "app_id": body.get("app_id"),
        "account_login": body.get("user") or body.get("hub_domain"),
        "account_name": body.get("hub_domain") or body.get("user"),
    }


def complete_oauth_callback(db: Session, *, code: str, state: str) -> dict[str, Any]:
    meta = _consume_oauth_state(db, state)
    team_id = UUID(str(meta["team_id"]))
    user_id = UUID(str(meta["user_id"]))
    token_body = _exchange_code(code)
    access_token = (token_body.get("access_token") or "").strip()
    if not access_token:
        raise HubSpotError("HubSpot did not return an access token")

    verified = _token_metadata(access_token)
    row = connect_provider(
        db,
        team_id=team_id,
        user_id=user_id,
        provider=PROVIDER_HUBSPOT,
        token=access_token,
    )
    cfg = dict(row.config or {})
    cfg.update(
        {
            "oauth": True,
            "refresh_token": token_body.get("refresh_token"),
            "expires_in": token_body.get("expires_in"),
            "mcp_server_url": mcp_server_url(),
            "sync_mode": cfg.get("sync_mode") or "auto_all",
            "sync_lead_ids": cfg.get("sync_lead_ids") or [],
            "verified": verified,
        }
    )
    row.config = cfg
    row.mcp_server_url = mcp_server_url()
    row.status = "active"
    db.commit()
    db.refresh(row)
    return {
        "connected": True,
        "return_to": meta.get("return_to") or "/integrations/hubspot",
        "hub_domain": verified.get("hub_domain"),
        "account_login": verified.get("account_login"),
    }


def get_sync_settings(db: Session, *, team_id: UUID) -> dict[str, Any]:
    row = _find_connection(db, team_id, PROVIDER_HUBSPOT)
    cfg = (row.config or {}) if row else {}
    return {
        "connected": bool(row and row.status == "active"),
        "sync_mode": cfg.get("sync_mode") or "auto_all",
        "sync_lead_ids": cfg.get("sync_lead_ids") or [],
        "mcp_server_url": row.mcp_server_url if row else mcp_server_url(),
    }


def update_sync_settings(
    db: Session,
    *,
    team_id: UUID,
    sync_mode: str,
    sync_lead_ids: list[int],
) -> dict[str, Any]:
    row = _find_connection(db, team_id, PROVIDER_HUBSPOT)
    if not row or row.status != "active":
        raise HubSpotError("Connect HubSpot before choosing sync settings")
    mode = sync_mode if sync_mode in ("auto_all", "manual_select") else "auto_all"
    cfg = dict(row.config or {})
    cfg["sync_mode"] = mode
    cfg["sync_lead_ids"] = sync_lead_ids[:200]
    row.config = cfg
    db.commit()
    return get_sync_settings(db, team_id=team_id)
