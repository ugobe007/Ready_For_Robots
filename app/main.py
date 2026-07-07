import os
import re
import time
import threading
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.api import leads, companies, scoring
from app.api.analyze import router as analyze_router
from app.api.scraper_health import router as scraper_health_router
from app.api.scraper_control import router as scraper_control_router
from app.api.admin import router as admin_router
from app.api.admin_snapshot import router as admin_snapshot_router
from app.api.admin_extended import router as admin_extended_router
from app.api.admin_users import router as admin_users_router
from app.api.agent import router as agent_router
from app.api.search import router as search_router
from app.api.trending import router as trending_router
from app.api.user import router as user_router
from app.api.robots import router as robots_router
from app.api.robot_ready import router as robot_ready_router
from app.api.humanoid_benchmark import router as humanoid_router
from app.api.analytics import router as analytics_router
from app.api.share import router as share_router
from app.api.playbook import router as playbook_router
from app.api.robot_companies import router as robot_companies_router
from app.api.newsletter import router as newsletter_router
from app.api.crm import router as crm_router
from app.api.webhooks import router as webhooks_router
from app.api.marketplace import router as marketplace_router
from app.api.sales import router as sales_router
from app.api.calendar import router as calendar_router
from app.api.proposals import router as proposals_router
from app.api.scout import router as scout_router
from app.api.waitlist import router as waitlist_router
from app.api.billing import router as billing_router
from app.api.robot_buyer_leads import router as robot_buyer_leads_router
from app.api.admin_purge import router as admin_purge_router
from app.api.admin_lead_ops import router as admin_lead_ops_router
from app.api.admin_humanoid_ops import router as admin_humanoid_ops_router
from app.api.admin_partners import router as admin_partners_router
from app.api.special_projects import admin_router as special_projects_admin_router
from app.api.special_projects import public_router as special_projects_public_router
from app.api.social_posts import router as social_posts_router
from app.api.linkedin import router as linkedin_router
from app.api.integrations import router as integrations_router
from app.api.integrations_hubspot import router as integrations_hubspot_router
from app.api.integrations_google_calendar import router as integrations_google_calendar_router
from app.api.vendor_design import router as vendor_design_router
from app.database import get_db
import app.models
import app.models.shared_calculation
import app.models.site_analytics_event
from app.db_events import register_db_events

register_db_events()

# DB is not touched at startup — first connection happens when an API that uses get_db() is called (browser/request).
# Schema is managed by Alembic migrations (run in release or background).


def _cors_allowed_origins() -> list[str]:
    """
    Browsers reject allow_origins=['*'] together with allow_credentials=True (Fetch + CORS spec).
    Static site on readyforrobots.com calling API on ready-2-robot.fly.dev requires both origins listed.
    Override with CORS_ORIGINS=comma,separated,urls (no trailing slashes).
    """
    raw = (os.getenv("CORS_ORIGINS") or "").strip()
    if raw:
        return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
    return [
        "https://readyforrobots.com",
        "https://www.readyforrobots.com",
        "https://ready-2-robot.fly.dev",
        # Vercel / local previews; add more origins via CORS_ORIGINS on Fly.
        "https://ready-for-robots.vercel.app",
        "https://ready-for-robots-ax5i.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Vite (readyforrobots_new_web) and other dev servers
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]


