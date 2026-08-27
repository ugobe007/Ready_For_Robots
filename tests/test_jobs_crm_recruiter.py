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
    STATUS_ACCEPTED,
    STATUS_APPLIED,
    STATUS_INTERVIEW_REQUESTED,
    STATUS_INTERVIEW_SCHEDULED,
    STATUS_SUCCESS,
    accept_application,
    employer_decision_url,
    employer_public_payload,
    find_application_by_employer_token,
    mark_application_outcome,
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


def test_reject_non_pdf_image_upload(db_session):
    with pytest.raises(ValueError, match="PDF or image"):
        store_user_document(
            db_session,
            _user(),
            filename="notes.exe",
            content=b"MZ",
            mime_type="application/x-msdownload",
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
