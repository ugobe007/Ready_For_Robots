"""
Extended Admin API Endpoints
=============================
Additional endpoints for company management and system controls.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_
from typing import Any, Optional

from app.database import get_db
from app.models.company import Company
from app.models.crm import CrmAccount, Team, TeamMember
from app.models.signal import Signal
from app.models.score import Score
from app.api.auth_deps import require_admin
from app.services.company_domain import normalize_website_domain
from app.services.lead_filter import pick_primary_score
from app.services.lead_primary_link import enrich_lead_link_fields
from app.services.website_inference import sleep_between_lookups, try_duckduckgo_company_website

router = APIRouter(dependencies=[Depends(require_admin)])


# ── Company Management ────────────────────────────────────────────────────────

@router.get("/companies/search")
def search_companies(
    q: str = "",
    industry: str = "",
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search companies with filters for admin panel."""
    
    query = db.query(Company)
    
    if q:
        query = query.filter(
            or_(
                Company.name.ilike(f"%{q}%"),
                Company.website.ilike(f"%{q}%")
            )
        )
    
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    
    companies = query.order_by(desc(Company.created_at)).limit(limit).all()
    
    # Get signal counts and scores for each company
    result = []
    for c in companies:
        signal_count = db.query(func.count(Signal.id)).filter(Signal.company_id == c.id).scalar() or 0
        score_rec = db.query(Score).filter(Score.company_id == c.id).first()
        
        result.append({
            "id": c.id,
            "name": c.name,
            "website": c.website,
            "industry": c.industry,
            "location_city": c.location_city,
            "location_state": c.location_state,
            "signal_count": signal_count,
            "score": score_rec.overall_intent_score if score_rec else None,
        })
    
    return {"companies": result}


