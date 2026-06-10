"""
Backfill humanoid_benchmarks from SEED_ROBOTS + curated catalog specs.

Fixes sparse HEIF rows (0.2 manipulation, 0 safety) when discovery inserted
catalog robots without full datasheet fields.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.humanoid_ai_stack import get_ai_stack, scoring_specs, specs_for_storage
from app.services.humanoid_scraper import SEED_ROBOTS, compute_scores, upsert_humanoid_robot
from app.services.humanoid_spec_gaps import SEED_SPECS_BY_SLUG
from app.services.humanoid_vendor_catalog import catalog_entries

logger = logging.getLogger(__name__)

# Largest vendors — always present with full seed specs when available
PRIORITY_SLUGS = (
    "unitree-g1",
    "unitree-h1",
    "unitree-r1",
    "figure-02",
    "figure-01",
    "figure-03",
    "agility-digit",
    "agility-digit-2",
    "boston-dynamics-atlas",
    "apptronik-apollo",
    "tesla-optimus-gen1",
    "tesla-optimus-gen2",
)

_CATALOG_SPECS_BY_SLUG: Dict[str, dict] = {
    e["model_slug"]: dict(e.get("specs") or {})
    for e in catalog_entries()
    if e.get("model_slug") and e.get("specs")
}


def _merge_specs(existing: dict, *layers: dict) -> dict:
    merged = dict(existing or {})
    for layer in layers:
        for key, val in (layer or {}).items():
            if val is None:
                continue
            cur = merged.get(key)
            if cur is None or cur == "" or cur == 0:
                merged[key] = val
            elif key not in merged:
                merged[key] = val
    return merged


def ensure_priority_humanoids(db: Session) -> dict:
    """Upsert flagship robots (Unitree G1/H1, etc.) from SEED_ROBOTS."""
    by_slug = {r["model_slug"]: r for r in SEED_ROBOTS}
    stats = {"upserted": 0, "skipped": 0, "missing_seed": []}
    for slug in PRIORITY_SLUGS:
        robot = by_slug.get(slug)
        if not robot:
            stats["missing_seed"].append(slug)
            continue
        specs = specs_for_storage(robot["specs"], slug, robot.get("ai_stack"))
        scores = compute_scores(
            scoring_specs(specs),
            status=robot["status"],
            vendor=robot["vendor"],
        )
        result = upsert_humanoid_robot(
            db,
            {
                **robot,
                "specs": specs,
                "scores": scores,
                "evidence_summary": "Priority seed backfill",
            },
            source="seed_backfill",
            commit=True,
        )
        if result == "skipped":
            stats["skipped"] += 1
        else:
            stats["upserted"] += 1
    return stats


def backfill_humanoid_specs(db: Session, *, sparse_heif_below: float = 1.2) -> dict:
    """
    Merge seed + catalog specs into DB rows and recompute scores.

    Targets rows with empty/partial specs or suspiciously low HEIF totals.
    """
    rows = db.execute(
        text("""
            SELECT id, model_slug, name, vendor, status, specs, heif_total
            FROM humanoid_benchmarks
            ORDER BY id
        """)
    ).mappings().all()

    updated = 0
    skipped = 0
    now = datetime.now(timezone.utc)

    for row in rows:
        slug = row["model_slug"]
        existing_specs = dict(row["specs"] or {})
        seed_specs = SEED_SPECS_BY_SLUG.get(slug) or {}
        catalog_specs = _CATALOG_SPECS_BY_SLUG.get(slug) or {}
        if not seed_specs and not catalog_specs:
            skipped += 1
            continue

        merged = _merge_specs(existing_specs, catalog_specs, seed_specs)
        merged = specs_for_storage(merged, slug)
        if merged == existing_specs and (row["heif_total"] or 0) >= sparse_heif_below:
            skipped += 1
            continue

        scores = compute_scores(
            scoring_specs(merged),
            status=row["status"] or "research",
            vendor=row["vendor"] or "",
        )
        if (row["heif_total"] or 0) >= sparse_heif_below and scores["heif_total"] <= (row["heif_total"] or 0):
            skipped += 1
            continue

        db.execute(
            text("""
                UPDATE humanoid_benchmarks SET
                    specs = cast(:specs as jsonb),
                    score_mobility = :score_mobility,
                    score_manipulation = :score_manipulation,
                    score_autonomy = :score_autonomy,
                    score_safety = :score_safety,
                    score_endurance = :score_endurance,
                    score_market_readiness = :score_market_readiness,
                    score_total = :score_total,
                    heif_mobility = :heif_mobility,
                    heif_manipulation = :heif_manipulation,
                    heif_cognition = :heif_cognition,
                    heif_safety = :heif_safety,
                    heif_data_pipeline = :heif_data_pipeline,
                    heif_production = :heif_production,
                    heif_total = :heif_total,
                    updated_at = :now
                WHERE model_slug = :slug
            """),
            {
                "specs": json.dumps(merged),
                "slug": slug,
                "now": now,
                **scores,
            },
        )
        updated += 1

    db.commit()
    return {"scanned": len(rows), "updated": updated, "skipped": skipped}


def backfill_sparse_humanoids(
    db: Session,
    *,
    slugs: Optional[List[str]] = None,
    rescore: bool = True,
) -> dict:
    """Backfill seed/catalog specs for specific slugs (secondary-pass rescue)."""
    if not slugs:
        return {"updated": 0, "skipped": 0}

    updated = 0
    skipped = 0
    now = datetime.now(timezone.utc)

    for slug in slugs:
        row = db.execute(
            text("""
                SELECT model_slug, name, vendor, status, specs, heif_total
                FROM humanoid_benchmarks WHERE model_slug = :slug
            """),
            {"slug": slug},
        ).mappings().first()
        if not row:
            skipped += 1
            continue

        existing_specs = dict(row["specs"] or {})
        seed_specs = SEED_SPECS_BY_SLUG.get(slug) or {}
        catalog_specs = _CATALOG_SPECS_BY_SLUG.get(slug) or {}
        if not seed_specs and not catalog_specs:
            skipped += 1
            continue

        merged = _merge_specs(existing_specs, catalog_specs, seed_specs)
        merged = specs_for_storage(merged, slug)
        if merged == existing_specs and not rescore:
            skipped += 1
            continue

        scores = compute_scores(
            scoring_specs(merged),
            status=row["status"] or "research",
            vendor=row["vendor"] or "",
        )
        db.execute(
            text("""
                UPDATE humanoid_benchmarks SET
                    specs = cast(:specs as jsonb),
                    score_mobility = :score_mobility,
                    score_manipulation = :score_manipulation,
                    score_autonomy = :score_autonomy,
                    score_safety = :score_safety,
                    score_endurance = :score_endurance,
                    score_market_readiness = :score_market_readiness,
                    score_total = :score_total,
                    heif_mobility = :heif_mobility,
                    heif_manipulation = :heif_manipulation,
                    heif_cognition = :heif_cognition,
                    heif_safety = :heif_safety,
                    heif_data_pipeline = :heif_data_pipeline,
                    heif_production = :heif_production,
                    heif_total = :heif_total,
                    updated_at = :now
                WHERE model_slug = :slug
            """),
            {"specs": json.dumps(merged), "slug": slug, "now": now, **scores},
        )
        updated += 1

    db.commit()
    return {"updated": updated, "skipped": skipped, "slugs": slugs}


def repair_humanoid_index(db: Session) -> dict:
    """Cleanup junk rows, ensure Unitree/flagships, backfill specs."""
    from app.services.humanoid_catalog_cleanup import cleanup_humanoid_benchmarks

    cleanup = cleanup_humanoid_benchmarks(db, dry_run=False)
    priority = ensure_priority_humanoids(db)
    backfill = backfill_humanoid_specs(db)
    return {"cleanup": cleanup, "priority": priority, "backfill": backfill}
