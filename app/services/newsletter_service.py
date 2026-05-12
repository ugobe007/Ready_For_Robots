"""
Newsletter edition generation — shared logic for API and Celery task.
Generates top stories from hot/warm leads for daily brief and social sharing.
"""
import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.score import Score
from app.models.signal import Signal
from app.services.lead_filter import classify_lead, pick_primary_score
from app.services.industry_brief_service import build_industry_brief_payload

def _industry_display(raw) -> str:
    """Never expose 'Unknown' in newsletter content."""
    s = (raw or "").strip()
    return s if s and s.lower() not in ("unknown", "other") else "New"

SIGNAL_CATEGORIES = {
    "labor_shortage": "Labor Shortage",
    "expansion": "Expansion",
    "strategic_hire": "Leadership Hire",
    "capex": "CapEx Budget",
    "funding_round": "Funding Round",
    "ma_activity": "M&A Activity",
    "job_posting": "Job Posting",
    "news": "News Signal",
    "automation_interest": "Automation Interest",
    "automation_intent": "Automation Intent",
    "labor_signal": "Labor Signal",
    "labor_pain": "Labor Pain",
    "pilot_success": "Pilot Success",
    "robot_installation": "Robot Deployment",
    "roi_documented": "ROI Documented",
    "vendor_selection": "Vendor Selection",
    "scale_expansion": "Scale-Up",
    "competitive_response": "Competitive Pressure",
    "economics_driven": "Economics Trigger",
    "problem_solution": "Problem-Solution",
    "quality_bottleneck": "Quality Problem",
    "safety_incident": "Safety Incident",
    "production_capacity": "At Capacity",
    "warehouse_throughput": "Warehouse Bottleneck",
    "packaging_automation": "Packaging Automation",
    "repetitive_process": "Repetitive Tasks",
    "material_handling": "Material Handling",
    "service_consistency": "Service Consistency",
    "equipment_integration": "Equipment Integration",
    "rfp_posted": "RFP Posted",
    "government_contract": "Gov Contract",
}

# Industry-specific automation framing used in summaries
_INDUSTRY_AUTOMATION_CONTEXT = {
    "logistics": ("autonomous mobile robots (AMRs), conveyor systems, and warehouse automation", "labor-intensive picking, packing, and last-mile delivery"),
    "supply chain": ("AMRs and warehouse orchestration software", "throughput bottlenecks and labor shortages"),
    "warehouse": ("AMRs, AS/RS, and goods-to-person systems", "picking efficiency and labor replacement"),
    "fulfillment": ("goods-to-person robots and automated conveyor systems", "order fulfillment speed and accuracy"),
    "hospitality": ("room service robots, housekeeping assist, and front-desk automation", "labor vacancies and guest experience consistency"),
    "hotel": ("delivery robots and back-of-house automation", "housekeeping labor shortages and service consistency"),
    "healthcare": ("hospital logistics robots, medication dispensing, and disinfection bots", "staff walking time and infection control"),
    "hospital": ("logistics robots and UV disinfection systems", "staff redeployment and patient safety"),
    "food service": ("kitchen automation, prep robots, and order fulfillment systems", "labor shortages and food consistency"),
    "restaurant": ("kitchen automation and front-of-house robots", "staff turnover and order accuracy"),
    "manufacturing": ("collaborative robots (cobots), welding automation, and assembly systems", "labor costs and quality control"),
    "food & beverage": ("packaging automation and processing robots", "labor costs and production throughput"),
}

def _industry_automation_context(industry: str) -> tuple:
    """Returns (automation_type, pain_point) for the given industry."""
    low = (industry or "").lower()
    for key, val in _INDUSTRY_AUTOMATION_CONTEXT.items():
        if key in low:
            return val
    return ("robotic automation", "operational efficiency and labor costs")


def _sig_label(signal_type: str) -> str:
    return SIGNAL_CATEGORIES.get(signal_type, signal_type.replace("_", " ").title())


