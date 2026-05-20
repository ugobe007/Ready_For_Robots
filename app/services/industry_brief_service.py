"""
Industry strategic brief — CB Insights / research-style synthesis from live signals.

Uses OpenAI when OPENAI_API_KEY is set; otherwise a deterministic heuristic from
the same aggregates as the daily analytics report.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.signal import Signal


def _cache_path() -> Path:
    base = Path(__file__).resolve().parent.parent.parent / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base / "industry_brief_latest.json"


def _read_cache(max_age_hours: float) -> Optional[Dict[str, Any]]:
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


def _write_cache(payload: Dict[str, Any]) -> None:
    p = _cache_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2))


def _normalize_industry_label(raw: Optional[str]) -> str:
    """Public-facing: never show Unknown/Other as industry — align with pipeline copy."""
    s = (raw or "").strip()
    if not s or s.lower() in ("unknown", "other", "uncategorized", "n/a", "na"):
        return "Emerging"
    return s


def _rollup_industry_counts(industries: Optional[Dict[str, Any]], limit: int = 5) -> List[Tuple[str, int]]:
    merged: Dict[str, int] = {}
    for k, v in (industries or {}).items():
        lab = _normalize_industry_label(str(k))
        try:
            n = int(v)
        except (TypeError, ValueError):
            n = 0
        merged[lab] = merged.get(lab, 0) + n
    ranked = sorted(merged.items(), key=lambda x: -x[1])
    return ranked[:limit]


def _signals_window_phrase(period_days: int, signal_count: int) -> str:
    """Harmonized opening line for heuristic and prompt guidance."""
    n = int(signal_count or 0)
    if period_days <= 1:
        return f"In the past 24 hours we discovered {n} opportunity signals."
    if period_days == 7:
        return f"In the past week we discovered {n} opportunity signals."
    return f"Over the last {period_days} days we discovered {n} opportunity signals."


def _theme_label(key: str) -> str:
    """Readable automation-theme labels (matches analytics keys)."""
    k = (key or "").replace("_", " ").strip()
    aliases = {
        "general awareness": "Awareness & news",
        "evaluation": "Evaluation & buying journey",
        "new facility": "New facilities & expansion",
        "labor replacement": "Labor & staffing pressure",
        "deployment": "Deployments & rollouts",
        "procurement": "Procurement & vendor moves",
        "budget allocated": "Budget & capex",
    }
    low = k.lower()
    return aliases.get(low, k.title() if k else key)


def _harmonize_executive_take(text: str) -> str:
    if not text or not text.strip():
        return text
    t = re.sub(r"\bUnknown\b", "Emerging", text, flags=re.IGNORECASE)
    t = re.sub(r"\bprocessed\b", "discovered", t, count=1, flags=re.IGNORECASE)
    t = re.sub(
        r"Robot categories most implied by text",
        "Robot categories trending",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"In the last\s+1\s+day\(s\)\s+we\s+",
        "In the past 24 hours we ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"In the last\s+(\d+)\s+day\(s\)\s+we\s+processed",
        r"Over the last \1 days we discovered",
        t,
        flags=re.IGNORECASE,
    )
    return t


_SNIPPET_HTML_RE = re.compile(r"<[^>]+>", re.DOTALL)
_SNIPPET_URL_RE = re.compile(r"https?://\S+|CBMi[A-Za-z0-9+/=]{10,}")

def _clean_snippet_text(raw: str) -> str:
    """Strip HTML tags, Google News tokens, and URLs from snippet text."""
    txt = _SNIPPET_HTML_RE.sub("", raw)
    txt = _SNIPPET_URL_RE.sub("", txt)
    txt = re.sub(r"\s{2,}", " ", txt).strip()
    return txt


def _gather_snippets(db: Session, days: int, limit: int = 100) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(Signal, Company.name, Company.industry)
        .join(Company, Company.id == Signal.company_id)
        .filter(Signal.created_at >= cutoff)
        .order_by(desc(Signal.created_at))
        .limit(limit)
        .all()
    )
    out = []
    for sig, company_name, company_industry in rows:
        txt = _clean_snippet_text(sig.signal_text or "")
        if len(txt) < 20:
            continue
        out.append(
            {
                "company": company_name or "",
                "industry": company_industry or "Unknown",
                "type": sig.signal_type or "news",
                "text": txt[:400],
            }
        )
    return out


def _heuristic_brief(analytics: Dict[str, Any], snippets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rule-based brief when no LLM — still useful for dashboards."""
    totals = analytics.get("totals") or {}
    sig_n = totals.get("signals") or 0
    company_n = totals.get("companies_with_signals") or 0
    period_days = int(analytics.get("period_days") or 1)
    top_auto = list((analytics.get("automation_types_inferred") or {}).items())[:3]
    top_robot = list((analytics.get("robot_types_needed") or {}).items())[:3]
    top_ind = _rollup_industry_counts(analytics.get("industries"), limit=5)
    top_signal = list((analytics.get("signal_types") or {}).items())[:5]
    top_tasks = list((analytics.get("common_tasks_to_automate") or {}).items())[:4]
    top_companies = analytics.get("top_companies_by_signals") or []
    roi_summary = analytics.get("calculator_roi_summary") or {}

    window_phrase = _signals_window_phrase(period_days, sig_n).rstrip(".")
    opening = f"{window_phrase} across {company_n} companies." if company_n else f"{window_phrase}."
    lines = [opening]
    if top_auto:
        lines.append(
            "The strongest automation themes are "
            + ", ".join(f"{_theme_label(k)} ({v})" for k, v in top_auto)
            + ", which points to buyers moving from general interest toward operational projects."
        )
    if top_robot:
        lines.append(
            "Robot categories trending are "
            + ", ".join(f"{k} ({v})" for k, v in top_robot)
            + ", suggesting near-term demand around movement, service consistency, and labor substitution."
        )
    if top_ind:
        lines.append(
            "Industries most active in this window are "
            + ", ".join(f"{lab} ({v})" for lab, v in top_ind)
            + "; sales teams should prioritize accounts where these industry signals overlap with expansion, hiring, or budget language."
        )
    if not top_auto and snippets:
        companies = ", ".join(s.get("company", "") for s in snippets[:3] if s.get("company"))
        if companies:
            lines.append(
                f"The signal set is thin, but recent evidence from {companies} is still useful for account monitoring and targeted follow-up."
            )

    macro = []
    for k, v in top_auto[:4]:
        macro.append(
            {
                "title": _theme_label(k),
                "detail": f"{v} signals in this rolling window point to buyer activity around this theme. Treat these accounts as timing-sensitive when the signal is paired with hiring, facility movement, capex, or customer-service pressure.",
            }
        )
    if top_signal:
        macro.append(
            {
                "title": "Signal mix",
                "detail": "Most visible signal types: "
                + ", ".join(f"{_theme_label(k)} ({v})" for k, v in top_signal[:4])
                + ". This mix helps separate active buying windows from broad market noise.",
            }
        )
    if top_tasks:
        macro.append(
            {
                "title": "Operational jobs to automate",
                "detail": "Common task language includes "
                + ", ".join(f"{k} ({v})" for k, v in top_tasks)
                + ", giving sales teams practical hooks for discovery and outreach.",
            }
        )
    if not macro and snippets:
        macro.append(
            {
                "title": "Thin but active signal set",
                "detail": "The current window has limited volume, so the right action is account monitoring, not broad market extrapolation.",
            }
        )

    company_examples = ", ".join(
        c.get("name", "") for c in top_companies[:3] if isinstance(c, dict) and c.get("name")
    )
    company_clause = (
        f" Current high-activity accounts include {company_examples}."
        if company_examples
        else ""
    )
    roi_clause = ""
    if roi_summary.get("avg_payback_months") or roi_summary.get("avg_roi_1_year_pct"):
        roi_parts = []
        if roi_summary.get("avg_payback_months"):
            roi_parts.append(f"{roi_summary['avg_payback_months']} month average payback")
        if roi_summary.get("avg_roi_1_year_pct"):
            roi_parts.append(f"{roi_summary['avg_roi_1_year_pct']}% first-year ROI")
        roi_clause = " Calculator activity indicates " + " and ".join(roi_parts) + "."

    strategic = [
        {
            "audience": "Robotics & automation vendors",
            "insight": "Prioritize accounts where expansion, labor pressure, and operational bottlenecks appear together. Those clusters are stronger buying-timing indicators than generic robotics news." + company_clause,
        },
        {
            "audience": "Sales leaders",
            "insight": "Use the signal type as the outreach reason, then map it to a concrete automation use case. Lead cards should explain the pain, the matching robot category, and why the timing is now." + roi_clause,
        },
        {
            "audience": "Partnership teams",
            "insight": "Watch industries with repeated facility, staffing, or service consistency signals. These markets can create channel opportunities with integrators, distributors, and service providers before direct vendor demand is obvious.",
        },
    ]
    if snippets:
        strategic.append(
            {
                "audience": "Market intelligence",
                "insight": "Validate thin daily windows against the rolling trend before changing positioning. A low-volume day can still matter if it reinforces a week-long pattern.",
            }
        )

    return {
        "executive_take": _harmonize_executive_take(" ".join(lines)),
        "macro_trends": macro[:5],
        "strategic_implications": strategic,
        "risks_and_unknowns": [
            "Signal text is news-derived — verify budget authority on key accounts.",
            "Geographic and sub-industry coverage may be uneven; cross-check before territory planning.",
        ],
        "watch_next": [
            "Expansion, facility opening, or renovation language paired with automation hiring.",
            "Labor shortage and wage-pressure mentions in logistics, hospitality, healthcare, and food service.",
            "Capex, funding, or budget language that suggests a 60- to 180-day procurement window.",
            "Repeated signals from the same account, which should move the lead from market watch to active Cal outreach.",
        ],
        "source": "heuristic",
        "model": None,
    }


