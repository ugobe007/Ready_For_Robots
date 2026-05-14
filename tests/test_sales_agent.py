import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa: F401 - register SQLAlchemy models
from app.models.crm import CrmAccount, Team
from app.models.outreach import OutreachMessage, OutreachReply
from app.models.sales_agent import SalesAgentAction, SalesMessage, SalesOpportunity
from app.services import sales_agent
from app.services.sales_agent import classify_sales_intent, handle_crm_reply_first_response, plan_sales_reply


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
