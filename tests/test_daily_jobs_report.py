"""Daily top-25 robot jobs report — named employers only."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.robot_directed_discovery import RobotJob
from app.services.daily_jobs_report import (
    TOP_N,
    compose_daily_jobs_report,
    get_daily_jobs_report_recipients,
    render_daily_jobs_report_html,
    render_daily_jobs_report_text,
    send_daily_jobs_report,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def _job(**extra):
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        job_key=f"job-{uuid4().hex[:10]}",
        company_name="Rochester Regional Health",
        locality="Rochester, NY",
        action="delivery",
        robot_compatible_task="Pharmacy delivery",
        investigate_status="yes",
        existence_confidence=0.9,
        definition_completeness=0.8,
        created_at=now,
        updated_at=now,
    )
    defaults.update(extra)
    return RobotJob(**defaults)


def test_recipients_always_include_operator(monkeypatch):
    monkeypatch.delenv("DAILY_JOBS_REPORT_EMAIL", raising=False)
    assert get_daily_jobs_report_recipients() == ["ugobe07@gmail.com"]
    monkeypatch.setenv("DAILY_JOBS_REPORT_EMAIL", "ops@example.com")
    assert get_daily_jobs_report_recipients() == [
        "ugobe07@gmail.com",
        "ops@example.com",
    ]


def test_compose_keeps_named_employers_drops_boards(db_session):
    db_session.add(
        _job(
            job_key="named",
            company_name="Rochester Regional Health",
            locality="Rochester, NY",
            robot_compatible_task="Pharmacy delivery",
            investigate_status="yes",
        )
    )
    db_session.add(
        _job(
            job_key="board",
            company_name="Indeed",
            locality="Remote",
            robot_compatible_task="Warehouse associate",
            investigate_status="yes",
            existence_confidence=0.99,
        )
    )
    db_session.add(
        _job(
            job_key="no-place",
            company_name="Acme Hospitals",
            locality=None,
            robot_compatible_task="EVS rounds",
        )
    )
    db_session.commit()
    report = compose_daily_jobs_report(db_session, limit=25)
    employers = [j["employer"] for j in report["jobs"]]
    assert employers == ["Rochester Regional Health"]
    assert report["jobs"][0]["title"] == "Pharmacy delivery"
    assert report["jobs"][0]["locality"] == "Rochester, NY"
    assert report["limit"] == TOP_N or report["limit"] == 25


def test_compose_ranks_yes_ahead_of_weak(db_session):
    db_session.add(
        _job(
            job_key="weak",
            company_name="Endeavor Health",
            locality="Evanston, IL",
            robot_compatible_task="Unit supply runs",
            investigate_status="weak",
            existence_confidence=0.99,
        )
    )
    db_session.add(
        _job(
            job_key="yes",
            company_name="GEODIS",
            locality="Plainfield, IN",
            robot_compatible_task="Pallet move",
            investigate_status="yes",
            existence_confidence=0.5,
        )
    )
    db_session.commit()
    report = compose_daily_jobs_report(db_session, limit=25)
    assert [j["employer"] for j in report["jobs"]] == ["GEODIS", "Endeavor Health"]


def test_render_email_is_jobs_not_signal():
    text = render_daily_jobs_report_text(
        {
            "date": "2026-10-07",
            "limit": 25,
            "jobs": [
                {
                    "rank": 1,
                    "employer": "Rochester Regional Health",
                    "title": "Pharmacy delivery",
                    "locality": "Rochester, NY",
                }
            ],
            "find_href": "https://readyforrobots.com/?visit=jobs",
            "admin_href": "https://readyforrobots.com/admin#daily-jobs-report",
        }
    )
    assert "Top 25 robot jobs — 2026-10-07" in text
    assert "Rochester Regional Health — Pharmacy delivery" in text
    assert "/?visit=jobs" in text
    assert "admin#daily-jobs-report" in text
    assert "HOT" not in text
    assert "SIGNAL" in text  # "not SIGNAL buyers"
    assert "/pipeline?co=" not in text
    html_body = render_daily_jobs_report_html(
        {
            "date": "2026-10-07",
            "limit": 25,
            "jobs": [
                {
                    "rank": 1,
                    "employer": "Rochester Regional Health",
                    "title": "Pharmacy delivery",
                    "locality": "Rochester, NY",
                }
            ],
            "find_href": "https://readyforrobots.com/?visit=jobs",
            "admin_href": "https://readyforrobots.com/admin#daily-jobs-report",
        }
    )
    assert "Rochester Regional Health" in html_body
    assert "/?visit=jobs" in html_body
    assert "/pipeline?co=" not in html_body


def test_html_escapes_employer_markup():
    html_body = render_daily_jobs_report_html(
        {
            "date": "2026-10-07",
            "limit": 25,
            "jobs": [
                {
                    "rank": 1,
                    "employer": "<script>alert(1)</script>",
                    "title": "Work",
                    "locality": "NY",
                }
            ],
        }
    )
    assert "<script>" not in html_body
    assert "&lt;script&gt;" in html_body


def test_send_skips_when_already_claimed(monkeypatch, db_session):
    monkeypatch.setattr(
        "app.services.daily_jobs_report._claim_report_day",
        lambda day: False,
    )
    result = send_daily_jobs_report(db_session, force=False)
    assert result["sent"] is False
    assert result["reason"] == "Already sent today"
    assert "ugobe07@gmail.com" in result["recipients"]


def test_send_emails_operator(monkeypatch, db_session):
    db_session.add(_job(job_key="named-send"))
    db_session.commit()
    sent = []
    monkeypatch.setattr(
        "app.services.daily_jobs_report._claim_report_day", lambda day: True
    )
    monkeypatch.setattr(
        "app.services.daily_jobs_report._mark_report_sent", lambda *a, **k: None
    )

    def _fake_send(**kwargs):
        sent.append(kwargs)
        return {"resend_id": "re_test"}

    monkeypatch.setattr(
        "app.services.resend_email.send_email_via_resend", _fake_send
    )
    result = send_daily_jobs_report(db_session, force=True)
    assert result["sent"] is True
    assert result["count"] == 1
    assert sent[0]["to_email"] == ["ugobe07@gmail.com"]
    assert sent[0]["subject"].startswith("Top 25 robot jobs")
    assert "Rochester Regional Health" in sent[0]["body_text"]
    assert "Rochester Regional Health" in (sent[0].get("body_html") or "")
