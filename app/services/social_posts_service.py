"""
Daily Social Media Content Generator
======================================
Produces 5 ready-to-post items per day, each with:
  - twitter: text ≤ 280 chars (URL counted separately by the platform)
  - linkedin: full professional post text
  - hashtags: list of relevant tags
  - type: hot_lead | signal_alert | industry_insight | market_trend | thought_leadership

Sources:
  1. HOT Lead #1 → "Hot Lead Spotlight"
  2. HOT Lead #2 → "Signal Alert"
  3. industryBrief.executive_take → "Industry Intelligence"
  4. industryBrief.macro_trends[0] → "Market Trend"
  5. Synthesized cross-sector insight → "Thought Leadership"

Cached for 4 hours in data/social_posts_latest.json.
"""
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.score import Score
from app.models.signal import Signal
from app.services.lead_filter import classify_lead, pick_primary_score
from app.services.newsletter_service import (
    SIGNAL_CATEGORIES,
    _industry_automation_context,
    _intelligence_summary,
    _sig_label,
    _company_size_descriptor,
    _industry_display,
)

# ── Cache ─────────────────────────────────────────────────────────────────────

def _data_dir() -> Path:
    base = Path(__file__).resolve().parent.parent.parent / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base

def _cache_path() -> Path:
    return _data_dir() / "social_posts_latest.json"

def _history_path() -> Path:
    return _data_dir() / "social_posts_history.json"


def read_cached_posts(max_age_hours: float = 4.0) -> Optional[Dict[str, Any]]:
    p = _cache_path()
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        gen = data.get("generated_at")
        if not gen:
            return None
        gen_dt = datetime.fromisoformat(gen.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - gen_dt > timedelta(hours=max_age_hours):
            return None
        return data
    except Exception:
        return None


def write_cached_posts(data: Dict[str, Any]) -> None:
    p = _cache_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, default=str))


# ── Posted history (7-day rolling window per company) ─────────────────────────

def _load_history() -> Dict[str, Any]:
    p = _history_path()
    if not p.exists():
        return {"entries": []}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"entries": []}


def _save_history(history: Dict[str, Any]) -> None:
    p = _history_path()
    p.write_text(json.dumps(history, indent=2, default=str))


def get_recently_posted_ids(days: int = 7) -> List[int]:
    """Return company IDs posted within the last `days` days."""
    history = _load_history()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [
        e["company_id"]
        for e in history.get("entries", [])
        if e.get("company_id") and _parse_dt(e.get("posted_at", "")) > cutoff
    ]


def mark_companies_posted(company_ids: List[int], post_types: Optional[List[str]] = None) -> None:
    """Record that these company IDs were just posted (for history tracking)."""
    history = _load_history()
    now_str = datetime.now(timezone.utc).isoformat()
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    # Prune entries older than 30 days to keep the file small
    history["entries"] = [
        e for e in history.get("entries", [])
        if _parse_dt(e.get("posted_at", "")) > cutoff
    ]

    for i, cid in enumerate(company_ids):
        history["entries"].append({
            "company_id": cid,
            "post_type": (post_types or [])[i] if post_types and i < len(post_types) else "unknown",
            "posted_at": now_str,
        })

    _save_history(history)


def _parse_dt(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


# ── Helpers ───────────────────────────────────────────────────────────────────

SITE_URL = "https://readyforrobots.com"

_INDUSTRY_HASHTAGS: Dict[str, List[str]] = {
    "logistics":       ["Logistics", "SupplyChain", "Automation"],
    "warehouse":       ["Warehouse", "SupplyChain", "Automation"],
    "fulfillment":     ["Fulfillment", "Ecommerce", "Automation"],
    "manufacturing":   ["Manufacturing", "Cobots", "IndustrialAutomation"],
    "hospitality":     ["Hospitality", "Hotels", "ServiceRobots"],
    "hotel":           ["Hotels", "Hospitality", "ServiceRobots"],
    "healthcare":      ["Healthcare", "HospitalRobots", "MedTech"],
    "food service":    ["FoodService", "Restaurants", "KitchenAutomation"],
    "restaurant":      ["Restaurants", "FoodTech", "KitchenAutomation"],
    "food & beverage": ["FoodBeverage", "PackagingAutomation", "Manufacturing"],
    "retail":          ["Retail", "RetailAutomation", "Robotics"],
    "construction":    ["Construction", "Robotics", "IndustrialAutomation"],
}

_BASE_HASHTAGS = ["Robotics", "Automation", "ReadyForRobots"]


def _industry_hashtags(industry: str) -> List[str]:
    low = (industry or "").lower()
    for key, tags in _INDUSTRY_HASHTAGS.items():
        if key in low:
            return tags + ["ReadyForRobots"]
    return _BASE_HASHTAGS


def _truncate_tweet(text: str, max_chars: int = 257) -> str:
    """Trim to max_chars, ending at a word boundary."""
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars].rsplit(" ", 1)[0]
    return trimmed.rstrip(".,;:") + "…"


