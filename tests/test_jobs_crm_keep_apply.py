"""Jobs CRM keep / apply / thread — account storage, no invented emails."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("COMPANY_URL_OPENAI_RESOLVE", "0")

import app.models  # noqa: F401
from app.database import Base
from app.models.jobs_crm import ApplicationMessage, JobApplication, KeptJob
from app.services.jobs_crm import (
    SEND_NOT_SENT_NO_EMAIL,
    SEND_PREPARED,
    apply_selected_jobs,
    apply_to_job,
    capture_inbound_message,
    employer_email_from_job,
    keep_jobs,
    list_kept_jobs,
    list_messages,
    paste_inbound_reply,
    send_prepared_application,
    set_application_meeting_url,
)
from app.services.plan_entitlements import JOBS_CRM_FREE_BATCH, JOBS_CRM_FREE_MONTHLY_CAP

TEST_USER_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture(autouse=True)
def _no_youtube(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.setattr("app.services.robot_youtube_evidence._http_get", lambda url: None)


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


def _user() -> dict:
    return {"uid": str(TEST_USER_ID), "email": "oem@test.com", "plan_tier": "free"}


def _job(n: int, *, email: str | None = None) -> dict:
    row = {
        "job_key": f"job-{n}",
        "title": f"Tend line {n}",
        "company_name": f"Employer {n}",
        "locality": "Portland, OR",
        "industry": "manufacturing",
        "path": "tend",
    }
    if email:
        row["employer_email"] = email
    return row


def test_keep_upserts_and_is_idempotent(db_session):
    first = keep_jobs(db_session, _user(), [_job(1), _job(2)], robot_name="Spot")
    assert first["saved_count"] == 2
    assert first["created_count"] == 2
    again = keep_jobs(db_session, _user(), [_job(1), _job(2)], robot_name="Spot")
    assert again["saved_count"] == 2
    assert again["created_count"] == 0
    rows = db_session.query(KeptJob).filter(KeptJob.user_id == TEST_USER_ID).all()
    assert len(rows) == 2
    assert {r.job_key for r in rows} == {"job-1", "job-2"}
    assert rows[0].employer_name.startswith("Employer")
    listed = list_kept_jobs(db_session, _user())
    assert len(listed) == 2


def test_keep_enforces_free_batch_and_monthly_cap(db_session):
    batch = [_job(i) for i in range(1, 9)]
    result = keep_jobs(db_session, _user(), batch, robot_name="Spot")
    assert result["saved_count"] == JOBS_CRM_FREE_BATCH
    assert result["created_count"] == JOBS_CRM_FREE_BATCH

    extra = keep_jobs(
        db_session,
        _user(),
        [_job(20), _job(21), _job(22), _job(23), _job(24)],
        robot_name="Spot",
    )
    assert extra["created_count"] == 5
    third = keep_jobs(
        db_session,
        _user(),
        [_job(30), _job(31), _job(32), _job(33), _job(34)],
        robot_name="Spot",
    )
    assert extra["created_count"] + third["created_count"] + result["created_count"] == JOBS_CRM_FREE_MONTHLY_CAP
    blocked = keep_jobs(db_session, _user(), [_job(40)], robot_name="Spot")
    assert blocked["created_count"] == 0
    assert blocked["skipped_monthly"] == 1


def test_application_snapshot_without_send_when_no_email(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="4800 / month RaaS",
        poc_evidence="",
        poc_skipped=True,
        send=True,
    )
    assert app["send_status"] == SEND_NOT_SENT_NO_EMAIL
    assert app["employer_email"] is None
    assert "do not invent" in (app["send_error"] or "").lower()
    assert app["offer_snapshot"]["monthly_price"] == "4800 / month RaaS"
    assert app["offer_snapshot"]["selected_models"] == ["Spot"]
    assert app["offer_snapshot"]["price_label"] == "proposed_offer"
    row = db_session.query(JobApplication).one()
    assert row.monthly_price == "4800 / month RaaS"
    kept = db_session.query(KeptJob).one()
    assert kept.acted_at is not None


def test_no_send_without_email(db_session, monkeypatch):
    sent = []

    def _capture(**kwargs):
        to_email = kwargs.get("to_email")
        sent.append(kwargs)
        if to_email == "ops@named-employer.com" or (
            isinstance(to_email, list) and "ops@named-employer.com" in to_email
        ):
            raise AssertionError("must not send without a real employer email")
        return {"resend_id": "re_oem", "from_email": "jobs@readyforrobots.com"}

    monkeypatch.setattr("app.services.resend_email.send_email_via_resend", _capture)
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="1200",
        send=True,
    )
    assert all(
        item.get("to_email") != "ops@named-employer.com" for item in sent
    )
    assert app["send_status"] == SEND_NOT_SENT_NO_EMAIL
    assert employer_email_from_job(_job(1)) is None
    assert employer_email_from_job({"employer_email": "ops@named-employer.com"}) == "ops@named-employer.com"
    assert employer_email_from_job({"employer_email": "Named Employer Inc"}) is None


def test_message_thread_outbound_and_paste_inbound(db_session):
    keep_jobs(
        db_session,
        _user(),
        [_job(1, email="ops@named-employer.com")],
        robot_name="Spot",
    )
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="4800",
        send=False,
    )
    row = db_session.query(JobApplication).one()
    capture_inbound_message(
        db_session,
        row,
        body="Thanks — send the site assessment window.",
        from_email="ops@named-employer.com",
        to_email=row.reply_to,
        subject="Re: Applying Spot",
        provider_id="resend_in_1",
    )
    db_session.commit()
    thread = paste_inbound_reply(
        db_session,
        _user(),
        app["id"],
        body="We can do Tuesday 9am.",
        from_email="ops@named-employer.com",
    )
    messages = thread["messages"]
    assert any(m["direction"] == "inbound" for m in messages)
    assert any("Tuesday" in (m["body"] or "") for m in messages)
    assert thread["thread_state"] == "replied"
    assert list_messages(db_session, row.id)
    assert db_session.query(ApplicationMessage).count() >= 2


def test_apply_requires_price_and_model(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    with pytest.raises(ValueError, match="proposed monthly"):
        apply_to_job(
            db_session,
            _user(),
            job_key="job-1",
            robot_name="Spot",
            selected_models=["Spot"],
            monthly_price="",
        )
    with pytest.raises(ValueError, match="catalogued model"):
        apply_to_job(
            db_session,
            _user(),
            job_key="job-1",
            robot_name="Spot",
            selected_models=[],
            monthly_price="900",
        )


def test_expired_unacted_free_jobs_drop(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    row = db_session.query(KeptJob).one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()
    listed = list_kept_jobs(db_session, _user())
    assert listed == []


def test_apply_selected_jobs_path(db_session):
    keep_jobs(db_session, _user(), [_job(1), _job(2)], robot_name="Spot")
    result = apply_selected_jobs(
        db_session,
        _user(),
        jobs=[_job(1), _job(2)],
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="6200 / month",
        poc_skipped=True,
    )
    assert result["applied_count"] == 2
    assert result["selected_count"] == 2
    assert {row["job_key"] for row in result["applied"]} == {"job-1", "job-2"}
    assert all(row["scheduling_state"] == "we_schedule_with_employer" for row in result["applied"])
    rows = db_session.query(JobApplication).all()
    assert len(rows) == 2
    assert all(row["send_status"] == SEND_PREPARED for row in result["applied"])
    assert all(row["status"] == "prepared" for row in result["applied"])
    assert all(row["draft"]["operator_sends"] is True for row in result["applied"])
    assert all(row["draft"]["video_url"] is None for row in result["applied"])
    assert all(row["contacts"] == [] for row in result["applied"])


def test_prepare_does_not_email_employer(db_session, monkeypatch):
    sent = []

    def _capture(**kwargs):
        sent.append(kwargs)
        return {"resend_id": "re_x", "from_email": "jobs@readyforrobots.com"}

    monkeypatch.setattr("app.services.resend_email.send_email_via_resend", _capture)
    keep_jobs(
        db_session,
        _user(),
        [_job(1, email="ops@named-employer.com")],
        robot_name="TUG",
    )
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="TUG",
        selected_models=["TUG"],
        monthly_price="4800",
        poc_skipped=True,
        send=False,
    )
    assert app["status"] == "prepared"
    assert app["send_status"] == SEND_PREPARED
    assert app["draft"]["why"]
    assert "TUG" in app["draft"]["why"]
    assert app["contacts"] == [{"email": "ops@named-employer.com", "source": "job_card"}]
    assert app["can_operator_send"] is True
    assert not sent
    sent_app = send_prepared_application(db_session, _user(), app["id"])
    assert sent_app["status"] == "applied"
    assert sent_app["send_status"] == "sent"
    assert any(item.get("to_email") == "ops@named-employer.com" for item in sent)


def test_prepare_empty_video_and_contact_is_honest(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="TUG")
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="TUG",
        selected_models=["TUG"],
        monthly_price="1200",
        send=False,
    )
    assert app["poc_video_url"] is None
    assert app["draft"]["video_url"] is None
    assert app["contacts"] == []
    assert app["employer_email"] is None
    assert app["can_operator_send"] is False
    assert "invent" in (app["no_email_reason"] or "").lower()
    with pytest.raises(ValueError, match="invent"):
        send_prepared_application(db_session, _user(), app["id"])


def test_meeting_url_paste_is_honest_schedule(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="6200 / month",
        poc_skipped=True,
    )
    assert app["scheduling_state"] == "we_schedule_with_employer"
    with pytest.raises(ValueError, match="https"):
        set_application_meeting_url(db_session, _user(), app["id"], "meet.google.com/abc")
    saved = set_application_meeting_url(
        db_session, _user(), app["id"], "https://employer.example/interview"
    )
    assert saved["scheduling_state"] == "meeting_url"
    assert saved["meeting_url"] == "https://employer.example/interview"

