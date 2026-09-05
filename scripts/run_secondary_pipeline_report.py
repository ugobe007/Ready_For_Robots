#!/usr/bin/env python3
"""
Run secondary pipelines on sales leads + humanoid benchmarks and print a combined report.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from app.database import SessionLocal
from app.services.humanoid_secondary_pass import (
    run_humanoid_secondary_pass_batch,
    select_humanoid_repair_candidates,
)
from app.services.humanoid_spec_gaps import analyze_humanoid_spec_gaps
from app.services.lead_gap_audit import select_gap_repair_candidates
from app.services.lead_secondary_pass import run_secondary_pass_batch


def _lead_gap_histogram(reports) -> dict:
    counts: Counter = Counter()
    for r in reports:
        for g in r.gaps:
            counts[g] += 1
    return dict(counts.most_common())


def main() -> int:
    parser = argparse.ArgumentParser(description="Combined secondary pipeline report")
    parser.add_argument("--lead-limit", type=int, default=10)
    parser.add_argument("--humanoid-limit", type=int, default=8)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--no-news", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        lead_candidates = select_gap_repair_candidates(db, limit=30, min_score=15.0)
        humanoid_gaps = analyze_humanoid_spec_gaps(db, sparse_threshold_pct=85.0)
        humanoid_candidates = select_humanoid_repair_candidates(db, limit=20)

        report = {
            "sales_leads": {
                "candidates_audited": len(lead_candidates),
                "gap_histogram_top30": _lead_gap_histogram(lead_candidates),
                "top_candidates": [r.to_dict() for r in lead_candidates[:10]],
            },
            "humanoids": {
                "total_robots": humanoid_gaps.get("total_robots"),
                "avg_spec_fill_pct": humanoid_gaps.get("avg_spec_fill_pct"),
                "robots_sparse_specs": humanoid_gaps.get("robots_sparse_specs"),
                "sparsest": (humanoid_gaps.get("sparse_robots") or [])[:8],
                "repair_candidates": humanoid_candidates[:10],
            },
        }

        if not args.audit_only:
            report["sales_leads"]["batch"] = run_secondary_pass_batch(
                db,
                limit=args.lead_limit,
                min_score=15.0,
                use_llm=not args.no_llm,
                rescore=True,
            )
            report["humanoids"]["batch"] = run_humanoid_secondary_pass_batch(
                db,
                limit=args.humanoid_limit,
                use_llm_scrape=not args.no_llm,
                persist_deployment_news=not args.no_news,
                deployment_query_cap=16,
            )

        print(json.dumps(report, indent=2, default=str))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
