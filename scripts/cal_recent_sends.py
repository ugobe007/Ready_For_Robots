"""Show status of OutreachMessages created in the last N minutes (delivery watch)."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=15)
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.outreach import OutreachMessage

    since = datetime.now(timezone.utc) - timedelta(minutes=args.minutes)
    db = SessionLocal()
    try:
        msgs = (
            db.query(OutreachMessage)
            .filter(OutreachMessage.created_at >= since)
            .order_by(OutreachMessage.created_at.desc())
            .all()
        )
        print("=" * 64)
        print(f"OUTREACH MESSAGES — last {args.minutes} min ({len(msgs)})")
        print("=" * 64)
        for m in msgs:
            ts = m.created_at.strftime("%H:%M:%S") if m.created_at else "-"
            print(f"  {ts}  {(m.status or '?'):11} {(m.to_email or '-')}")
        print("=" * 64)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
