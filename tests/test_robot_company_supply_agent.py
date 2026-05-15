import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.robot_companies import (
    _create_crm_supply_tracking_copy,
    _create_supply_outreach_record,
    _contact_strategy,
    _extract_contact_research,
    _request_emails,
    _research_robot_company_contacts,
    _supply_outreach_history,
    _vendor_signup_email,
)
from app.models.crm import CrmAccount
from app.models.outreach import OutreachMessage
from app.database import Base
import app.models  # noqa: F401 - register SQLAlchemy models


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


class _RobotCompany:
    company_name = "DexMate Robotics"


def test_vendor_signup_email_only_mentions_three_matches():
    matches = [
        {
            "company_name": f"Buyer {i}",
            "industry": "Unknown" if i == 1 else "Logistics",
            "why_match": "Relevant market signal: AMR workflow.",
            "signal": 'Pilot update <a href="https://news.google.com/rss/articles/abc">read more</a>',
        }
        for i in range(1, 6)
    ]

    email = _vendor_signup_email(_RobotCompany(), matches)

    assert "Buyer 1" in email["body"]
    assert "Buyer 2" in email["body"]
    assert "Buyer 3" in email["body"]
    assert "Buyer 4" not in email["body"]
    assert "Buyer 5" not in email["body"]
    assert "I am Cal with Ready For Robots." in email["body"]
    assert "We find automation sales leads and rank them by buying signals" in email["body"]
    assert "two-sided robot automation marketplace" not in email["body"]
    assert "Preformatted response sequence" not in email["body"]
    assert "<a href=" not in email["body"]
    assert "https://news.google.com" not in email["body"]
    assert "Buyer 1 (Unknown)" not in email["body"]
    assert "I am not assuming each one is a fit." in email["body"]
    assert "Cal\nRobot Automation Team" in email["body"]
    assert "Ready For Robots account" in email["body"]
    assert "15-minute call" in email["body"]


def test_contact_strategy_infers_role_email_from_website_not_url():
    company = _RobotCompany()
    company.website = "https://www.unitree.com"
    company.partnerships_contact = None
    company.sales_contact = None
    company.contact_email = None

    strategy = _contact_strategy(company)

    assert strategy["primary"]["contact"] == "partnerships@unitree.com"
    assert strategy["primary"]["source"] == "domain_inferred"
    assert strategy["primary"]["needs_verification"] is True
    assert "https://www.unitree.com" not in [target["contact"] for target in strategy["targets"]]
    assert strategy["recommended_to"] == [
        "partnerships@unitree.com",
        "events@unitree.com",
        "marketing@unitree.com",
        "sales@unitree.com",
    ]


def test_contact_strategy_adds_decision_maker_email_patterns():
    company = _RobotCompany()
    company.website = "https://www.dexmate.ai"
    company.partnerships_contact = "Jane Smith, Head of Partnerships"
    company.sales_contact = None
    company.contact_email = None

    strategy = _contact_strategy(company)

    assert "partnerships@dexmate.ai" in strategy["recommended_to"]
    assert "jane.smith@dexmate.ai" in strategy["recommended_to"]
    assert "jsmith@dexmate.ai" in strategy["recommended_to"]
    assert "smith@dexmate.ai" in strategy["recommended_to"]
    assert "jane@dexmate.ai" in strategy["recommended_to"]


def test_contact_research_extracts_decision_maker_and_linkedin():
    html = """
    <html><body>
      <section>Jane Smith Head of Partnerships leads channel strategy.</section>
      <a href="https://www.linkedin.com/in/jane-smith/">Jane Smith</a>
    </body></html>
    """

    research = _extract_contact_research(html, "https://dexmate.ai/team")

    assert research["decision_makers"][0]["first_name"] == "Jane"
    assert research["decision_makers"][0]["last_name"] == "Smith"
    assert research["decision_makers"][0]["title"] == "Head Of Partnerships"
    assert "https://www.linkedin.com/in/jane-smith" in research["linkedin_urls"]


