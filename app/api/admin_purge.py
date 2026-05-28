"""
Junk-purge admin endpoint.
Registered separately from the main admin router so it can use its own auth
(X-Admin-Key header matching ADMIN_KEY env var) without requiring a Supabase JWT.

POST /api/admin/purge-junk
  Headers:  X-Admin-Key: <value of ADMIN_KEY secret on Fly.io>
  Body:     {"dry_run": true}   — preview only (default, safe)
            {"dry_run": false}  — actually delete junk records
            {"dry_run": false, "limit": 500}  — cap deletions per call
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.admin_auth import check_admin_key as _check_admin_key
from app.database import get_db
from app.models.company import Company

router = APIRouter()


class PurgeJunkPayload(BaseModel):
    dry_run: bool = True          # safe default: preview only
    limit: Optional[int] = None   # safety cap on how many to delete at once


class DeleteByIdsPayload(BaseModel):
    company_ids: List[int]
    dry_run: bool = True


@router.post("/purge-junk")
def purge_junk(
    payload: PurgeJunkPayload,
    db: Session = Depends(get_db),
    _: None = Depends(_check_admin_key),
):
    """
    Scan all company records; delete those flagged by is_junk().
    dry_run=true  → preview list, no deletes.
    dry_run=false → delete + return summary.
    """
    from app.services.lead_filter import is_junk

    companies = db.query(Company).all()
    junk_found = []
    for c in companies:
        bad, reason = is_junk(c.name)
        if bad:
            junk_found.append({"id": c.id, "name": c.name, "reason": reason})

    if payload.limit:
        junk_found = junk_found[: payload.limit]

    if payload.dry_run:
        return {
            "dry_run": True,
            "junk_count": len(junk_found),
            "total_companies": len(companies),
            "preview": junk_found[:100],
            "message": "Set dry_run=false to delete these records.",
        }

    # Delete — must remove child rows first to satisfy FK constraints
    from sqlalchemy import text
    from app.services.scraper_blocklist import add_bulk_to_blocklist
    ids_to_delete = [r["id"] for r in junk_found]
    names_to_block = [r["name"] for r in junk_found]
    deleted = 0
    for cid in ids_to_delete:
        db.execute(text("DELETE FROM scores  WHERE company_id = :cid"), {"cid": cid})
        db.execute(text("DELETE FROM signals WHERE company_id = :cid"), {"cid": cid})
        db.execute(text("DELETE FROM companies WHERE id = :cid"), {"cid": cid})
        deleted += 1
    db.commit()
    # Blocklist all deleted names so scraper never re-ingests them
    add_bulk_to_blocklist(names_to_block, reason="purge_junk")

    return {
        "dry_run": False,
        "deleted": deleted,
        "total_companies_before": len(companies),
        "remaining": len(companies) - deleted,
        "sample_deleted": [r["name"] for r in junk_found[:30]],
    }


@router.post("/delete-by-ids")
def delete_by_ids(
    payload: DeleteByIdsPayload,
    db: Session = Depends(get_db),
    _: None = Depends(_check_admin_key),
):
    """
    Delete specific company records by ID list.
    dry_run=true  → preview only (shows what would be deleted).
    dry_run=false → permanently delete companies + their signals and scores.
    """
    companies = db.query(Company).filter(Company.id.in_(payload.company_ids)).all()
    found = [{"id": c.id, "name": c.name, "industry": c.industry} for c in companies]

    if payload.dry_run:
        return {"dry_run": True, "found": len(found), "records": found}

    from sqlalchemy import text
    from app.services.scraper_blocklist import add_bulk_to_blocklist
    deleted = 0
    for cid in payload.company_ids:
        db.execute(text("DELETE FROM scores  WHERE company_id = :cid"), {"cid": cid})
        db.execute(text("DELETE FROM signals WHERE company_id = :cid"), {"cid": cid})
        result = db.execute(text("DELETE FROM companies WHERE id = :cid"), {"cid": cid})
        deleted += result.rowcount
    db.commit()
    # Blocklist deleted names to prevent re-ingestion
    add_bulk_to_blocklist([r["name"] for r in found], reason="delete_by_ids")

    return {"dry_run": False, "deleted": deleted, "records": found}


@router.get("/review-queue")
def review_queue(
    db: Session = Depends(get_db),
    _: None = Depends(_check_admin_key),
    limit: int = Query(100, le=500),
):
    """
    Returns leads that are low-confidence and worth human review before appearing on site.
    Criteria: only weak signals (automation_interest / news) AND score < 60.
    These passed is_junk() but may still be article fragments or misclassified records.
    """
    from app.models.signal import Signal
    from app.models.score import Score
    from app.services.lead_filter import is_junk
    from sqlalchemy import func

    # Companies with at least one signal
    sig_counts = (
        db.query(Signal.company_id, func.count(Signal.id).label("n"))
        .group_by(Signal.company_id)
        .subquery()
    )
    # Weak signal types that alone don't confirm a buyer
    WEAK_SIGNALS = {"automation_interest", "news"}

    candidates = (
        db.query(Company)
        .join(sig_counts, Company.id == sig_counts.c.company_id)
        .limit(limit * 5)   # over-fetch; we'll filter below
        .all()
    )

    results = []
    for c in candidates:
        # Skip if already caught by is_junk (purge handles those)
        bad, _ = is_junk(c.name)
        if bad:
            continue
        sigs = db.query(Signal).filter(Signal.company_id == c.id).all()
        sig_types = {s.signal_type for s in sigs}
        # Only flag if ALL signals are weak
        if not sig_types.issubset(WEAK_SIGNALS):
            continue
        score_row = (
            db.query(Score)
            .filter(Score.company_id == c.id)
            .order_by(Score.last_calculated_at.desc())
            .first()
        )
        overall = getattr(score_row, "overall_intent_score", 0.0) if score_row else 0.0
        if overall >= 60:
            continue
        results.append({
            "id": c.id,
            "name": c.name,
            "industry": c.industry,
            "score": round(overall, 1),
            "signals": sorted(sig_types),
        })
        if len(results) >= limit:
            break

    results.sort(key=lambda r: r["score"])
    return {"count": len(results), "leads": results}
