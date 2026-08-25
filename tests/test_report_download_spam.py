import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app
from app.models.waitlist import WaitlistSignup


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite://",
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

    sent = []

    def fake_send(**kwargs):
        sent.append(kwargs)
        return {"id": "test"}

    monkeypatch.setenv("OWNER_EMAIL", "ugobe07@gmail.com")
    monkeypatch.setattr("app.api.leads.send_email_via_resend", fake_send)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        c.sent = sent
        c.db_factory = SessionLocal
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_spam_report_download_is_ignored(client):
    res = client.post(
        "/api/leads/report-download",
        json={
            "email": "info@alohaah.com",
            "name": "NLexdStETPSyhfSDp",
            "company": "Qpjgved LLC",
            "robotCategory": "zTBxnhfiXkjdwRgHNyZeXY",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["ignored"] is True
    assert body["lead"] is None
    assert client.sent == []
    db = client.db_factory()
    try:
        assert db.query(WaitlistSignup).count() == 0
    finally:
        db.close()


def test_honeypot_report_download_is_ignored(client):
    res = client.post(
        "/api/leads/report-download",
        json={
            "email": "sara@locusrobotics.com",
            "name": "Sara Chen",
            "company": "Locus Robotics",
            "robotCategory": "warehouse AMR",
            "website": "http://spam.bot",
        },
    )
    assert res.status_code == 200
    assert res.json()["ignored"] is True
    assert client.sent == []


def test_real_report_download_is_captured(client):
    res = client.post(
        "/api/leads/report-download",
        json={
            "email": "sara@locusrobotics.com",
            "name": "Sara Chen",
            "company": "Locus Robotics",
            "robotCategory": "warehouse AMR",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body.get("ignored") is not True
    assert body["lead"]["email"] == "sara@locusrobotics.com"
    assert body["lead"]["company"] == "Locus Robotics"
    assert len(client.sent) == 2
    db = client.db_factory()
    try:
        row = db.query(WaitlistSignup).one()
        assert row.source == "report_download"
        assert row.company == "Locus Robotics"
    finally:
        db.close()
