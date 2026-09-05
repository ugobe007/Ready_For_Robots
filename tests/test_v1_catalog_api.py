"""V1 catalog API smoke tests."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_catalog_summary_requires_flag(monkeypatch):
    monkeypatch.setattr("app.config.Config.V1_ROBOT_INTELLIGENCE", False)
    monkeypatch.setattr("app.api.v1.deps.Config.V1_ROBOT_INTELLIGENCE", False)
    from app.main import app

    client = TestClient(app)
    assert client.get("/api/v1/catalog/summary").status_code == 404


def test_catalog_summary_enabled(monkeypatch):
    monkeypatch.setattr("app.config.Config.V1_ROBOT_INTELLIGENCE", True)
    monkeypatch.setattr("app.api.v1.deps.Config.V1_ROBOT_INTELLIGENCE", True)
    from app.main import app

    client = TestClient(app)
    # May 500 without DB tables in empty sqlite — just ensure route is mounted
    res = client.get("/api/v1/meta")
    assert res.status_code == 200
    body = res.json()
    assert "GET /api/v1/catalog/summary" in body["endpoints"]
    assert "GET /api/v1/manufacturers" in body["endpoints"]
