#!/usr/bin/env python3
"""
Phase 3 audit: simulate reclassification for Unknown/Other leads and summarize gaps.

Outputs reports/unknown_industry_reclassify_audit.txt with:
  - how many would resolve via effective_industry_for_lead
  - top target industries
  - sample rows still unknown after simulation
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.industry_inference import effective_industry_for_lead

_UNKNOWN = frozenset({"", "unknown", "other", "new"})


def _is_unknown(val: str | None) -> bool:
    return (val or "").strip().lower() in _UNKNOWN


def _strip_html_noise(text: str) -> str:
    t = re.sub(r"<[^>]+>", " ", text or "")
    t = re.sub(r"&nbsp;|&amp;|&lt;|&gt;", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()


def main() -> None:
    db = SessionLocal()
    try:
        companies = (
            db.query(Company)
            .options(joinedload(Company.signals))
            .filter(
                (Company.industry == None)
                | (Company.industry == "")
                | (Company.industry.ilike("unknown"))
                | (Company.industry.ilike("other"))
                | (Company.industry.ilike("new"))
            )
            .all()
        )
    finally:
        db.close()

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    out_path = reports_dir / "unknown_industry_reclassify_audit.txt"

    would_resolve: list[tuple[str, str, str]] = []
    still_unknown: list[tuple[str, str]] = []
    by_industry: Counter[str] = Counter()
    html_noise = 0

    for c in companies:
        sig_blob = " ".join(
            _strip_html_noise(getattr(s, "signal_text", None) or "")
            for s in (c.signals or [])
        )
        if any(
            "<a href" in (getattr(s, "signal_text", "") or "").lower()
            for s in (c.signals or [])
        ):
            html_noise += 1

        inferred = effective_industry_for_lead(c.name, c.industry, c.signals or [])
        if _is_unknown(inferred):
            preview = (c.name or "") + " | " + sig_blob[:220]
            still_unknown.append((c.name or "(no name)", preview))
        else:
            would_resolve.append((c.name or "(no name)", c.industry or "", inferred))
            by_industry[inferred] += 1

    with out_path.open("w") as f:
        f.write(f"# Unknown-industry reclassify simulation ({len(companies)} leads)\n\n")
        f.write(f"Would resolve: {len(would_resolve)}\n")
        f.write(f"Still unknown: {len(still_unknown)}\n")
        f.write(f"Leads with HTML-heavy Google RSS signals: {html_noise}\n\n")
        f.write("## Target industries (simulated)\n")
        for ind, count in by_industry.most_common(40):
            f.write(f"  {count:5d}  {ind}\n")
        f.write("\n## Sample resolvable (first 60)\n")
        for i, (name, old, new) in enumerate(would_resolve[:60], 1):
            f.write(f"{i}. {name} | {old or '∅'} → {new}\n")
        f.write("\n## Still unknown (first 80)\n")
        for i, (name, preview) in enumerate(still_unknown[:80], 1):
            f.write(f"{i}. {name} | {preview}\n")

    print(f"Audit complete: {len(companies)} unknown leads")
    print(f"  Would resolve: {len(would_resolve)}")
    print(f"  Still unknown: {len(still_unknown)}")
    print(f"  HTML-noise leads: {html_noise}")
    print(f"Wrote {out_path}")
    if by_industry:
        print("Top industries:", [i for i, _ in by_industry.most_common(8)])


if __name__ == "__main__":
    main()
