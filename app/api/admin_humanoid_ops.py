"""
Humanoid benchmark admin ops — auth via X-Admin-Key or admin Supabase JWT.

POST /api/admin/humanoids/secondary-pass
POST /api/admin/secondary-pipeline
"""
from fastapi import APIRouter, Depends, Query

from app.admin_auth import require_admin_jwt_or_key

router = APIRouter(dependencies=[Depends(require_admin_jwt_or_key)])


@router.post("/humanoids/secondary-pass")
def run_humanoid_secondary_pass(
    limit: int = Query(40, ge=1, le=80),
    sparse_pct: float = Query(85.0, ge=0.0, le=100.0),
    use_llm: bool = Query(True),
    persist_news: bool = Query(True),
    news_queries: int = Query(24, ge=4, le=60),
):
    from app.services.secondary_pass_runner import (
        get_secondary_pass_status,
        run_humanoids_secondary_pass_sync,
        start_secondary_job_in_thread,
    )

    result = start_secondary_job_in_thread(
        run_humanoids_secondary_pass_sync,
        job_kind="humanoids",
        limit=limit,
        sparse_threshold_pct=sparse_pct,
        use_llm_scrape=use_llm,
        persist_deployment_news=persist_news,
        deployment_query_cap=news_queries,
    )
    return {
        **result,
        "limit": limit,
        "sparse_pct": sparse_pct,
        "use_llm": use_llm,
        "persist_news": persist_news,
        "news_queries": news_queries,
        "message": (
            f"Humanoid secondary pass processing up to {limit} sparse robots — "
            "spec backfill, news scrape, deployment evidence, capability rank."
        ),
        "status_url": "/api/scraper/secondary-pass/status",
        "current": get_secondary_pass_status(),
    }


@router.post("/secondary-pipeline")
def run_full_secondary_pipeline():
    """Run leads then humanoids sequentially (recommended for manual triggers)."""
    from app.services.secondary_pass_runner import (
        get_secondary_pass_status,
        run_full_secondary_pipeline_sync,
        start_secondary_job_in_thread,
    )

    result = start_secondary_job_in_thread(
        run_full_secondary_pipeline_sync,
        job_kind="full",
    )
    return {
        **result,
        "message": "Full secondary pipeline started (leads → humanoids, serialized).",
        "status_url": "/api/scraper/secondary-pass/status",
        "current": get_secondary_pass_status(),
    }
