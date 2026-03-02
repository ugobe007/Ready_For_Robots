import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
from app.api import leads, companies, scoring
from app.api.analyze import router as analyze_router
from app.api.scraper_health import router as scraper_health_router
from app.api.admin import router as admin_router
from app.api.agent import router as agent_router
from app.api.search import router as search_router
from app.api.trending import router as trending_router
from app.api.user import router as user_router
from app.api.strategy import router as strategy_router
from app.api.intelligence import router as intelligence_router
from app.database import Base, engine, SessionLocal
from app.scrapers.scheduled_jobs import (
    job_news, job_rss, job_jobs, job_hotel,
    job_serp, job_logistics, job_score_recalc, job_intelligence,
    job_publish_daily_top25, job_enrich_contacts,
)
from app.scrapers.intelligence_scraper import _ensure_table as _ensure_intelligence_table
import app.models

Base.metadata.create_all(bind=engine)
logger = logging.getLogger(__name__)


def _ensure_user_tables():
    """Create user-facing tables if they don't exist.
    These are not part of the SQLAlchemy ORM models so Base.metadata.create_all
    doesn't cover them — we create them here with raw SQL on every startup."""
    ddl = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id           UUID        PRIMARY KEY,
            email        TEXT        NOT NULL,
            display_name TEXT,
            created_at   TIMESTAMPTZ DEFAULT now(),
            updated_at   TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS user_saved_companies (
            id           SERIAL      PRIMARY KEY,
            user_id      UUID        NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            company_id   INTEGER     NOT NULL,
            company_name TEXT        NOT NULL,
            industry     TEXT,
            tier         TEXT,
            score        NUMERIC(6,2),
            website      TEXT,
            notes        TEXT,
            saved_at     TIMESTAMPTZ DEFAULT now(),
            UNIQUE (user_id, company_id)
        );

        CREATE TABLE IF NOT EXISTS user_lists (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID        NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            name        TEXT        NOT NULL,
            description TEXT,
            created_at  TIMESTAMPTZ DEFAULT now(),
            updated_at  TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS user_list_companies (
            id           SERIAL      PRIMARY KEY,
            list_id      UUID        NOT NULL REFERENCES user_lists(id) ON DELETE CASCADE,
            company_id   INTEGER     NOT NULL,
            company_name TEXT        NOT NULL,
            added_at     TIMESTAMPTZ DEFAULT now(),
            UNIQUE (list_id, company_id)
        );

        CREATE TABLE IF NOT EXISTS ai_reports (
            id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id      UUID        NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            company_id   INTEGER     NOT NULL,
            company_name TEXT        NOT NULL,
            title        TEXT,
            report_data  JSONB,
            summary_card JSONB,
            created_at   TIMESTAMPTZ DEFAULT now(),
            updated_at   TIMESTAMPTZ DEFAULT now()
        );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(ddl))
        logger.info("[startup] user tables ensured")
    except Exception as exc:
        logger.error(f"[startup] failed to create user tables: {exc}")


def _db_keepalive():
    """Ping the database every 2 minutes to prevent Supabase from sleeping
    and to keep the SQLAlchemy connection pool alive."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.debug("[keepalive] DB ping OK")
    except Exception as exc:
        logger.warning(f"[keepalive] DB ping failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure user tables exist (raw-SQL tables not covered by ORM)
    _ensure_user_tables()
    # Ensure intelligence table + migrations (adds relevance_score if missing)
    _ensure_intelligence_table()
    # Warm the DB connection on startup so the first user request isn't slow
    _db_keepalive()
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
    scheduler.add_job(job_score_recalc,  CronTrigger(minute=0,  hour="*/6"), id="scores",        replace_existing=True)
    # Strategic intelligence — once daily at 07:00 UTC
    scheduler.add_job(job_intelligence,         CronTrigger(minute=0,  hour=7),    id="intelligence",         replace_existing=True)
    # Contact enrichment — once daily at 06:45 UTC (before the daily brief)
    scheduler.add_job(job_enrich_contacts,      CronTrigger(minute=45, hour=6),    id="enrich_contacts",       replace_existing=True)
    # Publish daily top-25 brief — once daily at 07:30 UTC (after intelligence + enrichment)
    scheduler.add_job(job_publish_daily_top25,  CronTrigger(minute=30, hour=7),    id="daily_top25",           replace_existing=True)
    # DB keepalive — runs every 2 minutes so Supabase never goes idle
    scheduler.add_job(_db_keepalive, CronTrigger(minute="*/2"), id="db_keepalive", replace_existing=True)
    scheduler.start()
    logger.info("[scheduler] started — news/rss every 4h, jobs/hotel every 12h, serp/logistics daily 06:00 UTC, scores every 6h, daily brief 07:30 UTC")
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
app.include_router(strategy_router,     prefix="/api/strategy",     tags=["strategy"])
app.include_router(intelligence_router, prefix="/api",            tags=["intelligence"])

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