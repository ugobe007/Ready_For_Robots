"""Dry-run the lead research agent and write an audit report.

Usage:
    PYTHONPATH=. python3 scripts/dry_run_lead_research_agent.py --limit 5
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import app.models  # noqa: F401 - register SQLAlchemy models
from app.database import SessionLocal
from app.services.lead_research_agent import research_active_leads


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run lead research agent")
    parser.add_argument("--limit", type=int, default=5, help="Maximum candidate companies to inspect")
    parser.add_argument("--lookback-days", type=int, default=30, help="Signal lookback window")
    parser.add_argument("--out", type=str, default="", help="Optional CSV output path")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = research_active_leads(
            db,
            limit=max(1, min(args.limit, 50)),
            dry_run=True,
            lookback_days=max(1, args.lookback_days),
        )
    finally:
        db.close()

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    out_path = Path(args.out) if args.out else reports_dir / (
        "lead_research_dry_run_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )
    rows = result.get("results") or []
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "company_id",
                "company_name",
                "candidates_seen",
                "updates_created",
                "duplicates_skipped",
                "notifications_created",
                "planned_queries",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "company_id": row.get("company_id"),
                    "company_name": row.get("company_name"),
                    "candidates_seen": row.get("candidates_seen"),
                    "updates_created": row.get("updates_created"),
                    "duplicates_skipped": row.get("duplicates_skipped"),
                    "notifications_created": row.get("notifications_created"),
                    "planned_queries": " | ".join(row.get("planned_queries") or []),
                }
            )

    print(
        "Lead research dry run complete: "
        f"{result.get('companies_considered', 0)} companies, "
        f"{result.get('updates_created', 0)} potential updates, "
        f"{result.get('duplicates_skipped', 0)} duplicates. "
        f"Report: {out_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
