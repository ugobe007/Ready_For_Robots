import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.robot_companies import (
    _create_crm_supply_tracking_copy,
    _create_supply_outreach_record,
    _contact_strategy,
    _curated_vendor_leads,
    _extract_contact_research,
    _match_buyer_leads,
    _reply_domain,
    _request_emails,
    _research_robot_company_contacts,
    _select_supply_batch_matches,
    _prepare_supply_pipeline_copy,
    _supply_buyer_lead_eligible,
    _vendor_allows_logistics,
    _supply_reply_address,
    _supply_outreach_history,
    _vendor_signup_email,
)
from app.models.signal import Signal
from app.models.score import Score
from app.api.webhooks import _capture_delivery_event
from app.models.crm import CrmAccount
from app.models.company import Company
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
    product_category = None


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

    assert email["subject"] == "Buyer matches for DexMate Robotics"
    assert "Buyer 1" in email["body"]
    assert "Buyer 2" in email["body"]
    assert "Buyer 3" in email["body"]
    assert "Buyer 4" not in email["body"]
    assert "Buyer 5" not in email["body"]
    assert "DexMate Robotics" in email["body"]
    assert "PoC" in email["body"] or "PoCs" in email["body"]
    assert "ReadyBot" not in email["body"]
    assert "If the signal is weak" in email["body"]
    assert "onstage.bot" not in email["body"]
    assert "physical staging" not in email["body"]
    assert "Worth 15 minutes" in email["body"]
    assert "secure warehousing, staging" not in email["body"]
    assert "two-sided robot automation marketplace" not in email["body"]
    assert "Preformatted response sequence" not in email["body"]
    assert "<a href=" not in email["body"]
    assert "https://news.google.com" not in email["body"]
    assert "Buyer 1 (Unknown)" not in email["body"]
    assert "I'm not assuming each one is a fit" in email["body"]
    assert "— Cal\nReady For Robots" in email["body"]
    assert "channel strategy" in email["body"]


def test_vendor_logistics_requires_explicit_vendor_fit():
    company = _RobotCompany()
    company.robot_type = "humanoid"
    company.product_category = None
    company.target_market = "manufacturing"

    assert _vendor_allows_logistics(company) is False

    company.target_market = "warehouse logistics"

    assert _vendor_allows_logistics(company) is True


def test_curated_vendor_leads_uses_vendor_specific_diversity():
    warehouse_vendor = _RobotCompany()
    warehouse_vendor.id = 11
    warehouse_vendor.company_name = "WarehouseBot"
    warehouse_vendor.robot_type = "AMR"
    warehouse_vendor.target_market = "warehouse logistics"
    service_vendor = _RobotCompany()
    service_vendor.id = 22
    service_vendor.company_name = "ServiceBot"
    service_vendor.robot_type = "service"
    service_vendor.target_market = "hospitality"
    rows = [
        {"id": 1, "company_name": "Hotel One", "industry": "Hospitality", "fit_score": 90, "signal_strength": 70, "overlap_count": 1, "vendor_tiebreak": 0.1, "lead_terms": ["hospitality"]},
        {"id": 2, "company_name": "Hotel Two", "industry": "Hospitality", "fit_score": 89, "signal_strength": 69, "overlap_count": 1, "vendor_tiebreak": 0.2, "lead_terms": ["hospitality"]},
        {"id": 3, "company_name": "Warehouse One", "industry": "Logistics", "fit_score": 88, "signal_strength": 68, "overlap_count": 1, "vendor_tiebreak": 0.3, "lead_terms": ["warehouse"]},
        {"id": 4, "company_name": "Factory One", "industry": "Manufacturing", "fit_score": 87, "signal_strength": 67, "overlap_count": 1, "vendor_tiebreak": 0.4, "lead_terms": ["manufacturing"]},
        {"id": 5, "company_name": "Retail One", "industry": "Retail", "fit_score": 86, "signal_strength": 66, "overlap_count": 1, "vendor_tiebreak": 0.5, "lead_terms": ["retail"]},
    ]

    warehouse_ids = [row["id"] for row in _curated_vendor_leads(warehouse_vendor, rows, 3)]
    service_ids = [row["id"] for row in _curated_vendor_leads(service_vendor, rows, 3)]

    assert warehouse_ids != service_ids
    assert 3 in warehouse_ids
    assert 1 in service_ids


