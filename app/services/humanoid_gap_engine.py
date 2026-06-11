"""
Humanoid data gap logic engine — per-robot reasoning: what is missing, where to find it, then rescore.

Flow:
  1. analyze_robot_gaps (humanoid_spec_gaps) — field-level missing list
  2. build_humanoid_data_plan — maps gaps → HEIF impact + resolution steps + search queries
  3. execute_humanoid_data_plan — seed/catalog → product URL → targeted scrape → rescore
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.humanoid_benchmark_backfill import backfill_sparse_humanoids, rescore_humanoid
from app.services.humanoid_spec_gaps import (
    SEED_SPECS_BY_SLUG,
    analyze_robot_gaps,
    scoring_field_defs,
    spec_field_missing,
)
from app.services.humanoid_vendor_catalog import catalog_entries

logger = logging.getLogger(__name__)

SOURCE_SEED_CATALOG = "seed_catalog"
SOURCE_PRODUCT_PAGE = "product_page"
SOURCE_NEWS_LLM = "news_llm"
SOURCE_DEPLOYMENT_NEWS = "deployment_news"

# Human labels + why each field matters for HEIF scoring
_FIELD_META: Dict[str, dict] = {
    "top_speed_mps": {
        "label": "Top speed (m/s)",
        "why": "Mobility HEIF tiers on locomotion speed and dynamic capability.",
        "search_hint": "top speed m/s locomotion specifications",
    },
    "can_climb_stairs": {
        "label": "Stair climbing",
        "why": "Mobility HEIF rewards stair-capable bipeds for real facility use.",
        "search_hint": "stairs stair climbing capability",
    },
    "can_navigate_rough_terrain": {
        "label": "Rough terrain navigation",
        "why": "Mobility HEIF scores outdoor / uneven-floor readiness.",
        "search_hint": "rough terrain outdoor navigation",
    },
    "can_run": {
        "label": "Running capability",
        "why": "Mobility HEIF bonus for dynamic locomotion beyond walking.",
        "search_hint": "running jog dynamic locomotion speed",
    },
    "payload_kg": {
        "label": "Arm payload (kg)",
        "why": "Manipulation HEIF is driven primarily by payload capacity.",
        "search_hint": "payload kg arm lift capacity datasheet",
    },
    "finger_count": {
        "label": "Finger / DOF count",
        "why": "Manipulation HEIF uses dexterity and hand complexity.",
        "search_hint": "fingers DOF dexterous hand specifications",
    },
    "has_dexterous_hands": {
        "label": "Dexterous hands",
        "why": "Manipulation HEIF distinguishes tool-use vs gripper-only hands.",
        "search_hint": "dexterous hands manipulation gripper",
    },
    "autonomy_level": {
        "label": "Autonomy level",
        "why": "Cognition HEIF maps teleop vs semi vs full autonomy.",
        "search_hint": "autonomy teleoperation autonomous AI stack",
    },
    "commercial_deployments": {
        "label": "Commercial deployments",
        "why": "Cognition, data pipeline, and production HEIF weight fleet evidence.",
        "search_hint": "commercial deployment pilot customer fleet",
    },
    "has_sdk": {
        "label": "Developer SDK",
        "why": "Cognition and data pipeline HEIF reward integrator-ready APIs.",
        "search_hint": "SDK developer API software kit",
    },
    "has_api": {
        "label": "Control API",
        "why": "Data pipeline HEIF needs programmatic fleet integration paths.",
        "search_hint": "REST API control interface integration",
    },
    "has_estop": {
        "label": "Emergency stop",
        "why": "Safety HEIF requires e-stop for human-collaborative workcells.",
        "search_hint": "emergency stop e-stop safety",
    },
    "safety_certified": {
        "label": "Safety certification",
        "why": "Safety HEIF rewards CE/ISO collaborative robot certifications.",
        "search_hint": "ISO 10218 CE safety certification collaborative",
    },
    "force_limited_joints": {
        "label": "Force-limited joints",
        "why": "Safety HEIF uses ISO TS 15066 force-limited operation.",
        "search_hint": "force limited joints ISO 15066 collaborative",
    },
    "collision_force_n": {
        "label": "Collision force (N)",
        "why": "Safety HEIF compares contact force against ISO TS 15066 thresholds.",
        "search_hint": "collision force newtons ISO 15066",
    },
    "battery_life_h": {
        "label": "Battery life (hours)",
        "why": "Endurance HEIF scores runtime for shift-length tasks.",
        "search_hint": "battery life hours runtime endurance",
    },
    "charge_time_h": {
        "label": "Charge time (hours)",
        "why": "Endurance HEIF penalizes long recharge downtime.",
        "search_hint": "charge time charging hours",
    },
    "hot_swap_battery": {
        "label": "Hot-swap battery",
        "why": "Endurance HEIF bonus for field-swappable power modules.",
        "search_hint": "hot swap battery modular power",
    },
    "price_usd": {
        "label": "Price (USD)",
        "why": "Production HEIF uses commercial pricing as market-readiness signal.",
        "search_hint": "price USD cost MSRP purchase",
    },
    "has_support_sla": {
        "label": "Support SLA",
        "why": "Production HEIF rewards enterprise support and service contracts.",
        "search_hint": "support SLA warranty service contract",
    },
    "height_cm": {
        "label": "Height (cm)",
        "why": "Metadata for buyer fit — not a HEIF dimension but needed for comparisons.",
        "search_hint": "height cm dimensions specifications",
    },
    "weight_kg": {
        "label": "Weight (kg)",
        "why": "Metadata for payload / facility planning.",
        "search_hint": "weight kg mass specifications",
    },
}

_CATALOG_BY_SLUG: Dict[str, dict] = {
    e["model_slug"]: e for e in catalog_entries() if e.get("model_slug")
}


@dataclass(frozen=True)
class ResolutionStep:
    step: str
    priority: int
    targets: tuple
    queries: tuple = ()
    note: str = ""


def _field_sources(field: str, *, seed_available: bool, has_product_url: bool) -> List[str]:
    sources: List[str] = []
    if seed_available:
        sources.append(SOURCE_SEED_CATALOG)
    if has_product_url:
        sources.append(SOURCE_PRODUCT_PAGE)
    if field == "commercial_deployments":
        sources.append(SOURCE_DEPLOYMENT_NEWS)
    sources.append(SOURCE_NEWS_LLM)
    return sources


def _search_queries(name: str, vendor: str, fields: List[str]) -> List[str]:
    base = f"{vendor} {name} humanoid robot specifications"
    queries = [base]
    for field in fields[:4]:
        meta = _FIELD_META.get(field, {})
        hint = meta.get("search_hint") or field.replace("_", " ")
        queries.append(f"{vendor} {name} {hint}")
    return queries


def _dimensions_at_risk(missing_scoring: List[str]) -> List[str]:
    dims: set[str] = set()
    field_dims = {f.name: f.dimensions for f in scoring_field_defs()}
    for field in missing_scoring:
        dims.update(field_dims.get(field, ()))
    # Normalize legacy endurance label (battery fields use "endurance" in spec_gaps)
    normalized = {"data_pipeline" if d == "endurance" else d for d in dims}
    return sorted(normalized)


def build_humanoid_data_plan(row: dict, gap: Optional[dict] = None) -> Dict[str, Any]:
    """
    Logic engine output: what's missing, why it matters, and ordered steps to find it.
    """
    gap = gap or analyze_robot_gaps(row)
    slug = row.get("model_slug") or ""
    name = row.get("name") or ""
    vendor = row.get("vendor") or ""
    seed_available = bool(gap.get("seed_specs_available") or slug in SEED_SPECS_BY_SLUG)
    has_product_url = bool(row.get("product_url"))
    catalog_entry = _CATALOG_BY_SLUG.get(slug) or {}

    missing_scoring = list(gap.get("missing_scoring_fields") or [])
    missing_metadata = list(gap.get("missing_metadata_fields") or [])
    missing_row = list(gap.get("missing_row_fields") or [])

    missing_items: List[dict] = []
    seed_fillable: List[str] = []
    catalog_fillable: List[str] = []
    news_targets: List[str] = []

    catalog_specs = dict(catalog_entry.get("specs") or {})
    seed_specs = SEED_SPECS_BY_SLUG.get(slug) or {}

    for field in missing_scoring:
        meta = _FIELD_META.get(field, {})
        field_def = next((f for f in scoring_field_defs() if f.name == field), None)
        kind = field_def.kind if field_def else "numeric"
        can_seed = not spec_field_missing(seed_specs, field, kind)
        can_catalog = not spec_field_missing(catalog_specs, field, kind)
        if can_seed or can_catalog:
            seed_fillable.append(field)
        else:
            news_targets.append(field)
        missing_items.append({
            "field": field,
            "label": meta.get("label", field),
            "dimensions": list(field_def.dimensions) if field_def else [],
            "kind": kind,
            "why": meta.get("why", "Required for HEIF scoring."),
            "find_via": _field_sources(field, seed_available=can_seed or can_catalog, has_product_url=has_product_url),
            "search_queries": _search_queries(name, vendor, [field]),
            "seed_available": can_seed,
            "catalog_available": can_catalog,
        })

    for field in missing_metadata:
        meta = _FIELD_META.get(field, {})
        kind = "numeric"
        can_seed = not spec_field_missing(seed_specs, field, kind)
        can_catalog = not spec_field_missing(catalog_specs, field, kind)
        if can_seed or can_catalog:
            seed_fillable.append(field)
        else:
            news_targets.append(field)
        missing_items.append({
            "field": field,
            "label": meta.get("label", field),
            "dimensions": [],
            "kind": kind,
            "why": meta.get("why", "Metadata for buyer comparisons."),
            "find_via": _field_sources(field, seed_available=can_seed or can_catalog, has_product_url=has_product_url),
            "search_queries": _search_queries(name, vendor, [field]),
            "seed_available": can_seed,
            "catalog_available": can_catalog,
        })

    row_items = []
    for field in missing_row:
        if field == "product_url" and catalog_entry.get("product_url"):
            row_items.append({
                "field": field,
                "label": "Product URL",
                "why": "Manufacturer page is the primary datasheet source.",
                "find_via": [SOURCE_PRODUCT_PAGE],
                "catalog_available": True,
            })
        elif field == "sources":
            row_items.append({
                "field": field,
                "label": "Cited sources",
                "why": "HEIF claims need press URLs for evidence weighting.",
                "find_via": [SOURCE_NEWS_LLM, SOURCE_DEPLOYMENT_NEWS],
            })
        else:
            row_items.append({
                "field": field,
                "label": field.replace("_", " "),
                "why": "Row metadata for scrape freshness and provenance.",
                "find_via": [SOURCE_NEWS_LLM],
            })

    action_steps: List[ResolutionStep] = []
    pri = 1
    if seed_fillable or catalog_fillable:
        action_steps.append(ResolutionStep(
            step="seed_catalog_merge",
            priority=pri,
            targets=tuple(sorted(set(seed_fillable + catalog_fillable))),
            note="Merge curated seed/catalog specs without overwriting existing values.",
        ))
        pri += 1
    if "product_url" in missing_row and catalog_entry.get("product_url"):
        action_steps.append(ResolutionStep(
            step="sync_product_url",
            priority=pri,
            targets=("product_url",),
            note="Copy product URL from curated vendor catalog.",
        ))
        pri += 1
    if news_targets or "sources" in missing_row:
        action_steps.append(ResolutionStep(
            step="news_llm_scrape",
            priority=pri,
            targets=tuple(news_targets[:12]),
            queries=tuple(_search_queries(name, vendor, news_targets)),
            note="Search news/datasheets and LLM-extract only fields still missing.",
        ))
        pri += 1
    if "commercial_deployments" in missing_scoring or "sources" in missing_row:
        action_steps.append(ResolutionStep(
            step="deployment_news_scan",
            priority=pri,
            targets=("commercial_deployments", "sources"),
            note="Fleet deployment / trial press evidence (batch RSS scan).",
        ))
        pri += 1
    action_steps.append(ResolutionStep(
        step="rescore",
        priority=pri,
        targets=(),
        note="Recompute HEIF 0–4 and 0–100 scores from merged specs.",
    ))

    dims_risk = _dimensions_at_risk(missing_scoring)
    summary_parts = []
    if missing_scoring:
        summary_parts.append(f"Missing {len(missing_scoring)} scoring field(s)")
        if dims_risk:
            summary_parts.append(f"blocking {', '.join(dims_risk)} HEIF")
    if seed_fillable:
        summary_parts.append(f"seed/catalog can fill {len(seed_fillable)}")
    if news_targets:
        summary_parts.append(f"need news scrape for {len(news_targets)}")
    if not summary_parts:
        summary_parts.append("Specs complete — rescore only if stale.")

    return {
        "model_slug": slug,
        "name": name,
        "vendor": vendor,
        "scores": {
            "heif_total": row.get("heif_total"),
            "score_total": row.get("score_total"),
        },
        "spec_fill_pct": gap.get("spec_fill_pct"),
        "dimensions_at_risk": dims_risk,
        "missing_items": missing_items,
        "missing_row_items": row_items,
        "action_plan": [
            {
                "step": s.step,
                "priority": s.priority,
                "targets": list(s.targets),
                "queries": list(s.queries),
                "note": s.note,
            }
            for s in action_steps
        ],
        "summary": "; ".join(summary_parts) + ".",
        "planned_at": datetime.now(timezone.utc).isoformat(),
    }


def _sync_product_url_from_catalog(db: Session, slug: str) -> bool:
    entry = _CATALOG_BY_SLUG.get(slug) or {}
    url = (entry.get("product_url") or "").strip()
    if not url:
        return False
    db.execute(
        text("""
            UPDATE humanoid_benchmarks
            SET product_url = :url, updated_at = :now
            WHERE model_slug = :slug AND (product_url IS NULL OR product_url = '')
        """),
        {"slug": slug, "url": url, "now": datetime.now(timezone.utc)},
    )
    db.commit()
    return True


def _stamp_data_plan(db: Session, slug: str, plan: dict, *, execution: Optional[dict] = None) -> None:
    row = db.execute(
        text("SELECT specs FROM humanoid_benchmarks WHERE model_slug = :slug"),
        {"slug": slug},
    ).first()
    if not row:
        return
    specs = dict(row[0] or {})
    specs["data_gap_plan"] = plan
    if execution:
        specs["data_gap_execution"] = execution
    db.execute(
        text("""
            UPDATE humanoid_benchmarks
            SET specs = cast(:specs as jsonb), updated_at = :now
            WHERE model_slug = :slug
        """),
        {"slug": slug, "specs": json.dumps(specs), "now": datetime.now(timezone.utc)},
    )
    db.commit()


def execute_humanoid_data_plan(
    db: Session,
    row: dict,
    plan: dict,
    *,
    use_llm_scrape: bool = True,
    run_deployment_scan: bool = False,
) -> Dict[str, Any]:
    """Run the action plan: find missing data, merge, rescore."""
    slug = plan.get("model_slug") or row.get("model_slug")
    gap_before = analyze_robot_gaps(row)
    scores_before = {
        "heif_total": row.get("heif_total"),
        "score_total": row.get("score_total"),
    }
    step_outcomes: Dict[str, str] = {}
    fields_filled: List[str] = []

    for step in plan.get("action_plan") or []:
        key = step.get("step")
        if key == "seed_catalog_merge":
            stats = backfill_sparse_humanoids(db, slugs=[slug], rescore=True)
            if stats.get("updated"):
                step_outcomes[key] = "filled"
                fields_filled.extend(list(step.get("targets") or []))
            else:
                step_outcomes[key] = "skipped"
        elif key == "sync_product_url":
            if _sync_product_url_from_catalog(db, slug):
                step_outcomes[key] = "filled"
                fields_filled.append("product_url")
            else:
                step_outcomes[key] = "skipped"
        elif key == "news_llm_scrape" and use_llm_scrape:
            try:
                from app.services.humanoid_scraper import scrape_and_score_robot

                targets = list(step.get("targets") or [])
                result = scrape_and_score_robot(
                    db, slug, missing_fields=targets or None, search_queries=list(step.get("queries") or []),
                )
                if result.get("error"):
                    step_outcomes[key] = "failed"
                elif result.get("fields_filled"):
                    step_outcomes[key] = "filled"
                    fields_filled.extend(result["fields_filled"])
                elif result.get("sources_found", 0) > 0:
                    step_outcomes[key] = "partial"
                    fields_filled.append("sources")
                else:
                    step_outcomes[key] = "skipped"
            except Exception as exc:
                db.rollback()
                step_outcomes[key] = "error"
                logger.warning("Gap engine scrape failed %s: %s", slug, exc)
        elif key == "news_llm_scrape":
            step_outcomes[key] = "skipped"
        elif key == "deployment_news_scan":
            step_outcomes[key] = "deferred_batch" if not run_deployment_scan else "batch"
        elif key == "rescore":
            res = rescore_humanoid(db, slug)
            step_outcomes[key] = "ok" if res.get("updated") else "unchanged"

    fresh = db.execute(
        text("""
            SELECT model_slug, name, vendor, status, product_url, specs, sources,
                   heif_total, score_total, last_scraped_at
            FROM humanoid_benchmarks WHERE model_slug = :slug
        """),
        {"slug": slug},
    ).mappings().first()
    fresh_row = dict(fresh) if fresh else row
    gap_after = analyze_robot_gaps(fresh_row)

    execution = {
        "step_outcomes": step_outcomes,
        "fields_filled": sorted(set(fields_filled)),
        "gaps_before": gap_before.get("missing_scoring_fields"),
        "gaps_after": gap_after.get("missing_scoring_fields"),
        "spec_fill_before": gap_before.get("spec_fill_pct"),
        "spec_fill_after": gap_after.get("spec_fill_pct"),
        "scores_before": scores_before,
        "scores_after": {
            "heif_total": fresh_row.get("heif_total"),
            "score_total": fresh_row.get("score_total"),
        },
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }
    _stamp_data_plan(db, slug, plan, execution=execution)

    return {
        "model_slug": slug,
        "name": fresh_row.get("name"),
        "vendor": fresh_row.get("vendor"),
        "plan_summary": plan.get("summary"),
        **execution,
    }


def run_humanoid_gap_engine_for_slug(
    db: Session,
    slug: str,
    *,
    use_llm_scrape: bool = True,
    plan_only: bool = False,
) -> Dict[str, Any]:
    row = db.execute(
        text("""
            SELECT model_slug, name, vendor, status, product_url, specs, sources,
                   heif_total, score_total, last_scraped_at
            FROM humanoid_benchmarks WHERE model_slug = :slug
        """),
        {"slug": slug},
    ).mappings().first()
    if not row:
        return {"model_slug": slug, "error": "not_found"}
    row_dict = dict(row)
    plan = build_humanoid_data_plan(row_dict)
    if plan_only:
        _stamp_data_plan(db, slug, plan)
        return {"plan": plan, "plan_only": True}
    result = execute_humanoid_data_plan(db, row_dict, plan, use_llm_scrape=use_llm_scrape)
    result["plan"] = plan
    return result


def run_humanoid_gap_engine_batch(
    db: Session,
    *,
    limit: int = 25,
    sparse_threshold_pct: float = 85.0,
    use_llm_scrape: bool = True,
    persist_deployment_news: bool = True,
    deployment_query_cap: int = 24,
    plan_only: bool = False,
) -> Dict[str, Any]:
    """Second pass: plan gaps for each robot, find data, rescore."""
    from app.services.humanoid_deployment_news import run_humanoid_deployment_news_review
    from app.services.humanoid_secondary_pass import select_humanoid_repair_candidates

    candidates = select_humanoid_repair_candidates(
        db, limit=limit, sparse_threshold_pct=sparse_threshold_pct,
    )
    results: List[dict] = []
    errors = 0

    for cand in candidates:
        slug = cand.get("model_slug")
        if not slug:
            continue
        try:
            results.append(
                run_humanoid_gap_engine_for_slug(
                    db, slug, use_llm_scrape=use_llm_scrape, plan_only=plan_only,
                )
            )
        except Exception as exc:
            errors += 1
            db.rollback()
            logger.warning("Gap engine failed %s: %s", slug, exc)
            results.append({"model_slug": slug, "error": str(exc)[:200]})

    deployment_result: Dict[str, Any] = {}
    if persist_deployment_news and not plan_only:
        try:
            deployment_result = run_humanoid_deployment_news_review(
                db,
                persist=True,
                max_queries=deployment_query_cap,
                include_chinese=True,
                translate_chinese=True,
            )
            for slug in {r.get("model_slug") for r in results if r.get("model_slug")}:
                rescore_humanoid(db, slug)
        except Exception as exc:
            logger.warning("Deployment news batch after gap engine failed: %s", exc)
            deployment_result = {"error": str(exc)[:200]}

    from app.services.humanoid_spec_gaps import analyze_humanoid_spec_gaps

    gap_summary = analyze_humanoid_spec_gaps(db, sparse_threshold_pct=sparse_threshold_pct)
    improved = [
        r for r in results
        if (r.get("spec_fill_after") or 0) > (r.get("spec_fill_before") or 0)
        or (r.get("scores_after") or {}).get("heif_total", 0) > (r.get("scores_before") or {}).get("heif_total", 0)
    ]

    return {
        "engine": "humanoid_gap_engine",
        "plan_only": plan_only,
        "candidates": len(candidates),
        "processed": len(results),
        "errors": errors,
        "improved_count": len(improved),
        "avg_spec_fill_pct": gap_summary.get("avg_spec_fill_pct"),
        "robots_sparse_specs": gap_summary.get("robots_sparse_specs"),
        "deployment_news": deployment_result,
        "sample": results[:12],
        "top_improvements": sorted(
            improved,
            key=lambda r: (
                (r.get("spec_fill_after") or 0) - (r.get("spec_fill_before") or 0),
                ((r.get("scores_after") or {}).get("heif_total") or 0)
                - ((r.get("scores_before") or {}).get("heif_total") or 0),
            ),
            reverse=True,
        )[:10],
    }
