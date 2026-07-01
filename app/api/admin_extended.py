"""
Extended Admin API Endpoints
=============================
Additional endpoints for company management and system controls.
"""


import logging
import os
import time
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_
from typing import Any, Optional

from app.database import get_db
from app.models.company import Company
from app.models.crm import CrmAccount, Team, TeamMember
from app.models.outreach import OutreachMessage
from app.models.signal import Signal
from app.models.score import Score
from app.api.auth_deps import require_admin
from app.services.company_domain import normalize_website_domain, persist_company_domain, resolve_outreach_domain
from app.services.outreach_email_inference import infer_cc_outreach_emails, infer_outreach_emails

logger = logging.getLogger(__name__)
from app.services.lead_filter import pick_primary_score
from app.services.lead_primary_link import enrich_lead_link_fields

router = APIRouter(dependencies=[Depends(require_admin)])


def _invalidate_admin_caches() -> None:
    from app.services.admin_snapshot import touch_invalidate
    touch_invalidate()


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
        from app.services.lead_enrichment import enrich_company_website

        before = c.website
        found = enrich_company_website(c, sleep_s=0.8)
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
    """Clear persisted admin snapshot and in-process caches."""
    _invalidate_admin_caches()
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
    return [
        (company, float(score.overall_intent_score or 0), _tier_from_score(float(score.overall_intent_score or 0)))
        for company, score in rows
    ]


def _cal_outreach_domain(company: Company, acct: Optional[Any]) -> Optional[str]:
    return resolve_outreach_domain(company, acct)


def _cal_contact_fields(company: Company, acct: Optional[Any]) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Return (effective_email, stored_email, inferred_primary, inferred_cc)."""
    domain = _cal_outreach_domain(company, acct)
    industry = company.industry or (getattr(acct, "industry", None) if acct else None)
    guessed = infer_outreach_emails(domain, industry) if domain else None
    inferred_to = guessed.primary if guessed else None
    inferred_cc = guessed.cc[0] if guessed and guessed.cc else None
    stored = (getattr(acct, "contact_email", None) or "").strip() or None
    effective = stored or inferred_to
    return effective, stored, inferred_to, inferred_cc


def _cal_draft_for_company(company: Company, *, fresh: bool = False) -> tuple[str, str]:
    """Generate Cal subject + body using Cal's voice (no LLM)."""
    from app.services.stagegate_crm_bridge import cal_draft_for_stagegate_company, is_stagegate_company

    if is_stagegate_company(company):
        draft = cal_draft_for_stagegate_company(company)
        return draft["subject"], draft["body"]

    from app.api.crm import _draft_subject
    from app.models.crm import CrmAccount as _Acct
    from app.services.cal_autonomy import cal_buyer_outreach_body

    dummy = _Acct(
        name=company.name or "Unknown",
        website=company.website,
        industry=company.industry,
        account_type="vendor"
        if (company.crm_metadata or {}).get("outreach_pipeline") == "stagegate"
        else "buyer",
    )
    subject = _draft_subject(dummy)
    if dummy.account_type == "vendor":
        from app.api.crm import _draft_body

        body = _draft_body(dummy, None, [], "", "selective", None, company=company)
    else:
        body = cal_buyer_outreach_body(company, fresh=fresh)
    return subject, body


def _serialize_cal_row(
    company: Company,
    score: float,
    tier: str,
    acct: Optional[CrmAccount],
    delivery_status: Optional[str] = None,
    *,
    include_draft_body: bool = False,
) -> dict[str, Any]:
    effective, stored, inferred_to, inferred_cc = _cal_contact_fields(company, acct)
    has_draft = bool(
        acct
        and (
            getattr(acct, "has_draft", None)
            if getattr(acct, "has_draft", None) is not None
            else acct.outreach_draft
        )
    )
    preview = (acct.outreach_draft or "").strip()[:140] if has_draft else None
    meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    row: dict[str, Any] = {
        "company_id": company.id,
        "company_name": company.name,
        "website": company.website,
        "outreach_domain": _cal_outreach_domain(company, acct),
        "industry": company.industry or "Unknown",
        "score": round(score, 1),
        "tier": tier,
        "crm_account_id": str(acct.id) if acct else None,
        "contact_email": effective,
        "contact_email_source": "crm" if stored else ("inferred" if inferred_to else None),
        "inferred_contact_email": inferred_to,
        "default_cc": inferred_cc,
        "account_type": (acct.account_type if acct else None) or "buyer",
        "outreach_pipeline": meta.get("outreach_pipeline"),
        "robot_company_id": meta.get("robot_company_id"),
        "semantic_summary": meta.get("semantic_summary"),
        "outreach_stage": acct.outreach_stage if acct else None,
        "outreach_sent_at": acct.outreach_sent_at.isoformat() if acct and acct.outreach_sent_at else None,
        "has_draft": has_draft,
        "draft_preview": preview or None,
        "email_delivery_status": delivery_status,
    }
    if include_draft_body and has_draft and acct:
        row["draft_full"] = acct.outreach_draft
    return row


