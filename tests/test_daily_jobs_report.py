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
    _REDIS_SENT_KEY,
    _claim_key,
    _claim_report_day,
    _family_for_action,
    compose_daily_jobs_report,
    get_daily_jobs_report_recipients,
    maybe_send_missed_daily_jobs_report,
    public_job_card,
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
    assert report["jobs"][0]["job_type"] == "Delivery"
    assert report["jobs"][0]["decision_maker"] == "Not named on the posting"
    assert "will not invent" in report["jobs"][0]["contact"]
    assert "First seen" in report["jobs"][0]["timing"]
    assert report["jobs"][0]["card_href"].endswith("/?job=named")
    assert report["limit"] == TOP_N or report["limit"] == 25


def test_compose_sales_card_uses_page_contact_not_invented(db_session):
    db_session.add(
        _job(
            job_key="page-contact",
            company_name="GEODIS",
            locality="Plainfield, IN",
            action="pallet_move",
            robot_compatible_task="Pallet move",
            observed_workflow="Unload inbound trailers and stage pallets at the dock.",
            why_job="Dock labor is short on the night shift.",
            employer_email="dock.ops@geodis.com",
            apply_url="https://geodis.com/careers/dock",
            provenance={
                "contact_name": "Priya Shah",
                "contact_title": "Site operations manager",
            },
        )
    )
    db_session.add(
        _job(
            job_key="invented-ops",
            company_name="Chipotle",
            locality="Newport Beach, CA",
            action="assembly",
            robot_compatible_task="Bowl assembly",
            employer_email="operations@chipotle.com",
            provenance={
                "contact_name": "Operational Lead (Vice President of Restaurant & Dining Operations)",
                "contact_title": "Vice President of Restaurant & Dining Operations",
            },
        )
    )
    db_session.commit()
    report = compose_daily_jobs_report(db_session, limit=25)
    by_key = {j["job_key"]: j for j in report["jobs"]}
    real = by_key["page-contact"]
    assert real["job_type"] == "Pallet Move"
    assert "Unload inbound trailers" in real["description"]
    assert real["decision_maker"] == "Priya Shah · Site operations manager"
    assert "dock.ops@geodis.com" in real["contact"]
    html_named = render_daily_jobs_report_html(
        {"date": "2026-10-09", "limit": 25, "jobs": [real]}
    )
    assert "Priya Shah" in html_named
    assert "mailto:dock.ops@geodis.com" in html_named
    assert "Job card" in html_named
    assert real["card_href"].endswith("/?job=page-contact")
    fake = by_key["invented-ops"]
    assert fake["decision_maker"] == "Not named on the posting"
    assert "operations@chipotle.com" not in fake["contact"]
    assert "will not invent" in fake["contact"]


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
    card = {
        "rank": 1,
        "job_key": "rrh-pharmacy",
        "employer": "Rochester Regional Health",
        "title": "Pharmacy delivery",
        "locality": "Rochester, NY",
        "job_type": "Delivery",
        "description": "Pharmacy delivery between units and central pharmacy.",
        "decision_maker": "Not named on the posting",
        "timing": "First seen 2026-10-07 · new this week",
        "contact": "No page email or apply URL. We will not invent one.",
        "card_href": "https://readyforrobots.com/?job=rrh-pharmacy",
    }
    text = render_daily_jobs_report_text(
        {
            "date": "2026-10-07",
            "limit": 25,
            "jobs": [card],
            "find_href": "https://readyforrobots.com/?visit=jobs",
            "admin_href": "https://readyforrobots.com/admin#daily-jobs-report",
        }
    )
    assert "Top 25 hot job opportunities — 2026-10-07" in text
    assert "Rochester Regional Health" in text
    assert "Decision maker:" in text
    assert "Contact:" in text
    assert "Job card:" in text
    assert "Pharmacy delivery between units" in text
    assert "/?visit=jobs" in text
    assert "admin#daily-jobs-report" in text
    assert "HOT" not in text
    assert "Marcus Vance" not in text
    assert "operations@" not in text
    assert "/pipeline?co=" not in text
    html_body = render_daily_jobs_report_html(
        {
            "date": "2026-10-07",
            "limit": 25,
            "jobs": [card],
            "find_href": "https://readyforrobots.com/?visit=jobs",
            "admin_href": "https://readyforrobots.com/admin#daily-jobs-report",
        }
    )
    assert "Rochester Regional Health" in html_body
    assert "Decision maker:" in html_body
    assert "Contact:" in html_body
    assert "Job card" in html_body
    assert "/?job=rrh-pharmacy" in html_body
    assert "padding:16px" not in html_body
    assert "/?visit=jobs" in html_body
    assert "/pipeline?co=" not in html_body