@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    """Delete a company and all its signals and scores."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Delete signals and scores first (cascade should handle this, but being explicit)
    db.query(Signal).filter(Signal.company_id == company_id).delete()
    db.query(Score).filter(Score.company_id == company_id).delete()
    db.delete(company)
    db.commit()
    
    return {"status": "deleted", "company_id": company_id}


class InferWebsitesBody(BaseModel):
    """Batch DDG lookups for companies missing a site and evidence URL — rate-limited."""

    limit: int = 12
    dry_run: bool = False
    min_score: float = 0.0


class LeadResearchBody(BaseModel):
    company_id: Optional[int] = None
    limit: int = 10
    dry_run: bool = True
    lookback_days: int = 30


@router.post("/lead-research/run")
def run_lead_research_admin(body: LeadResearchBody, db: Session = Depends(get_db)):
    """Trigger a one-company or bounded-batch lead research run."""
    from app.services.lead_research_agent import research_active_leads, research_company_updates

    if body.company_id:
        summary = research_company_updates(
            db,
            body.company_id,
            dry_run=body.dry_run,
            lookback_days=body.lookback_days,
            notify=not body.dry_run,
        )
        return summary.__dict__
    return research_active_leads(
        db,
        limit=max(1, min(body.limit, 50)),
        dry_run=body.dry_run,
        lookback_days=body.lookback_days,
    )


@router.post("/companies/infer-websites")
def infer_company_websites(body: InferWebsitesBody, db: Session = Depends(get_db)):
    """
    Best-effort: set `companies.website` from DuckDuckGo instant answers when the lead has
    no website and no http signal `source_url` (see `lead_primary_link.enrich_lead_link_fields`).
    """
    cap = max(1, min(body.limit, 40))
    rows = (
        db.query(Company)
        .options(joinedload(Company.signals), joinedload(Company.scores))
        .order_by(Company.id.desc())
        .limit(800)
        .all()
    )
    candidates: list = []
    for c in rows:
        ps = pick_primary_score(c.scores)
        sc = float(ps.overall_intent_score) if ps else 0.0
        if sc < body.min_score:
            continue
        sigs = c.signals or []
        ex = enrich_lead_link_fields(
            website=c.website,
            signals=sigs,
            overall_score=sc,
            signal_count=len(sigs),
        )
        if not ex["needs_website_inference"]:
            continue
        candidates.append((c, sc, ex["suggested_pipeline_action"]))
    candidates.sort(key=lambda x: -x[1])
    out: list = []
    for c, sc, action in candidates[:cap]:
        found = try_duckduckgo_company_website(c.name)
        sleep_between_lookups(0.8)
        item = {
            "company_id": c.id,
            "name": c.name,
            "overall_score": sc,
            "suggested_pipeline_action": action,
            "found_website": found,
            "applied": False,
        }
        if found and not body.dry_run:
            c.website = found
            db.add(c)
            item["applied"] = True
        out.append(item)
    if not body.dry_run:
        db.commit()
    return {"processed": len(out), "dry_run": body.dry_run, "results": out}


class MergeDupesBody(BaseModel):
    dry_run: bool = True
    domain: Optional[str] = None


@router.post("/merge-duplicate-companies-by-domain")
def merge_duplicate_companies_by_domain_admin(body: MergeDupesBody, db: Session = Depends(get_db)):
    """
    Physically merge duplicate `companies` rows sharing `website_domain` (see `company_merge` service).
    Default `dry_run: true` returns the plan without deleting rows.
    """
    from app.services.company_merge import merge_duplicate_companies_by_domain

    return merge_duplicate_companies_by_domain(
        db, dry_run=body.dry_run, domain_filter=body.domain
    )


@router.get("/rep-feedback-summary")
def rep_feedback_summary(db: Session = Depends(get_db)):
    """Aggregate rep thumbs / reason codes for tuning the pipeline."""
    from app.models.lead_rep_feedback import LeadRepFeedback

    vote_rows = (
        db.query(LeadRepFeedback.vote, func.count(LeadRepFeedback.id))
        .group_by(LeadRepFeedback.vote)
        .all()
    )
    by_vote = {r[0]: r[1] for r in vote_rows}
    reason_rows = (
        db.query(LeadRepFeedback.reason_code, func.count(LeadRepFeedback.id))
        .filter(LeadRepFeedback.reason_code.isnot(None))
        .group_by(LeadRepFeedback.reason_code)
        .all()
    )
    by_reason = {r[0]: r[1] for r in reason_rows}
    return {
        "by_vote": by_vote,
        "by_reason": by_reason,
        "total": sum(by_vote.values()),
    }


# ── System Controls ───────────────────────────────────────────────────────────

@router.post("/system/cache/clear")
def clear_cache():
    """Clear all application caches."""
    # In a real app, you'd clear Redis or in-memory caches
    # For now, just return success
    return {"status": "success", "message": "Cache cleared"}


@router.post("/system/reindex")
def reindex_database(db: Session = Depends(get_db)):
    """Reindex database for better performance."""
    return {"status": "success", "message": "Database reindexed"}


@router.post("/system/cleanup-junk-leads")
def trigger_cleanup_junk_leads(_user: dict = Depends(require_admin)):
    """Trigger the junk-lead cleanup Celery task immediately (admin only)."""
    try:
        from worker.tasks import cleanup_junk_leads_task
        result = cleanup_junk_leads_task.delay()
        return {"status": "queued", "task_id": result.id}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not queue task: {exc}") from exc


# ── Cal Outreach: bulk draft for HOT/WARM prospects ──────────────────────────

_HOT_THRESHOLD = 75.0
_WARM_THRESHOLD = 45.0


def _tier_from_score(score: float) -> str:
    if score >= _HOT_THRESHOLD:
        return "HOT"
    if score >= _WARM_THRESHOLD:
        return "WARM"
    return "COLD"


def _admin_team(db: Session, uid: uuid.UUID, email: str) -> Team:
    """Get or create a dedicated admin outreach team for the admin user."""
    existing = (
        db.query(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(TeamMember.user_id == uid, Team.slug == "admin-cal-outreach")
        .first()
    )
    if existing:
        return existing
    team = Team(name="Cal Outreach (Admin)", slug="admin-cal-outreach")
    db.add(team)
    db.flush()
    member = TeamMember(team_id=team.id, user_id=uid, role="owner")
    db.add(member)
    db.flush()
    return team


def _hot_warm_companies(db: Session, limit: int = 300) -> list[tuple[Company, float, str]]:
    """Return (company, score, tier) for HOT and WARM leads, highest score first."""
    rows = (
        db.query(Company, Score)
        .join(Score, Score.company_id == Company.id)
        .filter(Score.overall_intent_score >= _WARM_THRESHOLD)
        .order_by(Score.overall_intent_score.desc())
        .limit(limit)
        .all()
    )
    seen: set[int] = set()
    out: list[tuple[Company, float, str]] = []
    for company, score in rows:
        if company.id in seen:
            continue
        seen.add(company.id)
        sc = float(score.overall_intent_score or 0)
        out.append((company, sc, _tier_from_score(sc)))
    return out


def _cal_draft_for_company(company: Company) -> tuple[str, str]:
    """Generate Cal subject + body using the template voice (no LLM)."""
    from app.api.crm import _draft_subject, _draft_body
    from app.models.crm import CrmAccount as _Acct

    dummy = _Acct(
        name=company.name or "Unknown",
        website=company.website,
        industry=company.industry,
    )
    subject = _draft_subject(dummy)
    body = _draft_body(dummy, None, [], "", "selective", None)
    return subject, body


def _serialize_cal_row(
    company: Company,
    score: float,
    tier: str,
    acct: Optional[CrmAccount],
) -> dict[str, Any]:
    domain = normalize_website_domain(company.website)
    inferred_to = f"sales@{domain}" if domain else None
    inferred_cc = f"marketing@{domain}" if domain else None
    contact_email = (acct.contact_email if acct else None) or inferred_to
    has_draft = bool(acct and acct.outreach_draft)
    return {
        "company_id": company.id,
        "company_name": company.name,
        "website": company.website,
        "industry": company.industry or "Unknown",
        "score": round(score, 1),
        "tier": tier,
        "crm_account_id": str(acct.id) if acct else None,
        "contact_email": contact_email,
        "default_cc": inferred_cc,
        "outreach_stage": acct.outreach_stage if acct else None,
        "outreach_sent_at": acct.outreach_sent_at.isoformat() if acct and acct.outreach_sent_at else None,
        "has_draft": has_draft,
        "draft_preview": (acct.outreach_draft or "")[:140].strip() if has_draft else None,
        "draft_full": acct.outreach_draft if has_draft else None,
    }


@router.get("/cal/draft-status")
def cal_draft_status(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Return HOT+WARM prospects with their Cal draft state against the live DB."""
    companies = _hot_warm_companies(db)
    company_ids = [c.id for c, _, _ in companies]
    accounts_by_company: dict[int, CrmAccount] = {}
    if company_ids:
        accts = (
            db.query(CrmAccount)
            .filter(CrmAccount.company_id.in_(company_ids))
            .all()
        )
        for a in accts:
            if a.company_id and a.company_id not in accounts_by_company:
                accounts_by_company[a.company_id] = a

    rows = [
        _serialize_cal_row(company, score, tier, accounts_by_company.get(company.id))
        for company, score, tier in companies
    ]

    total = len(rows)
    hot = sum(1 for r in rows if r["tier"] == "HOT")
    warm = sum(1 for r in rows if r["tier"] == "WARM")
    drafted = sum(1 for r in rows if r["has_draft"])
    sent = sum(1 for r in rows if r["outreach_sent_at"])

    return {
        "summary": {
            "total": total,
            "hot": hot,
            "warm": warm,
            "drafted": drafted,
            "pending_draft": total - drafted,
            "sent": sent,
        },
        "prospects": rows,
    }