def _company_size_descriptor(employee_estimate: Optional[int]) -> str:
    if not employee_estimate:
        return ""
    if employee_estimate >= 10000:
        return "large enterprise"
    if employee_estimate >= 5000:
        return "enterprise"
    if employee_estimate >= 1000:
        return "mid-market"
    if employee_estimate >= 200:
        return "growth-stage"
    return "small-to-mid-size"


def _tier_buy_window(tier: str, score: float) -> str:
    if tier == "HOT":
        return (
            f"With a composite score of {round(score)}/100, this is a high-confidence buyer — "
            "likely evaluating automation vendors within the next 60–90 days."
        )
    if tier == "WARM":
        return (
            f"Scoring {round(score)}/100, this account is in active exploration — "
            "a well-timed outreach now can shape the vendor shortlist before a decision is made."
        )
    return f"At {round(score)}/100, this is an early-stage opportunity worth monitoring for escalating signals."


def _intelligence_summary(
    name: str,
    industry: str,
    location_city: Optional[str],
    location_state: Optional[str],
    employee_estimate: Optional[int],
    pri,
    sigs: list,
    deduped_sigs: list,
) -> str:
    """
    Generates a 4-5 sentence intelligence paragraph leading with:
    '[Company] is targeting automation for their [use_case] due to [pain_point]
    which align with our signals [types]. The timing of the project is [X] months.'
    """
    ind = _industry_display(industry)
    loc = ""
    if location_city and location_state:
        loc = f", based in {location_city}, {location_state}"
    elif location_state:
        loc = f", based in {location_state}"

    size = _company_size_descriptor(employee_estimate)
    size_str = f"{size} " if size else ""
    automation_type, pain_point = _industry_automation_context(industry)

    # Signal labels
    unique_types = list(dict.fromkeys([getattr(s, "signal_type", "") for s in deduped_sigs]))[:4]
    labels = [_sig_label(t) for t in unique_types if t]
    signals_str = ", ".join(labels[:3]) if labels else "automation interest"

    buy_months = "60–90" if pri.tier == "HOT" else "90–120"

    # Sentence 1 — the intelligence-led hook (user's requested template)
    s1 = (
        f"{name} is targeting automation for their {automation_type} "
        f"due to {pain_point}, which aligns with our signals: {signals_str}. "
        f"The timing of this project is within {buy_months} days."
    )

    # Sentence 2 — company context + location
    loc_str = f" {loc.strip(',').strip()}" if loc else ""
    s2 = f"{name} is a {size_str}{ind} company{loc} with {len(sigs)} active buying indicators in our database."

    # Sentence 3 — strongest evidence (clean, no raw HTML)
    top = deduped_sigs[0] if deduped_sigs else None
    s3 = ""
    if top:
        import re as _re
        raw = (getattr(top, "signal_text", None) or "").replace("\n", " ").strip()
        raw = _re.sub(r"<[^>]+>", "", raw).strip()
        label = _sig_label(getattr(top, "signal_type", ""))
        if raw and len(raw) > 20:
            excerpt = raw[:180] + ("…" if len(raw) > 180 else "")
            s3 = f'Key evidence — {label}: "{excerpt}"'
        else:
            s3 = f"The leading indicator is a {label}, consistent with companies actively evaluating {automation_type}."

    # Sentence 4 — qualifying reasons
    reasons = pri.reasons or []
    s4 = f"Qualifying factors: {'; '.join(reasons[:2])}." if reasons else ""

    parts = [s1, s2]
    if s3:
        parts.append(s3)
    if s4:
        parts.append(s4)
    return " ".join(p for p in parts if p)