def test_public_job_card_is_named_employer_only(db_session):
    db_session.add(
        _job(
            job_key="rrh-live",
            company_name="Rochester Regional Health",
            locality="Rochester, NY",
            robot_compatible_task="Pharmacy delivery",
        )
    )
    db_session.add(
        _job(
            job_key="board",
            company_name="Indeed",
            locality="Remote",
            robot_compatible_task="Warehouse associate",
        )
    )
    db_session.commit()
    card = public_job_card(db_session, "rrh-live")
    assert card is not None
    assert card["employer"] == "Rochester Regional Health"
    assert card["card_href"].endswith("/?job=rrh-live")
    assert card["family"] == "transport"
    assert public_job_card(db_session, "board") is None
    assert public_job_card(db_session, "missing") is None


def test_family_tokens_not_substrings():
    assert _family_for_action("delivery", "Pharmacy delivery") == "transport"
    assert _family_for_action("pallet_move", "Pallet move") == "pallet"
    assert _family_for_action("palletizing", "Inbound palletizing") == "pallet"
    assert _family_for_action("picking", "Piece picking") == "gripper"
    assert _family_for_action("pick", "Bin pick") == "gripper"
    assert _family_for_action("manipulation", "Arm tend") == "gripper"
    assert _family_for_action("robotic_arm", "Machine tend") == "gripper"
    assert _family_for_action("cart_move", "Tote run") == "cart"


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


class _FakeRedis:
    def __init__(self, store: dict[str, str]):
        self.store = store

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def delete(self, key):
        self.store.pop(key, None)


def test_claim_allows_next_calendar_day(monkeypatch):
    store = {_REDIS_SENT_KEY: "2026-10-07"}
    monkeypatch.setattr(
        "app.services.daily_jobs_report._redis_client",
        lambda: _FakeRedis(store),
    )
    assert _claim_report_day("2026-10-07") is True
    assert _claim_report_day("2026-10-07") is False
    assert _claim_report_day("2026-10-08") is True
    assert _claim_report_day("2026-10-08") is False
    assert store[_REDIS_SENT_KEY] == "2026-10-07"
    assert store[_claim_key("2026-10-08")] == "2026-10-08"


def test_send_skips_when_already_claimed(monkeypatch, db_session):
    monkeypatch.delenv("HUNTER_API_KEY", raising=False)
    monkeypatch.setattr(
        "app.services.daily_jobs_report._claim_report_day",
        lambda day: False,
    )
    result = send_daily_jobs_report(db_session, force=False)
    assert result["sent"] is False
    assert result["reason"] == "Already sent today"
    assert "ugobe07@gmail.com" in result["recipients"]


def test_send_emails_operator(monkeypatch, db_session):
    monkeypatch.delenv("HUNTER_API_KEY", raising=False)
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
    assert sent[0]["subject"].startswith("Top 25 hot job opportunities")
    assert "Rochester Regional Health" in sent[0]["body_text"]
    assert "Decision maker:" in sent[0]["body_text"]
    assert "Job card:" in sent[0]["body_text"]
    assert "Rochester Regional Health" in (sent[0].get("body_html") or "")
    assert (sent[0].get("idempotency_key") or "").startswith(
        "daily-jobs-report-"
    )
    assert "force" in (sent[0].get("idempotency_key") or "")


def test_missed_send_runs_once_when_not_sent_today(monkeypatch, db_session):
    monkeypatch.delenv("HUNTER_API_KEY", raising=False)
    db_session.add(_job(job_key="missed"))
    db_session.commit()
    sent = []
    monkeypatch.setattr(
        "app.services.daily_jobs_report.last_sent_day", lambda: None
    )
    monkeypatch.setattr(
        "app.services.daily_jobs_report._claim_report_day", lambda day: True
    )
    monkeypatch.setattr(
        "app.services.daily_jobs_report._mark_report_sent", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "app.services.resend_email.send_email_via_resend",
        lambda **kwargs: sent.append(kwargs) or {"resend_id": "re_missed"},
    )
    result = maybe_send_missed_daily_jobs_report(db_session)
    assert result["sent"] is True
    assert sent
    monkeypatch.setattr(
        "app.services.daily_jobs_report.last_sent_day",
        lambda: result["date"],
    )
    again = maybe_send_missed_daily_jobs_report(db_session)
    assert again["sent"] is False
    assert again["reason"] == "Already sent today"
