"""Tests for Hermes → RFR deployment evidence ingest API (auth + dry_run, no DB)."""
from fastapi.testclient import TestClient


def test_deployment_ingest_requires_auth(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/deployment-evidence/ingest",
        json={
            "dry_run": True,
            "claims": [
                {
                    "text": "Digit moved more than 100,000 totes at GXO with operating hours reported.",
                    "vendor_name": "Agility Robotics",
                    "robot_model": "Digit",
                    "customer_name": "GXO",
                }
            ],
        },
    )
    assert r.status_code == 403


def test_deployment_ingest_dry_run_with_admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/market-graph/deployment-evidence/ingest",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "dry_run": True,
            "hermes_run_id": "test-run",
            "claims": [
                {
                    "text": (
                        "Digit moved more than 100,000 totes at GXO and accumulated more than "
                        "65,000 operating hours. Unloading totes from AMRs onto a conveyor."
                    ),
                    "source_url": "https://example.com/gxo",
                    "source_type": "oem_press_release",
                    "vendor_name": "Agility Robotics",
                    "robot_model": "Digit",
                    "customer_name": "GXO",
                    "facility_name": "Flowery Branch, GA",
                    "industry": "Logistics",
                    "work_type": "Tote handling",
                    "workflow": {"origin": "AMR", "action": "Unload tote", "destination": "Conveyor"},
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] == 1
    assert body["failed"] == 0
    assert body["results"][0]["dry_run"] is True
    assert body["results"][0]["deployment_id"]
    assert body["results"][0].get("metrics", {}).get("totes_moved") == 100000 or body["results"][0].get(
        "confidence", 0
    ) > 0
