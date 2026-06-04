"""
Lead pipeline admin ops — auth via X-Admin-Key or admin Supabase JWT.

POST /api/admin/leads/refresh-inference
POST /api/admin/leads/enrich-agent
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.admin_auth import require_admin_jwt_or_key

router = APIRouter(dependencies=[Depends(require_admin_jwt_or_key)])


@router.post("/leads/refresh-inference")
def refresh_pipeline_lead_inference(
    background_tasks: BackgroundTasks,
    limit: int = Query(300, ge=1, le=500),
):
    from app.services.pipeline_inference_batch import run_pipeline_inference_batch_and_refresh_caches

    background_tasks.add_task(run_pipeline_inference_batch_and_refresh_caches, limit=limit)
    return {
        "status": "started",
        "limit": limit,
        "message": (
            f"Refreshing inference for up to {limit} top pipeline companies in the "
            "background, then rebuilding public caches."
        ),
    }


@router.post("/leads/enrich-agent")
def enrich_pipeline_leads_with_agent(
    background_tasks: BackgroundTasks,
    limit: int = Query(300, ge=1, le=500),
    use_llm: bool = Query(True),
):
    from app.services.lead_enrichment_agent import run_sales_leads_enrichment_batch_and_refresh_caches

    background_tasks.add_task(
        run_sales_leads_enrichment_batch_and_refresh_caches,
        limit=limit,
        use_llm=use_llm,
    )
    return {
        "status": "started",
        "limit": limit,
        "use_llm": use_llm,
        "message": (
            f"Enrichment agent processing up to {limit} leads — inference refresh, "
            "rich data extraction, and learned ontology update."
        ),
    }
