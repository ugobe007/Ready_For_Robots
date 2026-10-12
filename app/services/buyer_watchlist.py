"""Buyer watchlist: search the news FOR named companies, not for headlines.

Discovery queries ("warehouse automation investment") only find a company when a
headline happens to name it, and the name has to be extracted — that is where
junk names come from. The watchlist goes the other way: for each company we
already care about, search Google News for that company + robots/automation, and
for that company + labor pressure/modernization. Evidence attaches straight to
the company row, and the title must name the company.

Who is watched, in priority order (least recently checked first within a bucket):
  1. companies already at evaluating / expanding / preparing / primed  (keep fresh,
     find the evidence that moves them up)
  2. labor-heavy companies in Watch with many open operational postings
     (pain at scale, intent not yet seen)
  3. the seed list app/data/operator_watchlist.txt (major operators, airports,
     agencies) — created if missing

State lives in companies.crm_metadata["watch"] = {last_checked, hits}.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

logger = logging.getLogger(__name__)

_SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "operator_watchlist.txt"
ACTIVE_STAGES = ("evaluating", "expanding", "preparing", "primed", "buying_now")

# One query for intent, one for pressure. OR-syntax keeps it to two requests per company.
QUERY_TEMPLATES = (
    '"{name}" (robot OR robots OR robotic OR automation OR automated OR autonomous OR AMR OR cobot)',
    '"{name}" ("labor shortage" OR "staffing shortage" OR turnover OR modernization OR "capital plan" '
    'OR "labor costs" OR "new distribution center" OR "technology investment")',
)


def watchlist_per_run() -> int:
    try:
        return max(0, int(os.getenv("WATCHLIST_COMPANIES_PER_RUN", "120")))
    except ValueError:
        return 120


def seed_names() -> list[str]:
    try:
        lines = _SEED_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def _last_checked(company: Any) -> str:
    meta = getattr(company, "crm_metadata", None) or {}
    watch = meta.get("watch") if isinstance(meta, dict) else None
    return (watch or {}).get("last_checked") or ""


def _stage(company: Any) -> Optional[str]:
    prof = getattr(company, "automation_profile", None) or {}
    br = prof.get("buyer_readiness") if isinstance(prof, dict) else None
    if not isinstance(br, dict) or br.get("is_primary") is False:
        return None
    return br.get("stage")


def ensure_seed_companies(db, create_company) -> int:
    """Make sure every seed operator has a company row. ``create_company(name)`` → Company|None."""
    from app.services.company_identity import find_existing_company

    created = 0
    for name in seed_names():
        if find_existing_company(db, name) is None and create_company(name) is not None:
            created += 1
    if created:
        db.commit()
    return created


def select_watchlist(db, limit: Optional[int] = None, *, min_postings: int = 5) -> list[Any]:
    """Companies to check this run, by priority bucket then least recently checked."""
    from sqlalchemy import func

    from app.models.company import Company
    from app.models.signal import Signal
    from app.services.buyer_readiness import is_labor_heavy
    from app.services.company_identity import find_existing_company, junk_name_reason

    cap = watchlist_per_run() if limit is None else limit
    if cap <= 0:
        return []
    picked: dict[int, tuple[int, str, Any]] = {}

    def add(company: Any, bucket: int) -> None:
        if company is None or company.id in picked or junk_name_reason(company.name):
            return
        picked[company.id] = (bucket, _last_checked(company), company)

    # 1. Companies already showing buyer stages.
    for c in db.query(Company).filter(Company.automation_profile.isnot(None)).yield_per(2000):
        if _stage(c) in ACTIVE_STAGES:
            add(c, 0 if _stage(c) in ("preparing", "primed") else 1)

    # 2. Labor-heavy companies with many operational postings, no intent yet.
    rows = (
        db.query(Signal.company_id, func.count(Signal.id))
        .filter(Signal.signal_type == "robot_job")
        .group_by(Signal.company_id)
        .having(func.count(Signal.id) >= min_postings)
        .all()
    )
    ids = [cid for cid, _ in rows]
    for i in range(0, len(ids), 1000):
        for c in db.query(Company).filter(Company.id.in_(ids[i:i + 1000])).all():
            if is_labor_heavy(c.industry or "", c.name or ""):
                add(c, 2)

    # 3. Seed operators.
    for name in seed_names():
        add(find_existing_company(db, name), 3)

    ordered = sorted(picked.values(), key=lambda t: (t[1] != "", t[1], t[0]))  # never-checked first, then oldest
    return [c for _, _, c in ordered[:cap]]


_TRAILING_CORP = re.compile(
    r"(?:,?\s+(?:inc|incorporated|corp|corporation|co|company|llc|ltd|plc|group|holdings|international|"
    r"brands|stores|logistics|industries|restaurants|resorts|entertainment|health|healthcare|foods))+\.?$",
    re.I,
)


def name_variants(company_name: str) -> list[str]:
    """'Kenco Logistics' → ['Kenco Logistics', 'Kenco']; 'Target Corporation' → [..., 'Target']."""
    name = (company_name or "").strip()
    out = [name] if name else []
    short = _TRAILING_CORP.sub("", name).strip(" ,.")
    if short and short.lower() != name.lower() and len(short) >= 3:
        out.append(short)
    return out


def title_names_company(title: str, company_name: str) -> bool:
    """The headline must name the company as a whole word (short names: exact case)."""
    t = title or ""
    for v in name_variants(company_name):
        flags = 0 if len(v) <= 4 else re.I
        if re.search(r"(?<![\w&])" + re.escape(v) + r"(?![\w&])", t, flags):
            return True
    return False


def mark_checked(company: Any, hits: int) -> None:
    meta = dict(getattr(company, "crm_metadata", None) or {})
    watch = dict(meta.get("watch") or {})
    watch["last_checked"] = datetime.now(timezone.utc).isoformat()
    watch["hits"] = int(watch.get("hits") or 0) + int(hits)
    meta["watch"] = watch
    company.crm_metadata = meta


def watch_queries(company_name: str) -> list[str]:
    return [t.format(name=company_name.replace('"', "")) for t in QUERY_TEMPLATES]


def existing_signal_urls(db, company_id: int, urls: Iterable[str]) -> set[str]:
    from app.models.signal import Signal

    urls = [u for u in urls if u]
    if not urls:
        return set()
    rows = db.query(Signal.source_url).filter(Signal.company_id == company_id, Signal.source_url.in_(urls)).all()
    return {r[0] for r in rows}
