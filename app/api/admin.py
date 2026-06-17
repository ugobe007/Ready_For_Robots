"""
Admin API
=========
Endpoints for the Ready for Robots admin panel.

  GET  /api/admin/stats              — system counts + recent activity
  POST /api/admin/import/urls        — bulk-import URLs as scrape targets
  POST /api/admin/import/companies   — bulk-import company records (JSON)
  GET  /api/admin/scrape/targets     — list all registered scrape targets
  POST /api/admin/scrape/trigger     — manually trigger a scraper run
  POST /api/admin/leads/refresh-inference — re-run inference on top pipeline companies
  POST /api/admin/leads/enrich-agent — AI agent enriches leads + grows learned ontology
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import Any, Callable, List, Optional
import time

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.api.auth_deps import require_admin

router = APIRouter(dependencies=[Depends(require_admin)])

# Short TTL cache — admin dashboard fires many count queries on every load.
_ADMIN_STATS_CACHE: tuple[float, dict] | None = None
_DAILY_BRIEF_CACHE: tuple[float, dict] | None = None
_ADMIN_CACHE_TTL = 60.0


def _admin_cache_get(cache: tuple[float, dict] | None) -> dict | None:
    if cache is None:
        return None
    ts, data = cache
    if time.monotonic() - ts < _ADMIN_CACHE_TTL:
        return data
    return None


def _admin_cache_set(data: dict) -> tuple[float, dict]:
    return (time.monotonic(), data)


def _industry_display(raw):
    """Public-facing: never expose 'Unknown'; use 'New' (unclassified)."""
    s = (raw or "").strip()
    return s if s and s.lower() not in ("unknown", "other") else "New"


def _iso(value):
    return value.isoformat() if value else None


def _short_text(value: Optional[str], limit: int = 220) -> Optional[str]:
    if not value:
        return None
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _action_state(status: Optional[str], requires_approval: bool = False) -> str:
    raw = (status or "").lower()
    if requires_approval and raw in {"planned", "draft", "drafted", "pending", "review"}:
        return "needs_approval"
    if raw in {"queued", "scheduled", "pending", "draft_approved"}:
        return "queued"
    if raw in {"running", "processing", "in_progress", "started"}:
        return "in_process"
    if raw in {"planned", "draft", "drafted", "new", "in_app"}:
        return "needs_review"
    if raw in {"sent", "completed", "done", "success", "read"}:
        return "completed"
    if raw in {"failed", "error", "rejected", "cancelled"}:
        return "failed"
    return raw or "unknown"


def _workflow_item(
    *,
    item_id: Any,
    source: str,
    title: str,
    status: Optional[str],
    created_at=None,
    updated_at=None,
    description: Optional[str] = None,
    owner: Optional[str] = None,
    entity: Optional[str] = None,
    priority: str = "normal",
    requires_approval: bool = False,
    next_action_label: Optional[str] = None,
    next_action_url: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    state = _action_state(status, requires_approval=requires_approval)
    return {
        "id": str(item_id),
        "source": source,
        "title": title,
        "description": _short_text(description),
        "status": status or state,
        "state": state,
        "priority": priority,
        "requires_approval": requires_approval,
        "owner": owner,
        "entity": entity,
        "next_action_label": next_action_label,
        "next_action_url": next_action_url,
        "created_at": _iso(created_at),
        "updated_at": _iso(updated_at),
        "metadata": metadata or {},
    }


def _safe_collect(
    collector: Callable[[], list[dict]],
    *,
    source: str,
    errors: list[dict],
) -> list[dict]:
    try:
        return collector()
    except Exception as exc:
        errors.append({"source": source, "detail": str(exc)})
        return []


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """System-wide counts and recent activity with business metrics."""
    global _ADMIN_STATS_CACHE
    cached = _admin_cache_get(_ADMIN_STATS_CACHE)
    if cached is not None:
        return cached
    companies = db.query(func.count(Company.id)).scalar() or 0
    signals   = db.query(func.count(Signal.id)).scalar()  or 0
    scored    = db.query(func.count(Score.id)).scalar()    or 0

    # Calculate business metrics
    hot_leads = db.query(Score).filter(Score.overall_intent_score >= 80).count()
    avg_score = db.query(func.avg(Score.overall_intent_score)).scalar() or 0
    
    # Estimated pipeline value ($50K per hot lead)
    pipeline_value = hot_leads * 50000

    industries = (
        db.query(Company.industry, func.count(Company.id).label("count"))
        .group_by(Company.industry)
        .order_by(desc("count"))
        .limit(8)
        .all()
    )

    sig_types = (
        db.query(Signal.signal_type, func.count(Signal.id).label("count"))
        .group_by(Signal.signal_type)
        .order_by(desc("count"))
        .all()
    )

    recent = (
        db.query(Company)
        .order_by(desc(Company.created_at))
        .limit(10)
        .all()
    )

    result = {
        "totals": {
            "companies": companies,
            "signals":   signals,
            "scored":    scored,
        },
        "pipeline_value": pipeline_value,
        "conversion_metrics": {
            "hot_rate": round((hot_leads / max(companies, 1)) * 100, 1),
            "avg_score": round(avg_score, 1),
        },
        "scraper_health": {
            "active": 5,  # Number of active scrapers
            "success_rate": 92,  # Mock data - can be enhanced
        },
        "database": {
            "size_mb": 156,  # Mock data - can query actual DB size
            "tables": 5,
        },
        "performance": {
            "cache_hit_rate": 85,
        },
        "by_industry": [
            {"industry": _industry_display(r[0]), "count": r[1]} for r in industries
        ],
        "by_signal_type": [
            {"signal_type": r[0], "count": r[1]} for r in sig_types
        ],
        "recent_companies": [
            {
                "id":       c.id,
                "name":     c.name,
                "industry": _industry_display(c.industry),
                "source":   c.source,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in recent
        ],
    }
    _ADMIN_STATS_CACHE = _admin_cache_set(result)
    return result


# ── Daily brief ───────────────────────────────────────────────────────────────

@router.get("/daily-brief")
def daily_brief(db: Session = Depends(get_db)):
    """Operator daily brief: today's intake, outreach activity, and next steps."""
    global _DAILY_BRIEF_CACHE
    cached = _admin_cache_get(_DAILY_BRIEF_CACHE)
    if cached is not None:
        return cached
    from datetime import datetime, timezone

    from app.models.crm import CrmAccount
    from app.models.lead_research import LeadResearchUpdate
    from app.models.outreach import OutreachMessage
    from app.models.sales_agent import SalesAgentAction
    from app.models.scout_chat import ScoutActivation

    day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    warm_threshold = 45.0
    sent_statuses = ["sent", "delivered", "opened", "clicked", "replied"]

    new_companies = (
        db.query(func.count(Company.id))
        .filter(Company.created_at >= day_start)
        .scalar() or 0
    )
    new_signals = (
        db.query(func.count(Signal.id))
        .filter(Signal.created_at >= day_start)
        .scalar() or 0
    )
    new_hot_warm = (
        db.query(func.count(Company.id))
        .join(Score, Score.company_id == Company.id)
        .filter(Company.created_at >= day_start, Score.overall_intent_score >= warm_threshold)
        .scalar() or 0
    )

    emails_sent_today = (
        db.query(func.count(OutreachMessage.id))
        .filter(OutreachMessage.sent_at >= day_start, OutreachMessage.status.in_(sent_statuses))
        .scalar() or 0
    )
    emails_sent_total = (
        db.query(func.count(OutreachMessage.id))
        .filter(OutreachMessage.status.in_(sent_statuses))
        .scalar() or 0
    )

    unsent_drafted = (
        db.query(func.count(CrmAccount.id))
        .filter(CrmAccount.outreach_draft.isnot(None), CrmAccount.outreach_sent_at.is_(None))
        .scalar() or 0
    )
    sendable = (
        db.query(func.count(CrmAccount.id))
        .filter(
            CrmAccount.outreach_draft.isnot(None),
            CrmAccount.outreach_sent_at.is_(None),
            CrmAccount.contact_email.isnot(None),
            CrmAccount.contact_email != "",
        )
        .scalar() or 0
    )
    drafts_created_today = (
        db.query(func.count(CrmAccount.id))
        .filter(CrmAccount.outreach_draft.isnot(None), CrmAccount.updated_at >= day_start)
        .scalar() or 0
    )

    scout_drafted = (
        db.query(func.count(ScoutActivation.id))
        .filter(ScoutActivation.status == "drafted")
        .scalar() or 0
    )
    research_pending = (
        db.query(func.count(LeadResearchUpdate.id))
        .filter(LeadResearchUpdate.status.in_(["new", "pending", "review"]))
        .scalar() or 0
    )
    needs_approval = (
        db.query(func.count(SalesAgentAction.id))
        .filter(
            SalesAgentAction.requires_approval.is_(True),
            SalesAgentAction.status.in_(["planned", "draft", "pending", "review", "drafted"]),
        )
        .scalar() or 0
    )
    hot_unsent = (
        db.query(func.count(CrmAccount.id))
        .join(Company, Company.id == CrmAccount.company_id)
        .join(Score, Score.company_id == Company.id)
        .filter(
            Score.overall_intent_score >= 75,
            CrmAccount.outreach_sent_at.is_(None),
        )
        .scalar() or 0
    )

    next_steps: list[dict] = []

    def add_step(label: str, count: int, href: str, priority: str = "medium") -> None:
        if count > 0:
            next_steps.append({"label": label, "count": count, "href": href, "priority": priority})

    add_step("Send Cal drafts ready to go", sendable, "/admin#cal-outreach", "high")
    add_step("Review unsent Cal drafts", unsent_drafted, "/admin#cal-outreach", "high")
    add_step("HOT leads not yet emailed", hot_unsent, "/admin#cal-outreach", "high")
    add_step("Sales actions need approval", needs_approval, "/sales-console", "high")
    add_step("SIGNAL drafts awaiting send", scout_drafted, "/admin#workflow", "medium")
    add_step("Research updates to review", research_pending, "/pipeline", "medium")
    if new_hot_warm > 0:
        add_step("New HOT/WARM companies today", new_hot_warm, "/pipeline", "medium")

    priority_rank = {"high": 0, "medium": 1, "low": 2}
    next_steps.sort(key=lambda s: priority_rank.get(s["priority"], 2))

    brief = {
        "date": day_start.date().isoformat(),
        "metrics": {
            "new_companies_today": new_companies,
            "new_signals_today": new_signals,
            "new_hot_warm_today": new_hot_warm,
            "drafts_created_today": drafts_created_today,
            "unsent_drafted": unsent_drafted,
            "sendable": sendable,
            "emails_sent_today": emails_sent_today,
            "emails_sent_total": emails_sent_total,
            "scout_drafted": scout_drafted,
            "needs_approval": needs_approval,
            "research_pending": research_pending,
        },
        "next_steps": next_steps,
    }
    _DAILY_BRIEF_CACHE = _admin_cache_set(brief)
    return brief


