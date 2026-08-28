"""Jobs CRM recruiter flow — docs, employer tokens, OEM status email."""
from __future__ import annotations

import os
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("COMPANY_URL_OPENAI_RESOLVE", "0")

import app.models  # noqa: F401
from app.database import Base
from app.models.jobs_crm import ApplicationMessage, JobApplication, UserRobotDocument
from app.services.jobs_crm import SEND_NOT_SENT_NO_EMAIL, apply_to_job, keep_jobs
from app.services.jobs_crm_recruiter import (
    HOLD_TTL_HOURS,
    STATUS_ACCEPTED,
    STATUS_APPLIED,
    STATUS_INTERVIEW_CONFIRMED,
    STATUS_INTERVIEW_HELD,
    STATUS_INTERVIEW_REQUESTED,
    STATUS_INTERVIEW_SCHEDULED,
    STATUS_SUCCESS,
    accept_application,
    confirm_hold,
    confirm_hold_by_token,
    employer_decision_url,
    employer_public_payload,
    find_application_by_employer_token,
    find_application_by_oem_hold_token,
    hold_slot,
    mark_application_outcome,
    oem_hold_url,
    release_hold,
    request_interview,
    store_user_document,
)

TEST_USER_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture()
def db_session(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBS_CRM_UPLOAD_DIR", str(tmp_path / "docs"))
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


def _job(n: int = 1, *, email: str | None = None) -> dict:
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


def test_keep_prompt_path_still_upserts_selected(db_session):
    result = keep_jobs(db_session, _user(), [_job(1), _job(2), _job(3)], robot_name="Spot")
    assert result["saved_count"] == 3
    assert result["created_count"] == 3


def test_upload_attach_and_apply_snapshot(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    doc = store_user_document(
        db_session,
        _user(),
        filename="spot-spec.pdf",
        content=b"%PDF-1.4 fake spec",
        mime_type="application/pdf",
        kind="brochure",
    )
    assert doc["filename"] == "spot-spec.pdf"
    assert db_session.query(UserRobotDocument).count() == 1
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="4800 / month",
        poc_skipped=True,
        document_ids=[doc["id"]],
        send=True,
    )
    assert app["send_status"] == SEND_NOT_SENT_NO_EMAIL
    assert any(row["filename"] == "spot-spec.pdf" for row in app["documents"])
    assert app["status"] == STATUS_APPLIED
    assert app["employer_decision_url"]
    assert "/employer/" in app["employer_decision_url"]
    row = db_session.query(JobApplication).one()
    assert row.employer_token
    assert row.oem_email == "oem@test.com"
    assert find_application_by_employer_token(db_session, row.employer_token) is row


def test_token_accept_and_interview(db_session, monkeypatch):
    sent = []

    def _fake_send(**kwargs):
        sent.append(kwargs)
        return {"resend_id": f"re_{len(sent)}", "from_email": "jobs@readyforrobots.com"}

    monkeypatch.setattr("app.services.resend_email.send_email_via_resend", _fake_send)
    keep_jobs(db_session, _user(), [_job(1, email="ops@named-employer.com")], robot_name="Spot")
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="1200",
        send=True,
    )
    row = db_session.query(JobApplication).one()
    public = employer_public_payload(db_session, row)
    assert public["can_accept"] is True
    assert "ops@" not in str(public.get("oem_email", ""))
    accepted = accept_application(db_session, row.employer_token)
    assert accepted["status"] == STATUS_ACCEPTED
    db_session.refresh(row)
    assert row.status == STATUS_ACCEPTED
    interview = request_interview(
        db_session,
        row.employer_token,
        proposed_at="2026-09-04T15:00:00+00:00",
        note="Loading dock",
    )
    assert interview["status"] == STATUS_INTERVIEW_SCHEDULED
    db_session.refresh(row)
    assert row.interview_at is not None
    assert "2026-09-04" in row.interview_at.isoformat()
    connect = request_interview(db_session, row.employer_token, connect_you=True)
    assert connect["status"] == STATUS_INTERVIEW_REQUESTED
    assert any("Accept:" in (item.get("body_text") or "") or "Applying" in (item.get("subject") or "") for item in sent)
    oem_subjects = [item.get("subject") or "" for item in sent if "oem@test.com" in str(item.get("to_email"))]
    assert any("accepted" in sub.lower() or "interview" in sub.lower() or "applied" in sub.lower() for sub in oem_subjects)
    assert db_session.query(ApplicationMessage).count() >= 2
    assert employer_decision_url(row.employer_token).endswith(f"/employer/{row.employer_token}")


