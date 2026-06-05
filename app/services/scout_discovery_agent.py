"""
SCOUT discovery & lead development — real pipeline data, not hallucinated prospects.

- discover_prospects: ranked HOT/WARM companies filtered by robot category / vertical / territory
- develop_lead_brief: inference refresh + structured sales development brief + Cal draft
- scan_company_in_pipeline: resolve URL or name to a scored company
- scan_for_results: robot-ready matching enriched with SCOUT briefs
- execute_activation: run inference + CRM capture + outreach drafts for an activation queue
"""
from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.crm import CrmAccount
from app.models.score import Score
from app.models.scout_chat import ScoutActivation
from app.services.company_domain import normalize_website_domain, resolve_outreach_domain
from app.services.lead_filter import classify_lead, is_junk, pick_primary_score
from app.services.lead_inference_engine import refresh_company_inference
from app.services.lead_project_timing import resolve_project_timing
from app.services.lead_sales_copy import build_lead_intelligence_copy, humanize_robot_types
from app.services.lead_signal_display import format_signal_for_sales, strip_extraction_artifacts
from app.services.outreach_email_inference import infer_outreach_emails

logger = logging.getLogger(__name__)

WARM_THRESHOLD = 45.0
HOT_THRESHOLD = 70.0

# Robot category slug → industry / signal hints for discovery queries
_CATEGORY_FILTERS: Dict[str, Dict[str, Any]] = {
    "amr": {
        "label": "Warehouse / AMR",
        "industries": ("warehouse", "logistics", "fulfillment", "distribution", "3pl"),
        "signal_types": ("warehouse_throughput", "material_handling", "expansion", "labor_shortage"),
    },
    "warehouse": {
        "label": "Warehouse / AMR",
        "industries": ("warehouse", "logistics", "fulfillment", "distribution"),
        "signal_types": ("warehouse_throughput", "material_handling", "expansion"),
    },
    "industrial": {
        "label": "Industrial arms",
        "industries": ("manufacturing", "factory", "production", "automotive", "aerospace"),
        "signal_types": ("production_capacity", "quality_bottleneck", "repetitive_process", "capex"),
    },
    "service": {
        "label": "Service robots",
        "industries": ("hospitality", "hotel", "retail", "restaurant", "casino"),
        "signal_types": ("labor_shortage", "expansion", "strategic_hire"),
    },
    "food": {
        "label": "Food & beverage automation",
        "industries": ("food", "beverage", "packaging", "restaurant", "grocery"),
        "signal_types": ("packaging_automation", "labor_shortage", "production_capacity"),
    },
    "healthcare": {
        "label": "Healthcare robots",
        "industries": ("healthcare", "hospital", "medical", "pharma", "clinical"),
        "signal_types": ("labor_shortage", "expansion", "strategic_hire", "capex"),
    },
    "partnerships": {
        "label": "SI / distributor partnerships",
        "industries": ("integrator", "automation", "robotics", "distribution", "systems"),
        "signal_types": ("ma_activity", "funding_round", "strategic_hire"),
    },
}


def _tier_from_score(score: float) -> str:
    if score >= HOT_THRESHOLD:
        return "HOT"
    if score >= WARM_THRESHOLD:
        return "WARM"
    return "COLD"