@router.get("/workflow/actions")
def workflow_actions(limit: int = 80, db: Session = Depends(get_db)):
    """Unified operator queue for AI agent, outreach, research, and notification work."""
    from app.models.crm import CrmAccount
    from app.models.lead_research import LeadResearchUpdate, UserNotification
    from app.models.outreach import OutreachMessage
    from app.models.robot_company import RobotCompany
    from app.models.sales_agent import SalesAgentAction, SalesOpportunity
    from app.models.supply_outreach import SupplyOutreachMessage

    cap = max(10, min(limit, 200))
    errors: list[dict] = []

    crm_names = {
        str(row.id): row.name
        for row in db.query(CrmAccount.id, CrmAccount.name).limit(1000).all()
    }
    company_names = {
        row.id: row.name
        for row in db.query(Company.id, Company.name).limit(2000).all()
    }
    robot_names = {
        row.id: row.company_name
        for row in db.query(RobotCompany.id, RobotCompany.company_name).limit(1000).all()
    }
    opportunities = {
        str(row.id): row
        for row in db.query(SalesOpportunity).order_by(desc(SalesOpportunity.updated_at)).limit(1000).all()
    }

    def collect_sales_actions() -> list[dict]:
        rows = (
            db.query(SalesAgentAction)
            .order_by(desc(SalesAgentAction.updated_at), desc(SalesAgentAction.created_at))
            .limit(cap)
            .all()
        )
        items: list[dict] = []
        for action in rows:
            opp = opportunities.get(str(action.sales_opportunity_id))
            entity = opp.title if opp else "Sales opportunity"
            items.append(_workflow_item(
                item_id=action.id,
                source="sales_agent",
                title=action.recommendation or action.action_type.replace("_", " ").title(),
                description=action.draft_subject or action.error,
                status=action.status,
                created_at=action.created_at,
                updated_at=action.updated_at,
                entity=entity,
                priority="high" if action.requires_approval or action.risk_level in {"medium", "high"} else "normal",
                requires_approval=bool(action.requires_approval),
                next_action_label="Review in Sales Console",
                next_action_url="/sales-console",
                metadata={
                    "risk_level": action.risk_level,
                    "intent": action.detected_intent,
                    "opportunity_id": str(action.sales_opportunity_id),
                    "resend_id": action.resend_id,
                },
            ))
        return items

    def collect_buyer_outreach() -> list[dict]:
        rows = (
            db.query(OutreachMessage)
            .order_by(desc(OutreachMessage.updated_at), desc(OutreachMessage.created_at))
            .limit(cap)
            .all()
        )
        return [
            _workflow_item(
                item_id=row.id,
                source="buyer_outreach",
                title=row.subject,
                description=f"To {row.to_email}",
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
                entity=crm_names.get(str(row.crm_account_id)) or company_names.get(row.company_id) or "Buyer lead",
                priority="high" if _action_state(row.status) in {"queued", "failed"} else "normal",
                next_action_label="Open CRM",
                next_action_url="/crm",
                metadata={
                    "to_email": row.to_email,
                    "crm_account_id": str(row.crm_account_id),
                    "company_id": row.company_id,
                    "resend_id": row.resend_id,
                },
            )
            for row in rows
        ]

    def collect_supply_outreach() -> list[dict]:
        rows = (
            db.query(SupplyOutreachMessage)
            .order_by(desc(SupplyOutreachMessage.updated_at), desc(SupplyOutreachMessage.created_at))
            .limit(cap)
            .all()
        )
        items: list[dict] = []
        for row in rows:
            emails = row.to_emails if isinstance(row.to_emails, list) else []
            items.append(_workflow_item(
                item_id=row.id,
                source="supply_outreach",
                title=row.subject,
                description=f"To {', '.join(emails[:3])}" if emails else "Robot company outreach",
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
                entity=robot_names.get(row.robot_company_id) or "Robot company",
                priority="high" if _action_state(row.status) in {"needs_approval", "queued", "failed"} else "normal",
                requires_approval=_action_state(row.status) == "needs_approval",
                next_action_label="Open Supply Pipeline",
                next_action_url="/supply-pipeline",
                metadata={
                    "robot_company_id": row.robot_company_id,
                    "to_emails": emails,
                    "is_test": bool(row.is_test),
                    "resend_id": row.resend_id,
                },
            ))
        return items

    def collect_research_updates() -> list[dict]:
        rows = (
            db.query(LeadResearchUpdate)
            .order_by(desc(LeadResearchUpdate.updated_at), desc(LeadResearchUpdate.detected_at))
            .limit(cap)
            .all()
        )
        return [
            _workflow_item(
                item_id=row.id,
                source="lead_research",
                title=row.title,
                description=row.summary,
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
                entity=company_names.get(row.company_id) or "Lead research",
                priority="high" if (row.significance_score or 0) >= 75 else "normal",
                next_action_label="Review Pipeline",
                next_action_url="/pipeline",
                metadata={
                    "company_id": row.company_id,
                    "update_type": row.update_type,
                    "significance_score": row.significance_score,
                    "source_domain": row.source_domain,
                },
            )
            for row in rows
        ]

    def collect_notifications() -> list[dict]:
        rows = (
            db.query(UserNotification)
            .order_by(desc(UserNotification.created_at))
            .limit(cap)
            .all()
        )
        return [
            _workflow_item(
                item_id=row.id,
                source="notification",
                title=row.title,
                description=row.body,
                status="read" if row.read_at else row.delivery_state,
                created_at=row.created_at,
                updated_at=row.created_at,
                entity=company_names.get(row.company_id) or "User notification",
                priority="normal",
                next_action_label="Open Profile",
                next_action_url="/profile",
                metadata={
                    "company_id": row.company_id,
                    "notification_type": row.notification_type,
                    "research_update_id": row.research_update_id,
                },
            )
            for row in rows
        ]

    items: list[dict] = []
    items.extend(_safe_collect(collect_sales_actions, source="sales_agent", errors=errors))
    items.extend(_safe_collect(collect_buyer_outreach, source="buyer_outreach", errors=errors))
    items.extend(_safe_collect(collect_supply_outreach, source="supply_outreach", errors=errors))
    items.extend(_safe_collect(collect_research_updates, source="lead_research", errors=errors))
    items.extend(_safe_collect(collect_notifications, source="notification", errors=errors))

    def sort_key(item: dict):
        state_rank = {
            "failed": 0,
            "needs_approval": 1,
            "queued": 2,
            "in_process": 3,
            "needs_review": 4,
            "unknown": 5,
            "completed": 6,
        }.get(item.get("state"), 5)
        timestamp = item.get("updated_at") or item.get("created_at") or ""
        return (state_rank, timestamp)

    items = sorted(items, key=sort_key, reverse=False)[:cap]
    counts = {
        "total": len(items),
        "needs_approval": 0,
        "queued": 0,
        "in_process": 0,
        "needs_review": 0,
        "completed": 0,
        "failed": 0,
    }
    by_source: dict[str, int] = {}
    for item in items:
        state = item.get("state") or "unknown"
        if state in counts:
            counts[state] += 1
        by_source[item["source"]] = by_source.get(item["source"], 0) + 1

    return {
        "counts": counts,
        "by_source": by_source,
        "items": items,
        "errors": errors,
    }


