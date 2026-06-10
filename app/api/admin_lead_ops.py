"""
Lead pipeline admin ops — auth via X-Admin-Key or admin Supabase JWT.

POST /api/admin/leads/refresh-inference
POST /api/admin/leads/enrich-agent
POST /api/admin/leads/secondary-pass
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


@router.post("/leads/secondary-pass")
def run_lead_secondary_pass(
    background_tasks: BackgroundTasks,
    limit: int = Query(120, ge=1, le=300),
    min_score: float = Query(15.0, ge=0.0, le=100.0),
    use_llm: bool = Query(True),
    rescore: bool = Query(True),
):
    from app.services.lead_secondary_pass import run_secondary_pass_batch_and_refresh_caches

    background_tasks.add_task(
        run_secondary_pass_batch_and_refresh_caches,
        limit=limit,
        min_score=min_score,
        use_llm=use_llm,
        rescore=rescore,
    )
    return {
        "status": "started",
        "limit": limit,
        "min_score": min_score,
        "use_llm": use_llm,
        "rescore": rescore,
        "message": (
            f"Secondary rescue pass processing up to {limit} gap-ranked leads — "
            "website, contacts (Apollo + role inbox), CRM, inference, rectification."
        ),
    }
