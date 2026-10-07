"""Hunter.io fill for operator daily-job sales cards."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.robot_directed_discovery import RobotJob
from app.services.daily_jobs_hunter import enrich_daily_jobs_with_hunter
from app.services.daily_jobs_report import compose_daily_jobs_report


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _job(**extra):
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        job_key=f"job-{uuid4().hex[:10]}",
        company_name="GEODIS",
        locality="Plainfield, IN",
        action="pallet_move",
        robot_compatible_task="Trailer unloading",
        investigate_status="yes",
        existence_confidence=0.9,
        definition_completeness=0.8,
        created_at=now,
        updated_at=now,
    )
    defaults.update(extra)
    return RobotJob(**defaults)


class _FakeHunter:
    def __init__(self, emails):
        self.emails = emails
        self.domain_calls = []
        self.finder_calls = []

    def find_email(self, **kwargs):
        self.finder_calls.append(kwargs)
        return None

    def domain_search(self, **kwargs):
        self.domain_calls.append(kwargs)
        return {"emails": self.emails}


def test_enrich_fills_missing_name_and_email(monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "test-key")
    monkeypatch.delenv("CONTACT_USE_HUNTER", raising=False)
    db = _session()
    db.add(_job(job_key="empty"))
    db.commit()
    hunter = _FakeHunter(
        [
            {
                "email": "priya.shah@geodis.com",
                "name": "Priya Shah",
                "title": "Site operations manager",
                "confidence": 92,
                "department": "operations",
                "verification_status": "valid",
            }
        ]
    )
    result = enrich_daily_jobs_with_hunter(db, limit=25, client=hunter)
    assert result["ok"] is True
    assert result["filled"] == 1
    assert hunter.domain_calls
    report = compose_daily_jobs_report(db, limit=25)
    card = report["jobs"][0]
    assert card["decision_maker"] == "Priya Shah · Site operations manager"
    assert "priya.shah@geodis.com" in card["contact"]
    assert card["contact_source"] == "decision_maker_agent"
    assert "Warehouse Operations Manager" in (card.get("target_titles") or [])


def test_enrich_rejects_role_and_invented_ops_mailboxes(monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "test-key")
    db = _session()
    db.add(_job(job_key="chipotle", company_name="Chipotle", locality="Newport Beach, CA"))
    db.commit()
    hunter = _FakeHunter(
        [
            {
                "email": "operations@chipotle.com",
                "name": "Carlos Rodriguez",
                "title": "VP",
                "confidence": 99,
                "department": "operations",
                "verification_status": "valid",
            }
        ]
    )
    result = enrich_daily_jobs_with_hunter(db, limit=25, client=hunter)
    assert result["filled"] == 0
    report = compose_daily_jobs_report(db, limit=25)
    assert "operations@chipotle.com" not in report["jobs"][0]["contact"]
    assert "Hunter.io found no" in report["jobs"][0]["contact"]


def test_enrich_skips_cards_that_already_have_page_contact(monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "test-key")
    db = _session()
    db.add(
        _job(
            job_key="page",
            employer_email="dock.ops@geodis.com",
            provenance={"contact_name": "Maya Chen", "contact_title": "Pharmacy ops"},
        )
    )
    db.commit()
    hunter = _FakeHunter(
        [
            {
                "email": "other.person@geodis.com",
                "name": "Other Person",
                "title": "COO",
                "confidence": 99,
                "department": "executive",
                "verification_status": "valid",
            }
        ]
    )
    result = enrich_daily_jobs_with_hunter(db, limit=25, client=hunter)
    assert result["skipped"] == 1
    assert hunter.domain_calls == []
    report = compose_daily_jobs_report(db, limit=25)
    assert "Maya Chen" in report["jobs"][0]["decision_maker"]
    assert "dock.ops@geodis.com" in report["jobs"][0]["contact"]


def test_enrich_picks_job_title_not_generic_executive(monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "test-key")
    db = _session()
    db.add(
        _job(
            job_key="pharm",
            company_name="Harris Health",
            locality="Houston, TX",
            action="delivery",
            robot_compatible_task="Pharmacy cart loop",
            observed_workflow="Move filled carts from pharmacy to nursing units",
        )
    )
    db.commit()
    hunter = _FakeHunter(
        [
            {
                "email": "kelli.fondren@harrishealth.org",
                "name": "Kelli Fondren",
                "title": "Chief Development Officer",
                "confidence": 99,
                "department": "executive",
                "verification_status": "valid",
            },
            {
                "email": "maya.chen@harrishealth.org",
                "name": "Maya Chen",
                "title": "Director of Pharmacy",
                "confidence": 82,
                "department": "health",
                "verification_status": "valid",
            },
        ]
    )
    result = enrich_daily_jobs_with_hunter(db, limit=25, client=hunter)
    assert result["filled"] == 1
    report = compose_daily_jobs_report(db, limit=25)
    assert "Maya Chen" in report["jobs"][0]["decision_maker"]
    assert "maya.chen@harrishealth.org" in report["jobs"][0]["contact"]
    assert "Kelli Fondren" not in report["jobs"][0]["decision_maker"]


def test_enrich_disabled_without_key(monkeypatch):
    monkeypatch.delenv("HUNTER_API_KEY", raising=False)
    db = _session()
    db.add(_job(job_key="no-key"))
    db.commit()
    result = enrich_daily_jobs_with_hunter(db, limit=25)
    assert result["ok"] is False
    assert result["reason"] == "hunter_disabled"


def test_enrich_does_not_overwrite_page_name(monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "test-key")
    db = _session()
    db.add(
        _job(
            job_key="named-no-mail",
            provenance={"contact_name": "Maya Chen", "contact_title": "Pharmacy ops"},
        )
    )
    db.commit()
    hunter = _FakeHunter(
        [
            {
                "email": "other.person@geodis.com",
                "name": "Other Person",
                "title": "COO",
                "confidence": 99,
                "department": "executive",
                "verification_status": "valid",
            }
        ]
    )
    result = enrich_daily_jobs_with_hunter(db, limit=25, client=hunter)
    assert result["filled"] == 0
    assert result["missed"] == 1
    assert hunter.domain_calls == []
    report = compose_daily_jobs_report(db, limit=25)
    assert "Maya Chen" in report["jobs"][0]["decision_maker"]
    assert "other.person@geodis.com" not in report["jobs"][0]["contact"]


def test_send_runs_hunter_before_email(monkeypatch):
    from app.services.daily_jobs_report import send_daily_jobs_report

    monkeypatch.setenv("HUNTER_API_KEY", "test-key")
    db = _session()
    db.add(_job(job_key="send-hunt"))
    db.commit()
    hunter = _FakeHunter(
        [
            {
                "email": "priya.shah@geodis.com",
                "name": "Priya Shah",
                "title": "Site operations manager",
                "confidence": 92,
                "department": "operations",
                "verification_status": "valid",
            }
        ]
    )
    sent = []
    monkeypatch.setattr(
        "app.services.daily_jobs_report._claim_report_day", lambda day: True
    )
    monkeypatch.setattr(
        "app.services.daily_jobs_report._mark_report_sent", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "app.services.resend_email.send_email_via_resend",
        lambda **kwargs: sent.append(kwargs) or {"resend_id": "re_hunt"},
    )
    monkeypatch.setattr(
        "app.services.daily_jobs_hunter.HunterClient",
        lambda: hunter,
    )
    result = send_daily_jobs_report(db, force=True)
    assert result["sent"] is True
    assert hunter.domain_calls
    assert result["hunter"]["filled"] == 1
    assert "priya.shah@geodis.com" in sent[0]["body_text"]
    assert "Priya Shah" in sent[0]["body_text"]


def test_email_must_belong_to_the_named_employer():
    from app.services.daily_jobs_hunter import _email_fits_employer

    assert _email_fits_employer(
        "thomasr@maringeneral.org",
        "Mercy General Hospital",
        "Columbus, OH",
    ) is False
    assert _email_fits_employer(
        "pjurisic@napaparts.com.au",
        "NAPA Auto Parts",
        "Duncansville, PA",
    ) is False
    assert _email_fits_employer(
        "jurias@unical.com",
        "Unifi (airport floor tech)",
        "ATL — Atlanta, GA",
    ) is False
    assert _email_fits_employer(
        "paul.spurzem@jhu.edu",
        "Johns Hopkins University",
        "Baltimore, MD",
    ) is True
    assert _email_fits_employer(
        "jcostella@industrialmetalsupply.com",
        "Industrial Metal Supply",
        "Riverside, CA",
    ) is True


def test_finder_search_does_not_import_hunter():
    from pathlib import Path

    search = Path("app/api/robot_job_search.py").read_text(encoding="utf-8")
    matcher = Path("app/services/robot_job_capability_match.py").read_text(
        encoding="utf-8"
    )
    assert "daily_jobs_hunter" not in search
    assert "HunterClient" not in search
    assert "job_decision_maker_agent" not in search
    assert "daily_jobs_hunter" not in matcher
    assert "job_decision_maker_agent" not in matcher
