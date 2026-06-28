"""Unit tests for the remote pipeline-cache refresh trigger helpers.

Regression guard: a 401/403 from the admin API must abort fast instead of
polling for the full --wait timeout (which masked auth failures as generic
"timed out" errors in the daily harness).
"""
from scripts.refresh_pipeline_cache import (
    _auth_header_args,
    _should_wait_after_post,
    resolve_remote_refresh_request,
)


def test_jwt_admin_key_routes_to_bearer():
    args = _auth_header_args("eyJhbGciOiJIUzI1NiJ9.payload.sig")
    assert args[0] == "-H"
    assert args[1].startswith("Authorization: Bearer eyJ")


def test_raw_secret_routes_to_x_admin_key():
    args = _auth_header_args("plain-shared-secret-123")
    assert args == ["-H", "X-Admin-Key: plain-shared-secret-123"]


def test_admin_key_is_whitespace_trimmed():
    assert _auth_header_args("  eyJabc  ")[1] == "Authorization: Bearer eyJabc"
    assert _auth_header_args("  secret  ")[1] == "X-Admin-Key: secret"


def test_only_2xx_proceeds_to_wait():
    assert _should_wait_after_post(200) is True
    assert _should_wait_after_post(202) is True
    assert _should_wait_after_post(299) is True


def test_auth_and_server_errors_do_not_wait():
    for status in (0, 301, 400, 401, 403, 404, 429, 500, 502, 503):
        assert _should_wait_after_post(status) is False