def test_oem_status_email_on_apply_and_outcome(db_session, monkeypatch):
    sent = []

    def _fake_send(**kwargs):
        sent.append(kwargs)
        return {"resend_id": f"re_{len(sent)}", "from_email": "jobs@readyforrobots.com"}

    monkeypatch.setattr("app.services.resend_email.send_email_via_resend", _fake_send)
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="900",
        send=True,
    )
    assert app["send_status"] == SEND_NOT_SENT_NO_EMAIL
    oem_mails = [item for item in sent if item.get("to_email") == "oem@test.com" or item.get("to_email") == ["oem@test.com"]]
    assert oem_mails, "OEM account email must get a recruiter confirmation on apply"
    assert "Tend line 1" in (oem_mails[0].get("body_text") or "")
    assert "Employer 1" in (oem_mails[0].get("body_text") or "")
    marked = mark_application_outcome(db_session, _user(), app["id"], "success")
    assert marked["status"] == STATUS_SUCCESS
    assert any("success" in (item.get("subject") or "").lower() for item in sent)


def _apply(db_session, *, email: str | None = None, send: bool = True):
    keep_jobs(db_session, _user(), [_job(1, email=email)], robot_name="Spot")
    return apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="1200",
        send=send,
    )


def test_hold_slot_persists_and_emails_both_sides(db_session, monkeypatch):
    sent = []

    def _fake_send(**kwargs):
        sent.append(kwargs)
        return {"resend_id": f"re_{len(sent)}", "from_email": "jobs@readyforrobots.com"}

    monkeypatch.setattr("app.services.resend_email.send_email_via_resend", _fake_send)
    _apply(db_session, email="ops@named-employer.com")
    row = db_session.query(JobApplication).one()
    held = hold_slot(
        db_session,
        row.employer_token,
        slot_start="2026-09-08T15:00:00+00:00",
        slot_end="2026-09-08T16:00:00+00:00",
        note="Loading dock",
    )
    assert held["status"] == STATUS_INTERVIEW_HELD
    assert held["can_confirm_hold"] is True
    assert held["slot_start"]
    assert "2026-09-08T15:00" in held["slot_start"]
    assert "2026-09-08T16:00" in (held["slot_end"] or "")
    db_session.refresh(row)
    assert row.status == STATUS_INTERVIEW_HELD
    assert row.interview_mode == "hold_slot"
    assert row.held_at is not None
    assert row.hold_expires_at is not None
    assert (row.hold_expires_at - row.held_at).total_seconds() == HOLD_TTL_HOURS * 3600
    assert row.oem_hold_token
    assert find_application_by_oem_hold_token(db_session, row.oem_hold_token) is row
    oem_hold = [item for item in sent if "slot held" in (item.get("subject") or "").lower()]
    assert oem_hold, "OEM must get a recruiter slot-held email"
    both = [
        item
        for item in sent
        if isinstance(item.get("to_email"), list)
        and "ops@named-employer.com" in item.get("to_email")
    ]
    assert both, "Both sides email requires a real employer address"
    body = (both[-1].get("body_text") or "") + (oem_hold[-1].get("body_text") or "")
    assert "Slot held for Employer 1 Tend line 1" in body
    assert oem_hold_url(row.oem_hold_token) in body
    assert "Cal sales autonomy" in body


