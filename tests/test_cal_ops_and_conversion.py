"""Tests for Cal pipeline enrichment, ops monitor, and supply conversion."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.company import Company
from app.models.sales_learning import SalesExperienceEvent
from app.models.score import Score
from app.models.signal import Signal
from app.services.cal_ops_monitor import get_cal_ops_monitor, record_cal_assembly_rejection
from app.services.cal_pipeline_enrichment import enrichment_supply_eligible
from app.services.supply_autonomy import append_signup_cta, build_supply_tracking
from app.services.supply_conversion import parse_supply_attribution, record_supply_signup_landing
import app.models  # noqa: F401


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


def test_build_supply_tracking_and_cta_url():
    rc = SimpleNamespace(id=42, website="https://robots.example.com")
    tracking = build_supply_tracking(rc, message_token="abc123")
    body = append_signup_cta("Hello vendor.", rc, tracking=tracking)
    assert "utm_source=cal_supply" in body
    assert "rc=42" in body
    assert "msg=abc123" in body
    assert "/results?url=" in body


def test_parse_supply_attribution():
    robot_id, token, source = parse_supply_attribution(
        {"rc": "7", "msg": "tok", "utm_source": "cal_supply"}
    )
    assert robot_id == 7
    assert token == "tok"
    assert source == "cal_supply"


def test_enrichment_supply_eligible_rejects_cold_tier(db_session):
    company = Company(id=1, name="Test Buyer", crm_metadata={
        "agent_enrichment": {
            "inference_snapshot": {"tier": "MONITORING"},
            "rich_facts": [],
        }
    })
    ok, reason = enrichment_supply_eligible(company)
    assert ok is False
    assert "MONITORING" in reason


def test_record_assembly_rejection_and_monitor(db_session):
    record_cal_assembly_rejection(
        db_session,
        channel="supply",
        robot_company_id=99,
        vendor_name="Bad Vendor",
        subject="Test subject",
        issues=["weak match", "mis-attributed signal"],
    )
    db_session.commit()
    monitor = get_cal_ops_monitor(db_session, limit=5)
    assert len(monitor["assembly_rejections"]) == 1
    assert monitor["assembly_rejections"][0]["vendor_name"] == "Bad Vendor"
    assert "weak match" in monitor["assembly_rejections"][0]["issues"][0]


def test_record_supply_signup_landing(db_session):
    record_supply_signup_landing(
        db_session,
        page="signup",
        robot_company_id=12,
        message_token="tok1",
        utm_source="cal_supply",
    )
    db_session.commit()
    rows = db_session.query(SalesExperienceEvent).filter(
        SalesExperienceEvent.event_type == "supply_signup_landing"
    ).all()
    assert len(rows) == 1
    assert rows[0].robot_company_id == 12
