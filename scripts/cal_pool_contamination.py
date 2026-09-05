"""
North-star audit: what contamination is in the HOT/WARM buyer pool that
classify_lead currently lets through? Buckets each surfaced lead by the reason
it should NOT be there. Read-only.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Domains that are media/generic properties, never a real buyer's corporate site.
_MEDIA_JUNK_DOMAINS = {
    "miami.com", "women.com", "dynamic.com", "firm.com", "example.com",
    "news.com", "today.com", "time.com", "forbes.com", "techcrunch.com",
    "medium.com", "wordpress.com", "blogspot.com", "substack.com",
}


def main() -> int:
    from app.api.admin_extended import _hot_warm_companies
    from app.database import SessionLocal
    from app.services.lead_enrichment import company_website_domain
    from app.services.lead_filter import is_junk

    db = SessionLocal()
    try:
        pool = _hot_warm_companies(db, 400)
        total = len(pool)
        buckets: Counter = Counter()
        examples: dict[str, list[str]] = {}
        clean = 0

        def add(bucket: str, name: str) -> None:
            buckets[bucket] += 1
            examples.setdefault(bucket, [])
            if len(examples[bucket]) < 12:
                examples[bucket].append(name)

        for company, _score, tier in pool:
            name = (company.name or "").strip()
            dom = (company_website_domain(company) or "").lower()
            hit = False
            # Authoritative check: anything is_junk flags must NOT be in the pool
            # (regression guard — _hot_warm_companies should have excluded it).
            junk, reason = is_junk(name)
            if junk:
                add(f"is_junk LEAK: {reason[:32]}", name); hit = True
            if dom in _MEDIA_JUNK_DOMAINS:
                add("media/junk domain", f"{name} -> {dom}"); hit = True
            if not dom:
                add("no real website domain", f"{name}"); hit = True
            if not hit:
                clean += 1

        print("=" * 66)
        print(f"HOT/WARM POOL CONTAMINATION — {total} leads")
        print("=" * 66)
        print(f"  clean (no flag)                 {clean}  ({100*clean//max(total,1)}%)")
        for b, n in buckets.most_common():
            print(f"  {n:>4}  {b}")
        print()
        for b, _n in buckets.most_common():
            print(f"[{b}]")
            for ex in examples[b]:
                print(f"    {ex}")
            print()
        print("=" * 66)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
