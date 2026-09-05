"""Tests for sales workflow hub aggregation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa: F401
from app.services.sales_workflow_hub import collect_next_actions, workflow_summary_since

_DB_SKIP = pytest.mark.skip(reason="SQLite UUID bind incompatible with CRM models")


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_collect_next_actions_empty_team(db_session):
    actions = collect_next_actions(db_session, team_ids=[], user_id=None, limit=10)
    assert actions == []


@_DB_SKIP
def test_workflow_summary_since_zero(db_session):
    summary = workflow_summary_since(
        db_session,
        team_ids=[str(uuid.uuid4())],
        since=datetime.now(timezone.utc),
    )
    assert summary["signalsDetected"] == 0
    assert summary["followupsSent"] == 0
    assert summary["highlights"] == []
