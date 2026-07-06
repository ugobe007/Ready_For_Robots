"""
Read-only pre-flight checks for Cal before re-enabling autopilot.

Validates the things autopilot depends on, without sending anything:
  1. Draft guard   — do unsent drafts pass draft_needs_regeneration (new voice, complete)?
  2. Sendability   — how many ready drafts have a usable recipient email?
  3. Junk hygiene  — how many drafts are suppressed as junk?
  4. Matching      — sample vendors; flag any off-domain buyer matches (aviation/finance/etc).
  5. Delivery cfg  — Resend API key + from-address present.

Run on Fly:
    fly ssh console -a ready-2-robot -C "sh -c 'cd /code && python scripts/cal_preflight.py'"

Add --fast to skip the slow vendor-matching sample (checks 1-3 + 5 only):
    fly ssh console -a ready-2-robot -C "sh -c 'cd /code && python scripts/cal_preflight.py --fast'"
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Buyer industries with no inherent robot-domain fit — a match here to a non-service
# vendor is suspicious unless grounded in explicit requirements.
_NO_FIT_INDUSTRIES = ("airport", "aviation", "airline", "finance", "bank", "media", "government")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Cal pre-flight checks.")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip the slow vendor-matching sample (checks 1-3 + 5 only).",
    )
    parser.add_argument(
        "--vendors",
        type=int,
        default=60,
        help="How many vendors to sample for the matching check (default 60).",
    )
    args = parser.parse_args()

    from app.database import SessionLocal
    from app.models.crm import CrmAccount
    from app.models.robot_company import RobotCompany
    from app.services.cal_draft_guard import draft_needs_regeneration
    from app.api.robot_companies import _match_buyer_leads

    db = SessionLocal()
    try:
        print("=" * 62)
        print("CAL PRE-FLIGHT (read-only)")
        print("=" * 62)

        # 1 + 2 + 3 — draft guard, sendability, junk
        accts = db.query(CrmAccount).filter(CrmAccount.outreach_draft.isnot(None)).all()
        unsent = [a for a in accts if a.outreach_sent_at is None]
        suppressed = db.query(CrmAccount).filter(CrmAccount.outreach_stage == "suppressed_junk").count()

        guard_ok = 0
        guard_fail: Counter = Counter()
        with_email = 0
        for a in unsent:
            needs, reason = draft_needs_regeneration(
                a.outreach_draft, account_type=(a.account_type or "buyer")
            )
            if needs:
                guard_fail[reason] += 1
            else:
                guard_ok += 1
            if (a.contact_email or "").strip():
                with_email += 1

        print(f"\n[1] Draft guard — unsent drafts: {len(unsent)}")
        print(f"    pass (new voice, complete): {guard_ok}")
        print(f"    needs regeneration:         {sum(guard_fail.values())}")
        for reason, n in guard_fail.most_common():
            print(f"        - {n:>3}  {reason}")
        print(f"\n[2] Sendability — unsent drafts with recipient email: {with_email}/{len(unsent)}")
        print(f"\n[3] Junk hygiene — drafts suppressed as junk: {suppressed}")

        # 4 — matching sanity (slow: samples vendors × 300-candidate match each)
        checked = 0
        flagged = []
        empty = 0
        if args.fast:
            print("\n[4] Matching — skipped (--fast)")
        else:
            vendors = (
                db.query(RobotCompany)
                .filter(RobotCompany.robot_type.isnot(None))
                .limit(max(args.vendors, 1))
                .all()
            )
            for v in vendors:
                ms = _match_buyer_leads(db, v, limit=3)
                checked += 1
                if not ms:
                    empty += 1
                for m in ms:
                    ind = (m.get("industry") or "").lower()
                    if any(tok in ind for tok in _NO_FIT_INDUSTRIES):
                        rt = (v.robot_type or "").lower()
                        # aviation/finance buyer matched to a warehouse/cleaning vendor is the smell
                        if "service" not in rt and "humanoid" not in rt:
                            flagged.append((v.company_name, v.robot_type, m.get("company_name"), m.get("industry")))
            print(f"\n[4] Matching — vendors sampled: {checked} (no-match: {empty})")
            if flagged:
                print(f"    ⚠ off-domain matches flagged: {len(flagged)}")
                for vn, rt, bn, bi in flagged[:15]:
                    print(f"        {vn} ({rt}) -> {bn} | {bi}")
            else:
                print("    ✓ no off-domain (aviation/finance/etc → AMR/industrial) matches")

        # 5 — delivery config
        has_key = bool((os.getenv("RESEND_API_KEY") or "").strip())
        from_email = (os.getenv("RESEND_FROM_EMAIL") or "").strip()
        print(f"\n[5] Delivery — RESEND_API_KEY set: {has_key} | from: {from_email or '(unset)'}")

        print("\n" + "=" * 62)
        ready = guard_ok
        match_note = "matching skipped" if args.fast else f"{len(flagged)} off-domain matches"
        print(f"SUMMARY: {ready} sendable drafts pass guard, {suppressed} junk suppressed, "
              f"{match_note}, delivery {'OK' if has_key else 'MISCONFIGURED'}")
        print("=" * 62)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
