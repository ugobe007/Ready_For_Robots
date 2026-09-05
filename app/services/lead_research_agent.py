"""Bounded lead research agent.

This first version does not scrape during page loads. Scheduled/admin tasks call
into this service, which turns newly collected/cited signals into durable
``LeadResearchUpdate`` rows and user-visible notifications.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from sqlalchemy import desc, func, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.lead_research import LeadResearchUpdate, UserNotification
from app.models.score import Score
from app.models.scout_chat import ScoutActivation
from app.models.signal import Signal
from app.services.lead_filter import classify_lead, pick_primary_score
from app.services.lead_signal_display import format_signal_for_sales, strip_extraction_artifacts
from app.services.shared_api_cache import shared_cache_get, shared_cache_set


MATERIAL_UPDATE_TYPES = {
    "funding": 0.95,
    "expansion": 0.9,
    "hiring": 0.76,
    "rfp_procurement": 0.94,
    "leadership_change": 0.72,
    "deployment": 0.88,
    "partnership": 0.82,
    "risk": 0.8,
    "news": 0.62,
}

UPDATE_TYPE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("funding", ("funding", "raised", "series ", "investment", "capital", "financing")),
    ("expansion", ("expansion", "opens", "opened", "new facility", "new plant", "warehouse", "distribution center")),
    ("hiring", ("hiring", "job posting", "recruiting", "headcount", "labor shortage", "staffing")),
    ("rfp_procurement", ("rfp", "request for proposal", "procurement", "tender", "bid", "contract award")),
    ("leadership_change", ("appointed", "named", "chief", "ceo", "coo", "vp ", "president")),
    ("deployment", ("deploy", "deployed", "installation", "rollout", "robot", "automation")),
    ("partnership", ("partnership", "partnered", "collaboration", "integrates", "alliance")),
    ("risk", ("layoff", "strike", "safety incident", "recall", "delay", "shortage", "shutdown")),
]


@dataclass(frozen=True)
class NormalizedResearchResult:
    company_id: int
    update_type: str
    title: str
    summary: str
    source_url: Optional[str]
    source_domain: Optional[str]
    detected_at: datetime
    significance_score: float
    dedupe_fingerprint: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ResearchRunSummary:
    company_id: int
    company_name: str
    planned_queries: list[str]
    candidates_seen: int
    updates_created: int
    signals_created: int
    score_after: Optional[float]
    crm_profile_updated: bool
    duplicates_skipped: int
    notifications_created: int
    dry_run: bool


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _domain(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = (parsed.netloc or parsed.path).lower().strip()
        return host[4:] if host.startswith("www.") else host or None
    except Exception:
        return None


def _uuid_or_none(value: Any):
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


def _compact_text(value: Optional[str], *, max_len: int = 480) -> str:
    text_value = strip_extraction_artifacts(value or "")
    text_value = re.sub(r"\s+", " ", text_value).strip()
    if len(text_value) <= max_len:
        return text_value
    return text_value[: max_len - 1].rstrip() + "…"


def classify_update_type(text_value: str, signal_type: Optional[str] = None) -> str:
    haystack = f"{signal_type or ''} {text_value}".lower()
    if signal_type:
        st = signal_type.lower()
        if st in {"funding_round", "capex"}:
            return "funding" if st == "funding_round" else "rfp_procurement"
        if st in {"job_posting", "labor_shortage", "strategic_hire"}:
            return "leadership_change" if st == "strategic_hire" else "hiring"
        if st in {"expansion", "production_capacity", "warehouse_throughput"}:
            return "expansion"
        if st in {"robot_installation", "automation_interest", "automation_intent"}:
            return "deployment"
    for update_type, keywords in UPDATE_TYPE_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return update_type
    return "news"


def dedupe_fingerprint(company_id: int, title: str, source_url: Optional[str], summary: str) -> str:
    key = "|".join(
        [
            str(company_id),
            (source_url or "").strip().lower(),
            re.sub(r"\W+", " ", title.lower()).strip(),
            re.sub(r"\W+", " ", summary.lower()).strip()[:160],
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:40]


def materiality_score(
    *,
    update_type: str,
    signal_strength: Optional[float] = None,
    lead_score: Optional[float] = None,
    source_url: Optional[str] = None,
) -> float:
    base = MATERIAL_UPDATE_TYPES.get(update_type, 0.55)
    signal_boost = min(max(float(signal_strength or 0), 0), 1) * 0.18
    lead_boost = min(max(float(lead_score or 0), 0), 100) / 100 * 0.15
    source_boost = 0.05 if source_url else 0.0
    return round(min(1.0, base + signal_boost + lead_boost + source_boost), 3)


def signal_type_for_update(update_type: str) -> str:
    return {
        "funding": "funding_round",
        "expansion": "expansion",
        "hiring": "job_posting",
        "rfp_procurement": "capex",
        "leadership_change": "strategic_hire",
        "deployment": "automation_intent",
        "partnership": "automation_interest",
        "risk": "operations_risk",
        "news": "news",
    }.get(update_type, "news")


def plan_lead_enrichment(
    company_id: int,
    company_name: str,
    *,
    website: Optional[str] = None,
    signal_snippets: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Return a machine-readable plan for an enrichment agent (stub — no network I/O).

    Downstream workers can map ``steps`` to tool calls (search, fetch URL, structured extract).
    """
    cache_key = f"{company_id}:{company_name}:{website or ''}"
    cached = shared_cache_get("lead_research_plan", cache_key)
    if cached:
        return cached
    plan = {
        "company_id": company_id,
        "company_name": company_name,
        "website": website,
        "objectives": [
            "confirm_operating_entity",
            "classify_vertical_with_evidence",
            "attach_ranking_rationale",
        ],
        "steps": [
            {"tool": "web_search", "query": f'"{company_name}" official site industry'},
            {"tool": "fetch", "target": website or ""},
            {"tool": "structured_extract", "fields": ["naics_hint", "employee_band", "hq_geo"]},
        ],
        "signal_context_head": (signal_snippets or [])[:5],
        "status": "planned",
    }
    shared_cache_set("lead_research_plan", cache_key, plan, ttl_sec=6 * 60 * 60)
    return plan


