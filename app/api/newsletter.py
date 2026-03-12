"""
Newsletter API
==============
GET /api/newsletter/edition

Returns fresh newsletter content for the daily brief:
- Top hot leads with actionable signals
- Formatted for social sharing
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.lead_filter import classify_lead, is_junk
from app.services.signal_ranker import compute_weighted_score

router = APIRouter()

SIGNAL_CATEGORIES = {
    "labor_shortage": "LABOR SHORTAGE",
    "expansion": "EXPANSION",
    "strategic_hire": "STRATEGIC HIRE",
    "capex": "CAPEX",
    "funding_round": "FUNDING",
    "ma_activity": "M&A",
    "job_posting": "JOB POSTING",
    "news": "DEPLOYMENT",
    "automation_interest": "AUTOMATION INTEREST",
    "labor_signal": "LABOR",
    "hospitality_fit": "HOSPITALITY",
    "pilot_success": "PILOT SUCCESS",
}


def _truncate(text: str, max_len: int) -> str:
    if not text:
        return ""
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."


@router.get("/edition")
def get_newsletter_edition(
    limit: int = Query(8, description="Max top stories"),
    db: Session = Depends(get_db),
):
    """
    Fresh newsletter edition: hot leads with actionable signals.
    Used by the newsletter page for daily brief and social sharing.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")
    edition = f"#{now.strftime('%j')}"  # Day of year as edition number

    # Fetch companies with scores and signals, ordered by signal activity
    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .limit(500)
        .all()
    )

    stories = []
    for c in companies:
        junk, _, pri = classify_lead(c, c.scores, c.signals)
        if junk or not c.signals:
            continue
        # Prefer HOT/WARM
        if pri.tier not in ("HOT", "WARM"):
            continue

        sigs = sorted(c.signals, key=lambda s: (s.signal_strength or 0), reverse=True)
        top_sig = sigs[0]
        sig_type = top_sig.signal_type or "news"
        category = SIGNAL_CATEGORIES.get(sig_type, sig_type.upper().replace("_", " "))

        # Headline from signal text or company + signal type
        raw = (top_sig.signal_text or "").strip()
        if len(raw) > 60:
            headline = _truncate(raw, 80)
        else:
            headline = f"{c.name or 'Company'}: {_truncate(raw, 70)}" if raw else f"{c.name} — {category}"

        snippet = _truncate(raw, 120) if raw else f"Buying signal detected for {c.name} in {c.industry or 'automation'}."

        # Build full text from all signals
        full_parts = [f"**{c.name}** ({c.industry or 'N/A'})"]
        for s in sigs[:5]:
            txt = (s.signal_text or "").strip()
            if txt:
                full_parts.append(f"• [{s.signal_type or 'signal'}]: {txt}")
        if c.website:
            full_parts.append(f"\n🔗 {c.website}")
        fullText = "\n\n".join(full_parts)

        score = (c.scores.overall_intent_score if c.scores else 0) or pri.score
        signal_strength = min(10, max(1, int(score / 10)))

        stories.append({
            "category": category,
            "company": c.name or "Unknown",
            "headline": headline,
            "snippet": snippet,
            "roi": "High intent" if pri.tier == "HOT" else "Warm lead",
            "economics": f"{c.industry or 'Automation'} · {len(sigs)} signals",
            "impact": f"Score {round(score, 0)}/100",
            "signalStrength": signal_strength,
            "fullText": fullText,
            "company_id": c.id,
            "_sort_score": (2 if pri.tier == "HOT" else 1) * score,
        })

    stories.sort(key=lambda x: x.pop("_sort_score", 0), reverse=True)
    stories = stories[:limit]

    # Headline from top story or generic
    if stories:
        top = stories[0]
        main_headline = f"{top['company']}: {_truncate(top.get('headline', '').replace(top['company'] + ': ', ''), 60)}"
        subheadline = f"{len(stories)} hot leads with actionable signals — {top.get('category', '')} leading"
    else:
        main_headline = "Automation Sales Leads with Actionable Signals"
        subheadline = "Daily roundup of robot-ready companies and buying intent. Subscribe for fresh leads."

    return {
        "latestEdition": {
            "date": date_str,
            "edition": edition,
            "headline": main_headline,
            "subheadline": subheadline,
        },
        "topStories": stories,
        "summary": {
            "total_leads": len(stories),
            "generated_at": now.isoformat(),
        },
    }
