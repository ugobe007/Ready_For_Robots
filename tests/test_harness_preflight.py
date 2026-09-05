"""Tests for harness preflight and remote refresh auth resolution."""
from scripts.harness_preflight import classify_admin_refresh_auth
from scripts.refresh_pipeline_cache import resolve_remote_refresh_request


def test_classify_cron_token_ok(monkeypatch):
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    monkeypatch.setenv("SCRAPER_CRON_TOKEN", "cron-secret")
    out = classify_admin_refresh_auth()
    assert out["ok"] is True
    assert out["method"] == "SCRAPER_CRON_TOKEN"


def test_classify_jwt_admin_key_blocked(monkeypatch):
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    monkeypatch.setenv("ADMIN_KEY", "eyJhbGciOiJIUzI1NiJ9.payload.sig")
    out = classify_admin_refresh_auth()
    assert out["ok"] is False
    assert "JWT" in out["hint"]


def test_classify_fly_digest_blocked(monkeypatch):
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    monkeypatch.setenv("ADMIN_KEY", "a1b2c3d4e5f67890")
    out = classify_admin_refresh_auth()
    assert out["ok"] is False
    assert "digest" in out["hint"]


def test_resolve_refresh_uses_cron_query(monkeypatch):
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    monkeypatch.setenv("SCRAPER_CRON_TOKEN", "tok/with+chars")
    url, headers = resolve_remote_refresh_request("https://ready-2-robot.fly.dev")
    assert "token=" in url
    assert headers == []


def test_resolve_refresh_uses_admin_key_header(monkeypatch):
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    monkeypatch.setenv("ADMIN_KEY", "plain-secret")
    url, headers = resolve_remote_refresh_request("https://api.example.com")
    assert url.endswith("/api/admin/leads/refresh-pipeline-cache")
    assert headers == ["-H", "X-Admin-Key: plain-secret"]
