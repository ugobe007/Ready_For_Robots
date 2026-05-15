import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.robot_companies import (
    _create_crm_supply_tracking_copy,
    _create_supply_outreach_record,
    _contact_strategy,
    _extract_contact_research,
    _reply_domain,
    _request_emails,
    _research_robot_company_contacts,
    _vendor_allows_logistics,
    _supply_reply_address,
    _supply_outreach_history,
    _vendor_signup_email,
)
from app.api.webhooks import _capture_delivery_event
from app.models.crm import CrmAccount
from app.models.outreach import OutreachMessage
from app.models.supply_outreach import SupplyOutreachMessage
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
    assert "ReadyBot" not in email["body"]
    assert "We find automation sales leads and rank them by buying signals" in email["body"]
    assert "search engine for your sales pipeline" in email["body"]
    assert "exact signal trail behind every lead" in email["body"]
    assert "If the signal logic is weak, we will say so." in email["body"]
    assert "onstage.bot" not in email["body"]
    assert "physical staging" not in email["body"]
    assert "Sales Channel & Lead Generation Strategy Call" in email["body"]
    assert "secure warehousing, staging" not in email["body"]
    assert "two-sided robot automation marketplace" not in email["body"]
    assert "Preformatted response sequence" not in email["body"]
    assert "<a href=" not in email["body"]
    assert "https://news.google.com" not in email["body"]
    assert "Buyer 1 (Unknown)" not in email["body"]
    assert "I am not assuming each one is a fit." in email["body"]
    assert "Cal\nRobot Automation Team" in email["body"]
    assert "sales channel strategy" in email["body"]


def test_vendor_logistics_requires_explicit_vendor_fit():
    company = _RobotCompany()
    company.robot_type = "humanoid"
    company.product_category = None
    company.target_market = "manufacturing"

    assert _vendor_allows_logistics(company) is False

    company.target_market = "warehouse logistics"

    assert _vendor_allows_logistics(company) is True


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


def test_supply_reply_domain_normalizes_full_sender(monkeypatch):
    monkeypatch.setenv("SCOUT_REPLY_DOMAIN", "Ready For Robots <outreach@readyforrobots.com>")
    monkeypatch.setenv("SUPPLY_REPLY_LOCAL_PART", "supply")

    assert _reply_domain() == "readyforrobots.com"
    assert _supply_reply_address("abc123") == "supply+abc123@readyforrobots.com"


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


def test_supply_outreach_history_includes_delivery_tracking(db_session):
    company = _RobotCompany()
    company.id = 303
    message = _create_supply_outreach_record(
        db_session,
        company,
        to_emails=["partnerships@unitree.com"],
        subject="3 buyer leads for Unitree",
        body="Review these buyer matches.",
        template_type="supply_pipeline",
        status="sent",
        send_result={"resend_id": "re_unitree_123", "from_email": "outreach@readyforrobots.com"},
        payload={"delivery_status": "delivered", "delivered_at": "2026-05-15T12:00:00+00:00"},
    )
    db_session.commit()

    history = _supply_outreach_history(db_session, 303)

    assert str(message.id) == history[0]["id"]
    assert history[0]["delivery_status"] == "delivered"
    assert history[0]["delivered_at"] == "2026-05-15T12:00:00+00:00"


def test_resend_delivery_event_updates_supply_message(db_session):
    company = _RobotCompany()
    company.id = 404
    message = _create_supply_outreach_record(
        db_session,
        company,
        to_emails=["partnerships@unitree.com"],
        subject="3 buyer leads for Unitree",
        body="Review these buyer matches.",
        template_type="supply_pipeline",
        status="sent",
        send_result={"resend_id": "re_delivery_123", "from_email": "outreach@readyforrobots.com"},
    )
    db_session.commit()

    result = _capture_delivery_event(
        db_session,
        "email.delivered",
        {"email_id": "re_delivery_123", "to": ["partnerships@unitree.com"]},
    )
    db_session.refresh(message)

    assert result["status"] == "delivered"
    assert message.status == "delivered"
    assert message.payload["delivery_status"] == "delivered"
    assert message.payload["delivered_at"]


def test_bounce_event_resends_to_alternate_role_inbox(db_session, monkeypatch):
    company = _RobotCompany()
    company.id = 505
    message = _create_supply_outreach_record(
        db_session,
        company,
        to_emails=["partnerships@unitree.com"],
        subject="3 buyer leads for Unitree",
        body="Review these buyer matches.",
        template_type="supply_pipeline",
        status="sent",
        send_result={"resend_id": "re_bounce_123", "from_email": "outreach@readyforrobots.com"},
    )
    db_session.commit()

    def fake_send(**kwargs):
        assert kwargs["to_email"] == "events@unitree.com"
        return {"resend_id": "re_resend_456", "from_email": "outreach@readyforrobots.com", "to": [kwargs["to_email"]]}

    monkeypatch.setattr("app.api.webhooks.send_email_via_resend", fake_send)

    result = _capture_delivery_event(
        db_session,
        "email.bounced",
        {"email_id": "re_bounce_123", "to": ["partnerships@unitree.com"], "reason": "mailbox not found"},
    )
    db_session.refresh(message)
    resent = db_session.query(SupplyOutreachMessage).filter(SupplyOutreachMessage.resend_id == "re_resend_456").first()

    assert result["status"] == "bounced"
    assert message.status == "bounced"
    assert message.payload["automated_resend_to"] == "events@unitree.com"
    assert "Resent to events@unitree.com" in message.payload["cal_delivery_action"]
    assert resent is not None
    assert resent.status == "resent"


def test_crm_bounce_event_resends_to_alternate_buyer_inbox(db_session, monkeypatch):
    team_id = "b1111111-1111-4111-8111-111111111111"
    account_id = "b2222222-2222-4222-8222-222222222222"
    user_id = "b3333333-3333-4333-8333-333333333333"
    message = OutreachMessage(
        id="b4444444-4444-4444-8444-444444444444",
        team_id=team_id,
        crm_account_id=account_id,
        sender_user_id=user_id,
        to_email="buyer@example.com",
        from_email="outreach@readyforrobots.com",
        reply_to="reply+crm_token@readyforrobots.com",
        reply_token="crm_token",
        subject="Automation opportunity",
        body_text="Worth comparing automation options?",
        send_identity="scout",
        resend_id="re_crm_bounce_123",
        status="sent",
        payload={},
    )
    db_session.add(message)
    db_session.commit()

    def fake_send(**kwargs):
        assert kwargs["to_email"] == "operations@example.com"
        assert kwargs["reply_to"] == "reply+crm_token-r1@readyforrobots.com"
        return {"resend_id": "re_crm_resend_456", "from_email": "outreach@readyforrobots.com", "to": [kwargs["to_email"]]}

    monkeypatch.setattr("app.api.webhooks.send_email_via_resend", fake_send)

    result = _capture_delivery_event(
        db_session,
        "email.bounced",
        {"email_id": "re_crm_bounce_123", "to": ["buyer@example.com"], "reason": "mailbox not found"},
    )
    db_session.refresh(message)
    resent = db_session.query(OutreachMessage).filter(OutreachMessage.resend_id == "re_crm_resend_456").first()

    assert result["status"] == "bounced"
    assert message.status == "bounced"
    assert message.payload["automated_resend_to"] == "operations@example.com"
    assert "Resent to operations@example.com" in message.payload["cal_delivery_action"]
    assert resent is not None
    assert resent.status == "resent"


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