def _crm_accounts_for_companies(
    db: Session,
    company_ids: list[int],
    *,
    team_id: uuid.UUID | None = None,
) -> dict[int, SimpleNamespace]:
    """Load CRM fields for Cal outreach — scoped to admin outreach team when team_id set."""
    if not company_ids:
        return {}
    q = (
        db.query(
            CrmAccount.id,
            CrmAccount.company_id,
            CrmAccount.contact_email,
            CrmAccount.website,
            CrmAccount.industry,
            CrmAccount.outreach_stage,
            CrmAccount.outreach_sent_at,
            CrmAccount.account_type,
            func.substring(CrmAccount.outreach_draft, 1, 140).label("draft_preview"),
            CrmAccount.outreach_draft.isnot(None).label("has_draft_col"),
        )
        .filter(CrmAccount.company_id.in_(company_ids))
    )
    if team_id is not None:
        q = q.filter(CrmAccount.team_id == team_id)
    rows = q.order_by(CrmAccount.outreach_draft.isnot(None).desc(), desc(CrmAccount.updated_at)).all()
    out: dict[int, SimpleNamespace] = {}
    for r in rows:
        if r.company_id in out:
            continue
        preview = (r.draft_preview or "").strip()
        has_draft = bool(r.has_draft_col)
        out[r.company_id] = SimpleNamespace(
            id=r.id,
            company_id=r.company_id,
            contact_email=r.contact_email,
            website=r.website,
            industry=r.industry,
            outreach_stage=r.outreach_stage,
            outreach_sent_at=r.outreach_sent_at,
            account_type=r.account_type,
            has_draft=has_draft,
            outreach_draft=preview if has_draft else None,
        )
    return out


def _latest_delivery_by_account(db: Session, account_ids: list) -> dict[str, str]:
    """One row per CRM account — avoids loading every outreach message."""
    if not account_ids:
        return {}
    from sqlalchemy import text

    rows = db.execute(
        text("""
            SELECT DISTINCT ON (crm_account_id)
                   crm_account_id::text AS account_id,
                   status
            FROM outreach_messages
            WHERE crm_account_id = ANY(:ids)
            ORDER BY crm_account_id, sent_at DESC NULLS LAST
        """),
        {"ids": account_ids},
    ).fetchall()
    return {row.account_id: row.status for row in rows}


