"""Sales console desk: review messages, delete box, and unsent drafts."""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.api.sales import discard_sales_message, list_outreach_ready, list_sales_inbox, restore_sales_message
from app.database import Base
from app.models.crm import CrmAccount, Team
from app.models.sales_agent import SalesMessage, SalesOpportunity


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _user():
    return {"uid": str(uuid.uuid4()), "email": "ugobe07@gmail.com"}


def _seed(db):
    team_id = uuid.uuid4()
    account_id = uuid.uuid4()
    opp_id = uuid.uuid4()
    msg_id = uuid.uuid4()
    db.add(Team(id=team_id, name="Cal Outreach (Admin)"))
    db.add(CrmAccount(
        id=account_id,
        team_id=team_id,
        name="Caesars Entertainment",
        industry="Casinos",
        contact_email="ops@caesars.example",
        outreach_draft="Subject: Housekeeping help\n\nCaesars can still use a bathroom-cleaning robot.",
    ))
    db.add(SalesOpportunity(
        id=opp_id,
        team_id=team_id,
        crm_account_id=account_id,
        title="Caesars Entertainment",
        opportunity_type="buyer_outreach",
        current_stage="ready_for_draft",
    ))
    db.add(SalesMessage(
        id=msg_id,
        sales_opportunity_id=opp_id,
        direction="inbound",
        from_email="ops@caesars.example",
        subject="Re: housekeeping",
        body_text="We already use floor scrubbers and want bathroom cleaning next.",
        payload={},
    ))
    db.commit()
    return msg_id


def test_inbox_discard_and_restore(db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "ugobe07@gmail.com")
    msg_id = _seed(db_session)
    user = _user()

    inbox = list_sales_inbox(team_id=None, folder="main", direction="inbound", db=db_session, user=user)
    assert [item["subject"] for item in inbox] == ["Re: housekeeping"]

    discard_sales_message(str(msg_id), db=db_session, user=user)
    assert list_sales_inbox(team_id=None, folder="main", direction="inbound", db=db_session, user=user) == []
    deleted = list_sales_inbox(team_id=None, folder="deleted", direction="all", db=db_session, user=user)
    assert len(deleted) == 1
    assert deleted[0]["body_text"].startswith("We already use floor scrubbers")

    restore_sales_message(str(msg_id), db=db_session, user=user)
    assert len(list_sales_inbox(team_id=None, folder="main", direction="inbound", db=db_session, user=user)) == 1


def test_outreach_ready_shows_unsent_draft(db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "ugobe07@gmail.com")
    _seed(db_session)
    ready = list_outreach_ready(db=db_session, user=_user())
    assert len(ready) == 1
    assert ready[0]["company"] == "Caesars Entertainment"
    assert ready[0]["subject"] == "Housekeeping help"
    assert "bathroom-cleaning robot" in ready[0]["body"]
    assert ready[0]["contact_email"] == "ops@caesars.example"
