import logging
import os
import secrets
import subprocess
from typing import Optional

from worker.celery_worker import celery_app
from app.database import SessionLocal
import app.models
from app.scrapers.scrape_targets import get_urls, get_news_queries

# DB schema is managed by Alembic; no create_all at worker startup.
logger = logging.getLogger(__name__)

INTELLIGENCE_SCRAPER_LOCK_KEY = "intelligence_scraper_lock"
_INTELLIGENCE_LOCK_RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
else
  return 0
end
"""


def _release_intelligence_scraper_lock(r, lock_key: str, token: str) -> None:
    """Only the worker that holds ``token`` may delete the lock (avoids deleting another run's lock)."""
    try:
        r.eval(_INTELLIGENCE_LOCK_RELEASE_LUA, 1, lock_key, token)
    except Exception as exc:
        logger.warning("Intelligence lock release failed (non-fatal): %s", exc)


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
    from app.scrapers.job_board_scraper_enhanced import EnhancedJobBoardScraper

    max_urls = int(os.getenv("JOB_SCRAPER_MAX_URLS_PER_RUN", "18"))
    urls = (urls or get_urls("job_board", industry=industry))[:max_urls]
    db = get_db()
    try:
        scraper = EnhancedJobBoardScraper()
        scraper.db = db
        scraper.run(urls)
        logger.info("Job scraper completed for %d URLs", len(urls))
    except Exception as exc:
        logger.error("Job scraper failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_news_scraper_task(self, queries=None, industry=None):
    from app.scrapers.news_scraper_enhanced import EnhancedNewsScraper

    max_queries = int(os.getenv("NEWS_SCRAPER_MAX_QUERIES_PER_RUN", "30"))
    queries = (queries or get_news_queries(industry=industry))[:max_queries]
    db = get_db()
    try:
        scraper = EnhancedNewsScraper(db=db)
        scraper.run_intent_queries(queries=queries)
        logger.info("News scraper completed for %d queries", len(queries))
    except Exception as exc:
        logger.error("News scraper failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_intelligence_scraper_task(
    self,
    max_articles: int = 15,
    max_queries: Optional[int] = 20,
    enrich: bool = True,
    enrich_limit: int = 20,
):
    """
    Intelligence News Scraper — discovers new companies from news.
    FREE alternative to LinkedIn, Pitchbook, CB Insights.

    Uses a Redis lock with a random token so only this execution releases its lock
    (safe under retries / overlapping workers). Default ``max_queries=20`` matches
    the in-app / cron quick run; pass ``max_queries=None`` for a full query list.
    """
    import redis
    from worker.celery_worker import celery_app as app

    redis_url = getattr(app.conf, "broker_url", None) or os.getenv(
        "REDIS_URL", "redis://localhost:6379/0"
    )
    lock_ttl = 7200  # 2 hours ceiling for a run (bounded default ~ minutes)

    r = redis.from_url(redis_url)
    token = secrets.token_urlsafe(24)
    acquired = r.set(INTELLIGENCE_SCRAPER_LOCK_KEY, token, nx=True, ex=lock_ttl)
    if not acquired:
        logger.info(
            "Intelligence scraper already running (lock held), skipping duplicate task"
        )
        return {"skipped": True, "reason": "another instance is running"}

    try:
        from app.scrapers.intelligence_news_scraper import IntelligenceNewsScraper

        db = get_db()
        try:
            scraper = IntelligenceNewsScraper(db=db)
            stats = scraper.discover_leads(
                max_articles_per_query=max_articles,
                max_queries=max_queries,
            )
            if enrich:
                enrich_stats = scraper.enrich_existing_companies(limit=enrich_limit)
                stats["companies_enriched"] = enrich_stats.get(
                    "companies_enriched", stats.get("companies_enriched", 0)
                )
                stats["signals_created"] = stats.get("signals_created", 0) + enrich_stats.get(
                    "signals_created", 0
                )
            logger.info(
                "Intelligence scraper completed: %d new companies, %d enriched, %d signals",
                stats.get("companies_discovered", 0),
                stats.get("companies_enriched", 0),
                stats.get("signals_created", 0),
            )
            return stats
        except Exception as exc:
            logger.error("Intelligence scraper failed: %s", exc)
            raise self.retry(exc=exc)
        finally:
            db.close()
    finally:
        _release_intelligence_scraper_lock(r, INTELLIGENCE_SCRAPER_LOCK_KEY, token)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_humanoid_discovery_task(
    self,
    agent_limit: int = 25,
    news_queries: int = 6,
    rescore_existing: bool = False,
):
    """Discover humanoid startups, AI-score HEIF, upsert humanoid_benchmarks."""
    from app.services.humanoid_discovery import run_humanoid_discovery

    db = get_db()
    try:
        stats = run_humanoid_discovery(
            db,
            use_catalog=True,
            use_robot_companies=True,
            news_queries=news_queries,
            agent_limit=agent_limit,
            rescore_existing=rescore_existing,
        )
        from app.services.humanoid_catalog_cleanup import cleanup_humanoid_benchmarks

        cleanup = cleanup_humanoid_benchmarks(db, dry_run=False)
        stats["cleanup_removed"] = cleanup.get("removed", 0)
        logger.info(
            "Humanoid discovery: +%d inserted, %d updated, %d agent-scored, %d cleanup removed, %d total in DB",
            stats.get("inserted", 0),
            stats.get("updated", 0),
            stats.get("agent_scored", 0),
            stats.get("cleanup_removed", 0),
            stats.get("total_in_db", 0),
        )
        return stats
    except Exception as exc:
        logger.error("Humanoid discovery failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_oem_discovery_task(self, max_queries: int = 30):
    """XBOT / StageGate OEM prospect discovery — robot companies needing show ops infrastructure."""
    from app.services.oem_discovery import run_oem_discovery

    db = get_db()
    try:
        stats = run_oem_discovery(db, max_queries=max_queries)
        logger.info(
            "OEM discovery: %d HOT, %d WARM, %d new robot_companies",
            stats.get("oem_hot", 0),
            stats.get("oem_warm", 0),
            stats.get("robot_companies_created", 0),
        )
        return stats
    except Exception as exc:
        logger.error("OEM discovery failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


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
def research_lead_updates_task(
    self,
    company_id: int,
    dry_run: bool = False,
    lookback_days: int = 30,
):
    """Research one lead and persist cited profile updates + in-app notifications."""
    from app.services.lead_research_agent import research_company_updates

    db = get_db()
    try:
        summary = research_company_updates(
            db,
            int(company_id),
            dry_run=dry_run,
            lookback_days=lookback_days,
            notify=not dry_run,
        )
        return summary.__dict__
    except Exception as exc:
        db.rollback()
        logger.error("Lead research task failed for company %s: %s", company_id, exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1, default_retry_delay=300)
def research_active_leads_task(
    self,
    limit: int = 50,
    dry_run: bool = False,
    lookback_days: int = 30,
):
    """Research a bounded HOT/WARM/saved/recent lead batch."""
    if os.getenv("LEAD_RESEARCH_AGENT_ENABLED", "").strip().lower() not in {"1", "true", "yes", "on"}:
        logger.info("Lead research agent disabled; set LEAD_RESEARCH_AGENT_ENABLED=1 to run scheduled batches")
        return {"skipped": True, "reason": "LEAD_RESEARCH_AGENT_ENABLED is not enabled"}

    from app.services.lead_research_agent import research_active_leads

    db = get_db()
    try:
        return research_active_leads(
            db,
            limit=max(1, min(int(limit), 200)),
            dry_run=dry_run,
            lookback_days=lookback_days,
        )
    except Exception as exc:
        db.rollback()
        logger.error("Active lead research batch failed: %s", exc)
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

                # ── Step 3: Lead inference dossier (problem, robots, timetable) ──
                try:
                    from app.services.lead_inference_engine import refresh_company_inference
                    refresh_company_inference(company, signals, db)
                except Exception as inf_exc:
                    logger.warning(
                        "Lead inference refresh failed for company %d (%r): %s",
                        company.id, company.name, inf_exc,
                    )
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


@celery_app.task(bind=True, max_retries=2, default_retry_delay=180)
def lead_secondary_pass_task(
    self,
    limit: int = 120,
    min_score: float = 15.0,
    use_llm: bool = True,
    rescore: bool = True,
):
    """
    Second-pass rescue batch — fill missing website, industry, contacts, CRM fields,
    and inference dossiers on leads already in the corpus (decoupled from scrapers).
    """
    from app.services.lead_secondary_pass import run_secondary_pass_batch_and_refresh_caches

    try:
        stats = run_secondary_pass_batch_and_refresh_caches(
            limit=limit,
            min_score=min_score,
            use_llm=use_llm,
            rescore=rescore,
        )
        logger.info(
            "Lead secondary pass: %d candidates, %d fields filled, %d errors",
            stats.get("candidates", 0),
            stats.get("fields_filled_total", 0),
            stats.get("errors", 0),
        )
        return stats
    except Exception as exc:
        logger.error("lead_secondary_pass_task failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=180)
def humanoid_secondary_pass_task(
    self,
    limit: int = 40,
    sparse_threshold_pct: float = 85.0,
    use_llm_scrape: bool = True,
    persist_deployment_news: bool = True,
    deployment_query_cap: int = 24,
):
    """Humanoid benchmark secondary pass — spec gaps, cited news, capability rank."""
    from app.services.humanoid_secondary_pass import run_humanoid_secondary_pass_batch_and_refresh_caches

    try:
        stats = run_humanoid_secondary_pass_batch_and_refresh_caches(
            limit=limit,
            sparse_threshold_pct=sparse_threshold_pct,
            use_llm_scrape=use_llm_scrape,
            persist_deployment_news=persist_deployment_news,
            deployment_query_cap=deployment_query_cap,
        )
        logger.info(
            "Humanoid secondary pass: %d candidates, %d processed, %d errors",
            stats.get("candidates", 0),
            stats.get("processed", 0),
            stats.get("errors", 0),
        )
        return stats
    except Exception as exc:
        logger.error("humanoid_secondary_pass_task failed: %s", exc)
        raise self.retry(exc=exc)


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
    from app.scrapers.serp_scraper_enhanced import EnhancedSerpScraper, EXPANSION_QUERIES

    max_queries = int(os.getenv("SERP_SCRAPER_MAX_QUERIES_PER_RUN", "24"))
    active_queries = (queries or EXPANSION_QUERIES)[:max_queries]
    db = get_db()
    try:
        scraper = EnhancedSerpScraper(db=db)
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


def _run_public_surface_refresh() -> dict:
    from app.services.public_surface_cache import hydrate_public_surface_caches, refresh_all_public_surface_caches

    db = get_db()
    try:
        stats = refresh_all_public_surface_caches(db)
        hydrate_public_surface_caches()
        return stats
    finally:
        db.close()


def _run_pipeline_surface_refresh() -> dict:
    from app.services.public_surface_cache import (
        hydrate_public_surface_caches,
        refresh_newsletter_surface_cache,
        refresh_pipeline_surface_caches,
    )

    db = get_db()
    try:
        stats = refresh_pipeline_surface_caches(db)
        stats.update(refresh_newsletter_surface_cache(db, force=False))
        hydrate_public_surface_caches()
        return stats
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def refresh_public_surface_caches_task(self):
    """
    Rebuild all public page caches once each morning (newsletter, pipeline, homepage,
    summaries, humanoid report). GET handlers serve these read-only — never regenerate on load.
    """
    try:
        stats = _run_public_surface_refresh()
        logger.info("Public surface caches refreshed: %s", stats)
        return stats
    except Exception as exc:
        logger.error("Public surface cache refresh failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def refresh_pipeline_caches_task(self):
    """
    Rebuild pipeline/public page caches every 2 hours (homepage, summary, leads,
    humanoid) plus incremental newsletter when signals changed.
    """
    try:
        stats = _run_pipeline_surface_refresh()
        logger.info("Pipeline surface caches refreshed (2h): %s", stats)
        return stats
    except Exception as exc:
        logger.error("Pipeline surface cache refresh failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=90)
def incremental_newsletter_update_task(self):
    """
    Post-scraper check (10:00 UTC). Rebuilds only when lead/signal fingerprint changed;
    otherwise rolls edition metadata forward from the library.
    """
    from app.services.newsletter_library import build_daily_newsletter_edition
    from app.services.newsletter_service import write_cached_edition
    from app.services.newsletter_snapshot import publish_api_snapshot
    from app.services.public_surface_cache import hydrate_public_surface_caches

    db = get_db()
    try:
        edition = build_daily_newsletter_edition(db, limit=15, force=False, skip_openai_brief=False)
        write_cached_edition(edition, db)
        publish_api_snapshot(db, edition, limit=15)
        hydrate_public_surface_caches()
        meta = edition.get("_meta") or {}
        logger.info(
            "Incremental newsletter update: mode=%s stories=%d",
            meta.get("update_mode"),
            len(edition.get("topStories") or []),
        )
        return {
            "update_mode": meta.get("update_mode"),
            "stories": len(edition.get("topStories") or []),
        }
    except Exception as exc:
        logger.error("Incremental newsletter update failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


def _newsletter_publish_window_open() -> bool:
    """True only at 6:00am America/Los_Angeles (handles PST/PDT via 13+14 UTC cron)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    la = datetime.now(ZoneInfo("America/Los_Angeles"))
    return la.hour == 6 and la.minute < 10


@celery_app.task(bind=True, max_retries=2, default_retry_delay=180)
def publish_newsletter_daily_task(self):
    """
    Daily newsletter publish — 6:00 America/Los_Angeles.
    Full rebuild + API snapshot; GET /api/newsletter/edition serves read-only.
    """
    if not _newsletter_publish_window_open():
        logger.info("Newsletter daily publish skipped (outside 6am Pacific window)")
        return {"skipped": True, "reason": "outside_6am_pacific"}

    from app.services.newsletter_library import build_daily_newsletter_edition
    from app.services.newsletter_service import write_cached_edition
    from app.services.newsletter_snapshot import get_newsletter_mem_cache, publish_api_snapshot
    from app.services.public_surface_cache import hydrate_public_surface_caches

    cached = get_newsletter_mem_cache()
    if cached:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        gen = (cached.get("summary") or {}).get("generated_at")
        if gen:
            try:
                gen_dt = datetime.fromisoformat(str(gen).replace("Z", "+00:00"))
                la_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
                if gen_dt.astimezone(ZoneInfo("America/Los_Angeles")).date() == la_today:
                    logger.info("Newsletter daily publish skipped (already published today)")
                    return {"skipped": True, "reason": "already_published_today"}
            except Exception:
                pass

    db = get_db()
    try:
        edition = build_daily_newsletter_edition(db, limit=15, force=True, skip_openai_brief=False)
        write_cached_edition(edition, db)
        publish_api_snapshot(db, edition, limit=15)
        from app.services.public_surface_cache import refresh_pipeline_surface_caches

        pipeline_stats = refresh_pipeline_surface_caches(db)
        hydrate_public_surface_caches()
        meta = edition.get("_meta") or {}
        logger.info(
            "Daily newsletter published: mode=%s stories=%d homepage_leads=%d",
            meta.get("update_mode"),
            len(edition.get("topStories") or []),
            pipeline_stats.get("homepage_hot_leads", 0),
        )
        return {
            "update_mode": meta.get("update_mode"),
            "stories": len(edition.get("topStories") or []),
            "published_at": (edition.get("summary") or {}).get("generated_at"),
            "homepage_rotation_day": pipeline_stats.get("homepage_rotation_day"),
        }
    except Exception as exc:
        logger.error("Daily newsletter publish failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def refresh_robots_page_surfaces_task(self):
    """
    Rebuild /robots page snapshots every 3 hours — robot list + HEIR intelligence report.
    GET handlers serve read-only from durable cache + L1.
    """
    from app.services.public_surface_cache import (
        hydrate_public_surface_caches,
        refresh_robots_page_surface_caches,
    )

    db = get_db()
    try:
        stats = refresh_robots_page_surface_caches(db)
        hydrate_public_surface_caches()
        logger.info("Robots page surface caches refreshed: %s", stats)
        return stats
    except Exception as exc:
        logger.error("Robots page surface cache refresh failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_newsletter_edition_task(self, limit=15):
    """Legacy task name — runs the full public-surface daily refresh."""
    try:
        stats = _run_public_surface_refresh()
        logger.info("Newsletter/public surfaces refreshed (legacy task): %s", stats)
        return stats
    except Exception as exc:
        logger.error("Newsletter edition failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=30)
def run_all_scrapers_task(self):
    """Trigger all active scraper tasks in sequence."""
    try:
        run_intelligence_scraper_task.delay()  # bounded defaults (20 queries + enrich)
        run_news_scraper_task.delay()
        run_company_news_task.delay(limit=80)  # XYZ company → news on XYZ
        run_enrich_companies_task.delay(limit=80)  # Enrich existing companies
        generate_newsletter_edition_task.delay(limit=15)  # Daily public surface refresh
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
                    from app.services.company_validator import is_valid_lead

                    cname = signal_data.get("company_name") or ""
                    ok, reason = is_valid_lead(cname)
                    if not ok:
                        logger.debug(
                            "RFP marketplace: skip invalid company name %r — %s",
                            cname,
                            reason,
                        )
                        continue
                    company = Company(
                        name=cname,
                        industry=signal_data.get("industry"),
                        source=signal_data["source"],
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


@celery_app.task(bind=True)
def run_outreach_sequences_task(self, limit: int = 50):
    """Process due outreach sequence enrollments (follow-up cadence)."""
    from app.services.sequence_runner import process_due_enrollments

    db = get_db()
    try:
        result = process_due_enrollments(db, limit=limit)
        logger.info("[SEQUENCES] Processed due enrollments: %s", result)
        return result
    except Exception as exc:
        logger.error("[SEQUENCES] Sequence runner failed: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()