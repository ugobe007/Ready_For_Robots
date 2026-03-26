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
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company

router = APIRouter()


class PurgeJunkPayload(BaseModel):
    dry_run: bool = True          # safe default: preview only
    limit: Optional[int] = None   # safety cap on how many to delete at once


def _check_admin_key(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")) -> None:
    """Accept X-Admin-Key matching ADMIN_KEY env var."""
    key = os.getenv("ADMIN_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="ADMIN_KEY not configured on server")
    if x_admin_key != key:
        raise HTTPException(status_code=401, detail="Invalid X-Admin-Key")


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
    ids_to_delete = [r["id"] for r in junk_found]
    deleted = 0
    for cid in ids_to_delete:
        db.execute(text("DELETE FROM scores  WHERE company_id = :cid"), {"cid": cid})
        db.execute(text("DELETE FROM signals WHERE company_id = :cid"), {"cid": cid})
        db.execute(text("DELETE FROM companies WHERE id = :cid"), {"cid": cid})
        deleted += 1
    db.commit()

    return {
        "dry_run": False,
        "deleted": deleted,
        "total_companies_before": len(companies),
        "remaining": len(companies) - deleted,
        "sample_deleted": [r["name"] for r in junk_found[:30]],
    }