def test_contact_strategy_uses_website_research_names():
    company = _RobotCompany()
    company.website = "https://www.dexmate.ai"
    company.partnerships_contact = None
    company.sales_contact = None
    company.contact_email = None

    strategy = _contact_strategy(
        company,
        {
            "status": "found",
            "decision_makers": [
                {"first_name": "Jane", "last_name": "Smith", "title": "Head of Partnerships"}
            ],
            "sources": ["https://www.dexmate.ai/team"],
            "linkedin_urls": ["https://www.linkedin.com/in/jane-smith"],
        },
    )

    assert "jane.smith@dexmate.ai" in strategy["recommended_to"]
    assert strategy["communication_policy"]["research_status"] == "found"
    assert strategy["communication_policy"]["researched_decision_makers"][0]["title"] == "Head of Partnerships"


def test_contact_research_can_be_disabled():
    company = _RobotCompany()
    company.website = "https://www.dexmate.ai"

    research = _research_robot_company_contacts(company, enabled=False)

    assert research["status"] == "skipped"
    assert research["decision_makers"] == []


def test_request_emails_splits_and_dedupes_policy_recipients():
    emails = _request_emails(
        "partnerships@unitree.com, events@unitree.com; partnerships@unitree.com"
    )

    assert emails == ["partnerships@unitree.com", "events@unitree.com"]


def test_supply_outreach_record_history_tracks_approval(db_session):
    company = _RobotCompany()
    company.id = 101
    message = _create_supply_outreach_record(
        db_session,
        company,
        to_emails=["partnerships@unitree.com", "events@unitree.com"],
        subject="3 buyer leads for Unitree",
        body="Review these buyer matches.",
        template_type="supply_pipeline",
        status="draft_approved",
        payload={"operator_checkpoint": "approved"},
    )
    db_session.commit()

    history = _supply_outreach_history(db_session, 101)

    assert str(message.id) == history[0]["id"]
    assert history[0]["status"] == "draft_approved"
    assert history[0]["to_emails"] == ["partnerships@unitree.com", "events@unitree.com"]
    assert history[0]["approved_at"] is not None


def test_supply_send_creates_crm_tracking_copy(db_session):
    user_id = "a1111111-1111-4111-8111-111111111111"
    company = _RobotCompany()
    company.id = 202
    company.website = "https://dexmate.ai"
    company.target_market = "warehouse"
    supply_message = _create_supply_outreach_record(
        db_session,
        company,
        to_emails=["partnerships@dexmate.ai", "sales@dexmate.ai"],
        subject="3 buyer leads for DexMate",
        body="Review these buyer matches.",
        template_type="supply_pipeline",
        status="sent",
        send_result={"from_email": "outreach@readyforrobots.com", "resend_id": "email_123"},
        payload={"operator_checkpoint": "sent"},
    )
    db_session.flush()

    account, message = _create_crm_supply_tracking_copy(
        db_session,
        company,
        user={"uid": user_id, "email": "operator@example.com"},
        to_emails=["partnerships@dexmate.ai", "sales@dexmate.ai"],
        subject="3 buyer leads for DexMate",
        body="Review these buyer matches.",
        reply_to=supply_message.reply_to,
        send_result={"from_email": "outreach@readyforrobots.com", "resend_id": "email_123"},
        supply_message=supply_message,
    )
    db_session.commit()

    assert db_session.query(CrmAccount).count() == 1
    assert db_session.query(OutreachMessage).count() == 1
    assert account.name == "DexMate Robotics"
    assert account.outreach_stage == "supply_outreach_sent"
    assert message.to_email == "partnerships@dexmate.ai"
    assert message.payload["all_recipients"] == ["partnerships@dexmate.ai", "sales@dexmate.ai"]
    assert message.payload["supply_outreach_message_id"] == str(supply_message.id)