def _category_key(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    key = raw.strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    if key in _CATEGORY_FILTERS:
        return key
    low = raw.strip().lower()
    for slug, meta in _CATEGORY_FILTERS.items():
        label_low = meta["label"].lower()
        if low == label_low or low == slug or slug in low or label_low in low:
            return slug
    if "amr" in low or "warehouse" in low:
        return "amr"
    if "industrial" in low or "arm" in low:
        return "industrial"
    if "healthcare" in low or "hospital" in low:
        return "healthcare"
    if "food" in low or "beverage" in low:
        return "food"
    if "partner" in low or "integrator" in low or "distributor" in low:
        return "partnerships"
    if "service" in low or "hospitality" in low:
        return "service"
    return None


def _company_query_base(db: Session):
    return (
        db.query(Company, Score)
        .join(Score, Score.company_id == Company.id)
        .options(joinedload(Company.signals), joinedload(Company.scores))
        .filter(Score.overall_intent_score >= WARM_THRESHOLD)
    )


def _apply_discovery_filters(
    q,
    *,
    robot_category: Optional[str] = None,
    vertical: Optional[str] = None,
    territory: Optional[str] = None,
):
    cat = _category_key(robot_category)
    if cat and cat in _CATEGORY_FILTERS:
        meta = _CATEGORY_FILTERS[cat]
        ind_clauses = [Company.industry.ilike(f"%{tok}%") for tok in meta["industries"][:6]]
        if ind_clauses:
            q = q.filter(or_(*ind_clauses))
    if vertical and vertical.strip():
        v = vertical.strip()[:80]
        q = q.filter(
            or_(
                Company.industry.ilike(f"%{v}%"),
                Company.name.ilike(f"%{v}%"),
            )
        )
    if territory and territory.strip():
        t = territory.strip()[:80]
        q = q.filter(
            or_(
                Company.location_state.ilike(f"%{t}%"),
                Company.location_city.ilike(f"%{t}%"),
                Company.name.ilike(f"%{t}%"),
            )
        )
    return q


def _top_signal_summary(company: Company) -> Tuple[str, str]:
    sigs = sorted(
        company.signals or [],
        key=lambda s: float(getattr(s, "signal_strength", 0) or 0),
        reverse=True,
    )
    if not sigs:
        return "automation interest", "news"
    top = sigs[0]
    st = (getattr(top, "signal_type", None) or "news").replace("_", " ")
    text = format_signal_for_sales(getattr(top, "signal_text", None))[:200]
    return text or "Active buying signal detected", st


def _recommended_action(tier: str, signal_types: Sequence[str]) -> str:
    types = {str(t).lower() for t in signal_types}
    if tier == "HOT":
        if "rfp_posted" in types or "vendor_selection" in types:
            return "Request intro to procurement owner; align proposal to active RFP window."
        if "strategic_hire" in types:
            return "Contact new operations or automation leader with ROI-first discovery call."
        if "expansion" in types:
            return "Pitch automation as part of facility rollout — budget is forming now."
        return "Prioritize personalized outreach this week; offer pilot scoped to their top pain signal."
    if tier == "WARM":
        return "Add to nurture sequence; monitor for additional signals before full outreach."
    return "Track only — qualify when intent score or signal count increases."


@dataclass
class ScoutLeadBrief:
    company_id: int
    company_name: str
    tier: str
    intent_score: float
    headline: str = ""
    sales_angle: str = ""
    talk_track: List[str] = field(default_factory=list)
    objection_handlers: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    timing_label: str = ""
    timing_source: str = ""
    procurement_notes: str = ""
    robot_fit: List[str] = field(default_factory=list)
    evidence: List[Dict[str, str]] = field(default_factory=list)
    share_summary: str = ""
    draft_subject: Optional[str] = None
    draft_body: Optional[str] = None
    contact_email: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _cal_draft_for_company(company: Company) -> tuple[str, str]:
    from app.services.stagegate_crm_bridge import cal_draft_for_stagegate_company, is_stagegate_company

    if is_stagegate_company(company):
        draft = cal_draft_for_stagegate_company(company)
        return draft["subject"], draft["body"]

    from app.api.crm import _draft_body, _draft_subject
    from app.models.crm import CrmAccount as _Acct

    dummy = _Acct(
        name=company.name or "Unknown",
        website=company.website,
        industry=company.industry,
    )
    return _draft_subject(dummy), _draft_body(dummy, None, [], "", "selective", None)


def _load_company(db: Session, company_id: int) -> Optional[Company]:
    return (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id == company_id)
        .first()
    )


