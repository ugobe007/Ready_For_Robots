import logging
from worker.celery_worker import celery_app
from app.database import SessionLocal, Base, engine
import app.models
from app.scrapers.scrape_targets import get_urls, get_news_queries

Base.metadata.create_all(bind=engine)
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_hotel_scraper_task(self, urls=None):
    from app.scrapers.hotel_directory_scraper import HotelDirectoryScraper
    urls = urls or get_urls("hotel_dir")
    db = get_db()
    try:
        scraper = HotelDirectoryScraper(db=db)
        scraper.run(urls)
        logger.info("Hotel scraper completed for %d URLs", len(urls))
    except Exception as exc:
        logger.error("Hotel scraper failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_job_scraper_task(self, urls=None, industry=None):
    from app.scrapers.job_board_scraper import JobBoardScraper
    urls = urls or get_urls("job_board", industry=industry)
    db = get_db()
    try:
        scraper = JobBoardScraper(db=db)
        scraper.run(urls)
        logger.info("Job scraper completed for %d URLs", len(urls))
    except Exception as exc:
        logger.error("Job scraper failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_news_scraper_task(self, queries=None, industry=None):
    from app.scrapers.news_scraper import NewsScraper
    queries = queries or get_news_queries(industry=industry)
    db = get_db()
    try:
        scraper = NewsScraper(db=db)
        scraper.run_intent_queries(queries=queries)
        logger.info("News scraper completed for %d queries", len(queries))
    except Exception as exc:
        logger.error("News scraper failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_rss_scraper_task(self, urls=None, industry=None):
    from app.scrapers.news_scraper import NewsScraper
    urls = urls or get_urls("rss_feed", industry=industry)
    db = get_db()
    try:
        scraper = NewsScraper(db=db)
        scraper.run_rss_feeds(urls)         # ← uses direct RSS fetch, not Google News
        logger.info("RSS scraper completed for %d feeds", len(urls))
    except Exception as exc:
        logger.error("RSS scraper failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_serp_scraper_task(self, queries=None):
    """Run targeted SERP-style expansion/automation queries."""
    from app.scrapers.serp_scraper import SerpScraper, EXPANSION_QUERIES
    active_queries = queries or EXPANSION_QUERIES
    db = get_db()
    try:
        scraper = SerpScraper(db=db)
        scraper.run(queries=active_queries)
        logger.info("SERP scraper completed for %d queries", len(active_queries))
    except Exception as exc:
        logger.error("SERP scraper failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_logistics_scraper_task(self, queries=None):
    """Run logistics directory / named-account news queries."""
    from app.scrapers.logistics_directory_scraper import LogisticsDirectoryScraper, LOGISTICS_COMPANY_QUERIES
    active_queries = queries or LOGISTICS_COMPANY_QUERIES
    db = get_db()
    try:
        scraper = LogisticsDirectoryScraper(db=db)
        scraper.run(queries=active_queries)
        logger.info("Logistics scraper completed for %d queries", len(active_queries))
    except Exception as exc:
        logger.error("Logistics scraper failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1, default_retry_delay=30)
def run_all_scrapers_task(self):
    """Trigger all active scraper tasks in sequence."""
    try:
        run_news_scraper_task.delay()
        run_rss_scraper_task.delay()
        run_serp_scraper_task.delay()
        run_logistics_scraper_task.delay()
        run_job_scraper_task.delay()
        run_hotel_scraper_task.delay()
        logger.info("All scraper tasks queued")
    except Exception as exc:
        logger.error("Failed to queue scraper tasks: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def recalculate_scores_task(self, company_id: int):
    from app.services.scoring_engine import compute_scores
    from app.models.company import Company
    from app.models.score import Score
    db = get_db()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            logger.warning("Company %d not found", company_id)
            return
        scores = compute_scores(company, company.signals)
        s = db.query(Score).filter(Score.company_id == company_id).first()
        if not s:
            s = Score(company_id=company_id, **scores)
            db.add(s)
        else:
            for k, v in scores.items():
                setattr(s, k, v)
        db.commit()
        logger.info("Scores recalculated for company %d", company_id)
    except Exception as exc:
        logger.error("Score recalc failed for company %d: %s", company_id, exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def recalculate_all_scores_task(self):
    """
    Recalculate scores for every company in the DB.
    Runs automatically after scrapers have had time to ingest new signals.
    """
    from app.models.company import Company
    from app.models.score import Score
    from app.services.scoring_engine import compute_scores
    db = get_db()
    try:
        companies = db.query(Company).all()
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
            except Exception as e:
                logger.warning("Score recalc skipped company %d: %s", company.id, e)
        db.commit()
        logger.info("Bulk score recalc done — %d companies updated", updated)
    except Exception as exc:
        logger.error("Bulk score recalc failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()        raise self.retry(exc=exc)
    finally:
        db.close()