def test_match_buyer_leads_differs_by_robot_vendor_fit(db_session):
    companies = [
        Company(id=1001, name="Marriott", industry="Hospitality", sub_industry="hotel operations", is_internal=True, crm_metadata={"automation_requirements": ["service"]}),
        Company(id=1002, name="DHL", industry="Logistics", sub_industry="warehouse fulfillment", is_internal=True, crm_metadata={"automation_requirements": ["warehouse"]}),
        Company(id=1003, name="Toyota", industry="Manufacturing", sub_industry="factory production", is_internal=True, crm_metadata={"automation_requirements": ["assembly"]}),
        Company(id=1004, name="Target", industry="Retail", sub_industry="store operations", is_internal=True, crm_metadata={"automation_requirements": ["service"]}),
    ]
    signal_rows = [
        (1001, "labor_shortage", "Marriott expands hotel service robotics pilot due to housekeeping labor shortage.", 78.0),
        (1002, "labor_shortage", "DHL opens new warehouse and seeks AMR automation for fulfillment labor shortage.", 80.0),
        (1003, "capex", "Toyota factory capex includes assembly line cobot automation budget.", 76.0),
        (1004, "labor_shortage", "Target store operations team evaluates service robot deployment for backroom labor gap.", 77.0),
    ]
    for company_id, sig_type, text, overall in signal_rows:
        companies[company_id - 1001].signals = [
            Signal(company_id=company_id, signal_type=sig_type, signal_text=text, signal_strength=0.8)
        ]
        companies[company_id - 1001].scores = [Score(company_id=company_id, overall_intent_score=overall)]
    db_session.add_all(companies)
    db_session.commit()
    service_vendor = _RobotCompany()
    service_vendor.id = 701
    service_vendor.company_name = "ServiceBot"
    service_vendor.robot_type = "service"
    service_vendor.target_market = "hospitality retail"
    warehouse_vendor = _RobotCompany()
    warehouse_vendor.id = 702
    warehouse_vendor.company_name = "WarehouseBot"
    warehouse_vendor.robot_type = "AMR"
    warehouse_vendor.target_market = "warehouse logistics"

    service_matches = _match_buyer_leads(db_session, service_vendor, limit=3)
    warehouse_matches = _match_buyer_leads(db_session, warehouse_vendor, limit=3)

    assert [m["id"] for m in service_matches] != [m["id"] for m in warehouse_matches]
    assert {m["company_name"] for m in service_matches}.intersection({"Marriott", "Target"})
    assert {m["company_name"] for m in warehouse_matches}.intersection({"DHL"})


def test_match_buyer_leads_excludes_off_domain_high_score_buyer(db_session):
    """A high-intent buyer in an unrelated domain must not be cited to a vendor.

    An airline trialing humanoids scores high but has no AMR/warehouse fit — citing it to
    a warehouse AMR vendor is the mismatch that got blocked at assembly.
    """
    airline = Company(
        id=3001,
        name="Japan Airlines",
        industry="Airports & Aviation",
        sub_industry="passenger aviation",
        is_internal=True,
    )
    airline.signals = [
        Signal(
            company_id=3001,
            signal_type="news",
            signal_text="Japan Airlines trials humanoid robots at Haneda for passenger assistance.",
            signal_strength=0.9,
        )
    ]
    airline.scores = [Score(company_id=3001, overall_intent_score=95.0)]

    warehouse_buyer = Company(
        id=3002,
        name="Nimbus Fulfillment",
        industry="Logistics",
        sub_industry="warehouse fulfillment",
        is_internal=True,
        crm_metadata={"automation_requirements": ["warehouse"]},
    )
    warehouse_buyer.signals = [
        Signal(
            company_id=3002,
            signal_type="labor_shortage",
            signal_text="Nimbus Fulfillment opens a warehouse and seeks AMR automation for fulfillment labor shortage.",
            signal_strength=0.8,
        )
    ]
    warehouse_buyer.scores = [Score(company_id=3002, overall_intent_score=80.0)]

    db_session.add_all([airline, warehouse_buyer])
    db_session.commit()

    amr_vendor = _RobotCompany()
    amr_vendor.id = 801
    amr_vendor.company_name = "Geek Plus"
    amr_vendor.robot_type = "AMR"
    amr_vendor.target_market = "warehouse logistics"

    names = {m["company_name"] for m in _match_buyer_leads(db_session, amr_vendor, limit=5)}
    assert "Nimbus Fulfillment" in names
    assert "Japan Airlines" not in names


