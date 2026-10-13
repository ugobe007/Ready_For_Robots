#!/usr/bin/env python3
"""Generate sales-ready robot job opportunity report.

Produces clean, structured output matching the PDF format with:
- RFP Open section (budget confirmed)  
- Exploring section (active pipeline)
- Per-company cards with job, robot types, timeline, budget, evidence

Usage:
    python3 scripts/generate_sales_report.py                     # top 25 opportunities
    python3 scripts/generate_sales_report.py --limit 50          # top 50
    python3 scripts/generate_sales_report.py --stage rfp_open    # only RFP open companies
    python3 scripts/generate_sales_report.py --output report.txt # save to file
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.signal import Signal  # noqa: E402
from app.services.buyer_ranking import STAGE_RANK, score_companies  # noqa: E402
from app.services.sales_report import build_job_opportunity, format_sales_report_text  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--limit", type=int, default=25, help="Number of opportunities to include")
    ap.add_argument(
        "--stage",
        choices=["rfp_open", "exploring", "expanding", "piloting", "all"],
        default="all",
        help="Filter by stage (default: all active stages)",
    )
    ap.add_argument("--output", help="Write report to file instead of stdout")
    args = ap.parse_args()
    
    db = SessionLocal()
    try:
        # Score all companies
        stages, scored = score_companies(db, apply=False)
        
        # Filter by stage
        if args.stage == "all":
            # Include all active buyer stages (not committed/watch)
            active_stages = ["rfp_open", "exploring", "expanding", "piloting", "preparing", "primed"]
            results = [
                (c, r) for c, r in scored
                if r.stage in active_stages
            ]
        else:
            results = [(c, r) for c, r in scored if r.stage == args.stage]
        
        # Take top N
        results = results[: args.limit]
        
        if not results:
            print(f"No companies found at stage {args.stage}", file=sys.stderr)
            return 1
        
        # Build job opportunities
        opportunities = []
        for rank, (company, readiness) in enumerate(results, 1):
            # Get all signals for this company
            signals = db.query(Signal).filter(Signal.company_id == company.id).all()
            signal_dicts = [
                {
                    "signal_type": s.signal_type,
                    "signal_text": s.signal_text,
                    "signal_strength": s.signal_strength,
                    "source_url": s.source_url,
                    "date_published": s.date_published,
                }
                for s in signals
            ]
            
            opp = build_job_opportunity(
                rank=rank,
                company=company,
                readiness=readiness,
                signals=signal_dicts,
            )
            opportunities.append(opp)
        
        # Format report
        report_text = format_sales_report_text(opportunities)
        
        # Output
        if args.output:
            Path(args.output).write_text(report_text, encoding="utf-8")
            print(f"Sales report written to {args.output} ({len(opportunities)} opportunities)")
        else:
            print(report_text)
        
        # Summary
        print(f"\n-- Generated {len(opportunities)} opportunities --", file=sys.stderr)
        print(f"RFP Open: {sum(1 for o in opportunities if o.status and o.status.startswith('RFP'))}", file=sys.stderr)
        print(f"Exploring: {sum(1 for o in opportunities if o.status and o.status.startswith('Exploring'))}", file=sys.stderr)
        print(f"Expanding: {sum(1 for o in opportunities if o.status and o.status.startswith('Expanding'))}", file=sys.stderr)
        
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
