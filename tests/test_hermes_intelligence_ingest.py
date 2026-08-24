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


def test_infer_qualify_rejects_supabase_service_role_jwt(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/infer-qualify",
        headers={
            "X-Admin-Key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.sig",
        },
        json={"dry_run": True, "limit": 1},
    )
    assert r.status_code == 401
    detail = (r.json().get("detail") or "").lower()
    assert "service_role" in detail
    assert "supabase" in detail


def test_qualify_overlay_dry_run_skips_db():
    from app.services.hermes_intelligence_ingest import apply_qualify_overlay

    result = apply_qualify_overlay(
        None,
        company_id=1,
        automation_fit=70,
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["hermes_qualify"]["automation_fit"] == 70


def test_contacts_ingest_dry_run_skips_db():
    from app.services.hermes_intelligence_ingest import ingest_contact

    result = ingest_contact(
        None,
        company_id=1,
        name="Pat Operations",
        title="VP Operations",
        confidence=70,
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["first_name"] == "Pat"


def test_buying_window_overlay_dry_run(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/buying-window-overlay",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "hermes_run_id": "test-window",
            "overlays": [
                {
                    "company_id": 1,
                    "urgency_0_100": 72,
                    "window_label": "peer proof + FY Q4 push",
                    "factors": [
                        {
                            "type": "peer_proof",
                            "peer": "DHL Supply Chain",
                            "robot": "Locus",
                            "recency_days": 12,
                        }
                    ],
                    "cal_hint": "Reference peer deployment; offer briefing in next 10 days.",
                    "confidence": 0.65,
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 1
    assert body["results"][0]["hermes_buying_window"]["urgency_0_100"] == 72
    assert body["results"][0]["dry_run"] is True


def test_video_evidence_ingest_dry_run(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/video-evidence/ingest",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "videos": [
                {
                    "company_name": "HelloFresh",
                    "source_url": "https://www.youtube.com/watch?v=example",
                    "platform": "youtube",
                    "evidence_kind": "facility_tour",
                    "title": "Inside a HelloFresh fulfillment center",
                    "excerpt": "Associates and AMRs moving meal kits through pack stations.",
                    "workflow_hint": "pack-out / meal kit assembly",
                    "robot_visible": "AMR",
                    "confidence": 0.72,
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 1
    assert body["results"][0]["dry_run"] is True
    assert "youtube.com" in body["results"][0]["hermes_video_evidence"]["source_url"]


def test_vendor_video_evidence_ingest_dry_run(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/vendor-video-evidence/ingest",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "videos": [
                {
                    "vendor_name": "Agility Robotics",
                    "source_url": "https://www.youtube.com/watch?v=digit-demo",
                    "platform": "youtube",
                    "evidence_kind": "oem_demo",
                    "title": "Digit tote handling demo",
                    "robot_model": "Digit",
                    "confidence": 0.8,
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 1
    assert body["results"][0]["vendor_name"] == "Agility Robotics"


def test_hermes_workflow_openapi_contract(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    paths = spec.get("paths") or {}
    required = [
        "/api/v1/market-graph/job-signals/ingest",
        "/api/v1/market-graph/qualify-overlay",
        "/api/v1/market-graph/infer-qualify",
        "/api/v1/market-graph/contacts/ingest",
        "/api/v1/market-graph/vendor-news/ingest",
        "/api/v1/market-graph/deployment-evidence/ingest",
        "/api/v1/market-graph/buying-window-overlay",
        "/api/v1/market-graph/video-evidence/ingest",
        "/api/v1/market-graph/vendor-video-evidence/ingest",
        "/api/v1/market-graph/video-evidence/seed-targets",
        "/api/v1/market-graph/daily-digest-send",
        "/api/v1/market-graph/reconstruct",
        "/api/v1/market-graph/status",
    ]
    missing = [p for p in required if p not in paths]
    assert missing == [], missing
