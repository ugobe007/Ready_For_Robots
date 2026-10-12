#!/usr/bin/env python3
"""Rank COMPANIES by readiness to buy or pilot robots, from the signals you already have.

    python3 scripts/rank_buyers.py                         # dry run: stage counts, top 40, CSV
    python3 scripts/rank_buyers.py --apply                 # also stamp companies.automation_profile.buyer_readiness
    python3 scripts/rank_buyers.py --csv buyers.csv --min-stage evaluating

Stages: rfp_open > expanding > exploring > preparing > primed > committed > watch (see app/services/buyer_readiness.py).
Reads every signal (job-posting signals included — they count as pain-at-scale,
never as a buyer by themselves). Never deletes anything.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.buyer_ranking import STAGE_RANK  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="stamp companies.automation_profile.buyer_readiness")
    ap.add_argument("--csv", default="reports/buyer_readiness.csv")
    ap.add_argument("--min-stage", default="primed", choices=list(STAGE_RANK))
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.services.buyer_ranking import score_companies

    db = SessionLocal()
    try:
        stages, scored = score_companies(db, apply=args.apply)
        results = [(c, r) for c, r in scored if STAGE_RANK[r.stage] <= STAGE_RANK[args.min_stage]]
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
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