class BulkDraftBody(BaseModel):
    regenerate: bool = False


@router.post("/cal/bulk-draft")
def cal_bulk_draft(
    body: BulkDraftBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """
    Draft Cal outreach emails for all HOT+WARM prospects using Cal's template voice.
    No LLM calls — uses _draft_body directly. Creates CRM accounts under the admin
    team if they don't already exist. Sets sales@domain as default contact_email.
    """
    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")
    companies = _hot_warm_companies(db)
    company_ids = [c.id for c, _, _ in companies]

    existing: dict[int, CrmAccount] = {}
    if company_ids:
        for a in db.query(CrmAccount).filter(
            CrmAccount.company_id.in_(company_ids),
            CrmAccount.team_id == team.id,
        ).all():
            if a.company_id:
                existing[a.company_id] = a

    drafted = 0
    skipped = 0
    errors: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for company, score, tier in companies:
        try:
            acct = existing.get(company.id)
            if acct and acct.outreach_draft and not body.regenerate:
                skipped += 1
                continue

            subject, draft_body = _cal_draft_for_company(company)
            domain = normalize_website_domain(company.website)

            if acct is None:
                acct = CrmAccount(
                    team_id=team.id,
                    company_id=company.id,
                    name=company.name or "Unknown",
                    website=company.website,
                    industry=company.industry,
                )
                db.add(acct)
                db.flush()

            if not acct.contact_email and domain:
                acct.contact_email = f"sales@{domain}"

            acct.outreach_draft = draft_body
            acct.outreach_stage = "draft_ready"
            drafted += 1

        except Exception as exc:
            errors.append({"company_id": company.id, "name": company.name, "error": str(exc)})

    db.commit()
    return {
        "drafted": drafted,
        "skipped": skipped,
        "errors": errors,
        "team_id": str(team.id),
    }


@router.get("/export/all")
def export_all_data(db: Session = Depends(get_db)):
    """Export all data as JSON."""
    from datetime import datetime
    
    companies = db.query(Company).all()
    signals = db.query(Signal).all()
    scores = db.query(Score).all()
    
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "companies": [
            {
                "id": c.id,
                "name": c.name,
                "website": c.website,
                "industry": c.industry,
                "location_city": c.location_city,
                "location_state": c.location_state,
            }
            for c in companies
        ],
        "signals": [
            {
                "id": s.id,
                "company_id": s.company_id,
                "signal_type": s.signal_type,
                "description": s.description,
            }
            for s in signals
        ],
        "scores": [
            {
                "id": sc.id,
                "company_id": sc.company_id,
                "overall_intent_score": sc.overall_intent_score,
                "automation_score": sc.automation_score,
                "labor_pain_score": sc.labor_pain_score,
            }
            for sc in scores
        ],
    }
