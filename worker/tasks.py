import logging
import subprocess
import os
from worker.celery_worker import celery_app
from app.database import SessionLocal
import app.models
from app.scrapers.scrape_targets import get_urls, get_news_queries

# DB schema is managed by Alembic; no create_all at worker startup.
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
def run_intelligence_scraper_task(self, max_articles=10):
    """
    Intelligence News Scraper — discovers new companies from news.
    FREE alternative to LinkedIn, Pitchbook, CB Insights.
    Uses Redis lock to prevent duplicate runs when Beat fires multiple schedules at once.
    """
    import redis
    from worker.celery_worker import celery_app as app
    redis_url = getattr(app.conf, 'broker_url', None) or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    lock_key = "intelligence_scraper_lock"
    lock_ttl = 7200  # 2 hours max (task takes ~10 min)

    r = redis.from_url(redis_url)
    acquired = r.set(lock_key, "1", nx=True, ex=lock_ttl)
    if not acquired:
        logger.info("Intelligence scraper already running (lock held), skipping duplicate task")
        return {"skipped": True, "reason": "another instance is running"}

    try:
        from app.scrapers.intelligence_news_scraper import IntelligenceNewsScraper
        db = get_db()
        try:
            scraper = IntelligenceNewsScraper(db=db)
            stats = scraper.discover_leads(max_articles_per_query=max_articles)
            logger.info(
                "Intelligence scraper completed: %d new companies, %d enriched, %d signals",
                stats['companies_discovered'],
                stats['companies_enriched'],
                stats['signals_created']
            )
            return stats
        except Exception as exc:
            logger.error("Intelligence scraper failed: %s", exc)
            raise self.retry(exc=exc)
        finally:
            db.close()
    finally:
        r.delete(lock_key)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_company_news_task(self, limit=80):
    """
    Company → News: Search news for each company (DB + KNOWN_COMPANIES).
    Correlates XYZ company with news about XYZ. Runs 2x daily.
    """
    from sqlalchemy import func
    from app.scrapers.news_scraper import NewsScraper, KNOWN_COMPANIES
    from app.models.company import Company
    from app.models.signal import Signal

    db = get_db()
    try:
        # Companies from DB (prioritize those with signals = real leads)
        db_companies = (
            db.query(Company.name)
            .outerjoin(Signal)
            .group_by(Company.id, Company.name)
            .order_by(func.count(Signal.id).desc())
            .limit(limit)
            .all()
        )
        company_names = list(dict.fromkeys(c[0] for c in db_companies))

        # Add KNOWN_COMPANIES canonical names we might not have in DB yet
        known_names = set(v[0] for v in KNOWN_COMPANIES.values())
        for name in known_names:
            if name not in company_names:
                company_names.append(name)
            if len(company_names) >= limit + 50:  # Cap total
                break

        if not company_names:
            logger.info("Company news task: no companies to query")
            return {"companies_queried": 0}

        scraper = NewsScraper(db=db)
        scraper.run_company_queries(company_names[:limit], max_per_company=5)
        logger.info("Company news task completed for %d companies", len(company_names[:limit]))
        return {"companies_queried": len(company_names[:limit])}
    except Exception as exc:
        logger.error("Company news task failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_enrich_companies_task(self, limit=50):
    """
    Enrich existing companies by searching news for their names.
    Finds recent signals we may have missed. Run daily.
    After enrichment, queues rectification + CRM extraction for each company.
    """
    from app.scrapers.intelligence_news_scraper import IntelligenceNewsScraper
    db = get_db()
    try:
        scraper = IntelligenceNewsScraper(db=db)
        stats = scraper.enrich_existing_companies(limit=limit)
        logger.info(
            "Enrichment completed: %d enriched, %d signals",
            stats['companies_enriched'],
            stats['signals_created']
        )
        # Queue rectification + CRM extraction after enrichment finishes
        rectify_and_enrich_crm_task.delay(limit=limit)
        return stats
    except Exception as exc:
        logger.error("Enrich companies failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def rectify_and_enrich_crm_task(self, limit=100, hours_since_scraped=48):
    """
    Post-enrichment quality sweep.

    Pipeline per company (in order):
      1. Rectifier — re-ask "what is this?" with full signal context.
           Quarantines (is_internal=False) anything that fails the sniff test.
      2. CRM Extractor — extracts budget, timing, automation requirements,
           and decision makers from signals; writes crm_metadata + contacts.

    Runs automatically after run_enrich_companies_task and is also scheduled
    independently as a nightly sweep.
    """
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import func
    from app.models.company import Company
    from app.models.signal import Signal
    from app.services.rectifier import validate as rectify_validate, quarantine
    from app.services.crm_extractor import extract as crm_extract, build_crm_metadata_dict

    db = get_db()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_since_scraped)

        # Fetch recently active, internal companies (up to limit)
        companies = (
            db.query(Company)
            .filter(Company.is_internal.is_(True))
            .outerjoin(Signal, Signal.company_id == Company.id)
            .group_by(Company.id)
            .having(func.count(Signal.id) > 0)
            .order_by(Company.created_at.desc())
            .limit(limit)
            .all()
        )

        rectified = 0
        quarantined = 0
        crm_enriched = 0

        for company in companies:
            try:
                signals = (
                    db.query(Signal)
                    .filter(Signal.company_id == company.id)
                    .order_by(Signal.created_at.desc())
                    .limit(20)
                    .all()
                )

                # ── Step 1: Rectification ────────────────────────────────────
                result = rectify_validate(company, signals)
                rectified += 1

                if not result.passed:
                    quarantine(company, db, reason=result.reason)
                    quarantined += 1
                    logger.info(
                        "Rectifier quarantined %r (id=%d): %s",
                        company.name, company.id, result.reason,
                    )
                    continue  # skip CRM extraction for quarantined leads

                # ── Step 2: CRM extraction ───────────────────────────────────
                descriptors = crm_extract(company, signals, db)
                metadata = build_crm_metadata_dict(descriptors)

                # Merge with existing crm_metadata (don't wipe prior extractions)
                existing = company.crm_metadata or {}
                existing.update(metadata)
                company.crm_metadata = existing
                db.commit()
                crm_enriched += 1

            except Exception as e:
                logger.warning(
                    "Rectify/CRM failed for company %d (%r): %s",
                    company.id, company.name, e,
                )
                db.rollback()
                continue

        logger.info(
            "Rectify+CRM sweep done — checked=%d quarantined=%d crm_enriched=%d",
            rectified, quarantined, crm_enriched,
        )
        return {
            "checked": rectified,
            "quarantined": quarantined,
            "crm_enriched": crm_enriched,
        }

    except Exception as exc:
        logger.error("rectify_and_enrich_crm_task failed: %s", exc)
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


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_newsletter_edition_task(self, limit=8):
    """
    Generate and cache the daily newsletter edition.
    Runs every 24 hours. Content is used for posting and social sharing.
    """
    from app.services.newsletter_service import generate_edition, write_cached_edition

    db = get_db()
    try:
        data = generate_edition(db, limit=limit)
        write_cached_edition(data)
        count = data.get("summary", {}).get("total_leads", 0)
        logger.info("Newsletter edition generated: %d stories cached", count)
        return {"stories": count, "edition": data.get("latestEdition", {}).get("edition")}
    except Exception as exc:
        logger.error("Newsletter edition failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1, default_retry_delay=30)
def run_all_scrapers_task(self):
    """Trigger all active scraper tasks in sequence."""
    try:
        run_intelligence_scraper_task.delay(max_articles=10)  # FREE lead discovery
        run_news_scraper_task.delay()
        run_company_news_task.delay(limit=80)  # XYZ company → news on XYZ
        run_enrich_companies_task.delay(limit=80)  # Enrich existing companies
        generate_newsletter_edition_task.delay(limit=8)  # Daily newsletter for posting
        run_rss_scraper_task.delay()
        run_serp_scraper_task.delay()
        run_logistics_scraper_task.delay()
        run_job_scraper_task.delay()
        run_hotel_scraper_task.delay()
        logger.info("All scraper tasks queued (including intelligence, company news, enrich)")
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
                
                # Create signal (Signal model: source_url, created_at, signal_strength)
                signal = Signal(
                    company_id=company.id,
                    signal_type=signal_data['signal_type'],
                    signal_text=signal_data['signal_text'],
                    source_url=signal_data.get('url', ''),
                    signal_strength=float(signal_data.get('confidence', 0.85)),
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
                
                # Score model uses overall_intent_score, robotics_fit_score (no tier - computed at query time)
                score.overall_intent_score = score_data.get('overall_intent_score', 0)
                score.automation_score = score_data.get('automation_score', 0)
                score.labor_pain_score = score_data.get('labor_pain_score', 0)
                score.expansion_score = score_data.get('expansion_score', 0)
                score.robotics_fit_score = score_data.get('robotics_fit_score', 0)
                
                db.commit()
            except Exception as e:
                logger.warning(f"Failed to score company {company.id}: {e}")
                db.rollback()
                continue
        
        logger.info(f"Re-scored {len(companies)} companies")
    except Exception as exc:
        logger.error(f"Rescore task failed: {exc}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_junk_leads_task(self):
    """Remove obvious junk: companies with score < 3 and 0 signals. Company has no is_junk column."""
    from app.models.company import Company
    from app.models.score import Score
    from app.models.signal import Signal
    
    db = get_db()
    try:
        low_score_ids = [r[0] for r in db.query(Score.company_id).filter(Score.overall_intent_score < 3).all()]
        junk_ids = [cid for cid in low_score_ids if db.query(Signal).filter(Signal.company_id == cid).count() == 0]
        if not junk_ids:
            logger.info("Cleanup: no junk leads to remove")
            return
        deleted = db.query(Company).filter(Company.id.in_(junk_ids)).delete(synchronize_session=False)
        db.commit()
        logger.info(f"Cleanup task deleted {deleted} junk leads (0 signals, score < 3)")
    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc}")
    finally:
        db.close()


@celery_app.task(bind=True)
def scheduler_heartbeat_task(self):
    """Runs every 2 min. Proves scheduler + worker pipeline is alive. No-op otherwise."""
    logger.info("[HEARTBEAT] Scheduler alive — next scrapers will run at their scheduled times")
    return {"ok": True}


@celery_app.task(bind=True)
def scraper_health_check_task(self):
    """Monitor scraper health and alert on failures (same JSON as app.scrapers.scraper_watchdog)."""
    import json
    from pathlib import Path

    from app.scrapers.scraper_watchdog import HEALTH_LOG_PATH

    health_file = Path(HEALTH_LOG_PATH)

    if health_file.exists():
        try:
            with open(health_file, encoding="utf-8") as f:
                health_data = json.load(f)
            runs = health_data.get("run_history") or []
            failed = [r for r in runs if isinstance(r, dict) and r.get("status") == "failed"]
            if failed:
                names = [r.get("scraper_name", "?") for r in failed[-5:]]
                logger.warning(
                    "Scraper health check: %d failed run(s) in history (recent: %s)",
                    len(failed),
                    names,
                )
            else:
                logger.info(
                    "Scraper health check: ok (%d URL(s) tracked, %d run(s) in history)",
                    len(health_data.get("url_health") or {}),
                    len(runs),
                )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    else:
        logger.info("No health data file yet at %s", health_file)


@celery_app.task(bind=True)
def daily_scraper_report_task(self):
    """
    Daily scraper performance report - actual vs projected metrics
    Runs at 8am UTC daily
    """
    logger.info("[REPORT] Generating daily scraper performance report...")
    
    try:
        # Run the daily report script
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'scripts',
            'daily_scraper_report.py'
        )
        
        import sys
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        
        if result.returncode == 0:
            logger.info("[REPORT] Daily report generated successfully")
            # Log key metrics from report
            for line in result.stdout.split('\n'):
                if 'New Leads' in line or 'Actual:' in line or 'Manufacturing' in line:
                    logger.info(f"[REPORT] {line.strip()}")
        else:
            logger.error(f"[REPORT] Report generation failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"[REPORT] Error generating daily report: {e}")


@celery_app.task(bind=True)
def daily_analytics_report_task(self, days: int = 1):
    """
    Daily opportunity analytics report - automation types, robot needs, ROI, tasks.
    Runs at 9:15am UTC daily (after scrapers + newsletter).
    """
    logger.info("[ANALYTICS] Generating daily opportunity analytics report...")
    try:
        from app.services.daily_analytics_service import get_daily_analytics, format_report_markdown
        from datetime import datetime, timezone

        db = get_db()
        try:
            analytics = get_daily_analytics(db, days=days)
            report_md = format_report_markdown(analytics)
        finally:
            db.close()

        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"daily_analytics_{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, 'w') as f:
            f.write(report_md)

        latest_path = os.path.join(reports_dir, 'daily_analytics_latest.md')
        with open(latest_path, 'w') as f:
            f.write(report_md)

        totals = analytics.get('totals', {})
        logger.info(f"[ANALYTICS] Report saved to {filepath} | Signals: {totals.get('signals', 0)}, Companies: {totals.get('companies_with_signals', 0)}")
    except Exception as e:
        logger.error(f"[ANALYTICS] Error generating daily analytics report: {e}")