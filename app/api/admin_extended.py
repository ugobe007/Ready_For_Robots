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


def cal_manual_approval_required() -> bool:
    """When false (default), Cal drafts and sends without manual approve step."""
    return (os.getenv("CAL_MANUAL_APPROVAL") or "0").strip().lower() in ("1", "true", "yes")


def _cal_is_approved(stage: Optional[str]) -> bool:
    if not cal_manual_approval_required():
        return True
    return (stage or "") in ("draft_approved", "approved")


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


def _skip_stagegate_for_rfr_admin(company: Company) -> bool:
    """StageGate OEM/show-ops accounts belong on onstage.bot — never in RFR Cal admin."""
    from app.services.brand import is_stagegate_branded

    return is_stagegate_branded(company)


def _hot_warm_companies_fast(db: Session, limit: int = 300) -> list[tuple[Company, float, str]]:
    """Score-threshold HOT/WARM list — no per-lead classify (fast for admin dashboard)."""
    rows = (
        db.query(Company, Score)
        .join(Score, Score.company_id == Company.id)
        .filter(Score.overall_intent_score >= _WARM_THRESHOLD)
        .filter(Company.is_internal.isnot(False))
        .order_by(Score.overall_intent_score.desc())
        .limit(limit)
        .all()
    )
    out: list[tuple[Company, float, str]] = []
    for company, score in rows:
        if _skip_stagegate_for_rfr_admin(company):
            continue
        s = float(score.overall_intent_score or 0)
        tier = "HOT" if s >= 75 else "WARM"
        out.append((company, s, tier))
        if len(out) >= limit:
            break
    return out


def _hot_warm_companies(db: Session, limit: int = 300) -> list[tuple[Company, float, str]]:
    """Return (company, score, tier) for HOT and WARM buyer leads — excludes junk/classified COLD."""
    from sqlalchemy.orm import joinedload

    from app.services.lead_filter import classify_lead

    rows = (
        db.query(Company, Score)
        .join(Score, Score.company_id == Company.id)
        .options(joinedload(Company.signals))
        .filter(Score.overall_intent_score >= _WARM_THRESHOLD)
        .filter(Company.is_internal.isnot(False))
        .order_by(Score.overall_intent_score.desc())
        .limit(max(limit * 4, limit))
        .all()
    )
    out: list[tuple[Company, float, str]] = []
    for company, score in rows:
        if _skip_stagegate_for_rfr_admin(company):
            continue
        junk, _, pri = classify_lead(company, score, company.signals)
        if junk or pri.tier not in ("HOT", "WARM"):
            continue
        out.append((company, float(score.overall_intent_score or 0), pri.tier))
        if len(out) >= limit:
            break
    return out


def _cal_outreach_domain(company: Company, acct: Optional[Any]) -> Optional[str]:
    return resolve_outreach_domain(company, acct)


