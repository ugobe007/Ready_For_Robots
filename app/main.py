import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.api import leads, companies, scoring
from app.api.analyze import router as analyze_router
from app.api.scraper_health import router as scraper_health_router
from app.api.admin import router as admin_router
from app.api.agent import router as agent_router
from app.api.search import router as search_router
from app.api.trending import router as trending_router
from app.api.user import router as user_router
from app.database import Base, engine, SessionLocal
import app.models

Base.metadata.create_all(bind=engine)
logger = logging.getLogger(__name__)

# ── Scheduled scraper jobs (run directly — no Celery/Redis needed) ─────────

def _db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise

def job_news():
    from app.scrapers.news_scraper import NewsScraper
    from app.scrapers.scrape_targets import get_news_queries
    db = _db()
    try:
        logger.info("[scheduler] news scraper starting")
        NewsScraper(db=db).run_intent_queries(queries=get_news_queries())
        logger.info("[scheduler] news scraper done")
    except Exception as e:
        logger.error("[scheduler] news scraper error: %s", e)
    finally:
        db.close()

def job_rss():
    from app.scrapers.news_scraper import NewsScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    try:
        logger.info("[scheduler] rss scraper starting")
        NewsScraper(db=db).run_rss_feeds(get_urls("rss_feed"))
        logger.info("[scheduler] rss scraper done")
    except Exception as e:
        logger.error("[scheduler] rss scraper error: %s", e)
    finally:
        db.close()

def job_jobs():
    from app.scrapers.job_board_scraper import JobBoardScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    try:
        logger.info("[scheduler] job board scraper starting")
        JobBoardScraper(db=db).run(get_urls("job_board"))
        logger.info("[scheduler] job board scraper done")
    except Exception as e:
        logger.error("[scheduler] job board scraper error: %s", e)
    finally:
        db.close()

def job_hotel():
    from app.scrapers.hotel_directory_scraper import HotelDirectoryScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    try:
        logger.info("[scheduler] hotel scraper starting")
        HotelDirectoryScraper(db=db).run(get_urls("hotel_dir"))
        logger.info("[scheduler] hotel scraper done")
    except Exception as e:
        logger.error("[scheduler] hotel scraper error: %s", e)
    finally:
        db.close()

def job_serp():
    from app.scrapers.serp_scraper import SerpScraper, EXPANSION_QUERIES
    db = _db()
    try:
        logger.info("[scheduler] serp scraper starting")
        SerpScraper(db=db).run(queries=EXPANSION_QUERIES)
        logger.info("[scheduler] serp scraper done")
    except Exception as e:
        logger.error("[scheduler] serp scraper error: %s", e)
    finally:
        db.close()

def job_logistics():
    from app.scrapers.logistics_directory_scraper import LogisticsDirectoryScraper, LOGISTICS_COMPANY_QUERIES
    db = _db()
    try:
        logger.info("[scheduler] logistics scraper starting")
        LogisticsDirectoryScraper(db=db).run(queries=LOGISTICS_COMPANY_QUERIES)
        logger.info("[scheduler] logistics scraper done")
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
        logger.info("[scheduler] score recalc starting")
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
            except Exception as ex:
                logger.warning("[scheduler] score skip company %d: %s", company.id, ex)
        db.commit()
        logger.info("[scheduler] score recalc done — %d companies", updated)
    except Exception as e:
        logger.error("[scheduler] score recalc error: %s", e)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler(timezone="UTC")
    # News + RSS — every 4 hours (freshest signals)
    scheduler.add_job(job_news,        CronTrigger(minute=0,  hour="*/4"),  id="news",     replace_existing=True)
    scheduler.add_job(job_rss,         CronTrigger(minute=20, hour="*/4"),  id="rss",      replace_existing=True)
    # Job boards + hotels — every 12 hours
    scheduler.add_job(job_jobs,        CronTrigger(minute=45, hour="*/12"), id="jobs",     replace_existing=True)
    scheduler.add_job(job_hotel,       CronTrigger(minute=15, hour="*/12"), id="hotel",    replace_existing=True)
    # SERP + logistics — once daily at 06:00 UTC
    scheduler.add_job(job_serp,        CronTrigger(minute=0,  hour=6),      id="serp",     replace_existing=True)
    scheduler.add_job(job_logistics,   CronTrigger(minute=30, hour=6),      id="logistics",replace_existing=True)
    # Score recalc — every 6 hours
    scheduler.add_job(job_score_recalc,CronTrigger(minute=0,  hour="*/6"),  id="scores",   replace_existing=True)
    scheduler.start()
    logger.info("[scheduler] started — news/rss every 4h, jobs/hotel every 12h, serp/logistics daily 06:00 UTC, scores every 6h")
    yield
    scheduler.shutdown(wait=False)
    logger.info("[scheduler] shut down")

app = FastAPI(title="Ready for Robots", docs_url="/api/docs", redoc_url="/api/redoc", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes (must come before catch-all) ────────────────────────────────
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["scoring"])
app.include_router(analyze_router, prefix="/api", tags=["analyze"])
app.include_router(scraper_health_router, prefix="/api", tags=["scraper-health"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(trending_router, prefix="/api/trending", tags=["trending"])
app.include_router(user_router,    prefix="/api/user",     tags=["user"])

@app.get("/health")
def health():
    return {"status": "ok"}

# ── Static frontend (Next.js export) ──────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

if os.path.exists(STATIC_DIR):
    # Mount Next.js chunk assets at /_next
    _next = os.path.join(STATIC_DIR, "_next")
    if os.path.exists(_next):
        app.mount("/_next", StaticFiles(directory=_next), name="nextjs_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        # 1. Exact file (e.g. favicon.ico)
        candidate = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        # 2. /admin/ → static/admin/index.html  (trailingSlash export)
        idx = os.path.join(STATIC_DIR, full_path, "index.html")
        if os.path.isfile(idx):
            return FileResponse(idx)
        # 3. /admin → static/admin.html
        html = os.path.join(STATIC_DIR, full_path + ".html")
        if os.path.isfile(html):
            return FileResponse(html)
        # 4. Root
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "Ready for Robots API", "docs": "/api/docs"}