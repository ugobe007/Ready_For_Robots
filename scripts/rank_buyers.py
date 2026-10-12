#!/usr/bin/env python3
"""Rank COMPANIES by readiness to buy or pilot robots, from the signals you already have.

    python3 scripts/rank_buyers.py                         # dry run: stage counts, top 40, CSV
    python3 scripts/rank_buyers.py --apply                 # also stamp companies.automation_profile.buyer_readiness
    python3 scripts/rank_buyers.py --csv buyers.csv --min-stage evaluating

Stages: buying_now > evaluating > expanding > primed > watch (see app/services/buyer_readiness.py).
Reads every signal (job-posting signals included — they count as pain-at-scale,
never as a buyer by themselves). Never deletes anything.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

STAGE_RANK = {"buying_now": 0, "evaluating": 1, "expanding": 2, "primed": 3, "watch": 4}


def iter_company_signals(db):
    """Yield (company, [signals]) grouped by company, streaming."""
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="stamp companies.automation_profile.buyer_readiness")
    ap.add_argument("--csv", default="reports/buyer_readiness.csv")
    ap.add_argument("--min-stage", default="primed", choices=list(STAGE_RANK))
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.services.buyer_readiness import assess_company

    db = SessionLocal()
    results = []
    stages: Counter = Counter()
    try:
        for i, (company, sigs) in enumerate(iter_company_signals(db), 1):
            if company is None:
                continue
            r = assess_company(company.name or "", sigs)
            stages[r.stage] += 1
            if STAGE_RANK[r.stage] <= STAGE_RANK[args.min_stage]:
                results.append((company, r))
            if args.apply:
                prof = dict(company.automation_profile or {})
                prof["buyer_readiness"] = r.to_dict()
                company.automation_profile = prof
                if i % 500 == 0:
                    db.commit()
        if args.apply:
            db.commit()

        results.sort(key=lambda cr: (STAGE_RANK[cr[1].stage], -cr[1].score))
        Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["company", "stage", "score", "why", "evidence_1", "evidence_2", "evidence_3", "evidence_url",
                        "workflows", "open_automatable_postings", "pain", "industry", "city", "state", "website"])
            for c, r in results:
                ev = [f"{e.label}: {e.text}" for e in r.evidence[:3]] + ["", "", ""]
                url = next((e.source_url for e in r.evidence if e.source_url), "")
                w.writerow([c.name, r.stage, r.score, r.why, *ev[:3], url, "; ".join(r.workflows),
                            r.open_automatable_postings, "; ".join(r.pain_labels), c.industry or "",
                            c.location_city or "", c.location_state or "", c.website or ""])
    finally:
        db.close()

    print("companies by stage:")
    for st in STAGE_RANK:
        print(f"  {st:11} {stages[st]:>7,}")
    print(f"\ntop {min(args.top, len(results))}:")
    for c, r in results[: args.top]:
        lead = r.evidence[0] if r.evidence else None
        print(f"  {r.stage:11} {r.score:5.1f}  {c.name[:34]:34} {(lead.label + ': ' + lead.text) if lead else r.why}"[:150])
    print(f"\nCSV: {args.csv}  ({len(results):,} companies at stage >= {args.min_stage})")
    if not args.apply:
        print("DRY RUN — companies not stamped. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
