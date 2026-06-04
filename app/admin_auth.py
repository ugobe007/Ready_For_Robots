"""Shared X-Admin-Key auth for ops endpoints (LinkedIn, purge, etc.)."""
from __future__ import annotations

import os
import re
from typing import Optional

from fastapi import Header, HTTPException, Query


def get_admin_key() -> str:
    """ADMIN_KEY is canonical; LINKEDIN_ADMIN_KEY is accepted as a legacy alias."""
    return (os.getenv("ADMIN_KEY") or os.getenv("LINKEDIN_ADMIN_KEY") or "").strip()


def get_cron_token() -> str:
    return (os.getenv("SCRAPER_CRON_TOKEN") or "").strip()


def _reject_misleading_admin_key(value: str) -> None:
    v = (value or "").strip()
    if re.fullmatch(r"[a-f0-9]{16}", v):
        raise HTTPException(
            status_code=401,
            detail=(
                "X-Admin-Key rejected: the 16-character hex from `fly secrets list` is a "
                "digest fingerprint, not ADMIN_KEY. Sync with: "
                "fly secrets set ADMIN_KEY='your-secret' -a ready-2-robot"
            ),
        )
    if v.startswith("eyJ"):
        raise HTTPException(
            status_code=401,
            detail=(
                "Put JWTs in Authorization: Bearer <token>, not X-Admin-Key. "
                "Use a user session access_token (not service_role) for admin JWT auth."
            ),
        )


def _auth_hint() -> str:
    return (
        "Auth options: header X-Admin-Key: <ADMIN_KEY>, "
        "query ?token=<SCRAPER_CRON_TOKEN>, or Authorization: Bearer <admin user JWT>."
    )


def check_admin_key(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")) -> None:
    key = get_admin_key()
    if not key:
        raise HTTPException(status_code=503, detail="ADMIN_KEY not configured on server")
    if not x_admin_key:
        raise HTTPException(status_code=401, detail=_auth_hint())
    if x_admin_key != key:
        _reject_misleading_admin_key(x_admin_key)
        raise HTTPException(status_code=401, detail="Invalid X-Admin-Key")


def require_admin_jwt_or_key(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None, description="SCRAPER_CRON_TOKEN (same as scraper cron URLs)"),
) -> dict:
    """
    Ops auth: X-Admin-Key, ?token=SCRAPER_CRON_TOKEN, raw ADMIN_KEY in Authorization,
    or Supabase Bearer JWT for ADMIN_EMAILS.
    """
    cron = get_cron_token()
    if cron and token and token.strip() == cron:
        return {"auth": "cron_token"}

    key = get_admin_key()
    if key and x_admin_key and x_admin_key.strip() == key:
        return {"auth": "admin_key"}

    auth_raw: Optional[str] = None
    if authorization:
        auth_raw = (
            authorization.split(" ", 1)[1].strip()
            if authorization.startswith("Bearer ")
            else authorization.strip()
        )

    if key and auth_raw and auth_raw == key:
        return {"auth": "admin_key"}

    if not auth_raw:
        if x_admin_key:
            _reject_misleading_admin_key(x_admin_key)
        raise HTTPException(status_code=401, detail=_auth_hint())

    if auth_raw in ("YOUR_ADMIN_JWT", "<token>", "token") or (
        len(auth_raw) < 30 and not auth_raw.count("-") >= 4
    ):
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid Authorization value — use Bearer <supabase_access_token> "
                "from a signed-in admin session, not a placeholder or bare UUID."
            ),
        )

    from app.api.auth_deps import _extract_email, _is_admin, _verify_jwt

    try:
        payload = _verify_jwt(auth_raw)
    except HTTPException as exc:
        if exc.status_code == 401 and key:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid JWT. {_auth_hint()}",
            ) from exc
        raise

    email = _extract_email(payload) or ""
    if not _is_admin(email):
        raise HTTPException(
            status_code=403,
            detail=f"Admin access required — {email or 'unknown email'} is not in ADMIN_EMAILS.",
        )
    return {"uid": payload["sub"], "email": email, "auth": "jwt"}
