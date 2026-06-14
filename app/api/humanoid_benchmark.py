"""
Humanoid Benchmark API  —  /api/humanoid
GET  /api/humanoid/robots               — list all with scores (public)
GET  /api/humanoid/gaps                 — missing spec fields for HEIF scoring (public)
GET  /api/humanoid/report               — formatted benchmark report (public)
GET  /api/humanoid/deployment-report    — HEIF vs PoC/deployment evidence report (public)
GET  /api/humanoid/intelligence-report   — top scores explained + trials/customers (public)
GET  /api/humanoid/intelligence-report/pdf — downloadable PDF (public)
GET  /api/humanoid/linkedin-post        — generate LinkedIn post text (public)
POST /api/humanoid/discover            — discover + AI-score humanoid companies (admin)
POST /api/humanoid/seed                 — seed known robots (admin)
POST /api/humanoid/scrape/{slug}        — scrape + rescore one robot (admin)
POST /api/humanoid/apply-verified-specs — apply fetch-verified specs + rescore (token)
POST /api/humanoid/deployment-news       — scan news for deployment/trial evidence (admin)
GET  /api/humanoid/cron/scrape-all      — cron trigger for weekly auto-scrape
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import SessionLocal, get_db
from app.db_timeout import run_db
from app.services.humanoid_ai_stack import (
    enrich_robot_with_ai_stack,
    resolve_ai_stack,
    scoring_specs,
    specs_for_storage,
)
from app.services.humanoid_scraper import SEED_ROBOTS, compute_scores, seed_robots, scrape_and_score_robot
from app.services.humanoid_spec_gaps import SEED_SPECS_BY_SLUG
from app.services.humanoid_benchmark_backfill import (
    backfill_humanoid_specs,
    ensure_priority_humanoids,
    repair_humanoid_index,
)
from app.services.humanoid_discovery import run_humanoid_discovery
from app.services.humanoid_catalog_cleanup import cleanup_humanoid_benchmarks, is_junk_humanoid_row
from app.services.humanoid_spec_gaps import analyze_humanoid_spec_gaps
from app.services.humanoid_deployment_report import build_humanoid_deployment_report_payload
from app.services.humanoid_intelligence_report import build_humanoid_intelligence_report_payload
from app.services.humanoid_intelligence_report_pdf import build_humanoid_intelligence_report_pdf
from app.services.humanoid_deployment_news import run_humanoid_deployment_news_review
from app.services.humanoid_vendor_catalog import catalog_count, sync_product_urls_from_catalog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/humanoid", tags=["humanoid-benchmark"])


def _enrich_robot_scores(row: dict) -> dict:
    """Backfill HEIF + aligned 0–100 scores when DB row predates migration or specs are sparse."""
    slug = row.get("model_slug") or ""
    specs = dict(row.get("specs") or {})
    seed = SEED_SPECS_BY_SLUG.get(slug) or {}
    if seed:
        for key, val in seed.items():
            if key == "ai_stack":
                continue
            if val is None:
                continue
            cur = specs.get(key)
            if cur is None or cur == "" or cur == 0:
                specs[key] = val

    needs_rescore = row.get("heif_total") is None or (
        seed and float(row.get("heif_total") or 0) < 1.5
    )
    if not needs_rescore and row.get("heif_total") is not None:
        out = dict(row)
        out["specs"] = specs
        if out.get("score_cognition") is None and out.get("score_autonomy") is not None:
            out["score_cognition"] = out["score_autonomy"]
        if out.get("score_data_pipeline") is None and out.get("score_endurance") is not None:
            out["score_data_pipeline"] = out["score_endurance"]
        if out.get("score_production") is None and out.get("score_market_readiness") is not None:
            out["score_production"] = out["score_market_readiness"]
        return enrich_robot_with_ai_stack(out)

    scores = compute_scores(
        scoring_specs(specs),
        status=row.get("status") or "research",
        vendor=row.get("vendor") or "",
    )
    out = dict(row)
    out["specs"] = specs
    out.update(scores)
    return enrich_robot_with_ai_stack(out)

_ROBOTS_LIST_CACHE: dict = {"ts": 0.0, "payload": None}
_ROBOTS_LIST_TTL_SEC = 300
_REPORT_MEM_CACHE: dict = {}

_LIST_SPEC_KEYS = frozenset({
    "top_speed_mps",
    "payload_kg",
    "battery_life_h",
    "charge_time_h",
    "height_cm",
    "weight_kg",
    "finger_count",
    "peak_torque_nm",
    "peak_torque_note",
    "total_dof",
    "dof_note",
    "price_usd",
    "can_climb_stairs",
    "has_sdk",
    "ai_stack",
})


def _slim_robot_for_list(robot: dict) -> dict:
    """Drop heavy nested blobs (sources, deployment news) from list API payloads."""
    out = dict(robot)
    specs = dict(robot.get("specs") or {})
    out["specs"] = {k: specs[k] for k in _LIST_SPEC_KEYS if k in specs}
    return out


def _seed_robots_payload() -> list[dict]:
    """Static fallback when Postgres is unreachable (matches SEED_ROBOTS shape)."""
    rows = []
    from app.services.humanoid_ai_stack import specs_for_storage

    for i, robot in enumerate(SEED_ROBOTS, start=1):
        specs = specs_for_storage(robot["specs"], robot["model_slug"], robot.get("ai_stack"))
        scores = compute_scores(
            scoring_specs(specs),
            status=robot["status"],
            vendor=robot["vendor"],
        )
        payload = {
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
            "score_cognition": scores["score_cognition"],
            "score_safety": scores["score_safety"],
            "score_endurance": scores["score_endurance"],
            "score_data_pipeline": scores["score_data_pipeline"],
            "score_market_readiness": scores["score_market_readiness"],
            "score_production": scores["score_production"],
            "score_total": scores["score_total"],
            "heif_mobility": scores["heif_mobility"],
            "heif_manipulation": scores["heif_manipulation"],
            "heif_cognition": scores["heif_cognition"],
            "heif_safety": scores["heif_safety"],
            "heif_data_pipeline": scores["heif_data_pipeline"],
            "heif_production": scores["heif_production"],
            "heif_total": scores["heif_total"],
            "last_scraped_at": None,
        }
        stack = resolve_ai_stack(specs, robot["model_slug"])
        if stack:
            payload["ai_stack"] = stack
        rows.append(payload)
    rows.sort(key=lambda r: (-(r["score_total"] or 0), r["name"]))
    return rows


def _fetch_robots_from_db() -> list[dict]:
    with SessionLocal() as db:
        rows = db.execute(
            text("""
                SELECT id, name, vendor, model_slug, product_url, image_url, status,
                       specs, score_mobility, score_manipulation, score_autonomy,
                       score_safety, score_endurance, score_market_readiness,
                       score_total,
                       heif_mobility, heif_manipulation, heif_cognition,
                       heif_safety, heif_data_pipeline, heif_production, heif_total,
                       last_scraped_at
                FROM humanoid_benchmarks
                ORDER BY score_total DESC NULLS LAST, name ASC
            """)
        ).mappings().all()
        return [
            _enrich_robot_scores(dict(r))
            for r in rows
            if not is_junk_humanoid_row(r["name"], r["vendor"], r["model_slug"])
        ]


def _require_admin(db: Session = Depends(get_db)):
    """Lightweight admin guard reusing the same pattern as admin_extended."""
    from app.api.admin_extended import require_admin  # avoid circular at module level
    return require_admin


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("/robots")
def list_robots(response: Response):
    """Return all humanoid robots — pre-built snapshot (refreshed every 3 hours)."""
    from app.services.humanoid_robots_snapshot import serve_robots_list

    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=10800, stale-while-revalidate=86400"
    return serve_robots_list()


def _provenance_host(url: str | None) -> str:
    if not url:
        return ""
    try:
        from urllib.parse import urlparse
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""


def _spec_provenance(sources: list | None) -> dict:
    """Build {field: {url, quote, tier}} from fetch_verify provenance records (latest wins)."""
    prov: dict[str, dict] = {}
    for rec in sources or []:
        if not isinstance(rec, dict):
            continue
        evidence = rec.get("evidence") or {}
        if not isinstance(evidence, dict):
            continue
        for field, ev in evidence.items():
            if not isinstance(ev, dict):
                continue
            prov[field] = {
                "url": ev.get("url"),
                "quote": ev.get("quote"),
                "tier": ev.get("tier") or "third_party",
            }
    return prov


_CONFIDENCE_IGNORE_KEYS = frozenset({"ai_stack", "peak_torque_note"})


def _data_confidence(provenance: dict, specs: dict, heif_total: float | None) -> dict:
    """
    Confidence in a robot's spec data, weighted across all populated fields.

    Per-field weight: official source = 1.0, third-party source = 0.5, curated
    seed/datasheet (no fetch-verify provenance) = 0.85. So a flagship on curated
    data stays high; third-party-heavy robots are discounted. heif_total_adjusted
    mildly scales HEIF by confidence WITHOUT mutating the canonical score.
    """
    tier_weight = {"official": 1.0, "third_party": 0.5}
    populated = [
        k for k, v in (specs or {}).items()
        if k not in _CONFIDENCE_IGNORE_KEYS and v is not None and v != ""
    ]
    verified = [(provenance.get(k) or {}).get("tier") for k in populated]
    verified_n = sum(1 for t in verified if t in tier_weight)
    official_n = sum(1 for t in verified if t == "official")
    if not populated:
        return {"data_confidence": None, "confidence_label": "curated",
                "verified_field_count": 0, "official_field_count": 0,
                "heif_total_adjusted": heif_total}
    total = sum(tier_weight.get(t, 0.85) for t in verified)
    score = round(100 * total / len(populated))
    if verified_n == 0:
        label = "curated"
    else:
        label = "high" if score >= 80 else "medium" if score >= 60 else "low"
    adjusted = (round(float(heif_total) * (0.7 + 0.3 * score / 100), 2)
                if heif_total is not None else None)
    return {"data_confidence": score, "confidence_label": label,
            "verified_field_count": verified_n, "official_field_count": official_n,
            "heif_total_adjusted": adjusted}


@router.get("/robots/{slug}")
def get_robot(slug: str, db: Session = Depends(get_db)):
    """Return a single robot with full specs, sources, and provenance confidence."""
    row = db.execute(
        text("SELECT * FROM humanoid_benchmarks WHERE model_slug = :slug"),
        {"slug": slug},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Robot not found")
    out = _enrich_robot_scores(dict(row))
    # product_url is the canonical robot URL; expose it under the entity-resolution name too.
    out["robot_url"] = out.get("product_url")
    provenance = _spec_provenance(row.get("sources"))
    out["spec_provenance"] = provenance
    out.update(_data_confidence(provenance, out.get("specs") or {}, out.get("heif_total")))
    return out


@router.get("/gaps")
def get_spec_gaps(
    db: Session = Depends(get_db),
    sparse_only: bool = Query(False, description="Return only robots below fill threshold"),
    sparse_threshold_pct: float = Query(80.0, ge=0, le=100),
    slug: Optional[str] = Query(None, description="Gap report for one model_slug"),
):
    """
    Missing spec fields needed for HEIF scoring.

    Lists per-field coverage, per-dimension gaps, and robots that need backfill/scraping.
    """
    report = analyze_humanoid_spec_gaps(
        db,
        sparse_threshold_pct=sparse_threshold_pct,
        slug=slug,
    )
    if sparse_only:
        report = {
            **{k: report[k] for k in (
                "total_robots", "sparse_threshold_pct", "robots_sparse_specs",
                "avg_spec_fill_pct", "catalog_not_in_db_count",
            )},
            "sparse_robots": report["sparse_robots"],
            "worst_fields": report["field_coverage"][:8],
        }
    return report


@router.get("/gaps/plan")
def get_humanoid_data_plan(
    db: Session = Depends(get_db),
    slug: str = Query(..., description="model_slug for gap logic plan"),
):
    """
    Per-robot data gap plan: what's missing, why it blocks HEIF, and how to find it.
    Does not mutate the database (read-only plan).
    """
    from app.services.humanoid_gap_engine import build_humanoid_data_plan
    from app.services.humanoid_spec_gaps import analyze_robot_gaps

    row = db.execute(
        text("""
            SELECT model_slug, name, vendor, status, product_url, specs, sources,
                   heif_total, score_total, last_scraped_at
            FROM humanoid_benchmarks WHERE model_slug = :slug
        """),
        {"slug": slug},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Robot not found")
    row_dict = dict(row)
    return build_humanoid_data_plan(row_dict, analyze_robot_gaps(row_dict))


@router.post("/gap-engine/run")
def run_humanoid_gap_engine(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    limit: int = Query(15, ge=1, le=80),
    sparse_threshold_pct: float = Query(85.0, ge=0, le=100),
    slug: Optional[str] = Query(None, description="Run for one robot only"),
    plan_only: bool = Query(False, description="Build plans only — no scrape/rescore"),
    use_llm: bool = Query(True),
):
    """
    Second pass: logic engine plans missing data per robot, finds it, rescoring HEIF.
    """
    from app.services.humanoid_gap_engine import (
        run_humanoid_gap_engine_batch,
        run_humanoid_gap_engine_for_slug,
    )

    if slug:
        return run_humanoid_gap_engine_for_slug(
            db, slug, use_llm_scrape=use_llm, plan_only=plan_only,
        )

    def _batch() -> None:
        batch_db = SessionLocal()
        try:
            run_humanoid_gap_engine_batch(
                batch_db,
                limit=limit,
                sparse_threshold_pct=sparse_threshold_pct,
                use_llm_scrape=use_llm,
                plan_only=plan_only,
            )
        finally:
            batch_db.close()

    background_tasks.add_task(_batch)
    return {
        "status": "started",
        "limit": limit,
        "plan_only": plan_only,
        "message": "Humanoid gap engine batch started in background.",
    }


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    """Seed the 10 known humanoid robots with published specs + initial scores."""
    result = seed_robots(db)
    _ROBOTS_LIST_CACHE.clear()
    return result


@router.post("/discover")
async def discover_humanoids(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    use_catalog: bool = Query(True, description="Import curated catalog (~180 products)"),
    use_robot_companies: bool = Query(True, description="Include robot_companies humanoid vendors"),
    news_queries: int = Query(8, ge=0, le=20, description="Google News RSS queries for new startups"),
    agent_limit: int = Query(30, ge=0, le=100, description="Max AI HEIF assessments per run"),
    rescore_existing: bool = Query(False, description="Re-run agent on robots already in DB"),
    sync: bool = Query(
        False,
        description="Wait for full run (can take 5–15 min). Default false runs in background.",
    ),
):
    """
    Discover humanoid companies/startups, score with HEIR HEIF agent, upsert leaderboard.
    Runs in background by default so the HTTP request returns immediately.
    """
    kwargs = dict(
        use_catalog=use_catalog,
        use_robot_companies=use_robot_companies,
        news_queries=news_queries,
        agent_limit=agent_limit,
        rescore_existing=rescore_existing,
    )

    if sync:
        result = run_humanoid_discovery(db, **kwargs)
        result["catalog_size"] = catalog_count()
        _ROBOTS_LIST_CACHE.clear()
        return result

    def _run():
        from app.database import SessionLocal
        with SessionLocal() as bg_db:
            try:
                result = run_humanoid_discovery(bg_db, **kwargs)
                logger.info("Humanoid discovery finished: %s", result)
                _ROBOTS_LIST_CACHE.clear()
            except Exception as exc:
                logger.warning("Humanoid discovery background run failed: %s", exc)

    background_tasks.add_task(_run)
    est_min = max(1, agent_limit // 4) if agent_limit else 1
    return {
        "status": "started",
        "catalog_size": catalog_count(),
        "agent_limit": agent_limit,
        "rescore_existing": rescore_existing,
        "message": (
            f"Discovery running in background — up to {agent_limit} AI HEIF assessments, "
            f"expect ~{est_min}–{est_min * 2} min. Poll GET /api/humanoid/robots for updates."
        ),
    }


@router.post("/cleanup")
def cleanup_humanoids(
    db: Session = Depends(get_db),
    dry_run: bool = Query(False, description="Preview removals without deleting"),
):
    """Remove deployment pilots, duplicate variants, placeholders, and RSS junk."""
    result = cleanup_humanoid_benchmarks(db, dry_run=dry_run)
    if not dry_run:
        _ROBOTS_LIST_CACHE.clear()
    return result


@router.post("/repair")
def repair_humanoids(db: Session = Depends(get_db)):
    """
    One-shot index repair: delete headline junk, upsert Unitree/flagship seeds, backfill specs.
    """
    result = repair_humanoid_index(db)
    _ROBOTS_LIST_CACHE.clear()
    return result


@router.post("/backfill-specs")
def backfill_specs(db: Session = Depends(get_db)):
    """Sync catalog metadata and merge SEED_ROBOTS + catalog specs into sparse rows."""
    catalog_sync = sync_product_urls_from_catalog(db)
    result = backfill_humanoid_specs(db)
    _ROBOTS_LIST_CACHE.clear()
    return {"catalog_sync": catalog_sync, **result}


@router.post("/ensure-priority")
def ensure_priority(db: Session = Depends(get_db)):
    """Upsert Unitree G1/H1/R1 and other flagship robots from seed data."""
    result = ensure_priority_humanoids(db)
    _ROBOTS_LIST_CACHE.clear()
    return result


@router.post("/scrape/{slug}")
def scrape_one(slug: str, db: Session = Depends(get_db)):
    """Scrape fresh specs and recompute scores for one robot."""
    result = scrape_and_score_robot(db, slug)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


_VERIFIED_FIELD_KINDS: dict[str, str] = {}


def _verified_field_kinds() -> dict[str, str]:
    if not _VERIFIED_FIELD_KINDS:
        from app.services.humanoid_spec_gaps import SCORING_SPEC_FIELDS, METADATA_SPEC_FIELDS
        _VERIFIED_FIELD_KINDS.update({f: k for f, _dims, k in SCORING_SPEC_FIELDS})
        _VERIFIED_FIELD_KINDS.update({f: k for f, k in METADATA_SPEC_FIELDS})
    return _VERIFIED_FIELD_KINDS


def _coerce_verified(val, kind: str):
    if val is None:
        return None
    if kind == "bool":
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("true", "yes", "1")
    if kind == "numeric":
        if isinstance(val, (int, float)):
            return val
        import re as _re
        m = _re.search(r"-?\d[\d,]*\.?\d*", str(val))
        return float(m.group().replace(",", "")) if m else None
    return val


@router.post("/apply-verified-specs")
def apply_verified_specs(
    body: dict = Body(...),
    token: str = Query("", description="SCRAPER_CRON_TOKEN secret"),
    db: Session = Depends(get_db),
):
    """
    Apply externally fetch-verified specs (merge missing-only) + rescore + record provenance.

    Token-protected (SCRAPER_CRON_TOKEN). Only fills fields currently null/empty — never
    overwrites existing values. Body shape:
      {"items": [{"slug": "...", "specs": {field: value},
                  "evidence": {field: {"url": "...", "quote": "..."}}}]}
    """
    import json as _json

    expected = os.getenv("SCRAPER_CRON_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")

    kind_by_field = _verified_field_kinds()
    items = body.get("items") or []
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="body.items must be a list")

    now = datetime.now(timezone.utc)
    results: list[dict] = []
    for item in items:
        slug = (item or {}).get("slug")
        in_specs = (item or {}).get("specs") or {}
        evidence = (item or {}).get("evidence") or {}
        if not slug:
            continue
        row = db.execute(
            text("SELECT name, vendor, status, specs, sources, product_url, score_total, heif_total "
                 "FROM humanoid_benchmarks WHERE model_slug = :s"),
            {"s": slug},
        ).mappings().first()
        if not row:
            results.append({"slug": slug, "error": "not found"})
            continue
        existing = dict(row["specs"] or {})
        merge: dict = {}
        rejected: list[str] = []
        for field, val in in_specs.items():
            if field not in kind_by_field:
                rejected.append(field)
                continue
            cv = _coerce_verified(val, kind_by_field[field])
            if cv is not None and existing.get(field) in (None, ""):
                merge[field] = cv
        if not merge:
            results.append({"slug": slug, "filled": [], "rejected": rejected, "note": "nothing to fill"})
            continue
        merged = specs_for_storage({**existing, **merge}, slug)
        scores = compute_scores(scoring_specs(merged), status=row["status"], vendor=row["vendor"])
        official_host = _provenance_host(row["product_url"])
        ev_out = {}
        for f in merge:
            ev = dict(evidence.get(f) or {})
            if "tier" not in ev:
                ev_host = _provenance_host(ev.get("url"))
                ev["tier"] = "official" if (official_host and ev_host == official_host) else "third_party"
            ev_out[f] = ev
        prov = list(row["sources"] or []) + [{
            "method": "fetch_verify",
            "scraped_at": now.isoformat(),
            "fields": list(merge.keys()),
            "evidence": ev_out,
        }]
        db.execute(
            text(
                "UPDATE humanoid_benchmarks SET specs = cast(:specs as jsonb), "
                "sources = cast(:sources as jsonb), last_scraped_at = :now, updated_at = :now, "
                "score_mobility=:score_mobility, score_manipulation=:score_manipulation, "
                "score_autonomy=:score_autonomy, score_safety=:score_safety, "
                "score_endurance=:score_endurance, score_market_readiness=:score_market_readiness, "
                "score_total=:score_total, heif_mobility=:heif_mobility, heif_manipulation=:heif_manipulation, "
                "heif_cognition=:heif_cognition, heif_safety=:heif_safety, heif_data_pipeline=:heif_data_pipeline, "
                "heif_production=:heif_production, heif_total=:heif_total WHERE model_slug = :slug"
            ),
            {"specs": _json.dumps(merged), "sources": _json.dumps(prov[-30:]),
             "now": now, "slug": slug, **scores},
        )
        db.commit()
        results.append({
            "slug": slug,
            "filled": list(merge.keys()),
            "rejected": rejected,
            "score_total": [row["score_total"], scores["score_total"]],
            "heif_total": [row["heif_total"], scores["heif_total"]],
        })
    _ROBOTS_LIST_CACHE.clear()
    return {
        "applied": sum(1 for r in results if r.get("filled")),
        "robots": len(results),
        "results": results,
    }


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


@router.get("/cron/repair-index")
async def cron_repair_humanoid_index(
    token: str = Query("", description="SCRAPER_CRON_TOKEN secret"),
    db: Session = Depends(get_db),
):
    """
    Delete headline junk, upsert Unitree/flagships, backfill HEIF specs.
    GET /api/humanoid/cron/repair-index?token=YOUR_SCRAPER_CRON_TOKEN
    """
    expected = os.getenv("SCRAPER_CRON_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")
    result = repair_humanoid_index(db)
    _ROBOTS_LIST_CACHE.clear()
    return {"status": "ok", **result}


@router.get("/cron/sync-product-urls")
async def cron_sync_product_urls(
    token: str = Query("", description="SCRAPER_CRON_TOKEN secret"),
    db: Session = Depends(get_db),
):
    """
    Push curated catalog product_url values into humanoid_benchmarks.
    GET /api/humanoid/cron/sync-product-urls?token=YOUR_TOKEN
    """
    expected = os.getenv("SCRAPER_CRON_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")
    stats = sync_product_urls_from_catalog(db)
    _ROBOTS_LIST_CACHE.clear()
    return {"status": "ok", **stats}


@router.get("/cron/discover")
async def cron_discover_humanoids(
    background_tasks: BackgroundTasks,
    token: str = Query("", description="SCRAPER_CRON_TOKEN secret"),
    agent_limit: int = Query(25, ge=0, le=50),
    news_queries: int = Query(6, ge=0, le=15),
):
    """
    Weekly discovery cron — import catalog + news, AI-score up to ``agent_limit`` robots.
    GET /api/humanoid/cron/discover?token=YOUR_TOKEN
    """
    expected = os.getenv("SCRAPER_CRON_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")

    def _run():
        from app.database import SessionLocal
        with SessionLocal() as bg_db:
            try:
                run_humanoid_discovery(
                    bg_db,
                    use_catalog=True,
                    use_robot_companies=True,
                    news_queries=news_queries,
                    agent_limit=agent_limit,
                )
                _ROBOTS_LIST_CACHE.clear()
            except Exception as exc:
                logger.warning("Cron humanoid discovery failed: %s", exc)

    background_tasks.add_task(_run)
    return {
        "status": "started",
        "catalog_size": catalog_count(),
        "agent_limit": agent_limit,
        "message": "Humanoid discovery running in background.",
    }


# ── Report generator ─────────────────────────────────────────────────────────

_HUMANOID_REPORT_SQL = """
    SELECT name, vendor, model_slug, status, specs, sources,
           score_mobility, score_manipulation, score_autonomy,
           score_safety, score_endurance, score_market_readiness, score_total,
           heif_mobility, heif_manipulation, heif_cognition,
           heif_safety, heif_data_pipeline, heif_production, heif_total
    FROM humanoid_benchmarks
    WHERE score_total IS NOT NULL
    ORDER BY score_total DESC
