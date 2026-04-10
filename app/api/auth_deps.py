"""
Shared auth dependencies for admin and other protected routes.
Supports both legacy HS256 JWT secret and JWKS (ES256/RS256) verification.
"""
import os
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Header

# PyJWKClient optional (PyJWT 2.8+)
try:
    from jwt import PyJWKClient
except ImportError:
    PyJWKClient = None

_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
_SUPABASE_URL = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "").rstrip("/")


def _email_from_identities(payload: dict) -> str:
    """Extract email from Supabase identities array (OAuth fallback)."""
    identities = payload.get("identities") or []
    if isinstance(identities, list) and identities:
        first = identities[0]
        if isinstance(first, dict):
            data = first.get("identity_data") or first
            if isinstance(data, dict):
                return data.get("email") or ""
    return ""


def _extract_email(payload: dict) -> str:
    """Extract email from Supabase JWT payload."""
    return (
        payload.get("email")
        or (payload.get("user_metadata") or {}).get("email")
        or (payload.get("app_metadata") or {}).get("email")
        or _email_from_identities(payload)
        or ""
    )


def _verify_jwt(token: str) -> dict:
    """Verify JWT and return payload. Tries legacy HS256 first, then JWKS."""
    if not _JWT_SECRET and not _SUPABASE_URL:
        raise HTTPException(status_code=503, detail="SUPABASE_JWT_SECRET or SUPABASE_URL not configured")
    # 1. Try legacy HS256 secret
    if _JWT_SECRET:
        try:
            payload = jwt.decode(
                token, _JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired — please log in again")
        except Exception:
            pass  # Fall through to JWKS (e.g. InvalidSignatureError, InvalidAlgorithmError for ES256 tokens)
    # 2. Try JWKS (Supabase signing keys)
    if _SUPABASE_URL and PyJWKClient:
        jwks_uri = f"{_SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        try:
            jwks_client = PyJWKClient(jwks_uri, cache_jwk_set=True, lifespan=600)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired — please log in again")
        except Exception:
            pass
    raise HTTPException(status_code=401, detail="Invalid token")


def optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Return {uid, email} when a valid Bearer token is present; otherwise None.
    Use for endpoints that accept both anonymous and authenticated callers.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ", 1)[1]
        payload = _verify_jwt(token)
        email = _extract_email(payload) or ""
        return {"uid": payload["sub"], "email": email}
    except HTTPException:
        return None


def _require_user(authorization: Optional[str] = Header(None)) -> dict:
    """Verify Supabase Bearer token and return {uid, email}."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization: Bearer <token> required")
    token = authorization.split(" ", 1)[1]
    payload = _verify_jwt(token)
    email = _extract_email(payload) or ""
    return {"uid": payload["sub"], "email": email}


def _is_admin(email: str) -> bool:
    """Check if email is in ADMIN_EMAILS (comma-separated)."""
    admins = os.getenv("ADMIN_EMAILS", "").strip().lower().split(",")
    return email.strip().lower() in [a.strip() for a in admins if a.strip()]


def require_admin(user: dict = Depends(_require_user)) -> dict:
    """Require authenticated user whose email is in ADMIN_EMAILS."""
    if not _is_admin(user.get("email", "")):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def assert_newsletter_regen_allowed(
    authorization: Optional[str],
    x_newsletter_regen_key: Optional[str],
) -> None:
    """
    When NEWSLETTER_REGEN_SECRET is set, regeneration endpoints require either
    header X-Newsletter-Regen-Key matching that secret, or a valid admin JWT.
    When unset, regeneration stays open (local dev).
    """
    secret = os.getenv("NEWSLETTER_REGEN_SECRET", "").strip()
    if not secret:
        return
    if x_newsletter_regen_key and x_newsletter_regen_key == secret:
        return
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = _verify_jwt(token)
            if _is_admin(_extract_email(payload)):
                return
        except HTTPException:
            pass
    raise HTTPException(
        status_code=403,
        detail="Newsletter regeneration requires X-Newsletter-Regen-Key or an admin session.",
    )