# ── URL Import ────────────────────────────────────────────────────────────────

class UrlImportPayload(BaseModel):
    urls: List[str]
    label:       Optional[str] = None
    industry:    Optional[str] = None   # Logistics | Hospitality | Healthcare | Food Service
    signal_type: Optional[str] = None
    scrape_now:  bool = False


def _detect_scraper(url: str) -> str:
    u = url.lower()
    if any(x in u for x in ["indeed.com", "linkedin.com", "glassdoor", "ziprecruiter", "monster.com"]):
        return "job_board"
    if any(x in u for x in ["yellowpages", "tripadvisor", "booking.com", "expedia", "hotels.com"]):
        return "hotel_dir"
    if any(x in u for x in ["/rss", "/feed", "atom", "feedburner"]):
        return "rss_feed"
    if any(x in u for x in ["warehouse", "3pl", "logistics-dir", "distribution-dir"]):
        return "logistics_dir"
    return "rss_feed"


def _detect_industries(url: str, hint: Optional[str]) -> List[str]:
    if hint:
        return [hint]
    u = url.lower()
    found = []
    if any(x in u for x in ["hotel", "hospitality", "resort", "lodging", "airbnb"]):
        found.append("Hospitality")
    if any(x in u for x in ["warehouse", "logistics", "fulfillment", "distribution", "3pl", "supply"]):
        found.append("Logistics")
    if any(x in u for x in ["hospital", "health", "medical", "clinic", "pharmacy"]):
        found.append("Healthcare")
    if any(x in u for x in ["restaurant", "food", "kitchen", "qsr", "dining", "cafe"]):
        found.append("Food Service")
    return found or ["Logistics", "Hospitality", "Healthcare", "Food Service"]


