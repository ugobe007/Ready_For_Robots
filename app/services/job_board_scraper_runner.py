"""In-process job-board runner — Fly worker path (SKIP_CELERY=1).

Celery Beat still exists for local/Redis setups. Production Fly does not consume
Beat, so this runner is what actually extracts Robot Jobs onto ``robot_jobs``.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional, Sequence

logger = logging.getLogger(__name__)

DEFAULT_INDUSTRY_ROTATION = (
    "Hospitality",
    "Logistics",
    "Healthcare",
    "Food Service",
)


def job_scraper_max_urls() -> int:
    return int(os.getenv("JOB_SCRAPER_MAX_URLS_PER_RUN", "18"))


def scheduled_industries() -> list[str]:
    raw = (os.getenv("JOB_BOARD_INDUSTRIES") or "").strip()
    if not raw:
        return list(DEFAULT_INDUSTRY_ROTATION)
    return [part.strip() for part in raw.split(",") if part.strip()]


def job_board_urls(
    *,
    industry: Optional[str] = None,
    max_urls: Optional[int] = None,
) -> list[str]:
    from app.scrapers.scrape_targets import get_targets

    cap = int(max_urls) if max_urls is not None else job_scraper_max_urls()
    targets = get_targets("job_board", industry=industry)
    robot_first = [t for t in targets if "robot_job" in (t.signal_types or [])]
    seen = {id(t) for t in robot_first}
    rest = [t for t in targets if id(t) not in seen]
    return [t.url for t in (robot_first + rest)][:cap]


def run_job_board_scraper_sync(
    *,
    industry: Optional[str] = None,
    urls: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """Scrape job boards in-process and persist Robot Jobs. Never raises for empty URL lists."""
    from app.database import SessionLocal
    from app.scrapers.job_board_scraper_enhanced import EnhancedJobBoardScraper

    if urls is not None:
        start_urls = list(urls)[: job_scraper_max_urls()]
    else:
        start_urls = job_board_urls(industry=industry)
    label = industry or "all"
    if not start_urls:
        logger.warning("Job board scraper skipped: 0 URLs industry=%s", label)
        return {"status": "skipped", "reason": "no_urls", "industry": label, "urls": 0}

    db = SessionLocal()
    try:
        scraper = EnhancedJobBoardScraper()
        scraper.db = db
        scraper.run(start_urls)
        logger.info(
            "Job board scraper completed industry=%s urls=%d",
            label,
            len(start_urls),
        )
        return {"status": "ok", "industry": label, "urls": len(start_urls)}
    except Exception:
        logger.exception("Job board scraper failed industry=%s", label)
        raise
    finally:
        db.close()


def run_scheduled_job_board_cycle() -> dict[str, Any]:
    """One Beat-equivalent pass: each industry in isolation so one failure cannot abort the rest."""
    results: list[dict[str, Any]] = []
    for industry in scheduled_industries():
        try:
            results.append(run_job_board_scraper_sync(industry=industry))
        except Exception as exc:
            results.append(
                {
                    "status": "failed",
                    "industry": industry,
                    "error": str(exc)[:240],
                }
            )
    ok = sum(1 for row in results if row.get("status") == "ok")
    skipped = sum(1 for row in results if row.get("status") == "skipped")
    failed = sum(1 for row in results if row.get("status") == "failed")
    logger.info(
        "Job board cycle finished ok=%s skipped=%s failed=%s",
        ok,
        skipped,
        failed,
    )
    return {
        "status": "completed",
        "ok": ok,
        "skipped": skipped,
        "failed": failed,
        "industries": results,
    }