def develop_lead_brief(
    db: Session,
    company_id: int,
    *,
    refresh_inference: bool = True,
    include_draft: bool = True,
) -> Dict[str, Any]:
    """Full lead development package for one pipeline company."""
    company = _load_company(db, company_id)
    if not company:
        return {"found": False, "error": "Company not found"}

    junk, junk_reason = is_junk(company.name)
    if junk:
        return {"found": False, "error": f"Lead filtered as junk: {junk_reason}"}

    if refresh_inference:
        try:
            refresh_company_inference(company, company.signals or [], db)
            db.refresh(company)
        except Exception as exc:
            logger.warning("SCOUT inference refresh failed for %s: %s", company_id, exc)

    _, _, pri = classify_lead(company, company.scores, company.signals)
    score_row = pick_primary_score(company.scores)
    intent = float(score_row.overall_intent_score or 0) if score_row else 0.0

    sigs = company.signals or []
    signal_labels = []
    signal_types: List[str] = []
    for sig in sigs[:8]:
        st = getattr(sig, "signal_type", None)
        if st:
            signal_types.append(str(st))
            signal_labels.append(st.replace("_", " ").title())

    signal_blob = " ".join(
        strip_extraction_artifacts(getattr(s, "signal_text", None)) for s in sigs[:12]
    )
    crm_meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    inf = crm_meta.get("lead_inference") if isinstance(crm_meta.get("lead_inference"), dict) else {}

    timing = resolve_project_timing(
        tier=pri.tier,
        crm_metadata=crm_meta,
        lead_inference=inf,
        signal_blob=signal_blob,
        signal_types=signal_types,
        procurement_hints=(crm_meta.get("procurement_hints") or []),
        intent_score=intent,
    )

    share_blurb, share_summary = build_lead_intelligence_copy(
        company_name=company.name or "This company",
        industry=company.industry or "",
        tier=pri.tier,
        signal_labels=signal_labels,
        signal_types=signal_types,
        automation_type=(company.automation_profile or {}).get("primary_type", ""),
        pain_point=(inf or {}).get("specific_problem") or "",
        automation_profile=company.automation_profile,
        crm_metadata=crm_meta,
        signal_blob=signal_blob,
    )

    robots = humanize_robot_types(
        company.automation_profile,
        industry=company.industry,
        signal_blob=signal_blob,
    )
    top_signal, top_type = _top_signal_summary(company)

    specific_problem = (inf or {}).get("specific_problem") or ""
    why_lead = (inf or {}).get("why_lead") or pri.reasons[:4]
    sales_angle = specific_problem or share_blurb or top_signal

    talk_track = [
        f"Open with their {top_type.replace('_', ' ')} signal: {top_signal[:120]}",
        f"Position {robots[0] if robots else 'automation'} against {sales_angle[:100]}",
        f"Confirm timeline: {timing.display_phrase}",
    ]
    if (inf or {}).get("procurement", {}).get("has_rfp"):
        talk_track.append("Ask who owns the RFP and what evaluation criteria matter most.")

    objection_handlers = [
        "ROI: anchor on labor, throughput, and error-cost deltas tied to their stated pain.",
        "Change management: offer phased pilot on one line or one facility first.",
        "Integration: reference similar deployments in their industry vertical.",
    ]

    next_steps = [
        "Save lead to CRM and approve Cal draft.",
        "Identify operations + finance stakeholders on LinkedIn or company site.",
        "Book 30-minute discovery to validate budget band and deployment scope.",
    ]
    if pri.tier == "HOT":
        next_steps.insert(0, "Send Cal outreach within 48 hours while signal is fresh.")

    evidence = []
    for sig in sigs[:4]:
        evidence.append(
            {
                "type": getattr(sig, "signal_type", None) or "signal",
                "text": format_signal_for_sales(getattr(sig, "signal_text", None))[:240],
            }
        )

    brief = ScoutLeadBrief(
        company_id=company.id,
        company_name=company.name or "Unknown",
        tier=pri.tier,
        intent_score=round(intent, 1),
        headline=f"{company.name} — {pri.tier} ({round(intent)} intent)",
        sales_angle=sales_angle[:500],
        talk_track=talk_track,
        objection_handlers=objection_handlers,
        next_steps=next_steps,
        timing_label=timing.display_phrase,
        timing_source=timing.source,
        procurement_notes=str((inf or {}).get("procurement") or "")[:400],
        robot_fit=robots[:4],
        evidence=evidence,
        share_summary=share_summary,
    )

    if include_draft:
        subject, body = _cal_draft_for_company(company)
        brief.draft_subject = subject
        brief.draft_body = body
        domain = resolve_outreach_domain(company)
        guessed = infer_outreach_emails(domain, company.industry) if domain else None
        brief.contact_email = guessed.primary if guessed else None

    meta = dict(crm_meta)
    meta["scout_development"] = {
        **brief.to_dict(),
        "developed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
    company.crm_metadata = meta
    db.add(company)
    db.commit()

    return {
        "found": True,
        "brief": brief.to_dict(),
        "priority_tier": pri.tier,
        "recommended_action": _recommended_action(pri.tier, signal_types),
    }


def discover_prospects(
    db: Session,
    *,
    robot_category: Optional[str] = None,
    vertical: Optional[str] = None,
    territory: Optional[str] = None,
    limit: int = 8,
    min_score: float = WARM_THRESHOLD,
) -> Dict[str, Any]:
    """Return ranked prospects from the live pipeline (not LLM-generated names)."""
    limit = max(1, min(limit, 25))
    q = _company_query_base(db).filter(Score.overall_intent_score >= min_score)
    q = _apply_discovery_filters(q, robot_category=robot_category, vertical=vertical, territory=territory)
    rows = q.order_by(Score.overall_intent_score.desc()).limit(limit * 4).all()

    prospects: List[Dict[str, Any]] = []
    cat_label = _CATEGORY_FILTERS.get(_category_key(robot_category) or "", {}).get("label")

    for company, score_row in rows:
        if len(prospects) >= limit:
            break
        junk, _ = is_junk(company.name)
        if junk:
            continue
        intent = float(score_row.overall_intent_score or 0)
        tier = _tier_from_score(intent)
        _, _, pri = classify_lead(company, company.scores, company.signals)
        signal_text, signal_type = _top_signal_summary(company)
        crm_meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
        inf = crm_meta.get("lead_inference") if isinstance(crm_meta.get("lead_inference"), dict) else {}
        timing = resolve_project_timing(
            tier=pri.tier,
            crm_metadata=crm_meta,
            lead_inference=inf if isinstance(inf, dict) else None,
            signal_blob="",
            signal_types=[],
            intent_score=intent,
        )
        loc_parts = [p for p in (company.location_city, company.location_state) if p]
        prospects.append(
            {
                "id": str(company.id),
                "company": company.name,
                "industry": company.industry or "New",
                "location": ", ".join(loc_parts) if loc_parts else "",
                "score": round(intent),
                "tier": tier,
                "signal": signal_text,
                "signalType": signal_type.replace(" ", "_"),
                "timing": timing.display_phrase,
                "action": _recommended_action(tier, [getattr(s, "signal_type", "") for s in (company.signals or [])[:6]]),
                "relevance": (inf or {}).get("specific_problem") or pri.reasons[0] if pri.reasons else signal_text[:160],
            }
        )

    summary_parts = [f"Found {len(prospects)} pipeline prospects"]
    if cat_label:
        summary_parts.append(f"for {cat_label}")
    if territory:
        summary_parts.append(f"in {territory}")
    if vertical:
        summary_parts.append(f"({vertical})")

    return {
        "prospects": prospects,
        "count": len(prospects),
        "summary": " ".join(summary_parts) + ".",
        "filters": {
            "robot_category": robot_category,
            "vertical": vertical,
            "territory": territory,
            "min_score": min_score,
        },
    }


def scan_company_in_pipeline(
    db: Session,
    *,
    url: Optional[str] = None,
    company_name: Optional[str] = None,
    robot_category: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve a URL or name to a scored company; optionally attach a development brief."""
    domain = ""
    if url:
        parsed = urlparse(url if url.startswith(("http://", "https://")) else f"https://{url}")
        domain = normalize_website_domain(parsed.netloc or url) or ""

    company: Optional[Company] = None
    if domain:
        company = (
            db.query(Company)
            .options(joinedload(Company.scores), joinedload(Company.signals))
            .filter(Company.website.ilike(f"%{domain}%"))
            .order_by(Company.updated_at.desc().nullslast())
            .first()
        )
    if not company and company_name:
        name = company_name.strip()[:200]
        company = (
            db.query(Company)
            .options(joinedload(Company.scores), joinedload(Company.signals))
            .filter(Company.name.ilike(f"%{name}%"))
            .order_by(Company.updated_at.desc().nullslast())
            .first()
        )

    if not company:
        return {
            "found": False,
            "in_pipeline": False,
            "message": "No matching company in the ReadyForRobots pipeline yet.",
            "domain": domain or None,
        }

    score_row = pick_primary_score(company.scores)
    intent = round(float(score_row.overall_intent_score or 0), 1) if score_row else 0.0
    tier = _tier_from_score(intent)
    signal_text, signal_type = _top_signal_summary(company)

    brief_payload = develop_lead_brief(db, company.id, refresh_inference=True, include_draft=False)

    return {
        "found": True,
        "in_pipeline": True,
        "company_id": company.id,
        "company_name": company.name,
        "website": company.website,
        "industry": company.industry,
        "score": intent,
        "tier": tier,
        "signals": [
            {
                "type": getattr(s, "signal_type", None),
                "text": format_signal_for_sales(getattr(s, "signal_text", None))[:200],
            }
            for s in (company.signals or [])[:5]
        ],
        "summary": brief_payload.get("brief", {}).get("share_summary") or signal_text,
        "recommendation": brief_payload.get("recommended_action"),
        "robot_category": robot_category,
        "top_signal": signal_text,
        "signal_type": signal_type,
        "development": brief_payload.get("brief"),
    }


def scan_for_results(
    db: Session,
    *,
    company_url: str,
    robot_name: Optional[str] = None,
    limit: int = 8,
) -> Dict[str, Any]:
    """Results-page scan: robot-ready matching + SCOUT brief on each match."""
    from app.api.robot_ready import (
        analyze_robot_capabilities,
        generate_overall_strategy,
        match_companies,
        scrape_robot_page,
    )

    url = (company_url or "").strip()
    if not url:
        return {"prospects": [], "overall_strategy": "", "error": "URL required"}

    page_text = scrape_robot_page(url) if url.startswith("http") else ""
    caps = analyze_robot_capabilities(robot_name or urlparse(url).hostname or "Robot", page_text)
    matches = match_companies(caps, db)[: max(limit, 25)]

    prospects: List[Dict[str, Any]] = []
    for m in matches[:limit]:
        cid = m.get("id")
        brief_snippet = ""
        timing = "60–90 days"
        if cid:
            try:
                dev = develop_lead_brief(db, int(cid), refresh_inference=False, include_draft=False)
                b = dev.get("brief") or {}
                brief_snippet = b.get("share_summary") or m.get("value_proposition") or ""
                timing = b.get("timing_label") or timing
            except Exception:
                brief_snippet = m.get("value_proposition") or ""

        sigs = m.get("signals") or []
        top_sig = sigs[0].get("display_text") if sigs else (m.get("key_signals") or [""])[0]
        prospects.append(
            {
                "id": str(cid) if cid else str(m.get("company_name", "")),
                "company": m.get("company_name"),
                "industry": m.get("industry"),
                "location": ", ".join(
                    p for p in (m.get("location_city"), m.get("location_state")) if p
                ),
                "score": round(m.get("match_score") or m.get("priority_score") or 0),
                "tier": m.get("priority_tier"),
                "signal": top_sig or "",
                "signalType": (sigs[0].get("signal_type") if sigs else "news") or "news",
                "timing": timing,
                "action": m.get("recommended_action") or "",
                "relevance": brief_snippet[:280] if brief_snippet else m.get("value_proposition", ""),
                "match_score": m.get("match_score"),
            }
        )

    return {
        "robot_capabilities": caps,
        "prospects": prospects,
        "matched_companies": matches[:limit],
        "overall_strategy": generate_overall_strategy(matches, caps),
        "submitted_url": url,
    }


def discovery_digest(
    db: Session,
    *,
    robot_category: Optional[str] = None,
    vertical: Optional[str] = None,
    territory: Optional[str] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """Short 'since you were away' digest from real pipeline movement."""
    discovered = discover_prospects(
        db,
        robot_category=robot_category,
        vertical=vertical,
        territory=territory,
        limit=limit,
    )
    prospects = discovered.get("prospects") or []
    if not prospects:
        return {
            "message": "No new HOT/WARM prospects match your filters right now. Try broadening territory or category.",
            "highlights": [],
            "count": 0,
        }

    lines = []
    for p in prospects[:3]:
        lines.append(
            f"{p.get('company')} ({p.get('tier')}, {p.get('score')}): {p.get('signal', '')[:80]}"
        )

    cat = _CATEGORY_FILTERS.get(_category_key(robot_category) or "", {}).get("label") or "your focus"
    message = (
        f"SCOUT surfaced {len(prospects)} live {cat} prospects. "
        + " ".join(lines[:2])
        + " Ready to develop any of them in your pipeline?"
    )
    return {
        "message": message[:500],
        "highlights": prospects,
        "count": len(prospects),
    }


def execute_activation(
    db: Session,
    activation: ScoutActivation,
    *,
    team_id: UUID,
    owner_user_id: UUID,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Run automated lead development for each lead in an activation:
    inference refresh → brief → CRM account → Cal draft.
    """
    leads = activation.leads_snapshot or []
    mode = activation.mode_choice or "manual"
    log = list(activation.activity_log or [])
    developed = 0
    errors: List[Dict[str, Any]] = []
    updated_snapshots: List[Dict[str, Any]] = []

    for lead in leads:
        if not isinstance(lead, dict):
            continue
        try:
            company_id = int(lead.get("id") or 0)
        except (TypeError, ValueError):
            errors.append({"lead": lead, "error": "invalid company id"})
            continue
        if not company_id:
            errors.append({"lead": lead, "error": "missing company id"})
            continue

        company = _load_company(db, company_id)
        if not company:
            errors.append({"company_id": company_id, "error": "not found"})
            continue

        if not dry_run:
            dev = develop_lead_brief(db, company_id, refresh_inference=True, include_draft=True)
        else:
            dev = {"brief": {}, "recommended_action": "dry_run"}

        brief = dev.get("brief") or {}
        acct = (
            db.query(CrmAccount)
            .filter(CrmAccount.team_id == team_id, CrmAccount.company_id == company_id)
            .first()
        )
        if not acct and not dry_run:
            domain = resolve_outreach_domain(company)
            guessed = infer_outreach_emails(domain, company.industry) if domain else None
            acct = CrmAccount(
                team_id=team_id,
                company_id=company_id,
                name=company.name or lead.get("company") or "Unknown",
                website=company.website,
                industry=company.industry,
                contact_email=brief.get("contact_email") or (guessed.primary if guessed else None),
                owner_user_id=owner_user_id,
                outreach_stage="draft_ready",
            )
            db.add(acct)
            db.flush()
        elif acct and not dry_run:
            if brief.get("draft_body") and not acct.outreach_draft:
                acct.outreach_draft = brief["draft_body"]
            if brief.get("contact_email") and not acct.contact_email:
                acct.contact_email = brief["contact_email"]
            acct.outreach_stage = "draft_ready"

        snap = dict(lead)
        snap.update(
            {
                "score": brief.get("intent_score") or snap.get("score"),
                "timing": brief.get("timing_label") or snap.get("timing"),
                "action": dev.get("recommended_action") or snap.get("action"),
                "relevance": brief.get("sales_angle") or snap.get("relevance"),
                "development": brief,
            }
        )
        updated_snapshots.append(snap)
        developed += 1

    if not dry_run:
        activation.leads_snapshot = updated_snapshots
        plan = dict(activation.work_plan or {})
        if updated_snapshots and len(updated_snapshots) == 1:
            b = (updated_snapshots[0].get("development") or {})
            plan.setdefault("draft_subject", b.get("draft_subject"))
            plan.setdefault("draft_body", b.get("draft_body"))
            plan.setdefault("to_email", b.get("contact_email"))
        plan["last_run"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        activation.work_plan = plan
        activation.status = "drafted" if mode == "autopilot" else "awaiting_approval"
        log.append(
            {
                "type": "discovery_run",
                "message": f"SCOUT developed {developed} lead(s): inference, brief, and Cal drafts ready for review.",
                "developed": developed,
                "errors": len(errors),
            }
        )
        activation.activity_log = log
        db.add(activation)
        db.commit()

    return {"developed": developed, "errors": errors, "status": activation.status}


def schedule_activation_run(activation_id: int, user_id: UUID, team_id: UUID) -> None:
    """Background thread — do not block activation HTTP response."""

    def _run() -> None:
        from app.database import SessionLocal

        db = SessionLocal()
        try:
            activation = db.query(ScoutActivation).filter(ScoutActivation.id == activation_id).first()
            if not activation:
                return
            activation.status = "evaluating"
            log = list(activation.activity_log or [])
            log.append({"type": "evaluating", "message": "SCOUT is running discovery and lead development."})
            activation.activity_log = log
            db.commit()
            execute_activation(db, activation, team_id=team_id, owner_user_id=user_id)
        except Exception as exc:
            logger.exception("SCOUT activation run failed id=%s: %s", activation_id, exc)
            try:
                activation = db.query(ScoutActivation).filter(ScoutActivation.id == activation_id).first()
                if activation:
                    log = list(activation.activity_log or [])
                    log.append({"type": "error", "message": str(exc)[:500]})
                    activation.activity_log = log
                    activation.status = "awaiting_approval"
                    db.commit()
            except Exception:
                db.rollback()
        finally:
            db.close()

    threading.Thread(target=_run, daemon=True, name=f"scout-activation-{activation_id}").start()
