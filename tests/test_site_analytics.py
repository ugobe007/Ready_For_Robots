"""Site analytics persistence and aggregation."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.robot_buyer_lead import RobotBuyerLead
from app.models.site_analytics_event import SiteAnalyticsEvent
from app.models.waitlist import WaitlistSignup
from app.services.site_analytics_service import (
    EVENT_FIRST_SAVE,
    EVENT_SIGNUP_COMPLETE,
    EVENT_SIGNUP_START,
    EVENT_URL_SCAN,
    EVENT_VISIT,
    aggregate_site_metrics,
    record_site_event,
    signup_funnel_metrics,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_record_and_aggregate_site_metrics(db_session):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)
    prev = now - timedelta(days=60)

    record_site_event(db_session, EVENT_VISIT, {"path": "/"})
    record_site_event(db_session, EVENT_URL_SCAN, {"url": "https://acme.com"})

    db_session.add(
        WaitlistSignup(
            email="buyer@example.com",
            source="report_download",
        )
    )
    db_session.add(
        RobotBuyerLead(
            email="ops@factory.com",
            company="Factory Inc",
            use_case="Warehouse AMR",
            robot_type="amr_warehouse",
            implementation_timeline="near_term_3_6mo",
        )
    )
    db_session.commit()

    metrics = aggregate_site_metrics(
        db_session,
        cutoff=cutoff,
        prev_cutoff=prev,
        in_memory_calcs=[],
        in_memory_searches=[],
        in_memory_visits=[],
    )

    assert metrics["site_visits"] >= 1
    assert metrics["total_calculations"] >= 1
    assert metrics["robot_searches"] >= 1
    assert metrics["email_captures"] >= 2
    assert metrics["conversion_rate"] > 0

    rows = db_session.query(SiteAnalyticsEvent).all()
    assert len(rows) == 2


def test_signup_funnel_metrics_counts_and_rates(db_session):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    # 4 started, 2 completed, 1 activated → 50% start→complete, 50% complete→save.
    for _ in range(4):
        record_site_event(db_session, EVENT_SIGNUP_START, {"plan": "pro"})
    for _ in range(2):
        record_site_event(db_session, EVENT_SIGNUP_COMPLETE, {})
    record_site_event(db_session, EVENT_FIRST_SAVE, {"company": "Acme"})

    funnel = signup_funnel_metrics(db_session, cutoff=cutoff)

    assert funnel["available"] is True
    assert funnel["signup_start"] == 4
    assert funnel["signup_complete"] == 2
    assert funnel["first_save"] == 1
    assert funnel["start_to_complete_rate"] == 50.0
    assert funnel["complete_to_save_rate"] == 50.0
    assert funnel["start_to_save_rate"] == 25.0


def test_signup_funnel_metrics_zero_safe(db_session):
    funnel = signup_funnel_metrics(db_session, cutoff=datetime.now(timezone.utc) - timedelta(days=7))
    assert funnel["signup_start"] == 0
    assert funnel["start_to_complete_rate"] == 0.0
    assert funnel["complete_to_save_rate"] == 0.0
