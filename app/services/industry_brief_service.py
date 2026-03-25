"""
Industry strategic brief — CB Insights / research-style synthesis from live signals.

Uses OpenAI when OPENAI_API_KEY is set; otherwise a deterministic heuristic from
the same aggregates as the daily analytics report.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def _gather_snippets(db: Session, days: int, limit: int = 100) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(Signal, Company.name)
        .join(Company, Company.id == Signal.company_id)
        .filter(Signal.created_at >= cutoff)
        .order_by(desc(Signal.created_at))
        .limit(limit)
        .all()
    )
    out = []
    for sig, company_name in rows:
        txt = (sig.signal_text or "").strip()
        if len(txt) < 20:
            continue
        out.append(
            {
                "company": company_name or "",
                "type": sig.signal_type or "news",
                "text": txt[:500],
            }
        )
    return out


def _heuristic_brief(analytics: Dict[str, Any], snippets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rule-based brief when no LLM — still useful for dashboards."""
    totals = analytics.get("totals") or {}
    sig_n = totals.get("signals") or 0
    top_auto = list((analytics.get("automation_types_inferred") or {}).items())[:3]
    top_robot = list((analytics.get("robot_types_needed") or {}).items())[:3]
    top_ind = list((analytics.get("industries") or {}).items())[:5]
    lines = [
        f"In the last {analytics.get('period_days', 1)} day(s) we processed **{sig_n}** opportunity signals.",
    ]
    if top_auto:
        lines.append(
            "Strongest automation themes: "
            + ", ".join(f"{k.replace('_', ' ')} ({v})" for k, v in top_auto)
            + "."
        )
    if top_robot:
        lines.append(
            "Robot categories most implied by text: " + ", ".join(f"{k} ({v})" for k, v in top_robot) + "."
        )
    if top_ind:
        lines.append("Most active industries: " + ", ".join(f"{k} ({v})" for k, v in top_ind) + ".")

    macro = []
    for k, v in top_auto[:4]:
        macro.append(
            {
                "title": k.replace("_", " ").title(),
                "detail": f"{v} signals in-window suggest continued focus on {k.replace('_', ' ')}.",
            }
        )
    strategic = [
        {
            "audience": "Robotics & automation vendors",
            "insight": "Prioritize outreach where labor_replacement and new_facility signals cluster — buyers are budgeting and expanding footprint.",
        },
        {
            "audience": "Investors & corp dev",
            "insight": "Track funding_round + capex pairings; they often precede a 6–12 month procurement window for automation.",
        },
    ]
    if snippets:
        strategic.append(
            {
                "audience": "Sales leaders",
                "insight": "Lead with ROI and pilot language when signals mention trials or payback — vocabulary match improves reply rates.",
            }
        )

    return {
        "executive_take": " ".join(lines),
        "macro_trends": macro[:5] or [{"title": "Building dataset", "detail": "Run scrapers to populate strategic trends."}],
        "strategic_implications": strategic,
        "risks_and_unknowns": [
            "Signal text is news-derived — verify budget authority on key accounts.",
            "Geographic and sub-industry coverage may be uneven; cross-check before territory planning.",
        ],
        "watch_next": [
            "Executive hire + expansion in same quarter (integration spend).",
            "Labor shortage + capex in logistics and hospitality (AMR/cleaning fit).",
        ],
        "source": "heuristic",
        "model": None,
    }


def _openai_brief(analytics: Dict[str, Any], snippets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=key)
    model = os.getenv("INDUSTRY_BRIEF_MODEL", "gpt-4o-mini")
    totals = analytics.get("totals") or {}
    digest = {
        "period_days": analytics.get("period_days"),
        "signal_count": totals.get("signals"),
        "top_automation_types": dict(list((analytics.get("automation_types_inferred") or {}).items())[:8]),
        "top_robot_types": dict(list((analytics.get("robot_types_needed") or {}).items())[:8]),
        "top_industries": dict(list((analytics.get("industries") or {}).items())[:10]),
        "top_signal_types": dict(list((analytics.get("signal_types") or {}).items())[:10]),
        "sample_headlines": snippets[:24],
    }
    prompt = """You are a senior industry analyst (McKinsey/CB Insights style). Using ONLY the JSON data below — aggregated opportunity signals for robotics / physical automation buyers — write a concise strategic brief for B2B robotics vendors and enterprise automation buyers.

Return valid JSON with this exact shape:
{
  "executive_take": "3-4 sentences, plain English, no hype",
  "macro_trends": [ {"title": "short", "detail": "1-2 sentences with numbers from data where possible" } ],
  "strategic_implications": [ {"audience": "who", "insight": "actionable" } ],
  "risks_and_unknowns": [ "bullet strings" ],
  "watch_next": [ "specific things to monitor next 2-4 weeks" ]
}
Do not invent company names not in sample_headlines. If data is thin, say so and still give framework-level guidance.

DATA:
"""
    try:
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You output only valid JSON."},
                {"role": "user", "content": prompt + json.dumps(digest, default=str)[:120000]},
            ],
            temperature=0.35,
            max_tokens=1800,
        )
        raw = (resp.choices[0].message.content or "").strip()
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
        return {
            "executive_take": data.get("executive_take", ""),
            "macro_trends": trends,
            "strategic_implications": impl,
            "risks_and_unknowns": data.get("risks_and_unknowns") or [],
            "watch_next": data.get("watch_next") or [],
            "source": "openai",
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
