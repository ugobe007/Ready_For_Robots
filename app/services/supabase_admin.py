"""Supabase Auth admin helpers — update app_metadata after billing events."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


def _supabase_admin_config() -> tuple[str, str]:
    base = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "").rstrip("/")
    key = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not base or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required for billing sync")
    return base, key


def update_user_app_metadata(user_id: str, patch: dict[str, Any]) -> bool:
    """Merge keys into Supabase auth app_metadata for a user."""
    if not user_id or not patch:
        return False
    try:
        base, key = _supabase_admin_config()
    except RuntimeError as exc:
        logger.warning("Supabase admin metadata update skipped: %s", exc)
        return False

    url = f"{base}/auth/v1/admin/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": "application/json",
    }
    try:
        resp = requests.put(url, headers=headers, json={"app_metadata": patch}, timeout=15)
        if resp.status_code >= 400:
            logger.warning("Supabase admin metadata update failed (%s): %s", resp.status_code, resp.text[:300])
            return False
        return True
    except requests.RequestException as exc:
        logger.warning("Supabase admin metadata update error: %s", exc)
        return False


def get_user_app_metadata(user_id: str) -> Optional[dict[str, Any]]:
    try:
        base, key = _supabase_admin_config()
    except RuntimeError:
        return None
    url = f"{base}/auth/v1/admin/users/{user_id}"
    headers = {"Authorization": f"Bearer {key}", "apikey": key}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code >= 400:
            return None
        data = resp.json()
        meta = data.get("app_metadata")
        return meta if isinstance(meta, dict) else {}
    except requests.RequestException:
        return None
