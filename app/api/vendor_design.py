"""Vendor deployment design API — ROI validation + workflow layout models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.pipeline_cache_store import cache_read, cache_write
from app.services.vendor_deployment_design import (
    INDUSTRY_BENCHMARKS,
    RoiInputs,
    default_workflow_layout,
    new_share_id,
    summarize_workflow_impact,
    validate_and_compute_roi,
)

router = APIRouter()

_CACHE_PREFIX = "vendor-design:v1:"


class RoiComputeIn(BaseModel):
    robot_unit_cost: float = Field(..., gt=0)
    robot_count: int = Field(1, ge=1, le=500)
    deployment_cost: float = Field(0, ge=0)
    annual_maintenance_pct: float = Field(10, ge=0, le=50)
    labor_mode: str = "fte"
    fte_count_replaced: float = Field(0, ge=0)
    fte_fully_loaded_cost: float = Field(0, ge=0)
    hours_per_day: float = Field(0, ge=0)
    hourly_wage: float = Field(0, ge=0)
    labor_replaced_pct: float = Field(100, ge=0, le=100)
    industry: str = ""
    shift_days_per_year: int = Field(365, ge=1, le=366)
    buyer_stated_payback_months: Optional[float] = Field(None, ge=0)
    buyer_stated_annual_savings: Optional[float] = Field(None, ge=0)


class WorkflowLayoutIn(BaseModel):
    width: int = 720
    height: int = 320
    zones: list[dict[str, Any]] = Field(default_factory=list)
    robots: list[dict[str, Any]] = Field(default_factory=list)
    flows: list[dict[str, Any]] = Field(default_factory=list)


class DeploymentModelIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    vendor_company: str = Field("", max_length=200)
    buyer_company: str = Field("", max_length=200)
    industry: str = ""
    robot_product: str = ""
    roi: RoiComputeIn
    layout: Optional[WorkflowLayoutIn] = None
    notes: str = ""


def _roi_to_dict(result) -> dict[str, Any]:
    return {
        "annual_labor_baseline": result.annual_labor_baseline,
        "annual_labor_replaced": result.annual_labor_replaced,
        "annual_maintenance": result.annual_maintenance,
        "annual_net_savings": result.annual_net_savings,
        "total_capex": result.total_capex,
        "payback_months": result.payback_months,
        "roi_year_1_pct": result.roi_year_1_pct,
        "roi_year_3_pct": result.roi_year_3_pct,
        "net_savings_3yr": result.net_savings_3yr,
        "corrected_from_buyer": result.corrected_from_buyer,
        "benchmark": result.benchmark,
        "issues": [
            {
                "code": i.code,
                "severity": i.severity,
                "message": i.message,
                "suggestion": i.suggestion,
            }
            for i in result.issues
        ],
    }


def _compute_from_payload(roi: RoiComputeIn):
    return validate_and_compute_roi(
        RoiInputs(
            robot_unit_cost=roi.robot_unit_cost,
            robot_count=roi.robot_count,
            deployment_cost=roi.deployment_cost,
            annual_maintenance_pct=roi.annual_maintenance_pct,
            labor_mode=roi.labor_mode,
            fte_count_replaced=roi.fte_count_replaced,
            fte_fully_loaded_cost=roi.fte_fully_loaded_cost,
            hours_per_day=roi.hours_per_day,
            hourly_wage=roi.hourly_wage,
            labor_replaced_pct=roi.labor_replaced_pct,
            industry=roi.industry,
            shift_days_per_year=roi.shift_days_per_year,
            buyer_stated_payback_months=roi.buyer_stated_payback_months,
            buyer_stated_annual_savings=roi.buyer_stated_annual_savings,
        )
    )


@router.get("/benchmarks")
def list_benchmarks():
    return {"industries": INDUSTRY_BENCHMARKS}


@router.get("/layout-template")
def layout_template(industry: str = ""):
    return default_workflow_layout(industry)


@router.post("/compute-roi")
def compute_roi(body: RoiComputeIn):
    result = _compute_from_payload(body)
    return _roi_to_dict(result)


@router.post("/models")
def save_deployment_model(body: DeploymentModelIn, db: Session = Depends(get_db)):
    roi_result = _compute_from_payload(body.roi)
    layout = (
        body.layout.model_dump() if body.layout else default_workflow_layout(body.industry)
    )
    share_id = new_share_id()
    model_id = str(uuid.uuid4())
    payload = {
        "id": model_id,
        "share_id": share_id,
        "title": body.title.strip(),
        "vendor_company": body.vendor_company.strip(),
        "buyer_company": body.buyer_company.strip(),
        "industry": body.industry.strip(),
        "robot_product": body.robot_product.strip(),
        "notes": body.notes.strip(),
        "roi_inputs": body.roi.model_dump(),
        "roi": _roi_to_dict(roi_result),
        "layout": layout,
        "workflow_impact": summarize_workflow_impact(layout),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    cache_write(db, f"{_CACHE_PREFIX}{share_id}", payload, ttl_minutes=60 * 24 * 90)
    return {
        "id": model_id,
        "share_id": share_id,
        "share_url": f"/design/{share_id}",
        "roi": payload["roi"],
        "workflow_impact": payload["workflow_impact"],
    }


@router.get("/models/{share_id}")
def get_deployment_model(share_id: str, db: Session = Depends(get_db)):
    data = cache_read(db, f"{_CACHE_PREFIX}{share_id}", stale_ok=True)
    if not isinstance(data, dict):
        raise HTTPException(status_code=404, detail="Design not found")
    return data
