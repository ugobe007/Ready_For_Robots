"""Daily email: companies ready to buy or pilot robots, with the evidence.

Replaces the robot-jobs list as the default daily report (DAILY_REPORT_MODE=buyers).
Reads the stage stamped on companies.automation_profile.buyer_readiness, after
re-scoring everyone first (DAILY_BUYERS_REFRESH=1, default) so the list is fresh.

Body: every Buying now and Evaluating company with up to 3 evidence lines, then a
short Preparing section. CSV attachment: all of them, one row per company.
"""
from __future__ import annotations

import base64
import csv
import html
import io
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

STAGE_TITLES = {
    "buying_now": "BUYING NOW — tender, pilot, purchase or vendor selection",
    "evaluating": "EVALUATING — automation hires, budgets, programs, or modernizing under labor pressure",
    "expanding": "EXPANDING — already running robots",
    "preparing": "PREPARING — budgeting, modernizing, redesigning workflows, or labor pressure",
}
DEFAULT_STAGES = ("buying_now", "evaluating", "preparing")
# Preparing can be long; the body shows the strongest N, the CSV has everyone.
PREPARING_BODY_LIMIT = 40


def report_stages() -> tuple[str, ...]:
    raw = (os.getenv("DAILY_BUYERS_STAGES") or "").strip()
    if not raw:
        return DEFAULT_STAGES
    return tuple(s.strip() for s in raw.split(",") if s.strip() in STAGE_TITLES)


def refresh_enabled() -> bool:
    return (os.getenv("DAILY_BUYERS_REFRESH", "1") or "1").strip().lower() not in ("0", "false", "no")


def _profile(company: Any) -> dict[str, Any]:
    prof = getattr(company, "automation_profile", None) or {}
    br = prof.get("buyer_readiness") if isinstance(prof, dict) else None
    return br if isinstance(br, dict) else {}


def _serialize(company: Any, br: dict[str, Any]) -> dict[str, Any]:
    ev = [e for e in (br.get("evidence") or []) if isinstance(e, dict)]
    return {
        "company_id": getattr(company, "id", None),
        "company": getattr(company, "name", "") or "",
        "stage": br.get("stage") or "",
        "score": float(br.get("score") or 0),
        "why": br.get("why") or "",
        "evidence": [
            {"label": e.get("label") or "", "text": (e.get("text") or "")[:240],
             "url": e.get("source_url") or "", "seen_at": (e.get("seen_at") or "")[:10]}
            for e in ev[:3]
        ],
        "workflows": list(br.get("workflows") or []),
        "pain": list(br.get("pain_labels") or []),
        "industry": getattr(company, "industry", "") or "",
        "city": getattr(company, "location_city", "") or "",
        "state": getattr(company, "location_state", "") or "",
        "website": getattr(company, "website", "") or "",
        "computed_at": (br.get("computed_at") or "")[:16],
    }


def select_buyers(db, *, stages: tuple[str, ...] = DEFAULT_STAGES) -> list[dict[str, Any]]:
    from app.models.company import Company
    from app.services.buyer_ranking import STAGE_RANK

    wanted = set(stages)
    rows = []
    q = db.query(Company).filter(Company.automation_profile.isnot(None))
    for company in q.yield_per(2000):
        br = _profile(company)
        if br.get("stage") in wanted:
            rows.append(_serialize(company, br))
    rows.sort(key=lambda r: (STAGE_RANK.get(r["stage"], 9), -r["score"], r["company"].lower()))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def compose_daily_buyers_report(db, *, refresh: Optional[bool] = None) -> dict[str, Any]:
    refreshed = None
    if refresh if refresh is not None else refresh_enabled():
        try:
            from app.services.buyer_ranking import score_companies

            counts, _ = score_companies(db, apply=True)
            refreshed = dict(counts)
        except Exception:
            logger.warning("buyer re-score before daily email failed; using stored stages", exc_info=True)
            try:
                db.rollback()
            except Exception:
                pass
    stages = report_stages()
    buyers = select_buyers(db, stages=stages)
    counts = {st: sum(1 for b in buyers if b["stage"] == st) for st in stages}
    return {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "kind": "buyers",
        "stages": list(stages),
        "counts": counts,
        "count": len(buyers),
        "buyers": buyers,
        "refreshed_counts": refreshed,
    }


