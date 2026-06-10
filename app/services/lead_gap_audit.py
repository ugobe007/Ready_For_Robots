"""
Lead gap audit — pillar 1 of secondary logic: find missing sales-lead data.

Secondary pipeline (decoupled from scrapers):
  1. Missing data   — this module (gaps + candidate ranking)
  2. Optimize data  — rescue passes normalize industry, identity, CRM fields
  3. Quality gate   — rectifier + classify_lead (junk vs sales lead)
  4. Additional data — agent QA, ontology, procurement/timing cues
  5. Opportunity rank — lead_secondary_assessment (value of data for the sale)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, List, Optional, Sequence

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.signal import Signal
from app.services.lead_primary_link import enrich_lead_link_fields
from app.services.lead_filter import pick_primary_score

# Ordered rescue passes (run only when the corresponding gap is open).
PASS_WEBSITE = "website_rescue"
PASS_INDUSTRY = "industry_rescue"
PASS_CONTACT = "contact_rescue"
PASS_CRM = "crm_rescue"
PASS_INFERENCE = "inference_rescue"
PASS_SIGNALS = "signal_backfill"
PASS_RECTIFY = "rectification"
PASS_AGENT_QA = "agent_qa"

GAP_TO_PASS = {
    "website": PASS_WEBSITE,
    "industry": PASS_INDUSTRY,
    "contact": PASS_CONTACT,
    "crm_descriptors": PASS_CRM,
    "lead_inference": PASS_INFERENCE,
    "low_signals": PASS_SIGNALS,
    "unrectified": PASS_RECTIFY,
    "ontology_gaps": PASS_AGENT_QA,
}

_UNKNOWN_INDUSTRY = frozenset({"", "unknown", "other", "new", "unclassified"})


@dataclass
class LeadGapReport:
    company_id: int
    company_name: str
    gaps: List[str] = field(default_factory=list)
    passes: List[str] = field(default_factory=list)
    priority: float = 0.0
    overall_score: float = 0.0
    signal_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "gaps": list(self.gaps),
            "passes": list(self.passes),
            "priority": round(self.priority, 2),
            "overall_score": round(self.overall_score, 2),
            "signal_count": self.signal_count,
        }


def _crm_meta(company: Company) -> dict:
    raw = getattr(company, "crm_metadata", None)
    return raw if isinstance(raw, dict) else {}


def _has_verified_email(contacts: Sequence[Contact]) -> bool:
    for c in contacts or []:
        email = (getattr(c, "email", None) or "").strip()
        if email and "@" in email:
            return True
    return False


def _has_decision_maker(contacts: Sequence[Contact], crm_meta: dict) -> bool:
    outreach = (crm_meta.get("outreach_email") or "").strip()
    if outreach and "@" in outreach:
        return True
    if _has_verified_email(contacts):
        return True
    for c in contacts or []:
        if (getattr(c, "title", None) or "").strip():
            return True
    dms = crm_meta.get("decision_makers")
    if isinstance(dms, list) and dms:
        return True
    inf = crm_meta.get("lead_inference")
    if isinstance(inf, dict) and (inf.get("decision_makers") or inf.get("contacts")):
        return True
    return False


def audit_company_gaps(
    company: Company,
    signals: Sequence[Signal],
    contacts: Sequence[Contact],
    *,
    overall_score: float = 0.0,
) -> LeadGapReport:
    """Return open gaps and suggested rescue passes for one lead."""
    gaps: List[str] = []
    sigs = list(signals or [])
    sig_count = len(sigs)
    score = float(overall_score or 0.0)
    meta = _crm_meta(company)
    ledger = meta.get("enrichment_ledger")
    if not isinstance(ledger, dict):
        ledger = {}

    link = enrich_lead_link_fields(
        website=company.website,
        signals=[{"source_url": getattr(s, "source_url", None)} for s in sigs[:12]],
        overall_score=score,
        signal_count=sig_count,
    )
    if link.get("needs_website_inference"):
        gaps.append("website")

    stored_industry = (company.industry or "").strip().lower()
    if stored_industry in _UNKNOWN_INDUSTRY:
        gaps.append("industry")

    if not _has_decision_maker(contacts, meta):
        gaps.append("contact")

    budget = meta.get("budget") if isinstance(meta.get("budget"), dict) else {}
    timing = meta.get("timing") if isinstance(meta.get("timing"), dict) else {}
    has_budget = bool(budget.get("signals") or budget.get("top_amount"))
    has_timing = bool(
        timing.get("signals")
        or timing.get("top_window")
        or meta.get("project_timing")
    )
    has_automation_reqs = bool(meta.get("automation_requirements"))
    if not (has_budget or has_timing or has_automation_reqs):
        gaps.append("crm_descriptors")

    inf = meta.get("lead_inference")
    if not isinstance(inf, dict) or not inf.get("specific_problem"):
        gaps.append("lead_inference")

    if score >= 40 and sig_count < 2:
        gaps.append("low_signals")

    if ledger.get(PASS_RECTIFY, {}).get("status") != "passed":
        gaps.append("unrectified")

    agent = meta.get("agent_enrichment")
    if isinstance(agent, dict) and agent.get("ontology_gaps"):
        gaps.append("ontology_gaps")
    elif score >= 55 and not isinstance(agent, dict):
        gaps.append("ontology_gaps")

    passes = list(dict.fromkeys(GAP_TO_PASS[g] for g in gaps if g in GAP_TO_PASS))

    # Higher-score leads with identity gaps are repaired first (sales-ready corpus).
    priority = score
    if "website" in gaps:
        priority += 25
    if "contact" in gaps:
        priority += 15
    if "lead_inference" in gaps:
        priority += 10
    if "industry" in gaps:
        priority += 8
    priority += min(sig_count, 5) * 2

    # Never secondary-processed leads get priority over stale complete rows.
    if not ledger:
        priority += 30
    elif not any(
        isinstance(ledger.get(k), dict) and ledger[k].get("last_run")
        for k in GAP_TO_PASS.values()
    ):
        priority += 20

    return LeadGapReport(
        company_id=int(company.id),
        company_name=company.name or "",
        gaps=gaps,
        passes=passes,
        priority=priority,
        overall_score=score,
        signal_count=sig_count,
    )


def select_gap_repair_candidates(
    db: Session,
    *,
    limit: int = 100,
    min_score: float = 0.0,
    require_gaps: Optional[Iterable[str]] = None,
) -> List[LeadGapReport]:
    """
    Rank internal leads with at least one signal by gap priority.
    Returns reports for companies that still have open gaps.
    """
    from app.models.score import Score

    cap = max(1, min(int(limit), 500))
    pool = min(cap * 4, 800)

    rows = (
        db.query(Company)
        .filter(Company.is_internal.is_(True))
        .join(Signal, Signal.company_id == Company.id)
        .outerjoin(Score, Score.company_id == Company.id)
        .group_by(Company.id)
        .order_by(desc(func.coalesce(func.max(Score.overall_intent_score), 0)), desc(Company.id))
        .limit(pool)
        .all()
    )

    require = set(require_gaps or [])
    reports: List[LeadGapReport] = []

    for company in rows:
        signals = (
            db.query(Signal)
            .filter(Signal.company_id == company.id)
            .order_by(Signal.created_at.desc())
            .limit(20)
            .all()
        )
        if not signals:
            continue
        contacts = db.query(Contact).filter(Contact.company_id == company.id).limit(10).all()
        score_row = pick_primary_score(company.scores)
        overall = float(score_row.overall_intent_score or 0) if score_row else 0.0
        if overall < min_score:
            continue

        report = audit_company_gaps(company, signals, contacts, overall_score=overall)
        if not report.gaps:
            continue
        if require and not require.intersection(report.gaps):
            continue
        reports.append(report)

    reports.sort(key=lambda r: r.priority, reverse=True)
    return reports[:cap]


def ledger_cooldown_ok(
    company: Company,
    pass_name: str,
    *,
    cooldown_hours: int = 24,
) -> bool:
    """True if this pass may run again (never run, failed, or cooldown elapsed)."""
    meta = _crm_meta(company)
    ledger = meta.get("enrichment_ledger")
    if not isinstance(ledger, dict):
        return True
    entry = ledger.get(pass_name)
    if not isinstance(entry, dict):
        return True
    if entry.get("status") in ("failed", "skipped"):
        return True
    last = entry.get("last_run")
    if not last:
        return True
    try:
        ts = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return True
    age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
    return age_h >= cooldown_hours


def stamp_ledger_entry(
    company: Company,
    pass_name: str,
    *,
    status: str,
    detail: Optional[str] = None,
    fields_filled: Optional[List[str]] = None,
) -> None:
    """Persist idempotent pass outcome on company.crm_metadata.enrichment_ledger."""
    meta = dict(_crm_meta(company))
    ledger = dict(meta.get("enrichment_ledger") or {})
    ledger[pass_name] = {
        "status": status,
        "last_run": datetime.now(timezone.utc).isoformat(),
        "detail": (detail or "")[:500] or None,
        "fields_filled": list(fields_filled or []),
    }
    meta["enrichment_ledger"] = ledger
    company.crm_metadata = meta
