"""
Humanoid benchmark admin ops — auth via X-Admin-Key or admin Supabase JWT.

POST /api/admin/humanoids/secondary-pass
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.admin_auth import require_admin_jwt_or_key

router = APIRouter(dependencies=[Depends(require_admin_jwt_or_key)])


@router.post("/humanoids/secondary-pass")
def run_humanoid_secondary_pass(
    background_tasks: BackgroundTasks,
    limit: int = Query(40, ge=1, le=80),
    sparse_pct: float = Query(85.0, ge=0.0, le=100.0),
    use_llm: bool = Query(True),
    persist_news: bool = Query(True),
    news_queries: int = Query(24, ge=4, le=60),
):
    from app.services.humanoid_secondary_pass import (
        run_humanoid_secondary_pass_batch_and_refresh_caches,
    )

    background_tasks.add_task(
        run_humanoid_secondary_pass_batch_and_refresh_caches,
        limit=limit,
        sparse_threshold_pct=sparse_pct,
        use_llm_scrape=use_llm,
        persist_deployment_news=persist_news,
        deployment_query_cap=news_queries,
    )
    return {
        "status": "started",
        "limit": limit,
        "sparse_pct": sparse_pct,
        "use_llm": use_llm,
        "persist_news": persist_news,
        "news_queries": news_queries,
        "message": (
            f"Humanoid secondary pass processing up to {limit} sparse robots — "
            "spec backfill, news scrape, deployment evidence, capability rank."
        ),
    }
