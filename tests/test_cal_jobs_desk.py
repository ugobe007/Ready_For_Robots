"""Cal Jobs CRM desk: persona, tool routing, task-model persist, apply-draft prepare."""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("COMPANY_URL_OPENAI_RESOLVE", "0")

import app.models  # noqa: F401
from app.database import Base
from app.models.jobs_crm import JobApplication, KeptJob
from app.services.cal_jobs_desk import (
    ASK_TASK_MODEL,
    REFUSE_BUYER,
    REFUSE_FIND,
    REFUSE_SEND,
    missing_apply_facts,
    read_desk,
    run_desk_tool,
)
from app.services.cal_persona import (
    CAL_JOBS_DESK_JOB,
    CAL_JOBS_DESK_TOOLS,
    CAL_JOBS_FORBIDDEN_TOOLS,
    CAL_SURFACE,
    CAL_TITLE,
    cal_persona_payload,
)
from app.services.jobs_crm import keep_jobs, list_kept_jobs, set_kept_job_task_model

TEST_USER_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture(autouse=True)
def _no_youtube(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.setattr("app.services.robot_youtube_evidence._http_get", lambda url: None)


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


def _user() -> dict:
    return {"uid": str(TEST_USER_ID), "email": "oem@test.com", "plan_tier": "free"}


def _job(n: int, *, email: str | None = None) -> dict:
    row = {
        "job_key": f"job-{n}",
        "title": f"Tend line {n}",
        "company_name": f"Employer {n}",
        "locality": "Portland, OR",
        "industry": "manufacturing",
        "path": "tend",
    }
    if email:
        row["employer_email"] = email
    return row


def test_persona_is_jobs_recruiter_on_crm_desk():
    payload = cal_persona_payload()
    assert payload["title"] == "Jobs Recruiter"
    assert payload["title"] == CAL_TITLE
    assert payload["job"] == CAL_JOBS_DESK_JOB
    assert payload["surface"] == CAL_SURFACE
    assert payload["tools"] == list(CAL_JOBS_DESK_TOOLS)
    assert "send_buyer_intro" in payload["forbidden_tools"]
    ident = payload["identity"].lower()
    assert "jobs recruiter" in ident
    assert "find" in ident
    assert "buyer" not in ident or "does not sell" in ident
    assert CAL_SURFACE == "/pipeline?src=jobs_activate"


def test_read_desk_asks_task_model_first(db_session):
    keep_jobs(db_session, _user(), [_job(1, email="ops@named-employer.com")], robot_name="Spot")
    desk = read_desk(db_session, _user())
    assert desk["ok"] is True
    assert desk["autonomy_enabled"] is False
    assert desk["operator_sends"] is True
    assert desk["next_question"]["fact"] == "task_model"
    assert ASK_TASK_MODEL in desk["next_question"]["prompt"]
    assert desk["jobs"][0]["contacts"][0]["email"] == "ops@named-employer.com"
    assert "task_model" in desk["jobs"][0]["missing"]


def test_save_task_model_tool_persists_user_words(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    with pytest.raises(ValueError, match="will not guess"):
        run_desk_tool(
            db_session,
            _user(),
            tool="save_task_model",
            job_key="job-1",
            kind="source",
            source="",
        )
    turn = run_desk_tool(
        db_session,
        _user(),
        tool="save_task_model",
        job_key="job-1",
        kind="source",
        source="  NVIDIA GR00T  ",
    )
    assert turn["ok"] is True
    assert turn["result"]["work_task_model_kind"] == "source"
    assert turn["result"]["work_task_model_source"] == "NVIDIA GR00T"
    listed = list_kept_jobs(db_session, _user())
    assert listed[0]["work_task_model_source"] == "NVIDIA GR00T"
    trained = run_desk_tool(
        db_session,
        _user(),
        tool="save_task_model",
        job_key="job-1",
        kind="self_train",
    )
    assert trained["result"]["work_task_model_kind"] == "self_train"
    assert trained["result"]["work_task_model_source"] is None


def test_prepare_apply_fills_draft_operator_sends(db_session):
    keep_jobs(db_session, _user(), [_job(1, email="ops@named-employer.com")], robot_name="Spot")
    set_kept_job_task_model(db_session, _user(), job_key="job-1", kind="self_train")
    turn = run_desk_tool(
        db_session,
        _user(),
        tool="prepare_apply",
        job_key="job-1",
        robot_name="Spot",
        selected_models=["Spot"],
        monthly_price="4800 / month RaaS",
        poc_skipped=True,
    )
    assert turn["ok"] is True
    app = turn["result"]
    assert app["send_status"] == "prepared"
    assert app["draft"]["operator_sends"] is True
    assert "Spot" in app["draft"]["subject"]
    assert "Employer 1" in app["draft"]["subject"]
    assert app["contacts"][0]["email"] == "ops@named-employer.com"
    assert db_session.query(JobApplication).count() == 1
    desk = turn["desk"]
    assert desk["jobs"][0]["application_status"] == "prepared"
    assert desk["next_question"] is None


def test_prepare_refuses_unknown_task_model_and_invented_sku(db_session, monkeypatch):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    with pytest.raises(ValueError, match="model for this work"):
        run_desk_tool(
            db_session,
            _user(),
            tool="prepare_apply",
            job_key="job-1",
            selected_models=["Spot"],
            monthly_price="1200",
        )
    set_kept_job_task_model(db_session, _user(), job_key="job-1", kind="self_train")
    monkeypatch.setattr(
        "app.services.cal_jobs_desk.catalog_skus_for_oem",
        lambda **kwargs: [{"name": "Spot", "slug": "spot", "source": "oem_listing"}],
    )
    with pytest.raises(ValueError, match="will not invent"):
        run_desk_tool(
            db_session,
            _user(),
            tool="prepare_apply",
            job_key="job-1",
            selected_models=["Galbot G2"],
            monthly_price="1200",
        )


def test_tool_routing_refuses_send_buyer_and_find(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    send = run_desk_tool(db_session, _user(), tool="send_application", job_key="job-1")
    assert send["ok"] is False
    assert send["refused"] is True
    assert REFUSE_SEND in send["detail"]
    buyer = run_desk_tool(db_session, _user(), tool="send_buyer_intro")
    assert buyer["ok"] is False
    assert REFUSE_BUYER in buyer["detail"]
    find = run_desk_tool(db_session, _user(), tool="find_jobs")
    assert find["ok"] is False
    assert REFUSE_FIND in find["detail"]
    plan = run_desk_tool(db_session, _user(), tool="generate_plan")
    assert plan["ok"] is False
    assert db_session.query(JobApplication).count() == 0
    assert db_session.query(KeptJob).count() == 1


def test_missing_facts_order_task_model_then_price(db_session):
    keep_jobs(db_session, _user(), [_job(1)], robot_name="Spot")
    row = list_kept_jobs(db_session, _user())[0]
    assert missing_apply_facts(row)[0] == "task_model"
    set_kept_job_task_model(db_session, _user(), job_key="job-1", kind="self_train")
    row = list_kept_jobs(db_session, _user())[0]
    missing = missing_apply_facts(row)
    assert "task_model" not in missing
    assert "selected_models" in missing
    assert "monthly_price" in missing
