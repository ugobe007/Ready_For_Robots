"""
Clean the Cal outreach queue — quarantine contaminated unsent drafts.

Classifies every unsent-draft CRM account and (with --apply) clears + suppresses
the contaminated ones so autopilot never sends them:

  • vendor/junk   — is_junk(name, "buyer") flags robot OEMs, publications,
                    headline fragments, non-company names.
  • no_real_domain — company has no verifiable website domain, so the send gate
                     can never produce a real recipient (dead-weight draft).
  • off_icp        — industry is a non-automation buyer class (aviation, hotels,
                     casinos, restaurants). Reported; cleaned only with --clean-off-icp.

Read-only by default. Run on Fly:
    fly ssh console -a ready-2-robot -C "sh -c 'cd /code && python scripts/clean_cal_queue.py'"
    fly ssh console -a ready-2-robot -C "sh -c 'cd /code && python scripts/clean_cal_queue.py --apply'"
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_OFF_ICP_TOKENS = (
    "airline", "aviation", "airport", "hotel", "resort", "casino", "hospitality",
    "restaurant", "quick service", "food service", "media", "publishing", "bank", "finance",
)


def _off_icp(industry: str | None, name: str | None) -> bool:
    blob = f"{(industry or '').lower()} {(name or '').lower()}"
    return any(tok in blob for tok in _OFF_ICP_TOKENS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean the Cal outreach queue.")
    parser.add_argument("--apply", action="store_true", help="Persist changes (default dry-run).")
    parser.add_argument("--clean-off-icp", action="store_true", help="Also clean off-ICP industry buyers.")
    parser.add_argument("--clean-no-domain", action="store_true", help="Also clean accounts with no verifiable domain.")
    args = parser.parse_args()

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.services.lead_filter import is_junk
    from app.services.lead_enrichment import company_website_domain

    db = SessionLocal()
    try:
        accts = (
            db.query(CrmAccount)
            .filter(CrmAccount.outreach_draft.isnot(None), CrmAccount.outreach_sent_at.is_(None))
            .all()
        )
        companies = {
            c.id: c
            for c in db.query(Company).filter(
                Company.id.in_([a.company_id for a in accts if a.company_id])
            ).all()
        }

        buckets: dict[str, list[tuple[str, str]]] = {"vendor_junk": [], "no_real_domain": [], "off_icp": [], "keep": []}
        reason_mix: Counter = Counter()

        for a in accts:
            c = companies.get(a.company_id) if a.company_id else None
            name = (c.name if c else None) or a.name or "(no name)"
            industry = c.industry if c else getattr(a, "industry", None)
            junk, jreason = is_junk(name, "buyer")
            domain = company_website_domain(c, a) if c else None
            if junk:
                buckets["vendor_junk"].append((name, jreason))
                reason_mix[jreason] += 1
            elif not domain:
                buckets["no_real_domain"].append((name, "no verifiable website domain"))
            elif _off_icp(industry, name):
                buckets["off_icp"].append((name, industry or "?"))
            else:
                buckets["keep"].append((name, industry or "?"))

        def _clean(a: CrmAccount) -> None:
            a.outreach_draft = None
            a.outreach_stage = "suppressed_junk"

        # Decide which buckets to clean
        clean_ids: set = set()
        for a in accts:
            c = companies.get(a.company_id) if a.company_id else None
            name = (c.name if c else None) or a.name or ""
            junk, _ = is_junk(name, "buyer")
            domain = company_website_domain(c, a) if c else None
            industry = c.industry if c else getattr(a, "industry", None)
            if junk:
                clean_ids.add(a.id)
            elif args.clean_no_domain and not domain:
                clean_ids.add(a.id)
            elif args.clean_off_icp and _off_icp(industry, name):
                clean_ids.add(a.id)

        print("=" * 66)
        print(f"CAL QUEUE CLEAN {'(APPLY)' if args.apply else '(dry-run)'} — {len(accts)} unsent drafts")
        print("=" * 66)
        for bucket, rows in buckets.items():
            print(f"\n[{bucket}] {len(rows)}")
            for name, note in rows[:40]:
                print(f"    {name[:38]:38}  {note}")
        if reason_mix:
            print("\nvendor_junk reasons:")
            for r, n in reason_mix.most_common():
                print(f"    {n:>3}  {r}")

        print(f"\nWould clean: {len(clean_ids)} accounts "
              f"(vendor_junk always; off_icp={args.clean_off_icp}; no_domain={args.clean_no_domain})")

        if args.apply and clean_ids:
            n = 0
            for a in accts:
                if a.id in clean_ids:
                    _clean(a)
                    n += 1
            db.commit()
            print(f"APPLIED: cleared + suppressed {n} contaminated drafts.")
        elif not args.apply:
            print("Dry-run — no changes written. Re-run with --apply.")
        print("=" * 66)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
