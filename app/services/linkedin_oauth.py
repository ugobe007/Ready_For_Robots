"""
LinkedIn OAuth + publishing for Ready For Robots.

Modes (LINKEDIN_POST_MODE):
  member       — Share on LinkedIn product (w_member_social). Posts to the authorizing
                 member's personal feed. Available now without Marketing API approval.
  organization — Community Management API (w_organization_social). Posts to company page
                 urn:li:organization:114404417 when LinkedIn approves that product.

Docs:
  https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin
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

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_UGC_URL = "https://api.linkedin.com/v2/ugcPosts"

MEMBER_SCOPES = "openid profile email w_member_social"
ORG_SCOPES = "openid profile email w_organization_social r_organization_social"


class LinkedInError(Exception):
    """LinkedIn API or OAuth failure."""


def post_mode() -> str:
    mode = (os.getenv("LINKEDIN_POST_MODE") or "member").strip().lower()
    return mode if mode in ("member", "organization") else "member"


def oauth_scopes() -> str:
    return ORG_SCOPES if post_mode() == "organization" else MEMBER_SCOPES


def organization_id() -> str:
    return (os.getenv("LINKEDIN_ORGANIZATION_ID") or DEFAULT_ORG_ID).strip()


def organization_urn() -> str:
    return f"urn:li:organization:{organization_id()}"


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
    api_base = (
        os.getenv("PUBLIC_API_URL")
        or os.getenv("NEXT_PUBLIC_API_URL")
        or "https://ready-2-robot.fly.dev"
    ).rstrip("/")
    return f"{api_base}/api/linkedin/callback"


def is_configured() -> bool:
    return bool(client_id() and client_secret())


def _load_tokens(db: Session) -> Optional[dict[str, Any]]:
    manual = (os.getenv("LINKEDIN_ACCESS_TOKEN") or "").strip()
    if manual:
        person_urn = (os.getenv("LINKEDIN_PERSON_URN") or "").strip() or None
        return {
            "access_token": manual,
            "refresh_token": (os.getenv("LINKEDIN_REFRESH_TOKEN") or "").strip() or None,
            "expires_at": None,
            "person_urn": person_urn,
            "post_mode": post_mode(),
            "source": "env",
        }
    data = cache_read(db, LINKEDIN_TOKEN_CACHE_KEY, stale_ok=True)
    return data if isinstance(data, dict) and data.get("access_token") else None


def _save_tokens(db: Session, payload: dict[str, Any]) -> None:
    cache_write(db, LINKEDIN_TOKEN_CACHE_KEY, payload, ttl_minutes=60 * 24 * 90)


def _fetch_member_identity(access_token: str) -> dict[str, str]:
    resp = requests.get(
        LINKEDIN_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise LinkedInError(f"Could not load LinkedIn profile ({resp.status_code}): {resp.text[:300]}")
    body = resp.json()
    sub = (body.get("sub") or "").strip()
    if not sub:
        raise LinkedInError("LinkedIn profile missing member id (sub)")
    person_urn = sub if sub.startswith("urn:li:person:") else f"urn:li:person:{sub}"
    name = (body.get("name") or body.get("given_name") or "").strip()
    return {"person_urn": person_urn, "member_name": name}


def connection_status(db: Session) -> dict[str, Any]:
    tokens = _load_tokens(db)
    org = organization_id()
    mode = post_mode()
    return {
        "configured": is_configured(),
        "connected": bool(tokens and tokens.get("access_token")),
        "post_mode": mode,
        "organization_page_posting": mode == "organization",
        "member_posting": mode == "member",
        "pending_marketing_api": mode == "member",
        "member_name": (tokens or {}).get("member_name"),
        "person_urn": (tokens or {}).get("person_urn"),
        "organization_id": org,
        "organization_urn": organization_urn(),
        "organization_url": f"https://www.linkedin.com/company/{org}/admin/dashboard/",
        "organization_page_status": (
            "active"
            if mode == "organization"
            else "pending_linkedin_support — Community Management API under review; use member mode meanwhile"
        ),
        "redirect_uri": redirect_uri(),
        "scopes": oauth_scopes(),
        "products_required": {
            "current": "Share on LinkedIn + Sign In with LinkedIn (OpenID Connect)",
            "for_company_page": "Community Management / Marketing API (LinkedIn review required)",
        },
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
        "scope": oauth_scopes(),
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
    token_payload = {
        "access_token": body["access_token"],
        "refresh_token": body.get("refresh_token"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat(),
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "post_mode": post_mode(),
        "source": "oauth",
    }
    if post_mode() == "member":
        token_payload.update(_fetch_member_identity(body["access_token"]))
    else:
        token_payload["organization_id"] = organization_id()
    return token_payload


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


def _access_token(db: Session) -> tuple[str, dict[str, Any]]:
    tokens = _load_tokens(db)
    if not tokens or not tokens.get("access_token"):
        raise LinkedInError("LinkedIn is not connected — authorize from Content Studio first")

    if tokens.get("source") != "env":
        expires_at = tokens.get("expires_at")
        refresh = tokens.get("refresh_token")
        if expires_at and refresh:
            try:
                exp = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if datetime.now(timezone.utc) >= exp - timedelta(minutes=5):
                    refreshed = _refresh_access_token(refresh)
                    tokens.update(refreshed)
                    tokens["post_mode"] = tokens.get("post_mode") or post_mode()
                    if tokens.get("post_mode") == "member" and not tokens.get("person_urn"):
                        tokens.update(_fetch_member_identity(tokens["access_token"]))
                    _save_tokens(db, tokens)
            except Exception as exc:
                logger.warning("LinkedIn token refresh failed: %s", exc)

    return tokens["access_token"], tokens


def complete_oauth_callback(db: Session, *, code: str, state: str) -> dict[str, Any]:
    state_payload = _consume_oauth_state(db, state)
    tokens = _exchange_code(code)
    _save_tokens(db, tokens)
    return {
        "connected": True,
        "return_to": state_payload.get("return_to") or "",
        "post_mode": tokens.get("post_mode"),
        "member_name": tokens.get("member_name"),
    }


def _publish_member_ugc(token: str, person_urn: str, text: str) -> str:
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    resp = requests.post(LINKEDIN_UGC_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        raise LinkedInError(f"LinkedIn publish failed ({resp.status_code}): {resp.text[:500]}")
    return resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id") or ""


def _publish_organization_rest(token: str, text: str, article_url: Optional[str]) -> str:
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
            "article": {"source": article_url, "title": "Ready For Robots"},
        }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Linkedin-Version": api_version(),
        "X-Restli-Protocol-Version": "2.0.0",
    }
    resp = requests.post(LINKEDIN_POSTS_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        raise LinkedInError(f"LinkedIn publish failed ({resp.status_code}): {resp.text[:500]}")
    return resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id") or ""


def publish_organization_post(db: Session, *, commentary: str, article_url: Optional[str] = None) -> dict[str, Any]:
    """Publish to LinkedIn — member feed (default) or company page when approved."""
    text = (commentary or "").strip()
    if not text:
        raise LinkedInError("Post text is required")
    if len(text) > 3000:
        raise LinkedInError("LinkedIn post text must be 3000 characters or fewer")

    token, tokens = _access_token(db)
    mode = tokens.get("post_mode") or post_mode()

    if mode == "organization":
        post_id = _publish_organization_rest(token, text, article_url)
        target = "organization_page"
    else:
        person_urn = tokens.get("person_urn")
        if not person_urn:
            tokens.update(_fetch_member_identity(token))
            person_urn = tokens["person_urn"]
            _save_tokens(db, tokens)
        post_id = _publish_member_ugc(token, person_urn, text)
        target = "member_profile"

    return {
        "ok": True,
        "post_id": post_id,
        "post_mode": mode,
        "published_as": target,
        "member_name": tokens.get("member_name"),
        "organization_id": organization_id(),
        "char_count": len(text),
        "published_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Posted to your personal LinkedIn feed (Share on LinkedIn). "
            "Company page posting requires Marketing API approval — set LINKEDIN_POST_MODE=organization when granted."
            if mode == "member"
            else None
        ),
    }
