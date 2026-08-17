#!/usr/bin/env python3
"""Idempotent import of ReadyForRobots_Robot_Vendor_Seed_v1 into manufacturers + models.

Usage:
  PYTHONPATH=. python scripts/import_robot_vendor_seed.py --dry-run
  PYTHONPATH=. python scripts/import_robot_vendor_seed.py
  PYTHONPATH=. python scripts/import_robot_vendor_seed.py --vendors-only
"""
from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.enums import assert_commercial_maturity, vendor_roles, vendor_types
from app.models.robot_catalog import Manufacturer, RobotConfiguration, RobotFamily, RobotModel

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "docs" / "calibration" / "robot_vendor_seed_v1.json"
TIER1 = ROOT / "docs" / "calibration" / "tier1_oem_catalog_v1.json"
TIER2 = ROOT / "docs" / "calibration" / "tier2_oem_stubs_v1.json"

# Seed display names → existing catalog manufacturer slugs / alternate names
VENDOR_ALIASES: dict[str, str] = {
    "mir (mobile industrial robots)": "mir",
    "mobile industrial robots (mir)": "mir",
    "otto motors": "otto-motors",
    "geekplus": "geekplus",
    "geek+": "geekplus",
    "figure ai": "figure",
    "figure": "figure",
    "boston dynamics spot": "boston-dynamics",
    "boston dynamics": "boston-dynamics",
    "universal robots": "universal-robots",
    "abb robotics": "abb",
    "fanuc": "fanuc",
    "kuka": "kuka",
    "yaskawa motoman": "yaskawa",
    "doosan robotics": "doosan-robotics",
    "agility robotics": "agility-robotics",
    "apptronik": "apptronik",
    "tesla optimus": "tesla",
    "fox robotics": "fox-robotics",
    "third wave automation": "third-wave-automation",
    "vecna robotics": "vecna-robotics",
    "fetch robotics / zebra": "fetch-robotics",
    "locus robotics": "locus-robotics",
    "greyorange": "greyorange",
    "invia robotics": "invia-robotics",
    "autoGuide / Dematic": "autoguide",
    "autoguide / dematic": "autoguide",
}


def _uid(db: Session):
    value = uuid.uuid4()
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return slug[:120] or f"vendor-{uuid.uuid4().hex[:8]}"


def _host(url: str | None) -> str | None:
    if not url:
        return None
    try:
        host = urlparse(url if "://" in url else f"https://{url}").netloc.lower()
        return host[4:] if host.startswith("www.") else host or None
    except Exception:
        return None


