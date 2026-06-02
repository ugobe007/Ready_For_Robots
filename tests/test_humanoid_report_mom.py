"""Month-over-month humanoid report snapshot tests."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.humanoid_report_snapshot import HumanoidReportSnapshot
from app.services.humanoid_report_mom import (
    build_compact_snapshot,
    compare_month_over_month,
    load_previous_snapshot,
    persist_snapshot,
)
from app.services.humanoid_intelligence_report import build_humanoid_intelligence_report_payload
from app.services.humanoid_scraper import SEED_ROBOTS, compute_scores


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _scored(slug: str) -> dict:
    robot = next(r for r in SEED_ROBOTS if r["model_slug"] == slug)
    scores = compute_scores(robot["specs"], status=robot["status"], vendor=robot["vendor"])
    return {**robot, **scores, "sources": []}


def test_mom_compare_after_two_snapshots(db_session):
    robots_may = [
        _scored("unitree-g1"),
        _scored("agility-digit"),
    ]
    robots_may.sort(key=lambda r: -(r.get("score_total") or 0))
    from app.services.humanoid_deployment_report import build_deployment_summary
    from app.services.humanoid_intelligence_report import _build_robot_profile

    dep = build_deployment_summary(robots_may)
    profiles = [_build_robot_profile(r, i + 1) for i, r in enumerate(robots_may)]
    snap_may = build_compact_snapshot(robots_may, dep, profiles, {"fleet_poc_or_better_pct": 50})
    snap_may["period_key"] = "2026-05"
    persist_snapshot(db_session, snap_may)

    robots_june = [
        _scored("figure-02"),
        _scored("unitree-g1"),
        _scored("agility-digit"),
    ]
    robots_june.sort(key=lambda r: -(r.get("score_total") or 0))
    dep2 = build_deployment_summary(robots_june)
    profiles2 = [_build_robot_profile(r, i + 1) for i, r in enumerate(robots_june[:3])]
    snap_june = build_compact_snapshot(robots_june, dep2, profiles2, {"fleet_poc_or_better_pct": 55})
    snap_june["period_key"] = "2026-06"

    prior = load_previous_snapshot(db_session, "2026-06")
    assert prior is not None
    assert prior["period_key"] == "2026-05"

    mom = compare_month_over_month(snap_june, prior)
    assert mom["has_prior"] is True
    assert mom["previous_period"] == "2026-05"
    assert mom["fleet_metrics"]["total_robots"]["delta"] == 1
    assert mom["narrative_bullets"]


def test_intelligence_report_includes_mom_with_db(db_session):
    robots = [_scored("unitree-g1"), _scored("agility-digit")]
    payload = build_humanoid_intelligence_report_payload(robots, top_n=2, db=db_session)
    assert "month_over_month" in payload["report"]
    assert payload["report"]["month_over_month"]["has_prior"] is False
