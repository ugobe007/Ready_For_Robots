"""V1 HTTP surface — contract alignment (Slice 0).

Feature-flagged behind V1_ROBOT_INTELLIGENCE. Domain endpoints land in later slices;
this package owns the shared envelope, meta route, and mount point.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.meta import router as meta_router
from app.api.v1.robot_analyses import router as robot_analyses_router
from app.api.v1.catalog import router as catalog_router

router = APIRouter()
router.include_router(meta_router)
router.include_router(robot_analyses_router)
router.include_router(catalog_router)