def test_hold_does_not_email_employer_without_email(db_session, monkeypatch):
    sent = []

    def _fake_send(**kwargs):
        sent.append(kwargs)
        return {"resend_id": f"re_{len(sent)}", "from_email": "jobs@readyforrobots.com"}

    monkeypatch.setattr("app.services.resend_email.send_email_via_resend", _fake_send)
    app = _apply(db_session)
    assert app["send_status"] == SEND_NOT_SENT_NO_EMAIL
    row = db_session.query(JobApplication).one()
    assert not row.employer_email
    held = hold_slot(
        db_session,
        row.employer_token,
        slot_start="2026-09-09T10:00:00+00:00",
    )
    assert held["status"] == STATUS_INTERVIEW_HELD
    db_session.refresh(row)
    assert row.slot_end is not None
    both = [
        item
        for item in sent
        if isinstance(item.get("to_email"), list) and len(item.get("to_email") or []) > 1
    ]
    assert both == []
    oem_only = [item for item in sent if item.get("to_email") == "oem@test.com"]
    assert any("slot held" in (item.get("subject") or "").lower() for item in oem_only)


def test_hold_rejects_inverted_window(db_session):
    _apply(db_session)
    row = db_session.query(JobApplication).one()
    with pytest.raises(ValueError, match="end after it starts"):
        hold_slot(
            db_session,
            row.employer_token,
            slot_start="2026-09-09T16:00:00+00:00",
            slot_end="2026-09-09T15:00:00+00:00",
        )
    with pytest.raises(ValueError, match="start time"):
        hold_slot(db_session, row.employer_token, slot_start="")


def test_propose_path_does_not_write_hold_columns(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.services.resend_email.send_email_via_resend",
        lambda **kwargs: {"resend_id": "re_1", "from_email": "jobs@readyforrobots.com"},
    )
    _apply(db_session, email="ops@named-employer.com")
    row = db_session.query(JobApplication).one()
    proposed = request_interview(
        db_session,
        row.employer_token,
        proposed_at="2026-09-04T15:00:00+00:00",
    )
    assert proposed["status"] == STATUS_INTERVIEW_SCHEDULED
    assert proposed["can_confirm_hold"] is False
    db_session.refresh(row)
    assert row.held_at is None
    assert row.slot_start is None
    assert row.interview_mode == "proposed_time"


def test_oem_confirm_and_release_hold(db_session, monkeypatch):
    sent = []

    def _fake_send(**kwargs):
        sent.append(kwargs)
        return {"resend_id": f"re_{len(sent)}", "from_email": "jobs@readyforrobots.com"}

    monkeypatch.setattr("app.services.resend_email.send_email_via_resend", _fake_send)
    app = _apply(db_session, email="ops@named-employer.com")
    row = db_session.query(JobApplication).one()
    hold_slot(
        db_session,
        row.employer_token,
        slot_start="2026-09-10T13:00:00+00:00",
        slot_end="2026-09-10T14:00:00+00:00",
    )
    confirmed = confirm_hold(db_session, _user(), app["id"])
    assert confirmed["status"] == STATUS_INTERVIEW_CONFIRMED
    db_session.refresh(row)
    assert row.status == STATUS_INTERVIEW_CONFIRMED
    assert any("confirmed" in (item.get("subject") or "").lower() for item in sent)

    hold_slot(
        db_session,
        row.employer_token,
        slot_start="2026-09-11T09:00:00+00:00",
        slot_end="2026-09-11T10:00:00+00:00",
    )
    released = release_hold(db_session, _user(), app["id"])
    assert released["status"] == STATUS_APPLIED
    assert released["can_confirm_hold"] is False
    db_session.refresh(row)
    assert row.slot_start is None
    assert row.held_at is None
    assert any("released" in (item.get("subject") or "").lower() for item in sent)


def test_oem_hold_token_confirm(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.services.resend_email.send_email_via_resend",
        lambda **kwargs: {"resend_id": "re_tok", "from_email": "jobs@readyforrobots.com"},
    )
    _apply(db_session, email="ops@named-employer.com")
    row = db_session.query(JobApplication).one()
    hold_slot(
        db_session,
        row.employer_token,
        slot_start="2026-09-12T11:00:00+00:00",
        slot_end="2026-09-12T12:00:00+00:00",
    )
    db_session.refresh(row)
    public = confirm_hold_by_token(db_session, row.oem_hold_token)
    assert public["status"] == STATUS_INTERVIEW_CONFIRMED
    assert public["can_confirm_hold"] is False


