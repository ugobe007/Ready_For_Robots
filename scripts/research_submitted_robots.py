#!/usr/bin/env python3
"""Research pass over stored FIND robot URLs.

Grounded spec/news snippets only. Incomplete stays incomplete. Caps crawl time.

  python3 scripts/research_submitted_robots.py
  python3 scripts/research_submitted_robots.py --limit 10 --budget 8
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Research stored robot URLs")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--budget", type=float, default=8.0, help="Seconds per robot")
    parser.add_argument("--stale-hours", type=float, default=24.0)
    args = parser.parse_args()

    from app.database import SessionLocal
    from app.services.robot_url_research import research_due_robots

    db = SessionLocal()
    try:
        rows = research_due_robots(
            db,
            limit=args.limit,
            budget_sec=args.budget,
            stale_hours=args.stale_hours,
        )
    finally:
        db.close()
    print(json.dumps({"researched": len(rows), "results": rows}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