def build_search_queries(company: Company) -> list[str]:
    industry = (company.industry or "").strip()
    base = f'"{company.name}"'
    queries = [
        f"{base} automation robotics news",
        f"{base} expansion hiring procurement",
        f"{base} funding partnership deployment",
    ]
    if industry:
        queries.append(f"{base} {industry} operations automation")
    if company.website_domain:
        queries.append(f"site:{company.website_domain} automation expansion procurement")
    return list(dict.fromkeys(queries))


def select_research_candidates(
    db: Session,
    *,
    limit: int = 50,
    min_score: float = 55.0,
    recent_days: int = 30,
) -> list[Company]:
    """Select a bounded HOT/WARM-like set, plus saved and recently signaled leads."""
    cap = max(1, min(limit, 200))
    since = _utcnow() - timedelta(days=max(1, recent_days))
    ids: list[int] = []

    # WARM leads matter: the agent should help them graduate when new evidence
    # appears, not only babysit already-hot accounts.
    warm_rows = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .outerjoin(Score, Score.company_id == Company.id)
        .filter(func.coalesce(Score.overall_intent_score, 0) >= 40)
        .filter(func.coalesce(Score.overall_intent_score, 0) < 80)
        .order_by(desc(func.coalesce(Score.overall_intent_score, 0)), desc(Company.id))
        .limit(cap * 2)
        .all()
    )
    for company in warm_rows:
        junk, _, pri = classify_lead(company, company.scores, company.signals)
        if not junk and pri.tier == "WARM":
            ids.append(company.id)
        if len(ids) >= max(1, cap // 2):
            break

    scored_rows = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .outerjoin(Score, Score.company_id == Company.id)
        .order_by(desc(func.coalesce(Score.overall_intent_score, 0)), desc(Company.id))
        .limit(cap * 4)
        .all()
    )
    for company in scored_rows:
        score = pick_primary_score(company.scores)
        if score and float(score.overall_intent_score or 0) < min_score:
            continue
        junk, _, pri = classify_lead(company, company.scores, company.signals)
        if not junk and pri.tier in {"HOT", "WARM"}:
            ids.append(company.id)
        if len(ids) >= cap:
            break

    recent_ids = [
        row[0]
        for row in (
            db.query(Signal.company_id)
            .filter(Signal.created_at >= since)
            .group_by(Signal.company_id)
            .order_by(desc(func.max(Signal.created_at)))
            .limit(cap)
            .all()
        )
    ]
    ids.extend(recent_ids)

    try:
        saved_ids = [
            row[0]
            for row in db.execute(
                text("SELECT DISTINCT company_id FROM user_saved_companies WHERE company_id IS NOT NULL LIMIT :limit"),
                {"limit": cap},
            ).fetchall()
        ]
        ids.extend(saved_ids)
    except (OperationalError, ProgrammingError):
        pass

    ordered_ids = list(dict.fromkeys(int(cid) for cid in ids if cid))[:cap]
    if not ordered_ids:
        return []
    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id.in_(ordered_ids))
        .all()
    )
    by_id = {c.id: c for c in companies}
    return [by_id[cid] for cid in ordered_ids if cid in by_id]


