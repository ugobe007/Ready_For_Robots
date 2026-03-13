"""
Shared auth dependencies for admin and other protected routes.
"""
import os
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Header

_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


def _require_user(authorization: Optional[str] = Header(None)) -> dict:
    """Verify Supabase Bearer token and return {uid, email}."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization: Bearer <token> required")
    token = authorization.split(" ", 1)[1]
    if not _JWT_SECRET:
        raise HTTPException(status_code=503, detail="SUPABASE_JWT_SECRET not configured")
    try:
        payload = jwt.decode(
            token, _JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        # Supabase JWT: email is top-level; fallback to user_metadata for OAuth
        email = (
            payload.get("email")
            or (payload.get("user_metadata") or {}).get("email")
            or (payload.get("app_metadata") or {}).get("email")
            or ""
        )
        return {"uid": payload["sub"], "email": email or ""}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired — please log in again")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def _is_admin(email: str) -> bool:
    """Check if email is in ADMIN_EMAILS (comma-separated)."""
    admins = os.getenv("ADMIN_EMAILS", "").strip().lower().split(",")
    return email.strip().lower() in [a.strip() for a in admins if a.strip()]


def require_admin(user: dict = Depends(_require_user)) -> dict:
    """Require authenticated user whose email is in ADMIN_EMAILS."""
    if not _is_admin(user.get("email", "")):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
