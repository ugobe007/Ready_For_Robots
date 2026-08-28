"""Product presentation offer — signup + pay, no fake deck."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.robot_submission import RobotPresentationRequest
from app.services.jobs_presentation import queue_presentation


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def test_presentation_requires_paid_plan(db_session):
    with pytest.raises(PermissionError, match="pay"):
        queue_presentation(
            db_session,
            {"uid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "email": "free@test.com", "plan_tier": "free"},
            url="https://www.relayrobotics.com/",
            company_name="Relay Robotics",
        )
    assert db_session.query(RobotPresentationRequest).count() == 0


def test_paid_presentation_queues_without_fake_deck(db_session, monkeypatch):
    monkeypatch.delenv("MANUS_API_KEY", raising=False)
    monkeypatch.delenv("REPLIT_API_KEY", raising=False)
    monkeypatch.delenv("JOBS_PRESENTATION_PROVIDER", raising=False)
    result = queue_presentation(
        db_session,
        {"uid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "email": "pro@test.com", "plan_tier": "pro"},
        url="https://www.relayrobotics.com/",
        company_name="Relay Robotics",
        product_name="Relay",
    )
    assert result["queued"] is True
    assert result["deck_url"] is None
    assert result["paid"] is True
    assert result["status"] in {"queued", "paid_queued"}
    assert "finished deck" in (result["hint"] or result["note"] or "").lower() or "queued" in (
        result["hint"] or ""
    ).lower()
    row = db_session.query(RobotPresentationRequest).one()
    assert row.deck_url is None
    assert row.paid == "true"