@router.post("/import/urls")
def import_urls(payload: UrlImportPayload, background_tasks: BackgroundTasks):
    """
    Accept a list of URLs, auto-detect scraper + industry, and register
    them as active scrape targets. Set scrape_now=true to queue immediately.
    """
    from app.scrapers.scrape_targets import ALL_TARGETS, ScrapeTarget

    existing_urls = {t.url for t in ALL_TARGETS}
    added, skipped = [], []

    for raw in payload.urls:
        url = raw.strip()
        if not url or not url.startswith("http"):
            skipped.append({"url": url, "reason": "invalid URL"})
            continue
        if url in existing_urls:
            skipped.append({"url": url, "reason": "already registered"})
            continue

        scraper    = _detect_scraper(url)
        industries = _detect_industries(url, payload.industry)
        sig_types  = [payload.signal_type] if payload.signal_type else ["labor_pain", "expansion"]

        target = ScrapeTarget(
            url=url,
            label=payload.label or f"Imported: {url[:80]}",
            scraper=scraper,
            industries=industries,
            signal_types=sig_types,
            cadence="daily",
            active=True,
            notes="Manually imported via admin panel",
        )
        ALL_TARGETS.append(target)
        existing_urls.add(url)
        added.append({"url": url, "scraper": scraper, "industries": industries, "signal_types": sig_types})

    if payload.scrape_now and added:
        try:
            from worker.tasks import run_job_scraper_task, run_rss_scraper_task
            job_urls = [a["url"] for a in added if a["scraper"] == "job_board"]
            rss_urls = [a["url"] for a in added if a["scraper"] == "rss_feed"]
            if job_urls:
                background_tasks.add_task(run_job_scraper_task.delay, urls=job_urls)
            if rss_urls:
                background_tasks.add_task(run_rss_scraper_task.delay, urls=rss_urls)
        except Exception:
            pass  # Celery may not be running

    return {
        "added":           len(added),
        "skipped":         len(skipped),
        "targets":         added,
        "skipped_details": skipped,
    }