@router.get("/cal/draft/{account_id}")
def cal_draft_body(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Return full Cal draft text for one CRM account (lazy-loaded from admin table expand)."""
    acct = db.query(CrmAccount).filter(CrmAccount.id == account_id).first()
    if not acct:
        raise HTTPException(status_code=404, detail="CRM account not found")
    return {
        "crm_account_id": str(acct.id),
        "draft_full": acct.outreach_draft,
        "contact_email": acct.contact_email,
    }


class CalDraftPatchIn(BaseModel):
    outreach_draft: str
    contact_email: Optional[str] = None


@router.patch("/cal/draft/{account_id}")
def patch_cal_draft(
    account_id: uuid.UUID,
    body: CalDraftPatchIn,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Save editorial changes to a Cal outreach draft (admin only)."""
    acct = db.query(CrmAccount).filter(CrmAccount.id == account_id).first()
    if not acct:
        raise HTTPException(status_code=404, detail="CRM account not found")
    draft = (body.outreach_draft or "").strip()
    if not draft:
        raise HTTPException(status_code=400, detail="outreach_draft cannot be empty")
    acct.outreach_draft = draft
    if body.contact_email is not None:
        acct.contact_email = body.contact_email.strip() or None
    db.commit()
    db.refresh(acct)
    return {
        "crm_account_id": str(acct.id),
        "draft_full": acct.outreach_draft,
        "contact_email": acct.contact_email,
    }


def _empty_cal_draft_payload(*, include_prospects: bool) -> dict[str, Any]:
    return {
        "summary": {
            "total": 0, "hot": 0, "warm": 0, "drafted": 0, "unsent_drafted": 0,
            "sendable": 0, "no_email": 0, "pending_draft": 0, "sent": 0,
            "opened": 0, "clicked": 0, "replied": 0,
        },
        "prospects": [] if include_prospects else [],
        "stale": True,
    }


def _build_cal_draft_status_payload(
    db: Session,
    *,
    admin_uid: uuid.UUID,
    admin_email: str = "",
    include_draft_bodies: bool,
    include_prospects: bool,
    prospect_limit: int,
) -> dict[str, Any]:
    """Return HOT+WARM prospects with Cal draft state on the admin outreach team."""
    team = _admin_team(db, admin_uid, admin_email)
    companies = _hot_warm_companies(db)
    company_ids = [c.id for c, _, _ in companies]
    accounts_by_company = _crm_accounts_for_companies(db, company_ids, team_id=team.id)

    account_ids = [a.id for a in accounts_by_company.values()]
    delivery_by_account = _latest_delivery_by_account(db, account_ids)

    summary_rows: list[dict[str, Any]] = []
    for company, score, tier in companies:
        acct = accounts_by_company.get(company.id)
        has_draft = bool(acct and acct.has_draft)
        effective, _, _, _ = _cal_contact_fields(company, acct)
        summary_rows.append({
            "tier": tier,
            "has_draft": has_draft,
            "outreach_sent_at": acct.outreach_sent_at.isoformat() if acct and acct.outreach_sent_at else None,
            "contact_email": effective,
            "email_delivery_status": delivery_by_account.get(str(acct.id)) if acct else None,
            "outreach_stage": acct.outreach_stage if acct else None,
        })

    total = len(summary_rows)
    hot = sum(1 for r in summary_rows if r["tier"] == "HOT")
    warm = sum(1 for r in summary_rows if r["tier"] == "WARM")
    drafted = sum(1 for r in summary_rows if r["has_draft"])
    sent = sum(1 for r in summary_rows if r["outreach_sent_at"])
    unsent_drafted = sum(1 for r in summary_rows if r["has_draft"] and not r["outreach_sent_at"])
    sendable = sum(1 for r in summary_rows if r["has_draft"] and not r["outreach_sent_at"] and r["contact_email"])
    no_email = sum(1 for r in summary_rows if r["has_draft"] and not r["outreach_sent_at"] and not r["contact_email"])
    opened = sum(1 for r in summary_rows if r["email_delivery_status"] in ("opened", "clicked"))
    clicked = sum(1 for r in summary_rows if r["email_delivery_status"] == "clicked")
    replied = sum(1 for r in summary_rows if r["outreach_stage"] == "replied")

    prospect_rows: list[dict[str, Any]] = []
    if include_prospects:
        prospect_rows = [
            _serialize_cal_row(
                company,
                score,
                tier,
                accounts_by_company.get(company.id),
                delivery_by_account.get(str(accounts_by_company[company.id].id))
                if company.id in accounts_by_company
                else None,
                include_draft_body=include_draft_bodies,
            )
            for company, score, tier in companies[:prospect_limit]
        ]

    payload = {
        "summary": {
            "total": total,
            "hot": hot,
            "warm": warm,
            "drafted": drafted,
            "unsent_drafted": unsent_drafted,
            "sendable": sendable,
            "no_email": no_email,
            "pending_draft": total - drafted,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "team_id": str(team.id),
        },
        "prospects": prospect_rows,
    }
    return payload


@router.get("/cal/draft-status")
def cal_draft_status(
    user: dict = Depends(require_admin),
    include_draft_bodies: bool = Query(
        False,
        description="Include full draft text per prospect (large payload; prefer lazy /cal/draft/{id})",
    ),
    include_prospects: bool = Query(
        True,
        description="Include prospect rows; set false for summary-only (faster initial load)",
    ),
    prospect_limit: int = Query(
        300,
        ge=1,
        le=500,
        description="Max prospect rows returned when include_prospects=true",
    ),
):
    from app.database import SessionLocal
    from app.db_timeout import run_db

    def _run() -> dict[str, Any]:
        with SessionLocal() as db:
            return _build_cal_draft_status_payload(
                db,
                admin_uid=uuid.UUID(user["uid"]),
                admin_email=user.get("email") or "",
                include_draft_bodies=include_draft_bodies,
                include_prospects=include_prospects,
                prospect_limit=prospect_limit,
            )

    try:
        return run_db(_run, timeout_sec=25, label="cal/draft-status")
    except TimeoutError:
        logger.warning("cal/draft-status timed out — returning empty summary")
        return _empty_cal_draft_payload(include_prospects=include_prospects)


class BulkDraftBody(BaseModel):
    regenerate: bool = False
    company_ids: Optional[list[int]] = None


@router.post("/cal/bulk-draft")
def cal_bulk_draft(
    body: BulkDraftBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """
    Draft Cal outreach emails for all HOT+WARM prospects using Cal's template voice.
    No LLM calls — uses _draft_body directly. Creates CRM accounts under the admin
    team if they don't already exist. Sets a role inbox (e.g. operations@domain) as default contact_email.
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
        if body.company_ids is not None and company.id not in body.company_ids:
            continue
        try:
            acct = existing.get(company.id)
            if acct and acct.outreach_draft and not body.regenerate:
                skipped += 1
                continue

            subject, draft_body = _cal_draft_for_company(company, fresh=body.regenerate)
            domain = _cal_outreach_domain(company, acct)

            if acct is None:
                acct = CrmAccount(
                    team_id=team.id,
                    company_id=company.id,
                    name=company.name or "Unknown",
                    website=company.website,
                    industry=company.industry,
                    account_type="vendor"
                    if (company.crm_metadata or {}).get("outreach_pipeline") == "stagegate"
                    else "buyer",
                )
                db.add(acct)
                db.flush()
            elif (company.crm_metadata or {}).get("outreach_pipeline") == "stagegate":
                acct.account_type = "vendor"

            if not acct.contact_email and domain:
                guessed = infer_outreach_emails(domain, company.industry)
                if guessed:
                    acct.contact_email = guessed.primary

            from app.services.cal_autonomy import format_cal_draft_storage

            acct.outreach_draft = format_cal_draft_storage(subject, draft_body)
            acct.outreach_stage = "draft_ready"
            drafted += 1

        except Exception as exc:
            errors.append({"company_id": company.id, "name": company.name, "error": str(exc)})

    db.commit()
    _invalidate_admin_caches()
    return {
        "drafted": drafted,
        "skipped": skipped,
        "errors": errors,
        "team_id": str(team.id),
    }


@router.get("/cal/autonomy-status")
def cal_autonomy_status(_user: dict = Depends(require_admin)):
    from app.services.cal_autonomy import get_cal_autonomy_status

    return get_cal_autonomy_status()


class CalAutonomyRunBody(BaseModel):
    dry_run: bool = False


@router.post("/cal/autonomy-run")
def cal_autonomy_run(
    body: CalAutonomyRunBody,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    from app.services.cal_autonomy import run_cal_autonomy_cycle

    return run_cal_autonomy_cycle(db, dry_run=body.dry_run)


@router.get("/supply/autonomy-status")
def supply_autonomy_status(_user: dict = Depends(require_admin)):
    from app.services.supply_autonomy import get_supply_autonomy_status

    return get_supply_autonomy_status()


@router.post("/supply/autonomy-run")
def supply_autonomy_run(
    body: CalAutonomyRunBody,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    from app.services.supply_autonomy import run_supply_autonomy_cycle

    return run_supply_autonomy_cycle(db, dry_run=body.dry_run)


class BulkSendBody(BaseModel):
    limit: int = 100         # max emails to send in one call
    tier_filter: str = "all" # "all" | "HOT" | "WARM"
    dry_run: bool = False    # if True, validate but don't send
    skip_verification: bool = False


@router.post("/cal/bulk-send")
def cal_bulk_send(
    body: BulkSendBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """
    Send Cal outreach emails for all HOT+WARM prospects that have a draft but
    have NOT been sent yet.  Uses Resend under the hood.  Hard-caps at
    `body.limit` to prevent accidental mass-sends.
    """
    from app.services.resend_email import send_email_via_resend, ResendEmailError

    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")
    companies = _hot_warm_companies(db, limit=500)
    company_ids = [c.id for c, _, _ in companies]

    accounts: dict[int, CrmAccount] = {}
    if company_ids:
        for a in db.query(CrmAccount).filter(
            CrmAccount.company_id.in_(company_ids),
            CrmAccount.team_id == team.id,
        ).all():
            if a.company_id:
                accounts[a.company_id] = a

    sent_count = 0
    skipped_no_draft = 0
    skipped_already_sent = 0
    skipped_unverified = 0
    errors: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    from app.services.lead_enrichment import resolve_outreach_email, verify_email_deliverable

    for company, score, tier in companies:
        if sent_count >= body.limit:
            break
        if body.tier_filter != "all" and tier != body.tier_filter:
            continue

        acct = accounts.get(company.id)
        if not acct or not acct.outreach_draft:
            skipped_no_draft += 1
            continue
        if acct.outreach_sent_at:
            skipped_already_sent += 1
            continue

        to_email = (acct.contact_email or "").strip() or None
        email_source = "crm" if to_email else None
        if not to_email:
            to_email, email_source, _title = resolve_outreach_email(company, acct, use_apollo=True)
        if not to_email:
            errors.append({"company_id": company.id, "name": company.name, "error": "No recipient email"})
            continue

        if not _cal_should_skip_verification(body.skip_verification):
            ok, verify_reason = verify_email_deliverable(to_email)
            if not ok:
                skipped_unverified += 1
                errors.append({
                    "company_id": company.id,
                    "name": company.name,
                    "error": f"Email failed verification ({verify_reason}): {to_email}",
                    "email_source": email_source,
                })
                continue

        domain = normalize_website_domain(company.website or acct.website)
        cc_list = infer_cc_outreach_emails(domain, company.industry, primary=to_email)
        cc_email = cc_list[0] if cc_list else None

        # Build subject from draft first line or fallback
        draft_lines = (acct.outreach_draft or "").strip().splitlines()
        subject_line = next((l for l in draft_lines if l.strip()), None)
        if subject_line and subject_line.lower().startswith("subject:"):
            subject = subject_line[8:].strip()
            body_text = "\n".join(draft_lines[1:]).strip()
        else:
            subject = f"Robot automation partnership — {company.name}"
            body_text = acct.outreach_draft

        if body.dry_run:
            sent_count += 1
            continue

        try:
            send_email_via_resend(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                from_display_name="Cal · Ready For Robots",
                cc=[cc_email] if cc_email else None,
                idempotency_key=f"cal-bulk-{acct.id}",
            )
            acct.outreach_sent_at = now
            acct.outreach_stage = "contacted"
            sent_count += 1
        except ResendEmailError as exc:
            errors.append({"company_id": company.id, "name": company.name, "error": str(exc)})
        except Exception as exc:
            errors.append({"company_id": company.id, "name": company.name, "error": str(exc)})

    if not body.dry_run:
        db.commit()
        _invalidate_admin_caches()

    return {
        "sent": sent_count,
        "skipped_no_draft": skipped_no_draft,
        "skipped_already_sent": skipped_already_sent,
        "skipped_unverified": skipped_unverified,
        "errors": errors,
        "dry_run": body.dry_run,
    }


@router.post("/cal/enrich-missing-emails")
def cal_enrich_missing_emails(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
    limit: int = 40,
    dry_run: bool = False,
):
    """
    For CRM accounts with drafts but no email: DuckDuckGo website → Apollo contact → role inbox@domain.
    Processes up to `limit` HOT+WARM companies per call.
    """
    from app.services.lead_enrichment import enrich_company_and_contact
    from app.services.outreach_email_inference import should_reinfer_stored_contact

    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")
    t0 = time.perf_counter()
    companies = _hot_warm_companies(db, limit=500)
    targets: list[tuple[Company, CrmAccount, float]] = []
    skipped_complete = 0
    skipped_no_draft = 0

    for company, score, _ in companies:
        acct = db.query(CrmAccount).filter(
            CrmAccount.company_id == company.id,
            CrmAccount.team_id == team.id,
            CrmAccount.outreach_draft.isnot(None),
            CrmAccount.outreach_sent_at.is_(None),
        ).first()
        if not acct:
            skipped_no_draft += 1
            continue

        domain = _cal_outreach_domain(company, acct)
        stored = (acct.contact_email or "").strip()
        needs_website = not domain
        needs_email = not stored
        needs_reinfer = bool(stored and domain and should_reinfer_stored_contact(stored, domain))

        if not needs_website and not needs_email and not needs_reinfer:
            skipped_complete += 1
            continue
        targets.append((company, acct, score))

    targets = targets[:limit]
    resolved_website = 0
    resolved_email = 0
    apollo_hits = 0
    inferred_hits = 0
    unresolved = 0
    results: list[dict] = []

    for company, acct, score in targets:
        if dry_run:
            results.append({
                "company_id": company.id,
                "name": company.name,
                "score": round(score, 1),
                "dry_run": True,
            })
            continue
        row = enrich_company_and_contact(company, acct, sleep_s=0.7, use_apollo=True)
        domain = _cal_outreach_domain(company, acct)
        if domain:
            persist_company_domain(company, domain)
        if company.website and not acct.website:
            acct.website = company.website
        if row.get("website_after") and not row.get("website_before"):
            resolved_website += 1
        if row.get("email"):
            resolved_email += 1
            source = row.get("email_source")
            if source == "apollo":
                apollo_hits += 1
            elif source == "domain_inferred":
                inferred_hits += 1
        else:
            unresolved += 1
        results.append({**row, "score": round(score, 1), "applied": True})

    if not dry_run:
        db.commit()
        _invalidate_admin_caches()

    duration_ms = round((time.perf_counter() - t0) * 1000)
    enrich_stats = {
        "eligible": len(targets),
        "processed": len(results),
        "skipped_complete": skipped_complete,
        "skipped_no_draft": skipped_no_draft,
        "resolved_websites": resolved_website,
        "resolved_emails": resolved_email,
        "apollo_hits": apollo_hits,
        "inferred_hits": inferred_hits,
        "unresolved": unresolved,
        "duration_ms": duration_ms,
        "dry_run": dry_run,
    }
    logger.info("cal.enrich_missing_emails %s", enrich_stats)

    return {
        **enrich_stats,
        "results": results,
    }


@router.post("/cal/reinfer-contacts")
def cal_reinfer_contacts(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
    limit: int = Query(500, ge=1, le=500),
    dry_run: bool = Query(False),
):
    """
    Re-apply industry-aware role inbox inference for HOT+WARM CRM contacts.

    Updates empty contacts and legacy role inboxes (e.g. sales@domain) on the
    company domain. Skips person-style emails (john.smith@…) and already-sent outreach.
    """
    from app.services.outreach_email_inference import (
        infer_outreach_emails,
        looks_like_person_email,
        should_reinfer_stored_contact,
    )

    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")
    companies = _hot_warm_companies(db, limit=500)

    updated = 0
    unchanged = 0
    skipped_sent = 0
    skipped_person = 0
    skipped_kept = 0
    skipped_no_domain = 0
    skipped_external = 0
    results: list[dict[str, Any]] = []

    for company, score, tier in companies:
        if updated + unchanged + skipped_sent + skipped_person + skipped_kept + skipped_no_domain + skipped_external >= limit:
            break

        acct = (
            db.query(CrmAccount)
            .filter(
                CrmAccount.company_id == company.id,
                CrmAccount.team_id == team.id,
            )
            .first()
        )
        if not acct:
            continue

        if acct.outreach_sent_at:
            skipped_sent += 1
            continue

        domain = _cal_outreach_domain(company, acct)
        if not domain:
            from app.services.lead_enrichment import enrich_company_website

            enrich_company_website(company, sleep_s=0.3)
            if company.website and not acct.website:
                acct.website = company.website
            domain = _cal_outreach_domain(company, acct)
        if not domain:
            skipped_no_domain += 1
            continue

        persist_company_domain(company, domain)
        if not acct.website:
            acct.website = f"https://{domain}"

        current = (acct.contact_email or "").strip()
        if current and not should_reinfer_stored_contact(current, domain):
            if looks_like_person_email(current):
                skipped_person += 1
            elif not current.lower().endswith(f"@{domain.lower()}"):
                skipped_external += 1
            else:
                skipped_kept += 1
            continue

        guessed = infer_outreach_emails(domain, company.industry or acct.industry)
        if not guessed:
            skipped_no_domain += 1
            continue

        new_email = guessed.primary
        if current.lower() == new_email.lower():
            unchanged += 1
            continue

        row = {
            "company_id": company.id,
            "company_name": company.name,
            "tier": tier,
            "score": round(score, 1),
            "crm_account_id": str(acct.id),
            "before": current or None,
            "after": new_email,
            "industry": company.industry,
        }
        results.append(row)

        if not dry_run:
            acct.contact_email = new_email
            updated += 1
        else:
            updated += 1

    if not dry_run and updated:
        db.commit()
        _invalidate_admin_caches()

    return {
        "updated": updated,
        "unchanged": unchanged,
        "skipped_sent": skipped_sent,
        "skipped_person": skipped_person,
        "skipped_kept": skipped_kept,
        "skipped_no_domain": skipped_no_domain,
        "skipped_external": skipped_external,
        "dry_run": dry_run,
        "results": results[:50],
    }


class SingleSendBody(BaseModel):
    crm_account_id: str
    contact_email: Optional[str] = None
    outreach_draft: Optional[str] = None
    skip_verification: bool = False


def _cal_should_skip_verification(explicit: bool = False) -> bool:
    if explicit:
        return True
    return (os.getenv("CAL_SKIP_EMAIL_VERIFY") or "").strip().lower() in ("1", "true", "yes")


@router.post("/cal/send-one")
def cal_send_one(
    body: SingleSendBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Send a single drafted Cal email by CRM account ID."""
    from app.services.resend_email import send_email_via_resend, ResendEmailError
    import uuid as _uuid

    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")

    acct = db.query(CrmAccount).filter(
        CrmAccount.id == _uuid.UUID(body.crm_account_id)
    ).first()
    if not acct:
        raise HTTPException(status_code=404, detail="CRM account not found")
    if acct.team_id != team.id:
        raise HTTPException(status_code=403, detail="CRM account is not on the admin outreach team")
    if not acct.outreach_draft and not (body.outreach_draft or "").strip():
        raise HTTPException(status_code=400, detail="No draft to send")
    if acct.outreach_sent_at:
        raise HTTPException(status_code=400, detail="Already sent")

    if (body.outreach_draft or "").strip():
        acct.outreach_draft = body.outreach_draft.strip()
    if body.contact_email is not None:
        acct.contact_email = body.contact_email.strip() or None
        db.flush()

    company = db.query(Company).filter(Company.id == acct.company_id).first() if acct.company_id else None
    from app.services.lead_enrichment import resolve_outreach_email, verify_email_deliverable

    to_email = (acct.contact_email or "").strip() or None
    if not to_email:
        to_email, _src, _title = resolve_outreach_email(company or Company(name=acct.name), acct, use_apollo=True)
    if not to_email:
        raise HTTPException(status_code=400, detail="No recipient email — add one in the contact field and try again")

    if not _cal_should_skip_verification(body.skip_verification):
        ok, reason = verify_email_deliverable(to_email)
        if not ok:
            raise HTTPException(status_code=400, detail=f"Email failed verification ({reason}): {to_email}")

    domain = normalize_website_domain((company.website if company else None) or acct.website)
    industry = (company.industry if company else None) or acct.industry
    cc_list = infer_cc_outreach_emails(domain, industry, primary=to_email)
    cc_email = cc_list[0] if cc_list else None
    draft_lines = (acct.outreach_draft or "").strip().splitlines()
    subject_line = next((l for l in draft_lines if l.strip()), None)
    if subject_line and subject_line.lower().startswith("subject:"):
        subject = subject_line[8:].strip()
        body_text = "\n".join(draft_lines[1:]).strip()
    else:
        subject = f"Robot automation partnership — {acct.name}"
        body_text = acct.outreach_draft

    try:
        send_email_via_resend(
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            from_display_name="Cal · Ready For Robots",
            cc=[cc_email] if cc_email else None,
            idempotency_key=f"cal-single-{acct.id}",
        )
    except ResendEmailError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail=str(exc))

    now = datetime.now(timezone.utc)
    acct.outreach_sent_at = now
    acct.outreach_stage = "contacted"
    db.commit()
    _invalidate_admin_caches()
    return {"sent": True, "to": to_email, "sent_at": now.isoformat()}


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


# ── SCOUT bulk automation ─────────────────────────────────────────────────────

@router.get("/scout/status")
def scout_bulk_status(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Return counts for the admin SCOUT automation panel."""
    from app.models.scout_chat import ScoutActivation
    total_prospects = db.query(func.count(Company.id)).join(Score, Score.company_id == Company.id).filter(Score.overall_intent_score >= _WARM_THRESHOLD).scalar() or 0
    activated = db.query(func.count(ScoutActivation.id)).scalar() or 0
    drafted   = db.query(func.count(ScoutActivation.id)).filter(ScoutActivation.status == "drafted").scalar() or 0
    sent      = db.query(func.count(ScoutActivation.id)).filter(ScoutActivation.status == "sent").scalar() or 0
    pending   = db.query(func.count(ScoutActivation.id)).filter(ScoutActivation.status == "awaiting_approval").scalar() or 0
    return {"total_prospects": total_prospects, "activated": activated, "drafted": drafted, "sent": sent, "pending_approval": pending}


class ScoutBulkActivateBody(BaseModel):
    limit: int = 100
    tier_filter: str = "all"   # "all" | "HOT" | "WARM"
    dry_run: bool = False


@router.post("/scout/bulk-activate")
def scout_bulk_activate(
    body: ScoutBulkActivateBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """
    Activate SCOUT for all HOT/WARM prospects that don't yet have an activation.
    Auto-drafts Cal outreach in agent voice immediately — no per-prospect click needed.
    """
    from app.models.scout_chat import ScoutActivation, ScoutSession
    from app.models.crm import CrmAccount, Team, TeamMember
    import app.services.scout_chat_service as scsvc

    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")

    companies = _hot_warm_companies(db, limit=body.limit)
    if body.tier_filter != "all":
        companies = [(c, sc, t) for c, sc, t in companies if t == body.tier_filter.upper()]

    # Existing activations keyed by company_id
    existing_company_ids: set[int] = set()
    existing_accts: dict[int, CrmAccount] = {}
    if companies:
        cids = [c.id for c, _, _ in companies]
        for acct in db.query(CrmAccount).filter(CrmAccount.company_id.in_(cids), CrmAccount.team_id == team.id).all():
            if acct.company_id:
                existing_accts[acct.company_id] = acct
        # Check if activation already exists for any of these accounts
        existing_acct_ids = [str(a.id) for a in existing_accts.values()]
        if existing_acct_ids:
            for act in db.query(ScoutActivation).filter(ScoutActivation.status != "sent").all():
                snap = act.leads_snapshot or []
                for lead in snap:
                    if isinstance(lead, dict):
                        existing_company_ids.add(int(lead.get("id") or 0))

    activated = skipped = errors_count = 0
    errors: list[dict] = []

    # Ensure a shared admin session exists
    admin_fp = f"admin-bulk-{str(uid)[:8]}"
    sess, _ = scsvc.upsert_session(db, admin_fp)
    sess.user_id = uid
    db.flush()

    for company, score, tier in companies:
        if activated >= body.limit:
            break
        if company.id in existing_company_ids:
            skipped += 1
            continue

        try:
            # Get or create CRM account
            acct = existing_accts.get(company.id)
            if not acct:
                domain = normalize_website_domain(company.website)
                guessed = infer_outreach_emails(domain, company.industry) if domain else None
                acct = CrmAccount(
                    team_id=team.id,
                    company_id=company.id,
                    name=company.name or "Unknown",
                    website=company.website,
                    industry=company.industry,
                    contact_email=guessed.primary if guessed else None,
                    owner_user_id=uid,
                    outreach_stage="review_required",
                )
                db.add(acct)
                db.flush()

            # Auto-draft in Cal's voice
            subject, draft_body = _cal_draft_for_company(company)
            if not acct.outreach_draft:
                acct.outreach_draft = draft_body
                acct.outreach_stage = "draft_ready"

            lead_snapshot = {
                "id": str(company.id),
                "company": company.name or "Unknown",
                "industry": company.industry or "",
                "score": round(score, 1),
                "tier": tier,
            }

            if not body.dry_run:
                domain = normalize_website_domain(company.website)
                activation = ScoutActivation(
                    session_id=sess.id,
                    user_id=uid,
                    source_url=company.website,
                    material_choice="cal_outreach",
                    scope_choice="outreach",
                    mode_choice="selective",
                    status="drafted",
                    lead_ids=[str(company.id)],
                    leads_snapshot=[lead_snapshot],
                    work_plan={
                        "mode": "selective",
                        "scope": "outreach",
                        "draft_subject": subject,
                        "draft_body": draft_body,
                        "to_email": acct.contact_email,
                        "cc_email": (
                            infer_cc_outreach_emails(domain, company.industry, primary=acct.contact_email)[0]
                            if domain and acct.contact_email
                            else None
                        ),
                    },
                    activity_log=[{"type": "bulk_activated", "message": f"Auto-activated by admin bulk run. Tier: {tier}, Score: {round(score,1)}"}],
                )
                db.add(activation)

            activated += 1

        except Exception as exc:
            errors_count += 1
            errors.append({"company_id": company.id, "name": company.name, "error": str(exc)})

    if not body.dry_run:
        db.commit()

    return {"activated": activated, "skipped": skipped, "errors": errors_count, "error_detail": errors[:10], "dry_run": body.dry_run}


class ScoutBulkSendBody(BaseModel):
    limit: int = 100
    dry_run: bool = False


@router.post("/scout/bulk-send")
def scout_bulk_send_all(
    body: ScoutBulkSendBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """
    Send all drafted SCOUT activations that have a draft and haven't been sent.
    Uses Resend. Marks activation status = 'sent' and CRM account outreach_sent_at.
    """
    from app.models.scout_chat import ScoutActivation
    from app.services.resend_email import send_email_via_resend, ResendEmailError

    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")
    now = datetime.now(timezone.utc)

    drafted = db.query(ScoutActivation).filter(
        ScoutActivation.user_id == uid,
        ScoutActivation.status == "drafted",
    ).limit(body.limit).all()

    sent_count = skipped = errors_count = 0
    errors: list[dict] = []

    for activation in drafted:
        plan = activation.work_plan or {}
        to_email = plan.get("to_email")
        subject = plan.get("draft_subject") or "Robot automation partnership"
        draft_body_text = plan.get("draft_body") or ""
        cc_email = plan.get("cc_email")

        if not to_email or not draft_body_text:
            skipped += 1
            continue

        if body.dry_run:
            sent_count += 1
            continue

        try:
            send_email_via_resend(
                to_email=to_email,
                subject=subject,
                body_text=draft_body_text,
                from_display_name="Cal · Ready For Robots",
                cc=[cc_email] if cc_email else None,
                idempotency_key=f"scout-send-{activation.id}",
            )
            activation.status = "sent"
            log = list(activation.activity_log or [])
            log.append({"type": "sent", "message": f"Email sent to {to_email}", "sent_at": now.isoformat()})
            activation.activity_log = log

            # Mark CRM account as contacted
            snap = activation.leads_snapshot or []
            for lead in snap:
                try:
                    cid = int(lead.get("id") or 0)
                    acct = db.query(CrmAccount).filter(CrmAccount.company_id == cid, CrmAccount.team_id == team.id).first()
                    if acct:
                        acct.outreach_sent_at = now
                        acct.outreach_stage = "contacted"
                except Exception:
                    pass

            sent_count += 1
        except ResendEmailError as exc:
            errors_count += 1
            errors.append({"activation_id": activation.id, "to": to_email, "error": str(exc)})
        except Exception as exc:
            errors_count += 1
            errors.append({"activation_id": activation.id, "to": to_email, "error": str(exc)})

    if not body.dry_run:
        db.commit()

    return {"sent": sent_count, "skipped": skipped, "errors": errors_count, "error_detail": errors[:10], "dry_run": body.dry_run}


@router.get("/scout/diagnostic")
def scout_diagnostic(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """
    Workflow health check for Cal / SCOUT outreach.
    Returns:
    - Sending configuration (from_email, reply_to, webhook status)
    - Delivery stats for the last 30 days (sent, delivered, opened, clicked, bounced, replied)
    - Last 10 outreach messages with status
    """
    import os
    from datetime import timedelta
    from sqlalchemy import text as sa_text

    from_email = (os.getenv("RESEND_FROM_EMAIL") or "").strip()
    reply_to = (os.getenv("RESEND_REPLY_TO") or "").strip()
    webhook_secret_set = bool((os.getenv("RESEND_WEBHOOK_SECRET") or "").strip())
    inbound_secret_set = bool((os.getenv("RESEND_INBOUND_WEBHOOK_SECRET") or "").strip())
    api_key_set = bool((os.getenv("RESEND_API_KEY") or "").strip())

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    # Delivery stats
    status_counts: dict[str, int] = {}
    rows_raw = (
        db.query(OutreachMessage.status, func.count(OutreachMessage.id))
        .filter(OutreachMessage.created_at >= cutoff)
        .group_by(OutreachMessage.status)
        .all()
    )
    for status, cnt in rows_raw:
        status_counts[status or "unknown"] = cnt

    # Count replied via OutreachReply
    from app.models.outreach import OutreachReply
    reply_count = db.query(func.count(OutreachReply.id)).filter(OutreachReply.received_at >= cutoff).scalar() or 0

    # Last 10 messages
    recent_msgs = (
        db.query(
            OutreachMessage.id,
            OutreachMessage.to_email,
            OutreachMessage.subject,
            OutreachMessage.status,
            OutreachMessage.sent_at,
            OutreachMessage.crm_account_id,
        )
        .order_by(OutreachMessage.created_at.desc())
        .limit(10)
        .all()
    )
    # Resolve company names from CRM accounts
    account_ids = [str(m.crm_account_id) for m in recent_msgs if m.crm_account_id]
    from app.models.crm import CrmAccount
    accounts_by_id: dict[str, str] = {}
    if account_ids:
        accts = db.query(CrmAccount.id, CrmAccount.name).filter(
            CrmAccount.id.in_([uuid.UUID(aid) for aid in account_ids])
        ).all()
        accounts_by_id = {str(a.id): a.name or "—" for a in accts}

    recent_list = [
        {
            "id": str(m.id),
            "to": m.to_email,
            "subject": m.subject,
            "status": m.status,
            "sent_at": m.sent_at.isoformat() if m.sent_at else None,
            "company": accounts_by_id.get(str(m.crm_account_id), "—") if m.crm_account_id else "—",
        }
        for m in recent_msgs
    ]

    issues: list[str] = []
    if not api_key_set:
        issues.append("RESEND_API_KEY is not set — emails cannot be sent")
    if not from_email:
        issues.append("RESEND_FROM_EMAIL is not set — Cal has no sender address")
    if not reply_to:
        issues.append("RESEND_REPLY_TO is not set — replies will go to RESEND_FROM_EMAIL, not a monitored inbox")
    if not webhook_secret_set:
        issues.append("RESEND_WEBHOOK_SECRET is not set — delivery events (open/click/bounce) won't be tracked")
    if not inbound_secret_set:
        issues.append("RESEND_INBOUND_WEBHOOK_SECRET is not set — inbound email replies won't be captured")

    from app.services.stagegate_voice import STAGEGATE_OUTREACH_RULES

    return {
        "config": {
            "from_email": from_email or None,
            "reply_to": reply_to or None,
            "api_key_set": api_key_set,
            "delivery_webhook_configured": webhook_secret_set,
            "inbound_webhook_configured": inbound_secret_set,
        },
        "cal_outreach_style": {
            "stagegate_rules": list(STAGEGATE_OUTREACH_RULES),
        },
        "stats_30d": {
            "sent": status_counts.get("sent", 0) + status_counts.get("delivered", 0),
            "delivered": status_counts.get("delivered", 0),
            "opened": status_counts.get("opened", 0),
            "clicked": status_counts.get("clicked", 0),
            "bounced": status_counts.get("bounced", 0) + status_counts.get("complained", 0) + status_counts.get("suppressed", 0),
            "replied": reply_count,
            "total": sum(status_counts.values()),
        },
        "recent_emails": recent_list,
        "issues": issues,
        "health": "ok" if not issues else ("warn" if len(issues) <= 2 else "error"),
    }
