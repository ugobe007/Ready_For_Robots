"""API feeds + ATS discovery + ontology routing (no network)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.robot_directed_discovery import RobotJob
from app.models.source import Source
from app.scrapers import opportunity_feed_scraper as feeds
from app.scrapers.robot_opportunity_sources import OpportunitySource, catalog, summary


@pytest.fixture(autouse=True)
def _ingest_unpaused(monkeypatch):
    """These tests cover the classify/persist path itself, which stays paused in production."""
    monkeypatch.setenv("PAUSE_JOB_POSTING_INGEST", "0")


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    s = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield s
    finally:
        s.close()


def test_catalog_is_large_and_unique():
    cat = catalog()
    assert 300 <= len(cat) <= 500
    assert len({s.key for s in cat}) == len(cat)
    kinds = summary()
    assert kinds["job_board"] >= 150 and kinds["rss_feed"] >= 50 and kinds["sam_gov"] >= 20


def test_find_ats_boards_from_apply_links():
    html = (
        '<a href="https://boards.greenhouse.io/sweetgreen/jobs/123">apply</a>'
        ' https://jobs.lever.co/shipbob/abc https://jobs.ashbyhq.com/flexport'
        ' https://kroger.wd5.myworkdayjobs.com/en-US/External/job/x'
        ' https://boards.greenhouse.io/embed/job_board?for=cava'
    )
    found = feeds.find_ats_boards(html)
    assert ("greenhouse", "sweetgreen") in found
    assert ("lever", "shipbob") in found
    assert ("ashby", "flexport") in found
    assert ("greenhouse", "cava") in found
    assert ("workday", "kroger.wd5.myworkdayjobs.com", "kroger", "External") in found
    assert not any(b[1] == "embed" for b in found)


def test_register_is_idempotent(db_session):
    text = "https://jobs.lever.co/shipbob/abc"
    assert feeds.register_ats_boards_from_text(db_session, text) == 1
    assert feeds.register_ats_boards_from_text(db_session, text) == 0
    assert db_session.query(Source).filter(Source.source_type == "ats_board").count() == 1


def test_run_sources_routes_operational_work_and_tenders(db_session):
    cards = {
        "jobs": [
            {"title": "Dishwasher", "company": "Wynn Las Vegas", "location": "Las Vegas, NV",
             "desc": "$18-$20 an hour, wash dishes, high volume", "url": "https://x/1", "html": ""},
            {"title": "Order Picker", "company": "Kroger", "location": "Las Vegas, NV",
             "desc": "Pick orders, 150 cases per hour, sign-on bonus, freezer", "url": "https://x/2", "html": ""},
            {"title": "Robotics Software Engineer", "company": "Kroger", "location": "Cincinnati, OH",
             "desc": "perception", "url": "https://x/3", "html": ""},
        ],
        "tender": [
            {"title": "Autonomous Floor Scrubbing Robots", "company": "Clark County Department of Aviation",
             "location": "Las Vegas, NV",
             "desc": "Request for proposals (Solicitation) issued by Clark County: Autonomous Floor Scrubbing Robots.",
             "url": "https://sam.gov/opp/1", "html": ""},
        ],
    }
    srcs = [OpportunitySource("amazon_jobs", "jobs", params=(("query", "x"),)),
            OpportunitySource("sam_gov", "tender", params=(("keyword", "robot"),), needs_env=()),
            OpportunitySource("adzuna", "needs key", params=(("what", "x"),), needs_env=("RFR_TEST_NOT_SET",))]
    out = feeds.run_sources(db_session, srcs, fetch=lambda s: cards["jobs" if s.label == "jobs" else "tender"], pause_s=0)
    assert out["skipped_no_key"] == 1 and out["failed"] == 0
    rows = {r.robot_compatible_task: r for r in db_session.query(RobotJob).all()}
    # Only buyer intent becomes a robot_job; labor postings are company pain signals.
    assert set(rows) == {"Autonomous Floor Scrubbing Robots"}
    assert rows["Autonomous Floor Scrubbing Robots"].opportunity_tier == 1
    from app.models.signal import Signal
    types = {s.signal_text.split("|")[1].strip(): s.signal_type for s in db_session.query(Signal).all()}
    assert types["Dishwasher"] == "labor_pain" and types["Order Picker"] == "labor_pain"
    assert "Robotics Software Engineer" not in types


def test_one_failing_source_does_not_stop_the_sweep(db_session):
    def fetch(src):
        if src.label == "bad":
            raise feeds.SourceGone("404")
        return [{"title": "Janitor", "company": "MGM Resorts", "location": "Las Vegas, NV",
                 "desc": "Operate our new autonomous floor scrubbing robots", "url": "u", "html": ""}]

    out = feeds.run_sources(db_session, [OpportunitySource("lever", "bad"), OpportunitySource("lever", "good")],
                            fetch=fetch, pause_s=0)
    assert out["failed"] == 1 and out["robot_jobs"] == 1
