"""Tests for Hermes intelligence ingest APIs (auth + dry_run, no DB writes required)."""
from fastapi.testclient import TestClient


def test_job_signals_ingest_requires_auth(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/job-signals/ingest",
        json={
            "dry_run": True,
            "jobs": [
                {
                    "job_title": "Warehouse Associate - AMR Operator",
                    "employer": "GXO Logistics",
                    "excerpt": (
                        "Operate AMRs and unload totes from robots onto conveyor for pack-out. "
                        "Material handling in a high-volume fulfillment center."
                    ),
                }
            ],
        },
    )
    assert r.status_code == 403


def test_job_signals_ingest_dry_run(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/job-signals/ingest",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "hermes_run_id": "test-jobs",
            "jobs": [
                {
                    "job_title": "Warehouse Associate - AMR Operator",
                    "employer": "GXO Logistics",
                    "excerpt": (
                        "Operate AMRs and unload totes from robots onto conveyor for pack-out. "
                        "Material handling in a high-volume fulfillment center."
                    ),
                    "source_url": "https://example.com/jobs/amr-1",
                    "location": "Flowery Branch, GA, USA",
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 1
    assert body["failed"] == 0
    assert body["results"][0]["dry_run"] is True
    assert body["results"][0]["work"]["work_unit_id"]


def test_qualify_overlay_dry_run(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/qualify-overlay",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "hermes_run_id": "test-qualify",
            "overlays": [
                {
                    "company_id": 1,
                    "automation_fit": 78,
                    "labor_intensity": "high",
                    "facility_clarity": "named_site",
                    "blockers": [],
                    "rationale": "Open AMR operator roles plus tote handling language.",
                    "vendor_shortlist": [{"vendor": "Agility Robotics", "model": "Digit"}],
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 1
    assert body["results"][0]["hermes_qualify"]["automation_fit"] == 78
    assert body["results"][0]["hermes_qualify"]["truth_state"] == "HERMES_OVERLAY"


def test_contacts_ingest_dry_run(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/contacts/ingest",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "contacts": [
                {
                    "company_id": 1,
                    "name": "Jane Operations",
                    "title": "VP Operations",
                    "linkedin_url": "https://www.linkedin.com/in/example",
                    "confidence": 70,
                    "source_url": "https://example.com/team",
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 1
    assert body["results"][0]["dry_run"] is True


def test_contacts_ingest_skips_low_confidence(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/contacts/ingest",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "contacts": [
                {
                    "company_id": 1,
                    "name": "Low Conf",
                    "confidence": 10,
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["skipped"] == 1
    assert body["accepted"] == 0
    assert body["results"][0]["skipped"] is True


def test_vendor_news_ingest_dry_run(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/vendor-news/ingest",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "hermes_run_id": "test-news",
            "items": [
                {
                    "entity_name": "Agility Robotics",
                    "entity_kind": "vendor",
                    "news_type": "capability",
                    "title": "Digit software update",
                    "text": (
                        "Agility announced a new Digit foundation-model-assisted "
                        "navigation stack for mixed-SKU tote handling."
                    ),
                    "source_url": "https://example.com/agility-news",
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 1
    assert body["results"][0]["dry_run"] is True
    assert body["results"][0]["news_id"].startswith("VN-")


def test_infer_qualify_requires_auth(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/infer-qualify",
        json={"dry_run": True, "limit": 2},
    )
    assert r.status_code == 403


def test_daily_digest_send_requires_auth(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/daily-digest-send",
        json={"force": False},
    )
    assert r.status_code == 403


def test_infer_qualify_rejects_fly_secrets_list_fingerprint(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/infer-qualify",
        headers={"X-Admin-Key": "0123456789abcdef"},
        json={"dry_run": True, "limit": 1},
    )
    assert r.status_code == 401
    assert "fingerprint" in (r.json().get("detail") or "").lower()
