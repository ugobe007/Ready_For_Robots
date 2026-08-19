"""Durable robot-submission ledger — dedupe by domain, ID + timestamps + counts."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register metadata
from app.database import Base
from app.models.robot_submission import RobotSubmission
from app.services.robot_submission_service import (
    record_robot_submission,
    record_submission_match,
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


def test_first_submission_creates_id_and_timestamp(db_session):
    row = record_robot_submission(
        db_session,
        url="https://relayrobotics.com/",
        company_name="Relay Robotics",
        product_name="Relay",
        robot_class="service_robot",
        profile_tier="C",
    )
    assert row is not None
    assert isinstance(row.id, int) and row.id > 0
    assert row.website_domain == "relayrobotics.com"
    assert row.submission_count == 1
    assert row.first_seen_at is not None
    assert row.last_seen_at is not None
    assert row.company_name == "Relay Robotics"


def test_resubmission_dedupes_by_domain_and_increments(db_session):
    a = record_robot_submission(db_session, url="https://relayrobotics.com/")
    b = record_robot_submission(db_session, url="https://www.relayrobotics.com/robots/relay")
    assert a.id == b.id  # same domain → same durable record
    assert b.submission_count == 2
    assert db_session.query(RobotSubmission).count() == 1


def test_match_enrichment_links_real_buyers(db_session):
    record_robot_submission(db_session, url="https://relayrobotics.com/")
    row = record_submission_match(
        db_session,
        url="https://relayrobotics.com/",
        capabilities=[{"key": "transport"}, {"key": "mobile"}, "transport"],
        matched_company_ids=[486, 5907, "5017", None],
        match_count=3,
        source="match_url",
    )
    assert row is not None
    assert row.matched_company_ids == [486, 5907, 5017]
    assert row.capabilities == ["transport", "mobile"]  # deduped, compacted
    assert row.last_match_count == 3
    assert row.last_matched_at is not None
    # Enrichment must not bump the submission counter.
    assert row.submission_count == 1


def test_match_can_be_first_touch(db_session):
    # A match (e.g. /pipeline buyers surface) before any profile build still records.
    row = record_submission_match(
        db_session, url="https://carbonrobotics.com/", matched_company_ids=[1, 2]
    )
    assert row is not None
    assert row.website_domain == "carbonrobotics.com"
    assert row.matched_company_ids == [1, 2]


def test_blank_url_is_ignored(db_session):
    assert record_robot_submission(db_session, url="") is None
    assert db_session.query(RobotSubmission).count() == 0
