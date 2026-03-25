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
from app.services.lead_filter import classify_lead
from app.services.industry_brief_service import build_industry_brief_payload

def _industry_display(raw) -> str:
    """Never expose 'Unknown' in newsletter content."""
    s = (raw or "").strip()
    return s if s and s.lower() not in ("unknown", "other") else "New"

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
    "robot_installation": "ROBOT DEPLOYMENT",
    "roi_documented": "ROI",
    "vendor_selection": "VENDOR SELECTION",
    "scale_expansion": "SCALE-UP",
    "competitive_response": "COMPETITIVE",
    "economics_driven": "ECONOMICS",
    "problem_solution": "PROBLEM-SOLUTION",
}


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
        top_sig = sigs[0]
        latest_at = max(
            (getattr(s, "created_at", None) for s in c.signals if getattr(s, "created_at", None)),
            default=None,
        )
        sig_type = top_sig.signal_type or "news"
        category = SIGNAL_CATEGORIES.get(sig_type, sig_type.upper().replace("_", " "))

        raw = (top_sig.signal_text or "").strip()
        if len(raw) > 60:
            headline = _truncate(raw, 80)
        else:
            headline = f"{c.name or 'Company'}: {_truncate(raw, 70)}" if raw else f"{c.name} — {category}"

        snippet = _truncate(raw, 120) if raw else f"Buying signal detected for {c.name} in {_industry_display(c.industry) or 'automation'}."

        full_parts = [f"**{c.name}** ({_industry_display(c.industry)})"]
        for s in sigs[:5]:
            txt = (s.signal_text or "").strip()
            if txt:
                full_parts.append(f"• [{s.signal_type or 'signal'}]: {txt}")
        if c.website:
            full_parts.append(f"\n🔗 {c.website}")
        fullText = "\n\n".join(full_parts)

        score = (c.scores.overall_intent_score if c.scores else 0) or pri.score
        signal_strength = min(10, max(1, int(score / 10)))

        base_score = (2 if pri.tier == "HOT" else 1) * score
        recency_key = _recency_sort_key(latest_at)
        stories.append({
            "category": category,
            "company": c.name or "Company",
            "headline": headline,
            "snippet": snippet,
            "roi": "High intent" if pri.tier == "HOT" else "Warm lead",
            "economics": f"{_industry_display(c.industry)} · {len(sigs)} signals",
            "impact": f"Score {round(score, 0)}/100",
            "signalStrength": signal_strength,
            "fullText": fullText,
            "company_id": c.id,
            "_recency": recency_key,
            "_score": base_score,
        })

    # Sort: recency first (newest signals), then score — fresh content wins
    newest_days_ago = min(s["_recency"][0] for s in stories) if stories else 0
    all_stale = newest_days_ago > 7

    stories.sort(key=lambda x: (x.pop("_recency", (999, 0)), -x.pop("_score", 0)))

    # Day-based rotation: when no fresh signals, rotate so different leads appear each day
    if all_stale and len(stories) > limit:
        day_seed = int(now.strftime("%j"))
        pool_size = min(24, len(stories))
        start_idx = (day_seed * 7) % pool_size
        rotated = stories[start_idx:] + stories[:start_idx]
        stories = rotated[:limit]
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


def read_cached_edition(max_age_hours: int = 25) -> Optional[Dict[str, Any]]:
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