def _first_n_sentences(text: str, n: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join(parts[:n])


def _format_hashtags(tags: List[str]) -> str:
    return " ".join(f"#{t}" for t in tags[:4])


# ── Post builders ─────────────────────────────────────────────────────────────

def _build_hot_lead_post(company: Company, pri, sigs: list, deduped: list, rank: int) -> Dict:
    name = company.name or "Company"
    industry = company.industry or "industrial"
    ind_display = _industry_display(industry)
    ps = pick_primary_score(company.scores)
    score = (ps.overall_intent_score if ps else 0) or pri.score
    automation_type, pain_point = _industry_automation_context(industry)
    hashtags = _industry_hashtags(industry)

    sig_count = len(sigs)
    top_sig = deduped[0] if deduped else (sigs[0] if sigs else None)
    unique_labels = [_sig_label(getattr(s, "signal_type", "")) for s in deduped[:4]]
    signals_str = ", ".join(unique_labels[:3]) if unique_labels else "automation interest"

    top_sig_excerpt = ""
    if top_sig:
        raw = (getattr(top_sig, "signal_text", None) or "").replace("\n", " ").strip()
        # Strip HTML tags and truncate
        raw = re.sub(r"<[^>]+>", "", raw).strip()
        if raw:
            top_sig_excerpt = raw[:200] + ("…" if len(raw) > 200 else "")

    buy_months = "60–90" if pri.tier == "HOT" else "90–120"
    emoji = "🔥" if rank == 1 else "📊"

    # ── Core intelligence sentence (the template the user asked for) ──────────
    # "[Company] is targeting automation for their [use_case] due to [pain_point]
    #  which aligns with our signals [signals]. The timing of the project is [X] months."
    core = (
        f"{name} is targeting automation for their {automation_type} "
        f"due to {pain_point}, which aligns with our signals: {signals_str}. "
        f"The timing of this project is within {buy_months} days."
    )

    # ── Twitter ──────────────────────────────────────────────────────────────
    tw_tags = _format_hashtags(hashtags)
    tw_hook = f"{emoji} {ind_display} | {name}"
    tw_core = f"{tw_hook}\n\n{core}"
    tw_core = _truncate_tweet(tw_core, max_chars=230 - len(tw_tags))
    twitter = f"{tw_core}\n\n{tw_tags}"

    # ── LinkedIn ─────────────────────────────────────────────────────────────
    li_hook = f"{emoji} Automation Intelligence: {name}"

    li_body = core

    li_evidence = ""
    if top_sig_excerpt:
        li_evidence = f'\n\nKey evidence: "{top_sig_excerpt}"'

    # Qualifying context
    li_qualify = (
        f"\n\nWith {len(sigs)} buying signals in our database and a priority score of "
        f"{round(score)}/100, this account is likely to evaluate and select a vendor "
        f"within {buy_months} days. First-mover outreach wins here."
    )

    li_cta = f"\n\n🔗 Full dossier + signal breakdown → {SITE_URL}"
    li_hashtag_str = "\n\n" + _format_hashtags(hashtags)

    linkedin = (
        f"{li_hook}\n\n"
        f"{li_body}"
        f"{li_evidence}"
        f"{li_qualify}"
        f"{li_cta}"
        f"{li_hashtag_str}"
    )

    return {
        "type": "hot_lead" if rank == 1 else "signal_alert",
        "title": f"{'🔥 Hot Lead Spotlight' if rank == 1 else '📊 Signal Alert'}: {name}",
        "source_name": name,
        "source_industry": ind_display,
        "source_tier": pri.tier,
        "score": round(score),
        "signal_count": sig_count,
        "company_id": company.id,
        "twitter": twitter.strip(),
        "linkedin": linkedin.strip(),
        "hashtags": hashtags,
        "share_url": SITE_URL,
    }


def _build_industry_insight_post(executive_take: str) -> Dict:
    if not executive_take:
        return None

    hashtags = ["Robotics", "AutomationTrends", "IndustrialAutomation", "ReadyForRobots"]

    # Twitter: first 2 sentences + hashtags
    tw_lead = _first_n_sentences(executive_take, 2)
    tw_tags = _format_hashtags(hashtags)
    tw_core = f"🧠 Industry Intelligence\n\n{tw_lead}"
    tw_core = _truncate_tweet(tw_core, max_chars=230 - len(tw_tags))
    twitter = f"{tw_core}\n\n{tw_tags}"

    # LinkedIn: full executive take + framing
    linkedin = (
        "🧠 Strategic Automation Intelligence\n\n"
        f"{executive_take}\n\n"
        "Companies showing these signals are typically 60–90 days from a vendor decision. "
        "Ready For Robots tracks thousands of buying indicators across hospitality, logistics, "
        "manufacturing, and more — surfacing the accounts that are actively ready to invest.\n\n"
        f"🔗 Explore today's signal dashboard → {SITE_URL}\n\n"
        + _format_hashtags(hashtags)
    )

    return {
        "type": "industry_insight",
        "title": "🧠 Industry Intelligence",
        "source_name": "Strategic Brief",
        "source_industry": "Cross-sector",
        "twitter": twitter.strip(),
        "linkedin": linkedin.strip(),
        "hashtags": hashtags,
        "share_url": f"{SITE_URL}/newsletter",
    }


def _build_market_trend_post(trend: Dict) -> Dict:
    title = trend.get("title", "Automation Trend")
    detail = trend.get("detail", "")
    if not detail:
        return None

    hashtags = ["AutomationTrends", "Robotics", "FutureOfWork", "ReadyForRobots"]

    tw_tags = _format_hashtags(hashtags)
    tw_core = f"📈 Market Trend: {title}\n\n{_first_n_sentences(detail, 2)}"
    tw_core = _truncate_tweet(tw_core, max_chars=230 - len(tw_tags))
    twitter = f"{tw_core}\n\n{tw_tags}"

    linkedin = (
        f"📈 Automation Market Trend: {title}\n\n"
        f"{detail}\n\n"
        "This signal pattern is consistent with what we're tracking across thousands of companies "
        "in our automation intelligence database. Companies that wait for this trend to mature before "
        "acting risk losing ground to early movers already deploying.\n\n"
        f"🔗 See today's full market brief → {SITE_URL}/newsletter\n\n"
        + _format_hashtags(hashtags)
    )

    return {
        "type": "market_trend",
        "title": f"📈 Market Trend: {title}",
        "source_name": title,
        "source_industry": "Cross-sector",
        "twitter": twitter.strip(),
        "linkedin": linkedin.strip(),
        "hashtags": hashtags,
        "share_url": f"{SITE_URL}/newsletter",
    }


def _build_thought_leadership_post(stories: List[Dict]) -> Dict:
    """Synthesize a broad insight from the day's top leads."""
    hashtags = ["Robotics", "Automation", "ROI", "FutureOfWork", "ReadyForRobots"]

    industries = list(dict.fromkeys([s.get("source_industry") or s.get("economics", "").split(" ·")[0].strip() for s in stories if s]))
    industries = [i for i in industries if i and i.lower() not in ("cross-sector", "strategic brief")][:3]

    hot_count = sum(1 for s in stories if s and s.get("source_tier") == "HOT")
    total_signals = sum(s.get("signal_count", 0) for s in stories if s)

    industries_str = ", ".join(industries) if industries else "hospitality, logistics, and manufacturing"

    tw_tags = _format_hashtags(hashtags)
    tw_core = (
        "🤖 Automation is no longer a future investment — it's a competitive necessity.\n\n"
        f"Today's signal feed shows {hot_count} high-intent buyers across {industries_str}. "
        "The window for being first to the conversation is closing."
    )
    tw_core = _truncate_tweet(tw_core, max_chars=230 - len(tw_tags))
    twitter = f"{tw_core}\n\n{tw_tags}"

    linkedin = (
        "🤖 Why the Automation Buying Window is Narrowing\n\n"
        f"Today's Ready For Robots signal feed picked up {total_signals}+ automation buying indicators "
        f"across {industries_str} and beyond. {hot_count} accounts are showing HOT intent — meaning "
        "they're likely to evaluate and select a vendor in the next 60–90 days.\n\n"
        "The companies that get to these buyers first — with the right message — win the deal. "
        "Those who wait for the RFP are already competing on price in a crowded field.\n\n"
        "Automation ROI is no longer a debate. The debate now is: which robotics vendor is positioned "
        "to capture the wave of first-time deployers coming to market this year?\n\n"
        f"🔗 See today's full lead intelligence feed → {SITE_URL}\n\n"
        + _format_hashtags(hashtags)
    )

    return {
        "type": "thought_leadership",
        "title": "🤖 Thought Leadership",
        "source_name": "Ready For Robots Intelligence",
        "source_industry": "Cross-sector",
        "twitter": twitter.strip(),
        "linkedin": linkedin.strip(),
        "hashtags": hashtags,
        "share_url": SITE_URL,
    }


# ── Main generator ────────────────────────────────────────────────────────────

def generate_daily_posts(
    db: Session,
    exclude_ids: Optional[List[int]] = None,
    trend_offset: int = 0,
) -> Dict[str, Any]:
    """
    Generate 5 daily social posts.
    exclude_ids: company IDs to skip (already-posted leads).
    trend_offset: rotate which macro trend is used for post #4.
    """
    from app.services.industry_brief_service import build_industry_brief_payload

    now = datetime.now(timezone.utc)

    # Merge caller-provided excludes with 7-day history
    history_ids = get_recently_posted_ids(days=7)
    skip_ids = set((exclude_ids or []) + history_ids)

    # Pull a wide pool of leads (score desc)
    ranked_ids = (
        db.query(Company.id)
        .outerjoin(Score, Score.company_id == Company.id)
        .group_by(Company.id)
        .order_by(func.coalesce(func.max(Score.overall_intent_score), 0).desc())
        .limit(500)
        .all()
    )
    id_list = [r[0] for r in ranked_ids]
    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id.in_(id_list))
        .all()
        if id_list else []
    )
    rank_map = {cid: i for i, cid in enumerate(id_list)}
    companies.sort(key=lambda c: rank_map.get(c.id, 9999))

    def _build_lead_tuple(c):
        sigs = sorted(c.signals, key=lambda s: (s.signal_strength or 0), reverse=True)
        seen: set = set()
        deduped: list = []
        for s in sigs:
            t = getattr(s, "signal_type", None) or "unknown"
            if t not in seen:
                seen.add(t)
                deduped.append(s)
            if len(deduped) >= 5:
                break
        return (c, sigs, deduped)

    # Collect fresh HOT leads first, then WARM as fallback
    hot_leads = []
    warm_leads = []
    for c in companies:
        if c.id in skip_ids:
            continue
        junk, _, pri = classify_lead(c, c.scores, c.signals)
        if junk or not c.signals:
            continue
        if pri.tier == "HOT":
            hot_leads.append((pri, *_build_lead_tuple(c)))
        elif pri.tier == "WARM" and len(warm_leads) < 10:
            warm_leads.append((pri, *_build_lead_tuple(c)))
        if len(hot_leads) >= 5:
            break

    candidates = hot_leads[:5] + warm_leads
    selected: list = candidates[:2]

    # If we exhausted fresh leads, fall back to history-excluded companies only
    if len(selected) < 2:
        for c in companies:
            if any(s[1].id == c.id for s in selected):
                continue
            junk, _, pri = classify_lead(c, c.scores, c.signals)
            if junk or not c.signals:
                continue
            if pri.tier in ("HOT", "WARM"):
                selected.append((pri, *_build_lead_tuple(c)))
            if len(selected) >= 2:
                break

    # Industry brief for insight + trend posts
    brief = build_industry_brief_payload(db, days=1, analytics=None, use_cache=True, force_refresh=False)
    executive_take = brief.get("executive_take", "") or ""
    macro_trends = brief.get("macro_trends") or []

    posts = []

    # Posts 1 & 2: lead spotlights
    for rank, lead_data in enumerate(selected[:2], start=1):
        pri, c, sigs, deduped = lead_data
        post = _build_hot_lead_post(c, pri, sigs, deduped, rank)
        posts.append(post)

    # Post 3: industry insight
    insight = _build_industry_insight_post(executive_take)
    if insight:
        posts.append(insight)

    # Post 4: market trend — rotate through available trends using trend_offset
    trend_post = None
    valid_trends = [t for t in macro_trends if _build_market_trend_post(t)]
    if valid_trends:
        idx = trend_offset % len(valid_trends)
        trend_post = _build_market_trend_post(valid_trends[idx])
    if trend_post:
        posts.append(trend_post)

    # Post 5: thought leadership
    posts.append(_build_thought_leadership_post(posts))

    # Ensure exactly 5
    posts = [p for p in posts if p][:5]

    # Embed posted company IDs so the frontend can send them back on next refresh
    posted_company_ids = [
        p["company_id"] for p in posts if p.get("company_id") is not None
    ]

    return {
        "date": now.strftime("%B %d, %Y"),
        "date_iso": now.date().isoformat(),
        "posts": posts,
        "posted_company_ids": posted_company_ids,
        "trend_offset": trend_offset,
        "total": len(posts),
        "generated_at": now.isoformat(),
    }
