"""Tenant isolation — team = organization (Sprint 1 / RFR-111)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models  # noqa: F401
from app.models.crm import CrmAccount, Team
from app.models.sales_agent import SalesOpportunity


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


def _team_with_opportunity(db, name: str):
    # CRM models use raw Postgres UUID (need uuid.UUID).
    # SalesOpportunity uses dialect-aware UUID (string on SQLite).
    team_id = uuid.uuid4()
    account_id = uuid.uuid4()
    team = Team(id=team_id, name=name)
    db.add(team)
    db.flush()
    account = CrmAccount(id=account_id, team_id=team_id, name=f"{name} Account")
    db.add(account)
    db.flush()
    opp = SalesOpportunity(
        id=str(uuid.uuid4()),
        opportunity_type="deployment",
        team_id=str(team_id),
        crm_account_id=str(account_id),
        title=f"{name} opp",
        current_stage="discovered",
        disposition="active",
    )
    db.add(opp)
    db.commit()
    return team, opp


def test_opportunities_are_team_scoped(db_session):
    team_a, opp_a = _team_with_opportunity(db_session, "Alpha Robotics")
    team_b, opp_b = _team_with_opportunity(db_session, "Beta Robotics")

    visible_a = (
        db_session.query(SalesOpportunity)
        .filter(SalesOpportunity.team_id == str(team_a.id))
        .all()
    )
    visible_b = (
        db_session.query(SalesOpportunity)
        .filter(SalesOpportunity.team_id == str(team_b.id))
        .all()
    )
    assert {o.id for o in visible_a} == {opp_a.id}
    assert {o.id for o in visible_b} == {opp_b.id}
    assert opp_a.id not in {o.id for o in visible_b}