# ── Company Import ────────────────────────────────────────────────────────────

class CompanyRecord(BaseModel):
    name:           str
    website:        Optional[str] = None
    industry:       Optional[str] = None
    location_city:  Optional[str] = None
    location_state: Optional[str] = None
    source:         Optional[str] = "manual_import"


class CompanyImportPayload(BaseModel):
    companies: List[CompanyRecord]


@router.post("/import/companies")
def import_companies(payload: CompanyImportPayload, db: Session = Depends(get_db)):
    """Bulk-import company records. Skips names that fail `is_valid_lead` (same gate as scrapers) and duplicates."""
    from app.services.company_validator import is_valid_lead

    added, skipped = [], []

    for rec in payload.companies:
        ok, reason = is_valid_lead(rec.name or "")
        if not ok:
            skipped.append({"name": rec.name, "reason": reason})
            continue

        existing = db.query(Company).filter(Company.name == rec.name).first()
        if existing:
            skipped.append({"name": rec.name, "reason": "duplicate"})
            continue

        company = Company(
            name=rec.name,
            website=rec.website,
            industry=rec.industry or "Unknown",
            location_city=rec.location_city,
            location_state=rec.location_state,
            source=rec.source,
        )
        db.add(company)
        added.append(rec.name)

    db.commit()
    return {"added": len(added), "skipped": len(skipped), "names": added}


