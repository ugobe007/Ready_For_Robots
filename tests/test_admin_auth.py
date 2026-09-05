"""Unit tests for X-Admin-Key checks (no app import / DB)."""
import pytest
from fastapi import HTTPException

from app.admin_auth import _reject_misleading_admin_key


def test_reject_fly_secrets_list_fingerprint():
    with pytest.raises(HTTPException) as ei:
        _reject_misleading_admin_key("0123456789abcdef")
    assert ei.value.status_code == 401
    assert "fingerprint" in str(ei.value.detail).lower()


def test_reject_supabase_service_role_jwt():
    with pytest.raises(HTTPException) as ei:
        _reject_misleading_admin_key(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.sig"
        )
    assert ei.value.status_code == 401
    detail = str(ei.value.detail).lower()
    assert "service_role" in detail
    assert "supabase" in detail


def test_plain_wrong_key_is_not_misleading():
    _reject_misleading_admin_key("not-the-admin-key")
