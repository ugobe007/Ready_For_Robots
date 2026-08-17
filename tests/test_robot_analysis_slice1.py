"""Slice 1 tests — SSRF, provenance, confirm versioning."""
from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
import app.models  # noqa: F401
from app.api.v1 import router as v1_router
from app.api.v1.errors import V1HTTPException, error_response
from app.services.robot_analysis_service import confirm_analysis, create_analysis
from app.services.robot_profile_extract import extract_robot_profile
from app.services.robot_url_safety import UrlSafetyError, assert_public_http_url


FORKLIFT_HTML = """
<html><head><title>AutoFork X1 — Acme Robotics</title></head>
<body>
<h1>AutoFork X1 Autonomous Forklift</h1>
<p>Payload capacity 1500 kg. Lift height 4.5 m. Runtime 10 hours.</p>
<p>Speed 1.5 m/s. Indoor mixed traffic with lidar navigation.</p>
<p>Transports pallets between production and warehouse. Rack placement supported.</p>
</body></html>
"""


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session, monkeypatch):
    monkeypatch.setattr("app.config.Config.V1_ROBOT_INTELLIGENCE", True)
    monkeypatch.setattr("app.api.v1.deps.Config.V1_ROBOT_INTELLIGENCE", True)
    monkeypatch.setenv("V1_ANALYSIS_ASYNC", "false")

    app = FastAPI()
    app.include_router(v1_router, prefix="/api/v1")

    @app.exception_handler(V1HTTPException)
    async def _handler(_req, exc: V1HTTPException):
        from fastapi.responses import JSONResponse

        detail = exc.detail if isinstance(exc.detail, dict) else None
        if detail and "error" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)
        return error_response(exc.status_code, code="v1_error", message=str(exc.detail))

    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    return TestClient(app)


def test_ssrf_rejects_private_hosts():
    with pytest.raises(UrlSafetyError):
        assert_public_http_url("http://127.0.0.1/robot")
    with pytest.raises(UrlSafetyError):
        assert_public_http_url("http://localhost/product")
    with pytest.raises(UrlSafetyError):
        assert_public_http_url("http://169.254.169.254/latest/meta-data")


def test_unknown_differs_from_false():
    result = extract_robot_profile(description="A warehouse vehicle with no specs listed.")
    payload = next(c for c in result.claims if c.field_path == "payload_max_kg")
    assert payload.value is None
    assert payload.truth_state == "unknown"
    assert payload.confidence == 0.0


def test_observed_claims_require_excerpt():
    result = extract_robot_profile(html=FORKLIFT_HTML, source_url="https://acme.example/autofork")
    payload = next(c for c in result.claims if c.field_path == "payload_max_kg")
    assert payload.value == 1500
    assert payload.truth_state == "observed"
    assert payload.excerpt
    assert "1500" in payload.excerpt


def test_create_analysis_builds_reviewable_forklift_profile(db_session):
    def fetcher(_url):
        return FORKLIFT_HTML, "https://acme.example/autofork-x1"

    analysis = create_analysis(
        db_session,
        source_url="https://acme.example/autofork-x1",
        process_inline=True,
        fetcher=fetcher,
    )
    db_session.commit()
    assert analysis.status == "needs_review"
    assert analysis.draft_profile["category"] == "autonomous_forklift"
    fields = {f["field_path"]: f for f in analysis.draft_profile["fields"]}
    assert fields["payload_max_kg"]["value"] == 1500
    assert fields["payload_max_kg"]["truth_state"] == "observed"
    assert fields["payload_max_kg"]["excerpt"]
    # No invented trailer claim as false — remains unknown unless evidenced
    trailer = next(w for w in analysis.draft_profile["work_envelope"] if w["key"] == "trailer_entry")
    assert trailer["status"] == "unknown"
    assert trailer["truth_state"] == "unknown"


