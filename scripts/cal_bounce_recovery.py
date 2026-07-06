"""
Unlock real buyer supply locked behind bounce-era sends.

During the guessed-domain era, Cal emailed real buyers (hotels, airlines, casinos)
at fabricated domains -> bounces. Those accounts now carry outreach_sent_at, so Cal
will not re-contact them at the corrected real domain. This script finds accounts
whose ONLY outcome was a bounce/complaint AT A DOMAIN THAT DIFFERS from the company's
real website domain (i.e. a fixable guessed-domain failure), and (with --apply) clears
outreach_sent_at so Cal re-contacts them properly through the recipient-trust gate.

Read-only by default.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_LANDED = {"delivered", "opened", "clicked", "replied", "resent"}
_FAILED = {"bounced", "complained", "suppressed", "failed"}


def _dom(email: str | None) -> str:
    return (email or "").split("@")[-1].lower().strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Clear outreach_sent_at for recoverable accounts.")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.models.outreach import OutreachMessage
    from app.services.cal_autonomy import _cal_buyer_eligible
    from app.services.lead_enrichment import company_website_domain

    db = SessionLocal()
    try:
        status_mix = Counter(s for (s,) in db.query(OutreachMessage.status).all())
        print("=" * 60)
        print("OUTREACH STATUS DISTRIBUTION")
        print("=" * 60)
        for s, n in status_mix.most_common():
            print(f"  {n:>5}  {s}")

        # Group messages by account
        msgs = db.query(OutreachMessage).all()
        by_acct: dict = {}
        for m in msgs:
            by_acct.setdefault(m.crm_account_id, []).append(m)

        recoverable = []
        landed_ok = bounced_real_domain = ineligible_now = 0
        for acct_id, ms in by_acct.items():
            outcomes = {(m.status or "").lower() for m in ms}
            if outcomes & _LANDED:
                landed_ok += 1
                continue
            if not (outcomes & _FAILED):
                continue  # still pending, leave alone
            acct = db.query(CrmAccount).filter(CrmAccount.id == acct_id).first()
            if not acct or not acct.company_id:
                continue
            company = db.query(Company).filter(Company.id == acct.company_id).first()
            if not company:
                continue
            ok, _r = _cal_buyer_eligible(company, acct)
            if not ok:
                ineligible_now += 1
                continue
            real = (company_website_domain(company, acct) or "").lower()
            bounced_domains = {_dom(m.to_email) for m in ms if (m.status or "").lower() in _FAILED}
            # fixable = bounced at a domain that is NOT the real one
            if real and all(d != real for d in bounced_domains if d):
                recoverable.append((company.name, real, sorted(bounced_domains)))
            else:
                bounced_real_domain += 1

        print("\n" + "=" * 60)
        print("RECOVERY ANALYSIS")
        print("=" * 60)
        print(f"  accounts that landed (delivered/opened/replied)  {landed_ok}")
        print(f"  bounced at REAL domain (address bad, skip)        {bounced_real_domain}")
        print(f"  ineligible now (skip)                             {ineligible_now}")
        print(f"  RECOVERABLE (bounced at guessed domain)           {len(recoverable)}")
        for name, real, bd in recoverable[:25]:
            print(f"      {name[:28]:28} real={real:24} bounced={bd[:2]}")

        if args.apply and recoverable:
            names = {r[0] for r in recoverable}
            n = 0
            for acct_id, ms in by_acct.items():
                acct = db.query(CrmAccount).filter(CrmAccount.id == acct_id).first()
                if not acct or not acct.company_id:
                    continue
                company = db.query(Company).filter(Company.id == acct.company_id).first()
                if company and company.name in names:
                    acct.outreach_sent_at = None
                    if acct.outreach_stage == "suppressed_junk":
                        acct.outreach_stage = None
                    n += 1
            db.commit()
            print(f"\nAPPLIED: reset outreach_sent_at for {n} recoverable accounts.")
        elif not args.apply:
            print("\nDry-run — no changes. Re-run with --apply to unlock re-contact.")
        print("=" * 60)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
