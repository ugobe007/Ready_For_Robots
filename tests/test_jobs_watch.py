"""Jobs watch — free taste, cron diff, no paid LLM."""
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register metadata
from app.database import Base
from app.models.jobs_watch import JobsWatch, JobsWatchEvent
from app.models.robot_submission import RobotSubmission
from app.services.jobs_watch import (
    JOBS_WATCH_FREE_ALERTS,
    apply_search_result,
    build_watch_email,
    run_jobs_watch_cycle,
    upsert_watch,
    watch_status,
)
from app.services.plan_entitlements import PLAN_FREE, PLAN_PAID


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


def _user(**extra):
    return {
        "uid": str(uuid4()),
        "email": "buyer@example.com",
        **extra,
    }


def _jobs(*keys):
    return [
        {"job_key": key, "title": f"Job {key}", "company_name": f"Co {key}"}
        for key in keys
    ]


def test_first_cron_run_seeds_without_email(db_session):
    watch = JobsWatch(
        user_id=uuid4(),
        email="buyer@example.com",
        robot_url="https://robot.example/sku",
        website_domain="robot.example",
        product_name="Relay",
        opted_in=True,
        last_job_keys=[],
        notify_count=0,
    )
    db_session.add(watch)
    db_session.flush()
    diff = apply_search_result(
        db_session, watch, _jobs("a", "b"), plan=PLAN_FREE
    )
    assert diff["first_run"] is True
    assert diff["new_count"] == 0
    assert diff["can_email"] is False
    assert watch.last_job_keys == ["a", "b"]
    assert db_session.query(JobsWatchEvent).count() == 0


def test_second_run_new_key_is_new_and_can_email(db_session):
    watch = JobsWatch(
        user_id=uuid4(),
        email="buyer@example.com",
        robot_url="https://robot.example/sku",
        website_domain="robot.example",
        product_name="Relay",
        opted_in=True,
        last_job_keys=["a"],
        notify_count=0,
    )
    db_session.add(watch)
    db_session.flush()
    diff = apply_search_result(
        db_session, watch, _jobs("a", "b"), plan=PLAN_FREE
    )
    assert diff["first_run"] is False
    assert diff["new_count"] == 1
    assert diff["can_email"] is True
    assert diff["new_jobs"][0].kind == "new"
    assert diff["new_jobs"][0].job_key == "b"


def test_free_alert_cap_blocks_email_after_two(db_session):
    watch = JobsWatch(
        user_id=uuid4(),
        email="buyer@example.com",
        robot_url="https://robot.example/sku",
        website_domain="robot.example",
        opted_in=True,
        last_job_keys=["a"],
        notify_count=JOBS_WATCH_FREE_ALERTS,
    )
    db_session.add(watch)
    db_session.flush()
    diff = apply_search_result(
        db_session, watch, _jobs("a", "c"), plan=PLAN_FREE
    )
    assert diff["new_count"] == 1
    assert diff["can_email"] is False


def test_cycle_emails_new_jobs_then_respects_free_cap(db_session, monkeypatch):
    uid = uuid4()
    watch = JobsWatch(
        user_id=uid,
        email="buyer@example.com",
        robot_url="https://robot.example/sku",
        website_domain="robot.example",
        product_name="Relay",
        opted_in=True,
        last_job_keys=["pack"],
        notify_count=0,
    )
    db_session.add(watch)
    db_session.commit()

    sent = []

    def _search(_url, product=None):
        return {"jobs": _jobs("pack", "pallet")}

    monkeypatch.setattr(
        "app.services.jobs_watch.send_watch_email",
        lambda w, events, plan: sent.append((w.id, [e.job_key for e in events], plan)) or True,
    )
    first = run_jobs_watch_cycle(db_session, search_fn=_search, send=True)
    assert first["checked"] == 1
    assert first["emailed"] == 1
    assert first["new_jobs"] == 1
    assert sent and sent[0][1] == ["pallet"]
    db_session.refresh(watch)
    assert watch.notify_count == 1

    def _search_more(_url, product=None):
        return {"jobs": _jobs("pack", "pallet", "inspect")}

    second = run_jobs_watch_cycle(db_session, search_fn=_search_more, send=True)
    assert second["emailed"] == 1
    db_session.refresh(watch)
    assert watch.notify_count == 2

    def _search_third(_url, product=None):
        return {"jobs": _jobs("pack", "pallet", "inspect", "weld")}

    third = run_jobs_watch_cycle(db_session, search_fn=_search_third, send=True)
    assert third["new_jobs"] == 1
    assert third["emailed"] == 0
    db_session.refresh(watch)
    assert watch.notify_count == 2


def test_free_user_cannot_watch_second_robot(db_session):
    user = _user()
    upsert_watch(
        db_session,
        user=user,
        robot_url="https://robot.example/sku",
        product_name="Relay",
        seed_jobs=_jobs("pack"),
        opted_in=True,
    )
    assert db_session.query(RobotSubmission).filter_by(website_domain="robot.example").count() == 1
    with pytest.raises(PermissionError, match="Free watches 1 robot"):
        upsert_watch(
            db_session,
            user=user,
            robot_url="https://other.example/arm",
            product_name="Arm",
            opted_in=True,
        )


def test_paid_user_can_watch_second_robot(db_session):
    user = _user(plan_tier="pro")
    upsert_watch(
        db_session,
        user=user,
        robot_url="https://robot.example/sku",
        product_name="Relay",
        opted_in=True,
    )
    second = upsert_watch(
        db_session,
        user=user,
        robot_url="https://other.example/arm",
        product_name="Arm",
        opted_in=True,
    )
    assert second.website_domain == "other.example"
    assert db_session.query(JobsWatch).filter_by(opted_in=True).count() == 2


def test_watch_status_locks_extra_free_events(db_session):
    user = _user()
    watch = upsert_watch(
        db_session,
        user=user,
        robot_url="https://robot.example/sku",
        product_name="Relay",
        seed_jobs=_jobs("a", "b", "c", "d", "e"),
        opted_in=True,
    )
    status = watch_status(db_session, user, [watch])
    assert status["opted_in"] is True
    assert status["free_taste"] is True
    unlocked = [e for e in status["events"] if not e["locked"]]
    locked = [e for e in status["events"] if e["locked"]]
    assert len(unlocked) == 3
    assert len(locked) == 2
    assert locked[0]["title"] == "New work for your robot"


def test_build_watch_email_mentions_upgrade_for_free():
    watch = JobsWatch(
        user_id=uuid4(),
        email="buyer@example.com",
        robot_url="https://robot.example/sku",
        website_domain="robot.example",
        product_name="Relay",
        opted_in=True,
        last_job_keys=[],
        notify_count=0,
    )
    event = JobsWatchEvent(
        watch_id=uuid4(),
        job_key="pallet",
        title="Pallet move",
        company_name="Acme",
        kind="new",
    )
    subject, body = build_watch_email(watch, [event], plan=PLAN_FREE)
    assert "Relay" in subject
    assert "Pallet move" in body
    assert "Upgrade" in body
    paid_subject, paid_body = build_watch_email(watch, [event], plan=PLAN_PAID)
    assert "Upgrade" not in paid_body
    assert paid_subject.startswith("New jobs")