def _split_list(value: str | list | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [p.strip() for p in re.split(r"[;,|/]", str(value)) if p.strip()]


def _parse_sales_flags(sales_model: str | None) -> dict[str, bool | None]:
    s = (sales_model or "").lower()
    if not s:
        return {
            "direct_sales": None,
            "distributor_sales": None,
            "integrator_sales": None,
            "raas_available": None,
        }
    return {
        "direct_sales": "direct" in s,
        "distributor_sales": "distributor" in s or "channel" in s,
        "integrator_sales": "integrator" in s or "si" in s.split("+"),
        "raas_available": "raas" in s or "rental" in s or "as-a-service" in s,
    }


def _tier_slug_index() -> dict[str, str]:
    """normalized name / alias → preferred slug from tier catalogs."""
    out: dict[str, str] = {}
    for path in (TIER1, TIER2):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for m in data.get("manufacturers") or []:
            out[_norm_name(m["name"])] = m["slug"]
            out[m["slug"].replace("-", "")] = m["slug"]
    for alias, slug in VENDOR_ALIASES.items():
        out[_norm_name(alias)] = slug
    return out


def _build_lookup(db: Session) -> tuple[dict[str, Manufacturer], dict[str, Manufacturer], dict[str, Manufacturer]]:
    by_slug: dict[str, Manufacturer] = {}
    by_name: dict[str, Manufacturer] = {}
    by_host: dict[str, Manufacturer] = {}
    for row in db.query(Manufacturer).all():
        by_slug[row.slug] = row
        by_name[_norm_name(row.name)] = row
        host = _host(row.website)
        if host:
            by_host[host] = row
    return by_slug, by_name, by_host


def _resolve_manufacturer(
    db: Session,
    *,
    company_name: str,
    website: str | None,
    preferred_slugs: dict[str, str],
    by_slug: dict[str, Manufacturer],
    by_name: dict[str, Manufacturer],
    by_host: dict[str, Manufacturer],
) -> tuple[Manufacturer | None, str]:
    nkey = _norm_name(company_name)
    alias_slug = preferred_slugs.get(nkey) or VENDOR_ALIASES.get(company_name.lower())
    if alias_slug and alias_slug in by_slug:
        return by_slug[alias_slug], alias_slug
    if nkey in by_name:
        return by_name[nkey], by_name[nkey].slug
    slug = alias_slug or _slugify(company_name)
    if slug in by_slug:
        return by_slug[slug], slug
    # Host match only when existing name is a near-alias of the seed name
    host = _host(website)
    if host and host in by_host:
        existing = by_host[host]
        en = _norm_name(existing.name)
        if en in nkey or nkey in en or preferred_slugs.get(nkey) == existing.slug:
            return existing, existing.slug
    return None, slug


def upsert_vendors(db: Session, vendors: list[dict], *, dry_run: bool) -> dict[str, int]:
    preferred = _tier_slug_index()
    by_slug, by_name, by_host = _build_lookup(db)
    counts = {"created": 0, "updated": 0, "skipped": 0}
    roles = vendor_roles()
    types = vendor_types()

    for v in vendors:
        name = (v.get("company_name") or "").strip()
        if not name:
            counts["skipped"] += 1
            continue
        row, slug = _resolve_manufacturer(
            db,
            company_name=name,
            website=v.get("website"),
            preferred_slugs=preferred,
            by_slug=by_slug,
            by_name=by_name,
            by_host=by_host,
        )
        role = v.get("vendor_role") or "robot_oem"
        if role not in roles:
            role = "robot_oem"
        vtype = v.get("vendor_type") or "oem"
        if vtype not in types:
            vtype = "oem"
        maturity = assert_commercial_maturity(v.get("commercial_maturity") or "unknown")
        sales = _parse_sales_flags(v.get("sales_model"))
        cats = [v["robot_category"]] if v.get("robot_category") else []
        industries = _split_list(v.get("industries"))
        work_types = _split_list(v.get("work_type"))
        verification = v.get("verification") or "unverified"
        if verification == "curated":
            verification = "curated"
        confidence = 0.7 if verification in {"curated", "verified"} else 0.4
        notes = v.get("notes") or None
        source_url = v.get("website")
        external = {
            "seed_dataset": "robot_vendor_seed_v1",
            "seed_source": v.get("source"),
            "primary_robots": v.get("primary_robots"),
        }

        if row is None:
            counts["created"] += 1
            if dry_run:
                continue
            row = Manufacturer(
                id=_uid(db),
                slug=slug,
                name=name,
                website=v.get("website"),
                country=v.get("country"),
                vendor_role=role,
                vendor_type=vtype,
                robot_categories=cats,
                primary_industries=industries,
                primary_work_types=work_types,
                commercial_maturity=maturity,
                sales_geography=["US"] if (v.get("us_availability") or "").lower() in {"yes", "y", "true"} else [],
                service_geography=["US"] if (v.get("us_availability") or "").lower() in {"yes", "y", "true"} else [],
                direct_sales=sales["direct_sales"],
                distributor_sales=sales["distributor_sales"],
                integrator_sales=sales["integrator_sales"],
                raas_available=sales["raas_available"],
                source_url=source_url,
                source_date=None,
                verification_status=verification,
                confidence=confidence,
                us_availability=v.get("us_availability"),
                sales_model=v.get("sales_model"),
                calibration_tier=3,  # market-graph seed (not Tier-1 calibration)
                notes=notes,
                external_refs=external,
            )
            db.add(row)
            db.flush()
            by_slug[slug] = row
            by_name[_norm_name(name)] = row
            host = _host(row.website)
            if host:
                by_host[host] = row
        else:
            counts["updated"] += 1
            if dry_run:
                continue
            row.name = name if len(name) >= len(row.name or "") else row.name
            row.website = v.get("website") or row.website
            row.country = v.get("country") or row.country
            row.vendor_role = role
            row.vendor_type = vtype
            # merge categories
            existing_cats = list(row.robot_categories or [])
            for c in cats:
                if c not in existing_cats:
                    existing_cats.append(c)
            row.robot_categories = existing_cats
            if industries:
                row.primary_industries = industries
            if work_types:
                row.primary_work_types = work_types
            if maturity != "unknown" or row.commercial_maturity == "unknown":
                row.commercial_maturity = maturity
            for k, val in sales.items():
                if val is not None:
                    setattr(row, k, val)
            row.us_availability = v.get("us_availability") or row.us_availability
            row.sales_model = v.get("sales_model") or row.sales_model
            row.verification_status = verification or row.verification_status
            row.confidence = max(float(row.confidence or 0), confidence)
            row.source_url = source_url or row.source_url
            if notes:
                row.notes = notes
            refs = dict(row.external_refs or {})
            refs.update(external)
            row.external_refs = refs
            # never demote tier-1/2 calibration rows
            if row.calibration_tier is None or row.calibration_tier > 3:
                row.calibration_tier = 3

    return counts


def upsert_models(db: Session, models: list[dict], *, dry_run: bool) -> dict[str, int]:
    preferred = _tier_slug_index()
    by_slug, by_name, by_host = _build_lookup(db)
    counts = {"created": 0, "updated": 0, "skipped_no_vendor": 0, "skipped_tier1": 0}

    for m in models:
        # Prefer not to overwrite deep Tier-1 catalog rows via thin primary_robots stubs
        if m.get("source") == "tier1_oem_catalog_v1" or int(m.get("calibration_tier") or 99) == 1:
            existing = db.query(RobotModel).filter(RobotModel.slug == m.get("model_slug")).first()
            if existing:
                counts["skipped_tier1"] += 1
                continue

        vendor_name = (m.get("vendor_name") or "").strip()
        row, _slug = _resolve_manufacturer(
            db,
            company_name=vendor_name,
            website=None,
            preferred_slugs=preferred,
            by_slug=by_slug,
            by_name=by_name,
            by_host=by_host,
        )
        if row is None:
            # try alias-only slug presence
            counts["skipped_no_vendor"] += 1
            continue

        model_slug = (m.get("model_slug") or _slugify(f"{vendor_name}-{m.get('model_name')}"))[:160]
        family_name = (m.get("family") or m.get("model_name") or "Default").strip()
        family_slug = _slugify(f"{row.slug}-{family_name}")[:160]
        primary_class = m.get("primary_class") or "unknown"
        maturity = assert_commercial_maturity(m.get("commercial_maturity") or "unknown")
        work = _split_list(m.get("work_to_map"))
        tier = int(m.get("calibration_tier") or 3)
        if tier < 1:
            tier = 3

        fam = (
            db.query(RobotFamily)
            .filter(RobotFamily.manufacturer_id == row.id, RobotFamily.slug == family_slug)
            .first()
        )
        if fam is None:
            # also match by name under manufacturer
            fam = (
                db.query(RobotFamily)
                .filter(RobotFamily.manufacturer_id == row.id, RobotFamily.name == family_name)
                .first()
            )
        if fam is None:
            if not dry_run:
                fam = RobotFamily(
                    id=_uid(db),
                    manufacturer_id=row.id,
                    slug=family_slug,
                    name=family_name,
                    primary_class=primary_class,
                )
                db.add(fam)
                db.flush()
            else:
                counts["created"] += 1
                continue

        model_row = db.query(RobotModel).filter(RobotModel.slug == model_slug).first()
        if model_row is None:
            counts["created"] += 1
            if dry_run:
                continue
            model_row = RobotModel(
                id=_uid(db),
                manufacturer_id=row.id,
                family_id=fam.id,
                slug=model_slug,
                name=m.get("model_name") or model_slug,
                primary_class=primary_class,
                work_to_map=work,
                calibration_tier=tier,
                commercial_maturity=maturity,
                external_refs={"seed_dataset": "robot_vendor_seed_v1", "seed_source": m.get("source")},
                is_active=True,
            )
            db.add(model_row)
            db.flush()
            cfg = RobotConfiguration(
                id=_uid(db),
                robot_model_id=model_row.id,
                slug="default",
                name="Default",
                is_default=True,
                description="Seed stub configuration",
            )
            db.add(cfg)
        else:
            counts["updated"] += 1
            if dry_run:
                continue
            # do not demote tier-1
            if model_row.calibration_tier == 1:
                counts["skipped_tier1"] += 1
                continue
            model_row.name = m.get("model_name") or model_row.name
            model_row.primary_class = primary_class or model_row.primary_class
            if work:
                model_row.work_to_map = work
            model_row.commercial_maturity = maturity
            if model_row.calibration_tier is None or model_row.calibration_tier > tier:
                model_row.calibration_tier = tier

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--vendors-only", action="store_true")
    parser.add_argument("--models-only", action="store_true")
    parser.add_argument("--seed", type=Path, default=SEED)
    args = parser.parse_args()

    data = json.loads(args.seed.read_text(encoding="utf-8"))
    vendors = data.get("vendors") or []
    models = data.get("models") or []
    assert len(vendors) == 500, f"expected 500 vendors, got {len(vendors)}"

    db = SessionLocal()
    try:
        result: dict = {"dry_run": args.dry_run, "seed": str(args.seed)}
        if not args.models_only:
            result["vendors"] = upsert_vendors(db, vendors, dry_run=args.dry_run)
        if not args.vendors_only:
            result["models"] = upsert_models(db, models, dry_run=args.dry_run)
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
        result["db"] = {
            "manufacturers": db.query(Manufacturer).count(),
            "families": db.query(RobotFamily).count(),
            "models": db.query(RobotModel).count(),
            "configurations": db.query(RobotConfiguration).count(),
            "by_tier": {
                1: db.query(Manufacturer).filter(Manufacturer.calibration_tier == 1).count(),
                2: db.query(Manufacturer).filter(Manufacturer.calibration_tier == 2).count(),
                3: db.query(Manufacturer).filter(Manufacturer.calibration_tier == 3).count(),
            },
        }
        print(json.dumps(result, indent=2))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
