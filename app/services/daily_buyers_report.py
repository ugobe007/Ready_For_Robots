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
    "rfp_open": "RFP OPEN — published RFP / vendor search, budget confirmed",
    "expanding": "EXPANDING — has robots and wants more, or a new category",
    "exploring": "EXPLORING — exploring, planning, budgeting or piloting, no vendor locked in",
    "preparing": "PREPARING — modernizing or labor pressure; predicted needs, no statement yet",
}
DEFAULT_STAGES = ("rfp_open", "expanding", "exploring", "preparing")
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
            {"kind": e.get("kind") or "", "label": e.get("label") or "", "text": (e.get("text") or "")[:240],
             "url": e.get("source_url") or "", "seen_at": (e.get("seen_at") or "")[:10]}
            for e in ev[:12]
        ],
        "workflows": list(br.get("workflows") or []),
        "pain": list(br.get("pain_labels") or []),
        "industry": getattr(company, "industry", "") or "",
        "city": getattr(company, "location_city", "") or "",
        "state": getattr(company, "location_state", "") or "",
        "website": getattr(company, "website", "") or "",
        "computed_at": (br.get("computed_at") or "")[:16],
        "also_listed_as": list(br.get("duplicate_names") or []),
        "open": [
            {"label": o.get("label"), "status": o.get("status"), "score": o.get("score"),
             "vendors": o.get("vendors") or [], "evidence": (o.get("evidence") or [])[:1]}
            for o in ((br.get("opportunities") or {}).get("open") or [])[:4]
        ],
        "already_has": [
            {"label": o.get("label"), "vendors": o.get("vendors") or []}
            for o in ((br.get("opportunities") or {}).get("already_has") or [])[:4]
        ],
        "predicted_next": [o.get("label") for o in ((br.get("opportunities") or {}).get("predicted_next") or [])[:3]],
    }


def select_buyers(db, *, stages: tuple[str, ...] = DEFAULT_STAGES) -> list[dict[str, Any]]:
    from app.models.company import Company
    from app.services.buyer_ranking import STAGE_RANK

    wanted = set(stages)
    rows = []
    q = db.query(Company).filter(Company.automation_profile.isnot(None))
    for company in q.yield_per(2000):
        br = _profile(company)
        if br.get("stage") in wanted and br.get("is_primary", True):
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


def _subject(report: dict[str, Any]) -> str:  # noqa: D401
    c = report.get("counts") or {}
    parts = []
    for st, word in (("rfp_open", "RFPs open"), ("expanding", "expanding"), ("exploring", "exploring"),
                     ("preparing", "preparing")):
        if st in c:
            parts.append(f"{c[st]} {word}")
    return f"Robot buyers — {', '.join(parts)} — {report.get('date')}"


def _buyer_lines(b: dict[str, Any]) -> list[str]:
    where = ", ".join(p for p in (b.get("city"), b.get("state")) if p)
    head = f"{b['rank']:03d}  {b['company']}"
    meta = " · ".join(p for p in (b.get("industry"), where) if p)
    if meta:
        head += f"  ({meta})"
    out = [head, f"     Why: {b.get('why') or '—'}  [score {b.get('score', 0):.0f}]"]
    if b.get("also_listed_as"):
        out.append(f"     Also listed as: {', '.join(b['also_listed_as'][:4])}")
    status_word = {"rfp": "RFP", "expanding": "wants more", "exploring": "exploring", "piloting": "piloting"}
    for o in b.get("open") or []:
        line = f"     ▸ {o['label']}: {status_word.get(o['status'], o['status'])}"
        if o.get("vendors"):
            line += f" (incumbent: {', '.join(o['vendors'][:2])})"
        out.append(line)
        for e in o.get("evidence") or []:
            out.append(f"         “{e.get('text', '')[:200]}”" + (f" ({e['seen_at']})" if e.get("seen_at") else ""))
            if e.get("url"):
                out.append(f"         {e['url']}")
    if b.get("already_has"):
        has = "; ".join(f"{h['label']}" + (f" ({', '.join(h['vendors'][:2])})" if h.get("vendors") else "")
                        for h in b["already_has"])
        out.append(f"     Already has: {has}")
    if b.get("predicted_next"):
        out.append(f"     Likely next: {', '.join(b['predicted_next'])}")
    if b.get("open"):
        return out
    ev = b.get("evidence") or []
    # Preparing/primed: lead with the pressure or modernization that reopened the door.
    ev = [e for e in ev if e.get("kind") in ("preparing", "pressure")] or ev
    seen_text: set = set()
    ev = [e for e in ev if not (e.get("text") in seen_text or seen_text.add(e.get("text")))]
    for e in ev[:3]:
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
        "  ".join(f"{STAGE_TITLES[st].split(' —')[0].capitalize().replace('Rfp', 'RFP')}: {c.get(st, 0)}"
                  for st in report.get("stages") or []),
        "",
        "Every company below has an open door: no vendor locked in for the listed workflow.",
        "Companies that already bought robots and said nothing new are left out (committed).",
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


CSV_COLUMNS = ("rank", "company", "stage", "score", "why", "open_categories", "already_has", "likely_next", "evidence_1", "evidence_1_url", "evidence_2",
               "evidence_2_url", "evidence_3", "evidence_3_url", "industry", "city", "state", "website",
               "workflows", "labor_pressure", "also_listed_as", "scored_at")


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
            "also_listed_as": "; ".join(b.get("also_listed_as") or []),
            "open_categories": "; ".join(f"{o['label']} ({o['status']})" for o in b.get("open") or []),
            "already_has": "; ".join(h["label"] + (f" ({', '.join(h['vendors'][:2])})" if h.get("vendors") else "")
                                     for h in b.get("already_has") or []),
            "likely_next": "; ".join(b.get("predicted_next") or []),
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


