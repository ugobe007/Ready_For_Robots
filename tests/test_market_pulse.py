"""Public homepage market-pulse endpoint (auth not required)."""
from fastapi.testclient import TestClient


def test_market_pulse_public(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")

    # Avoid live DB dependency: stub builder
    import app.api.leads as leads_mod

    monkeypatch.setattr(
        leads_mod,
        "_build_market_pulse",
        lambda db: {
            "buyer_opportunities": 1979,
            "hot_windows": 279,
            "robot_vendors": 88,
            "active_deployments": 42,
            "buying_signals": 4100,
            "built_at": "2026-08-14T00:00:00+00:00",
        },
    )
    # Clear L1 cache
    leads_mod._MARKET_PULSE_CACHE["ts"] = 0.0
    leads_mod._MARKET_PULSE_CACHE["data"] = None

    client = TestClient(app)
    r = client.get("/api/leads/market-pulse")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["buyer_opportunities"] == 1979
    assert body["hot_windows"] == 279
    assert body["robot_vendors"] == 88
    assert body["active_deployments"] == 42