def normalize_signal_result(company: Company, signal: Signal) -> NormalizedResearchResult:
    score = pick_primary_score(company.scores)
    raw_summary = signal.signal_text or signal.ingestion_raw_text or ""
    summary = _compact_text(format_signal_for_sales(raw_summary), max_len=650) or "New market signal detected."
    update_type = classify_update_type(summary, signal.signal_type)
    source_url = signal.source_url
    detected_at = signal.created_at or _utcnow()
    lead_score = float(score.overall_intent_score) if score else 0.0
    significance = materiality_score(
        update_type=update_type,
        signal_strength=signal.signal_strength,
        lead_score=lead_score,
        source_url=source_url,
    )
    title = _title_for_update(company.name, update_type, summary)
    return NormalizedResearchResult(
        company_id=company.id,
        update_type=update_type,
        title=title,
        summary=summary,
        source_url=source_url,
        source_domain=_domain(source_url),
        detected_at=detected_at,
        significance_score=significance,
        dedupe_fingerprint=dedupe_fingerprint(company.id, title, source_url, summary),
        payload={
            "signal_id": signal.id,
            "signal_type": signal.signal_type,
            "signal_strength": signal.signal_strength,
            "lead_score": lead_score,
        },
    )


def _title_for_update(company_name: str, update_type: str, summary: str) -> str:
    labels = {
        "funding": "Funding signal",
        "expansion": "Expansion signal",
        "hiring": "Hiring or labor signal",
        "rfp_procurement": "Procurement signal",
        "leadership_change": "Leadership signal",
        "deployment": "Automation deployment signal",
        "partnership": "Partnership signal",
        "risk": "Operational risk signal",
        "news": "Market news signal",
    }
    prefix = labels.get(update_type, "Research signal")
    clue = _compact_text(summary, max_len=92)
    return f"{prefix}: {company_name}" if not clue else f"{prefix}: {clue}"


def normalize_research_results(
    company: Company,
    *,
    lookback_days: int = 30,
    max_results: int = 8,
) -> list[NormalizedResearchResult]:
    since = _utcnow() - timedelta(days=max(1, lookback_days))
    signals = sorted(
        company.signals or [],
        key=lambda s: (_aware(s.created_at) or datetime.min.replace(tzinfo=timezone.utc), s.signal_strength or 0),
        reverse=True,
    )
    recent = [s for s in signals if (_aware(s.created_at) or since) >= since]
    selected = recent[:max_results] or signals[: min(max_results, 3)]
    return [normalize_signal_result(company, signal) for signal in selected]


