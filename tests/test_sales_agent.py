import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa: F401 - register SQLAlchemy models
from app.models.crm import CrmAccount, Team
from app.models.outreach import OutreachMessage, OutreachReply
from app.models.sales_agent import SalesAgentAction, SalesMessage, SalesOpportunity
from app.models.supply_outreach import SupplyOutreachMessage, SupplyOutreachReply
from app.services import sales_agent
from app.services.sales_agent import (
    classify_sales_intent,
    create_automated_next_action,
    handle_crm_reply_first_response,
    handle_supply_reply_first_response,
    plan_sales_reply,
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


def test_classify_sales_intent_detects_pricing_and_meeting():
    assert classify_sales_intent("Can you send pricing and budget ranges?") == "pricing_request"
    assert classify_sales_intent("Can we schedule a demo next week?") == "meeting_requested"


def test_plan_sales_reply_automates_first_reply_without_approval():
    plan = plan_sales_reply(
        opportunity_title="DexMate opportunity",
        inbound_text="Can you send pricing?",
        inbound_subject="Pricing",
        sender_email="buyer@example.com",
    )

    assert plan.detected_intent == "pricing_request"
    assert plan.stage_after == "quote_requested"
    assert plan.action_type == "automated_first_reply"
    assert plan.requires_approval is False
    assert "Pricing depends on deployment scope" in plan.draft_body


def test_plan_sales_reply_routes_technical_questions_to_max():
    plan = plan_sales_reply(
        opportunity_title="DexMate opportunity",
        inbound_text="Can you share payload specs and API integration details?",
        inbound_subject="Technical specs",
        sender_email="buyer@example.com",
    )

    assert plan.detected_intent == "technical_specs_request"
    assert plan.stage_after == "needs_info"
    assert plan.payload["responder_persona"] == "max"
    assert plan.payload["copied_by"] == "cal"
    assert plan.payload["management_escalation_required"] is False
    assert "Cal copied me on this" in plan.draft_body
    assert "Max\nTechnical Support Lead" in plan.draft_body


def test_plan_sales_reply_escalates_risky_technical_questions_to_management():
    plan = plan_sales_reply(
        opportunity_title="DexMate opportunity",
        inbound_text="Can you guarantee ISO compliance and final specs for our custom API?",
        inbound_subject="Compliance question",
        sender_email="buyer@example.com",
    )

    assert plan.detected_intent == "technical_specs_request"
    assert plan.stage_after == "technical_escalation"
    assert plan.risk_level == "medium"
    assert plan.payload["management_escalation_required"] is True
    assert "checking with management" in plan.draft_body
    assert "rather than guess" in plan.draft_body


def test_handle_crm_reply_sends_and_tracks_first_reply(db_session, monkeypatch):
    sent = {}

    def fake_send_email(**kwargs):
        sent.update(kwargs)
        return {
            "resend_id": "email_test",
            "from_email": "scout@readyforrobots.com",
            "to": [kwargs["to_email"]],
            "reply_to": kwargs.get("reply_to"),
        }

    monkeypatch.setattr(sales_agent, "send_email_via_resend", fake_send_email)
    team_uuid = uuid.uuid4()
    account_uuid = uuid.uuid4()
    team_id = str(team_uuid)
    account_id = str(account_uuid)
    msg_id = str(uuid.uuid4())
    reply_id = str(uuid.uuid4())
    db_session.add(Team(id=team_uuid, name="Ready For Robots"))
    account = CrmAccount(id=account_uuid, team_id=team_uuid, name="DexMate", outreach_stage="sent")
    msg = OutreachMessage(
        id=msg_id,
        team_id=team_id,
        crm_account_id=account_id,
        to_email="buyer@example.com",
        reply_token="reply-token",
        subject="Ready For Robots intro",
        body_text="Initial outreach",
        reply_to="reply+reply-token@readyforrobots.com",
        status="sent",
    )
    reply = OutreachReply(
        id=reply_id,
        outreach_message_id=msg_id,
        team_id=team_id,
        crm_account_id=account_id,
        from_email="buyer@example.com",
        to_email="reply+reply-token@readyforrobots.com",
        subject="Re: Ready For Robots intro",
        body_text="Can you send pricing?",
    )
    db_session.add_all([account, msg, reply])
    db_session.commit()

    action = handle_crm_reply_first_response(db_session, msg, reply, account)
    db_session.commit()

    assert action.status == "sent"
    assert action.detected_intent == "pricing_request"
    assert sent["to_email"] == "buyer@example.com"
    opportunity = db_session.query(SalesOpportunity).one()
    assert opportunity.current_stage == "quote_requested"
    assert db_session.query(SalesMessage).count() == 2
    assert db_session.query(SalesAgentAction).count() == 1


def test_handle_supply_reply_attaches_visible_team_opportunity(db_session, monkeypatch):
    sent = {}

    def fake_send_email(**kwargs):
        sent.update(kwargs)
        return {
            "resend_id": "email_supply",
            "from_email": "outreach@readyforrobots.com",
            "to": [kwargs["to_email"]],
            "reply_to": kwargs.get("reply_to"),
        }

    monkeypatch.setattr(sales_agent, "send_email_via_resend", fake_send_email)
    team_uuid = uuid.uuid4()
    owner_uuid = uuid.uuid4()
    db_session.add(Team(id=team_uuid, name="Ready For Robots"))
    msg = SupplyOutreachMessage(
        id=str(uuid.uuid4()),
        robot_company_id=202,
        to_emails=["partnerships@robotco.com"],
        reply_token="supply-token",
        reply_to="supply+supply-token@readyforrobots.com",
        subject="Sales channel signals for RobotCo",
        body_text="Hello RobotCo team",
        status="replied",
    )
    reply = SupplyOutreachReply(
        id=str(uuid.uuid4()),
        supply_outreach_message_id=msg.id,
        robot_company_id=202,
        from_email="partnerships@robotco.com",
        to_email=msg.reply_to,
        subject="Re: Sales channel signals for RobotCo",
        body_text="Can we schedule a call?",
    )
    db_session.add_all([msg, reply])
    db_session.commit()

    action = handle_supply_reply_first_response(
        db_session,
        msg,
        reply,
        team_id=team_uuid,
        owner_user_id=owner_uuid,
    )
    db_session.commit()

    opportunity = db_session.query(SalesOpportunity).one()
    assert opportunity.team_id == str(team_uuid)
    assert opportunity.owner_user_id == str(owner_uuid)
    assert opportunity.current_stage == "meeting_requested"
    assert action.status == "sent"
    assert sent["to_email"] == "partnerships@robotco.com"


def test_handle_crm_technical_reply_sends_from_max_and_copies_support(db_session, monkeypatch):
    sent = {}

    def fake_send_email(**kwargs):
        sent.update(kwargs)
        return {
            "resend_id": "email_tech",
            "from_email": "outreach@readyforrobots.com",
            "to": [kwargs["to_email"]],
            "cc": kwargs.get("cc") or [],
            "reply_to": kwargs.get("reply_to"),
        }

    monkeypatch.setenv("MAX_TECH_SUPPORT_EMAIL", "max@readyforrobots.com")
    monkeypatch.setattr(sales_agent, "send_email_via_resend", fake_send_email)
    team_uuid = uuid.uuid4()
    account_uuid = uuid.uuid4()
    team_id = str(team_uuid)
    account_id = str(account_uuid)
    msg_id = str(uuid.uuid4())
    reply_id = str(uuid.uuid4())
    db_session.add(Team(id=team_uuid, name="Ready For Robots"))
    account = CrmAccount(id=account_uuid, team_id=team_uuid, name="DexMate", outreach_stage="sent")
    msg = OutreachMessage(
        id=msg_id,
        team_id=team_id,
        crm_account_id=account_id,
        to_email="buyer@example.com",
        reply_token="reply-token",
        subject="Ready For Robots intro",
        body_text="Initial outreach",
        reply_to="reply+reply-token@readyforrobots.com",
        status="sent",
    )
    reply = OutreachReply(
        id=reply_id,
        outreach_message_id=msg_id,
        team_id=team_id,
        crm_account_id=account_id,
        from_email="buyer@example.com",
        to_email="reply+reply-token@readyforrobots.com",
        subject="Re: Technical specs",
        body_text="Can you share payload specs and integration API details?",
    )
    db_session.add_all([account, msg, reply])
    db_session.commit()

    action = handle_crm_reply_first_response(db_session, msg, reply, account)
    db_session.commit()

    assert action.status == "sent"
    assert action.detected_intent == "technical_specs_request"
    assert action.payload["responder_persona"] == "max"
    assert sent["from_display_name"] == "Max"
    assert sent["cc"] == ["max@readyforrobots.com"]
    assert "Max\nTechnical Support Lead" in sent["body_text"]


def test_handle_crm_risky_technical_reply_notifies_management(db_session, monkeypatch):
    sent = []

    def fake_send_email(**kwargs):
        sent.append(kwargs)
        return {
            "resend_id": f"email_{len(sent)}",
            "from_email": "outreach@readyforrobots.com",
            "to": kwargs["to_email"] if isinstance(kwargs["to_email"], list) else [kwargs["to_email"]],
            "reply_to": kwargs.get("reply_to"),
        }

    monkeypatch.setenv("ADMIN_EMAILS", "admin@readyforrobots.com")
    monkeypatch.setattr(sales_agent, "send_email_via_resend", fake_send_email)
    team_uuid = uuid.uuid4()
    account_uuid = uuid.uuid4()
    team_id = str(team_uuid)
    account_id = str(account_uuid)
    msg_id = str(uuid.uuid4())
    reply_id = str(uuid.uuid4())
    db_session.add(Team(id=team_uuid, name="Ready For Robots"))
    account = CrmAccount(id=account_uuid, team_id=team_uuid, name="DexMate", outreach_stage="sent")
    msg = OutreachMessage(
        id=msg_id,
        team_id=team_id,
        crm_account_id=account_id,
        to_email="buyer@example.com",
        reply_token="reply-token",
        subject="Ready For Robots intro",
        body_text="Initial outreach",
        status="sent",
    )
    reply = OutreachReply(
        id=reply_id,
        outreach_message_id=msg_id,
        team_id=team_id,
        crm_account_id=account_id,
        from_email="buyer@example.com",
        subject="Re: Compliance",
        body_text="Can you guarantee ISO compliance and final specs for our custom API?",
    )
    db_session.add_all([account, msg, reply])
    db_session.commit()

    action = handle_crm_reply_first_response(db_session, msg, reply, account)
    db_session.commit()

    assert action.status == "sent"
    assert action.payload["management_escalation_required"] is True
    assert action.payload["management_escalation_status"] == "sent"
    assert len(sent) == 2
    assert sent[0]["from_display_name"] == "Max"
    assert sent[1]["to_email"] == ["admin@readyforrobots.com"]
    assert sent[1]["from_display_name"] == "Max"
    assert "Max needs help" in sent[1]["subject"]


def test_handle_crm_reply_only_sends_first_reply_once(db_session, monkeypatch):
    calls = []

    def fake_send_email(**kwargs):
        calls.append(kwargs)
        return {"resend_id": f"email_{len(calls)}", "from_email": "scout@readyforrobots.com"}

    monkeypatch.setattr(sales_agent, "send_email_via_resend", fake_send_email)
    team_uuid = uuid.uuid4()
    account_uuid = uuid.uuid4()
    team_id = str(team_uuid)
    account_id = str(account_uuid)
    db_session.add(Team(id=team_uuid, name="Ready For Robots"))
    account = CrmAccount(id=account_uuid, team_id=team_uuid, name="DexMate")
    msg = OutreachMessage(
        id=str(uuid.uuid4()),
        team_id=team_id,
        crm_account_id=account_id,
        to_email="buyer@example.com",
        reply_token="reply-token",
        subject="Intro",
        body_text="Initial outreach",
        status="sent",
    )
    db_session.add_all([account, msg])
    db_session.commit()

    for body in ["Can we schedule a call?", "Also, send pricing."]:
        reply = OutreachReply(
            id=str(uuid.uuid4()),
            outreach_message_id=msg.id,
            team_id=team_id,
            crm_account_id=account_id,
            from_email="buyer@example.com",
            subject="Re: Intro",
            body_text=body,
        )
        db_session.add(reply)
        db_session.commit()
        handle_crm_reply_first_response(db_session, msg, reply, account)
        db_session.commit()

    assert len(calls) == 1
    statuses = [row.status for row in db_session.query(SalesAgentAction).order_by(SalesAgentAction.created_at).all()]
    assert statuses == ["sent", "skipped"]


def test_create_automated_next_action_sends_when_recipient_available(db_session, monkeypatch):
    sent = {}

    def fake_send_email(**kwargs):
        sent.update(kwargs)
        return {"resend_id": "next_email", "from_email": "scout@readyforrobots.com"}

    monkeypatch.setattr(sales_agent, "send_email_via_resend", fake_send_email)
    opportunity = SalesOpportunity(
        id=str(uuid.uuid4()),
        opportunity_type="crm",
        title="DexMate opportunity",
        current_stage="qualified",
        automation_level="auto",
        next_best_action={"intent": "meeting_requested", "recommendation": "Book a technical qualification call."},
    )
    db_session.add(opportunity)
    db_session.commit()

    action = create_automated_next_action(
        db_session,
        opportunity,
        recipient="buyer@example.com",
        reply_to="reply+token@readyforrobots.com",
    )
    db_session.commit()

    assert action.status == "sent"
    assert action.resend_id == "next_email"
    assert sent["to_email"] == "buyer@example.com"
    assert "I am Cal with Ready For Robots." in sent["body_text"]
    assert "We track automation buying signals" in sent["body_text"]
    assert "Cal @ Robot Automation Team" not in sent["body_text"]
    assert db_session.query(SalesMessage).filter(SalesMessage.direction == "outbound").count() == 1
