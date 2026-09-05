#!/usr/bin/env python3
"""
Reclassify stored industry when keyword inference disagrees with companies.industry.

Targets HOT/WARM scored leads and common mislabels (hospitality → Healthcare, etc.).

Usage:
  python scripts/reclassify_mislabeled_leads.py              # dry-run
  python scripts/reclassify_mislabeled_leads.py --apply
  python scripts/reclassify_mislabeled_leads.py --apply --tier HOT
"""
from __future__ import annotations

import argparse
import re
import sys
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
from app.services.lead_filter import is_junk, pick_primary_score, priority_tier
from app.services.industry_inference import (
    KNOWN_COMPANY_INDUSTRY,
    infer_industry_from_text,
    infer_industry_scores,
    should_skip_industry_reinfer_for_company_name,
)

_HOSPITALITY_FIX_FROM = frozenset({"Healthcare", "Medical Technology", "Logistics", "Automotive & Manufacturing"})
_HOSPITALITY_FIX_TO = frozenset({"Hospitality", "Casinos & Gaming", "Food Service", "Cruise Lines"})
_HOSPITALITY_NAME_RE = re.compile(
    r"(?i)\b(casino|resort|gaming|hotel|hospitality|entertainment|cruise|voyages|sands|wynn|mgm|caesars|boyd|penn)\b"
)


def _blob(c: Company) -> str:
    parts = [c.name or ""]
    for s in c.signals or []:
        if s.signal_text:
            parts.append(s.signal_text)
    return " ".join(parts)


def _known_override(name: str) -> str | None:
    low = (name or "").lower()
    for key in sorted(KNOWN_COMPANY_INDUSTRY.keys(), key=len, reverse=True):
        if key in low:
            return KNOWN_COMPANY_INDUSTRY[key]
    return None


def _confident_inference(blob: str, inferred: str) -> bool:
    scores = infer_industry_scores(blob)
    if not scores or inferred not in scores:
        return False
    top = max(scores.values())
    if top >= 10**5:
        return True
    second = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
    return top >= 3 and top >= second * 2


def _should_reclassify(c: Company, blob: str, stored: str, inferred: str) -> bool:
    if len((c.name or "").strip()) < 6:
        return False
    if inferred == "Automotive & Manufacturing" and stored in {
        "Food Service", "Hospitality", "Casinos & Gaming", "Cruise Lines", "Retail",
    }:
        return False
    known = _known_override(c.name or "")
    if known:
        return known != stored
    if stored in _HOSPITALITY_FIX_FROM and inferred in _HOSPITALITY_FIX_TO:
        if _HOSPITALITY_NAME_RE.search(c.name or ""):
            return True
    if stored == "Automotive & Manufacturing" and inferred == "Food Service":
        if re.search(r"(?i)\b(gourmet|sky chefs|hmshost|catering|aramark|sodexo|compass)\b", c.name or blob):
            return True
    if inferred == "Datacenters" and re.search(
        r"(?i)\b(amazon|walmart|target|home depot|uber|costco|mcdonald)\b", c.name or ""
    ):
        return False
    if stored == "Logistics" and inferred == "Datacenters":
        if re.search(r"(?i)\b(datacenter|data center|hyperscale|colocation)\b", blob):
            return _confident_inference(blob, inferred)
    return _confident_inference(blob, inferred)


def _tier(c: Company) -> str:
    ps = pick_primary_score(c.scores)
    score = float(ps.overall_intent_score if ps else 0)
    sig_types = [s.signal_type for s in (c.signals or []) if s.signal_type]
    return priority_tier(score, c.industry, sig_types, len(c.signals or []), c.employee_estimate).tier


def main() -> None:
    ap = argparse.ArgumentParser(description="Reclassify mislabeled lead industries")
    ap.add_argument("--apply", action="store_true", help="Persist changes (default dry-run)")
    ap.add_argument("--tier", choices=("HOT", "WARM", "ALL"), default="ALL")
    ap.add_argument("--limit", type=int, default=0, help="Max rows to update (0 = no limit)")
    args = ap.parse_args()

    db = SessionLocal()
    updated = 0
    by_industry: dict[str, int] = {}
    try:
        companies = (
            db.query(Company)
            .options(joinedload(Company.signals), joinedload(Company.scores))
            .all()
        )
        for c in companies:
            if is_junk(c.name or "")[0]:
                continue
            if should_skip_industry_reinfer_for_company_name(c.name):
                continue
            t = _tier(c)
            if args.tier != "ALL" and t != args.tier:
                continue
            blob = _blob(c)
            known = _known_override(c.name or "")
            inferred = known or infer_industry_from_text(blob)
            if inferred == "Unknown":
                continue
            stored = (c.industry or "").strip()
            if stored == inferred:
                continue
            if not _should_reclassify(c, blob, stored, inferred):
                continue
            updated += 1
            if updated <= 40:
                tag = "" if args.apply else "[dry-run] "
                print(f"  {tag}{c.name[:45]!r}: {stored or '(empty)'} → {inferred} ({t})")
            elif updated == 41:
                print("  … (further lines suppressed)")
            by_industry[inferred] = by_industry.get(inferred, 0) + 1
            if args.apply:
                c.industry = inferred
            if args.limit and updated >= args.limit:
                break
        if args.apply and updated:
            db.commit()
        print(f"\n{'Updated' if args.apply else 'Would update'}: {updated} companies")
        if by_industry:
            for ind, n in sorted(by_industry.items(), key=lambda x: -x[1]):
                print(f"  → {ind}: {n}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