# ── Scrape Targets list ───────────────────────────────────────────────────────

@router.get("/scrape/targets")
def list_scrape_targets(
    scraper:  Optional[str] = None,
    industry: Optional[str] = None,
):
    """List all registered scrape targets."""
    from app.scrapers.scrape_targets import get_targets, summary

    targets = get_targets(scraper=scraper, industry=industry)
    return {
        "summary": summary(),
        "targets": [
            {
                "url":          t.url,
                "label":        t.label,
                "scraper":      t.scraper,
                "industries":   t.industries,
                "signal_types": t.signal_types,
                "cadence":      t.cadence,
                "active":       t.active,
                "notes":        t.notes,
            }
            for t in targets
        ],
    }


# Lead batch ops: see app/api/admin_lead_ops.py (X-Admin-Key or admin JWT)

# ── Trigger Scrape ────────────────────────────────────────────────────────────

class TriggerScrapePayload(BaseModel):
    scraper:  str = "all"   # all | job_board | hotel_dir | rss_feed | news | serp | logistics | score_recalc
    industry: Optional[str] = None
    urls:     Optional[List[str]] = None


@router.post("/scrape/trigger")
def trigger_scrape(payload: TriggerScrapePayload, background_tasks: BackgroundTasks):
    """Queue a scraper run. Returns immediately; work happens in background."""
    try:
        from worker.tasks import (
            run_all_scrapers_task,
            run_job_scraper_task,
            run_hotel_scraper_task,
            run_news_scraper_task,
            run_rss_scraper_task,
            run_serp_scraper_task,
            run_logistics_scraper_task,
            recalculate_all_scores_task,
        )
        task_map = {
            "all":          run_all_scrapers_task,
            "job_board":    run_job_scraper_task,
            "hotel_dir":    run_hotel_scraper_task,
            "news":         run_news_scraper_task,
            "rss_feed":     run_rss_scraper_task,
            "serp":         run_serp_scraper_task,
            "logistics":    run_logistics_scraper_task,
            "score_recalc": recalculate_all_scores_task,
        }
        fn = task_map.get(payload.scraper)
        if not fn:
            raise HTTPException(400, f"Unknown scraper '{payload.scraper}'. Options: {list(task_map)}")

        if payload.scraper in ("all", "score_recalc"):
            background_tasks.add_task(fn.delay)
        elif payload.urls:
            background_tasks.add_task(fn.delay, urls=payload.urls)
        else:
            background_tasks.add_task(fn.delay, industry=payload.industry)

        return {"status": "queued", "scraper": payload.scraper, "industry": payload.industry}

    except ImportError:
        pass
    except Exception as exc:
        # Celery broker up but worker down — fall back to in-process intelligence for "all"/news.
        if payload.scraper not in ("all", "news", "intelligence"):
            return {
                "status": "skipped",
                "reason": f"Celery unavailable ({exc}) — only intelligence can run in-process.",
            }

    if payload.scraper in ("all", "news", "intelligence"):
        from app.api.scraper_control import _run_intelligence_scraper_sync

        background_tasks.add_task(
            _run_intelligence_scraper_sync,
            articles_per_query=15,
            max_queries=20,
            enrich=True,
        )
        return {
            "status": "started",
            "scraper": payload.scraper,
            "mode": "in_process",
            "message": "Intelligence scraper running in-process (Celery worker not available).",
        }

    return {
        "status": "skipped",
        "reason": "Celery worker not running — start with: celery -A worker.celery_worker worker -B",
    }


# purge_router is registered separately in main.py (no require_admin global dep)
# so it can do its own flexible auth via X-Admin-Key or admin JWT.
