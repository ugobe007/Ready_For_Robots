"""
Humanoid Benchmark API  —  /api/humanoid
GET  /api/humanoid/robots          — list all with scores (public)
GET  /api/humanoid/robots/{slug}   — single robot detail (public)
POST /api/humanoid/seed            — seed known robots (admin)
POST /api/humanoid/scrape/{slug}   — scrape + rescore one robot (admin)
POST /api/humanoid/scrape-all      — scrape + rescore all robots (admin)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.services.humanoid_scraper import seed_robots, scrape_and_score_robot

router = APIRouter(prefix="/api/humanoid", tags=["humanoid-benchmark"])


def _require_admin(db: Session = Depends(get_db)):
    """Lightweight admin guard reusing the same pattern as admin_extended."""
    from app.api.admin_extended import require_admin  # avoid circular at module level
    return require_admin


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("/robots")
def list_robots(db: Session = Depends(get_db)):
    """Return all humanoid robots ordered by total benchmark score."""
    rows = db.execute(
        text("""
            SELECT id, name, vendor, model_slug, product_url, image_url, status,
                   specs, score_mobility, score_manipulation, score_autonomy,
                   score_safety, score_endurance, score_market_readiness,
                   score_total, last_scraped_at
            FROM humanoid_benchmarks
            ORDER BY score_total DESC NULLS LAST, name ASC
        """)
    ).mappings().all()
    return {"robots": [dict(r) for r in rows]}


@router.get("/robots/{slug}")
def get_robot(slug: str, db: Session = Depends(get_db)):
    """Return a single robot with full specs and sources."""
    row = db.execute(
        text("SELECT * FROM humanoid_benchmarks WHERE model_slug = :slug"),
        {"slug": slug},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Robot not found")
    return dict(row)


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    """Seed the 10 known humanoid robots with published specs + initial scores."""
    result = seed_robots(db)
    return result


@router.post("/scrape/{slug}")
def scrape_one(slug: str, db: Session = Depends(get_db)):
    """Scrape fresh specs and recompute scores for one robot."""
    result = scrape_and_score_robot(db, slug)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/scrape-all")
def scrape_all(db: Session = Depends(get_db)):
    """Scrape and rescore every robot in the database."""
    slugs = [
        r[0] for r in db.execute(
            text("SELECT model_slug FROM humanoid_benchmarks ORDER BY last_scraped_at ASC NULLS FIRST")
        ).all()
    ]
    results = []
    for slug in slugs:
        results.append(scrape_and_score_robot(db, slug))
    return {"scraped": len(results), "results": results}
