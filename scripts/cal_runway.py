"""How many eligible HOT/WARM buyers has Cal NOT yet contacted? (send runway)"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=300, help="HOT/WARM window size to measure.")
    args = ap.parse_args()

    from app.api.admin_extended import _hot_warm_companies
    from app.database import SessionLocal
    from app.models.crm import CrmAccount
    from app.services.cal_autonomy import _cal_buyer_eligible

    db = SessionLocal()
    try:
        pool = _hot_warm_companies(db, args.limit)
        eligible = ineligible = sent = unsent_no_draft = unsent_ready = 0
        ready_names = []
        for company, _s, _t in pool:
            ok, _r = _cal_buyer_eligible(company)
            if not ok:
                ineligible += 1
                continue
            eligible += 1
            acct = db.query(CrmAccount).filter(CrmAccount.company_id == company.id).first()
            if acct and acct.outreach_sent_at:
                sent += 1
            elif acct and acct.outreach_draft:
                unsent_ready += 1
                if len(ready_names) < 15:
                    ready_names.append(company.name)
            else:
                unsent_no_draft += 1
                if len(ready_names) < 15:
                    ready_names.append(company.name + " (needs draft)")
        print("=" * 54)
        print("CAL SEND RUNWAY (HOT/WARM pool)")
        print("=" * 54)
        print(f"  pool size           {len(pool)}")
        print(f"  eligible            {eligible}")
        print(f"  ineligible (gated)  {ineligible}")
        print(f"  already contacted   {sent}")
        print(f"  eligible + unsent   {unsent_ready + unsent_no_draft}"
              f"  (ready={unsent_ready}, needs-draft={unsent_no_draft})")
        if ready_names:
            print("\n  next up:")
            for n in ready_names:
                print(f"    {n}")
        print("=" * 54)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
