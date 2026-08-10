"""V1 robot market-graph catalog endpoints (vendors / models)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import require_v1_enabled
from app.api.v1.errors import V1HTTPException
from app.database import get_db
from app.models.robot_catalog import Manufacturer, RobotFamily, RobotModel

router = APIRouter(tags=["v1-catalog"])


def _mfr_to_api(row: Manufacturer) -> dict:
    return {
        "id": str(row.id),
        "slug": row.slug,
        "name": row.name,
        "website": row.website,
        "country": row.country,
        "headquarters": row.headquarters,
        "vendor_role": row.vendor_role,
        "vendor_type": row.vendor_type,
        "robot_categories": row.robot_categories or [],
        "primary_industries": row.primary_industries or [],
        "primary_work_types": row.primary_work_types or [],
        "commercial_maturity": row.commercial_maturity,
        "sales_geography": row.sales_geography or [],
        "service_geography": row.service_geography or [],
        "direct_sales": row.direct_sales,
        "distributor_sales": row.distributor_sales,
        "integrator_sales": row.integrator_sales,
        "raas_available": row.raas_available,
        "us_availability": row.us_availability,
        "sales_model": row.sales_model,
        "verification_status": row.verification_status,
        "confidence": float(row.confidence or 0),
        "calibration_tier": row.calibration_tier,
        "known_robot_count": row.known_robot_count,
        "active_model_count": row.active_model_count,
        "source_url": row.source_url,
    }


def _model_to_api(row: RobotModel, *, include_family: bool = False) -> dict:
    payload = {
        "id": str(row.id),
        "slug": row.slug,
        "name": row.name,
        "manufacturer_id": str(row.manufacturer_id),
        "family_id": str(row.family_id),
        "primary_class": row.primary_class,
        "work_to_map": row.work_to_map or [],
        "commercial_maturity": row.commercial_maturity,
        "calibration_tier": row.calibration_tier,
        "product_url": row.product_url,
        "is_active": row.is_active,
        "capability_stubs": row.capability_stubs or [],
        "work_envelope_stubs": row.work_envelope_stubs or [],
    }
    if include_family and row.family_id:
        payload["family_id"] = str(row.family_id)
    return payload


@router.get("/catalog/summary")
def catalog_summary(_: None = Depends(require_v1_enabled), db: Session = Depends(get_db)):
    from sqlalchemy import func

    by_role = (
        db.query(Manufacturer.vendor_role, func.count())
        .group_by(Manufacturer.vendor_role)
        .all()
    )
    by_tier = (
        db.query(Manufacturer.calibration_tier, func.count())
        .group_by(Manufacturer.calibration_tier)
        .all()
    )
    return {
        "manufacturers": db.query(Manufacturer).count(),
        "families": db.query(RobotFamily).count(),
        "models": db.query(RobotModel).count(),
        "active_models": db.query(RobotModel).filter(RobotModel.is_active.is_(True)).count(),
        "by_vendor_role": {r or "unknown": n for r, n in by_role},
        "by_calibration_tier": {str(t): n for t, n in by_tier},
    }


@router.get("/manufacturers")
def list_manufacturers(
    _: None = Depends(require_v1_enabled),
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    vendor_role: str | None = Query(default=None, max_length=64),
    calibration_tier: int | None = Query(default=None, ge=1, le=3),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(Manufacturer)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(Manufacturer.name.ilike(like))
    if vendor_role:
        query = query.filter(Manufacturer.vendor_role == vendor_role)
    if calibration_tier is not None:
        query = query.filter(Manufacturer.calibration_tier == calibration_tier)

    rows = query.order_by(Manufacturer.name).all()
    if category:
        rows = [r for r in rows if category in (r.robot_categories or [])]
    total = len(rows)
    page = rows[offset : offset + limit]
    return {"total": total, "limit": limit, "offset": offset, "items": [_mfr_to_api(r) for r in page]}


@router.get("/manufacturers/{slug}")
def get_manufacturer(
    slug: str,
    _: None = Depends(require_v1_enabled),
    db: Session = Depends(get_db),
    include_models: bool = Query(default=True),
):
    row = db.query(Manufacturer).filter(Manufacturer.slug == slug).first()
    if not row:
        raise V1HTTPException(status_code=404, code="not_found", message=f"Manufacturer not found: {slug}")
    payload = _mfr_to_api(row)
    if include_models:
        models = (
            db.query(RobotModel)
            .filter(RobotModel.manufacturer_id == row.id, RobotModel.is_active.is_(True))
            .order_by(RobotModel.name)
            .all()
        )
        payload["models"] = [_model_to_api(m) for m in models]
    return payload


@router.get("/robot-models")
def list_robot_models(
    _: None = Depends(require_v1_enabled),
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, max_length=120),
    primary_class: str | None = Query(default=None, max_length=80),
    manufacturer_slug: str | None = Query(default=None, max_length=120),
    calibration_tier: int | None = Query(default=None, ge=1, le=3),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(RobotModel).filter(RobotModel.is_active.is_(True))
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(RobotModel.name.ilike(like))
    if primary_class:
        query = query.filter(RobotModel.primary_class == primary_class)
    if calibration_tier is not None:
        query = query.filter(RobotModel.calibration_tier == calibration_tier)
    if manufacturer_slug:
        mfr = db.query(Manufacturer).filter(Manufacturer.slug == manufacturer_slug).first()
        if not mfr:
            return {"total": 0, "limit": limit, "offset": offset, "items": []}
        query = query.filter(RobotModel.manufacturer_id == mfr.id)
    total = query.count()
    rows = query.order_by(RobotModel.name).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "items": [_model_to_api(r) for r in rows]}


@router.get("/robot-models/{slug}")
def get_robot_model(
    slug: str,
    _: None = Depends(require_v1_enabled),
    db: Session = Depends(get_db),
):
    row = db.query(RobotModel).filter(RobotModel.slug == slug).first()
    if not row:
        raise V1HTTPException(status_code=404, code="not_found", message=f"Robot model not found: {slug}")
    payload = _model_to_api(row)
    mfr = db.query(Manufacturer).filter(Manufacturer.id == row.manufacturer_id).first()
    if mfr:
        payload["manufacturer"] = {"slug": mfr.slug, "name": mfr.name, "vendor_role": mfr.vendor_role}
    return payload