def test_supply_buyer_lead_eligible_rejects_vendors_and_research(db_session):
    cobot_vendor = _RobotCompany()
    cobot_vendor.robot_type = "cobot"
    cobot_vendor.target_market = "manufacturing"

    brain = Company(
        id=2001,
        name="Brain Corp",
        industry="Datacenters",
        is_internal=True,
    )
    uc_davis = Company(
        id=2002,
        name="UC Davis",
        industry="Automotive & Manufacturing",
        is_internal=True,
    )
    uc_davis.signals = [
        Signal(
            company_id=2002,
            signal_type="news",
            signal_text=(
                "UC Davis launches first long-term U.S. study led by nurses on humanoid robots "
                "in dementia care - University of California - Davis"
            ),
            signal_strength=0.7,
        )
    ]
    uc_davis.scores = [Score(company_id=2002, overall_intent_score=72.0)]
    good = Company(
        id=2003,
        name="Harbor Fresh Foods",
        industry="Food Service",
        is_internal=True,
        crm_metadata={"automation_requirements": ["assembly", "production"]},
    )
    good.signals = [
        Signal(
            company_id=2003,
            signal_type="labor_shortage",
            signal_text="Harbor Fresh Foods expands production line and seeks cobot automation for packaging due to labor shortage.",
            signal_strength=0.8,
        )
    ]
    good.scores = [Score(company_id=2003, overall_intent_score=78.0)]
    db_session.add_all([brain, uc_davis, good])
    db_session.commit()

    assert _supply_buyer_lead_eligible(brain, cobot_vendor)[0] is False
    assert _supply_buyer_lead_eligible(uc_davis, cobot_vendor)[0] is False
    assert _supply_buyer_lead_eligible(good, cobot_vendor)[0] is True

    matches = _match_buyer_leads(db_session, cobot_vendor, limit=5)
    names = {m["company_name"] for m in matches}
    assert "Brain Corp" not in names
    assert "UC Davis" not in names


def test_supply_batch_matches_prefer_unused_buyer_leads():
    matches = [{"id": i, "company_name": f"Buyer {i}"} for i in range(1, 8)]

    first = _select_supply_batch_matches(matches, set(), limit=3)
    used = {match["id"] for match in first}
    second = _select_supply_batch_matches(matches, used, limit=3)

    assert [match["id"] for match in first] == [1, 2, 3]
    assert [match["id"] for match in second] == [4, 5, 6]


def test_supply_batch_matches_falls_back_when_unused_pool_is_short():
    matches = [{"id": i, "company_name": f"Buyer {i}"} for i in range(1, 5)]

    selected = _select_supply_batch_matches(matches, {1, 2, 3}, limit=3)

    assert [match["id"] for match in selected] == [4, 1, 2]


def test_supply_pipeline_copy_forces_company_specific_subject():
    company = _RobotCompany()
    company.company_name = "Agility Robotics"

    subject, body = _prepare_supply_pipeline_copy(
        company,
        "Sales channel signals for Unitree Robotics",
        "Hello Agility Robotics team,\n\nI came across buyer signals.",
    )

    assert subject == "Sales channel signals for Agility Robotics"
    assert "Agility Robotics" in body


def test_supply_pipeline_copy_rejects_stale_body_company():
    company = _RobotCompany()
    company.company_name = "Agility Robotics"

    with pytest.raises(Exception) as exc:
        _prepare_supply_pipeline_copy(
            company,
            "Sales channel signals for Unitree Robotics",
            "Hello Unitree Robotics team,\n\nI came across buyer signals.",
        )

    assert "Body/company mismatch" in str(exc.value)


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
        "sales@unitree.com",
        "marketing@unitree.com",
    ]


def test_contact_strategy_adds_decision_maker_email_patterns():
    company = _RobotCompany()
    company.website = "https://www.dexmate.ai"
    company.partnerships_contact = "Jane Smith, Head of Partnerships"
    company.sales_contact = None
    company.contact_email = None

    strategy = _contact_strategy(company)

    assert "partnerships@dexmate.ai" in [t["contact"] for t in strategy["targets"]]
    assert "sales@dexmate.ai" in strategy["recommended_to"]
    assert "marketing@dexmate.ai" in strategy["recommended_to"]
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


def test_crm_bounce_event_does_not_resend_to_guessed_inbox(db_session, monkeypatch):
    # Hardened: a buyer bounce must NOT auto-resend to a guessed role inbox
    # (operations@/info@…) — guessed mailboxes create bounce loops. Cal only
    # contacts verified addresses; on bounce it records the problem and notifies.
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
        raise AssertionError("bounce must not trigger a guessed-inbox resend")

    monkeypatch.setattr("app.api.webhooks.send_email_via_resend", fake_send)

    result = _capture_delivery_event(
        db_session,
        "email.bounced",
        {"email_id": "re_crm_bounce_123", "to": ["buyer@example.com"], "reason": "mailbox not found"},
    )
    db_session.refresh(message)

    assert result["status"] == "bounced"
    assert message.status == "bounced"
    assert "automated_resend_to" not in message.payload
    assert "no unused alternate" in message.payload["cal_delivery_action"]
    # No resent message row created.
    resent = (
        db_session.query(OutreachMessage)
        .filter(OutreachMessage.payload["source"].astext == "crm_auto_resend")
        .first()
    )
    assert resent is None


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