"""


def _fetch_scored_humanoids(db: Session) -> list[dict]:
    rows = db.execute(text(_HUMANOID_REPORT_SQL)).mappings().all()
    return [dict(r) for r in rows]


def build_humanoid_report_payload(db: Session) -> dict:
    """
    Structured benchmark report from current scores.
    Used by daily cache refresh, GET /report, and LinkedIn post generator.
    """
    rows = _fetch_scored_humanoids(db)

    if not rows:
        return {"report": None, "generated_at": datetime.now(timezone.utc).isoformat()}

    robots = [
        r for r in rows
        if not is_junk_humanoid_row(r["name"], r["vendor"], r["model_slug"])
    ]
    top3 = robots[:3]
    leader = robots[0]

    dims = {
        "Mobility": "score_mobility",
        "Manipulation": "score_manipulation",
        "Cognition": "score_autonomy",
        "Safety": "score_safety",
        "Data Pipeline": "score_endurance",
        "Production": "score_market_readiness",
    }
    category_winners = {}
    for label, key in dims.items():
        best = max(robots, key=lambda r: r.get(key) or 0)
        category_winners[label] = {
            "name": best["name"],
            "vendor": best["vendor"],
            "score": round(best.get(key) or 0, 1),
        }

    available = [r for r in robots if r["status"] == "available"]
    pilot = [r for r in robots if r["status"] == "pilot"]
    research = [r for r in robots if r["status"] == "research"]

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

    deployment_payload = build_humanoid_deployment_report_payload(robots)
    deployment_summary = deployment_payload.get("report")
    if deployment_summary:
        dep_findings = deployment_summary.get("key_findings") or []
        findings.extend(dep_findings[:3])

    return {
        "report": {
            "title": f"Humanoid Robot Benchmark Report — {datetime.now(timezone.utc).strftime('%B %Y')}",
            "total_robots": len(robots),
            "available_count": len(available),
            "pilot_count": len(pilot),
            "research_count": len(research),
            "deployment_summary": {
                k: deployment_summary[k]
                for k in (
                    "deployment_tier_breakdown",
                    "evidence_class_breakdown",
                    "commercial_deployments_breakdown",
                    "poc_or_better_count",
                    "deployment_signal_count",
                    "poc_to_deployment_ratio",
                    "key_findings",
                )
                if deployment_summary and k in deployment_summary
            } if deployment_summary else None,
            "overall_leader": {
                "name": leader["name"],
                "vendor": leader["vendor"],
                "score": round(leader["score_total"] or 0, 1),
            },
            "top_3": [
                {
                    "name": r["name"],
                    "vendor": r["vendor"],
                    "score": round(r["score_total"] or 0, 1),
                    "status": r["status"],
                }
                for r in top3
            ],
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
                    "heif_total": round(r.get("heif_total") or 0, 2),
                    "heif_mobility": round(r.get("heif_mobility") or 0, 1),
                    "heif_manipulation": round(r.get("heif_manipulation") or 0, 1),
                    "heif_cognition": round(r.get("heif_cognition") or 0, 1),
                    "heif_safety": round(r.get("heif_safety") or 0, 1),
                    "heif_data_pipeline": round(r.get("heif_data_pipeline") or 0, 1),
                    "heif_production": round(r.get("heif_production") or 0, 1),
                }
                for i, r in enumerate(robots)
            ],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def set_humanoid_report_mem_cache(data: dict) -> None:
    _REPORT_MEM_CACHE["payload"] = data
    _REPORT_MEM_CACHE["ts"] = time.monotonic()


@router.get("/report")
def get_report(response: Response, db: Session = Depends(get_db)):
    """Benchmark report — L1 → durable cache only (3h robots-page refresh)."""
    from app.services.public_surface_cache import KEY_HUMANOID_REPORT, read_public_cache

    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=10800, stale-while-revalidate=86400"

    mem = _REPORT_MEM_CACHE.get("payload")
    if mem is not None:
        return mem

    cached = read_public_cache(KEY_HUMANOID_REPORT, stale_ok=True)
    if cached is not None:
        set_humanoid_report_mem_cache(cached)
        return cached

    return {"report": None, "generated_at": datetime.now(timezone.utc).isoformat(), "cache_pending": True}


@router.get("/deployment-report")
def get_deployment_report(db: Session = Depends(get_db)):
    """
    HEIF capability vs public PoC/deployment evidence.
    Live from DB (not cached) — use for adoption reviews and CSV export clients.
    """
    robots = _fetch_scored_humanoids(db)
    if not robots:
        raise HTTPException(
            status_code=404,
            detail="No benchmark data available. Run /seed or /discover first.",
        )
    return build_humanoid_deployment_report_payload(robots)


@router.get("/intelligence-report")
def get_intelligence_report(
    response: Response,
    top_n: int = Query(12, ge=5, le=25, description="How many top robots to explain in depth"),
):
    """HEIR intelligence report — pre-built snapshot only (refreshed every 3 hours)."""
    from app.services.humanoid_robots_snapshot import serve_intelligence_report

    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=10800, stale-while-revalidate=86400"
    return serve_intelligence_report()


def _intelligence_pdf_response(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_intelligence_pdf_bytes(
    db: Session, *, top_n: int = 12, renderer: str = "fast"
) -> tuple[bytes, str]:
    robots = _fetch_scored_humanoids(db)
    if not robots:
        raise HTTPException(status_code=404, detail="No benchmark data available.")
    robots = [
        r for r in robots
        if not is_junk_humanoid_row(r["name"], r["vendor"], r["model_slug"])
    ]
    payload = build_humanoid_intelligence_report_payload(robots, top_n=top_n, db=db)
    if not payload.get("report"):
        raise HTTPException(status_code=404, detail="Report unavailable")
    return build_humanoid_intelligence_report_pdf(payload, renderer=renderer)


@router.get("/intelligence-report/pdf")
def get_intelligence_report_pdf(
    top_n: int = Query(12, ge=5, le=25),
    renderer: str = Query(
        "fast",
        description="fast = Manus HTML/WeasyPrint PDF (default). reportlab = plain fallback.",
    ),
):
    """Download HEIR intelligence report PDF — cache hit when warm; otherwise builds on demand."""
    import base64

    from app.services.content_surfaces import KEY_HUMANOID_INTELLIGENCE_PDF
    from app.services.pipeline_cache_store import cache_read_safe, cache_write
    from app.services.public_surface_cache import maybe_schedule_public_cache_refresh

    maybe_schedule_public_cache_refresh()
    mode = (renderer or "fast").strip().lower()

    if mode in ("fast", "reportlab", ""):
        cached = cache_read_safe(KEY_HUMANOID_INTELLIGENCE_PDF, stale_ok=True)
        if cached and cached.get("bytes_b64"):
            pdf_bytes = base64.standard_b64decode(cached["bytes_b64"])
            filename = cached.get("filename") or "Humanoid_Intelligence_Report.pdf"
            return _intelligence_pdf_response(pdf_bytes, filename)

        db = SessionLocal()
        try:
            pdf_bytes, filename = _build_intelligence_pdf_bytes(db, top_n=top_n, renderer="fast")
            try:
                cache_write(
                    db,
                    KEY_HUMANOID_INTELLIGENCE_PDF,
                    {
                        "filename": filename,
                        "bytes_b64": base64.standard_b64encode(pdf_bytes).decode("ascii"),
                        "renderer": "fast",
                    },
                    ttl_minutes=120,
                )
            except Exception:
                logger.warning("Failed to cache intelligence PDF after on-demand build", exc_info=True)
        finally:
            db.close()
        return _intelligence_pdf_response(pdf_bytes, filename)

    db = SessionLocal()
    try:
        pdf_bytes, filename = _build_intelligence_pdf_bytes(db, top_n=top_n, renderer=renderer)
    finally:
        db.close()
    return _intelligence_pdf_response(pdf_bytes, filename)


@router.post("/deployment-news")
async def scan_deployment_news(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    persist: bool = Query(False, description="Save matched articles to humanoid_benchmarks.sources"),
    max_queries: Optional[int] = Query(None, ge=1, le=300, description="Cap RSS queries (default: all EN + ZH)"),
    include_chinese: bool = Query(True, description="Search Google News China RSS for Chinese vendors"),
    translate_chinese: bool = Query(True, description="Translate Chinese headlines to English via LLM"),
    sync: bool = Query(False, description="Wait for scan (5–10 min full run). Default false runs in background."),
):
    """
    Scan Google News (EN + ZH) for deployment / pilot / trial headlines by vendor and robot name.
    """
    kwargs = dict(
        persist=persist,
        max_queries=max_queries,
        use_db=True,
        include_chinese=include_chinese,
        translate_chinese=translate_chinese,
    )
    if sync:
        return run_humanoid_deployment_news_review(db, **kwargs)

    def _run():
        from app.database import SessionLocal
        with SessionLocal() as bg_db:
            try:
                result = run_humanoid_deployment_news_review(bg_db, **kwargs)
                logger.info("Deployment news scan finished: %s", result.get("summary"))
            except Exception as exc:
                logger.warning("Deployment news scan failed: %s", exc)

    background_tasks.add_task(_run)
    return {
        "status": "started",
        "persist": persist,
        "include_chinese": include_chinese,
        "message": "Deployment news scan running in background (EN + Chinese RSS). Poll /api/humanoid/deployment-report for updated sources.",
    }


@router.get("/deployment-news/report")
def get_deployment_news_report(
    db: Session = Depends(get_db),
    max_queries: Optional[int] = Query(40, ge=5, le=300),
    include_chinese: bool = Query(True),
    translate_chinese: bool = Query(True),
):
    """Run a bounded news scan and return results without persisting (preview)."""
    return run_humanoid_deployment_news_review(
        db,
        persist=False,
        max_queries=max_queries,
        use_db=True,
        include_chinese=include_chinese,
        translate_chinese=translate_chinese,
    )


# ── LinkedIn post generator ───────────────────────────────────────────────────

@router.get("/linkedin-post")
def generate_linkedin_post(db: Session = Depends(get_db)):
    """
    Generate a LinkedIn post from current benchmark results.
    Returns post text + a LinkedIn share URL.
    """
    from app.api.humanoid_benchmark import build_humanoid_report_payload
    report_data = build_humanoid_report_payload(db)
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

We scored {report['total_robots']} humanoid robots using the HEIF framework (HEIR 2026): Mobility, Manipulation, Cognition, Safety, Data Pipeline, and Production — each 0–4, shown as 0–100 on the live index.

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
