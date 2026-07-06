"""
Cal pipeline development report — what autopilot has done recently.

Read-only. Prints send volume, delivery-status breakdown, follow-ups, queue
state, recent sends, and autopilot config for a rolling window.

Run on Fly:
    fly ssh console -a ready-2-robot -C "sh -c 'cd /code && python scripts/cal_pipeline_report.py --hours 16'"
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Cal pipeline development report.")
    parser.add_argument("--hours", type=int, default=16, help="Look-back window in hours (default 16).")
    args = parser.parse_args()

    from sqlalchemy import func
    from app.database import SessionLocal
    from app.models.crm import CrmAccount
    from app.models.outreach import OutreachMessage, OutreachReply
    from app.services.cal_autonomy import get_cal_autonomy_status

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=max(1, args.hours))

        window = (
            db.query(OutreachMessage)
            .filter(OutreachMessage.sent_at.isnot(None), OutreachMessage.sent_at >= since)
            .order_by(OutreachMessage.sent_at.desc())
            .all()
        )
        intro = [m for m in window if (m.send_identity or "") != "sequence"]
        followup = [m for m in window if (m.send_identity or "") == "sequence"]
        status_mix: Counter = Counter((m.status or "unknown") for m in window)
        identity_mix: Counter = Counter((m.send_identity or "unknown") for m in window)

        replies = (
            db.query(func.count(OutreachReply.id))
            .filter(OutreachReply.received_at >= since)
            .scalar()
            or 0
        )
        total_sent = (
            db.query(func.count(OutreachMessage.id)).filter(OutreachMessage.sent_at.isnot(None)).scalar() or 0
        )
        replies_total = db.query(func.count(OutreachReply.id)).scalar() or 0

        # Queue state (lightweight counts)
        unsent = (
            db.query(func.count(CrmAccount.id))
            .filter(CrmAccount.outreach_draft.isnot(None), CrmAccount.outreach_sent_at.is_(None))
            .scalar()
            or 0
        )
        suppressed = (
            db.query(func.count(CrmAccount.id))
            .filter(CrmAccount.outreach_stage == "suppressed_junk")
            .scalar()
            or 0
        )
        sent_accts = (
            db.query(func.count(CrmAccount.id)).filter(CrmAccount.outreach_sent_at.isnot(None)).scalar() or 0
        )

        st = get_cal_autonomy_status()

        print("=" * 64)
        print(f"CAL PIPELINE REPORT — last {args.hours}h  ({now.isoformat(timespec='minutes')})")
        print("=" * 64)
        print(f"\nAutopilot: {'ON' if st.get('enabled') else 'OFF'}  "
              f"(every {st.get('every_hours')}h, send_limit {st.get('send_limit')}, "
              f"followup_limit {st.get('followup_limit')}, manual_approval {st.get('manual_approval')})")

        print(f"\nActivity (last {args.hours}h)")
        print(f"  intro emails sent:    {len(intro)}")
        print(f"  follow-up emails:     {len(followup)}")
        print(f"  inbound replies:      {replies}")
        print(f"  sends by identity:    {dict(identity_mix)}")

        print("\nDelivery status of window sends")
        if status_mix:
            for status, n in status_mix.most_common():
                print(f"  {n:>4}  {status}")
        else:
            print("  (no sends in window)")
        delivered = sum(status_mix.get(s, 0) for s in ("delivered", "opened", "clicked", "replied"))
        opened = sum(status_mix.get(s, 0) for s in ("opened", "clicked", "replied"))
        problems = sum(status_mix.get(s, 0) for s in ("bounced", "complained", "suppressed", "failed"))
        denom = len(window) or 1
        print(f"  → delivered+: {delivered}/{len(window)} ({100*delivered//denom}%)  "
              f"opened+: {opened}  problems: {problems}")

        print("\nQueue right now")
        print(f"  unsent drafts:        {unsent}")
        print(f"  suppressed (junk):    {suppressed}")
        print(f"  accounts contacted:   {sent_accts}")
        print(f"  total sent (all-time):{total_sent}   replies (all-time): {replies_total}")

        print(f"\nRecent sends (latest {min(10, len(window))})")
        for m in window[:10]:
            when = m.sent_at.strftime("%m-%d %H:%M") if m.sent_at else "?"
            subj = (m.subject or "")[:52]
            print(f"  {when}  [{(m.status or '?'):>9}]  {(m.to_email or '?')[:32]:32}  {subj}")

        print("\n" + "=" * 64)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
