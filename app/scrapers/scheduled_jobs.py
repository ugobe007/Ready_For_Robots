"""
Scheduled scraper job functions
================================
Extracted here so they can be imported by both:
  - app/main.py (APScheduler lifespan)
  - app/api/admin.py (manual trigger endpoint)

All functions are synchronous — safe to call from FastAPI BackgroundTasks
or directly from an APScheduler job.
"""

import logging
from app.database import SessionLocal
from app.scrapers.scraper_watchdog import get_watchdog

logger = logging.getLogger(__name__)


def _db():
    return SessionLocal()


def job_news():
    from app.scrapers.news_scraper import NewsScraper
    from app.scrapers.scrape_targets import get_news_queries
    db = _db()
    queries = get_news_queries()
    try:
        with get_watchdog().track("news") as run:
            run.urls_attempted = len(queries)
            scraper = NewsScraper(db=db)
            scraper.run_intent_queries(queries=queries)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] news scraper error: %s", e)
    finally:
        db.close()


def job_rss():
    from app.scrapers.news_scraper import NewsScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    urls = get_urls("rss_feed")
    try:
        with get_watchdog().track("rss") as run:
            run.urls_attempted = len(urls)
            scraper = NewsScraper(db=db)
            scraper.run_rss_feeds(urls)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] rss scraper error: %s", e)
    finally:
        db.close()


def job_jobs():
    from app.scrapers.job_board_scraper import JobBoardScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    urls = get_urls("job_board")
    try:
        with get_watchdog().track("job_board") as run:
            run.urls_attempted = len(urls)
            scraper = JobBoardScraper(db=db)
            scraper.run(urls)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] job board scraper error: %s", e)
    finally:
        db.close()


def job_hotel():
    from app.scrapers.hotel_directory_scraper import HotelDirectoryScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    urls = get_urls("hotel_dir")
    try:
        with get_watchdog().track("hotel") as run:
            run.urls_attempted = len(urls)
            scraper = HotelDirectoryScraper(db=db)
            scraper.run(urls)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] hotel scraper error: %s", e)
    finally:
        db.close()


def job_serp():
    from app.scrapers.serp_scraper import SerpScraper, EXPANSION_QUERIES
    db = _db()
    try:
        with get_watchdog().track("serp") as run:
            run.urls_attempted = len(EXPANSION_QUERIES)
            scraper = SerpScraper(db=db)
            scraper.run(queries=EXPANSION_QUERIES)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] serp scraper error: %s", e)
    finally:
        db.close()


def job_logistics():
    from app.scrapers.logistics_directory_scraper import LogisticsDirectoryScraper, LOGISTICS_COMPANY_QUERIES
    db = _db()
    try:
        with get_watchdog().track("logistics") as run:
            run.urls_attempted = len(LOGISTICS_COMPANY_QUERIES)
            scraper = LogisticsDirectoryScraper(db=db)
            scraper.run(queries=LOGISTICS_COMPANY_QUERIES)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] logistics scraper error: %s", e)
    finally:
        db.close()


def job_score_recalc():
    from app.models.company import Company
    from app.models.score import Score
    from app.services.scoring_engine import compute_scores
    db = _db()
    try:
        with get_watchdog().track("score_recalc") as run:
            companies = db.query(Company).all()
            run.urls_attempted = len(companies)
            updated = 0
            for company in companies:
                try:
                    scores = compute_scores(company, company.signals or [])
                    s = db.query(Score).filter(Score.company_id == company.id).first()
                    if not s:
                        s = Score(company_id=company.id, **scores)
                        db.add(s)
                    else:
                        for k, v in scores.items():
                            setattr(s, k, v)
                    updated += 1
                except Exception as ex:
                    run.errors.append(f"company {company.id}: {ex}")
                    logger.warning("[scheduler] score skip company %d: %s", company.id, ex)
            db.commit()
            run.urls_succeeded = updated
            logger.info("[scheduler] score recalc done — %d companies", updated)
    except Exception as e:
        logger.error("[scheduler] score recalc error: %s", e)
    finally:
        db.close()


def job_all():
    """Run all scrapers sequentially."""
    job_news()
    job_rss()
    job_jobs()
    job_hotel()
    job_serp()
    job_logistics()
    job_score_recalc()