def _openai_brief(analytics: Dict[str, Any], snippets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Generate the strategic brief via whichever LLM provider is configured.
    Returns None when no provider is available — caller falls back to heuristics.
    """
    from app.services.llm_client import llm_json_completion, active_provider
    provider = active_provider()
    if provider is None:
        return None  # no API key — use local heuristics
    try:
        timeout = float(os.getenv("INDUSTRY_BRIEF_OPENAI_TIMEOUT", "20"))
    except ValueError:
        timeout = 20.0
    model = provider  # used for the "source" label below
    totals = analytics.get("totals") or {}
    ind_rolled = dict(_rollup_industry_counts(analytics.get("industries"), limit=12))

    # Build co-occurrence clusters: group companies by signal type so the AI can
    # detect "3 logistics companies all fired labor_shortage in the same window"
    from collections import defaultdict
    sig_type_companies: dict = defaultdict(list)
    industry_sig_types: dict = defaultdict(set)
    for s in snippets:
        st = s.get("type", "unknown")
        co = s.get("company", "")
        ind = s.get("industry", "")
        if co:
            sig_type_companies[st].append(co)
        if ind and co:
            industry_sig_types[ind].add(st)
    # Keep only meaningful clusters (2+ companies per signal type)
    clusters = {
        k: list(dict.fromkeys(v))[:8]
        for k, v in sig_type_companies.items()
        if len(v) >= 2
    }
    ind_signal_map = {
        k: sorted(v)
        for k, v in industry_sig_types.items()
        if k and k.lower() not in ("unknown", "other")
    }

    digest = {
        "period_days": analytics.get("period_days"),
        "signal_count": totals.get("signals"),
        "top_automation_types": dict(list((analytics.get("automation_types_inferred") or {}).items())[:8]),
        "top_robot_types": dict(list((analytics.get("robot_types_needed") or {}).items())[:8]),
        "top_industries": ind_rolled,
        "top_signal_types": dict(list((analytics.get("signal_types") or {}).items())[:10]),
        "signal_type_clusters": clusters,
        "industry_signal_map": ind_signal_map,
        "sample_headlines": snippets[:24],
        "language_rules": {
            "opening": (
                "If period_days is 1, start executive_take with exactly: "
                "'In the past 24 hours we discovered [signal_count] opportunity signals.' "
                "If period_days is 7: 'In the past week we discovered …'. "
                "Otherwise: 'Over the last N days we discovered …'. "
                "Never say 'processed' — use discovered."
            ),
            "robot_line": "Refer to robot type counts as 'Robot categories trending:' not 'implied by text'.",
            "industries": (
                "Never use the word Unknown for industry. "
                "The JSON already merges unclassified into 'Emerging' — use that label only."
            ),
            "automation_themes": "Call them 'Top automation themes we're seeing:' (not 'Strongest automation themes').",
            "industry_line": "Use 'Industries most active in this window:' for the industry sentence.",
        },
    }
    prompt = """You are a senior industry analyst (McKinsey/CB Insights level). Using ONLY the JSON data below — aggregated opportunity signals from real enterprise buyers in robotics / physical automation — write an intelligence brief for B2B robotics vendors.

CRITICAL REQUIREMENT — PATTERN SYNTHESIS:
Your job is NOT to describe the data. Your job is to find the PATTERN ACROSS companies and explain what it MEANS.

Bad: "Three companies show labor shortage signals."
Good: "Three major 3PLs posted automation officer roles within the same 10-day window — that's a coordinated response to Q2 labor data, not coincidence. Vendors who call on these accounts now will shape the short list before RFPs are issued."

Ask yourself before writing each sentence: "So what? What should a B2B sales team DO with this?" If you can't answer that, rewrite it.

Follow language_rules in the JSON exactly for tone and vocabulary.

Return valid JSON with this exact shape:
{
  "executive_take": "3-4 sentences. Lead with the most surprising or actionable pattern you found across the signals. Name industries or signal clusters — not individual companies. Plain English, no hype.",
  "macro_trends": [ {"title": "short title", "detail": "1-2 sentences with numbers from data. Focus on what changed, not just what exists." } ],
  "strategic_implications": [ {"audience": "specific role (e.g. AMR vendor CRO, warehouse integrator)", "insight": "what they should do THIS WEEK based on the pattern" } ],
  "risks_and_unknowns": [ "specific open question or risk — not generic. E.g. 'Q3 CapEx freeze could delay 40% of active evaluations'" ],
  "watch_next": [ "specific leading indicator to watch in the next 2-4 weeks — e.g. 'Walmart Q2 earnings call for distribution capex commentary'" ]
}
Do not invent company names not in sample_headlines. If data is thin, say so and still give framework-level guidance.

DATA:
"""
    try:
        raw = llm_json_completion(
            system_prompt="You output only valid JSON.",
            user_prompt=prompt + json.dumps(digest, default=str)[:120000],
            max_tokens=2400,
            temperature=0.35,
            timeout=timeout,
        )
        if not raw:
            return None
        data = json.loads(raw)
        trends = []
        for t in data.get("macro_trends") or []:
            if isinstance(t, dict):
                trends.append(
                    {
                        "title": t.get("title") or t.get("headline") or "Trend",
                        "detail": t.get("detail") or t.get("summary") or "",
                    }
                )
            elif isinstance(t, str):
                trends.append({"title": "Trend", "detail": t})
        impl = []
        for s in data.get("strategic_implications") or []:
            if isinstance(s, dict):
                impl.append(
                    {
                        "audience": s.get("audience")
                        or s.get("for_who")
                        or s.get("stakeholder")
                        or "Stakeholders",
                        "insight": s.get("insight") or s.get("detail") or "",
                    }
                )
            elif isinstance(s, str):
                impl.append({"audience": "Stakeholders", "insight": s})
        exec_take = _harmonize_executive_take(data.get("executive_take", "") or "")
        return {
            "executive_take": exec_take,
            "macro_trends": trends,
            "strategic_implications": impl,
            "risks_and_unknowns": data.get("risks_and_unknowns") or [],
            "watch_next": data.get("watch_next") or [],
            "source": model,  # "anthropic" or "openai"
            "model": model,
        }
    except Exception:
        return None


def build_industry_brief_payload(
    db: Session,
    days: int = 1,
    analytics: Optional[Dict[str, Any]] = None,
    *,
    force_refresh: bool = False,
    use_cache: bool = True,
    cache_hours: float = 1.5,
) -> Dict[str, Any]:
    """
    Build or load cached industry brief. Pass analytics from get_daily_analytics to avoid double DB scan for aggregates.
    """
    if use_cache and not force_refresh:
        cached = _read_cache(cache_hours)
        if cached and cached.get("period_days") == days:
            return cached

    from app.services.daily_analytics_service import get_daily_analytics

    analytics = analytics or get_daily_analytics(db, days=days)
    snippets = _gather_snippets(db, days=days, limit=100)

    brief = _openai_brief(analytics, snippets)
    if not brief:
        brief = _heuristic_brief(analytics, snippets)

    now = datetime.now(timezone.utc)
    payload = {
        **brief,
        "period_days": days,
        "generated_at": now.isoformat(),
        "snippets_used": len(snippets),
    }
    if use_cache:
        try:
            _write_cache(payload)
        except OSError:
            pass
    return payload


def format_brief_markdown(brief: Dict[str, Any]) -> str:
    lines = [
        "## Strategic industry brief",
        f"*Generated {brief.get('generated_at', '')} · source: {brief.get('source', '')}*",
        "",
        brief.get("executive_take") or "",
        "",
        "### Macro trends",
    ]
    for t in brief.get("macro_trends") or []:
        if isinstance(t, dict):
            lines.append(f"- **{t.get('title', '')}** — {t.get('detail', '')}")
        else:
            lines.append(f"- {t}")
    lines.append("")
    lines.append("### Strategic implications")
    for s in brief.get("strategic_implications") or []:
        if isinstance(s, dict):
            lines.append(f"- **{s.get('audience', 'Stakeholders')}:** {s.get('insight', '')}")
        else:
            lines.append(f"- {s}")
    lines.append("")
    lines.append("### Risks & unknowns")
    for r in brief.get("risks_and_unknowns") or []:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("### What to watch")
    for w in brief.get("watch_next") or []:
        lines.append(f"- {w}")
    lines.append("")
    return "\n".join(lines)
