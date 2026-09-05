"""
Cal lead drops — shareable buyer briefs for preview page, email, and in-app nudges.

Built during public cache refresh; served read-only on GET /api/leads/cal-drops.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.services.lead_filter import classify_lead, is_junk, pick_primary_score
from app.services.industry_inference import effective_industry_for_lead
from app.services.automation_profile import get_automation_profile_for_response
from app.services.lead_project_timing import resolve_project_timing
from app.services.lead_sales_copy import build_lead_intelligence_copy, humanize_robot_types
from app.services.lead_signal_display import format_signal_for_sales, strip_extraction_artifacts

logger = logging.getLogger(__name__)

_VERTICAL_PICKS: Tuple[Tuple[str, str, bool], ...] = (
    ("hospitality", "Hospitality", True),
    ("restaurant", "Restaurant / QSR", False),
    ("logistics", "Logistics", False),
)

_TIER_RANK = {"HOT": 0, "WARM": 1, "COLD": 2}


def _buyer_outreach_subject(
    company_name: str,
    industry: str,
    signal_type: str,
    *,
    pipeline_action: str = "",
) -> str:
    """Value-first subject — email TO the buyer ops team (matches the shortlist CTA)."""
    company = (company_name or "your team").strip()
    ind = (industry or "").lower()
    if "hospitality" in ind or "hotel" in ind or "casino" in ind:
        return f"{company}: robots worth a pilot (and which to skip)"
    if "food" in ind or "restaurant" in ind or "qsr" in ind:
        return f"{company}: the automation math"
    if "healthcare" in ind or "medical" in ind:
        return f"robotics that actually fit {company}"
    # Logistics, warehousing, and everything else land on the shortlist framing.
    return f"a robotics shortlist for {company}"


def _cal_personal_observation(
    tier: str,
    company_name: str,
    *,
    industry: str = "",
    signal_text: str = "",
    signal_type_label: str = "",
    why_now: str = "",
) -> str:
    """First-person Cal read on the account — professional, specific."""
    name = (company_name or "this account").strip()
    t = (tier or "").upper()
    ind = (industry or "").strip()

    detail = ""
    if signal_text:
        detail = signal_text.strip().rstrip(".")[:200]
    elif why_now:
        detail = why_now.strip().rstrip(".")[:200]

    if t == "HOT":
        if detail:
            return (
                f"My read on {name}: {detail}. "
                "Intent is elevated — I'd prioritize outreach while the window is open."
            )
        if ind:
            return (
                f"My read on {name}: multiple {ind.lower()} signals are aligning. "
                "I'd reach out this week while intent is high."
            )
        return (
            f"{name} is ranking HOT in your pipeline. "
            "Signals are strong — I'd prioritize outreach this week."
        )

    if t == "WARM":
        if detail:
            return (
                f"My read on {name}: {detail}. "
                "Not urgent, but worth developing before competitors move in."
            )
        return (
            f"{name} shows credible intent — not screaming HOT, but the signals are real. "
            "I'd validate budget and timing on a discovery call."
        )

    if detail:
        return f"My read on {name}: {detail}. I'd track for now and revisit if intent strengthens."
    return f"I'd pass on {name} for now — signal is thin. Stronger matches are in your pipeline."


def _cal_prompt_for_tier(tier: str, company_name: str) -> str:
    """Short action line after Cal's observation."""
    t = (tier or "").upper()
    name = (company_name or "this account").strip()
    if t == "HOT":
        return f"I can save {name} and hand you a send-ready draft. Move on it now?"
    if t == "WARM":
        return f"Want the full brief and talk track for {name}?"
    return f"Want me to surface stronger matches instead of {name}?"


def _recommended_action(tier: str) -> str:
    t = (tier or "").upper()
    if t == "HOT":
        return "Send Cal outreach within 48 hours while the signal is fresh."
    if t == "WARM":
        return "Book a 30-minute discovery to validate budget and deployment scope."
    return "Track only — wait for stronger intent."