def _cors_headers_for_request(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if not origin:
        return {}
    o = origin.rstrip("/")
    if o not in _cors_allowed_origins():
        return {}
    return {
        "access-control-allow-origin": origin,
        "access-control-allow-credentials": "true",
    }


class EnsureCORSHeadersMiddleware(BaseHTTPMiddleware):
    """
    CORSMiddleware does not always attach headers to error bodies (e.g. plain-text 500 from
    unhandled exceptions). Browsers then report a CORS failure even when the real issue is 500.
    This outer layer adds Allow-Origin for allowed origins when missing, and wraps uncaught errors.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled exception in ASGI stack")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers=_cors_headers_for_request(request),
            )
        origin = request.headers.get("origin")
        if origin and "access-control-allow-origin" not in response.headers:
            hdr = _cors_headers_for_request(request)
            for k, v in hdr.items():
                response.headers[k] = v
        return response


def _configure_logging() -> None:
    """Ensure app loggers and secondary-pass prints appear in Fly logs."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    logging.getLogger("app").setLevel(level)


def _ensure_cache_table_async() -> None:
    def _ensure_cache_table() -> None:
        import time
        time.sleep(3)
        try:
            from app.database import SessionLocal
            from app.services.pipeline_cache_store import ensure_pipeline_cache_table

            db = SessionLocal()
            try:
                ensure_pipeline_cache_table(db)
                logger.info("pipeline_cache_store table ready")
            finally:
                db.close()
        except Exception as exc:
            logger.warning("pipeline_cache_store ensure failed: %s", exc)

    threading.Thread(target=_ensure_cache_table, daemon=True, name="cache-table-ensure").start()


def _staggered_warm(label: str, fn, delay_sec: float) -> None:
    def _run() -> None:
        import time
        time.sleep(delay_sec)
        try:
            fn()
        except Exception as exc:
            logger.warning("%s warm-up failed: %s", label, exc)
    threading.Thread(target=_run, daemon=True, name=f"warm-{label}").start()


def _run_web_startup() -> None:
    """API machine: hydrate L1 caches only — never run rebuild loops or schedulers."""
    from app.runtime_role import is_web_process

    if not is_web_process():
        return

    if os.getenv("DISABLE_STARTUP_CACHE_WARM", "").strip().lower() in ("1", "true", "yes"):
        logger.info("Web startup cache hydrate disabled (DISABLE_STARTUP_CACHE_WARM)")
        return

    _ensure_cache_table_async()

    def _hydrate_l1_only() -> None:
        import time
        time.sleep(2)
        try:
            from app.services.public_surface_cache import hydrate_public_surface_caches

            hydrate_public_surface_caches()
            logger.info("Web: public surface L1 hydration complete (read-only)")
        except Exception as exc:
            logger.warning("Web cache hydration failed: %s", exc)

    threading.Thread(target=_hydrate_l1_only, daemon=True, name="public-surface-hydrate").start()


def _run_worker_startup() -> None:
    """Worker machine: schedulers, cache refresh loops, and warm-ups."""
    from app.runtime_role import is_worker_process

    if not is_worker_process():
        return

    _start_scheduled_scraper()
    _start_scheduled_secondary_pipeline()
    _start_scheduled_data_quality()
    _start_scheduled_cal_autonomy()
    _start_scheduled_cal_daily_digest()
    _start_scheduled_supply_autonomy()

    if os.getenv("DISABLE_STARTUP_CACHE_WARM", "").strip().lower() in ("1", "true", "yes"):
        logger.info("Worker startup cache warm disabled (DISABLE_STARTUP_CACHE_WARM)")
        return

    _ensure_cache_table_async()

    def _hydrate_public_caches() -> None:
        import time
        time.sleep(5)
        try:
            from app.services.content_surfaces import KEY_HUMANOID_ROBOTS_LIST
            from app.services.public_surface_cache import (
                KEY_HOMEPAGE,
                hydrate_public_surface_caches,
                read_public_cache,
                schedule_public_cache_refresh,
                schedule_robots_page_cache_refresh,
                start_public_cache_refresh_loop,
            )

            hydrate_public_surface_caches()
            logger.info("Worker: public surface L1 hydration complete")

            start_public_cache_refresh_loop()

            homepage = read_public_cache(KEY_HOMEPAGE, stale_ok=True)
            if not homepage or not (homepage.get("hotLeads") or []):
                schedule_public_cache_refresh(
                    force=True,
                    pipeline_only=True,
                    reason="bootstrap_empty",
                )

            robots_snap = read_public_cache(KEY_HUMANOID_ROBOTS_LIST, stale_ok=True)
            if not robots_snap or not (robots_snap.get("robots") or []):
                schedule_robots_page_cache_refresh(reason="bootstrap_empty")
        except Exception as exc:
            logger.warning("Worker public surface hydration failed: %s", exc)

    threading.Thread(target=_hydrate_public_caches, daemon=True, name="public-surface-hydrate").start()

    def _warm_social_posts() -> None:
        from app.database import SessionLocal
        from app.services.social_posts_service import read_cached_posts, refresh_social_posts_cache

        cached = read_cached_posts(max_age_hours=4.0)
        if cached and (cached.get("posts") or []):
            return
        db = SessionLocal()
        try:
            refresh_social_posts_cache(db)
            logger.info("Social posts cache warmed at startup")
        finally:
            db.close()

    _staggered_warm("social-posts", _warm_social_posts, 60)
    _staggered_warm(
        "robot-ready",
        lambda: __import__(
            "app.api.robot_ready",
            fromlist=["warm_robot_ready_candidate_cache"],
        ).warm_robot_ready_candidate_cache(),
        30,
    )
    _staggered_warm(
        "admin-snapshot",
        lambda: __import__(
            "app.services.admin_snapshot",
            fromlist=["warm_admin_snapshot_cache"],
        ).warm_admin_snapshot_cache(),
        90,
    )


def _run_startup() -> None:
    _configure_logging()
    from app.runtime_role import is_worker_process

    if is_worker_process():
        logger.info("Process role=worker — starting background jobs")
        _run_worker_startup()
    else:
        logger.info("Process role=web — API-only startup")
        _run_web_startup()


@asynccontextmanager
async def _app_lifespan(app):
    _run_startup()
    yield


_mcp_asgi = None
if os.getenv("R4R_MCP_ENABLED", "").strip().lower() in ("1", "true", "yes"):
    try:
        from app.mcp.server import mcp_http_app

        _mcp_asgi = mcp_http_app()
    except Exception as exc:
        logger.warning("MCP setup skipped: %s", exc)

if _mcp_asgi is not None:
    from fastmcp.utilities.lifespan import combine_lifespans

    _lifespan = combine_lifespans(_app_lifespan, _mcp_asgi.lifespan)
else:
    _lifespan = _app_lifespan


app = FastAPI(
    title="Ready for Robots",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
app.add_middleware(EnsureCORSHeadersMiddleware)

# ── Rate limit + 404 for probe paths (reduces bot log noise) ─────────────────
_PROBE_PATTERNS = re.compile(
    r"\.(php|asp|aspx|jsp|cgi|pl|py|sh|env)$|"
    r"(wp-|xmlrpc|wp_content|wp_includes|wp_admin|wp_login|"
    r"shell|filemanager|backup|config\.|\.git|admin\.php)",
    re.I,
)
# In-memory: {ip: [(ts, count), ...]} — prune when checking
_RATE_LIMIT: dict[str, list[tuple[float, int]]] = defaultdict(list)
_RATE_WINDOW = 60  # seconds
_RATE_MAX = 300   # requests per window per IP (generous for real users)


@app.middleware("http")
async def rate_limit_and_block_probes(request: Request, call_next):
    path = request.url.path
    # 404 immediately for obvious scanner probes
    if _PROBE_PATTERNS.search(path):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    # Rate limit by IP (only for catch-all paths; exclude API, health, root, static assets)
    if (
        not path.startswith("/api/")
        and not path.startswith("/mcp")
        and not path.startswith("/_next/")
        and path != "/health"
        and path != "/"
    ):
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        # Prune old entries
        _RATE_LIMIT[ip] = [(t, c) for t, c in _RATE_LIMIT[ip] if now - t < _RATE_WINDOW]
        total = sum(c for _, c in _RATE_LIMIT[ip])
        if total >= _RATE_MAX:
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        _RATE_LIMIT[ip].append((now, 1))
    return await call_next(request)

# ── API routes (must come before catch-all) ────────────────────────────────
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["scoring"])
app.include_router(analyze_router, prefix="/api", tags=["analyze"])
app.include_router(scraper_health_router, prefix="/api", tags=["scraper-health"])
app.include_router(scraper_control_router, tags=["scraper-control"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_snapshot_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_extended_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_users_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_purge_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_lead_ops_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_humanoid_ops_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_partners_router, prefix="/api/admin", tags=["admin-partners"])
app.include_router(special_projects_admin_router, prefix="/api/admin", tags=["special-projects"])
app.include_router(special_projects_public_router, prefix="/api", tags=["special-projects"])
app.include_router(social_posts_router, prefix="/api/social", tags=["social"])
app.include_router(linkedin_router, prefix="/api/linkedin", tags=["linkedin"])
app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(trending_router, prefix="/api/trending", tags=["trending"])
app.include_router(user_router,    prefix="/api/user",     tags=["user"])
app.include_router(robots_router,  prefix="/api",          tags=["robots"])
app.include_router(robot_ready_router, prefix="/api/robot-ready", tags=["robot-ready"])
app.include_router(humanoid_router)
app.include_router(analytics_router, prefix="/api", tags=["analytics"])
app.include_router(share_router, prefix="/api", tags=["share"])
app.include_router(playbook_router, prefix="/api", tags=["playbook"])
app.include_router(robot_companies_router, tags=["robot-companies"])
app.include_router(newsletter_router, prefix="/api/newsletter", tags=["newsletter"])
app.include_router(crm_router, prefix="/api/crm", tags=["crm"])
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(marketplace_router, prefix="/api/marketplace", tags=["marketplace"])
app.include_router(sales_router, prefix="/api/sales", tags=["sales"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["calendar"])
app.include_router(proposals_router, prefix="/api/proposals", tags=["proposals"])
app.include_router(scout_router, prefix="/api/scout", tags=["scout"])
app.include_router(waitlist_router, prefix="/api/waitlist", tags=["waitlist"])
app.include_router(billing_router, prefix="/api/billing", tags=["billing"])
app.include_router(integrations_router, prefix="/api", tags=["integrations"])
app.include_router(integrations_hubspot_router, prefix="/api", tags=["integrations"])
app.include_router(integrations_google_calendar_router, prefix="/api", tags=["integrations"])
app.include_router(robot_buyer_leads_router, prefix="/api/robot-buyer-leads", tags=["robot-buyer-leads"])
app.include_router(vendor_design_router, prefix="/api/vendor-design", tags=["vendor-design"])

if _mcp_asgi is not None:
    app.mount("/mcp", _mcp_asgi, name="mcp")
    logger.info("MCP server mounted at /mcp (Streamable HTTP)")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    """Quick Postgres probe — fails fast instead of hanging the request."""
    from sqlalchemy import text

    from app.database import DATABASE_URL, SessionLocal
    from app.db_timeout import run_db

    if not DATABASE_URL or "postgresql" not in DATABASE_URL:
        return {"status": "skipped", "reason": "sqlite or no DATABASE_URL"}

    def _probe() -> int:
        with SessionLocal() as db:
            return db.execute(text("SELECT 1")).scalar()

    try:
        run_db(_probe, timeout_sec=8, label="health/db")
        return {"status": "ok", "database": "connected"}
    except TimeoutError:
        return JSONResponse(
            status_code=503,
            content={"status": "timeout", "database": "connection timed out"},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": str(exc)[:200]},
        )


# ── In-app scheduled scraper (fallback when no Redis/Celery) ───────────────
# On Fly with REDIS_URL, `scripts/start_all.sh` starts Beat + worker; this thread is skipped
# so intelligence is not scheduled twice (see `_start_scheduled_scraper`).

def _scheduled_scraper_loop():
    """Run intelligence scraper on an interval. Catches and logs errors so one failure doesn't stop the loop."""
    from app.api.scraper_control import _run_intelligence_scraper_sync
    first_delay_min = int(os.getenv("SCRAPER_FIRST_RUN_DELAY_MINUTES", "5"))
    interval_hours = float(os.getenv("RUN_SCRAPER_EVERY_HOURS", "6"))
    if interval_hours <= 0:
        return
    # Quick run: 20 queries, ~3–5 min, so we don't block the process long
    articles_per_query = 15
    max_queries = 20
    time.sleep(first_delay_min * 60)
    while True:
        try:
            logger.info("Scheduled intelligence scraper starting (in-app thread)")
            _run_intelligence_scraper_sync(
                articles_per_query=articles_per_query,
                max_queries=max_queries,
                enrich=True,
            )
            logger.info("Scheduled intelligence scraper finished")
            try:
                from app.database import SessionLocal
                from app.services.oem_discovery import run_oem_discovery

                odb = SessionLocal()
                try:
                    logger.info("Scheduled OEM/XBOT discovery starting")
                    run_oem_discovery(odb, max_queries=20)
                    logger.info("Scheduled OEM/XBOT discovery finished")
                finally:
                    odb.close()
            except Exception as oe:
                logger.warning("Scheduled OEM discovery skipped: %s", oe)
        except Exception as e:
            logger.exception("Scheduled intelligence scraper failed: %s", e)
        time.sleep(max(3600, int(interval_hours * 3600)))


def _start_scheduled_scraper():
    """Start the in-app scraper loop when Celery Beat is not running (worker machine)."""
    from app.runtime_role import is_worker_process

    if not is_worker_process():
        logger.info("In-app scheduled scraper skipped on web process")
        return
    skip_celery = os.getenv("SKIP_CELERY", "").strip().lower() in ("1", "true", "yes")
    has_broker = bool(os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL"))
    if has_broker and not skip_celery:
        logger.info(
            "In-app scheduled scraper skipped: Celery Beat + worker expected (broker configured)"
        )
        return
    if skip_celery and has_broker:
        logger.info(
            "In-app scheduled scraper enabled: SKIP_CELERY=1 (dedicated worker machine)"
        )
    enabled = (
        os.getenv("FLY_APP_NAME")
        or os.getenv("ENABLE_SCHEDULED_SCRAPER", "").lower() in ("1", "true", "yes")
        or skip_celery
    )
    if not enabled:
        return
    if os.getenv("ENABLE_SCHEDULED_SCRAPER", "").strip().lower() in ("0", "false", "no"):
        logger.info("In-app scheduled scraper disabled (ENABLE_SCHEDULED_SCRAPER=0)")
        return
    t = threading.Thread(target=_scheduled_scraper_loop, daemon=True)
    t.start()
    logger.info("In-app scheduled scraper thread started (every %s hours)", os.getenv("RUN_SCRAPER_EVERY_HOURS", "6"))


def _scheduled_secondary_pipeline_loop():
    """Daily leads → humanoids secondary pipeline on Fly (SKIP_CELERY=1)."""
    from app.api.scraper_control import _run_full_secondary_pipeline_sync

    first_delay_min = int(os.getenv("SECONDARY_PASS_FIRST_RUN_DELAY_MINUTES", "60"))
    interval_hours = float(os.getenv("SECONDARY_PASS_EVERY_HOURS", "24"))
    if interval_hours <= 0:
        return

    print(
        f"[secondary-pass] scheduler armed first_run_min={first_delay_min} "
        f"interval_hours={interval_hours}",
        flush=True,
    )
    time.sleep(max(60, first_delay_min * 60))
    while True:
        try:
            logger.info("Scheduled secondary pipeline starting (leads then humanoids)")
            result = _run_full_secondary_pipeline_sync()
            if result.get("status") == "skipped":
                logger.info("Scheduled secondary pipeline skipped: %s", result.get("reason"))
            else:
                leads = result.get("leads") or {}
                humanoids = result.get("humanoids") or {}
                logger.info(
                    "Scheduled secondary pipeline finished: leads_processed=%s "
                    "humanoids_processed=%s",
                    leads.get("processed"),
                    humanoids.get("processed"),
                )
        except Exception as exc:
            logger.exception("Scheduled secondary pipeline failed: %s", exc)
        time.sleep(max(3600, int(interval_hours * 3600)))


def _start_scheduled_secondary_pipeline():
    """Start daily secondary pipeline on the worker machine."""
    from app.runtime_role import is_worker_process

    if not is_worker_process():
        logger.info("In-app scheduled secondary pipeline skipped on web process")
        return

    leads_off = os.getenv("ENABLE_SCHEDULED_SECONDARY_PASS", "1").strip().lower() in (
        "0", "false", "no"
    )
    humanoids_off = os.getenv("ENABLE_SCHEDULED_HUMANOID_SECONDARY_PASS", "1").strip().lower() in (
        "0", "false", "no"
    )
    if leads_off and humanoids_off:
        logger.info("In-app scheduled secondary pipeline disabled")
        return

    skip_celery = os.getenv("SKIP_CELERY", "").strip().lower() in ("1", "true", "yes")
    has_broker = bool(os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL"))
    if has_broker and not skip_celery:
        logger.info(
            "In-app scheduled secondary pipeline skipped: Celery Beat runs secondary tasks"
        )
        return

    enabled = (
        os.getenv("FLY_APP_NAME")
        or os.getenv("ENABLE_SCHEDULED_SECONDARY_PASS", "").lower() in ("1", "true", "yes")
        or os.getenv("ENABLE_SCHEDULED_HUMANOID_SECONDARY_PASS", "").lower() in ("1", "true", "yes")
        or skip_celery
    )
    if not enabled:
        return

    t = threading.Thread(target=_scheduled_secondary_pipeline_loop, daemon=True, name="secondary-pipeline")
    t.start()
    print("[secondary-pass] scheduler thread started", flush=True)
    logger.info(
        "In-app scheduled secondary pipeline thread started (every %s hours, first run in %s min)",
        os.getenv("SECONDARY_PASS_EVERY_HOURS", "24"),
        os.getenv("SECONDARY_PASS_FIRST_RUN_DELAY_MINUTES", "60"),
    )


def _scheduled_data_quality_loop():
    """Weekly purge + normalize + quality decision log export."""
    from app.services.scheduled_data_quality import run_weekly_data_quality_job

    first_delay_hours = float(os.getenv("DATA_QUALITY_FIRST_RUN_DELAY_HOURS", "12"))
    interval_hours = float(os.getenv("DATA_QUALITY_EVERY_HOURS", "168"))
    if interval_hours <= 0:
        return

    print(
        f"[data-quality] scheduler armed first_run_hours={first_delay_hours} "
        f"interval_hours={interval_hours}",
        flush=True,
    )
    time.sleep(max(3600, int(first_delay_hours * 3600)))
    while True:
        try:
            logger.info("Scheduled weekly data quality job starting")
            result = run_weekly_data_quality_job(apply=True)
            logger.info(
                "Scheduled data quality finished: status=%s purged=%s log_rows=%s",
                result.get("status"),
                result.get("purge_deleted"),
                result.get("quality_log_rows"),
            )
        except Exception as exc:
            logger.exception("Scheduled data quality job failed: %s", exc)
        time.sleep(max(3600, int(interval_hours * 3600)))


def _start_scheduled_data_quality():
    from app.runtime_role import is_worker_process

    if not is_worker_process():
        logger.info("In-app scheduled data quality skipped on web process")
        return

    if os.getenv("ENABLE_SCHEDULED_DATA_QUALITY", "1").strip().lower() in (
        "0", "false", "no"
    ):
        logger.info("In-app scheduled data quality disabled")
        return
    enabled = (
        os.getenv("FLY_APP_NAME")
        or os.getenv("ENABLE_SCHEDULED_DATA_QUALITY", "").lower() in ("1", "true", "yes")
        or os.getenv("SKIP_CELERY", "").strip().lower() in ("1", "true", "yes")
    )
    if not enabled:
        return
    t = threading.Thread(
        target=_scheduled_data_quality_loop,
        daemon=True,
        name="data-quality-weekly",
    )
    t.start()
    print("[data-quality] weekly scheduler thread started", flush=True)
    logger.info(
        "In-app weekly data quality thread started (every %s hours)",
        os.getenv("DATA_QUALITY_EVERY_HOURS", "168"),
    )


def _scheduled_cal_autonomy_loop():
    from app.database import SessionLocal
    from app.services.cal_autonomy import cal_autonomy_enabled, run_cal_autonomy_cycle

    delay_min = float(os.getenv("CAL_AUTONOMY_FIRST_RUN_DELAY_MINUTES", "20") or "20")
    time.sleep(max(60, delay_min * 60))
    while True:
        if not cal_autonomy_enabled():
            time.sleep(3600)
            continue
        try:
            with SessionLocal() as db:
                result = run_cal_autonomy_cycle(db)
            logger.info(
                "Cal autonomy cycle: status=%s drafted=%s sent=%s format_notified=%s",
                result.get("status"),
                result.get("drafted"),
                result.get("sent"),
                result.get("format_review_notified"),
            )
        except Exception as exc:
            logger.exception("Cal autonomy cycle failed: %s", exc)
        interval_hours = float(os.getenv("CAL_AUTONOMY_EVERY_HOURS", "6") or "6")
        time.sleep(max(1800, int(interval_hours * 3600)))


def _start_scheduled_cal_autonomy():
    from app.runtime_role import is_worker_process

    if not is_worker_process():
        logger.info("In-app Cal autonomy skipped on web process")
        return
    if os.getenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "1").strip().lower() in (
        "0", "false", "no"
    ):
        logger.info("In-app Cal autonomy disabled")
        return
    enabled = (
        os.getenv("FLY_APP_NAME")
        or os.getenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "").lower() in ("1", "true", "yes")
    )
    if not enabled:
        return
    t = threading.Thread(
        target=_scheduled_cal_autonomy_loop,
        daemon=True,
        name="cal-autonomy",
    )
    t.start()
    print("[cal-autonomy] scheduler thread started", flush=True)
    logger.info(
        "In-app Cal autonomy thread started (every %s hours)",
        os.getenv("CAL_AUTONOMY_EVERY_HOURS", "6"),
    )


def _scheduled_supply_autonomy_loop():
    from app.database import SessionLocal
    from app.services.supply_autonomy import run_supply_autonomy_cycle, supply_autonomy_enabled

    delay_min = float(os.getenv("SUPPLY_AUTONOMY_FIRST_RUN_DELAY_MINUTES", "30") or "30")
    time.sleep(max(60, delay_min * 60))
    while True:
        if not supply_autonomy_enabled():
            time.sleep(3600)
            continue
        try:
            with SessionLocal() as db:
                result = run_supply_autonomy_cycle(db)
            logger.info(
                "Supply autonomy cycle: status=%s sent=%s format_notified=%s",
                result.get("status"),
                result.get("sent"),
                result.get("format_review_notified"),
            )
        except Exception as exc:
            logger.exception("Supply autonomy cycle failed: %s", exc)
        interval_hours = float(os.getenv("SUPPLY_AUTONOMY_EVERY_HOURS", "6") or "6")
        time.sleep(max(1800, int(interval_hours * 3600)))


def _scheduled_cal_daily_digest_loop():
    from datetime import datetime, timezone

    from app.database import SessionLocal
    from app.services.cal_daily_digest import (
        cal_daily_digest_enabled,
        next_digest_run_utc,
        send_cal_daily_digest,
    )

    hour = int(os.getenv("CAL_DAILY_DIGEST_HOUR_UTC", "15") or "15")
    minute = int(os.getenv("CAL_DAILY_DIGEST_MINUTE_UTC", "0") or "0")
    first = next_digest_run_utc(hour=hour, minute=minute)
    delay = max(60, int((first - datetime.now(timezone.utc)).total_seconds()))
    time.sleep(delay)
    while True:
        if not cal_daily_digest_enabled():
            time.sleep(3600)
            continue
        try:
            with SessionLocal() as db:
                result = send_cal_daily_digest(db)
            logger.info(
                "Cal daily digest: sent=%s recipients=%s reason=%s",
                result.get("sent"),
                result.get("recipients"),
                result.get("reason"),
            )
        except Exception as exc:
            logger.exception("Cal daily digest failed: %s", exc)
        next_run = next_digest_run_utc(hour=hour, minute=minute)
        sleep_sec = max(300, int((next_run - datetime.now(timezone.utc)).total_seconds()))
        time.sleep(sleep_sec)


def _start_scheduled_cal_daily_digest():
    from app.runtime_role import is_worker_process

    if not is_worker_process():
        logger.info("In-app Cal daily digest skipped on web process")
        return
    if os.getenv("ENABLE_SCHEDULED_CAL_DAILY_DIGEST", "1").strip().lower() in (
        "0", "false", "no"
    ):
        logger.info("In-app Cal daily digest disabled")
        return
    enabled = (
        os.getenv("FLY_APP_NAME")
        or os.getenv("ENABLE_SCHEDULED_CAL_DAILY_DIGEST", "").lower() in ("1", "true", "yes")
    )
    if not enabled:
        return
    t = threading.Thread(
        target=_scheduled_cal_daily_digest_loop,
        daemon=True,
        name="cal-daily-digest",
    )
    t.start()
    print("[cal-daily-digest] scheduler thread started", flush=True)
    logger.info(
        "In-app Cal daily digest thread started (daily at %s:%02d UTC)",
        os.getenv("CAL_DAILY_DIGEST_HOUR_UTC", "15"),
        int(os.getenv("CAL_DAILY_DIGEST_MINUTE_UTC", "0") or "0"),
    )


def _start_scheduled_supply_autonomy():
    from app.runtime_role import is_worker_process

    if not is_worker_process():
        logger.info("In-app supply autonomy skipped on web process")
        return
    if os.getenv("ENABLE_SCHEDULED_SUPPLY_AUTONOMY", "1").strip().lower() in (
        "0", "false", "no"
    ):
        logger.info("In-app supply autonomy disabled")
        return
    enabled = (
        os.getenv("FLY_APP_NAME")
        or os.getenv("ENABLE_SCHEDULED_SUPPLY_AUTONOMY", "").lower() in ("1", "true", "yes")
    )
    if not enabled:
        return
    t = threading.Thread(
        target=_scheduled_supply_autonomy_loop,
        daemon=True,
        name="supply-autonomy",
    )
    t.start()
    print("[supply-autonomy] scheduler thread started", flush=True)
    logger.info(
        "In-app supply autonomy thread started (every %s hours)",
        os.getenv("SUPPLY_AUTONOMY_EVERY_HOURS", "6"),
    )


# ── Static frontend (Vite SPA build → static/) ────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

if os.path.exists(STATIC_DIR):
    # Legacy Next export used /_next; Vite uses /assets. Mount if present.
    _next = os.path.join(STATIC_DIR, "_next")
    if os.path.exists(_next):
        app.mount("/_next", StaticFiles(directory=_next), name="nextjs_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        # 0. 404 for probe-like paths (middleware also catches, but belt-and-suspenders)
        if _PROBE_PATTERNS.search(full_path):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
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
        # 4. Root (SPA fallback)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "Ready for Robots API", "docs": "/api/docs"}