"""Google Calendar OAuth — sync operator meetings to Google Calendar."""
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

from app.services.integration_connections import PROVIDER_GOOGLE_CALENDAR, connect_provider, _find_connection
from app.services.integration_tokens import decrypt_token, encrypt_token
from app.services.pipeline_cache_store import cache_read, cache_write

logger = logging.getLogger(__name__)

GOOGLE_OAUTH_STATE_KEY = "google_calendar:oauth:state:"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
# calendar.events covers create/list on primary; calendarList needs calendar.readonly (avoid extra scope).
GOOGLE_SCOPES = "https://www.googleapis.com/auth/calendar.events"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarError(Exception):
    """Google Calendar OAuth or API failure."""


def client_id() -> str:
    return (os.getenv("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_OAUTH_CLIENT_ID") or "").strip()


def client_secret() -> str:
    return (os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_OAUTH_CLIENT_SECRET") or "").strip()


def redirect_uri() -> str:
    explicit = (os.getenv("GOOGLE_CALENDAR_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit
    api_base = (
        os.getenv("PUBLIC_API_URL")
        or os.getenv("NEXT_PUBLIC_API_URL")
        or "https://ready-2-robot.fly.dev"
    ).rstrip("/")
    return f"{api_base}/api/integrations/google-calendar/callback"


def is_configured() -> bool:
    return bool(client_id() and client_secret())


def _normalize_frontend_origin(origin: str) -> str:
    raw = (origin or "").strip().rstrip("/")
    if not raw:
        return ""
    allowed = {
        "https://readyforrobots.com",
        "https://www.readyforrobots.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    if raw in allowed or raw.endswith(".readyforrobots.com"):
        return raw
    return ""


def build_authorization_url(
    db: Session,
    *,
    team_id: UUID,
    user_id: UUID,
    return_to: str = "",
    frontend_origin: str = "",
) -> tuple[str, str]:
    if not is_configured():
        raise GoogleCalendarError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set on the API server")

    state = secrets.token_urlsafe(24)
    cache_write(
        db,
        f"{GOOGLE_OAUTH_STATE_KEY}{state}",
        {
            "team_id": str(team_id),
            "user_id": str(user_id),
            "return_to": return_to[:500],
            "frontend_origin": _normalize_frontend_origin(frontend_origin)[:500],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        ttl_minutes=15,
    )
    params = {
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}", state


def _consume_oauth_state(db: Session, state: str) -> dict[str, Any]:
    payload = cache_read(db, f"{GOOGLE_OAUTH_STATE_KEY}{state}", stale_ok=False)
    if not payload or not isinstance(payload, dict):
        raise GoogleCalendarError("Invalid or expired OAuth state — restart Google Calendar connect")
    return payload


def _exchange_code(code: str) -> dict[str, Any]:
    resp = requests.post(
        GOOGLE_TOKEN_URL,
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
        raise GoogleCalendarError(f"Google token exchange failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()


def verify_google_calendar_access_token(access_token: str) -> dict[str, Any]:
    """Verify token using primary events list (works with calendar.events scope)."""
    resp = requests.get(
        f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"maxResults": 1},
        timeout=20,
    )
    if resp.status_code == 401:
        raise GoogleCalendarError("Google Calendar token rejected — reconnect Google.")
    if resp.status_code >= 400:
        raise GoogleCalendarError(
            f"Google Calendar verification failed ({resp.status_code}): {resp.text[:200]}"
        )
    return {"verified": True, "account_name": "Google Calendar"}


def _verify_access_token(access_token: str) -> dict[str, Any]:
    return verify_google_calendar_access_token(access_token)


def complete_oauth_callback(db: Session, *, code: str, state: str) -> dict[str, Any]:
    meta = _consume_oauth_state(db, state)
    team_id = UUID(str(meta["team_id"]))
    user_id = UUID(str(meta["user_id"]))
    token_body = _exchange_code(code)
    access_token = (token_body.get("access_token") or "").strip()
    if not access_token:
        raise GoogleCalendarError("Google did not return an access token")

    verified = _verify_access_token(access_token)
    row = connect_provider(
        db,
        team_id=team_id,
        user_id=user_id,
        provider=PROVIDER_GOOGLE_CALENDAR,
        token=access_token,
    )
    cfg = dict(row.config or {})
    refresh_token = token_body.get("refresh_token")
    cfg.update(
        {
            "oauth": True,
            "refresh_token_ciphertext": encrypt_token(refresh_token) if refresh_token else cfg.get("refresh_token_ciphertext"),
            "expires_at": (
                datetime.now(timezone.utc).timestamp() + float(token_body.get("expires_in") or 3600)
            ),
            "verified": verified,
        }
    )
    row.config = cfg
    row.status = "active"
    db.commit()
    db.refresh(row)
    return {
        "connected": True,
        "return_to": meta.get("return_to") or "/calendar",
        "frontend_origin": meta.get("frontend_origin") or "",
        "account_name": verified.get("account_name"),
    }


def resolve_google_calendar_token(db: Session, *, team_id: UUID) -> Optional[str]:
    from app.services.google_calendar_sync import get_valid_access_token

    try:
        return get_valid_access_token(db, team_id=team_id)
    except GoogleCalendarError:
        return None


def connection_status(db: Session, *, team_id: UUID) -> dict[str, Any]:
    row = _find_connection(db, team_id, PROVIDER_GOOGLE_CALENDAR)
    cfg = (row.config or {}) if row else {}
    verified = cfg.get("verified") or {}
    return {
        "connected": bool(row and row.status == "active"),
        "configured": is_configured(),
        "account_name": verified.get("account_name"),
        "connected_at": cfg.get("connected_at"),
    }