HUMANOID_HTML = """
<html><head><title>HMND 01 Alpha — Humanoid</title></head>
<body>
<h1>Industrial-grade humanoid labour</h1>
<p>Wheeled humanoid for factory logistics and tote movement.</p>
<p>Payload 15 kg. Runtime 4 hours. Handles totes and cases on the line.</p>
</body></html>
"""


def test_humanoid_is_supported_v1_category(db_session):
    def fetcher(_url):
        return HUMANOID_HTML, "https://acme.example/hmnd-01"

    analysis = create_analysis(
        db_session,
        source_url="https://acme.example/hmnd-01",
        process_inline=True,
        fetcher=fetcher,
    )
    db_session.commit()
    assert analysis.status == "needs_review"
    assert analysis.draft_profile["category"] == "humanoid"
    fields = {f["field_path"]: f for f in analysis.draft_profile["fields"]}
    assert fields["payload_max_kg"]["value"] == 15
    assert fields["category"]["value"] == "humanoid"


def test_confirm_creates_immutable_new_version(db_session):
    def fetcher(_url):
        return FORKLIFT_HTML, "https://acme.example/autofork-x1"

    analysis = create_analysis(
        db_session,
        source_url="https://acme.example/autofork-x1",
        process_inline=True,
        fetcher=fetcher,
    )
    first = confirm_analysis(
        db_session,
        analysis,
        profile_etag=analysis.profile_etag,
        corrections=[
            {
                "field_path": "payload_max_kg",
                "value": 1600,
                "truth_state": "oem_verified",
                "note": "Updated datasheet",
            }
        ],
    )
    db_session.commit()
    assert first["robot_id"]
    assert first["profile_version_id"]

    # Second confirmation path: new analysis for same robot creates version 2 via confirm on fresh analysis
    analysis2 = create_analysis(
        db_session,
        source_url="https://acme.example/autofork-x1?v=2",
        process_inline=True,
        fetcher=fetcher,
        requester_scope="other",
    )
    second = confirm_analysis(
        db_session,
        analysis2,
        profile_etag=analysis2.profile_etag,
        corrections=[],
    )
    db_session.commit()
    from app.models.robot_intelligence import RobotProfileVersion

    versions = (
        db_session.query(RobotProfileVersion)
        .filter(RobotProfileVersion.robot_id == first["robot_id"])
        .order_by(RobotProfileVersion.version.asc())
        .all()
    )
    assert len(versions) == 2
    assert versions[0].version == 1
    assert versions[1].version == 2
    assert versions[1].supersedes_version_id == versions[0].id
    # Original version unchanged
    assert versions[0].physical_capabilities["payload_max_kg"]["value"] == 1600


def test_api_robot_analysis_flow(client, db_session, monkeypatch):
    def fetcher(_url):
        return FORKLIFT_HTML, "https://acme.example/autofork-x1"

    monkeypatch.setattr(
        "app.services.robot_analysis_service.fetch_product_page",
        lambda url, timeout=12.0, fetcher=None: {
            "url": "https://acme.example/autofork-x1",
            "html": FORKLIFT_HTML,
            "fetched_at": "2026-08-10T18:00:00Z",
        },
    )

    created = client.post(
        "/api/v1/robot-analyses",
        json={"source_url": "https://acme.example/autofork-x1"},
    )
    assert created.status_code == 202
    body = created.json()
    analysis_id = body["analysis_id"]
    token = body["analysis_token"]

    got = client.get(
        f"/api/v1/robot-analyses/{analysis_id}",
        headers={"X-Analysis-Token": token},
    )
    assert got.status_code == 200
    profile = got.json()
    assert profile["status"] == "needs_review"
    assert profile["draft_profile"]["category"] == "autonomous_forklift"

    confirmed = client.post(
        f"/api/v1/robot-analyses/{analysis_id}/confirm",
        headers={"X-Analysis-Token": token},
        json={"profile_etag": profile["profile_etag"], "corrections": []},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["robot_id"]
    assert confirmed.json()["profile_version_id"]


def test_api_rejects_ssrf(client):
    response = client.post("/api/v1/robot-analyses", json={"source_url": "http://127.0.0.1/secret"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsafe_url"