def _cal_contact_fields(company: Company, acct: Optional[Any]) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Return (effective_email, stored_email, inferred_primary, inferred_cc)."""
    from app.services.email_address import normalize_recipient_email

    domain = _cal_outreach_domain(company, acct)
    industry = company.industry or (getattr(acct, "industry", None) if acct else None)
    guessed = infer_outreach_emails(domain, industry) if domain else None
    inferred_to = guessed.primary if guessed else None
    inferred_cc = guessed.cc[0] if guessed and guessed.cc else None
    stored_raw = (getattr(acct, "contact_email", None) or "").strip() or None
    stored = normalize_recipient_email(stored_raw) if stored_raw else None
    effective = stored or normalize_recipient_email(inferred_to) or inferred_to
    return effective, stored, inferred_to, inferred_cc


def _cal_draft_for_company(
    company: Company, *, fresh: bool = False, variant_id: str | None = None
) -> tuple[str, str]:
    """Generate Cal subject + body using Cal's voice (no LLM).

    For buyers, `variant_id` selects the trust-first angle. When omitted it is
    resolved deterministically from the company id so drafts are reproducible.
    """
    from app.services.brand import is_stagegate_branded

    if is_stagegate_branded(company):
        raise ValueError(
            "StageGate accounts are isolated from Ready For Robots Cal admin — "
            "work them on onstage.bot, not readyforrobots.com/admin."
        )

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
    if dummy.account_type == "vendor":
        from app.api.crm import _draft_body

        subject = _draft_subject(dummy)
        body = _draft_body(dummy, None, [], "", "selective", None, company=company)
    else:
        from app.services.agent_messaging import pick_buyer_variant

        vid = variant_id or pick_buyer_variant(getattr(company, "id", None))
        subject = _draft_subject(dummy, variant_id=vid)
        body = cal_buyer_outreach_body(company, fresh=fresh, variant_id=vid)
    return subject, body


def _serialize_cal_row(
    company: Company,
    score: float,
    tier: str,
    acct: Optional[CrmAccount],
    delivery_status: Optional[str] = None,
    *,
    include_draft_body: bool = False,
    fast_contact: bool = False,
) -> dict[str, Any]:
    if fast_contact:
        stored = (getattr(acct, "contact_email", None) or "").strip() or None
        effective, stored, inferred_to, inferred_cc = stored, stored, None, None
    else:
        effective, stored, inferred_to, inferred_cc = _cal_contact_fields(company, acct)
    has_draft = bool(
        acct
        and (
            getattr(acct, "has_draft", None)
            if getattr(acct, "has_draft", None) is not None
            else acct.outreach_draft
        )
    )
    preview_src = getattr(acct, "draft_preview", None) or getattr(acct, "outreach_draft", None)
    preview = (preview_src or "").strip()[:140] if has_draft else None
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
            draft_preview=preview if has_draft else None,
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
    from app.services.cal_draft_guard import draft_needs_regeneration

    acct = db.query(CrmAccount).filter(CrmAccount.id == account_id).first()
    if not acct:
        raise HTTPException(status_code=404, detail="CRM account not found")

    company = (
        db.query(Company).filter(Company.id == acct.company_id).first()
        if acct.company_id
        else None
    )
    from app.services.brand import is_stagegate_branded

    if is_stagegate_branded(company, acct):
        raise HTTPException(
            status_code=409,
            detail=(
                "This is a StageGate (onstage.bot) account — not part of Ready For Robots "
                "buyer outreach. Work StageGate OEM leads on onstage.bot."
            ),
        )

    legacy_repaired = False
    needs, _ = draft_needs_regeneration(
        acct.outreach_draft,
        account_type=getattr(acct, "account_type", None) or "buyer",
    )
    if needs and company:
        from app.services.agent_messaging import pick_buyer_variant, resolve_buyer_variant
        from app.services.cal_autonomy import format_cal_draft_storage

        variant_id = resolve_buyer_variant(company, acct)
        if variant_id is None and (getattr(acct, "account_type", None) or "buyer") == "buyer":
            variant_id = pick_buyer_variant(company.id)
        subject, draft_body = _cal_draft_for_company(
            company, fresh=True, variant_id=variant_id
        )
        acct.outreach_draft = format_cal_draft_storage(subject, draft_body)
        db.commit()
        legacy_repaired = True

    return {
        "crm_account_id": str(acct.id),
        "draft_full": acct.outreach_draft,
        "contact_email": acct.contact_email,
        "legacy_repaired": legacy_repaired,
    }


class CalDraftPatchIn(BaseModel):
    outreach_draft: Optional[str] = None
    contact_email: Optional[str] = None
    outreach_stage: Optional[str] = None


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
    if body.outreach_draft is not None:
        draft = (body.outreach_draft or "").strip()
        if not draft:
            raise HTTPException(status_code=400, detail="outreach_draft cannot be empty")
        from app.services.cal_draft_guard import is_complete_cal_draft

        ok, reason = is_complete_cal_draft(draft)
        if not ok:
            raise HTTPException(status_code=400, detail=f"Draft incomplete — load full text before saving: {reason}")
        acct.outreach_draft = draft
    if body.contact_email is not None:
        from app.services.email_address import normalize_recipient_email, recipient_email_error

        raw_contact = (body.contact_email or "").strip()
        if raw_contact:
            normalized = normalize_recipient_email(raw_contact)
            if not normalized:
                raise HTTPException(status_code=400, detail=recipient_email_error(raw_contact))
            acct.contact_email = normalized
        else:
            acct.contact_email = None
    if body.outreach_stage is not None:
        acct.outreach_stage = body.outreach_stage.strip() or None
    db.commit()
    db.refresh(acct)
    return {
        "crm_account_id": str(acct.id),
        "draft_full": acct.outreach_draft,
        "contact_email": acct.contact_email,
        "outreach_stage": acct.outreach_stage,
    }


@router.post("/cal/approve-one/{account_id}")
def cal_approve_one(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Mark one Cal draft approved and ready to send."""
    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")
    acct = db.query(CrmAccount).filter(
        CrmAccount.id == account_id,
        CrmAccount.team_id == team.id,
    ).first()
    if not acct:
        raise HTTPException(status_code=404, detail="CRM account not found")
    if not acct.outreach_draft:
        raise HTTPException(status_code=400, detail="No draft to approve")
    if acct.outreach_sent_at:
        raise HTTPException(status_code=400, detail="Already sent")
    acct.outreach_stage = "draft_approved"
    db.commit()
    _invalidate_admin_caches()
    return {"approved": True, "crm_account_id": str(acct.id)}


