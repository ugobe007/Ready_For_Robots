"""Slice 0 — /api/v1 mount, envelope, and feature flag."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import router as v1_router
from app.api.v1.errors import V1HTTPException, error_response


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(v1_router, prefix="/api/v1")

    @app.exception_handler(V1HTTPException)
    async def _v1_handler(_request, exc: V1HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else None
        if detail and "schema_version" in detail and "error" in detail:
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=exc.status_code, content=detail)
        return error_response(exc.status_code, code="v1_error", message=str(exc.detail))

    return app


def test_v1_meta_disabled_by_default(monkeypatch):
    monkeypatch.setattr("app.config.Config.V1_ROBOT_INTELLIGENCE", False)
    monkeypatch.setattr("app.api.v1.deps.Config.V1_ROBOT_INTELLIGENCE", False)

    client = TestClient(_build_app())
    response = client.get("/api/v1/meta")
    assert response.status_code == 404
    body = response.json()
    assert body["schema_version"] == "v1"
    assert body["error"]["code"] == "v1_disabled"
    assert body["error"]["retryable"] is False


def test_v1_meta_enabled(monkeypatch):
    monkeypatch.setattr("app.config.Config.V1_ROBOT_INTELLIGENCE", True)
    monkeypatch.setattr("app.api.v1.deps.Config.V1_ROBOT_INTELLIGENCE", True)

    client = TestClient(_build_app())
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "v1"
    assert body["enabled"] is True
    assert "site_review" in body["truth_stages"]
    assert "expanding" not in body["truth_stages"]
    assert set(body["dispositions"]) == {"active", "watch", "paused", "lost"}
    assert "deployment_readiness" not in body["decision_dimensions"]
    assert len(body["decision_dimensions"]) == 7
    assert "do_not_surface" in body["call_priorities"]
