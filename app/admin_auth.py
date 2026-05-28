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
