#!/usr/bin/env python3
"""Send Cal daily activity digest email (operator inbox)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Cal daily activity digest")
    parser.add_argument("--force", action="store_true", help="Send even if already sent today")
    parser.add_argument("--preview", action="store_true", help="Print body only; do not email")
    parser.add_argument("--period-hours", type=int, default=24)
    args = parser.parse_args()

    from app.database import SessionLocal
    from app.services.cal_daily_digest import build_cal_daily_digest, send_cal_daily_digest

    with SessionLocal() as db:
        if args.preview:
            digest = build_cal_daily_digest(db, period_hours=args.period_hours)
            print(digest["subject"])
            print()
            print(digest["body_text"])
            return 0
        result = send_cal_daily_digest(db, period_hours=args.period_hours, force=args.force)
    print(result)
    return 0 if result.get("sent") or args.preview else 1


if __name__ == "__main__":
    raise SystemExit(main())
