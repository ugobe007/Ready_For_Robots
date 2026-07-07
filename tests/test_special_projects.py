"""Special projects — admin CRUD + token-gated client portal."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.auth_deps import require_admin
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = lambda: {"uid": "admin", "email": "admin@example.com"}
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _create(client, **kw):
    payload = {"name": "NIMO Technology", **kw}
    res = client.post("/api/admin/special-projects", json=payload)
    assert res.status_code == 200, res.text
    return res.json()


def test_create_generates_slug_and_token(client):
    body = _create(client, robot_description="Tactile kitchen humanoid")
    assert body["slug"] == "nimo-technology"
    assert body["share_token"]
    assert body["portal_path"] == f"/p/{body['share_token']}"
    assert body["status"] == "discovery"


def test_slug_is_unique(client):
    a = _create(client)
    b = _create(client)
    assert a["slug"] != b["slug"]
    assert b["slug"].startswith("nimo-technology-")


def test_patch_metrics_status_and_pipeline(client):
    proj = _create(client)
    res = client.patch(
        f"/api/admin/special-projects/{proj['id']}",
        json={
            "status": "piloting",
            "metrics": {"demos_booked": 4, "pilots_signed": 1},
            "pipeline": {"targeted": 50, "contacted": 30, "demo": 4, "pilot_signed": 1},
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "piloting"
    assert body["metrics"]["demos_booked"] == 4
    assert body["pipeline"]["contacted"] == 30


def test_invalid_status_rejected(client):
    proj = _create(client)
    res = client.patch(f"/api/admin/special-projects/{proj['id']}", json={"status": "bogus"})
    assert res.status_code == 400


def test_add_update_and_list(client):
    proj = _create(client)
    res = client.post(
        f"/api/admin/special-projects/{proj['id']}/updates",
        json={"title": "First demo booked", "body": "CloudKitchens demo Friday", "category": "milestone"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["update_count"] == 1
    assert body["updates"][0]["title"] == "First demo booked"
    assert body["updates"][0]["category"] == "milestone"


def test_invalid_update_category_rejected(client):
    proj = _create(client)
    res = client.post(
        f"/api/admin/special-projects/{proj['id']}/updates",
        json={"title": "x", "category": "not-a-category"},
    )
    assert res.status_code == 400


def test_public_portal_returns_client_safe_view(client):
    proj = _create(client, summary="Tactile humanoid for kitchens")
    client.patch(
        f"/api/admin/special-projects/{proj['id']}",
        json={"metrics": {"demos_booked": 2}, "pipeline": {"targeted": 40, "contacted": 12, "demo": 2}},
    )
    client.post(
        f"/api/admin/special-projects/{proj['id']}/updates",
        json={"title": "Outreach live", "category": "outreach"},
    )

    # Public portal — no auth, by share token.
    res = client.get(f"/api/special-projects/portal/{proj['share_token']}")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["name"] == "NIMO Technology"
    assert body["summary"] == "Tactile humanoid for kitchens"
    assert body["metrics"]["demos_booked"] == 2
    # Funnel is ordered by the beta-motion stages.
    stages = [f["stage"] for f in body["funnel"]]
    assert stages == ["targeted", "contacted", "demo"]
    assert body["updates"][0]["title"] == "Outreach live"
    # Internal fields must NOT leak to the client.
    assert "share_token" not in body
    assert "slug" not in body
    assert "contact_email" not in body


def test_public_portal_unknown_token_404(client):
    res = client.get("/api/special-projects/portal/nope")
    assert res.status_code == 404


def test_rotate_token_invalidates_old(client):
    proj = _create(client)
    old = proj["share_token"]
    res = client.post(f"/api/admin/special-projects/{proj['id']}/rotate-token")
    assert res.status_code == 200
    new = res.json()["share_token"]
    assert new != old
    assert client.get(f"/api/special-projects/portal/{old}").status_code == 404
    assert client.get(f"/api/special-projects/portal/{new}").status_code == 200
