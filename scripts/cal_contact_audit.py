"""
How many eligible HOT/WARM buyers already have a VERIFIED contact email
(the runway Cal keeps once the send gate is hardened to verified-source-only)?
Read-only, no provider API calls.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_VERIFIED = {"apollo", "hunter", "hunter_domain", "website_mailto", "signal_email"}


def main() -> int:
    from app.api.admin_extended import _hot_warm_companies
    from app.database import SessionLocal
    from app.models.contact import Contact
    from app.services.cal_autonomy import _cal_buyer_eligible
    from app.services.outreach_email_inference import looks_like_person_email

    db = SessionLocal()
    try:
        pool = _hot_warm_companies(db, 300)
        eligible = 0
        verified_stored = 0
        person_contact = 0
        only_guessable = 0
        src_mix: Counter = Counter()
        need_enrich_samples = []

        for company, _s, _t in pool:
            ok, _r = _cal_buyer_eligible(company)
            if not ok:
                continue
            eligible += 1
            meta = company.crm_metadata or {}
            stored_email = (meta.get("outreach_email") or "").strip().lower()
            stored_src = (meta.get("outreach_email_source") or "").strip().lower()
            has_verified = bool(stored_email) and stored_src in _VERIFIED
            if has_verified:
                verified_stored += 1
                src_mix[stored_src] += 1
                continue
            contacts = db.query(Contact).filter(Contact.company_id == company.id).limit(10).all()
            if any(looks_like_person_email((c.email or "")) for c in contacts if c.email):
                person_contact += 1
                continue
            only_guessable += 1
            if len(need_enrich_samples) < 20:
                need_enrich_samples.append(company.name)

        print("=" * 60)
        print("CAL CONTACT AUDIT — verified coverage of eligible buyers")
        print("=" * 60)
        print(f"  eligible buyers                 {eligible}")
        print(f"  verified stored email           {verified_stored}")
        print(f"  person contact on file          {person_contact}")
        print(f"  only guessable (needs enrich)   {only_guessable}")
        if src_mix:
            print("\n  verified sources:")
            for s, n in src_mix.most_common():
                print(f"    {n:>4}  {s}")
        if need_enrich_samples:
            print("\n  needs enrichment (sample):")
            for n in need_enrich_samples:
                print(f"    {n}")
        print("=" * 60)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