def _subject(report: dict[str, Any]) -> str:
    c = report.get("counts") or {}
    parts = []
    if "buying_now" in c:
        parts.append(f"{c['buying_now']} buying now")
    if "evaluating" in c:
        parts.append(f"{c['evaluating']} evaluating")
    if "preparing" in c:
        parts.append(f"{c['preparing']} preparing")
    return f"Robot buyers — {', '.join(parts)} — {report.get('date')}"


def _buyer_lines(b: dict[str, Any]) -> list[str]:
    where = ", ".join(p for p in (b.get("city"), b.get("state")) if p)
    head = f"{b['rank']:03d}  {b['company']}"
    meta = " · ".join(p for p in (b.get("industry"), where) if p)
    if meta:
        head += f"  ({meta})"
    out = [head, f"     Why: {b.get('why') or '—'}  [score {b.get('score', 0):.0f}]"]
    for e in b.get("evidence") or []:
        line = f"     • {e['label']}: {e['text']}"
        if e.get("seen_at"):
            line += f" ({e['seen_at']})"
        out.append(line)
        if e.get("url"):
            out.append(f"       {e['url']}")
    return out


def render_daily_buyers_text(report: dict[str, Any]) -> str:
    c = report.get("counts") or {}
    lines = [
        f"Companies ready to buy or pilot robots — {report.get('date')}",
        "",
        "  ".join(f"{STAGE_TITLES[st].split(' —')[0].title()}: {c.get(st, 0)}" for st in report.get("stages") or []),
        "",
        "Every company below has evidence on record. Robot vendors and junk names are excluded.",
        "",
    ]
    buyers = list(report.get("buyers") or [])
    for st in report.get("stages") or []:
        group = [b for b in buyers if b["stage"] == st]
        if not group:
            continue
        lines += ["=" * 72, f"{STAGE_TITLES[st]} ({len(group)})", "=" * 72, ""]
        shown = group if st != "preparing" else group[:PREPARING_BODY_LIMIT]
        for b in shown:
            lines += _buyer_lines(b) + [""]
        if len(shown) < len(group):
            lines += [f"… {len(group) - len(shown)} more {st.replace('_', ' ')} companies in the attached CSV.", ""]
    if not buyers:
        lines += ["No companies at these stages yet. Run: python3 scripts/rank_buyers.py --apply", ""]
    lines += [f"Full list attached ({_csv_filename(report)}).", ""]
    return "\n".join(lines)


def render_daily_buyers_html(report: dict[str, Any]) -> str:
    body = html.escape(render_daily_buyers_text(report))
    return ("<div style=\"font-family:Georgia,serif;max-width:720px;color:#111827\">"
            "<pre style=\"white-space:pre-wrap;font-family:Georgia,serif;font-size:14px;line-height:1.45\">"
            f"{body}</pre></div>")


CSV_COLUMNS = ("rank", "company", "stage", "score", "why", "evidence_1", "evidence_1_url", "evidence_2",
               "evidence_2_url", "evidence_3", "evidence_3_url", "industry", "city", "state", "website",
               "workflows", "labor_pressure", "scored_at")


def _csv_filename(report: dict[str, Any]) -> str:
    return f"robot-buyers-{str(report.get('date') or '')[:10]}.csv"


def render_daily_buyers_csv(report: dict[str, Any]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for b in report.get("buyers") or []:
        ev = (b.get("evidence") or []) + [{}, {}, {}]
        row = {
            "rank": b["rank"], "company": b["company"], "stage": b["stage"], "score": f"{b['score']:.1f}",
            "why": b.get("why") or "", "industry": b.get("industry") or "", "city": b.get("city") or "",
            "state": b.get("state") or "", "website": b.get("website") or "",
            "workflows": "; ".join(b.get("workflows") or []), "labor_pressure": "; ".join(b.get("pain") or []),
            "scored_at": b.get("computed_at") or "",
        }
        for i in range(3):
            e = ev[i] or {}
            row[f"evidence_{i + 1}"] = f"{e.get('label')}: {e.get('text')}" if e.get("label") else ""
            row[f"evidence_{i + 1}_url"] = e.get("url") or ""
        w.writerow(row)
    return buf.getvalue()


def buyers_csv_attachment(report: dict[str, Any], csv_text: str) -> dict[str, str]:
    return {"filename": _csv_filename(report),
            "content": base64.b64encode(csv_text.encode("utf-8")).decode("ascii"),
            "content_type": "text/csv"}
