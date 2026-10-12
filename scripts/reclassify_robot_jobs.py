#!/usr/bin/env python3
"""Re-tier existing robot_jobs with the workflow ontology. Never deletes.

    python3 scripts/reclassify_robot_jobs.py            # dry run: tier counts + samples
    python3 scripts/reclassify_robot_jobs.py --apply    # write opportunity_tier / class / score

Tier 1 automation intent · 2 automation-ready · 3 automatable work · 0 not an opportunity.
Tier 0 rows are only labelled, not removed. Hide them in queries, don't delete them.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.robot_directed_discovery import RobotJob
    from app.services.automation_opportunity_classifier import _class_for
    from app.services.workflow_ontology import analyze_posting

    db = SessionLocal()
    counts: Counter = Counter()
    samples: dict[int, list[str]] = {}
    try:
        for i, row in enumerate(db.query(RobotJob).yield_per(1000), 1):
            req = dict(row.requirements or {})
            desc = str(req.get("job_description") or row.observed_workflow or "")
            a = analyze_posting(row.robot_compatible_task or "", desc, row.company_name or "")
            counts[a.tier] += 1
            samples.setdefault(a.tier, [])
            if len(samples[a.tier]) < 6:
                samples[a.tier].append(f"    {row.company_name[:30]:30} | {(row.robot_compatible_task or '')[:50]:50} | {a.reason}")
            if args.apply:
                row.opportunity_tier = a.tier
                row.opportunity_class = int(_class_for(a))
                req["opportunity"] = a.to_requirements()
                if a.primary and (not req.get("job_function") or row.action in (None, "", "work")):
                    req["job_function"] = a.primary.key
                    row.action = a.primary.key
                row.requirements = req
                if i % 1000 == 0:
                    db.commit()
        if args.apply:
            db.commit()
    finally:
        db.close()
    names = {1: "automation intent", 2: "automation ready", 3: "automatable work", 0: "not an opportunity"}
    for tier in (1, 2, 3, 0):
        print(f"tier {tier} {names[tier]:20} {counts[tier]:>8,}")
        print("\n".join(samples.get(tier, [])))
    print("\nwritten." if args.apply else "\nDRY RUN — re-run with --apply (updates tiers only, deletes nothing).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
