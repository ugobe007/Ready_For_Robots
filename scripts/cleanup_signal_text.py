#!/usr/bin/env python3
"""
Historical cleanup for ``signals.signal_text`` (scraper / LLM scaffolding, HTML, etc.).

Requires Alembic revision ``c0d1e2f3a4b5`` (column ``signals.ingestion_raw_text``):
  alembic upgrade head

Behavior (``--apply``):
  - For each row with ``ingestion_raw_text`` NULL, copies current ``signal_text`` into
    ``ingestion_raw_text`` (one-time archive of the pre-cleanup body).
  - Sets ``signal_text`` to ``normalize_signal_text_for_storage(ingestion_raw_text)``.
  - Rows already cleaned (normalized canonical raw equals current ``signal_text``) are skipped.
  - Rows that normalize to empty string are skipped (logged).
  - Refreshes ``companies.automation_profile`` once per affected company after each commit batch
    (bulk ``update()`` does not fire ORM profile hooks).

Dry-run (default): counts rows that would change and prints a short sample.

Usage:
  python3 scripts/cleanup_signal_text.py
  python3 scripts/cleanup_signal_text.py --apply
  python3 scripts/cleanup_signal_text.py --apply --since-id 5000
  python3 scripts/cleanup_signal_text.py --apply --limit 2000
  python3 scripts/cleanup_signal_text.py --apply --max-chars 4000

Env: DATABASE_URL (same resolution as ``scripts/cleanup_leads.py``).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_cleanup_dotenv = (os.getenv("DOTENV_PATH") or "").strip()
if _cleanup_dotenv:
    load_dotenv(Path(_cleanup_dotenv).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy import inspect
from sqlalchemy.orm import joinedload

from app.database import SessionLocal, engine
from app.models.company import Company
from app.models.signal import Signal
from app.services.automation_profile import build_automation_profile_dict_from_company
from app.services.lead_signal_display import normalize_signal_text_for_storage


def _signals_has_ingestion_raw(eng) -> bool:
    insp = inspect(eng)
    try:
        cols = {c["name"] for c in insp.get_columns("signals")}
    except Exception:
        return False
    return "ingestion_raw_text" in cols


def _refresh_profiles(session, company_ids: set[int]) -> int:
    n = 0
    for cid in sorted(company_ids):
        c = (
            session.query(Company)
            .options(joinedload(Company.signals))
            .filter(Company.id == cid)
            .first()
        )
        if not c:
            continue
        c.automation_profile = build_automation_profile_dict_from_company(c)
        n += 1
    if n:
        session.commit()
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean historical signals.signal_text")
    parser.add_argument("--apply", action="store_true", help="Write changes (default is dry-run)")
    parser.add_argument("--since-id", type=int, default=0, dest="since_id", metavar="ID")
    parser.add_argument("--limit", type=int, default=0, help="Max rows to scan/change (0 = all)")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=8000,
        dest="max_chars",
        help="Storage cap passed to normalizer",
    )
    args = parser.parse_args()

    if not _signals_has_ingestion_raw(engine):
        print(
            "error: column ``signals.ingestion_raw_text`` is missing. "
            "Apply migration ``c0d1e2f3a4b5`` (``alembic upgrade head``) before running this script.",
            file=sys.stderr,
        )
        return 1

    session = SessionLocal()
    scanned = 0
    try:
        q = session.query(Signal).order_by(Signal.id)
        if args.since_id:
            q = q.filter(Signal.id > args.since_id)
        if args.limit:
            q = q.limit(args.limit)

        would_change = 0
        would_skip_empty = 0
        sample: list[tuple[int, str, str]] = []

        batch_affected: set[int] = set()
        batch_updates = 0
        total_profiles = 0

        def flush_batch():
            nonlocal batch_affected, batch_updates, total_profiles
            if batch_affected and args.apply:
                total_profiles += _refresh_profiles(session, batch_affected)
            batch_affected = set()
            batch_updates = 0

        for sig in q.yield_per(400):
            scanned += 1
            cur_st = sig.signal_text or ""
            ing = sig.ingestion_raw_text
            canonical_raw = (ing if ing is not None else cur_st) or ""

            cleaned = normalize_signal_text_for_storage(
                canonical_raw,
                max_chars=args.max_chars,
            )
            if not cleaned:
                would_skip_empty += 1
                continue

            if cleaned == cur_st:
                continue

            would_change += 1
            if len(sample) < 5:
                sample.append((sig.id, cur_st[:120], cleaned[:120]))

            if args.apply:
                new_ing = ing if ing is not None else cur_st
                session.query(Signal).filter(Signal.id == sig.id).update(
                    {
                        "ingestion_raw_text": new_ing,
                        "signal_text": cleaned,
                    },
                    synchronize_session=False,
                )
                batch_affected.add(sig.company_id)
                batch_updates += 1
                if batch_updates >= 250:
                    session.commit()
                    flush_batch()

        if args.apply and batch_updates:
            session.commit()
            flush_batch()
        elif args.apply:
            session.commit()

        print(f"rows_scanned={scanned} would_change={would_change} empty_normalize={would_skip_empty}")
        if sample:
            print("sample (id | before… | after…):")
            for sid, b, a in sample:
                print(f"  {sid} | {b!r} | {a!r}")
        if args.apply:
            print(f"automation_profile companies refreshed: {total_profiles}")
        else:
            print("dry-run only — pass ``--apply`` to write")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
