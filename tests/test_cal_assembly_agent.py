"""Cal Assembly Agent — pre-send curation and review."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.robot_companies import _vendor_signup_email
from app.database import Base
from app.models.company import Company
from app.models.score import Score
from app.models.signal import Signal
from app.services.cal_assembly_agent import (
    assemble_supply_outreach,
    cal_assembly_required,
    curate_supply_matches,
)
from app.services.cal_persona import cal_persona_payload
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


class _Vendor:
    company_name = "AUBO Robotics"
    robot_type = "cobot"
    target_market = "manufacturing"
    product_category = None
    data_source = None
    market_intelligence = {}


def test_cal_persona_has_mission_and_never_rules():
    payload = cal_persona_payload()
    assert payload["name"] == "Cal"
    assert "sign up" in payload["mission"].lower()
    assert any("universit" in n.lower() for n in payload["never"])


def test_assembly_rejects_stagegate_voice_in_supply_body(db_session):
    vendor = _Vendor()
    matches = [
        {
            "id": 1,
            "company_name": "Harbor Fresh Foods",
            "industry": "Food Service",
            "why_match": "Relevant market signal: cobot.",
            "signal": "Harbor Fresh Foods expands packaging line due to labor shortage.",
        },
        {
            "id": 2,
            "company_name": "Motive",
            "industry": "Manufacturing",
            "why_match": "Relevant market signal: industrial.",
            "signal": "Motive invests in factory automation and cobot assembly.",
        },
    ]
    good = Company(
        id=1,
        name="Harbor Fresh Foods",
        industry="Food Service",
        is_internal=True,
    )
    good.signals = [
        Signal(
            company_id=1,
            signal_type="labor_shortage",
            signal_text="Harbor Fresh Foods expands packaging line due to labor shortage.",
            signal_strength=0.8,
        )
    ]
    good.scores = [Score(company_id=1, overall_intent_score=78.0)]
    motive = Company(
        id=2,
        name="Motive",
        industry="Automotive & Manufacturing",
        is_internal=True,
    )
    motive.signals = [
        Signal(
            company_id=2,
            signal_type="capex",
            signal_text="Motive invests in factory automation and cobot assembly.",
            signal_strength=0.75,
        )
    ]
    motive.scores = [Score(company_id=2, overall_intent_score=76.0)]
    db_session.add_all([good, motive])
    db_session.commit()

    draft = _vendor_signup_email(vendor, matches, force_rfr=True)
    bad_body = draft["body"] + "\n\nVisit onstage.bot for booth staging."

    result = assemble_supply_outreach(
        db_session,
        vendor,
        matches,
        subject=draft["subject"],
        body=bad_body,
        min_matches=2,
    )
    assert result.approved is False
    assert any("onstage" in i.lower() for i in result.issues)


def test_curate_drops_uc_davis_research(db_session):
    vendor = _Vendor()
    uc = Company(id=10, name="UC Davis", industry="Automotive & Manufacturing", is_internal=True)
    uc.signals = [
        Signal(
            company_id=10,
            signal_type="news",
            signal_text="UC Davis launches study led by nurses on humanoid robots in dementia care.",
            signal_strength=0.7,
        )
    ]
    uc.scores = [Score(company_id=10, overall_intent_score=70.0)]
    db_session.add(uc)
    db_session.commit()

    matches = [
        {
            "id": 10,
            "company_name": "UC Davis",
            "industry": uc.industry,
            "signal": uc.signals[0].signal_text,
        }
    ]
    curated, issues = curate_supply_matches(db_session, vendor, matches, min_matches=1, limit=3)
    assert curated == []
    assert issues


def test_cal_assembly_required_default_on():
    assert cal_assembly_required() is True