@router.post("/cal/approve-all")
def cal_approve_all(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Approve all unsent Cal drafts on the admin outreach team."""
    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")
    rows = db.query(CrmAccount).filter(
        CrmAccount.team_id == team.id,
        CrmAccount.outreach_draft.isnot(None),
        CrmAccount.outreach_sent_at.is_(None),
    ).all()
    approved = 0
    for acct in rows:
        if (acct.outreach_stage or "") not in ("draft_approved", "approved"):
            acct.outreach_stage = "draft_approved"
            approved += 1
    db.commit()
    _invalidate_admin_caches()
    return {"approved": approved, "total_unsent_drafted": len(rows)}


def _cal_draft_is_sendable(acct: CrmAccount) -> bool:
    if not acct.outreach_draft or acct.outreach_sent_at:
        return False
    if (acct.outreach_stage or "") not in ("draft_approved", "approved"):
        return False
    return bool((acct.contact_email or "").strip())


def _empty_cal_draft_payload(*, include_prospects: bool) -> dict[str, Any]:
    return {
        "summary": {
            "total": 0, "hot": 0, "warm": 0, "drafted": 0, "unsent_drafted": 0,
            "sendable": 0, "no_email": 0, "pending_draft": 0, "sent": 0,
            "approved": 0, "needs_approval": 0,
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
    fast_summary: bool = False,
) -> dict[str, Any]:
    """Return HOT+WARM prospects with Cal draft state on the admin outreach team."""
    team = _admin_team(db, admin_uid, admin_email)
    companies = _hot_warm_companies_fast(db) if fast_summary else _hot_warm_companies(db)
    company_ids = [c.id for c, _, _ in companies]
    accounts_by_company = _crm_accounts_for_companies(db, company_ids, team_id=team.id)

    account_ids = [a.id for a in accounts_by_company.values()]
    delivery_by_account = _latest_delivery_by_account(db, account_ids)

    summary_rows: list[dict[str, Any]] = []
    for company, score, tier in companies:
        acct = accounts_by_company.get(company.id)
        has_draft = bool(acct and acct.has_draft)
        if fast_summary:
            stored = (getattr(acct, "contact_email", None) or "").strip() or None
            effective = stored
        else:
            effective, _, _, _ = _cal_contact_fields(company, acct)
        summary_rows.append({
            "tier": tier,
            "has_draft": has_draft,
            "outreach_sent_at": acct.outreach_sent_at.isoformat() if acct and acct.outreach_sent_at else None,
            "contact_email": effective,
            "email_delivery_status": delivery_by_account.get(str(acct.id)) if acct else None,
            "outreach_stage": acct.outreach_stage if acct else None,
            "account_type": getattr(acct, "account_type", None) or "buyer",
        })

    total = len(summary_rows)
    hot = sum(1 for r in summary_rows if r["tier"] == "HOT")
    warm = sum(1 for r in summary_rows if r["tier"] == "WARM")
    drafted = sum(1 for r in summary_rows if r["has_draft"])
    sent = sum(1 for r in summary_rows if r["outreach_sent_at"])
    unsent_drafted = sum(1 for r in summary_rows if r["has_draft"] and not r["outreach_sent_at"])
    approved = sum(
        1 for r in summary_rows
        if r["has_draft"] and not r["outreach_sent_at"]
        and _cal_is_approved(r["outreach_stage"])
    )
    needs_approval = 0 if not cal_manual_approval_required() else sum(
        1 for r in summary_rows
        if r["has_draft"] and not r["outreach_sent_at"]
        and not _cal_is_approved(r["outreach_stage"])
    )
    sendable = sum(
        1 for r in summary_rows
        if r["has_draft"] and not r["outreach_sent_at"] and r["contact_email"]
        and _cal_is_approved(r["outreach_stage"])
    )
    no_email = sum(1 for r in summary_rows if r["has_draft"] and not r["outreach_sent_at"] and not r["contact_email"])
    opened = sum(1 for r in summary_rows if r["email_delivery_status"] in ("opened", "clicked"))
    clicked = sum(1 for r in summary_rows if r["email_delivery_status"] == "clicked")
    replied = sum(1 for r in summary_rows if r["outreach_stage"] == "replied")
    buyers = sum(1 for r in summary_rows if (r.get("account_type") or "buyer") == "buyer")
    vendors = sum(1 for r in summary_rows if r.get("account_type") == "vendor")

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
                fast_contact=fast_summary,
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
            "approved": approved,
            "needs_approval": needs_approval,
            "sendable": sendable,
            "no_email": no_email,
            "pending_draft": total - drafted,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "buyers": buyers,
            "vendors": vendors,
            "scope": "HOT/WARM",
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
    fast_summary: bool = Query(
        False,
        description="Skip slow email inference + delivery lookups for counts-only refresh",
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
                fast_summary=fast_summary or not include_prospects,
            )

    timeout = 20 if (not include_prospects or fast_summary) else 45
    try:
        return run_db(_run, timeout_sec=timeout, label="cal/draft-status")
    except TimeoutError:
        logger.warning("cal/draft-status timed out — returning empty summary")
        return _empty_cal_draft_payload(include_prospects=include_prospects)


@router.get("/cal/queue-summary")
def cal_queue_summary(
    user: dict = Depends(require_admin),
):
    """Fast counts-only Cal queue — avoids 502 on full draft-status."""
    from app.database import SessionLocal
    from app.db_timeout import run_db

    def _run() -> dict[str, Any]:
        with SessionLocal() as db:
            return _build_cal_draft_status_payload(
                db,
                admin_uid=uuid.UUID(user["uid"]),
                admin_email=user.get("email") or "",
                include_draft_bodies=False,
                include_prospects=False,
                prospect_limit=1,
                fast_summary=True,
            )

    try:
        return run_db(_run, timeout_sec=20, label="cal/queue-summary")
    except TimeoutError:
        return _empty_cal_draft_payload(include_prospects=False)


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
        if _skip_stagegate_for_rfr_admin(company):
            skipped += 1
            continue
        try:
            acct = existing.get(company.id)
            if acct and acct.outreach_draft and not body.regenerate:
                from app.services.cal_draft_guard import draft_needs_regeneration

                account_type = getattr(acct, "account_type", None) or "buyer"
                if not draft_needs_regeneration(acct.outreach_draft, account_type=account_type)[0]:
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

            # Do NOT stamp a guessed role inbox onto contact_email at draft time. A stored
            # contact_email short-circuits resolve_outreach_email (returns the untrusted
            # "crm_contact" source) BEFORE it reaches Hunter/Apollo — so a guess written
            # here permanently blocks the verified-contact upgrade and becomes a bounce.
            # Leave it empty; the send gate resolves through the full verified waterfall.

            from app.services.cal_autonomy import format_cal_draft_storage

            # Record which trust-first angle this draft used so the send tag and the
            # weekly learning report stay consistent with the deterministic pick.
            if acct.account_type != "vendor" and (company.crm_metadata or {}).get("outreach_pipeline") != "stagegate":
                from app.services.agent_messaging import pick_buyer_variant

                cmeta = dict(company.crm_metadata or {})
                cmeta["cal_variant_id"] = pick_buyer_variant(company.id)
                company.crm_metadata = cmeta

            acct.outreach_draft = format_cal_draft_storage(subject, draft_body)
            acct.outreach_stage = (
                "draft_approved" if not cal_manual_approval_required() else "draft_ready"
            )
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


@router.get("/cal/activity")
def cal_activity(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_admin),
    limit: int = Query(40, ge=10, le=100),
):
    """Operator timeline: what Cal is doing autonomously + items needing human help."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import desc, func

    from app.models.calendar import CalendarEvent
    from app.models.crm import CrmAccount
    from app.models.outreach import OutreachMessage, OutreachReply
    from app.models.sales_agent import SalesAgentAction, SalesOpportunity
    from app.models.sequences import OutreachSequenceEnrollment
    from app.services.cal_autonomy import get_cal_autonomy_status, resolve_cal_admin_context
    from app.services.cal_ops_monitor import get_cal_ops_monitor

    cap = max(10, min(limit, 100))
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=14)

    autopilot = get_cal_autonomy_status()
    ops = get_cal_ops_monitor(db, limit=15)

    enroll_active = (
        db.query(func.count(OutreachSequenceEnrollment.id))
        .filter(OutreachSequenceEnrollment.status == "active")
        .scalar() or 0
    )
    enroll_due = (
        db.query(func.count(OutreachSequenceEnrollment.id))
        .filter(
            OutreachSequenceEnrollment.status == "active",
            OutreachSequenceEnrollment.next_step_at.isnot(None),
            OutreachSequenceEnrollment.next_step_at <= now,
        )
        .scalar() or 0
    )
    enroll_paused = (
        db.query(func.count(OutreachSequenceEnrollment.id))
        .filter(OutreachSequenceEnrollment.status == "paused")
        .scalar() or 0
    )

    crm_names = {
        str(row.id): row.name
        for row in db.query(CrmAccount.id, CrmAccount.name).limit(2000).all()
    }

    timeline: list[dict] = []

    for msg in (
        db.query(OutreachMessage)
        .filter(OutreachMessage.sent_at.isnot(None), OutreachMessage.sent_at >= since)
        .order_by(desc(OutreachMessage.sent_at))
        .limit(cap)
        .all()
    ):
        identity = (msg.send_identity or "").lower()
        kind = "followup_sent" if identity == "sequence" else "intro_sent"
        body_text = (msg.body_text or "").strip()
        timeline.append({
            "id": str(msg.id),
            "kind": kind,
            "at": msg.sent_at.isoformat() if msg.sent_at else None,
            "title": msg.subject,
            "detail": f"To {msg.to_email}",
            "entity": crm_names.get(str(msg.crm_account_id)) or msg.to_email,
            "to_email": msg.to_email,
            "body_preview": body_text[:500] if body_text else None,
            "body_full": body_text if len(body_text) <= 4000 else None,
            "crm_account_id": str(msg.crm_account_id) if msg.crm_account_id else None,
            "action_url": "/inbox",
        })

    for reply in (
        db.query(OutreachReply)
        .filter(OutreachReply.received_at >= since)
        .order_by(desc(OutreachReply.received_at))
        .limit(cap)
        .all()
    ):
        timeline.append({
            "id": str(reply.id),
            "kind": "reply_received",
            "at": reply.received_at.isoformat() if reply.received_at else None,
            "title": reply.subject or "Inbound reply",
            "detail": (reply.from_email or "unknown sender"),
            "entity": crm_names.get(str(reply.crm_account_id)) or reply.from_email,
            "action_url": "/inbox",
        })

    for action in (
        db.query(SalesAgentAction)
        .filter(SalesAgentAction.created_at >= since)
        .order_by(desc(SalesAgentAction.created_at))
        .limit(cap)
        .all()
    ):
        kind = "auto_reply_sent" if action.status in ("sent", "completed") else "cal_planned_action"
        timeline.append({
            "id": str(action.id),
            "kind": kind,
            "at": (action.updated_at or action.created_at).isoformat() if (action.updated_at or action.created_at) else None,
            "title": action.recommendation or action.action_type.replace("_", " ").title(),
            "detail": action.detected_intent or action.status,
            "entity": action.draft_subject or "Sales agent",
            "action_url": "/sales-console",
        })

    for row in ops.get("assembly_rejections") or []:
        timeline.append({
            "id": str(row.get("id") or row.get("created_at")),
            "kind": "assembly_blocked",
            "at": row.get("created_at"),
            "title": "Assembly blocked send",
            "detail": "; ".join((row.get("issues") or [])[:2]) or row.get("note") or "",
            "entity": row.get("vendor_name") or "Buyer outreach",
            "action_url": "/admin#cal-outreach",
        })

    timeline.sort(key=lambda x: x.get("at") or "", reverse=True)
    timeline = timeline[:cap]

    needs_you: list[dict] = []

    pending_approval = (
        db.query(SalesAgentAction)
        .filter(
            SalesAgentAction.requires_approval.is_(True),
            SalesAgentAction.status.in_(["planned", "draft", "pending", "review", "drafted"]),
        )
        .order_by(desc(SalesAgentAction.updated_at))
        .limit(10)
        .all()
    )
    for action in pending_approval:
        needs_you.append({
            "kind": "approval_required",
            "title": action.recommendation or "Cal action needs approval",
            "detail": action.detected_intent or action.action_type,
            "action_url": "/sales-console",
        })

    meeting_opps = (
        db.query(SalesOpportunity)
        .filter(SalesOpportunity.current_stage.in_(["meeting_requested", "qualified"]))
        .order_by(desc(SalesOpportunity.updated_at))
        .limit(8)
        .all()
    )
    scheduled_opp_ids = {
        str(row.sales_opportunity_id)
        for row in db.query(CalendarEvent.sales_opportunity_id)
        .filter(CalendarEvent.sales_opportunity_id.isnot(None))
        .all()
        if row.sales_opportunity_id
    }
    for opp in meeting_opps:
        if str(opp.id) in scheduled_opp_ids:
            continue
        if opp.current_stage != "meeting_requested":
            continue
        needs_you.append({
            "kind": "schedule_meeting",
            "title": f"Schedule meeting — {opp.title or 'Opportunity'}",
            "detail": "Cal replied asking for times — book on calendar when ready",
            "action_url": f"/calendar?sales_opportunity_id={opp.id}",
        })

    for row in ops.get("assembly_rejections") or []:
        needs_you.append({
            "kind": "edit_draft",
            "title": f"Fix draft — {row.get('vendor_name') or 'blocked send'}",
            "detail": "; ".join((row.get("issues") or [])[:2]) or "Assembly rejected copy",
            "action_url": "/admin#cal-outreach",
        })

    sent_recent = sum(1 for row in timeline if row.get("kind") in ("intro_sent", "followup_sent"))
    manual_approval = bool(autopilot.get("manual_approval"))

    pending_cal_approvals: list[dict] = []
    if manual_approval:
        ctx = resolve_cal_admin_context(db)
        if ctx:
            _uid, team = ctx
            for acct in (
                db.query(CrmAccount)
                .filter(
                    CrmAccount.team_id == team.id,
                    CrmAccount.outreach_draft.isnot(None),
                    CrmAccount.outreach_sent_at.is_(None),
                    CrmAccount.outreach_stage.notin_(["draft_approved", "approved"]),
                )
                .order_by(desc(CrmAccount.updated_at))
                .limit(20)
                .all()
            ):
                pending_cal_approvals.append({
                    "crm_account_id": str(acct.id),
                    "company_name": acct.name,
                    "contact_email": acct.contact_email,
                    "outreach_stage": acct.outreach_stage,
                })
                needs_you.insert(0, {
                    "kind": "cal_draft_approval",
                    "title": f"Approve draft — {acct.name}",
                    "detail": acct.contact_email or "No contact email yet",
                    "action_url": "/admin#cal-approvals",
                })

    return {
        "autopilot": autopilot,
        "operator_mode": "approval_required" if manual_approval else "auto_send",
        "sent_recent_count": sent_recent,
        "pending_approval_count": len(pending_cal_approvals),
        "pending_approvals": pending_cal_approvals,
        "sequences": {
            "active": enroll_active,
            "due_now": enroll_due,
            "paused": enroll_paused,
        },
        "timeline": timeline,
        "needs_you": needs_you[:12],
        "capabilities": {
            "draft_autonomous": True,
            "send_autonomous": bool(autopilot.get("enabled")) and not manual_approval,
            "followup_autonomous": True,
            "reply_autonomous": True,
            "meeting_autonomous": False,
            "meeting_note": "Cal classifies meeting requests and asks for times; you confirm on Calendar.",
        },
    }


