"""Score every company with signals and (optionally) stamp the result.

Shared by scripts/rank_buyers.py and the daily buyers email so both use the
same numbers. Never deletes anything.
"""
from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Iterator

logger = logging.getLogger(__name__)

STAGE_RANK = {"buying_now": 0, "evaluating": 1, "expanding": 2, "preparing": 3, "primed": 4, "watch": 5}


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


def score_companies(db, *, apply: bool = False, commit_every: int = 500) -> tuple[Counter, list[tuple[Any, Any]]]:
    """Assess every company that has signals. Returns (stage counts, [(company, readiness)])."""
    from app.services.buyer_readiness import assess_company

    stages: Counter = Counter()
    results: list[tuple[Any, Any]] = []
    for i, (company, sigs) in enumerate(iter_company_signals(db), 1):
        if company is None:
            continue
        r = assess_company(company.name or "", sigs, industry=company.industry or "")
        stages[r.stage] += 1
        results.append((company, r))
        if apply:
            prof = dict(company.automation_profile or {})
            prof["buyer_readiness"] = r.to_dict()
            company.automation_profile = prof
            if i % commit_every == 0:
                db.commit()
    if apply:
        db.commit()
    results.sort(key=lambda cr: (STAGE_RANK.get(cr[1].stage, 9), -cr[1].score))
    return stages, results