def _intelligence_fulltext(
    name: str,
    industry: str,
    website: Optional[str],
    pri,
    sigs: list,
    deduped_sigs: list,
    summary: str,
) -> str:
    """
    Full expanded story body: intelligence paragraph + structured signal breakdown.
    """
    ind = _industry_display(industry)
    automation_type, _ = _industry_automation_context(industry)

    lines = [f"**{name}** ({ind})\n", summary, ""]

    # Signal breakdown
    if deduped_sigs:
        lines.append("**Buying signals detected:**")
        for s in deduped_sigs[:5]:
            label = _sig_label(getattr(s, "signal_type", "signal"))
            raw = (getattr(s, "signal_text", None) or "").replace("\n", " ").strip()
            excerpt = (raw[:200] + "…" if len(raw) > 200 else raw) if raw else "(no text)"
            strength = getattr(s, "signal_strength", None)
            strength_str = f" [{int((strength or 0) * 100)}% strength]" if strength else ""
            lines.append(f"• **{label}**{strength_str}: {excerpt}")
        lines.append("")

    # Automation fit note
    lines.append(f"**Automation fit:** {name} matches the profile for {automation_type}.")
    if pri.reasons:
        lines.append(f"**Qualifiers:** {' · '.join(pri.reasons[:3])}")

    if website:
        lines.append(f"\n🔗 {website}")

    return "\n".join(lines)


def _truncate(text: str, max_len: int) -> str:
    if not text:
        return ""
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."


def get_cache_path() -> Path:
    """Path to cached newsletter edition JSON (persists for 24h)."""
    env_path = os.getenv("NEWSLETTER_CACHE_DIR")
    if env_path and Path(env_path).is_absolute():
        base = Path(env_path)
    else:
        # Project root (parent of app/)
        base = Path(__file__).resolve().parent.parent.parent
        if env_path:
            base = base / env_path
    cache_dir = base / "data"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "newsletter_latest.json"


def _recency_sort_key(created_at) -> tuple:
    """Sort key: newer = better. Returns (days_ago, 0) for oldest-first ordering."""
    if not created_at:
        return (999, 0)  # No date = treat as very old
    now = datetime.now(timezone.utc)
    if isinstance(created_at, datetime) and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    days_ago = (now - created_at).total_seconds() / 86400
    return (days_ago, 0)