@router.get("/cal/ops-monitor")
def cal_ops_monitor(
    db: Session = Depends(get_db),
    limit: int = Query(25, ge=1, le=100),
    _user: dict = Depends(require_admin),
):
    from app.services.cal_ops_monitor import get_cal_ops_monitor

    return get_cal_ops_monitor(db, limit=limit)


class CalAutonomyRunBody(BaseModel):
    dry_run: bool = False


@router.post("/cal/autonomy-run")
def cal_autonomy_run(
    body: CalAutonomyRunBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    from app.services.cal_autonomy import run_cal_autonomy_cycle

    return run_cal_autonomy_cycle(
        db,
        dry_run=body.dry_run,
        admin_uid=uuid.UUID(user["uid"]),
        admin_email=user.get("email") or "",
    )


@router.get("/cal/operator-dashboard")
def cal_operator_dashboard(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Unified operator metrics: queue, opportunities, workflow, buyer/vendor split, engagement."""
    from sqlalchemy import desc, func

    from app.api.admin import workflow_actions
    from app.models.crm import CrmAccount
    from app.models.sales_agent import SalesOpportunity
    from app.services.cal_autonomy import cal_buyer_outreach_body, get_cal_autonomy_status

    uid = uuid.UUID(user["uid"])
    team = _admin_team(db, uid, user.get("email") or "")
    cal_payload = _build_cal_draft_status_payload(
        db,
        admin_uid=uid,
        admin_email=user.get("email") or "",
        include_draft_bodies=False,
        include_prospects=False,
        prospect_limit=1,
        fast_summary=True,
    )
    summary = cal_payload.get("summary") or {}

    prospects: list[dict[str, Any]] = []
    sample_company_row = (
        db.query(CrmAccount, Company)
        .join(Company, Company.id == CrmAccount.company_id)
        .filter(CrmAccount.team_id == team.id, CrmAccount.outreach_draft.isnot(None))
        .order_by(desc(CrmAccount.updated_at))
        .first()
    )

    opp_total = db.query(func.count(SalesOpportunity.id)).scalar() or 0
    opp_by_stage = {
        row[0] or "unknown": row[1]
        for row in db.query(SalesOpportunity.current_stage, func.count(SalesOpportunity.id))
        .group_by(SalesOpportunity.current_stage)
        .all()
    }

    workflow = workflow_actions(limit=80, db=db)

    sample_company = None
    template_sample: dict[str, Any] = {}
    if sample_company_row:
        acct, company = sample_company_row
        sample_company = {"company_id": company.id, "company_name": company.name}
        subject, body = _cal_draft_for_company(company, fresh=False)
        template_sample = {
            "company_name": company.name,
            "subject": subject,
            "body": body,
            "note": "Template voice is code-defined (agent_messaging.py). Per-lead drafts stored on CRM accounts.",
        }

    return {
        "cal_queue": summary,
        "buyer_vendor": {
            "buyers": int(summary.get("buyers") or 0),
            "vendors": int(summary.get("vendors") or 0),
            "scope": "HOT/WARM",
        },
        "sales_opportunities": {
            "total": int(opp_total),
            "by_stage": opp_by_stage,
        },
        "workflow": {
            "counts": workflow.get("counts"),
            "by_source": workflow.get("by_source"),
            "items": workflow.get("items"),
        },
        "autopilot": get_cal_autonomy_status(),
        "template_sample": template_sample,
        "ai_assistants": [
            {
                "id": "cal_autonomy",
                "name": "Cal autonomy",
                "role": "Drafts HOT/WARM buyer emails, sends on schedule, runs follow-up sequences",
                "review_url": "/admin#cal-outreach",
                "status": "active" if get_cal_autonomy_status().get("enabled") else "paused",
            },
            {
                "id": "cal_assembly",
                "name": "Cal assembly QA",
                "role": "Pre-send copy review — blocks weak buyer–vendor pairings",
                "review_url": "/admin#cal-outreach",
                "status": "active" if get_cal_autonomy_status().get("assembly", {}).get("assembly_required") else "off",
            },
            {
                "id": "sales_agent",
                "name": "Sales agent (Max)",
                "role": "Classifies inbound replies, drafts follow-ups, auto-replies when safe",
                "review_url": "/sales-console",
                "status": "active",
            },
            {
                "id": "lead_research",
                "name": "Lead research agent",
                "role": "Enriches signals and company context for pipeline prioritization",
                "review_url": "/admin#workflow",
                "status": "active",
            },
        ],
    }


@router.get("/cal/template-sample")
def cal_template_sample(
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
    company_id: Optional[int] = Query(None),
):
    """Preview Cal's buyer outreach template for a sample or specific company."""
    from app.models.company import Company

    uid = uuid.UUID(user["uid"])
    if company_id:
        company = db.query(Company).filter(Company.id == company_id).first()
    else:
        companies = _hot_warm_companies(db, limit=1)
        company = companies[0][0] if companies else None
    if not company:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="No sample company in Cal queue")
    subject, body = _cal_draft_for_company(company, fresh=False)
    return {
        "company_id": company.id,
        "company_name": company.name,
        "subject": subject,
        "body": body,
        "storage_format": f"Subject: {subject}\n\n{body}",
        "template_version": os.getenv("CAL_TEMPLATE_VERSION") or "2",
        "editable_note": "Global voice lives in agent_messaging.py. Edit per-lead copy via PATCH /api/admin/cal/draft/{crm_account_id}.",
    }


@router.get("/cal/variant-preview/{company_id}")
def cal_variant_preview(
    company_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Preview all buyer trust-first angles (subject + body) for one company."""
    from app.models.company import Company
    from app.services.agent_messaging import (
        BUYER_VARIANTS,
        build_buyer_variant_body,
        build_context_reason,
        buyer_variant_subject,
        pick_buyer_variant,
    )
    from app.services.brand import is_stagegate_branded
    from app.services.lead_signal_display import strip_extraction_artifacts

    company = (
        db.query(Company)
        .options(joinedload(Company.signals))
        .filter(Company.id == company_id)
        .first()
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if is_stagegate_branded(company):
        raise HTTPException(
            status_code=400,
            detail="Variant preview is buyer-only. StageGate/vendor accounts do not use buyer trust-first angles.",
        )

    name = (company.name or "your team").strip()
    industry = (company.industry or "your industry").strip()
    blob_parts = [
        strip_extraction_artifacts(getattr(s, "signal_text", None))
        for s in list(company.signals or [])[:12]
    ]
    signal_blob = " ".join(p for p in blob_parts if p).strip()
    reason = build_context_reason(name, signal_blob)

    stored_variant = None
    meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    if meta.get("cal_variant_id") in BUYER_VARIANTS:
        stored_variant = str(meta.get("cal_variant_id"))
    selected_variant = stored_variant or pick_buyer_variant(getattr(company, "id", None))

    previews: list[dict[str, str]] = []
    for vid in BUYER_VARIANTS:
        previews.append(
            {
                "variant_id": vid,
                "subject": buyer_variant_subject(name, industry, vid),
                "body": build_buyer_variant_body(name, industry, vid, reason=reason),
            }
        )

    return {
        "company_id": company.id,
        "company_name": company.name,
        "industry": company.industry,
        "selected_variant": selected_variant,
        "stored_variant": stored_variant,
        "reason": reason,
        "variants": previews,
    }


class CalAutonomyToggleBody(BaseModel):
    enabled: bool


@router.post("/cal/autonomy-toggle")
def cal_autonomy_toggle(
    body: CalAutonomyToggleBody,
    _user: dict = Depends(require_admin),
):
    """Runtime on/off for Cal worker autopilot (Redis override; env default remains on Fly)."""
    from app.services.cal_autonomy import get_cal_autonomy_status, set_cal_autonomy_runtime_override

    if not set_cal_autonomy_runtime_override(body.enabled):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="Autopilot toggle failed — could not persist runtime flag.",
        )
    return get_cal_autonomy_status()


class CalDailyDigestSendBody(BaseModel):
    force: bool = False
    period_hours: int = 24


@router.post("/cal/daily-digest-send")
def cal_daily_digest_send(
    body: CalDailyDigestSendBody,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Send the plain-text Cal daily activity email now (for testing or catch-up)."""
    from app.services.cal_daily_digest import send_cal_daily_digest

    return send_cal_daily_digest(db, period_hours=body.period_hours, force=body.force)


class CommunicationLearningSendBody(BaseModel):
    force: bool = True
    period_hours: int = 168
    preview_only: bool = False


@router.post("/communication-learning-send")
def communication_learning_send(
    body: CommunicationLearningSendBody,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Build (and optionally email) the weekly per-angle learning report now."""
    from app.services.communication_learning_report import (
        build_communication_learning_report,
        render_communication_learning_text,
        send_communication_learning_report,
    )

    if body.preview_only:
        report = build_communication_learning_report(db, period_hours=body.period_hours)
        return {
            "sent": False,
            "preview": True,
            "totals": report.get("totals"),
            "variants": report.get("variants"),
            "body_text": render_communication_learning_text(report),
        }
    return send_communication_learning_report(
        db, period_hours=body.period_hours, force=body.force
    )


@router.get("/communication-learning")
def communication_learning_report(
    period_hours: int = 168,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_admin),
):
    """Live per-angle learning scoreboard for the admin UI (reply rate by angle
    and by industry). Read-only; no email is sent."""
    from app.services.communication_learning_report import build_communication_learning_report

    ph = max(1, min(int(period_hours or 168), 24 * 90))
    return build_communication_learning_report(db, period_hours=ph)


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
    from app.services.cal_outreach_send import enroll_cal_followup, parse_cal_draft, send_cal_intro_email
    from app.services.resend_email import ResendEmailError

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
    skipped_duplicate = 0
    errors: list[dict[str, Any]] = []
    # Guard against duplicate Company rows (same recipient) inside a single run —
    # otherwise one inbox can receive the same intro several times.
    seen_recipients: set[str] = set()
    now = datetime.now(timezone.utc)

    from app.services.lead_enrichment import (
        address_previously_bounced,
        outreach_recipient_trusted,
        resolve_outreach_email,
        verify_email_deliverable,
    )

    for company, score, tier in companies:
        if sent_count >= body.limit:
            break
        if body.tier_filter != "all" and tier != body.tier_filter:
            continue

        if _skip_stagegate_for_rfr_admin(company):
            skipped_no_draft += 1
            continue

        acct = accounts.get(company.id)
        if not acct or not acct.outreach_draft:
            skipped_no_draft += 1
            continue
        from app.services.cal_draft_guard import is_complete_cal_draft

        draft_ok, draft_reason = is_complete_cal_draft(acct.outreach_draft)
        if not draft_ok:
            skipped_no_draft += 1
            errors.append({
                "company_id": company.id,
                "name": company.name,
                "error": f"Incomplete draft — run Draft all pending or regenerate: {draft_reason}",
            })
            continue
        if acct.outreach_sent_at:
            skipped_already_sent += 1
            continue
        if (acct.outreach_stage or "") not in ("draft_approved", "approved") and cal_manual_approval_required():
            skipped_no_draft += 1
            errors.append({
                "company_id": company.id,
                "name": company.name,
                "error": "Draft not approved — approve in Step 2 before sending",
            })
            continue

        # Always resolve so we know the email SOURCE — a stored acct.contact_email may be a
        # laundered name-guess from a prior cycle, and using it directly bypassed the guard.
        to_email, email_source, _title = resolve_outreach_email(company, acct, use_apollo=True)
        from app.services.email_address import normalize_recipient_email, recipient_email_error

        to_email = normalize_recipient_email(to_email)
        if not to_email:
            errors.append({
                "company_id": company.id,
                "name": company.name,
                "error": recipient_email_error(acct.contact_email) or "Invalid recipient email format",
            })
            continue

        recipient_key = to_email.strip().lower()
        if recipient_key in seen_recipients:
            skipped_duplicate += 1
            continue
        seen_recipients.add(recipient_key)

        # Same hard gate as autopilot: trusted source, not previously bounced, deliverable.
        trusted, trust_reason = outreach_recipient_trusted(company, acct, to_email, email_source)
        if not trusted:
            skipped_unverified += 1
            errors.append({
                "company_id": company.id,
                "name": company.name,
                "error": f"Unverified recipient skipped ({trust_reason})",
                "email_source": email_source,
            })
            continue
        if address_previously_bounced(db, to_email):
            skipped_unverified += 1
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

        # CC only a peer that clears the SAME trust + suppression + deliverability gate as
        # the primary (guessed role-inbox CCs were a dominant bounce class).
        domain = normalize_website_domain(company.website or acct.website)
        cc_email = None
        for _cc in infer_cc_outreach_emails(domain, company.industry, primary=to_email):
            cc_trusted, _ = outreach_recipient_trusted(company, acct, _cc, "cc_inferred")
            if not cc_trusted or address_previously_bounced(db, _cc):
                continue
            cc_ok, _ = verify_email_deliverable(_cc)
            if cc_ok:
                cc_email = _cc
                break

        # Build subject from draft first line or fallback
        subject, body_text = parse_cal_draft(acct.outreach_draft, company.name or "Unknown")

        if body.dry_run:
            sent_count += 1
            continue

        try:
            from app.services.agent_messaging import resolve_buyer_variant

            variant_id = resolve_buyer_variant(company, acct)
            send_cal_intro_email(
                db,
                acct=acct,
                company=company,
                team_id=team.id,
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                cc=[cc_email] if cc_email else None,
                sender_user_id=uid,
                idempotency_key=f"cal-bulk-{acct.id}",
                send_identity="cal",
                variant_id=variant_id,
            )
            sent_count += 1
            enroll_cal_followup(db, team_id=team.id, crm_account_id=acct.id, variant_id=variant_id)
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
        "skipped_duplicate": skipped_duplicate,
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


def _cal_resolve_send_to_email(company: Company | None, acct: CrmAccount) -> tuple[str | None, str | None]:
    """Normalize CRM/inferred recipient; return (email, error_message)."""
    from app.services.email_address import normalize_recipient_email, recipient_email_error
    from app.services.lead_enrichment import resolve_outreach_email

    stored = normalize_recipient_email(acct.contact_email)
    if stored:
        return stored, None

    to_raw, _src, _title = resolve_outreach_email(
        company or Company(name=acct.name),
        acct,
        use_apollo=True,
    )
    normalized = normalize_recipient_email(to_raw)
    if normalized:
        return normalized, None
    if (to_raw or "").strip():
        return None, recipient_email_error(to_raw)
    return None, "No recipient email — enter name@company.com in the contact field."


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
    from app.services.cal_outreach_send import enroll_cal_followup, parse_cal_draft, send_cal_intro_email
    from app.services.resend_email import ResendEmailError
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
    if (acct.outreach_stage or "") not in ("draft_approved", "approved") and cal_manual_approval_required():
        raise HTTPException(status_code=400, detail="Draft not approved — approve before sending")

    if (body.outreach_draft or "").strip():
        from app.services.cal_draft_guard import is_complete_cal_draft

        draft_candidate = body.outreach_draft.strip()
        ok, reason = is_complete_cal_draft(draft_candidate)
        if not ok:
            raise HTTPException(status_code=400, detail=f"Draft incomplete — wait for full draft to load: {reason}")
        acct.outreach_draft = draft_candidate
    if body.contact_email is not None:
        from app.services.email_address import normalize_recipient_email, recipient_email_error

        raw_contact = body.contact_email.strip()
        if raw_contact:
            normalized = normalize_recipient_email(raw_contact)
            if not normalized:
                raise HTTPException(status_code=400, detail=recipient_email_error(raw_contact))
            acct.contact_email = normalized
        else:
            acct.contact_email = None
        db.flush()

    company = db.query(Company).filter(Company.id == acct.company_id).first() if acct.company_id else None
    from app.services.lead_enrichment import (
        address_previously_bounced,
        outreach_recipient_trusted,
        verify_email_deliverable,
    )

    to_email, email_err = _cal_resolve_send_to_email(company, acct)
    if not to_email:
        raise HTTPException(status_code=400, detail=email_err or "No recipient email")

    # Never re-send to an address that already bounced/complained — a dead mailbox stays
    # dead and re-hitting it just burns sender reputation.
    if address_previously_bounced(db, to_email):
        raise HTTPException(
            status_code=400,
            detail=f"{to_email} previously bounced/complained and is suppressed — add a verified contact instead.",
        )

    if not _cal_should_skip_verification(body.skip_verification):
        ok, reason = verify_email_deliverable(to_email)
        if not ok:
            raise HTTPException(status_code=400, detail=f"Email failed verification ({reason}): {to_email}")

    from app.services.cal_draft_guard import is_complete_cal_draft, parse_cal_draft_or_raise

    ok, reason = is_complete_cal_draft(acct.outreach_draft)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Cannot send incomplete draft: {reason}")

    # CC only a peer that clears the same trust + suppression + deliverability gate as the
    # primary (guessed role-inbox CCs were a dominant bounce class and a CC bounce flags the
    # whole message bounced).
    domain = normalize_website_domain((company.website if company else None) or acct.website)
    industry = (company.industry if company else None) or acct.industry
    cc_email = None
    for _cc in infer_cc_outreach_emails(domain, industry, primary=to_email):
        cc_trusted, _ = outreach_recipient_trusted(company, acct, _cc, "cc_inferred") if company else (False, "no-company")
        if not cc_trusted or address_previously_bounced(db, _cc):
            continue
        cc_ok, _ = verify_email_deliverable(_cc)
        if cc_ok:
            cc_email = _cc
            break
    try:
        subject, body_text = parse_cal_draft_or_raise(acct.outreach_draft, acct.name or "Unknown")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        from app.services.agent_messaging import resolve_buyer_variant

        variant_id = resolve_buyer_variant(company, acct)
        send_cal_intro_email(
            db,
            acct=acct,
            company=company,
            team_id=team.id,
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            cc=[cc_email] if cc_email else None,
            sender_user_id=uid,
            idempotency_key=f"cal-single-{acct.id}",
            send_identity="cal",
            variant_id=variant_id,
        )
    except ResendEmailError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    enroll_cal_followup(db, team_id=team.id, crm_account_id=acct.id, variant_id=variant_id)
    now = datetime.now(timezone.utc)
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
    hints: list[str] = []
    if webhook_secret_set and inbound_secret_set:
        hints.append(
            "Inbound replies: Resend → Inbound → "
            "https://ready-2-robot.fly.dev/api/webhooks/resend/inbound (email.received)"
        )
        hints.append(
            "Opens/clicks: Resend → Webhooks → add endpoint "
            "https://ready-2-robot.fly.dev/api/webhooks/resend/delivery "
            "with email.sent, email.delivered, email.opened, email.clicked, email.bounced"
        )

    sent_30d = status_counts.get("sent", 0) + status_counts.get("delivered", 0)
    opened_30d = status_counts.get("opened", 0)
    if sent_30d > 10 and opened_30d == 0 and webhook_secret_set:
        issues.append(
            f"{sent_30d} emails sent in 30d but 0 opens tracked — confirm the delivery webhook URL "
            "in Resend points to /api/webhooks/resend/delivery (not only inbound)"
        )

    from app.services.stagegate_voice import STAGEGATE_OUTREACH_RULES

    return {
        "config": {
            "from_email": from_email or None,
            "reply_to": reply_to or None,
            "api_key_set": api_key_set,
            "delivery_webhook_configured": webhook_secret_set,
            "inbound_webhook_configured": inbound_secret_set,
            "webhook_urls": {
                "delivery": "https://ready-2-robot.fly.dev/api/webhooks/resend/delivery",
                "inbound": "https://ready-2-robot.fly.dev/api/webhooks/resend/inbound",
            },
            "resend_setup": {
                "delivery_events": [
                    "email.sent",
                    "email.delivered",
                    "email.opened",
                    "email.clicked",
                    "email.bounced",
                    "email.complained",
                ],
                "inbound_events": ["email.received"],
                "delivery_secret_env": "RESEND_WEBHOOK_SECRET",
                "inbound_secret_env": "RESEND_INBOUND_WEBHOOK_SECRET",
            },
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
        "hints": hints,
        "health": "ok" if not issues else ("warn" if len(issues) <= 2 else "error"),
    }
