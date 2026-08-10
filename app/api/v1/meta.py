"""V1 meta / health endpoints (Slice 0)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.deps import require_v1_enabled, v1_robot_intelligence_enabled
from app.api.v1.errors import SCHEMA_VERSION
from app.services.deployment_conversion import (
    CALL_PRIORITIES,
    CONVERSION_STAGES,
    DECISION_DIMENSIONS,
    DISPOSITIONS,
)

router = APIRouter(tags=["v1-meta"])


@router.get("/meta")
def v1_meta(_: None = Depends(require_v1_enabled)):
    """Contract probe for clients and feature-flag verification."""
    return {
        "schema_version": SCHEMA_VERSION,
        "api": "readyforrobots.v1",
        "feature_flag": "V1_ROBOT_INTELLIGENCE",
        "enabled": v1_robot_intelligence_enabled(),
        "truth_stages": list(CONVERSION_STAGES),
        "dispositions": list(DISPOSITIONS),
        "decision_dimensions": sorted(DECISION_DIMENSIONS),
        "call_priorities": sorted(CALL_PRIORITIES),
        "slices": {
            "complete": [
                "0_contract_alignment",
                "1_robot_input_and_verified_profile",
                "sprint0_enums_ontology_golden_skeleton",
                "sprint1_sources_facilities_primitives_truth",
            ],
            "next": "sprint0_finish_job_labeling_RFR008_009",
        },
        "endpoints": [
            "GET /api/v1/meta",
            "GET /api/v1/catalog/summary",
            "GET /api/v1/manufacturers",
            "GET /api/v1/manufacturers/{slug}",
            "GET /api/v1/robot-models",
            "GET /api/v1/robot-models/{slug}",
            "POST /api/v1/robot-analyses",
            "GET /api/v1/robot-analyses/{analysisId}",
            "POST /api/v1/robot-analyses/{analysisId}/confirm",
        ],
    }
