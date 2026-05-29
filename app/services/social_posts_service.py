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


# Plain-English triggers for social copy — avoid internal "signal" jargon.
_PLAIN_TRIGGERS: Dict[str, str] = {
    "labor_shortage": "staffing pressure",
    "expansion": "new locations or capacity growth",
    "strategic_hire": "leadership changes driving new initiatives",
    "capex": "capital budgets opening up",
    "funding_round": "fresh investment to deploy",
    "ma_activity": "M&A or portfolio moves",
    "job_posting": "automation-related hiring",
    "news": "public automation news",
    "news_signal": "public automation news",
    "automation_interest": "stated interest in automation",
    "automation_intent": "active automation planning",
    "labor_signal": "workforce strain",
    "robot_installation": "robots already going in",
    "rfp_posted": "vendor selection underway",
    "budget_allocated": "budget set aside for automation",
}


def _plain_triggers(deduped: list, limit: int = 3) -> List[str]:
    out: List[str] = []
    for s in deduped[:limit]:
        t = (getattr(s, "signal_type", None) or "").strip().lower()
        label = _PLAIN_TRIGGERS.get(t) or _sig_label(t).lower()
        if label and label not in out:
            out.append(label)
    return out


def _format_trigger_list(triggers: List[str]) -> str:
    if not triggers:
        return "operational pressure is building"
    if len(triggers) == 1:
        return triggers[0]
    if len(triggers) == 2:
        return f"{triggers[0]} and {triggers[1]}"
    return f"{triggers[0]}, {triggers[1]}, and {triggers[2]}"


def _headline_excerpt(top_sig) -> str:
    if not top_sig:
        return ""
    raw = (getattr(top_sig, "signal_text", None) or "").replace("\n", " ").strip()
    raw = re.sub(r"<[^>]+>", "", raw).strip()
    if not raw:
        return ""
    sentence = re.split(r"[.!?]\s+", raw)[0].strip()
    # Drop trailing publisher / source names (common in scraped news).
    if " - " in sentence:
        sentence = sentence.split(" - ", 1)[0].strip()
    # Drop long subtitle after colon (keep the headline lead).
    if ": " in sentence and len(sentence) > 90:
        lead, _sub = sentence.split(": ", 1)
        if len(lead) >= 24:
            sentence = lead.strip()
    if len(sentence) > 120:
        sentence = sentence[:120].rsplit(" ", 1)[0].rstrip(".,;:") + "…"
    return sentence


# ── Post builders ─────────────────────────────────────────────────────────────

def _build_hot_lead_post(company: Company, pri, sigs: list, deduped: list, rank: int) -> Dict:
    name = company.name or "Company"
    industry = company.industry or "industrial"
    ind_display = _industry_display(industry)
    automation_type, pain_point = _industry_automation_context(industry)
    hashtags = _industry_hashtags(industry)

    sig_count = len(sigs)
    top_sig = deduped[0] if deduped else (sigs[0] if sigs else None)
    triggers = _plain_triggers(deduped)
    trigger_phrase = _format_trigger_list(triggers)
    headline = _headline_excerpt(top_sig)

    buy_window = "60–90 days" if pri.tier == "HOT" else "90–120 days"
    emoji = "🔥" if rank == 1 else "📊"
    spotlight = "Buyer spotlight" if rank == 1 else "Buyer alert"
    ps = pick_primary_score(company.scores)
    score = (ps.overall_intent_score if ps else 0) or pri.score

    vendor_value = (
        f"For robotics vendors and integrators: accounts like this often start "
        f"evaluating partners within the next {buy_window}. "
        f"A specific use case beats a generic pitch — especially before the RFP."
    )

    # ── Twitter ──────────────────────────────────────────────────────────────
    tw_tags = _format_hashtags(hashtags)
    tw_hook = f"{emoji} {ind_display} | {name}"
    tw_core = (
        f"{tw_hook}\n\n"
        f"{name} is investing in {automation_type} as {pain_point}. "
        f"Vendor conversations often start within {buy_window}."
    )
    tw_core = _truncate_tweet(tw_core, max_chars=230 - len(tw_tags))
    twitter = f"{tw_core}\n\n{tw_tags}"

    # ── LinkedIn ─────────────────────────────────────────────────────────────
    li_hook = f"{emoji} {spotlight}: {name}"

    li_body = (
        f"{name} ({ind_display}) is moving on automation — {automation_type} — "
        f"because {pain_point}.\n\n"
        f"What's happening now: {trigger_phrase}."
    )

    li_headline = ""
    if headline:
        li_headline = f"\n\nRecent headline: \"{headline}\""

    li_value = f"\n\n{vendor_value}"

    li_cta = f"\n\nSee who's on today's automation buyer list → {SITE_URL}"
    li_hashtag_str = "\n\n" + _format_hashtags(hashtags)

    linkedin = (
        f"{li_hook}\n\n"
        f"{li_body}"
        f"{li_headline}"
        f"{li_value}"
        f"{li_cta}"
        f"{li_hashtag_str}"
    )

    return {
        "type": "hot_lead" if rank == 1 else "signal_alert",
        "title": f"{'🔥 Buyer Spotlight' if rank == 1 else '📊 Buyer Alert'}: {name}",
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

    # LinkedIn: full executive take + value framing
    linkedin = (
        "🧠 What we're seeing in automation this week\n\n"
        f"{executive_take}\n\n"
        "The takeaway for vendors: companies under this kind of pressure don't announce "
        "an RFP first — they talk to partners who show up with a concrete solution. "
        "Ready For Robots surfaces those accounts daily so you can reach out while "
        "the window is still open.\n\n"
        f"See today's buyer list → {SITE_URL}/newsletter\n\n"
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
        f"📈 Market trend: {title}\n\n"
        f"{detail}\n\n"
        "Why this matters if you sell robotics: when a trend shows up across multiple "
        "sectors at once, buyers move from \"someday\" to \"this quarter.\" "
        "Ready For Robots tracks which companies are actually acting on it — "
        "not just reading about it.\n\n"
        f"Read today's market brief → {SITE_URL}/newsletter\n\n"
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

    industries_str = ", ".join(industries) if industries else "hospitality, logistics, and manufacturing"

    tw_tags = _format_hashtags(hashtags)
    tw_core = (
        "🤖 The automation buying window is getting shorter.\n\n"
        f"Today's list includes {hot_count} high-intent accounts across {industries_str}. "
        "The vendors who win are usually in the conversation before the RFP."
    )
    tw_core = _truncate_tweet(tw_core, max_chars=230 - len(tw_tags))
    twitter = f"{tw_core}\n\n{tw_tags}"

    linkedin = (
        "🤖 Why early outreach beats waiting for the RFP\n\n"
        f"Across {industries_str}, we're tracking a wave of companies actively planning "
        f"automation investments — not just talking about them. {hot_count} accounts on "
        "today's list are high-intent, meaning vendor conversations are likely in the "
        "next 60–90 days.\n\n"
        "The pattern is consistent: teams that reach out with a specific use case and ROI "
        "story get in early. Teams that wait for the public RFP compete on price in a "
        "crowded field.\n\n"
        "Ready For Robots publishes that buyer list daily — ranked, sourced, and ready "
        "for outreach.\n\n"
        f"See today's list → {SITE_URL}\n\n"
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
