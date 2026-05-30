"""
Humanoid spec gap analysis — fields required for HEIF / rule-based scoring.

Used to prioritize scraping, agent assessment, and manual datasheet backfill.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.humanoid_scraper import SEED_ROBOTS
from app.services.humanoid_vendor_catalog import catalog_entries

# (field, heif_dimensions, kind: numeric|bool|enum)
SCORING_SPEC_FIELDS: List[tuple] = [
    ("top_speed_mps", ("mobility",), "numeric"),
    ("can_climb_stairs", ("mobility",), "bool"),
    ("can_navigate_rough_terrain", ("mobility",), "bool"),
    ("can_run", ("mobility",), "bool"),
    ("payload_kg", ("manipulation",), "numeric"),
    ("finger_count", ("manipulation",), "numeric"),
    ("has_dexterous_hands", ("manipulation",), "bool"),
    ("autonomy_level", ("cognition",), "enum"),
    ("commercial_deployments", ("cognition", "data_pipeline", "production"), "numeric"),
    ("has_sdk", ("cognition", "data_pipeline", "production"), "bool"),
    ("has_api", ("cognition", "data_pipeline", "production"), "bool"),
    ("has_estop", ("safety",), "bool"),
    ("safety_certified", ("safety",), "bool"),
    ("force_limited_joints", ("safety",), "bool"),
    ("collision_force_n", ("safety",), "numeric"),
    ("battery_life_h", ("endurance",), "numeric"),
    ("charge_time_h", ("endurance",), "numeric"),
    ("hot_swap_battery", ("endurance",), "bool"),
    ("price_usd", ("production",), "numeric"),
    ("has_support_sla", ("production",), "bool"),
]

METADATA_SPEC_FIELDS: List[tuple] = [
    ("height_cm", "numeric"),
    ("weight_kg", "numeric"),
]

ROW_FIELDS = ("product_url", "sources", "last_scraped_at")

SEED_SPECS_BY_SLUG: Dict[str, dict] = {
    r["model_slug"]: dict(r.get("specs") or {}) for r in SEED_ROBOTS
}


@dataclass(frozen=True)
class FieldDef:
    name: str
    dimensions: tuple
    kind: str


def scoring_field_defs() -> List[FieldDef]:
    return [FieldDef(name=f, dimensions=dims, kind=kind) for f, dims, kind in SCORING_SPEC_FIELDS]


def spec_field_missing(spec: dict, field: str, kind: str) -> bool:
    if field not in spec:
        return True
    val = spec.get(field)
    if val is None:
        return True
    if kind == "enum" and str(val).strip() == "":
        return True
    return False


def analyze_robot_gaps(row: dict) -> dict:
    """Return missing fields for one humanoid_benchmarks row."""
    spec = row.get("specs") or {}
    missing_scoring = [
        f.name
        for f in scoring_field_defs()
        if spec_field_missing(spec, f.name, f.kind)
    ]
    missing_metadata = [
        name
        for name, kind in METADATA_SPEC_FIELDS
        if spec_field_missing(spec, name, kind)
    ]
    missing_row = []
    if not row.get("product_url"):
        missing_row.append("product_url")
    sources = row.get("sources") or []
    if not sources:
        missing_row.append("sources")
    if not row.get("last_scraped_at"):
        missing_row.append("last_scraped_at")

    total = len(SCORING_SPEC_FIELDS)
    present = total - len(missing_scoring)
    seed_available = row.get("model_slug") in SEED_SPECS_BY_SLUG

    return {
        "model_slug": row.get("model_slug"),
        "name": row.get("name"),
        "vendor": row.get("vendor"),
        "status": row.get("status"),
        "spec_fill_pct": round(100 * present / total, 1) if total else 0.0,
        "missing_scoring_fields": missing_scoring,
        "missing_metadata_fields": missing_metadata,
        "missing_row_fields": missing_row,
        "seed_specs_available": seed_available,
        "heif_total": row.get("heif_total"),
        "score_total": row.get("score_total"),
    }


def analyze_humanoid_spec_gaps(
    db: Session,
    *,
    sparse_threshold_pct: float = 80.0,
    slug: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Summarize missing scoring fields across humanoid_benchmarks.

    ``sparse_threshold_pct``: robots below this spec fill % are listed in ``sparse_robots``.
    """
    query = """
        SELECT model_slug, name, vendor, status, product_url, specs, sources,
               heif_total, score_total, last_scraped_at
        FROM humanoid_benchmarks
    """
    params: dict = {}
    if slug:
        query += " WHERE model_slug = :slug"
        params["slug"] = slug
    query += " ORDER BY vendor, name"

    rows = db.execute(text(query), params).mappings().all()
    catalog_slugs = {e["model_slug"] for e in catalog_entries()}
    db_slugs = {r["model_slug"] for r in rows}

    robot_gaps = [analyze_robot_gaps(dict(r)) for r in rows]
    total = len(robot_gaps)

    field_stats: List[dict] = []
    for field_def in scoring_field_defs():
        missing_count = sum(1 for g in robot_gaps if field_def.name in g["missing_scoring_fields"])
        field_stats.append({
            "field": field_def.name,
            "dimensions": list(field_def.dimensions),
            "kind": field_def.kind,
            "present": total - missing_count,
            "missing": missing_count,
            "fill_pct": round(100 * (total - missing_count) / total, 1) if total else 0.0,
        })
    field_stats.sort(key=lambda x: x["fill_pct"])

    dim_stats: List[dict] = []
    all_dims: Set[str] = set()
    for field_def in scoring_field_defs():
        all_dims.update(field_def.dimensions)
    for dim in sorted(all_dims):
        fields = [f.name for f in scoring_field_defs() if dim in f.dimensions]
        robots_missing = sum(
            1 for g in robot_gaps if any(f in g["missing_scoring_fields"] for f in fields)
        )
        dim_stats.append({
            "dimension": dim,
            "fields": fields,
            "robots_missing_any": robots_missing,
            "robots_complete": total - robots_missing,
        })

    sparse = [g for g in robot_gaps if g["spec_fill_pct"] < sparse_threshold_pct]
    sparse.sort(key=lambda g: (g["spec_fill_pct"], g["name"] or ""))

    return {
        "total_robots": total,
        "catalog_not_in_db": sorted(catalog_slugs - db_slugs),
        "catalog_not_in_db_count": len(catalog_slugs - db_slugs),
        "avg_spec_fill_pct": round(
            sum(g["spec_fill_pct"] for g in robot_gaps) / total, 1
        ) if total else 0.0,
        "robots_fully_scored_specs": sum(1 for g in robot_gaps if g["spec_fill_pct"] >= 100),
        "robots_sparse_specs": len(sparse),
        "sparse_threshold_pct": sparse_threshold_pct,
        "field_coverage": field_stats,
        "dimension_coverage": dim_stats,
        "sparse_robots": sparse,
        "robots": robot_gaps if slug else None,
        "seed_specs_available_count": sum(1 for g in robot_gaps if g["seed_specs_available"]),
        "scoring_spec_fields": [f.name for f in scoring_field_defs()],
        "metadata_spec_fields": [f[0] for f in METADATA_SPEC_FIELDS],
    }
