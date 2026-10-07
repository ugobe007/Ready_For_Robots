from __future__ import annotations

from unittest.mock import patch
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
import app.models  # noqa: F401
import app.models.crm  # noqa: F401
import app.models.outreach  # noqa: F401
from app.main import app
from app.api.auth_deps import _require_user
from app.models.outreach import OutreachMessage


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_send_custom_email_endpoint(db_session):
    test_uid = uuid.uuid4()

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    def _override_user():
        return {"uid": str(test_uid), "email": "test@readyforrobots.com"}

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[_require_user] = _override_user

    with patch("app.api.crm.send_email_via_resend") as mock_send:
        mock_send.return_value = {
            "resend_id": "res_test_12345",
            "from_email": "Phelan <phelan@readyforrobots.com>",
        }

        client = TestClient(app)
        res = client.post(
            "/api/crm/send-custom-email",
            json={
                "to_email": "prospect@company.com",
                "subject": "Robotic Labor Placement — Company X",
                "body_text": "Hi Jane,\n\nI’m Phelan, a Robot Job Analyst at ReadyForRobots.",
                "company_name": "Company X",
            },
        )

        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["resend_id"] == "res_test_12345"
        assert data["to"] == "prospect@company.com"

        msg = db_session.query(OutreachMessage).filter(OutreachMessage.to_email == "prospect@company.com").first()
        assert msg is not None
        assert msg.resend_id == "res_test_12345"
        assert msg.subject == "Robotic Labor Placement — Company X"

    app.dependency_overrides.clear()
