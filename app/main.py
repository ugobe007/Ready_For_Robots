from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import leads, companies, scoring
from app.api.analyze import router as analyze_router
from app.api.scraper_health import router as scraper_health_router
from app.database import Base, engine
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ready for Robots")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["scoring"])
app.include_router(analyze_router, prefix="/api", tags=["analyze"])
app.include_router(scraper_health_router, prefix="/api", tags=["scraper-health"])

@app.get("/")
def root():
    return {"message": "Ready for Robots API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}