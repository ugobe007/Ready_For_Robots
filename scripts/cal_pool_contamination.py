"""
North-star audit: what contamination is in the HOT/WARM buyer pool that
classify_lead currently lets through? Buckets each surfaced lead by the reason
it should NOT be there. Read-only.
"""
from __future__ import annotations

import re
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

_GENERIC_NAME_RE = re.compile(
    r"(?i)^(the\s+)?([a-z]+\s+)?(logistics|tech|technology|manufacturing|warehouse|"
    r"hotel|casino|robotics|automation|ai|software|startup|firm)\s+"
    r"(company|firm|startup|business|corp|group)\.?$"
)


def main() -> int:
    from app.api.admin_extended import _hot_warm_companies
    from app.database import SessionLocal
    from app.services.lead_enrichment import company_website_domain
    from app.services.lead_filter import is_headline_fragment
    from app.services.robot_vendor_names import is_known_robotics_vendor_name
    from app.services.company_name_validation import reject_as_non_company_name

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
            if is_known_robotics_vendor_name(name):
                add("robot vendor/OEM", f"{name}"); hit = True
            if is_headline_fragment(name)[0]:
                add("headline fragment", f"{name}"); hit = True
            if _GENERIC_NAME_RE.match(name):
                add("generic descriptor name", f"{name}"); hit = True
            if reject_as_non_company_name(name)[0]:
                add("non-company name (validator)", f"{name}"); hit = True
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
