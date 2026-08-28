"""Robot-centric CRM hub — saved leads grouped by the sourcing robot submission."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — register ORM metadata
from app.api.auth_deps import _require_user
from app.database import Base, get_db
from app.main import app
from app.models.crm import CrmAccount, Team, TeamMember
from app.models.robot_submission import RobotSubmission
from app.models.user_profile import UserProfile

TEST_USER_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture()
def db_session():
    # StaticPool → one shared in-memory connection so the TestClient worker thread
    # sees the tables/rows this fixture created.
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
def seeded(db_session):
    user = UserProfile(id=TEST_USER_ID, email="hub@test.com")
    team = Team(id=uuid.uuid4(), name="Hub Team", slug="hub-team")
    db_session.add_all([user, team])
    db_session.flush()
    db_session.add(TeamMember(team_id=team.id, user_id=user.id, role="owner"))
    sub = RobotSubmission(
        canonical_url="https://relayrobotics.com",
        website_domain="relayrobotics.com",
        host="relayrobotics.com",
        submitted_url="https://relayrobotics.com/",
        company_name="Relay Robotics",
        product_name="Relay",
        profile_tier="C",
        capabilities=["transport", "mobile"],
        submission_count=1,
        research_snippets=[],
    )
    db_session.add(sub)
    db_session.flush()
    # Two buyers collected for this robot + one buyer with no robot link.
    db_session.add_all([
        CrmAccount(team_id=team.id, company_id=486, robot_submission_id=sub.id,
                   name="HCA Healthcare", industry="Healthcare", outreach_stage="new"),
        CrmAccount(team_id=team.id, company_id=5017, robot_submission_id=sub.id,
                   name="Atria Senior Living", industry="Healthcare", outreach_stage="draft_ready"),
        CrmAccount(team_id=team.id, company_id=999, robot_submission_id=None,
                   name="Unlinked Co", industry="Other", outreach_stage="new"),
    ])
    db_session.commit()
    return {"team": team, "submission": sub}


@pytest.fixture()
def client(db_session, seeded):
    saved = dict(app.dependency_overrides)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[_require_user] = lambda: {
        "uid": str(TEST_USER_ID), "email": "hub@test.com", "plan": "paid",
    }
    try:
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)


def test_hub_groups_leads_by_robot(client, seeded):
    team_id = str(seeded["team"].id)
    res = client.get(f"/api/crm/robots?team_id={team_id}")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["robot_count"] == 1  # only robots with saved leads; unlinked excluded
    robot = data["robots"][0]
    assert robot["robot"]["product_name"] == "Relay"
    assert robot["robot"]["profile_tier"] == "C"
    assert robot["lead_count"] == 2
    names = {l["name"] for l in robot["leads"]}
    assert names == {"HCA Healthcare", "Atria Senior Living"}
    assert robot["stage_counts"].get("new") == 1
    assert robot["stage_counts"].get("draft_ready") == 1


def test_account_persists_and_serializes_robot_submission_id(db_session, seeded):
    # Column round-trips, and the CrmAccountOut serializer surfaces it (so the
    # create/list responses carry robot_submission_id). (The POST path itself is a
    # field pass-through; the HTTP create can't run on SQLite because _ensure_profile
    # uses raw Postgres now().)
    from app.api.crm import _serialize_account

    a = (
        db_session.query(CrmAccount)
        .filter(CrmAccount.robot_submission_id.isnot(None))
        .first()
    )
    assert a is not None
    assert a.robot_submission_id == seeded["submission"].id
    out = _serialize_account(a)
    assert out["robot_submission_id"] == seeded["submission"].id