def test_reject_non_pdf_image_upload(db_session):
    with pytest.raises(ValueError, match="PDF or image"):
        store_user_document(
            db_session,
            _user(),
            filename="notes.exe",
            content=b"MZ",
            mime_type="application/x-msdownload",
        )


def test_reject_video_mime_on_spec_upload(db_session):
    with pytest.raises(ValueError, match="PDF or image"):
        store_user_document(
            db_session,
            _user(),
            filename="demo.mp4",
            content=b"\x00\x00\x00 ftypmp42",
            mime_type="video/mp4",
        )
    with pytest.raises(ValueError, match="PDF or image"):
        store_user_document(
            db_session,
            _user(),
            filename="clip.webm",
            content=b"\x1aE\xdf\xa3",
            mime_type="video/webm",
        )


def test_attach_ignores_other_users_docs(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    other = {"uid": str(uuid.uuid4()), "email": "other@test.com", "plan_tier": "free"}
    foreign = store_user_document(
        db_session,
        other,
        filename="not-yours.pdf",
        content=b"%PDF-1.4 x",
        mime_type="application/pdf",
    )
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="1100",
        document_ids=[foreign["id"]],
        send=False,
    )
    assert app["documents"] == []


def test_apply_stores_poc_video_url_on_employer_payload(db_session, monkeypatch):
    sent = []

    def _fake_send(**kwargs):
        sent.append(kwargs)
        return {"resend_id": f"re_{len(sent)}", "from_email": "jobs@readyforrobots.com"}

    monkeypatch.setattr("app.services.resend_email.send_email_via_resend", _fake_send)
    video = "https://www.loom.com/share/abcd1234efgh5678"
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
        monthly_price="1200",
        poc_evidence="Cell demo notes from the integrator.",
        poc_video_url=video,
        poc_skipped=False,
        send=True,
    )
    assert app["poc_video_url"] == video
    assert app["poc_evidence"] == "Cell demo notes from the integrator."
    assert app["offer_snapshot"]["poc_video_url"] == video
    row = db_session.query(JobApplication).one()
    assert row.poc_video_url == video
    public = employer_public_payload(db_session, row)
    assert public["poc_video_url"] == video
    assert public["poc_evidence"] == "Cell demo notes from the integrator."
    employer_mail = [
        item
        for item in sent
        if item.get("to_email") == "ops@named-employer.com"
        or (
            isinstance(item.get("to_email"), list)
            and "ops@named-employer.com" in item.get("to_email")
        )
    ]
    assert employer_mail, "Outreach should include the video URL when sending"
    body = employer_mail[0].get("body_text") or ""
    assert video in body
    assert "Video résumé" in body


def test_empty_poc_video_url_does_not_block_apply(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    app = apply_to_job(
        db_session,
        _user(),
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="900",
        poc_evidence="",
        poc_video_url="",
        poc_skipped=True,
        send=False,
    )
    assert app["poc_video_url"] is None
    assert app["poc_skipped"] is True
    public = employer_public_payload(db_session, db_session.query(JobApplication).one())
    assert public["poc_video_url"] is None


def test_invalid_poc_video_url_rejects_without_echo(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    sneaky = "https://evil.example/watch?v=not-a-video"
    with pytest.raises(ValueError) as exc:
        apply_to_job(
            db_session,
            _user(),
            job_key="job-1",
            robot_name="Spot",
            selected_models=["Spot"],
            monthly_price="900",
            poc_video_url=sneaky,
            send=False,
        )
    assert sneaky not in str(exc.value)
    assert "evil.example" not in str(exc.value)
    assert "not allowed" in str(exc.value).lower() or "HTTPS" in str(exc.value)

