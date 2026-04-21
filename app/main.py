import os
import re
import time
import threading
import logging
from collections import defaultdict
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
from app.api.admin_extended import router as admin_extended_router
from app.api.admin_users import router as admin_users_router
from app.api.agent import router as agent_router
from app.api.search import router as search_router
from app.api.trending import router as trending_router
from app.api.user import router as user_router
from app.api.robots import router as robots_router
from app.api.robot_ready import router as robot_ready_router
from app.api.analytics import router as analytics_router
from app.api.share import router as share_router
from app.api.playbook import router as playbook_router
from app.api.robot_companies import router as robot_companies_router
from app.api.newsletter import router as newsletter_router
from app.api.crm import router as crm_router
from app.api.admin_purge import router as admin_purge_router
from app.api.social_posts import router as social_posts_router
from app.database import get_db
import app.models
import app.models.shared_calculation
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
        "http://localhost:3000",
        "http://127.0.0.1:3000",
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


app = FastAPI(title="Ready for Robots", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(admin_extended_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_users_router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_purge_router, prefix="/api/admin", tags=["admin"])
app.include_router(social_posts_router, prefix="/api/social", tags=["social"])
app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(trending_router, prefix="/api/trending", tags=["trending"])
app.include_router(user_router,    prefix="/api/user",     tags=["user"])
app.include_router(robots_router,  prefix="/api",          tags=["robots"])
app.include_router(robot_ready_router, prefix="/api/robot-ready", tags=["robot-ready"])
app.include_router(analytics_router, prefix="/api", tags=["analytics"])
app.include_router(share_router, prefix="/api", tags=["share"])
app.include_router(playbook_router, prefix="/api", tags=["playbook"])
app.include_router(robot_companies_router, tags=["robot-companies"])
app.include_router(newsletter_router, prefix="/api/newsletter", tags=["newsletter"])
app.include_router(crm_router, prefix="/api/crm", tags=["crm"])


@app.on_event("startup")
def startup():
    _start_scheduled_scraper()
    # Pre-warm the homepage cache so the first user request is never slow
    try:
        from app.api.leads import warm_homepage_cache
        warm_homepage_cache()
    except Exception as exc:
        logger.warning("Homepage cache warm-up could not be scheduled: %s", exc)


@app.get("/health")
def health():
    return {"status": "ok"}


# ── In-app scheduled scraper (no Redis/Celery required) ─────────────────────
# On Fly.io we only run the web process; Celery beat/worker are not deployed.
# This thread runs the intelligence scraper every N hours so leads keep flowing.

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
                from app.services.newsletter_service import generate_edition, write_cached_edition
                from app.services.industry_brief_service import build_industry_brief_payload

                ndb = SessionLocal()
                try:
                    # Refresh strategic brief first so newsletter embed matches post-scrape data.
                    build_industry_brief_payload(
                        ndb, days=1, analytics=None, use_cache=True, force_refresh=True
                    )
                    edition = generate_edition(ndb, limit=8)
                    write_cached_edition(edition)
                    logger.info("Newsletter edition refreshed after scraper run")
                finally:
                    ndb.close()
            except Exception as ne:
                logger.warning("Newsletter refresh after scraper skipped: %s", ne)
        except Exception as e:
            logger.exception("Scheduled intelligence scraper failed: %s", e)
        time.sleep(max(3600, int(interval_hours * 3600)))


def _start_scheduled_scraper():
    """Start the in-app scraper loop only when running on Fly (or when explicitly enabled)."""
    if os.getenv("FLY_APP_NAME") or os.getenv("ENABLE_SCHEDULED_SCRAPER", "").lower() in ("1", "true", "yes"):
        t = threading.Thread(target=_scheduled_scraper_loop, daemon=True)
        t.start()
        logger.info("In-app scheduled scraper thread started (every %s hours)", os.getenv("RUN_SCRAPER_EVERY_HOURS", "6"))

# ── Static frontend (Next.js export) ──────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

if os.path.exists(STATIC_DIR):
    # Mount Next.js chunk assets at /_next
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