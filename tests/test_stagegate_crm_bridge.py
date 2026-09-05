"""Tests for StageGate robot_companies ↔ Cal CRM bridge."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.company import Company
from app.models.crm import CrmAccount
from app.models.robot_company import RobotCompany
from app.models.score import Score
from app.services.semantic_frame import parse_news_semantic_frame
from app.services.stagegate_crm_bridge import (
    build_stagegate_draft,
    cal_draft_for_stagegate_company,
    is_stagegate_company,
    sync_robot_company_to_crm,
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


AMAZON_FRAME = parse_news_semantic_frame(
    "Figure AI is planning CES debut of new humanoid, reducing setup time by 40%."
).to_dict()


def test_sync_creates_company_score_and_crm_account(db_session):
    rc = RobotCompany(
        company_name="Figure AI",
        robot_type="humanoid",
        lead_score=78,
        priority_tier="hot",
        data_source="stagegate_oem_xbot",
        next_trade_show="CES",
        market_intelligence={
            "semantic_frame": AMAZON_FRAME,
            "semantic_summary": "Figure AI · plan → humanoid",
            "stagegate_oem": {"oem_need_score": 78, "icp": "Foreign Humanoid / Exoskeleton"},
        },
    )
    db_session.add(rc)
    db_session.flush()

    result = sync_robot_company_to_crm(db_session, rc, refresh_draft=True)
    db_session.commit()

    assert result["synced"] is True
    company = db_session.query(Company).filter(Company.id == result["company_id"]).one()
    assert is_stagegate_company(company)
    assert company.crm_metadata["robot_company_id"] == rc.id
    assert company.crm_metadata["semantic_frame"]["actor"] == "Figure AI"

    score = db_session.query(Score).filter(Score.company_id == company.id).one()
    assert score.overall_intent_score >= 78

    acct = db_session.query(CrmAccount).filter(CrmAccount.company_id == company.id).one()
    assert acct.account_type == "vendor"
    assert acct.outreach_draft
    assert "StageGate" in acct.outreach_draft

    db_session.refresh(rc)
    assert rc.market_intelligence["crm_company_id"] == company.id


def test_cal_and_supply_share_same_stagegate_draft(db_session):
    rc = RobotCompany(
        company_name="German Bionic",
        robot_type="humanoid",
        lead_score=65,
        priority_tier="warm",
        data_source="stagegate_oem_xbot",
        market_intelligence={
            "semantic_frame": AMAZON_FRAME,
            "semantic_summary": "German Bionic · CES humanoid",
            "stagegate_oem": {"oem_need_score": 65},
        },
    )
    db_session.add(rc)
    db_session.flush()
    sync_robot_company_to_crm(db_session, rc, refresh_draft=True)
    db_session.commit()

    company = db_session.query(Company).filter(Company.name == "German Bionic").one()
    supply_draft = build_stagegate_draft(rc, company=company)
    cal_draft = cal_draft_for_stagegate_company(company)

    assert supply_draft["body"] == cal_draft["body"]
    assert "pre-floor" in cal_draft["subject"].lower() or "Yaskawa" in cal_draft["subject"] or "German Bionic" in cal_draft["subject"]
    assert "onstage.bot" in cal_draft["body"]
    assert "Ready For Robots" not in cal_draft["body"]