def generate_edition(db: Session, limit: int = 8) -> Dict[str, Any]:
    """
    Generate newsletter edition from hot/warm leads.
    Prioritizes RECENT signals so each day shows fresh content.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")
    edition = f"#{now.strftime('%j')}"

    # Highest-intent companies with at least one signal (not an arbitrary first-500 slice)
    ranked_ids = (
        db.query(Company.id)
        .join(Signal, Signal.company_id == Company.id)
        .outerjoin(Score, Score.company_id == Company.id)
        .group_by(Company.id)
        .order_by(func.coalesce(func.max(Score.overall_intent_score), 0).desc())
        .limit(900)
        .all()
    )
    id_list = [r[0] for r in ranked_ids]
    if not id_list:
        companies = []
    else:
        companies = (
            db.query(Company)
            .options(joinedload(Company.scores), joinedload(Company.signals))
            .filter(Company.id.in_(id_list))
            .all()
        )
        rank = {cid: i for i, cid in enumerate(id_list)}
        companies.sort(key=lambda c: rank.get(c.id, 9999))

    stories: List[Dict] = []
    for c in companies:
        junk, _, pri = classify_lead(c, c.scores, c.signals)
        if junk or not c.signals:
            continue
        if pri.tier not in ("HOT", "WARM"):
            continue

        sigs = sorted(c.signals, key=lambda s: (s.signal_strength or 0), reverse=True)
        latest_at = max(
            (getattr(s, "created_at", None) for s in c.signals if getattr(s, "created_at", None)),
            default=None,
        )

        # Deduplicate by signal type (best per type, strongest first)
        seen_types: set = set()
        deduped: list = []
        for s in sigs:
            t = getattr(s, "signal_type", None) or "unknown"
            if t not in seen_types:
                seen_types.add(t)
                deduped.append(s)
            if len(deduped) >= 5:
                break

        top_sig = deduped[0] if deduped else sigs[0]
        sig_type = top_sig.signal_type or "news"
        category = SIGNAL_CATEGORIES.get(sig_type, sig_type.replace("_", " ").title())

        # Build intelligence summary (4-5 sentences — the key upgrade)
        name = c.name or "Company"
        ind = _industry_display(c.industry)
        ps = pick_primary_score(c.scores)
        score = (ps.overall_intent_score if ps else 0) or pri.score

        summary = _intelligence_summary(
            name=name,
            industry=c.industry or "",
            location_city=c.location_city,
            location_state=c.location_state,
            employee_estimate=c.employee_estimate,
            pri=pri,
            sigs=sigs,
            deduped_sigs=deduped,
        )

        fullText = _intelligence_fulltext(
            name=name,
            industry=c.industry or "",
            website=c.website,
            pri=pri,
            sigs=sigs,
            deduped_sigs=deduped,
            summary=summary,
        )

        # Headline: company name + leading signal type — not raw scraped text
        automation_type, pain_point = _industry_automation_context(c.industry or "")
        headline = f"{name}: {_sig_label(sig_type)} Signal Detected"

        # Snippet: first 2 sentences of summary (shows under headline in collapsed view)
        sentences = summary.split(". ")
        snippet = ". ".join(sentences[:2]).strip()
        if not snippet.endswith("."):
            snippet += "."

        signal_strength = min(10, max(1, int(score / 10)))
        base_score = (2 if pri.tier == "HOT" else 1) * score
        recency_key = _recency_sort_key(latest_at)

        # roi/economics/impact — contextual, not generic
        unique_label_str = ", ".join([_sig_label(getattr(s, "signal_type", "")) for s in deduped[:2]])
        tier_label = "High intent" if pri.tier == "HOT" else "In-market"

        stories.append({
            "category": category,
            "company": name,
            "headline": headline,
            "snippet": snippet,
            "summary": summary,           # ← 4-5 sentence intelligence paragraph
            "roi": tier_label,
            "economics": f"{ind} · {len(sigs)} signals",
            "impact": f"Score {round(score)}/100",
            "signalStrength": signal_strength,
            "fullText": fullText,
            "company_id": c.id,
            "_recency": recency_key,
            "_score": base_score,
        })

    # Sort: recency first (newest signals), then score — fresh content wins.
    # Rotate within the top pool each day so the public brief does not freeze on
    # the same headlines when the highest-scored signal set is unchanged.
    stories.sort(key=lambda x: (x.pop("_recency", (999, 0)), -x.pop("_score", 0)))

    if len(stories) > limit:
        day_seed = int(now.strftime("%j"))
        pool_size = min(24, len(stories))
        top_pool = stories[:pool_size]
        start_idx = (day_seed * 7) % pool_size
        rotated_pool = top_pool[start_idx:] + top_pool[:start_idx]
        stories = rotated_pool[:limit]
    else:
        stories = stories[:limit]

    if stories:
        top = stories[0]
        main_headline = f"{top['company']}: {_truncate(top.get('headline', '').replace(top['company'] + ': ', ''), 60)}"
        subheadline = f"{len(stories)} hot leads with actionable signals — {top.get('category', '')} leading"
    else:
        main_headline = "Automation Sales Leads with Actionable Signals"
        subheadline = "Daily roundup of robot-ready companies and buying intent. Subscribe for fresh leads."

    industry_brief = build_industry_brief_payload(
        db,
        days=1,
        analytics=None,
        use_cache=True,
        force_refresh=False,
    )
    return {
        "latestEdition": {
            "date": date_str,
            "edition": edition,
            "headline": main_headline,
            "subheadline": subheadline,
        },
        "industryBrief": industry_brief,
        "topStories": stories,
        "summary": {
            "total_leads": len(stories),
            "generated_at": now.isoformat(),
        },
    }


def read_cached_edition(max_age_hours: float = 1.5) -> Optional[Dict[str, Any]]:
    """Read cached edition if it exists and is fresh. Returns None if stale or missing."""
    path = get_cache_path()
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        gen = data.get("summary", {}).get("generated_at")
        if not gen:
            return None
        gen_dt = datetime.fromisoformat(gen.replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - gen_dt
        # A "daily" brief should turn over with the calendar even if the prior cache
        # is still within its hour-based TTL.
        if gen_dt.date() != datetime.now(timezone.utc).date():
            return None
        if age > timedelta(hours=max_age_hours):
            return None
        return data
    except Exception:
        return None


def write_cached_edition(data: Dict[str, Any]) -> None:
    """Write edition to cache file."""
    path = get_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
