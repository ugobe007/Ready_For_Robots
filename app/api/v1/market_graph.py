"""Market graph loop status + snapshot for product/admin surfaces."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.market_graph_loop import (
    get_market_graph_loop_status,
    read_market_graph_snapshot,
    run_market_graph_loop,
)

router = APIRouter(prefix="/market-graph", tags=["v1-market-graph"])


@router.get("/status")
def market_graph_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    snap = read_market_graph_snapshot(db) or {}
    return {
        "scheduler": get_market_graph_loop_status(),
        "snapshot": {
            "generated_at": snap.get("generated_at"),
            "status": snap.get("status"),
            "tension_count": snap.get("tension_count"),
            "match_count": snap.get("match_count"),
            "refresh_queue_count": snap.get("refresh_queue_count"),
            "demand_sampled": snap.get("demand_sampled"),
            "vendors_sampled": snap.get("vendors_sampled"),
        },
    }


@router.get("/tensions")
def market_graph_tensions(
    limit: int = Query(12, ge=1, le=40),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    snap = read_market_graph_snapshot(db) or {}
    tensions = list(snap.get("tensions") or [])[:limit]
    return {
        "generated_at": snap.get("generated_at"),
        "count": len(tensions),
        "tensions": tensions,
    }


@router.get("/matches")
def market_graph_matches(
    limit: int = Query(20, ge=1, le=80),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    snap = read_market_graph_snapshot(db) or {}
    matches = list(snap.get("matches") or [])[:limit]
    return {
        "generated_at": snap.get("generated_at"),
        "count": len(matches),
        "matches": matches,
    }


@router.post("/run")
def market_graph_run(
    persist: bool = Query(True),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Manual trigger (admin/ops). Scheduler also runs this on the worker."""
    result = run_market_graph_loop(db, persist=persist)
    return {"ok": result.get("status") in {"completed", "skipped"}, "result": result}
