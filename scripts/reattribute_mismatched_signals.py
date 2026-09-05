#!/usr/bin/env python3
"""
Find signals attached to the wrong company and re-attribute or detach them.

Typical failure mode: a comparison clause ("— Joining GM and Tyson…") was matched
instead of the headline subject ("Nike Axes 775 Warehouse Jobs…").

Default is dry-run (report only):
  python3 scripts/reattribute_mismatched_signals.py

Write CSV audit:
  python3 scripts/reattribute_mismatched_signals.py --report reports/signal_mismatch_audit.csv

Apply fixes (re-attribute when target exists; detach when it does not):
  python3 scripts/reattribute_mismatched_signals.py --apply --yes

Create missing target companies before moving signals:
  python3 scripts/reattribute_mismatched_signals.py --apply --yes --create-missing

Re-score companies touched by --apply:
  python3 scripts/reattribute_mismatched_signals.py --apply --yes --rescore-affected
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.models.score import Score
from app.models.signal import Signal
from app.scrapers.news_scraper import KNOWN_COMPANIES, _headline_lead_clause, extract_company_from_article_text
from app.services.company_validator import is_valid_lead
from app.services.known_brands import is_allowlisted_company_name
from app.services.lead_filter import pick_primary_score
from app.services.scoring_engine import compute_scores

_LEGAL_SUFFIXES = (
    " incorporated",
    " corporation",
    " company",
    " holdings",
    " international",
    " worldwide",
    " group",
    " inc",
    " corp",
    " llc",
    " ltd",
    " plc",
    " co",
    " foods",
)


def _norm_company_name(name: str) -> str:
    s = re.sub(r"[^\w\s&']", " ", (name or "").lower())
    s = re.sub(r"\s+", " ", s).strip()
    for suf in _LEGAL_SUFFIXES:
        if s.endswith(suf):
            s = s[: -len(suf)].strip()
    return s


def _significant_tokens(name: str) -> list[str]:
    stop = {"and", "the", "of", "for", "usa", "us", "uk"}
    tokens = []
    for raw in re.split(r"[\s'&]+", (name or "").lower()):
        tok = re.sub(r"[^\w]", "", raw)
        if len(tok) >= 3 and tok not in stop:
            tokens.append(tok)
    return tokens


def names_match(stored: str, extracted: str) -> bool:
    """True when stored and extracted names refer to the same company."""
    a = _norm_company_name(stored)
    b = _norm_company_name(extracted)
    if not a or not b:
        return False
    if a == b:
        return True
    if a in b or b in a:
        return True
    ta = a.split()
    tb = b.split()
    if ta and tb and ta[0] == tb[0] and (len(ta[0]) >= 4 or is_allowlisted_company_name(stored) or is_allowlisted_company_name(extracted)):
        return True
    return False


def extracted_name_is_trustworthy(name: str, db_lookup: dict) -> bool:
    """Reject headline fragments and generic single words masquerading as companies."""
    stripped = (name or "").strip()
    if not stripped or len(stripped) < 2:
        return False
    if "'" in stripped or "’" in stripped:
        return False
    low = stripped.lower()
    if is_allowlisted_company_name(stripped) or low in KNOWN_COMPANIES:
        return True
    tokens = _significant_tokens(stripped)
    if len(tokens) < 2:
        return False
    if re.search(r"(?i)\b(news|market|facility|modernization|construction|warehouse)\b", stripped):
        return False
    if low in db_lookup:
        return is_valid_lead(stripped, skip_external_checks=True)[0]
    return is_valid_lead(stripped, skip_external_checks=True)[0]


def stored_name_is_credited_in_tail(text: str, stored_name: str) -> bool:
    """True when stored company is the source/byline tail ('… - Tyson Foods')."""
    t = text.strip()
    for sep in (" - ", " – ", " | "):
        if sep not in t:
            continue
        tail = t.rsplit(sep, 1)[-1].strip()
        tail = re.sub(r"<[^>]+>.*", "", tail).strip()
        if _name_in_lead(stored_name, tail[:120]):
            return True
    return False


def _name_in_lead(name: str, lead: str) -> bool:
    low = lead.lower()
    norm = _norm_company_name(name)
    if norm and norm in low:
        return True
    return any(tok in low for tok in _significant_tokens(name))


def mismatch_confidence(stored_name: str, extracted_name: str, text: str) -> str:
    """
    high   — extracted subject in lead clause; stored name absent from lead
    medium — stored name not corroborated in lead clause
    low    — both names appear in lead (ambiguous)
    none   — names match
    """
    if names_match(stored_name, extracted_name):
        return "none"
    lead = _headline_lead_clause(text)
    stored_in_lead = _name_in_lead(stored_name, lead)
    extracted_in_lead = _name_in_lead(extracted_name, lead)
    if extracted_in_lead and not stored_in_lead:
        return "high"
    if not stored_in_lead:
        return "medium"
    if not extracted_in_lead:
        return "medium"
    return "low"


def signal_text_blob(signal: Signal) -> str:
    raw = (signal.ingestion_raw_text or "").strip()
    clean = (signal.signal_text or "").strip()
    return raw if len(raw) > len(clean) else clean


def build_company_lookup(companies: Iterable[Company]) -> dict:
    lookup: dict = {}
    for company in companies:
        if company.name and len(company.name) >= 3:
            key = company.name.lower()
            if key not in lookup:
                lookup[key] = (company.name, company.industry or "Unknown")
    return lookup


def find_company_by_extracted_name(
    db: Session,
    extracted_name: str,
    *,
    cache: dict[str, Optional[Company]],
) -> Optional[Company]:
    key = _norm_company_name(extracted_name)
    if key in cache:
        return cache[key]

    exact = (
        db.query(Company)
        .filter(Company.name.ilike(extracted_name.strip()))
        .order_by(Company.id.asc())
        .first()
    )
    if exact:
        cache[key] = exact
        return exact

    first = extracted_name.split()[0] if extracted_name.split() else extracted_name
    if not first or len(first) < 2:
        cache[key] = None
        return None
    candidates = (
        db.query(Company)
        .filter(Company.name.ilike(f"%{first}%"))
        .order_by(Company.id.asc())
        .limit(80)
        .all()
    )
    for candidate in candidates:
        if names_match(candidate.name, extracted_name):
            cache[key] = candidate
            return candidate
    cache[key] = None
    return None


def duplicate_on_target(db: Session, target_id: int, signal: Signal) -> Optional[Signal]:
    url = (signal.source_url or "").strip()
    if url:
        twin = (
            db.query(Signal)
            .filter(Signal.company_id == target_id, Signal.source_url == url)
            .first()
        )
        if twin:
            return twin
    text = (signal.signal_text or "").strip()
    if text:
        return (
            db.query(Signal)
            .filter(Signal.company_id == target_id, Signal.signal_text == text)
            .first()
        )
    return None


@dataclass
class MismatchRow:
    signal_id: int
    source_company_id: int
    source_company_name: str
    extracted_name: str
    confidence: str
    action: str
    target_company_id: Optional[int]
    target_company_name: Optional[str]
    signal_preview: str
    source_url: str


def scan_mismatches(
    db: Session,
    *,
    limit: int,
    since: Optional[datetime],
    company_id: Optional[int],
    company_name_contains: Optional[str],
    min_confidence: str,
    db_lookup: dict,
) -> list[MismatchRow]:
    conf_rank = {"low": 0, "medium": 1, "high": 2}
    min_rank = conf_rank[min_confidence]

    q = (
        db.query(Signal)
        .join(Company, Signal.company_id == Company.id)
        .options(joinedload(Signal.company))
        .order_by(Signal.id.desc())
    )
    if since:
        q = q.filter(Signal.created_at >= since)
    if company_id:
        q = q.filter(Signal.company_id == company_id)
    if company_name_contains:
        q = q.filter(Company.name.ilike(f"%{company_name_contains.strip()}%"))
    signals = q.limit(limit).all()

    rows: list[MismatchRow] = []
    target_cache: dict[str, Optional[Company]] = {}
    for signal in signals:
        company = signal.company
        if not company:
            continue
        text = signal_text_blob(signal)
        if len(text) < 20:
            continue

        extracted_name, _industry = extract_company_from_article_text(text, db_lookup=db_lookup)
        if not extracted_name:
            continue
        if not extracted_name_is_trustworthy(extracted_name, db_lookup):
            continue
        if stored_name_is_credited_in_tail(text, company.name):
            continue

        confidence = mismatch_confidence(company.name, extracted_name, text)
        if confidence == "none" or conf_rank.get(confidence, -1) < min_rank:
            continue

        target = find_company_by_extracted_name(db, extracted_name, cache=target_cache)
        if target and target.id == company.id:
            continue

        if target:
            action = "reattribute"
            target_id = target.id
            target_name = target.name
        else:
            action = "create_reattribute"
            target_id = None
            target_name = extracted_name

        rows.append(
            MismatchRow(
                signal_id=signal.id,
                source_company_id=company.id,
                source_company_name=company.name,
                extracted_name=extracted_name,
                confidence=confidence,
                action=action,
                target_company_id=target_id,
                target_company_name=target_name,
                signal_preview=text[:140],
                source_url=(signal.source_url or "")[:200],
            )
        )
    return rows


def write_report(path: Path, rows: list[MismatchRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "signal_id",
                "source_company_id",
                "source_company_name",
                "extracted_name",
                "confidence",
                "action",
                "target_company_id",
                "target_company_name",
                "source_url",
                "signal_preview",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.signal_id,
                    row.source_company_id,
                    row.source_company_name,
                    row.extracted_name,
                    row.confidence,
                    row.action,
                    row.target_company_id or "",
                    row.target_company_name or "",
                    row.source_url,
                    row.signal_preview,
                ]
            )


def rescore_companies(db: Session, company_ids: set[int]) -> int:
    updated = 0
    for cid in sorted(company_ids):
        company = db.query(Company).filter(Company.id == cid).first()
        if not company:
            continue
        signals = db.query(Signal).filter(Signal.company_id == cid).all()
        if not signals:
            score_row = db.query(Score).filter(Score.company_id == cid).first()
            if score_row:
                db.delete(score_row)
                updated += 1
            continue
        scores = compute_scores(company, signals)
        score_row = pick_primary_score(db.query(Score).filter(Score.company_id == cid).all())
        if score_row:
            score_row.automation_score = scores["automation_score"]
            score_row.labor_pain_score = scores["labor_pain_score"]
            score_row.expansion_score = scores["expansion_score"]
            score_row.robotics_fit_score = scores["robotics_fit_score"]
            score_row.overall_intent_score = scores["overall_intent_score"]
            score_row.last_calculated_at = datetime.now(timezone.utc)
        else:
            db.add(
                Score(
                    company_id=cid,
                    **scores,
                    last_calculated_at=datetime.now(timezone.utc),
                )
            )
        updated += 1
    return updated


def apply_fixes(
    db: Session,
    rows: list[MismatchRow],
    *,
    create_missing: bool,
    detach_unresolved: bool,
) -> tuple[dict[str, int], set[int]]:
    stats = {
        "reattributed": 0,
        "created_and_reattributed": 0,
        "detached_duplicate": 0,
        "detached": 0,
        "skipped": 0,
    }
    touched_company_ids: set[int] = set()

    for row in rows:
        signal = db.query(Signal).filter(Signal.id == row.signal_id).first()
        if not signal:
            stats["skipped"] += 1
            continue
        if signal.company_id != row.source_company_id:
            stats["skipped"] += 1
            continue

        touched_company_ids.add(row.source_company_id)
        target: Optional[Company] = None
        created_new = False
        if row.target_company_id:
            target = db.query(Company).filter(Company.id == row.target_company_id).first()
        elif create_missing and row.target_company_name:
            target = Company(
                name=row.target_company_name,
                industry="Unknown",
                source="signal_reattribution",
            )
            db.add(target)
            db.flush()
            created_new = True

        if not target:
            if detach_unresolved:
                db.delete(signal)
                stats["detached"] += 1
            else:
                stats["skipped"] += 1
            continue

        touched_company_ids.add(target.id)
        twin = duplicate_on_target(db, target.id, signal)
        if twin and twin.id != signal.id:
            db.delete(signal)
            stats["detached_duplicate"] += 1
            continue

        signal.company_id = target.id
        if created_new:
            stats["created_and_reattributed"] += 1
        else:
            stats["reattributed"] += 1

    db.commit()
    return stats, touched_company_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=5000, help="Max signals to scan (newest first)")
    parser.add_argument("--since-days", type=int, default=0, help="Only scan signals from the last N days")
    parser.add_argument("--company-id", type=int, default=0, help="Limit scan to one source company id")
    parser.add_argument(
        "--company-name-contains",
        type=str,
        default="",
        help="Limit scan to source companies whose name contains this substring (e.g. Tyson)",
    )
    parser.add_argument(
        "--min-confidence",
        choices=("medium", "high"),
        default="medium",
        help="Minimum mismatch confidence to include (default: medium)",
    )
    parser.add_argument("--report", type=str, default="", help="Optional CSV report path")
    parser.add_argument("--apply", action="store_true", help="Write changes to the database")
    parser.add_argument("--yes", action="store_true", help="Required with --apply to confirm writes")
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="Create a company row when the extracted target does not exist",
    )
    parser.add_argument(
        "--detach-unresolved",
        action="store_true",
        help="Delete misplaced signals when no target company exists and --create-missing is off",
    )
    parser.add_argument(
        "--rescore-affected",
        action="store_true",
        help="Re-score source and target companies after --apply",
    )
    args = parser.parse_args()

    since = None
    if args.since_days > 0:
        since = datetime.now(timezone.utc) - timedelta(days=args.since_days)

    db = SessionLocal()
    try:
        name_rows = db.query(Company.name, Company.industry).all()
        db_lookup = build_company_lookup(
            Company(name=name, industry=industry) for name, industry in name_rows if name
        )

        rows = scan_mismatches(
            db,
            limit=args.limit,
            since=since,
            company_id=args.company_id or None,
            company_name_contains=args.company_name_contains or None,
            min_confidence=args.min_confidence,
            db_lookup=db_lookup,
        )

        print(f"Scanned up to {args.limit} signals")
        print(f"Mismatches found: {len(rows)} (min_confidence={args.min_confidence})")
        by_conf = {}
        by_action = {}
        for row in rows:
            by_conf[row.confidence] = by_conf.get(row.confidence, 0) + 1
            by_action[row.action] = by_action.get(row.action, 0) + 1
        if by_conf:
            print("By confidence:", ", ".join(f"{k}={v}" for k, v in sorted(by_conf.items())))
        if by_action:
            print("Proposed actions:", ", ".join(f"{k}={v}" for k, v in sorted(by_action.items())))

        for row in rows[:40]:
            print(
                f"\n  signal={row.signal_id}  {row.confidence:<6}  {row.action}"
                f"\n    from: {row.source_company_name} (id={row.source_company_id})"
                f"\n    to:   {row.target_company_name or '—'} (id={row.target_company_id or '—'})"
                f"\n    text: {row.signal_preview!r}"
            )
        if len(rows) > 40:
            print(f"\n… {len(rows) - 40} more rows (use --report for full list)")

        if args.report:
            write_report(Path(args.report), rows)
            print(f"\nWrote report: {args.report}")

        if not args.apply:
            print("\nDry run only. Re-run with --apply --yes to write changes.")
            return
        if not args.yes:
            print("\nRefusing to write without --yes.")
            return
        if not rows:
            print("\nNothing to apply.")
            return

        stats, touched = apply_fixes(
            db,
            rows,
            create_missing=args.create_missing,
            detach_unresolved=args.detach_unresolved,
        )
        print("\nApply results:", stats)
        if args.rescore_affected and touched:
            rescored = rescore_companies(db, touched)
            db.commit()
            print(f"Re-scored {rescored} companies")
    finally:
        db.close()


if __name__ == "__main__":
    main()
