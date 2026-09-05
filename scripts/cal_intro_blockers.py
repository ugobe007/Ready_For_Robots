"""
Diagnose why HOT/WARM intro candidates are not currently sendable.

Focuses on the exact intro path gates and highlights the top blockers:
- untrusted recipient source/domain
- zerobounce_do_not_mail (or other deliverability failures)

Read-only.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _short(text: str | None, n: int = 72) -> str:
    raw = (text or "").strip()
    if len(raw) <= n:
        return raw
    return raw[: n - 1] + "…"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500, help="HOT/WARM pool window to scan.")
    ap.add_argument("--samples", type=int, default=20, help="Sample rows per blocker bucket.")
    ap.add_argument("--use-apollo", action="store_true", help="Opt in to Apollo lookup during resolution.")
    args = ap.parse_args()

    from app.api.admin_extended import _hot_warm_companies
    from app.database import SessionLocal
    from app.models.crm import CrmAccount
    from app.services.cal_autonomy import _cal_buyer_eligible, resolve_cal_admin_context
    from app.services.lead_enrichment import (
        address_previously_bounced,
        outreach_recipient_trusted,
        resolve_outreach_email,
        verify_email_deliverable,
    )

    db = SessionLocal()
    try:
        ctx = resolve_cal_admin_context(db)
        if not ctx:
            print("No Cal admin context available.")
            return 1
        _uid, team = ctx

        pool = _hot_warm_companies(db, limit=max(100, args.limit))
        company_ids = [c.id for c, _score, _tier in pool]

        accounts: dict[int, CrmAccount] = {}
        if company_ids:
            for acct in db.query(CrmAccount).filter(
                CrmAccount.company_id.in_(company_ids),
                CrmAccount.team_id == team.id,
            ).all():
                if acct.company_id:
                    accounts[acct.company_id] = acct

        counts = Counter()
        sample_untrusted: list[tuple[int, str, str, str]] = []
        sample_do_not_mail: list[tuple[int, str, str, str]] = []
        sample_other_deliverability: list[tuple[int, str, str, str]] = []
        sample_sendable: list[tuple[int, str, str, str]] = []

        for company, _score, tier in pool:
            if tier not in ("HOT", "WARM"):
                continue
            acct = accounts.get(company.id)

            if not acct or not acct.outreach_draft:
                counts["no_draft_or_account"] += 1
                continue
            if acct.outreach_sent_at:
                counts["already_sent"] += 1
                continue

            ok, why = _cal_buyer_eligible(company, acct)
            if not ok:
                counts[f"ineligible:{why}"] += 1
                continue

            to_email, source, _title = resolve_outreach_email(
                company,
                acct,
                use_apollo=args.use_apollo,
            )
            if not to_email:
                counts["no_email"] += 1
                continue

            if address_previously_bounced(db, to_email):
                counts["suppressed_bounced"] += 1
                continue

            trusted, trust_reason = outreach_recipient_trusted(company, acct, to_email, source)
            if not trusted:
                counts[f"untrusted:{source or 'unknown'}"] += 1
                if len(sample_untrusted) < args.samples:
                    sample_untrusted.append((company.id, company.name or "", to_email, trust_reason))
                continue

            deliverable, deliver_reason = verify_email_deliverable(to_email)
            if not deliverable:
                key = f"undeliverable:{deliver_reason}"
                counts[key] += 1
                row = (company.id, company.name or "", to_email, deliver_reason)
                if "do_not_mail" in (deliver_reason or "") and len(sample_do_not_mail) < args.samples:
                    sample_do_not_mail.append(row)
                elif len(sample_other_deliverability) < args.samples:
                    sample_other_deliverability.append(row)
                continue

            counts["sendable_now"] += 1
            if len(sample_sendable) < args.samples:
                sample_sendable.append((company.id, company.name or "", to_email, source or ""))

        print("=" * 70)
        print("CAL INTRO BLOCKERS — HOT/WARM UNSENT DIAGNOSTIC")
        print("=" * 70)
        print(f"pool scanned                              {len(pool)}")
        for key, val in counts.most_common(20):
            print(f"{key:40} {val}")

        if sample_do_not_mail:
            print("\nTop do_not_mail blockers:")
            for cid, name, email, reason in sample_do_not_mail:
                print(f"  {cid:>6}  {_short(name, 34):34}  {email:34}  {reason}")

        if sample_untrusted:
            print("\nTop untrusted blockers:")
            for cid, name, email, reason in sample_untrusted:
                print(f"  {cid:>6}  {_short(name, 34):34}  {email:34}  {reason}")

        if sample_other_deliverability:
            print("\nOther deliverability blockers:")
            for cid, name, email, reason in sample_other_deliverability:
                print(f"  {cid:>6}  {_short(name, 34):34}  {email:34}  {reason}")

        if sample_sendable:
            print("\nSendable now:")
            for cid, name, email, source in sample_sendable:
                print(f"  {cid:>6}  {_short(name, 34):34}  {email:34}  source={source}")

        print("=" * 70)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