def _recipients_for_company(db: Session, company_id: int) -> list[uuid.UUID]:
    recipients: dict[str, uuid.UUID] = {}
    try:
        rows = db.execute(
            text("SELECT DISTINCT user_id FROM user_saved_companies WHERE company_id = :company_id"),
            {"company_id": company_id},
        ).fetchall()
        for row in rows:
            uid = _uuid_or_none(row[0])
            if uid:
                recipients[str(uid)] = uid
    except (OperationalError, ProgrammingError):
        pass

    activations = (
        db.query(ScoutActivation)
        .filter(ScoutActivation.user_id.isnot(None))
        .order_by(desc(ScoutActivation.created_at))
        .limit(500)
        .all()
    )
    needle = str(company_id)
    for activation in activations:
        lead_ids = activation.lead_ids or []
        if any(str(item) == needle for item in lead_ids):
            uid = _uuid_or_none(activation.user_id)
            if uid:
                recipients[str(uid)] = uid
            continue
        for item in activation.leads_snapshot or []:
            if isinstance(item, dict) and str(item.get("id")) == needle:
                uid = _uuid_or_none(activation.user_id)
                if uid:
                    recipients[str(uid)] = uid
                break
    return list(recipients.values())


def create_notifications_for_update(
    db: Session,
    update: LeadResearchUpdate,
    *,
    significance_threshold: float = 0.72,
) -> int:
    if float(update.significance_score or 0) < significance_threshold:
        return 0
    recipients = _recipients_for_company(db, update.company_id)
    created = 0
    for user_id in recipients:
        exists = (
            db.query(UserNotification.id)
            .filter(
                UserNotification.user_id == user_id,
                UserNotification.research_update_id == update.id,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            UserNotification(
                user_id=user_id,
                company_id=update.company_id,
                research_update_id=update.id,
                notification_type=update.update_type,
                title=update.title,
                body=update.summary,
                delivery_state="in_app",
                payload={"source_domain": update.source_domain, "significance_score": update.significance_score},
            )
        )
        created += 1
    return created


def _signal_exists_for_result(db: Session, result: NormalizedResearchResult) -> Optional[Signal]:
    signal_id = (result.payload or {}).get("signal_id")
    if signal_id:
        return db.query(Signal).filter(Signal.id == signal_id).first()
    query = db.query(Signal).filter(
        Signal.company_id == result.company_id,
        Signal.signal_type == signal_type_for_update(result.update_type),
        Signal.signal_text == result.summary,
    )
    if result.source_url:
        query = query.filter(Signal.source_url == result.source_url)
    return query.first()


def ensure_signal_for_research_result(
    db: Session,
    result: NormalizedResearchResult,
    *,
    materiality_threshold: float = 0.72,
) -> tuple[Optional[Signal], bool]:
    """
    Convert new material research into the same Signal evidence scored by the pipeline.

    If the research result came from an existing Signal, return it and do not duplicate.
    """
    existing = _signal_exists_for_result(db, result)
    if existing:
        return existing, False
    if result.significance_score < materiality_threshold:
        return None, False
    signal = Signal(
        company_id=result.company_id,
        signal_type=signal_type_for_update(result.update_type),
        signal_text=result.summary,
        ingestion_raw_text=result.title,
        signal_strength=max(0.1, min(float(result.significance_score), 1.0)),
        source_url=result.source_url,
        created_at=result.detected_at,
    )
    db.add(signal)
    db.flush()
    return signal, True


def rescore_company(db: Session, company: Company) -> Optional[float]:
    from app.services.scoring_engine import compute_scores

    signals = db.query(Signal).filter(Signal.company_id == company.id).all()
    score_data = compute_scores(company, signals)
    score = pick_primary_score(company.scores)
    if score is None:
        score = Score(company_id=company.id)
        db.add(score)
    score.automation_score = float(score_data.get("automation_score", 0) or 0)
    score.labor_pain_score = float(score_data.get("labor_pain_score", 0) or 0)
    score.expansion_score = float(score_data.get("expansion_score", 0) or 0)
    score.robotics_fit_score = float(score_data.get("robotics_fit_score", 0) or 0)
    score.overall_intent_score = float(score_data.get("overall_intent_score", 0) or 0)
    db.flush()
    return score.overall_intent_score


def update_crm_profile_from_research(
    db: Session,
    company: Company,
    updates: Iterable[LeadResearchUpdate],
) -> bool:
    """Refresh CRM metadata when material research adds useful sales evidence."""
    material = [
        update
        for update in updates
        if float(update.significance_score or 0) >= 0.72
        and update.update_type in MATERIAL_UPDATE_TYPES
        and update.update_type != "news"
    ]
    if not material:
        return False

    from app.services.crm_extractor import build_crm_metadata_dict, extract

    existing_meta = dict(company.crm_metadata or {})
    signals = db.query(Signal).filter(Signal.company_id == company.id).all()
    extracted = build_crm_metadata_dict(extract(company, signals, db))

    previous_research = existing_meta.get("research_agent")
    previous_evidence = existing_meta.get("research_evidence")
    extracted["research_agent"] = previous_research
    extracted["research_evidence"] = _merge_research_evidence(previous_evidence, material)

    flags = dict(extracted.get("quality_flags") or {})
    flags["has_material_research"] = True
    flags["last_research_profile_update_at"] = _utcnow().isoformat()
    extracted["quality_flags"] = flags

    company.crm_metadata = extracted
    db.add(company)
    db.flush()
    return True


def _merge_research_evidence(existing: Any, updates: Iterable[LeadResearchUpdate]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    seen: set[int] = set()
    if isinstance(existing, list):
        for item in existing:
            if not isinstance(item, dict):
                continue
            update_id = item.get("research_update_id") or item.get("id")
            if isinstance(update_id, int):
                seen.add(update_id)
            evidence.append(item)
    for update in sorted(updates, key=lambda u: (u.detected_at or _utcnow()), reverse=True):
        if update.id in seen:
            continue
        evidence.insert(
            0,
            {
                "research_update_id": update.id,
                "update_type": update.update_type,
                "title": update.title,
                "summary": update.summary,
                "source_url": update.source_url,
                "source_domain": update.source_domain,
                "detected_at": update.detected_at.isoformat() if update.detected_at else None,
                "significance_score": update.significance_score,
                "scoring_signal_id": (update.payload or {}).get("scoring_signal_id") or (update.payload or {}).get("signal_id"),
            },
        )
    return evidence[:12]


def _upsert_company_research_metadata(
    company: Company,
    updates: Iterable[LeadResearchUpdate],
    *,
    researched_at: datetime,
) -> None:
    material = sorted(updates, key=lambda u: (u.significance_score or 0, u.detected_at or researched_at), reverse=True)
    meta = dict(company.crm_metadata or {})
    meta["research_agent"] = {
        "last_researched_at": researched_at.isoformat(),
        "latest_material_update": (
            {
                "id": material[0].id,
                "title": material[0].title,
                "summary": material[0].summary,
                "update_type": material[0].update_type,
                "source_url": material[0].source_url,
                "source_domain": material[0].source_domain,
                "detected_at": material[0].detected_at.isoformat() if material[0].detected_at else None,
                "significance_score": material[0].significance_score,
            }
            if material
            else None
        ),
    }
    company.crm_metadata = meta


def research_company_updates(
    db: Session,
    company_id: int,
    *,
    dry_run: bool = False,
    lookback_days: int = 30,
    max_results: int = 8,
    notify: bool = True,
) -> ResearchRunSummary:
    company = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id == company_id)
        .first()
    )
    if not company:
        raise ValueError(f"Company {company_id} not found")

    snippets = [_compact_text(s.signal_text or s.ingestion_raw_text, max_len=180) for s in (company.signals or [])[:5]]
    planned = plan_lead_enrichment(company.id, company.name, website=company.website, signal_snippets=snippets)
    results = normalize_research_results(company, lookback_days=lookback_days, max_results=max_results)
    created_updates: list[LeadResearchUpdate] = []
    duplicates = 0
    notifications = 0
    signals_created = 0
    score_after: Optional[float] = None
    crm_profile_updated = False

    if dry_run:
        existing = {
            row[0]
            for row in db.query(LeadResearchUpdate.dedupe_fingerprint)
            .filter(LeadResearchUpdate.dedupe_fingerprint.in_([r.dedupe_fingerprint for r in results]))
            .all()
        }
        duplicates = sum(1 for result in results if result.dedupe_fingerprint in existing)
        return ResearchRunSummary(
            company_id=company.id,
            company_name=company.name,
            planned_queries=[step.get("query", "") for step in planned.get("steps", []) if step.get("query")],
            candidates_seen=len(results),
            updates_created=len(results) - duplicates,
            signals_created=0,
            score_after=None,
            crm_profile_updated=False,
            duplicates_skipped=duplicates,
            notifications_created=0,
            dry_run=True,
        )

    for result in results:
        if db.query(LeadResearchUpdate.id).filter_by(dedupe_fingerprint=result.dedupe_fingerprint).first():
            duplicates += 1
            continue
        scoring_signal, signal_created = ensure_signal_for_research_result(db, result)
        signals_created += 1 if signal_created else 0
        payload = dict(result.payload or {})
        if scoring_signal:
            payload["scoring_signal_id"] = scoring_signal.id
        row = LeadResearchUpdate(
            company_id=result.company_id,
            update_type=result.update_type,
            title=result.title,
            summary=result.summary,
            source_url=result.source_url,
            source_domain=result.source_domain,
            detected_at=result.detected_at,
            significance_score=result.significance_score,
            status="new",
            dedupe_fingerprint=result.dedupe_fingerprint,
            payload=payload,
        )
        db.add(row)
        db.flush()
        created_updates.append(row)
        if notify:
            notifications += create_notifications_for_update(db, row)

    if created_updates or signals_created:
        score_after = rescore_company(db, company)
        crm_profile_updated = update_crm_profile_from_research(db, company, created_updates)
    _upsert_company_research_metadata(company, created_updates, researched_at=_utcnow())
    db.add(company)
    db.commit()
    return ResearchRunSummary(
        company_id=company.id,
        company_name=company.name,
        planned_queries=[step.get("query", "") for step in planned.get("steps", []) if step.get("query")],
        candidates_seen=len(results),
        updates_created=len(created_updates),
        signals_created=signals_created,
        score_after=score_after,
        crm_profile_updated=crm_profile_updated,
        duplicates_skipped=duplicates,
        notifications_created=notifications,
        dry_run=False,
    )


def research_active_leads(
    db: Session,
    *,
    limit: int = 50,
    dry_run: bool = False,
    lookback_days: int = 30,
) -> dict[str, Any]:
    companies = select_research_candidates(db, limit=limit)
    summaries = [
        research_company_updates(
            db,
            company.id,
            dry_run=dry_run,
            lookback_days=lookback_days,
        )
        for company in companies
    ]
    return {
        "dry_run": dry_run,
        "companies_considered": len(companies),
        "updates_created": sum(item.updates_created for item in summaries),
        "signals_created": sum(item.signals_created for item in summaries),
        "crm_profiles_updated": sum(1 for item in summaries if item.crm_profile_updated),
        "duplicates_skipped": sum(item.duplicates_skipped for item in summaries),
        "notifications_created": sum(item.notifications_created for item in summaries),
        "results": [item.__dict__ for item in summaries],
    }
