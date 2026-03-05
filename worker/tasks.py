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
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_rfp_marketplace_scraper_task(self):
    """
    Scrape RFP marketplaces for direct buyer intent signals.
    HIGH-VALUE: Companies posting automation projects are ready to buy.
    """
    from app.scrapers.rfp_marketplace_scraper import scrape_rfp_marketplaces
    from app.models.company import Company
    from app.models.signal import Signal
    
    db = get_db()
    try:
        signals = scrape_rfp_marketplaces()
        logger.info(f"RFP marketplace scraper found {len(signals)} signals")
        
        # Process signals and create/update companies
        for signal_data in signals:
            try:
                # Find or create company
                company = db.query(Company).filter(
                    Company.name == signal_data['company_name']
                ).first()
                
                if not company:
                    company = Company(
                        name=signal_data['company_name'],
                        industry=signal_data.get('industry'),
                        source=signal_data['source']
                    )
                    db.add(company)
                    db.flush()
                
                # Create signal
                signal = Signal(
                    company_id=company.id,
                    signal_type=signal_data['signal_type'],
                    signal_text=signal_data['signal_text'],
                    url=signal_data['url'],
                    detected_at=signal_data['detected_at'],
                    confidence=signal_data.get('confidence', 0.85)
                )
                db.add(signal)
                
            except Exception as e:
                logger.warning(f"Failed to process RFP signal: {e}")
                continue
        
        db.commit()
        logger.info("RFP marketplace scraper completed successfully")
        
    except Exception as exc:
        logger.error(f"RFP marketplace scraper failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_manufacturing_news_task(self):
    """
    Dedicated manufacturing signal scraper
    Searches for: quality bottlenecks, safety incidents, production capacity,
    warehouse throughput, packaging automation, repetitive processes, material handling
    """
    from app.scrapers.news_scraper import NewsScraper
    
    manufacturing_queries = [
        "quality control problems manufacturing",
        "production bottleneck factory",
        "workplace safety incident manufacturing",
        "warehouse automation fulfillment",
        "packaging line automation",
        "repetitive manufacturing tasks",
        "material handling forklift",
        "production capacity expansion",
        "manufacturing labor shortage",
        "factory automation investment",
    ]
    
    db = get_db()
    try:
        scraper = NewsScraper(db=db)
        scraper.run_intent_queries(queries=manufacturing_queries)
        logger.info(f"Manufacturing news scraper completed {len(manufacturing_queries)} queries")
    except Exception as exc:
        logger.error(f"Manufacturing news scraper failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_linkedin_scraper_task(self, max_companies=50):
    """
    LinkedIn company scraper (requires authentication)
    Note: Use LinkedIn Sales Navigator API or Phantombuster for production
    """
    logger.info("LinkedIn scraper task - requires API authentication")
    logger.info("Implement LinkedIn Sales Navigator API or Phantombuster integration")
    # TODO: Integrate with LinkedIn API when credentials available
    pass


@celery_app.task(bind=True)
def rescore_all_companies_task(self):
    """Re-score all companies after new signals have been collected"""
    from app.models.company import Company
    from app.models.signal import Signal
    from app.models.score import Score
    from app.services.scoring_engine import compute_scores
    from app.services.lead_filter import classify_lead
    
    db = get_db()
    try:
        companies = db.query(Company).all()
        for company in companies:
            try:
                signals = db.query(Signal).filter(Signal.company_id == company.id).all()
                score_data = compute_scores(company, signals)
                
                score = db.query(Score).filter(Score.company_id == company.id).first()
                if not score:
                    score = Score(company_id=company.id)
                    db.add(score)
                
                score.overall_score = score_data.get('overall_score', 0)
                score.automation_score = score_data.get('automation_score', 0)
                score.labor_pain_score = score_data.get('labor_pain_score', 0)
                score.expansion_score = score_data.get('expansion_score', 0)
                score.market_fit_score = score_data.get('market_fit_score', 0)
                
                tier_data = classify_lead(company, signals, score_data)
                score.tier = tier_data.get('tier', 'COLD')
                
            except Exception as e:
                logger.warning(f"Failed to score company {company.id}: {e}")
                continue
        
        db.commit()
        logger.info(f"Re-scored {len(companies)} companies")
    except Exception as exc:
        logger.error(f"Rescore task failed: {exc}")
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_junk_leads_task(self):
    """Remove leads marked as junk or with very low scores"""
    from app.models.company import Company
    
    db = get_db()
    try:
        # Delete companies marked as junk
        deleted = db.query(Company).filter(Company.is_junk == True).delete()
        db.commit()
        logger.info(f"Cleanup task deleted {deleted} junk leads")
    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc}")
    finally:
        db.close()


@celery_app.task(bind=True)
def scraper_health_check_task(self):
    """Monitor scraper health and alert on failures"""
    import json
    from pathlib import Path
    
    health_file = Path("/tmp/scraper_health.json")
    
    if health_file.exists():
        try:
            with open(health_file) as f:
                health_data = json.load(f)
            
            # Check for failures
            failures = [k for k, v in health_data.items() if v.get('status') == 'failed']
            
            if failures:
                logger.warning(f"Scraper health check: {len(failures)} scrapers failing: {failures}")
            else:
                logger.info("Scraper health check: All scrapers operational")
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    else:
        logger.info("No health data available yet")