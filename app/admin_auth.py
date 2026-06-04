"""Shared X-Admin-Key auth for ops endpoints (LinkedIn, purge, etc.)."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException


def get_admin_key() -> str:
    """ADMIN_KEY is canonical; LINKEDIN_ADMIN_KEY is accepted as a legacy alias."""
    return (os.getenv("ADMIN_KEY") or os.getenv("LINKEDIN_ADMIN_KEY") or "").strip()


def check_admin_key(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")) -> None:
    key = get_admin_key()
    if not key:
        raise HTTPException(status_code=503, detail="ADMIN_KEY not configured on server")
    if x_admin_key != key:
        raise HTTPException(status_code=401, detail="Invalid X-Admin-Key")


def require_admin_jwt_or_key(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    Ops auth for CLI/curl: ``X-Admin-Key`` (Fly ``ADMIN_KEY`` secret) or
    Supabase Bearer JWT for an email in ``ADMIN_EMAILS``.
    """
    key = get_admin_key()
    if key and x_admin_key == key:
        return {"auth": "admin_key"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail=(
                "Use Authorization: Bearer <supabase_access_token> "
                "(signed-in admin) or header X-Admin-Key: <ADMIN_KEY from Fly secrets>."
            ),
        )
    token = authorization.split(" ", 1)[1].strip()
    if token in ("YOUR_ADMIN_JWT", "<token>", "token") or len(token) < 30:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid token — use a real Supabase session access_token, not the placeholder. "
                "In the browser: log in → DevTools → Application → localStorage → "
                "supabase auth token, or Network tab → any /api request → Authorization header."
            ),
        )

    from app.api.auth_deps import _extract_email, _is_admin, _verify_jwt

    payload = _verify_jwt(token)
    email = _extract_email(payload) or ""
    if not _is_admin(email):
        raise HTTPException(
            status_code=403,
            detail=f"Admin access required — {email or 'unknown email'} is not in ADMIN_EMAILS.",
        )
    return {"uid": payload["sub"], "email": email, "auth": "jwt"}
