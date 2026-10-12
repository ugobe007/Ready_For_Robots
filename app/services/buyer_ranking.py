"""Score every company with signals and (optionally) stamp the result.

Shared by scripts/rank_buyers.py and the daily buyers email so both use the
same numbers. Never deletes anything.
"""
from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Iterator

logger = logging.getLogger(__name__)

STAGE_RANK = {"rfp_open": 0, "expanding": 1, "exploring": 2, "preparing": 3, "primed": 4, "committed": 5, "watch": 6}


def iter_company_signals(db) -> Iterator[tuple[Any, list[dict]]]:
    """Yield (company, [signal dicts]) grouped by company, streaming."""
    from app.models.company import Company
    from app.models.signal import Signal

    q = (db.query(Signal.company_id, Signal.signal_type, Signal.signal_text, Signal.source_url, Signal.created_at)
         .order_by(Signal.company_id))
    current, bucket = None, []
    for row in q.yield_per(5000):
        if row.company_id != current and bucket:
            yield db.get(Company, current), bucket
            bucket = []
        current = row.company_id
        bucket.append({"signal_type": row.signal_type, "signal_text": row.signal_text,
                       "source_url": row.source_url, "created_at": row.created_at})
    if bucket:
        yield db.get(Company, current), bucket


def _company_groups(db) -> dict[int, int]:
    """{company_id: group_root_id} — rows that are the same company (name variants, same domain)."""
    from app.models.company import Company
    from app.services.company_identity import group_companies

    rows = db.query(Company.id, Company.name, Company.website_domain).yield_per(5000)
    return group_companies((r.id, r.name or "", r.website_domain) for r in rows)


def _pick_primary(members: list[Any], signal_counts: dict[int, int]) -> Any:
    """Most signals wins; then has website; then shortest clean name; then oldest id."""
    return sorted(
        members,
        key=lambda c: (-signal_counts.get(c.id, 0), 0 if getattr(c, "website", None) else 1,
                       len(c.name or ""), c.id),
    )[0]


def score_companies(db, *, apply: bool = False, commit_every: int = 500,
                    group_duplicates: bool = True) -> tuple[Counter, list[tuple[Any, Any]]]:
    """Assess every company with signals. Duplicate rows of one company (Target / Target
    Corporation / target.com) are scored once on their pooled evidence; every row gets
    the same stamp, and only the primary row is returned.

    Returns (stage counts per company group, [(primary company, readiness)])."""
    from app.services.buyer_readiness import assess_company

    groups = _company_groups(db) if group_duplicates else {}
    pooled: dict[int, list[dict]] = {}
    members: dict[int, list[Any]] = {}
    counts: dict[int, int] = {}
    for company, sigs in iter_company_signals(db):
        if company is None:
            continue
        root = groups.get(company.id, company.id)
        pooled.setdefault(root, []).extend(sigs)
        members.setdefault(root, []).append(company)
        counts[company.id] = len(sigs)

    stages: Counter = Counter()
    results: list[tuple[Any, Any]] = []
    for i, (root, sigs) in enumerate(pooled.items(), 1):
        rows = members[root]
        primary = _pick_primary(rows, counts)
        industry = primary.industry or next((c.industry for c in rows if c.industry and c.industry != "Unknown"), "")
        r = assess_company(primary.name or "", sigs, industry=industry or "")
        stages[r.stage] += 1
        results.append((primary, r))
        if apply:
            stamp = r.to_dict()
            stamp["primary_company_id"] = primary.id
            stamp["duplicate_company_ids"] = sorted(c.id for c in rows if c.id != primary.id)
            stamp["duplicate_names"] = sorted({c.name for c in rows if c.id != primary.id})[:10]
            for c in rows:
                prof = dict(c.automation_profile or {})
                prof["buyer_readiness"] = dict(stamp, is_primary=(c.id == primary.id))
                c.automation_profile = prof
            if i % commit_every == 0:
                db.commit()
    if apply:
        db.commit()
    results.sort(key=lambda cr: (STAGE_RANK.get(cr[1].stage, 9), -cr[1].score))
    return stages, results
