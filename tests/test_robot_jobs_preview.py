"""Public FIND preview lists named-employer jobs without inventing people."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.robot_directed_discovery import RobotJob
from app.api.robot_jobs_preview import _public_job
from app.services.daily_jobs_report import select_daily_report_rows


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
        observed_workflow="Move pharmacy totes between the basement and floors.",
        investigate_status="yes",
        existence_confidence=0.9,
        definition_completeness=0.8,
        created_at=now,
        updated_at=now,
    )
    defaults.update(extra)
    return RobotJob(**defaults)


def test_preview_keeps_named_employers_drops_boards(db_session):
    db_session.add(
        _job(
            job_key="named",
            company_name="Rochester Regional Health",
            locality="Rochester, NY",
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
    rows = select_daily_report_rows(db_session, limit=3)
    jobs = [_public_job(row, i) for i, row in enumerate(rows, start=1)]
    assert len(jobs) == 1
    job = jobs[0]
    assert job["employer"] == "Rochester Regional Health"
    assert job["workplace"] == "Rochester, NY"
    assert "Pharmacy" in job["description"] or "delivery" in job["work"].lower()
    assert "operations@" not in (job["contact"] or "").lower()
    assert "ROI" not in job["description"]
    assert len(select_daily_report_rows(db_session, limit=3)) == 1


def test_public_job_does_not_invent_a_person():
    row = _job(provenance={}, requirements={})
    public = _public_job(row, 1)
    assert "Not named on the posting" in public["decision_maker"]
    assert "operations@" not in public["contact"].lower()
    assert public["contact"].startswith("No page email")


def test_public_job_redacts_hunter_enriched_contact():
    """Hunter.io data must not leak to the anonymous public preview."""
    row = _job(
        employer_email="john.doe@example.com",
        provenance={
            "contact_name": "John Doe",
            "contact_title": "Operations Manager",
            "contact_source": "hunter_domain",
            "hunter_checked_at": "2026-10-08",
        },
        requirements={},
    )
    public = _public_job(row, 1)
    assert "john.doe@example.com" not in public["contact"]
    assert "John Doe" not in public["decision_maker"]
    assert "Not named on the posting" in public["decision_maker"]
    assert "No page email" in public["contact"]


def test_public_job_redacts_hunter_finder_contact():
    """Hunter.io finder results must not leak to the anonymous public preview."""
    row = _job(
        employer_email="jane.smith@company.org",
        provenance={
            "contact_name": "Jane Smith",
            "contact_title": "Director of Operations",
            "contact_source": "hunter_finder",
            "hunter_checked_at": "2026-10-08",
        },
        requirements={},
    )
    public = _public_job(row, 1)
    assert "jane.smith@company.org" not in public["contact"]
    assert "Jane Smith" not in public["decision_maker"]
    assert "Not named on the posting" in public["decision_maker"]
    assert "No page email" in public["contact"]


def test_public_job_redacts_decision_maker_agent_contact():
    """Decision maker agent enrichment must not leak to the anonymous public preview."""
    row = _job(
        employer_email="contact@facility.com",
        provenance={
            "contact_name": "Operations Lead",
            "contact_title": "Facility Manager",
            "contact_source": "decision_maker_agent",
            "hunter_checked_at": "2026-10-08",
        },
        requirements={},
    )
    public = _public_job(row, 1)
    assert "contact@facility.com" not in public["contact"]
    assert "Operations Lead" not in public["decision_maker"]
    assert "Not named on the posting" in public["decision_maker"]
    assert "No page email" in public["contact"]


def test_public_job_keeps_page_sourced_contact():
    """Page-sourced contact information should be preserved (not Hunter)."""
    row = _job(
        employer_email="jobs@hospital.org",
        contact_url="https://hospital.org/apply",
        provenance={
            "contact_name": "HR Department",
            "contact_source": "job_posting_page",
        },
        requirements={},
    )
    public = _public_job(row, 1)
    assert "jobs@hospital.org" in public["contact"] or "hospital.org" in public["contact"]
