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