# ─── Sales-Ready Report Format ────────────────────────────────────────────────

def render_sales_ready_report(report: dict[str, Any]) -> str:
    """Render report in sales-ready PDF format with job cards."""
    from app.services.sales_report import (
        ROBOT_TYPES,
        extract_budget,
        extract_vendor,
        estimate_timeline,
    )
    
    lines = []
    lines.append(f"Robot Buyer Intelligence Report — {report.get('date')}")
    lines.append("")
    
    # Group by section
    rfp_open = []
    exploring = []
    
    for stage_name in report.get("stages") or []:
        for b in report.get("by_stage", {}).get(stage_name) or []:
            card_lines = _format_sales_card(b, report)
            
            if stage_name == "rfp_open":
                rfp_open.extend(card_lines)
            elif stage_name in ("exploring", "expanding", "preparing", "piloting"):
                exploring.extend(card_lines)
    
    # RFP Open section
    if rfp_open:
        lines.append("RFP Open — Published RFP / Vendor Search, Budget Confirmed")
        lines.append("")
        lines.extend(rfp_open)
    
    # Exploring section
    if exploring:
        lines.append("Exploring — Planning, Budgeting or Piloting, No Vendor Locked In")
        lines.append("")
        lines.extend(exploring)
    
    return "\n".join(lines)


def _format_sales_card(b: dict[str, Any], report: dict[str, Any]) -> list[str]:
    """Format one buyer as a sales card."""
    from app.services.sales_report import (
        ROBOT_TYPES,
        extract_budget,
        extract_vendor,
    )
    
    lines = []
    
    # Header: rank, company, industry, location
    where = ", ".join(p for p in (b.get("city"), b.get("state")) if p)
    lines.append(f"{b['rank']:03d}  {b['company']}")
    if where:
        lines.append(f"{b.get('industry') or 'Unknown'} · {where}")
    else:
        lines.append(f"{b.get('industry') or 'Unknown'}")
    
    # Job workflows (top 1-2 open categories)
    open_cats = [o for o in (b.get("open") or [])[:2]]
    if open_cats:
        lines.append(f"Job: {'; '.join(o['label'] for o in open_cats)}")
    
    # Robot types
    if open_cats:
        robot_types = []
        for o in open_cats:
            # Try to map category label back to key
            for cat_key, (cat_label, _) in __import__("app.services.opportunity_map", fromlist=["CATEGORIES"]).CATEGORIES.items():
                if cat_label == o['label']:
                    robot_types.append(ROBOT_TYPES.get(cat_key, cat_label))
                    break
            else:
                robot_types.append(o['label'])
        
        lines.append(f"Robot Types: {'; '.join(robot_types)}")
    
    # Sales intelligence line
    intel_parts = []
    
    # Timeline (estimate from stage)
    stage = b.get("stage") or "exploring"
    if stage == "rfp_open":
        timeline = "High-intent window (est. 45–120 days)"
    elif stage in ("exploring", "piloting"):
        timeline = "Capital program phase (est. 90–210 days)"
    elif stage == "expanding":
        timeline = "Expansion window (est. 60–180 days)"
    else:
        timeline = "Capital program phase (est. 90–210 days)"
    
    intel_parts.append(f"Schedule: {timeline}")
    
    # Has robots
    already_has = b.get("already_has") or []
    if already_has:
        has_str = "; ".join(h["label"] for h in already_has[:2])
        if len(already_has) > 2:
            has_str += f" (+{len(already_has) - 2} more)"
        intel_parts.append(f"Has Robots: Yes — {has_str}")
    else:
        intel_parts.append("Has Robots: No")
    
    # Budget (extract from evidence)
    budget = None
    for ev in (b.get("evidence") or [])[:5]:
        budget = extract_budget(ev.get("text") or "")
        if budget:
            break
    
    if budget:
        intel_parts.append(f"Budget: {budget}")
    
    lines.append(" | ".join(intel_parts))
    
    # Status line
    status_parts = []
    if stage == "rfp_open":
        status_parts.append("RFP")
    elif stage in ("exploring", "piloting"):
        status_parts.append("Exploring")
    elif stage == "expanding":
        status_parts.append("Expanding")
    
    # Extract incumbent from evidence or open categories
    vendors = []
    for o in (b.get("open") or []):
        vendors.extend(o.get("vendors") or [])
    
    if not vendors:
        for ev in (b.get("evidence") or [])[:5]:
            vendor = extract_vendor(ev.get("text") or "")
            if vendor and vendor not in vendors:
                vendors.append(vendor)
    
    if status_parts:
        if vendors:
            status_parts.append(f"(incumbent: {vendors[0]})")
        lines.append(f"Status: {' '.join(status_parts)}")
    
    # Evidence quotes
    for ev in (b.get("evidence") or [])[:3]:
        text = ev.get("text") or ""
        date = ev.get("seen_at") or ""
        date_str = f" ({date})" if date else ""
        lines.append(f'"{text}"{date_str}')
    
    # Likely next
    likely_next = b.get("predicted_next") or []
    if likely_next:
        lines.append(f"Likely Next: {', '.join(likely_next[:4])}")
    
    lines.append("")  # Blank line between cards
    
    return lines

