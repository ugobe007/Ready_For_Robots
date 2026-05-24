"""OEM prospect gate — robot vendors must pass into robot_companies pipeline."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.robot_company import RobotCompany
from app.services.company_validator import is_valid_lead
from app.services.lead_filter import is_junk
from app.services.lead_name_gate import (
    check_lead_name,
    check_oem_prospect_name,
    is_acceptable_oem_prospect_name,
)
from app.services.text_classifier import classify


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


@pytest.mark.parametrize(
    "name",
    [
        "Fetch Robotics",
        "Agility Robotics",
        "Figure AI",
        "6 River Systems",
        "Universal Robots",
        "GreyOrange",
    ],
)
def test_known_robot_vendors_pass_oem_gate(name):
    assert is_junk(name, mode="buyer")[0] is True
    assert is_junk(name, mode="oem_prospect")[0] is False
    ok, reason = check_oem_prospect_name(name)
    assert ok is True, reason
    assert is_acceptable_oem_prospect_name(name) is True


@pytest.mark.parametrize(
    "name",
    [
        "Fetch Robotics",
        "Agility Robotics",
        "Figure AI",
    ],
)
def test_known_robot_vendors_rejected_by_buyer_gate(name):
    ok, reason = check_lead_name(name)
    assert ok is False, reason


@pytest.mark.parametrize(
    "name",
    [
        "Fetch Robotics",
        "Agility Robotics",
        "MiR",
    ],
)
def test_is_valid_lead_oem_mode(name):
    tc = classify(name)
    ok, reason = is_valid_lead(name, entity_hint=tc, mode="oem_prospect")
    assert ok is True, reason


@pytest.mark.parametrize(
    "name",
    [
        "Distribution Centers Turn",
        "Your Warehouse",
        "7 Best Robot Vacuums",
    ],
)
def test_headline_junk_still_rejected_in_oem_mode(name):
    ok, reason = check_oem_prospect_name(name)
    assert ok is False, reason


def test_enrich_vendors_mentioned_in_article(db_session):
    from app.services.oem_discovery import enrich_vendors_mentioned_in_article

    text = (
        "Sysco Corporation announced it will deploy Fetch Robotics AMRs across "
        "three distribution centers after a successful pilot with Locus Robotics."
    )
    count = enrich_vendors_mentioned_in_article(
        db_session,
        text,
        article_url="https://example.com/sysco-fetch",
    )
    assert count >= 1

    names = {
        row.company_name.lower()
        for row in db_session.query(RobotCompany).all()
    }
    assert "fetch robotics" in names or "locus robotics" in names
