from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.scrapers import opportunity_feed_scraper as feeds
from app.scrapers.job_board_scraper_enhanced import EnhancedJobBoardScraper
from app.services import job_board_scraper_runner as runner
from app.services.job_posting_ingest_pause import job_posting_ingest_paused

CARD = {"title": "Warehouse Associate - Picker", "company": "Acme Logistics", "location": "Reno, NV",
        "desc": "Apply now, $18/hr", "url": "https://example.com/job/1"}


def test_paused_by_default(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    assert job_posting_ingest_paused() is True


@pytest.mark.parametrize("value", ["0", "false", "no"])
def test_only_explicit_off_unpauses(monkeypatch, value):
    monkeypatch.setenv("PAUSE_JOB_POSTING_INGEST", value)
    assert job_posting_ingest_paused() is False


def test_paused_entry_points_touch_nothing(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    monkeypatch.setattr(runner, "job_board_urls", lambda **_: pytest.fail("fetched URLs while paused"))
    assert runner.run_scheduled_job_board_cycle()["status"] == "paused"
    assert runner.run_job_board_scraper_sync(industry="Logistics")["status"] == "paused"
    monkeypatch.setattr(feeds, "api_sources", lambda *_: pytest.fail("loaded feeds while paused"))
    assert feeds.run_opportunity_feeds()["status"] == "paused"


def test_paused_process_cards_writes_nothing(monkeypatch):
    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    scraper = EnhancedJobBoardScraper.__new__(EnhancedJobBoardScraper)
    scraper.db = MagicMock()
    scraper.save_company = MagicMock()
    scraper.save_signal = MagicMock()
    stats = scraper.process_cards([CARD], "https://example.com/board")
    assert stats["paused"] is True and stats["robot_jobs"] == 0 and stats["signals_only"] == 0
    scraper.save_company.assert_not_called()
    scraper.save_signal.assert_not_called()
    scraper.db.add.assert_not_called()
    scraper.db.commit.assert_not_called()


def test_manual_job_board_trigger_refused_while_paused(monkeypatch):
    import asyncio

    from app.api.scraper_control import run_specific_scraper

    monkeypatch.delenv("PAUSE_JOB_POSTING_INGEST", raising=False)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(run_specific_scraper("job_boards", MagicMock(), db=MagicMock()))
    assert exc.value.status_code == 409
