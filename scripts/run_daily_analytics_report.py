#!/usr/bin/env python3
"""
Run Daily Opportunity Analytics Report
======================================
Generates report answering:
- What type of automation is required or inferred from opportunity postings?
- What type of robots are needed and what specs?
- Is there expected ROI or schedule for running trials?
- What are the most common tasks to automate?
- Industry, geography, top companies breakdown.

Usage:
    python scripts/run_daily_analytics_report.py [--days 7] [--format json|markdown]
"""
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from app.database import SessionLocal
from app.services.daily_analytics_service import get_daily_analytics, format_report_markdown


def main():
    parser = argparse.ArgumentParser(description="Run Daily Opportunity Analytics Report")
    parser.add_argument("--days", type=int, default=1, help="Number of days to analyze (default: 1)")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--save", action="store_true", help="Save report to reports/")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        analytics = get_daily_analytics(db, days=args.days)
    finally:
        db.close()

    if args.format == "markdown":
        report = format_report_markdown(analytics)
        print(report)
        if args.save:
            reports_dir = Path(__file__).parent.parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            from datetime import datetime, timezone
            filename = f"daily_analytics_{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
            filepath = reports_dir / filename
            filepath.write_text(report)
            (reports_dir / "daily_analytics_latest.md").write_text(report)
            print(f"\nSaved to {filepath}")
    else:
        import json
        print(json.dumps(analytics, indent=2))


if __name__ == "__main__":
    main()
