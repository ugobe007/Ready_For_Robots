"""
LinkedIn OAuth + company page publishing for Ready For Robots.

Organization page: urn:li:organization:114404417
Docs: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
"""
from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlencode

import requests
from sqlalchemy.orm import Session

from app.services.pipeline_cache_store import cache_read, cache_write

logger = logging.getLogger(__name__)

LINKEDIN_TOKEN_CACHE_KEY = "linkedin:oauth:v1"
LINKEDIN_OAUTH_STATE_KEY = "linkedin:oauth:state:"
DEFAULT_ORG_ID = "114404417"
DEFAULT_ORG_URN = f"urn:li:organization:{DEFAULT_ORG_ID}"

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"

DEFAULT_SCOPES = "w_organization_social r_organization_social openid profile email"


class LinkedInError(Exception):
    """LinkedIn API or OAuth failure."""


def organization_id() -> str:
    return (os.getenv("LINKEDIN_ORGANIZATION_ID") or DEFAULT_ORG_ID).strip()


def organization_urn() -> str:
    oid = organization_id()
    return f"urn:li:organization:{oid}"


def api_version() -> str:
    return (os.getenv("LINKEDIN_API_VERSION") or "202505").strip()


def client_id() -> str:
    return (os.getenv("LINKEDIN_CLIENT_ID") or "").strip()


def client_secret() -> str:
    return (os.getenv("LINKEDIN_CLIENT_SECRET") or "").strip()


def redirect_uri() -> str:
    explicit = (os.getenv("LINKEDIN_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit
    api_base = (os.getenv("PUBLIC_API_URL") or os.getenv("NEXT_PUBLIC_API_URL") or "https://ready-2-robot.fly.dev").rstrip("/")
    return f"{api_base}/api/linkedin/callback"


def is_configured() -> bool:
    return bool(client_id() and client_secret())


def _load_tokens(db: Session) -> Optional[dict[str, Any]]:
    manual = (os.getenv("LINKEDIN_ACCESS_TOKEN") or "").strip()
    if manual:
        return {
            "access_token": manual,
            "refresh_token": (os.getenv("LINKEDIN_REFRESH_TOKEN") or "").strip() or None,
            "expires_at": None,
            "organization_id": organization_id(),
            "source": "env",
        }
    data = cache_read(db, LINKEDIN_TOKEN_CACHE_KEY, stale_ok=True)
    return data if isinstance(data, dict) and data.get("access_token") else None


def _save_tokens(db: Session, payload: dict[str, Any]) -> None:
    cache_write(db, LINKEDIN_TOKEN_CACHE_KEY, payload, ttl_minutes=60 * 24 * 90)


def connection_status(db: Session) -> dict[str, Any]:
    tokens = _load_tokens(db)
    org = organization_id()
    return {
        "configured": is_configured(),
        "connected": bool(tokens and tokens.get("access_token")),
        "organization_id": org,
        "organization_urn": organization_urn(),
        "organization_url": f"https://www.linkedin.com/company/{org}/admin/dashboard/",
        "redirect_uri": redirect_uri(),
        "scopes": DEFAULT_SCOPES,
        "source": (tokens or {}).get("source"),
        "connected_at": (tokens or {}).get("connected_at"),
        "expires_at": (tokens or {}).get("expires_at"),
    }


def build_authorization_url(db: Session, *, return_to: str = "") -> tuple[str, str]:
    if not is_configured():
        raise LinkedInError("LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be set")

    state = secrets.token_urlsafe(24)
    cache_write(
        db,
        f"{LINKEDIN_OAUTH_STATE_KEY}{state}",
        {"return_to": return_to[:500], "created_at": datetime.now(timezone.utc).isoformat()},
        ttl_minutes=15,
    )

    params = {
        "response_type": "code",
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "state": state,
        "scope": DEFAULT_SCOPES,
    }
    return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}", state


def _consume_oauth_state(db: Session, state: str) -> dict[str, Any]:
    key = f"{LINKEDIN_OAUTH_STATE_KEY}{state}"
    payload = cache_read(db, key, stale_ok=False)
    if not payload:
        raise LinkedInError("Invalid or expired OAuth state — restart connect from Content Studio")
    return payload if isinstance(payload, dict) else {}


def _exchange_code(code: str) -> dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri(),
        "client_id": client_id(),
        "client_secret": client_secret(),
    }
    resp = requests.post(
        LINKEDIN_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise LinkedInError(f"Token exchange failed ({resp.status_code}): {resp.text[:300]}")
    body = resp.json()
    expires_in = int(body.get("expires_in") or 3600)
    return {
        "access_token": body["access_token"],
        "refresh_token": body.get("refresh_token"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat(),
        "organization_id": organization_id(),
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "source": "oauth",
    }


def _refresh_access_token(refresh_token: str) -> dict[str, Any]:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id(),
        "client_secret": client_secret(),
    }
    resp = requests.post(
        LINKEDIN_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise LinkedInError(f"Token refresh failed ({resp.status_code}): {resp.text[:300]}")
    body = resp.json()
    expires_in = int(body.get("expires_in") or 3600)
    return {
        "access_token": body["access_token"],
        "refresh_token": body.get("refresh_token") or refresh_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat(),
    }


def _access_token(db: Session) -> str:
    tokens = _load_tokens(db)
    if not tokens or not tokens.get("access_token"):
        raise LinkedInError("LinkedIn is not connected — authorize the Ready For Robots company page first")

    if tokens.get("source") == "env":
        return tokens["access_token"]

    expires_at = tokens.get("expires_at")
    refresh = tokens.get("refresh_token")
    if expires_at and refresh:
        try:
            exp = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            if datetime.now(timezone.utc) >= exp - timedelta(minutes=5):
                refreshed = _refresh_access_token(refresh)
                tokens.update(refreshed)
                tokens["organization_id"] = organization_id()
                tokens["source"] = "oauth"
                _save_tokens(db, tokens)
        except Exception as exc:
            logger.warning("LinkedIn token refresh failed: %s", exc)

    return tokens["access_token"]


def complete_oauth_callback(db: Session, *, code: str, state: str) -> dict[str, Any]:
    state_payload = _consume_oauth_state(db, state)
    tokens = _exchange_code(code)
    _save_tokens(db, tokens)
    return {
        "connected": True,
        "return_to": state_payload.get("return_to") or "",
        "organization_id": organization_id(),
    }


def publish_organization_post(db: Session, *, commentary: str, article_url: Optional[str] = None) -> dict[str, Any]:
    text = (commentary or "").strip()
    if not text:
        raise LinkedInError("Post text is required")
    if len(text) > 3000:
        raise LinkedInError("LinkedIn post text must be 3000 characters or fewer")

    token = _access_token(db)
    payload: dict[str, Any] = {
        "author": organization_urn(),
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if article_url:
        payload["content"] = {
            "article": {
                "source": article_url,
                "title": "Ready For Robots",
            }
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Linkedin-Version": api_version(),
        "X-Restli-Protocol-Version": "2.0.0",
    }

    resp = requests.post(
        LINKEDIN_POSTS_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if resp.status_code >= 400:
        raise LinkedInError(f"LinkedIn publish failed ({resp.status_code}): {resp.text[:500]}")

    post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id")
    return {
        "ok": True,
        "post_id": post_id,
        "organization_id": organization_id(),
        "char_count": len(text),
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
