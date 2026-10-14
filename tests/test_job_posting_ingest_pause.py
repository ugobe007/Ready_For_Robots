from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.scrapers import opportunity_feed_scraper as feeds
from app.scrapers.job_board_scraper_enhanced import EnhancedJobBoardScraper
from app.scrapers.robot_opportunity_sources import OpportunitySource, catalog
from app.services import job_board_scraper_runner as runner
from app.services.job_posting_ingest_pause import (
    BUYER_SIGNAL,
    FEED_CLASSIFICATION,
    PEOPLE_POSTING,
    job_posting_ingest_paused,
    source_kind_paused,
)

CARD = {"title": "Warehouse Associate - Picker", "company": "Acme Logistics", "location": "Reno, NV",
        "desc": "Apply now, $18/hr", "url": "https://example.com/job/1"}
PEOPLE_KINDS = ("job_board", "amazon_jobs", "greenhouse", "lever", "ashby", "smartrecruiters",
                "workday", "adzuna", "jooble", "usajobs")


def _scraper():
    scraper = EnhancedJobBoardScraper.__new__(EnhancedJobBoardScraper)
    scraper.db = MagicMock()
    scraper.save_company = MagicMock()
    scraper.save_signal = MagicMock()
    scraper.request_count = 0
    scraper.session_seen_fingerprints = set()
    return scraper


def test_paused_by_default(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    assert job_posting_ingest_paused() is True


@pytest.mark.parametrize("value", ["0", "false", "no"])
def test_only_explicit_off_unpauses(monkeypatch, value):
    monkeypatch.setenv("PAUSE_JOB_POSTING_INGEST", value)
    assert job_posting_ingest_paused() is False
    assert not any(source_kind_paused(k) for k in PEOPLE_KINDS)


def test_classification_people_paused_procurement_runs(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    assert {k for k, v in FEED_CLASSIFICATION.items() if v == PEOPLE_POSTING} == set(PEOPLE_KINDS)
    assert {k for k, v in FEED_CLASSIFICATION.items() if v == BUYER_SIGNAL} == {"sam_gov"}
    assert all(source_kind_paused(k) for k in PEOPLE_KINDS)
    assert source_kind_paused("sam_gov") is False
    assert source_kind_paused("some_new_feed") is True


def test_every_card_feed_kind_is_classified():
    card_kinds = {s.kind for s in catalog() if s.kind != "rss_feed"}
    assert card_kinds <= set(FEED_CLASSIFICATION)


def test_job_board_entry_points_touch_nothing(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    monkeypatch.setattr(runner, "job_board_urls", lambda **_: pytest.fail("fetched URLs while paused"))
    assert runner.run_scheduled_job_board_cycle()["status"] == "paused"
    assert runner.run_job_board_scraper_sync(industry="Logistics")["status"] == "paused"


def test_opportunity_feeds_run_only_procurement_while_paused(monkeypatch):
    import app.database

    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    monkeypatch.setattr(app.database, "SessionLocal", MagicMock)
    monkeypatch.setattr(feeds, "discovered_board_sources", lambda db, limit: [
        (MagicMock(), OpportunitySource("greenhouse", "Acme (greenhouse, discovered)", params=(("token", "acme"),)))])
    ran = []
    monkeypatch.setattr(feeds, "run_sources", lambda db, srcs, **_: ran.extend(srcs) or {})
    out = feeds.run_opportunity_feeds()
    assert ran and {s.kind for s in ran} == {"sam_gov"}
    assert out["discovered_boards"] == 0
    assert set(out["paused_kinds"]) == {"adzuna", "amazon_jobs", "greenhouse", "jooble"}


def test_paused_kind_process_cards_writes_nothing(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    for kind in ("job_board", "adzuna"):
        scraper = _scraper()
        stats = scraper.process_cards([CARD], "https://example.com/board", source_kind=kind)
        assert stats["paused"] is True and stats["robot_jobs"] == 0 and stats["signals_only"] == 0
        scraper.save_company.assert_not_called()
        scraper.save_signal.assert_not_called()
        scraper.db.add.assert_not_called()
        scraper.db.commit.assert_not_called()


def test_html_board_default_kind_is_paused(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    assert _scraper().process_cards([CARD], "https://www.indeed.com/jobs?q=x")["paused"] is True


def test_sam_gov_cards_are_not_paused(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    stats = _scraper().process_cards([], "SAM.gov tenders · robot", source_kind="sam_gov")
    assert "paused" not in stats


def test_run_sources_passes_kind_and_skips_ats_registration_for_paused_kinds(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    seen = []
    fake = MagicMock()
    fake.process_cards.side_effect = lambda cards, label, source_kind: seen.append(source_kind) or {}
    monkeypatch.setattr(feeds, "_scraper", lambda db: fake)
    registered = []
    monkeypatch.setattr(feeds, "register_ats_boards_from_text", lambda db, text, found_on="": registered.append(found_on))
    card = {"url": "https://boards.greenhouse.io/acme/jobs/1", "html": ""}
    feeds.run_sources(MagicMock(), [OpportunitySource("adzuna", "a"), OpportunitySource("sam_gov", "s")],
                      fetch=lambda s: [card], pause_s=0)
    assert seen == ["adzuna", "sam_gov"]
    assert registered == ["s"]


def test_manual_job_board_trigger_refused_while_paused(monkeypatch):
    import asyncio

    from app.api.scraper_control import run_specific_scraper

    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(run_specific_scraper("job_boards", MagicMock(), db=MagicMock()))
    assert exc.value.status_code == 409


def test_sam_gov_schedule_defaults_to_the_no_role_daily_cap():
    calls, interval = feeds.sam_gov_schedule(26, daily_limit=10)
    assert calls == 10
    assert interval == 24 * 60
    assert calls * (1440 // interval) <= 10


def test_sam_gov_schedule_stays_inside_a_role_limit():
    calls, interval = feeds.sam_gov_schedule(26, daily_limit=1000)
    assert calls == 26
    assert calls * (1440 // interval) <= 1000


def test_sam_gov_budget_takes_only_as_many_keywords_as_the_cap(monkeypatch):
    sources = [OpportunitySource("sam_gov", f"k{i}", params=(("keyword", str(i)),)) for i in range(26)]
    sources.append(OpportunitySource("rss_feed", "news"))
    monkeypatch.setenv("SAM_GOV_DAILY_REQUEST_LIMIT", "10")
    chosen, interval = feeds._apply_sam_gov_budget(sources)
    sam = [s for s in chosen if s.kind == "sam_gov"]
    assert len(sam) == 10
    assert interval == 24 * 60
    assert any(s.kind == "rss_feed" for s in chosen)
