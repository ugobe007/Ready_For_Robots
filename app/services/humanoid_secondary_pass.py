"""
Humanoid benchmark secondary logic — five pillars (mirrors sales-lead secondary pass).

1. Missing data    — spec gaps, missing sources, stale scrape
2. Optimize data   — seed/catalog backfill, per-robot news scrape + LLM spec extract
3. Quality gate    — junk row detection, vendor/name coherence
4. Additional data — deployment/trial news with cited press URLs (EN + ZH RSS)
5. Capability rank — evidence-weighted confidence for HEIF / deployment claims
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.humanoid_catalog_cleanup import is_junk_humanoid_row
from app.services.humanoid_deployment_news import (
    news_evidence_level_from_sources,
    run_humanoid_deployment_news_review,
)
from app.services.humanoid_spec_gaps import analyze_humanoid_spec_gaps, analyze_robot_gaps

logger = logging.getLogger(__name__)

DEFAULT_HUMANOID_BATCH_LIMIT = 40
MAX_HUMANOID_BATCH_LIMIT = 80

PILLAR_MISSING = "missing_data"
PILLAR_OPTIMIZE = "optimize_data"
PILLAR_QUALITY = "quality_gate"
PILLAR_ADDITIONAL = "additional_data"
PILLAR_RANK = "capability_rank"

PASS_BACKFILL = "spec_backfill"
PASS_SCRAPE = "news_spec_scrape"
PASS_DEPLOYMENT_NEWS = "deployment_news"
PASS_QUALITY = "quality_review"
PASS_ASSESSMENT = "capability_assessment"

_EVIDENCE_WEIGHTS = {
    "deployment": 1.0,
    "trial": 0.65,
    "humanoid_mention": 0.35,
    "none": 0.0,
}


def _fetch_robot_row(db: Session, slug: str) -> Optional[dict]:
    row = db.execute(
        text("""
            SELECT model_slug, name, vendor, status, product_url, specs, sources,
                   heif_total, score_total, last_scraped_at
            FROM humanoid_benchmarks WHERE model_slug = :slug
        """),
        {"slug": slug},
    ).mappings().first()
    return dict(row) if row else None


def select_humanoid_repair_candidates(
    db: Session,
    *,
    limit: int = DEFAULT_HUMANOID_BATCH_LIMIT,
    sparse_threshold_pct: float = 85.0,
) -> List[dict]:
    """Rank robots needing secondary rescue (sparse specs or no cited sources)."""
    summary = analyze_humanoid_spec_gaps(db, sparse_threshold_pct=sparse_threshold_pct)
    gaps = summary.get("sparse_robots") or []

    enriched: List[dict] = []
    for g in gaps:
        row = _fetch_robot_row(db, g["model_slug"])
        if not row:
            continue
        sources = row.get("sources") or []
        news_level = news_evidence_level_from_sources(sources)
        priority = (100 - g.get("spec_fill_pct", 0)) + (0 if sources else 25)
        if news_level == "none":
            priority += 15
        if row.get("heif_total"):
            priority += float(row["heif_total"]) * 5
        enriched.append({
            **g,
            "priority": round(priority, 2),
            "news_evidence_level": news_level,
            "source_count": len(sources),
        })

    # Also include high-score robots missing sources even if specs are full
    if len(enriched) < limit:
        rows = db.execute(
            text("""
                SELECT model_slug, name, vendor, specs, sources, heif_total, score_total
                FROM humanoid_benchmarks
                WHERE score_total IS NOT NULL
                ORDER BY score_total DESC NULLS LAST
                LIMIT :pool
            """),
            {"pool": limit * 3},
        ).mappings().all()
        seen = {e["model_slug"] for e in enriched}
        for r in rows:
            slug = r["model_slug"]
            if slug in seen:
                continue
            sources = r["sources"] or []
            if len(sources) >= 2:
                continue
            gap = analyze_robot_gaps(dict(r))
            enriched.append({
                **gap,
                "priority": float(r["score_total"] or 0) + 20,
                "news_evidence_level": news_evidence_level_from_sources(sources),
                "source_count": len(sources),
            })
            seen.add(slug)
            if len(enriched) >= limit:
                break

    enriched.sort(key=lambda x: x.get("priority", 0), reverse=True)
    return enriched[: max(1, min(int(limit), MAX_HUMANOID_BATCH_LIMIT))]


def _quality_verdict(row: dict) -> dict:
    name = row.get("name") or ""
    vendor = row.get("vendor") or ""
    slug = row.get("model_slug") or ""
    junk = is_junk_humanoid_row(name, vendor, slug)
    vendor_in_name = vendor.lower() in name.lower() if vendor and name else False
    return {
        "is_valid_humanoid": not junk,
        "junk_reason": "junk_pattern" if junk else None,
        "vendor_name_coherent": vendor_in_name or len(vendor) <= 3,
        "recommendation": "quarantine" if junk else "keep",
    }


def _capability_rank(row: dict, gap: dict, *, news_level: str) -> dict:
    spec_fill = float(gap.get("spec_fill_pct") or 0)
    heif = float(row.get("heif_total") or 0)
    score = float(row.get("score_total") or 0)
    sources = row.get("sources") or []
    cited = sum(1 for s in sources if s.get("url"))
    evidence = _EVIDENCE_WEIGHTS.get(news_level, 0.0)

    capability_confidence = round(
        0.35 * (spec_fill / 100.0) * 100
        + 0.25 * min(heif / 4.0, 1.0) * 100
        + 0.20 * min(score / 100.0, 1.0) * 100
        + 0.20 * evidence * 100,
        2,
    )

    return {
        "capability_confidence_rank": capability_confidence,
        "spec_fill_pct": spec_fill,
        "heif_total": heif,
        "score_total": score,
        "cited_source_count": cited,
        "news_evidence_level": news_level,
        "missing_scoring_fields": gap.get("missing_scoring_fields") or [],
    }


def build_humanoid_assessment(
    row: dict,
    gap: dict,
    *,
    pass_outcomes: Optional[Dict[str, str]] = None,
    fields_filled: Optional[List[str]] = None,
    news_articles: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    sources = row.get("sources") or []
    news_level = news_evidence_level_from_sources(sources)
    quality = _quality_verdict(row)
    rank = _capability_rank(row, gap, news_level=news_level)

    cited_sources = [
        {
            "url": s.get("url"),
            "title": s.get("title_en") or s.get("title"),
            "type": s.get("type"),
            "evidence_level": s.get("evidence_level"),
            "scraped_at": s.get("scraped_at"),
        }
        for s in sources
        if s.get("url")
    ][:8]

    return {
        "pillars": {
            PILLAR_MISSING: {
                "missing_scoring_fields": gap.get("missing_scoring_fields"),
                "missing_row_fields": gap.get("missing_row_fields"),
                "spec_fill_pct": gap.get("spec_fill_pct"),
            },
            PILLAR_OPTIMIZE: {
                "fields_improved": list(fields_filled or []),
                "pass_outcomes": dict(pass_outcomes or {}),
            },
            PILLAR_QUALITY: quality,
            PILLAR_ADDITIONAL: {
                "cited_sources": cited_sources,
                "news_scan_articles": (news_articles or [])[:5],
                "news_evidence_level": news_level,
                "deployment_signals": [
                    s.get("signals") for s in sources if s.get("evidence_level") in ("deployment", "trial")
                ][:4],
            },
            PILLAR_RANK: rank,
        },
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "model_slug": row.get("model_slug"),
        "name": row.get("name"),
        "vendor": row.get("vendor"),
    }


def _stamp_humanoid_assessment(db: Session, slug: str, assessment: dict) -> None:
    row = db.execute(
        text("SELECT specs FROM humanoid_benchmarks WHERE model_slug = :slug"),
        {"slug": slug},
    ).first()
    if not row:
        return
    specs = dict(row[0] or {})
    specs["secondary_assessment"] = assessment
    db.execute(
        text("""
            UPDATE humanoid_benchmarks
            SET specs = cast(:specs as jsonb), updated_at = :now
            WHERE model_slug = :slug
        """),
        {"slug": slug, "specs": json.dumps(specs), "now": datetime.now(timezone.utc)},
    )
    db.commit()


def run_rescue_passes_for_humanoid(
    db: Session,
    candidate: dict,
    *,
    use_llm_scrape: bool = True,
    run_deployment_scan: bool = True,
) -> Dict[str, Any]:
    """Delegate to gap logic engine: plan → find data → rescore."""
    from app.services.humanoid_gap_engine import execute_humanoid_data_plan, build_humanoid_data_plan

    slug = candidate["model_slug"]
    row = _fetch_robot_row(db, slug)
    if not row:
        return {"model_slug": slug, "skipped": True, "reason": "not_found"}

    gap_before = analyze_robot_gaps(row)
    plan = build_humanoid_data_plan(row, gap_before)
    engine_result = execute_humanoid_data_plan(
        db,
        row,
        plan,
        use_llm_scrape=use_llm_scrape,
        run_deployment_scan=run_deployment_scan,
    )

    row = _fetch_robot_row(db, slug) or row
    gap_after = analyze_robot_gaps(row)
    news_level = news_evidence_level_from_sources(row.get("sources") or [])
    quality = _quality_verdict(row)
    outcomes = dict(engine_result.get("step_outcomes") or {})
    outcomes[PASS_QUALITY] = "passed" if quality["is_valid_humanoid"] else "failed"
    if run_deployment_scan:
        outcomes.setdefault(PASS_DEPLOYMENT_NEWS, "deferred_batch")
    outcomes[PASS_BACKFILL] = outcomes.get("seed_catalog_merge", "skipped")
    outcomes[PASS_SCRAPE] = outcomes.get("news_llm_scrape", "skipped")
    outcomes[PASS_ASSESSMENT] = outcomes.get("rescore", "ok")

    assessment = build_humanoid_assessment(
        row,
        gap_after,
        pass_outcomes=outcomes,
        fields_filled=engine_result.get("fields_filled"),
        news_articles=[],
    )
    _stamp_humanoid_assessment(db, slug, assessment)

    return {
        "model_slug": slug,
        "name": row.get("name"),
        "vendor": row.get("vendor"),
        "plan_summary": plan.get("summary"),
        "action_plan": plan.get("action_plan"),
        "pass_outcomes": outcomes,
        "fields_filled": engine_result.get("fields_filled"),
        "gaps_before": engine_result.get("gaps_before"),
        "gaps_after": engine_result.get("gaps_after"),
        "spec_fill_before": engine_result.get("spec_fill_before"),
        "spec_fill_after": engine_result.get("spec_fill_after"),
        "scores_before": engine_result.get("scores_before"),
        "scores_after": engine_result.get("scores_after"),
        "capability_confidence_rank": assessment["pillars"][PILLAR_RANK]["capability_confidence_rank"],
        "cited_sources": len(assessment["pillars"][PILLAR_ADDITIONAL]["cited_sources"]),
        "is_valid_humanoid": quality["is_valid_humanoid"],
    }


def run_humanoid_secondary_pass_batch(
    db: Session,
    *,
    limit: int = DEFAULT_HUMANOID_BATCH_LIMIT,
    sparse_threshold_pct: float = 85.0,
    use_llm_scrape: bool = True,
    persist_deployment_news: bool = True,
    deployment_query_cap: int = 24,
) -> Dict[str, Any]:
    """Full humanoid secondary batch: per-robot rescue + fleet deployment news scan."""
    candidates = select_humanoid_repair_candidates(
        db, limit=limit, sparse_threshold_pct=sparse_threshold_pct
    )

    results: List[Dict[str, Any]] = []
    errors = 0
    for cand in candidates:
        try:
            results.append(
                run_rescue_passes_for_humanoid(
                    db,
                    cand,
                    use_llm_scrape=use_llm_scrape,
                    run_deployment_scan=False,
                )
            )
        except Exception as exc:
            errors += 1
            db.rollback()
            logger.warning("Humanoid secondary failed %s: %s", cand.get("model_slug"), exc)
            if len(results) < 20:
                results.append({"model_slug": cand.get("model_slug"), "error": str(exc)[:200]})

    deployment_result: Dict[str, Any] = {}
    if persist_deployment_news:
        try:
            deployment_result = run_humanoid_deployment_news_review(
                db,
                persist=True,
                max_queries=deployment_query_cap,
                include_chinese=True,
                translate_chinese=True,
            )
            for entry in (deployment_result.get("robots") or [])[:limit]:
                slug = entry.get("model_slug")
                if not slug:
                    continue
                row = _fetch_robot_row(db, slug)
                if not row:
                    continue
                gap = analyze_robot_gaps(row)
                assessment = build_humanoid_assessment(
                    row,
                    gap,
                    news_articles=entry.get("articles"),
                )
                _stamp_humanoid_assessment(db, slug, assessment)
        except Exception as exc:
            logger.warning("Fleet deployment news scan failed: %s", exc)
            deployment_result = {"error": str(exc)[:200]}

    gap_summary = analyze_humanoid_spec_gaps(db, sparse_threshold_pct=sparse_threshold_pct)

    return {
        "candidates": len(candidates),
        "processed": len(results),
        "errors": errors,
        "avg_spec_fill_pct": gap_summary.get("avg_spec_fill_pct"),
        "robots_sparse_specs": gap_summary.get("robots_sparse_specs"),
        "deployment_news": {
            "robots_updated": (deployment_result.get("persist") or {}).get("robots_updated"),
            "summary": deployment_result.get("summary"),
            "key_findings": deployment_result.get("key_findings"),
        },
        "sample": results[:15],
        "top_capability_ranks": sorted(
            [r for r in results if r.get("capability_confidence_rank")],
            key=lambda x: x["capability_confidence_rank"],
            reverse=True,
        )[:10],
    }


def run_humanoid_secondary_pass_batch_and_refresh_caches(
    *,
    limit: int = DEFAULT_HUMANOID_BATCH_LIMIT,
    sparse_threshold_pct: float = 85.0,
    use_llm_scrape: bool = True,
    persist_deployment_news: bool = True,
    deployment_query_cap: int = 24,
) -> Dict[str, Any]:
    """Run humanoid secondary batch then refresh public humanoid benchmark cache."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        stats = run_humanoid_secondary_pass_batch(
            db,
            limit=limit,
            sparse_threshold_pct=sparse_threshold_pct,
            use_llm_scrape=use_llm_scrape,
            persist_deployment_news=persist_deployment_news,
            deployment_query_cap=deployment_query_cap,
        )
    finally:
        db.close()

    try:
        from app.services.public_surface_cache import schedule_public_cache_refresh

        schedule_public_cache_refresh(pipeline_only=True, reason="humanoid_secondary_pass")
        stats["cache_refresh"] = "scheduled"
    except Exception as exc:
        logger.warning("Humanoid cache refresh after secondary pass failed: %s", exc)
        stats["cache_refresh"] = f"failed: {exc}"

    return stats
