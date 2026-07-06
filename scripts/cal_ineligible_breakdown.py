"""
Diagnose WHY the HOT/WARM buyer pool is contaminated: categorize every
ineligible record by reason and trace which ingestion source created it.
Read-only.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    from app.api.admin_extended import _hot_warm_companies
    from app.database import SessionLocal
    from app.services.cal_autonomy import _cal_buyer_eligible

    db = SessionLocal()
    try:
        pool = _hot_warm_companies(db, 300)
        by_reason: Counter = Counter()
        by_source: Counter = Counter()
        reason_source: Counter = Counter()
        samples: dict[str, list[str]] = {}

        for company, _s, _t in pool:
            ok, reason = _cal_buyer_eligible(company)
            if ok:
                continue
            cat = reason.split("(")[0].strip().rstrip(":")
            if "junk/vendor" in reason:
                cat = "vendor/OEM/junk-name"
            elif "domain" in reason:
                cat = "no-real-domain"
            elif "off-ICP" in reason:
                cat = "off-ICP-industry"
            by_reason[cat] += 1
            src = (getattr(company, "source", None) or getattr(company, "discovery_source", None) or "unknown")
            by_source[src] += 1
            reason_source[f"{cat} <- {src}"] += 1
            samples.setdefault(cat, [])
            if len(samples[cat]) < 8:
                ind = getattr(company, "industry", None) or "?"
                samples[cat].append(f"{company.name[:30]} [{ind}] src={src}")

        total = sum(by_reason.values())
        print("=" * 60)
        print(f"INELIGIBLE BREAKDOWN — {total} of {len(pool)} HOT/WARM")
        print("=" * 60)
        print("\nBY REASON:")
        for cat, n in by_reason.most_common():
            print(f"  {n:>4}  {cat}")
        print("\nBY SOURCE:")
        for src, n in by_source.most_common():
            print(f"  {n:>4}  {src}")
        print("\nREASON x SOURCE (top 12):")
        for k, n in reason_source.most_common(12):
            print(f"  {n:>4}  {k}")
        print("\nSAMPLES:")
        for cat, rows in samples.items():
            print(f"  [{cat}]")
            for r in rows:
                print(f"      {r}")
        print("=" * 60)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
