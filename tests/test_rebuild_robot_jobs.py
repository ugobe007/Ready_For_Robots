"""Recovery after the 2026-10-11 purge: rebuild robot_jobs from surviving signals."""
import importlib.util
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.company import Company
from app.models.robot_directed_discovery import RobotJob
from app.models.signal import Signal
from app.services.robot_job_extract import extract_robot_job, format_robot_job_signal

_spec = importlib.util.spec_from_file_location(
    "rebuild_robot_jobs", Path(__file__).resolve().parents[1] / "scripts" / "rebuild_robot_jobs.py"
)
rebuild = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rebuild)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    s = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield s
    finally:
        s.close()


def test_parse_signal_text_round_trips_formatter():
    job = extract_robot_job(
        title="Order Picker",
        description="$18-$22 an hour. 45 cases per hour. Lift 50 lbs. Night shift.",
        company="Acme Fulfillment",
        locality="Reno, NV",
    )
    parsed = rebuild.parse_signal_text(format_robot_job_signal(job))
    assert parsed["job_title"] == "Order Picker"
    assert parsed["employer"] == "Acme Fulfillment"
    assert parsed["compensation"]["wage_min"] == 18
    assert parsed["compensation"]["wage_max"] == 22


def test_parse_signal_text_accepts_legacy_prefix_and_rejects_noise():
    assert rebuild.parse_signal_text("ROBOT_JOB | Dishwasher | Warewash | pay unknown | specs unknown | open | Wynn")[
        "job_title"
    ] == "Dishwasher"
    assert rebuild.parse_signal_text("Pipeline opportunity (labor_challenge): Cook") is None
    assert rebuild.parse_signal_text("") is None


def test_from_signals_dry_run_writes_nothing_then_apply_rebuilds(db_session, monkeypatch):
    company = Company(name="Caesars Entertainment", industry="Food Service",
                      location_city="Las Vegas", location_state="NV")
    db_session.add(company)
    db_session.flush()
    then = datetime(2026, 6, 1, tzinfo=timezone.utc)
    for title in ("Dishwasher", "Line Cook", "Housekeeper", "Line Cook"):  # one dupe
        job = extract_robot_job(title=title, company="Caesars Entertainment", locality="Las Vegas, NV")
        db_session.add(Signal(company_id=company.id, signal_type="robot_job",
                              signal_text=format_robot_job_signal(job), signal_strength=0.8,
                              source_url="https://example.com/job", created_at=then))
    db_session.commit()
    monkeypatch.setattr(rebuild, "_session", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    rebuild.cmd_from_signals(Namespace(apply=False))
    assert db_session.query(RobotJob).count() == 0

    rebuild.cmd_from_signals(Namespace(apply=True))
    rows = db_session.query(RobotJob).all()
    assert sorted(r.robot_compatible_task for r in rows) == ["Dishwasher", "Housekeeper", "Line Cook"]
    assert all(r.provenance.get("rebuilt_from") == "signals" for r in rows)
    assert all(r.opportunity_tier in (1, 2, 3) for r in rows)

    # Idempotent.
    rebuild.cmd_from_signals(Namespace(apply=True))
    assert db_session.query(RobotJob).count() == 3
