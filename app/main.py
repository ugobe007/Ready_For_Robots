import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import leads, companies, scoring
from app.api.analyze import router as analyze_router
from app.api.scraper_health import router as scraper_health_router
from app.api.admin import router as admin_router
from app.api.agent import router as agent_router
from app.api.search import router as search_router
from app.api.trending import router as trending_router
from app.api.user import router as user_router
from app.database import Base, engine
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ready for Robots", docs_url="/api/docs", redoc_url="/api/redoc")

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