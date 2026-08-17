#!/usr/bin/env python3
"""Idempotent upsert of Tier-1 / Tier-2 robot catalog hierarchy seeds."""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.enums import assert_commercial_maturity
from app.models.robot_catalog import Manufacturer, RobotConfiguration, RobotFamily, RobotModel

ROOT = Path(__file__).resolve().parents[1]
TIER1 = ROOT / "docs" / "calibration" / "tier1_oem_catalog_v1.json"
TIER2 = ROOT / "docs" / "calibration" / "tier2_oem_stubs_v1.json"


def _uid(db: Session):
    value = uuid.uuid4()
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def upsert_catalog(db: Session, payload: dict) -> dict[str, int]:
    counts = {"manufacturers": 0, "families": 0, "models": 0, "configurations": 0, "updated": 0}
    for mfr in payload.get("manufacturers") or []:
        slug = mfr["slug"]
        row = db.query(Manufacturer).filter(Manufacturer.slug == slug).first()
        if row is None:
            row = Manufacturer(
                id=_uid(db),
                slug=slug,
                name=mfr["name"],
                website=mfr.get("website"),
                country=mfr.get("country"),
                calibration_tier=int(mfr.get("calibration_tier") or payload.get("calibration_tier") or 2),
                notes=mfr.get("notes"),
                external_refs=mfr.get("external_refs") or {},
            )
            db.add(row)
            db.flush()
            counts["manufacturers"] += 1
        else:
            row.name = mfr["name"]
            row.website = mfr.get("website") or row.website
            row.country = mfr.get("country") or row.country
            row.calibration_tier = int(mfr.get("calibration_tier") or row.calibration_tier)
            counts["updated"] += 1

        for fam in mfr.get("families") or []:
            fam_row = (
                db.query(RobotFamily)
                .filter(RobotFamily.manufacturer_id == row.id, RobotFamily.slug == fam["slug"])
                .first()
            )
            if fam_row is None:
                fam_row = RobotFamily(
                    id=_uid(db),
                    manufacturer_id=row.id,
                    slug=fam["slug"],
                    name=fam["name"],
                    description=fam.get("description"),
                    primary_class=fam.get("primary_class"),
                )
                db.add(fam_row)
                db.flush()
                counts["families"] += 1
            else:
                fam_row.name = fam["name"]
                fam_row.primary_class = fam.get("primary_class") or fam_row.primary_class
                counts["updated"] += 1

            for model in fam.get("models") or []:
                maturity = assert_commercial_maturity(model.get("commercial_maturity") or "unknown")
                model_row = db.query(RobotModel).filter(RobotModel.slug == model["slug"]).first()
                if model_row is None:
                    model_row = RobotModel(
                        id=_uid(db),
                        manufacturer_id=row.id,
                        family_id=fam_row.id,
                        slug=model["slug"],
                        name=model["name"],
                        primary_class=model["primary_class"],
                        work_to_map=model.get("work_to_map") or [],
                        calibration_tier=int(model.get("calibration_tier") or row.calibration_tier),
                        commercial_maturity=maturity,
                        product_url=model.get("product_url"),
                        capability_stubs=model.get("capability_stubs") or [],
                        work_envelope_stubs=model.get("work_envelope_stubs") or [],
                        external_refs=model.get("external_refs") or {},
                        availability_geography=model.get("availability_geography"),
                        deployment_evidence=model.get("deployment_evidence"),
                        known_customers=model.get("known_customers"),
                        pricing_model=model.get("pricing_model"),
                        direct_sales=model.get("direct_sales"),
                        distributor_sales=model.get("distributor_sales"),
                        integrator_sales=model.get("integrator_sales"),
                        raas_available=model.get("raas_available"),
                        service_regions=model.get("service_regions"),
                        is_active=True,
                    )
                    db.add(model_row)
                    db.flush()
                    counts["models"] += 1
                else:
                    model_row.name = model["name"]
                    model_row.primary_class = model["primary_class"]
                    model_row.work_to_map = model.get("work_to_map") or model_row.work_to_map
                    model_row.calibration_tier = int(model.get("calibration_tier") or model_row.calibration_tier)
                    model_row.commercial_maturity = maturity
                    model_row.capability_stubs = model.get("capability_stubs") or model_row.capability_stubs
                    model_row.work_envelope_stubs = model.get("work_envelope_stubs") or model_row.work_envelope_stubs
                    model_row.product_url = model.get("product_url") or model_row.product_url
                    counts["updated"] += 1

                for cfg in model.get("configurations") or []:
                    cfg_row = (
                        db.query(RobotConfiguration)
                        .filter(
                            RobotConfiguration.robot_model_id == model_row.id,
                            RobotConfiguration.slug == cfg["slug"],
                        )
                        .first()
                    )
                    if cfg_row is None:
                        cfg_row = RobotConfiguration(
                            id=_uid(db),
                            robot_model_id=model_row.id,
                            slug=cfg["slug"],
                            name=cfg["name"],
                            description=cfg.get("description"),
                            options=cfg.get("options") or {},
                            is_default=bool(cfg.get("is_default")),
                        )
                        db.add(cfg_row)
                        counts["configurations"] += 1
                    else:
                        cfg_row.name = cfg["name"]
                        cfg_row.is_default = bool(cfg.get("is_default"))
                        counts["updated"] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier1-only", action="store_true")
    parser.add_argument("--tier2-only", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        totals = {"manufacturers": 0, "families": 0, "models": 0, "configurations": 0, "updated": 0}
        paths = []
        if not args.tier2_only:
            paths.append(TIER1)
        if not args.tier1_only:
            paths.append(TIER2)
        for path in paths:
            counts = upsert_catalog(db, _load(path))
            for k, v in counts.items():
                totals[k] = totals.get(k, 0) + v
            print(path.name, counts)
        db.commit()
        print("totals", totals)
        print(
            "db",
            {
                "manufacturers": db.query(Manufacturer).count(),
                "tier1_models": db.query(RobotModel).filter(RobotModel.calibration_tier == 1).count(),
                "all_models": db.query(RobotModel).count(),
            },
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
