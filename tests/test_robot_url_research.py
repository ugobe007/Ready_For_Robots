"""Grounded research pass over stored robot URLs — no invented SKUs."""
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.services.robot_submission_service import record_robot_submission
from app.services.robot_url_research import extract_grounded_snippets, research_robot_row


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


def test_snippets_require_same_host_source():
    page = SimpleNamespace(
        url="https://agtonomy.com/",
        final_url="https://agtonomy.com/",
        title="Agtonomy — autonomous farming",
        text="Software for mixed fleets on the farm.",
        links=[],
    )
    out = extract_grounded_snippets(page, host="agtonomy.com")
    assert out
    assert all(s["source_url"].startswith("https://agtonomy.com") for s in out)
    foreign = SimpleNamespace(
        url="https://other.example/news",
        final_url="https://other.example/news",
        title="Unrelated",
        text="Not this company.",
        links=[],
    )
    mixed = extract_grounded_snippets(page, host="agtonomy.com", extra_pages=[foreign])
    assert all("other.example" not in s["source_url"] for s in mixed)


def test_chrome_only_stays_incomplete(db_session):
    row = record_robot_submission(db_session, url="https://www.agtonomy.com/")
    page = SimpleNamespace(
        url="https://agtonomy.com/",
        final_url="https://agtonomy.com/",
        title="Agtonomy",
        text="",
        links=[],
        fetch_degraded=True,
    )

    def fake_fetch(*_a, **_k):
        return page

    result = research_robot_row(
        db_session,
        row,
        budget_sec=2,
        fetch_page=fake_fetch,
        homepage_is_chrome_only=lambda _p: True,
    )
    db_session.refresh(row)
    assert result["status"] == "incomplete"
    assert result.get("chrome_only") is True
    assert row.last_researched_at is not None
    assert row.research_snippets == []
    assert row.product_name is None


def test_grounded_spec_snippet_is_persisted(db_session):
    row = record_robot_submission(db_session, url="https://www.relayrobotics.com/")
    page = SimpleNamespace(
        url="https://relayrobotics.com/",
        final_url="https://relayrobotics.com/",
        title="Relay workplace robot",
        text="Indoor delivery robot for hospitals and hotels.",
        links=[],
    )
    result = research_robot_row(
        db_session,
        row,
        budget_sec=2,
        fetch_page=lambda *_a, **_k: page,
        homepage_is_chrome_only=lambda _p: False,
    )
    db_session.refresh(row)
    assert result["status"] == "complete"
    assert row.research_snippets
    assert row.last_researched_at is not None
    assert "Relay" in row.research_snippets[0]["text"]
    assert row.research_snippets[0]["source_url"].startswith("https://relayrobotics.com")
