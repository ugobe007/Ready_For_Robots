import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app
from app.models.robot_buyer_lead import RobotBuyerLead


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setenv("OWNER_EMAIL", "")
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_create_robot_buyer_lead(client):
    res = client.post(
        "/api/robot-buyer-leads",
        json={
            "email": "buyer@acme.com",
            "name": "Alex Buyer",
            "company": "Acme Logistics",
            "phone": "+15551234",
            "jobTitle": "VP Operations",
            "useCase": "We need AMRs for case picking in a 200k sq ft DC with WMS integration.",
            "robotType": "amr_warehouse",
            "implementationTimeline": "near_term_3_6mo",
            "source": "test",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["lead"]["company"] == "Acme Logistics"
    assert body["lead"]["robotType"] == "amr_warehouse"
    assert body["lead"]["implementationTimeline"] == "near_term_3_6mo"


def test_rejects_honeypot_and_invalid_robot_type(client):
    res = client.post(
        "/api/robot-buyer-leads",
        json={
            "email": "spam@bad.com",
            "company": "Spam Co",
            "useCase": "Enough characters here for validation.",
            "robotType": "amr_warehouse",
            "implementationTimeline": "exploring",
            "website": "http://spam.bot",
        },
    )
    assert res.status_code == 400

    res2 = client.post(
        "/api/robot-buyer-leads",
        json={
            "email": "buyer@acme.com",
            "company": "Acme",
            "useCase": "Valid use case description here.",
            "robotType": "flying_robot",
            "implementationTimeline": "exploring",
        },
    )
    assert res2.status_code == 400
