import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa: F401 - register SQLAlchemy models
from app.models.crm import CrmAccount, Team
from app.models.sales_learning import SalesExperienceEvent
from app.services.sales_learning_agent import (
    crm_workflow_intelligence,
    record_sales_experience,
    scraper_learning_report,
)


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


def test_record_sales_experience_persists_event(db_session):
    team_id = str(uuid.uuid4())
    db_session.add(Team(id=uuid.UUID(team_id), name="Ready For Robots"))
    db_session.commit()

    event = record_sales_experience(
        db_session,
        event_type="crm_outreach_sent",
        outcome="sent",
        team_id=team_id,
        channel="email",
        source_domain="freightwaves.com",
        signal_type="automation_intent",
        payload={"subject": "Intro"},
    )
    db_session.commit()

    row = db_session.query(SalesExperienceEvent).one()
    assert str(event.id) == str(row.id)
    assert row.outcome == "sent"
    assert row.source_domain == "freightwaves.com"
    assert row.payload["subject"] == "Intro"


def test_crm_workflow_intelligence_recommends_follow_up(db_session):
    team_uuid = uuid.uuid4()
    account_uuid = uuid.uuid4()
    db_session.add(Team(id=team_uuid, name="Ready For Robots"))
    account = CrmAccount(
        id=account_uuid,
        team_id=team_uuid,
        name="Acme Logistics",
        outreach_stage="intro_sent",
        contact_email="ops@example.com",
    )
    db_session.add(account)
    db_session.commit()
    record_sales_experience(
        db_session,
        event_type="crm_outreach_sent",
        outcome="sent",
        team_id=team_uuid,
        crm_account_id=account_uuid,
        channel="email",
    )
    db_session.commit()

    intel = crm_workflow_intelligence(db_session, account)

    assert intel["experience_count"] == 1
    assert intel["sent_count"] == 1
    assert "follow-up" in intel["recommended_action"].lower()
    assert intel["priority_score"] > 45


def test_scraper_learning_report_prioritizes_positive_sources(db_session):
    record_sales_experience(
        db_session,
        event_type="reply",
        outcome="replied",
        source_domain="freightwaves.com",
        signal_type="automation_intent",
    )
    record_sales_experience(
        db_session,
        event_type="send_failed",
        outcome="failed",
        source_domain="example-noise.com",
        signal_type="news",
    )
    db_session.commit()

    report = scraper_learning_report(db_session)

    assert report["experience_events"] == 2
    assert report["source_domain_priorities"][0]["key"] == "freightwaves.com"
    assert report["signal_type_priorities"][0]["key"] == "automation_intent"
    assert report["scraper_guidance"]
