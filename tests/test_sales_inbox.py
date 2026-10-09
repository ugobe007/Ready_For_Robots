"""Operator /inbox listing — admin sees inbound replies."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import sales as sales_api
from app.database import Base
import app.models  # noqa: F401
from app.models.crm import CrmAccount, Team, TeamMember
from app.models.outreach import OutreachMessage, OutreachReply
from app.models.sales_agent import SalesMessage, SalesOpportunity


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal()


def test_admin_inbox_lists_inbound_without_team_membership(monkeypatch):
    monkeypatch.setattr(
        "app.api.auth_deps._is_admin",
        lambda email: email == "ugobe07@gmail.com",
    )
    engine, db = _session()
    try:
        team_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        admin_id = uuid.uuid4()
        opp_id = uuid.uuid4()
        msg_id = uuid.uuid4()
        db.add(Team(id=team_id, name="Ready For Robots"))
        db.add(TeamMember(team_id=team_id, user_id=owner_id, role="owner"))
        db.add(
            SalesOpportunity(
                id=str(opp_id),
                team_id=str(team_id),
                opportunity_type="crm",
                title="GEODIS",
                current_stage="replied",
            )
        )
        db.add(
            SalesMessage(
                id=str(msg_id),
                sales_opportunity_id=str(opp_id),
                direction="inbound",
                from_email="ops@geodis.com",
                subject="Re: pallet work",
                body_text="We can talk Thursday.",
            )
        )
        db.commit()
        items = sales_api.list_sales_inbox(
            team_id=None,
            folder="all",
            db=db,
            user={"uid": str(admin_id), "email": "ugobe07@gmail.com"},
        )
        assert len(items) == 1
        assert items[0]["from_email"] == "ops@geodis.com"
        assert items[0]["title"] == "GEODIS"
        member_empty = sales_api.list_sales_inbox(
            team_id=None,
            folder="all",
            db=db,
            user={"uid": str(uuid.uuid4()), "email": "someone@example.com"},
        )
        assert member_empty == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_inbox_includes_outreach_reply_missing_sales_message(monkeypatch):
    monkeypatch.setattr("app.api.auth_deps._is_admin", lambda email: False)
    engine, db = _session()
    try:
        team_id = uuid.uuid4()
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()
        msg_id = uuid.uuid4()
        reply_id = uuid.uuid4()
        db.add(Team(id=team_id, name="Ready For Robots"))
        db.add(TeamMember(team_id=team_id, user_id=user_id, role="owner"))
        db.add(
            CrmAccount(
                id=account_id,
                team_id=team_id,
                name="Endeavor Health",
            )
        )
        db.add(
            OutreachMessage(
                id=msg_id,
                team_id=team_id,
                crm_account_id=account_id,
                sender_user_id=user_id,
                to_email="buyer@endeavor.example",
                reply_token="tok-inbox-1",
                subject="Robot job at Endeavor",
                body_text="Intro",
                status="replied",
            )
        )
        db.add(
            OutreachReply(
                id=reply_id,
                outreach_message_id=msg_id,
                team_id=team_id,
                crm_account_id=account_id,
                from_email="buyer@endeavor.example",
                subject="Re: Robot job at Endeavor",
                body_text="Send the job card.",
                received_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        items = sales_api.list_sales_inbox(
            team_id=None,
            folder="all",
            db=db,
            user={"uid": str(user_id), "email": "owner@example.com"},
        )
        assert len(items) == 1
        assert items[0]["from_email"] == "buyer@endeavor.example"
        assert items[0]["source_type"] == "outreach_reply"
        assert items[0]["title"] == "Endeavor Health"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