def build_cal_drop_for_company(
    db: Session,
    company: Company,
    *,
    vertical_label: str = "",
) -> Optional[Dict[str, Any]]:
    """One Cal drop card — no DB writes."""
    junk, junk_reason = is_junk(company.name)
    if junk:
        return None

    _, _, pri = classify_lead(company, company.scores, company.signals)
    score_row = pick_primary_score(company.scores)
    intent = float(score_row.overall_intent_score or 0) if score_row else 0.0
    tier = (pri.tier or "COLD").upper()

    sigs = company.signals or []
    signal_types: List[str] = []
    signal_labels: List[str] = []
    for sig in sigs[:8]:
        st = getattr(sig, "signal_type", None)
        if st:
            signal_types.append(str(st))
            signal_labels.append(str(st).replace("_", " ").title())

    signal_blob = " ".join(
        strip_extraction_artifacts(getattr(s, "signal_text", None)) for s in sigs[:12]
    )
    top_sig = sigs[0] if sigs else None
    signal_text = ""
    signal_type_label = ""
    if top_sig:
        signal_text = format_signal_for_sales(getattr(top_sig, "signal_text", None) or "")[:240]
        signal_type_label = (getattr(top_sig, "signal_type", None) or "signal").replace("_", " ").title()

    industry_display = effective_industry_for_lead(company.name, company.industry, company.signals) or "New"
    crm_meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    inf = crm_meta.get("lead_inference") if isinstance(crm_meta.get("lead_inference"), dict) else {}

    timing = resolve_project_timing(
        tier=tier,
        crm_metadata=crm_meta,
        lead_inference=inf if isinstance(inf, dict) else None,
        signal_blob=signal_blob,
        signal_types=signal_types,
        intent_score=intent,
    )

    automation_profile = get_automation_profile_for_response(company, industry_override=industry_display)
    automation_type = (automation_profile or {}).get("primary_type") or "automation"
    pain_point = (inf or {}).get("specific_problem") or ""

    share_blurb, share_summary = build_lead_intelligence_copy(
        company_name=company.name or "This company",
        industry=industry_display,
        tier=tier,
        signal_labels=signal_labels,
        signal_types=signal_types,
        automation_type=automation_type,
        pain_point=pain_point,
        automation_profile=automation_profile,
        crm_metadata=crm_meta,
        signal_blob=signal_blob,
        intent_score=intent,
    )

    robot_fit = humanize_robot_types(
        automation_profile,
        industry=industry_display,
        signal_blob=signal_blob,
    )[:4]

    from app.api.crm import _draft_buyer_body
    from app.models.crm import CrmAccount
    from app.services.pipeline_action_copy import pipeline_action_for_lead

    unique_types = list(dict.fromkeys(signal_types))[:4]
    pipeline_action = pipeline_action_for_lead(industry_display, tier=tier, signal_types=unique_types)

    buyer_acct = CrmAccount(
        name=company.name or "Unknown",
        website=company.website,
        industry=industry_display,
        account_type="buyer",
    )
    draft_body = _draft_buyer_body(buyer_acct, None, [], "none", None)
    draft_subject = _buyer_outreach_subject(
        company.name or "",
        industry_display,
        signal_type_label,
        pipeline_action=pipeline_action,
    )

    loc_parts = [p for p in (company.location_city, company.location_state) if p]
    why_now = (inf or {}).get("specific_problem") or share_summary or share_blurb or signal_text

    return {
        "id": company.id,
        "company_name": company.name,
        "tier": tier,
        "intent_score": round(intent, 1),
        "industry": industry_display,
        "location": ", ".join(loc_parts) if loc_parts else "",
        "vertical_label": vertical_label or industry_display,
        "why_now": (why_now or "")[:500],
        "robot_fit": robot_fit,
        "timing": timing.display_phrase,
        "pipeline_action": pipeline_action,
        "signal_type": signal_type_label,
        "signal_text": signal_text,
        "draft_subject": draft_subject,
        "draft_body": draft_body,
        "cal_observation": _cal_personal_observation(
            tier,
            company.name or "",
            industry=industry_display,
            signal_text=signal_text,
            signal_type_label=signal_type_label,
            why_now=why_now or "",
        ),
        "cal_prompt": _cal_prompt_for_tier(tier, company.name or ""),
        "recommended_action": _recommended_action(tier),
        "share_blurb": share_blurb,
    }


def _pick_best_from_cards(
    db: Session,
    cards: List[dict],
    *,
    vertical_label: str,
    prefer_hot: bool,
    seen_ids: set[int],
) -> Optional[Dict[str, Any]]:
    ranked: List[tuple] = []
    for card in cards:
        cid = int(card.get("id") or 0)
        if not cid or cid in seen_ids:
            continue
        tier = (card.get("priority_tier") or "COLD").upper()
        if prefer_hot and tier != "HOT":
            continue
        raw_score = card.get("priority_score")
        if raw_score is None and isinstance(card.get("score"), dict):
            raw_score = card["score"].get("overall_score")
        score = float(raw_score or 0)
        ranked.append((_TIER_RANK.get(tier, 9), -score, cid, tier))

    if not ranked and prefer_hot:
        for card in cards:
            cid = int(card.get("id") or 0)
            if not cid or cid in seen_ids:
                continue
            tier = (card.get("priority_tier") or "COLD").upper()
            score = float(card.get("priority_score") or 0)
            ranked.append((_TIER_RANK.get(tier, 9), -score, cid, tier))

    if not ranked:
        return None

    ranked.sort()
    company = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id == ranked[0][2])
        .first()
    )
    if not company:
        return None
    drop = build_cal_drop_for_company(db, company, vertical_label=vertical_label)
    if drop:
        seen_ids.add(company.id)
    return drop


def build_cal_lead_drops_preview(db: Session, *, limit: int = 3) -> Dict[str, Any]:
    """Curated Cal drops across hospitality, restaurant, logistics."""
    from datetime import datetime, timezone

    from app.api.leads import build_industry_search_leads_list

    seen: set[int] = set()
    drops: List[Dict[str, Any]] = []

    for query, label, prefer_hot in _VERTICAL_PICKS:
        if len(drops) >= limit:
            break
        cards = build_industry_search_leads_list(db, query, limit=50)
        drop = _pick_best_from_cards(
            db, cards, vertical_label=label, prefer_hot=prefer_hot, seen_ids=seen
        )
        if drop:
            drops.append(drop)

    if len(drops) < limit:
        from app.api.leads import build_public_leads_list

        hot_cards = build_public_leads_list(db, limit=12, tier="HOT")
        for card in hot_cards:
            if len(drops) >= limit:
                break
            drop = _pick_best_from_cards(
                db, [card], vertical_label="Pipeline", prefer_hot=False, seen_ids=seen
            )
            if drop:
                drops.append(drop)

    return {
        "headline": "Cal's pipeline brief",
        "subhead": "Priority accounts with Cal's read, robot fit, and send-ready outreach.",
        "drops": drops,
        "count": len(drops),
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
