"""Hermes is retired: ingest 410 by default; scripts refuse without override."""
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
RETIRED = "Hermes is retired — Jobs uses POST /api/robot-job-match"
INGEST = "/api/v1/market-graph/job-signals/ingest"
JOB = {
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
}


def test_hermes_ingest_retired_by_default(monkeypatch):
    monkeypatch.delenv("HERMES_INGEST_ENABLED", raising=False)
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)
    r = client.post(
        INGEST,
        headers={"X-Admin-Key": "test-admin-secret"},
        json=JOB,
    )
    assert r.status_code == 410, r.text
    assert "Hermes ingest retired" in (r.json().get("detail") or "")
    assert "robot-job-match" in (r.json().get("detail") or "")


def test_hermes_ingest_enabled_still_requires_auth(monkeypatch):
    monkeypatch.setenv("HERMES_INGEST_ENABLED", "1")
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    monkeypatch.delenv("SCRAPER_CRON_TOKEN", raising=False)
    from app.main import app

    client = TestClient(app)
    r = client.post(INGEST, json=JOB)
    assert r.status_code == 403


def test_hermes_script_refuses_without_override():
    scripts = [
        ROOT / "scripts" / "hermes_auth_smoke.py",
        ROOT / "scripts" / "hermes_health_probe.py",
        ROOT / "scripts" / "run_hermes_intelligence_bridge.py",
        ROOT / "scripts" / "hermes_ingest_intelligence.py",
        ROOT / "scripts" / "hermes_fly_smoke.py",
    ]
    env = {k: v for k, v in os.environ.items() if k != "HERMES_RETIRED_OVERRIDE"}
    for script in scripts:
        proc = subprocess.run(
            [sys.executable, str(script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert proc.returncode == 2, (script.name, proc.returncode, proc.stderr)
        assert RETIRED in proc.stderr, script.name


def test_hermes_auth_smoke_jwt_still_checked_with_override():
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("RFR_ADMIN_KEY", "ADMIN_KEY")
    }
    env["HERMES_RETIRED_OVERRIDE"] = "1"
    env["RFR_ADMIN_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.sig"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "hermes_auth_smoke.py")],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "wrong_kind_of_secret" in proc.stdout
