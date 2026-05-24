"""
Humanoid Benchmark API  —  /api/humanoid
GET  /api/humanoid/robots               — list all with scores (public)
GET  /api/humanoid/robots/{slug}        — single robot detail (public)
GET  /api/humanoid/report               — formatted benchmark report (public)
GET  /api/humanoid/linkedin-post        — generate LinkedIn post text (public)
POST /api/humanoid/seed                 — seed known robots (admin)
POST /api/humanoid/scrape/{slug}        — scrape + rescore one robot (admin)
POST /api/humanoid/scrape-all           — scrape + rescore all robots (admin)
GET  /api/humanoid/cron/scrape-all      — cron trigger for weekly auto-scrape
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import SessionLocal, get_db
from app.db_timeout import run_db
from app.services.humanoid_scraper import SEED_ROBOTS, compute_scores, seed_robots, scrape_and_score_robot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/humanoid", tags=["humanoid-benchmark"])

_ROBOTS_LIST_CACHE: dict = {"ts": 0.0, "payload": None}
_ROBOTS_LIST_TTL_SEC = 300


def _seed_robots_payload() -> list[dict]:
    """Static fallback when Postgres is unreachable (matches SEED_ROBOTS shape)."""
    rows = []
    for i, robot in enumerate(SEED_ROBOTS, start=1):
        specs = robot["specs"]
        scores = compute_scores(specs, status=robot["status"])
        rows.append({
            "id": i,
            "name": robot["name"],
            "vendor": robot["vendor"],
            "model_slug": robot["model_slug"],
            "product_url": robot.get("product_url"),
            "image_url": robot.get("image_url"),
            "status": robot["status"],
            "specs": specs,
            "score_mobility": scores["score_mobility"],
            "score_manipulation": scores["score_manipulation"],
            "score_autonomy": scores["score_autonomy"],
            "score_safety": scores["score_safety"],
            "score_endurance": scores["score_endurance"],
            "score_market_readiness": scores["score_market_readiness"],
            "score_total": scores["score_total"],
            "last_scraped_at": None,
        })
    rows.sort(key=lambda r: (-(r["score_total"] or 0), r["name"]))
    return rows


def _fetch_robots_from_db() -> list[dict]:
    with SessionLocal() as db:
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
        return [dict(r) for r in rows]


def _require_admin(db: Session = Depends(get_db)):
    """Lightweight admin guard reusing the same pattern as admin_extended."""
    from app.api.admin_extended import require_admin  # avoid circular at module level
    return require_admin


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("/robots")
def list_robots():
    """Return all humanoid robots ordered by total benchmark score."""
    now = time.monotonic()
    cached = _ROBOTS_LIST_CACHE.get("payload")
    if cached is not None and now - _ROBOTS_LIST_CACHE["ts"] < _ROBOTS_LIST_TTL_SEC:
        return {"robots": cached}

    try:
        robots = run_db(_fetch_robots_from_db, timeout_sec=12, label="humanoid/robots")
        if robots:
            _ROBOTS_LIST_CACHE["ts"] = now
            _ROBOTS_LIST_CACHE["payload"] = robots
            return {"robots": robots}
    except TimeoutError:
        logger.warning("humanoid/robots DB timed out — serving cache or seed fallback")
    except Exception as exc:
        logger.warning("humanoid/robots DB failed: %s", exc)

    if cached:
        return {"robots": cached, "stale": True}
    return {"robots": _seed_robots_payload(), "stale": True, "source": "seed"}


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


# ── Cron endpoint ────────────────────────────────────────────────────────────

@router.get("/cron/scrape-all")
async def cron_scrape_all(
    background_tasks: BackgroundTasks,
    token: str = Query("", description="SCRAPER_CRON_TOKEN secret"),
    db: Session = Depends(get_db),
):
    """
    Weekly cron trigger — scrapes fresh specs and rescores all humanoid robots.
    Set up at cron-job.org:
      GET https://ready-2-robot.fly.dev/api/humanoid/cron/scrape-all?token=YOUR_TOKEN
      Schedule: every Monday 06:00 UTC
    Token must match SCRAPER_CRON_TOKEN Fly secret.
    """
    expected = os.getenv("SCRAPER_CRON_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")

    slugs = [
        r[0] for r in db.execute(
            text("SELECT model_slug FROM humanoid_benchmarks ORDER BY last_scraped_at ASC NULLS FIRST")
        ).all()
    ]

    def _run():
        from app.database import SessionLocal
        with SessionLocal() as bg_db:
            for slug in slugs:
                try:
                    scrape_and_score_robot(bg_db, slug)
                except Exception as exc:
                    import logging
                    logging.getLogger(__name__).warning("Cron scrape failed for %s: %s", slug, exc)

    background_tasks.add_task(_run)
    return {
        "status": "started",
        "robots": len(slugs),
        "message": f"Scraping {len(slugs)} humanoid robots in background — scores updated in ~2 min.",
    }


# ── Report generator ─────────────────────────────────────────────────────────

@router.get("/report")
def get_report(db: Session = Depends(get_db)):
    """
    Generate a structured benchmark report from current scores.
    Used by Newsletter page and LinkedIn post generator.
    """
    rows = db.execute(
        text("""
            SELECT name, vendor, model_slug, status, specs,
                   score_mobility, score_manipulation, score_autonomy,
                   score_safety, score_endurance, score_market_readiness, score_total
            FROM humanoid_benchmarks
            WHERE score_total IS NOT NULL
            ORDER BY score_total DESC
        """)
    ).mappings().all()

    if not rows:
        return {"report": None, "generated_at": datetime.now(timezone.utc).isoformat()}

    robots = [dict(r) for r in rows]
    top3 = robots[:3]
    leader = robots[0]

    # Category winners
    dims = {
        "Mobility":         "score_mobility",
        "Manipulation":     "score_manipulation",
        "Autonomy":         "score_autonomy",
        "Safety":           "score_safety",
        "Endurance":        "score_endurance",
        "Market Readiness": "score_market_readiness",
    }
    category_winners = {}
    for label, key in dims.items():
        best = max(robots, key=lambda r: r.get(key) or 0)
        category_winners[label] = {"name": best["name"], "vendor": best["vendor"], "score": round(best.get(key) or 0, 1)}

    # Available vs pilot split
    available = [r for r in robots if r["status"] == "available"]
    pilot = [r for r in robots if r["status"] == "pilot"]
    research = [r for r in robots if r["status"] == "research"]

    # Key findings
    specs_leader = dict(leader["specs"] or {})
    findings = []

    fastest = max(robots, key=lambda r: float((r["specs"] or {}).get("top_speed_mps") or 0))
    findings.append(f"{fastest['name']} leads on speed at {(fastest['specs'] or {}).get('top_speed_mps')} m/s")

    best_battery = max(robots, key=lambda r: float((r["specs"] or {}).get("battery_life_h") or 0))
    findings.append(f"{best_battery['name']} has the longest battery life at {(best_battery['specs'] or {}).get('battery_life_h')} hours")

    heaviest_payload = max(robots, key=lambda r: float((r["specs"] or {}).get("payload_kg") or 0))
    findings.append(f"{heaviest_payload['name']} carries the most at {(heaviest_payload['specs'] or {}).get('payload_kg')} kg payload")

    safe_robots = [r for r in robots if float((r["specs"] or {}).get("collision_force_n") or 9999) <= 265]
    if safe_robots:
        findings.append(f"{len(safe_robots)} robot(s) meet ISO TS 15066 collision force thresholds for human co-working")
    else:
        findings.append("No current humanoid fully meets ISO TS 15066 collision force limits for unguarded human co-working")

    sdk_robots = [r for r in robots if (r["specs"] or {}).get("has_sdk")]
    findings.append(f"{len(sdk_robots)} of {len(robots)} robots offer a developer SDK")

    return {
        "report": {
            "title": f"Humanoid Robot Benchmark Report — {datetime.now(timezone.utc).strftime('%B %Y')}",
            "total_robots": len(robots),
            "available_count": len(available),
            "pilot_count": len(pilot),
            "research_count": len(research),
            "overall_leader": {"name": leader["name"], "vendor": leader["vendor"], "score": round(leader["score_total"] or 0, 1)},
            "top_3": [{"name": r["name"], "vendor": r["vendor"], "score": round(r["score_total"] or 0, 1), "status": r["status"]} for r in top3],
            "category_winners": category_winners,
            "key_findings": findings,
            "all_robots": [
                {
                    "rank": i + 1,
                    "name": r["name"],
                    "vendor": r["vendor"],
                    "status": r["status"],
                    "score_total": round(r["score_total"] or 0, 1),
                    "score_mobility": round(r["score_mobility"] or 0, 1),
                    "score_manipulation": round(r["score_manipulation"] or 0, 1),
                    "score_autonomy": round(r["score_autonomy"] or 0, 1),
                    "score_safety": round(r["score_safety"] or 0, 1),
                    "score_endurance": round(r["score_endurance"] or 0, 1),
                    "score_market_readiness": round(r["score_market_readiness"] or 0, 1),
                }
                for i, r in enumerate(robots)
            ],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── LinkedIn post generator ───────────────────────────────────────────────────

@router.get("/linkedin-post")
def generate_linkedin_post(db: Session = Depends(get_db)):
    """
    Generate a LinkedIn post from current benchmark results.
    Returns post text + a LinkedIn share URL.
    """
    from app.api.humanoid_benchmark import get_report
    report_data = get_report(db)
    report = report_data.get("report")
    if not report:
        raise HTTPException(status_code=404, detail="No benchmark data available. Run /seed first.")

    leader = report["overall_leader"]
    top3 = report["top_3"]
    findings = report["key_findings"]
    month_year = datetime.now(timezone.utc).strftime("%B %Y")

    # Build post text
    top3_lines = "\n".join(
        f"  {'🥇' if i == 0 else '🥈' if i == 1 else '🥉'} {r['name']} ({r['vendor']}) — {r['score']}/100 [{r['status'].upper()}]"
        for i, r in enumerate(top3)
    )

    findings_lines = "\n".join(f"  • {f}" for f in findings[:4])

    post = f"""🤖 Humanoid Robot Benchmark — {month_year}

We scored {report['total_robots']} humanoid robots across 6 dimensions: Mobility, Manipulation, Autonomy, Safety, Endurance, and Market Readiness.

📊 Top performers:
{top3_lines}

🔑 Key findings:
{findings_lines}

Of {report['total_robots']} robots benchmarked:
  → {report['available_count']} commercially available
  → {report['pilot_count']} in active pilot programs
  → {report['research_count']} still in research phase

Scoring uses published manufacturer specs and the Fraunhofer IPA framework (May 2026). Estimates used where live test data is unavailable.

Full benchmark + specs: readyforrobots.com/robots
Evaluation framework: readyforrobots.com/benchmark

#Robotics #HumanoidRobots #Automation #RoboticsIndustry #AIRobotics #ReadyForRobots"""

    # LinkedIn share URL (pre-populates the share dialog with the site URL)
    share_url = "https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Freadyforrobots.com%2Frobots"

    return {
        "post_text": post,
        "char_count": len(post),
        "linkedin_share_url": share_url,
        "note": "LinkedIn posts are capped at 3,000 characters. This post is within limit.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
