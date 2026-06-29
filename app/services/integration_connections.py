"""Per-workspace CRM and developer integrations (HubSpot, GitHub)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import requests
from sqlalchemy.orm import Session

from app.models.marketplace import MarketplaceIntegrationConnection
from app.services.integration_tokens import decrypt_token, encrypt_token

PROVIDER_HUBSPOT = "hubspot"
PROVIDER_GITHUB = "github"
PROVIDER_GOOGLE_CALENDAR = "google_calendar"

_PROVIDER_META: dict[str, dict[str, Any]] = {
    PROVIDER_HUBSPOT: {
        "name": "HubSpot",
        "connection_type": "crm",
        "auth_type": "private_app_token",
        "description": "Push SIGNAL-qualified leads into HubSpot contacts and companies.",
        "docs_url": "https://developers.hubspot.com/docs/api/private-apps",
        "scopes_hint": "crm.objects.contacts.read, crm.objects.contacts.write, crm.objects.companies.write",
    },
    PROVIDER_GITHUB: {
        "name": "GitHub",
        "connection_type": "vendor_api",
        "auth_type": "personal_access_token",
        "description": "Let SIGNAL read repos and automation context from your GitHub workspace.",
        "docs_url": "https://github.com/settings/tokens",
        "scopes_hint": "repo, read:org (fine-grained or classic PAT)",
    },
    PROVIDER_GOOGLE_CALENDAR: {
        "name": "Google Calendar",
        "connection_type": "calendar",
        "auth_type": "oauth",
        "description": "Sync operator meetings to Google Calendar and send invites from your calendar.",
        "docs_url": "https://developers.google.com/calendar/api/guides/overview",
        "scopes_hint": "calendar.events",
    },
}


class IntegrationError(Exception):
    """Integration connect/verify failure."""


def _provider_meta(provider: str) -> dict[str, Any]:
    meta = _PROVIDER_META.get(provider)
    if not meta:
        raise IntegrationError(f"Unknown provider: {provider}")
    return meta


def _find_connection(db: Session, team_id: UUID, provider: str) -> Optional[MarketplaceIntegrationConnection]:
    rows = (
        db.query(MarketplaceIntegrationConnection)
        .filter(MarketplaceIntegrationConnection.team_id == team_id)
        .order_by(MarketplaceIntegrationConnection.updated_at.desc())
        .all()
    )
    for row in rows:
        cfg = row.config or {}
        if cfg.get("provider") == provider:
            return row
    return None


def _verify_hubspot(token: str) -> dict[str, Any]:
    response = requests.get(
        "https://api.hubapi.com/crm/v3/objects/contacts",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1},
        timeout=20,
    )
    if response.status_code == 401:
        raise IntegrationError("HubSpot token rejected — check scopes and expiration.")
    if response.status_code >= 400:
        raise IntegrationError(f"HubSpot verification failed ({response.status_code}).")
    return {"verified": True}


def _verify_github(token: str) -> dict[str, Any]:
    response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=20,
    )
    if response.status_code == 401:
        raise IntegrationError("GitHub token rejected — check scopes and expiration.")
    if response.status_code >= 400:
        raise IntegrationError(f"GitHub verification failed ({response.status_code}).")
    data = response.json()
    return {
        "verified": True,
        "account_login": data.get("login"),
        "account_name": data.get("name") or data.get("login"),
        "account_type": data.get("type"),
    }


def _verify_google_calendar(token: str) -> dict[str, Any]:
    response = requests.get(
        "https://www.googleapis.com/calendar/v3/users/me/calendarList",
        headers={"Authorization": f"Bearer {token}"},
        params={"maxResults": 1},
        timeout=20,
    )
    if response.status_code == 401:
        raise IntegrationError("Google Calendar token rejected — reconnect Google.")
    if response.status_code >= 400:
        raise IntegrationError(f"Google Calendar verification failed ({response.status_code}).")
    return {"verified": True, "account_name": "Google Calendar"}


def verify_provider_token(provider: str, token: str) -> dict[str, Any]:
    token = (token or "").strip()
    if not token:
        raise IntegrationError("Token is required.")
    if provider == PROVIDER_HUBSPOT:
        return _verify_hubspot(token)
    if provider == PROVIDER_GITHUB:
        return _verify_github(token)
    if provider == PROVIDER_GOOGLE_CALENDAR:
        return _verify_google_calendar(token)
    raise IntegrationError(f"Unknown provider: {provider}")


def connect_provider(
    db: Session,
    *,
    team_id: UUID,
    user_id: UUID,
    provider: str,
    token: str,
) -> MarketplaceIntegrationConnection:
    meta = _provider_meta(provider)
    verified = verify_provider_token(provider, token)
    now = datetime.now(timezone.utc)
    row = _find_connection(db, team_id, provider)
    config: dict[str, Any] = {
        "provider": provider,
        "token_ciphertext": encrypt_token(token),
        "connected_at": now.isoformat(),
        "verified": verified,
    }
    if row:
        row.status = "active"
        row.auth_type = meta["auth_type"]
        row.connection_type = meta["connection_type"]
        row.name = meta["name"]
        row.config = config
        row.last_checked_at = now
        row.updated_at = now
    else:
        row = MarketplaceIntegrationConnection(
            team_id=team_id,
            created_by_user_id=user_id,
            connection_type=meta["connection_type"],
            name=meta["name"],
            status="active",
            auth_type=meta["auth_type"],
            config=config,
            last_checked_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def disconnect_provider(db: Session, *, team_id: UUID, provider: str) -> bool:
    row = _find_connection(db, team_id, provider)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def get_provider_token(db: Session, *, team_id: UUID, provider: str) -> Optional[str]:
    row = _find_connection(db, team_id, provider)
    if not row or row.status != "active":
        return None
    cfg = row.config or {}
    ciphertext = cfg.get("token_ciphertext")
    if not ciphertext:
        return None
    try:
        return decrypt_token(str(ciphertext))
    except Exception:
        return None


def resolve_hubspot_token(db: Session, *, team_id: UUID) -> Optional[str]:
    token = get_provider_token(db, team_id=team_id, provider=PROVIDER_HUBSPOT)
    if token:
        return token
    return (os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or "").strip() or None


def resolve_google_calendar_token(db: Session, *, team_id: UUID) -> Optional[str]:
    try:
        from app.services.google_calendar_sync import get_valid_access_token

        return get_valid_access_token(db, team_id=team_id)
    except Exception:
        return None


def serialize_provider_status(
    provider: str,
    *,
    row: Optional[MarketplaceIntegrationConnection],
    entitled: bool = True,
    entitlement_message: Optional[str] = None,
) -> dict[str, Any]:
    meta = _provider_meta(provider)
    connected = bool(row and row.status == "active")
    cfg = (row.config or {}) if row else {}
    verified = cfg.get("verified") or {}
    return {
        "provider": provider,
        "name": meta["name"],
        "description": meta["description"],
        "docs_url": meta["docs_url"],
        "scopes_hint": meta["scopes_hint"],
        "connected": connected,
        "status": "connected" if connected else "not_connected",
        "connected_at": cfg.get("connected_at"),
        "account_login": verified.get("account_login"),
        "account_name": verified.get("account_name"),
        "entitled": entitled,
        "entitlement_message": entitlement_message,
        "connection_id": str(row.id) if row else None,
    }
