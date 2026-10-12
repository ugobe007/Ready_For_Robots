#!/usr/bin/env python3
"""Rebuild robot_jobs after the 2026-10-11 purge.

The purge (scripts/clean_human_labor_from_robot_jobs.py) deleted rows from
``robot_jobs`` (and, by cascade, ``job_evidence`` / ``robot_job_matches``).
It did NOT touch ``signals`` or ``companies``. Every scraped Robot Job also wrote
a signal row:

    signal_type = 'robot_job'
    signal_text = 'ROBOT TASK SIGNAL | {title} | {function} | {pay} | {specs} | {status} | {employer}'
                  (older rows: 'ROBOT_JOB | ...')
    company_id, source_url, created_at

NOTE (2026-10-11, Bob): we sell to companies ready to buy or pilot robots,
not labor postings. ``from-signals`` therefore restores only postings with
automation intent; plain labor postings stay where they are (signals) and feed
company ranking:  python3 scripts/rank_buyers.py

So there are two recovery paths. Both are DRY-RUN unless you pass --apply,
and both are idempotent (upsert on job_key — safe to re-run, safe to run both).

  # 0. What survived?
  python3 scripts/rebuild_robot_jobs.py count

  # 1. Best fidelity: copy job tables from a restored Supabase backup.
  #    Restore the pre-purge backup into a NEW project (or a branch), then:
  python3 scripts/rebuild_robot_jobs.py from-backup --source-url "postgresql://...restored..."
  python3 scripts/rebuild_robot_jobs.py from-backup --source-url "postgresql://..." --apply

  # 2. No backup? Rebuild from surviving signals.
  python3 scripts/rebuild_robot_jobs.py from-signals
  python3 scripts/rebuild_robot_jobs.py from-signals --apply

Path 2 recovers employer, title, location, pay, specs, status, source URL and the
original timestamp. It cannot recover full job descriptions (they were never on
the signal) — the next scrape of the same posting fills them on the same job_key.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SIGNAL_PREFIXES = ("ROBOT TASK SIGNAL", "ROBOT_JOB", "ROBOT JOB")
_PAY_RANGE = re.compile(r"\$([\d.,]+)\s*[–-]\s*\$?([\d.,]+)\s*/\s*(\w+)")
_PAY_ONE = re.compile(r"\$([\d.,]+)\s*/\s*(\w+)")
_THROUGHPUT = re.compile(r"(\d+(?:\.\d+)?)\s+([a-z ]+?)/(\w+)")
_PAYLOAD = re.compile(r"(\d+(?:\.\d+)?)\s*(lb|lbs|kg)\b", re.I)


def _money(raw: str) -> Optional[float]:
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def parse_signal_text(text: str) -> Optional[dict[str, Any]]:
    """Inverse of robot_job_extract.format_robot_job_signal."""
    if not text:
        return None
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 2 or not any(parts[0].upper().startswith(p) for p in SIGNAL_PREFIXES):
        return None
    parts += [""] * (7 - len(parts))
    _, title, function, pay, specs, status, employer = parts[:7]
    if not title or title.lower() == "untitled work":
        return None
    comp: dict[str, Any] = {"wage_min": None, "wage_max": None, "wage_unit": None,
                            "currency": None, "signing_bonus": None, "excerpt": None}
    m = _PAY_RANGE.search(pay) or None
    if m:
        comp.update(wage_min=_money(m.group(1)), wage_max=_money(m.group(2)), wage_unit=m.group(3),
                    currency="USD", excerpt=pay)
    else:
        m = _PAY_ONE.search(pay)
        if m:
            v = _money(m.group(1))
            comp.update(wage_min=v, wage_max=v, wage_unit=m.group(2), currency="USD", excerpt=pay)
    perf: dict[str, Any] = {"throughput": None, "payload": None, "shift": None}
    if specs and specs != "specs unknown":
        for bit in (b.strip() for b in specs.split(",")):
            t = _THROUGHPUT.fullmatch(bit)
            p = _PAYLOAD.fullmatch(bit)
            if t:
                perf["throughput"] = {"count": float(t.group(1)), "unit": t.group(2).strip(), "per": t.group(3)}
            elif p:
                perf["payload"] = {"value": float(p.group(1)), "unit": p.group(2).lower()}
            elif bit:
                perf["shift"] = bit
    fn = (function or "").strip().lower().replace(" ", "_")
    return {
        "job_title": title,
        "job_function": None if fn in ("", "operational_task") else fn,
        "compensation": comp,
        "performance_specs": perf,
        "status": (status or "open").strip() or "open",
        "employer": None if employer in ("", "Hiring Employer") else employer,
    }


def _session():
    from app.database import SessionLocal

    return SessionLocal()


def cmd_count(_args) -> int:
    from sqlalchemy import text

    db = _session()
    try:
        q = {
            "robot_jobs": "select count(*) from robot_jobs",
            "job_evidence": "select count(*) from job_evidence",
            "signals (robot_job)": "select count(*) from signals where signal_type = 'robot_job'",
            "signals (robot text)": "select count(*) from signals where signal_text like 'ROBOT TASK SIGNAL |%' "
                                    "or signal_text like 'ROBOT_JOB |%'",
            "companies": "select count(*) from companies",
        }
        for label, sql in q.items():
            try:
                print(f"{label:24} {db.execute(text(sql)).scalar():>8,}")
            except Exception as exc:  # table may not exist
                db.rollback()
                print(f"{label:24}   n/a ({exc.__class__.__name__})")
        try:
            if db.execute(text("select to_regclass('public.rfr_deleted_rows')")).scalar():
                n = db.execute(text("select count(*) from rfr_deleted_rows where table_name = 'robot_jobs' "
                                    "and restored_at is null")).scalar()
                print(f"{'archived robot_jobs':24} {n:>8,}  (restore with: from-archive --apply)")
        except Exception:
            db.rollback()
    finally:
        db.close()
    return 0


def cmd_from_signals(args) -> int:
    from sqlalchemy import or_

    from app.models.company import Company
    from app.models.signal import Signal
    from app.services.robot_job_extract import extract_robot_job
    from app.services.robot_job_lifecycle import robot_job_key, upsert_robot_job_from_extract
    from app.models.robot_directed_discovery import RobotJob

    db = _session()
    stats: Counter = Counter()
    seen_keys: set[str] = set()
    samples: list[str] = []
    try:
        q = (
            db.query(Signal, Company)
            .outerjoin(Company, Company.id == Signal.company_id)
            .filter(
                or_(
                    Signal.signal_type == "robot_job",
                    Signal.signal_text.like("ROBOT TASK SIGNAL |%"),
                    Signal.signal_text.like("ROBOT_JOB |%"),
                )
            )
            .order_by(Signal.created_at.asc())
        )
        total = q.count()
        print(f"signals to read: {total:,}")
        for i, (sig, company) in enumerate(q.yield_per(1000), 1):
            parsed = parse_signal_text(sig.signal_text or "")
            if not parsed:
                stats["unparseable"] += 1
                continue
            employer = (getattr(company, "name", None) or parsed["employer"] or "").strip()
            if not employer:
                stats["no_employer"] += 1
                continue
            city = (getattr(company, "location_city", None) or "").strip()
            state = (getattr(company, "location_state", None) or "").strip()
            locality = ", ".join(p for p in (city, state) if p)
            extract = extract_robot_job(
                title=parsed["job_title"],
                description="",
                company=employer,
                locality=locality,
                source_url=sig.source_url or "",
            )
            if not extract.get("persistable"):
                stats["gate_rejected"] += 1
                continue
            if extract.get("opportunity_tier") != 1:
                # Labor postings stay as company signals (pain evidence for
                # scripts/rank_buyers.py). Only buyer intent becomes a robot_job.
                stats["labor_posting_kept_as_signal" if extract.get("opportunity_tier") else "not_an_opportunity"] += 1
                continue
            # Signal text is the evidence we have; prefer it over a blank re-extract.
            if parsed["compensation"]["wage_min"] is not None:
                extract["compensation"] = parsed["compensation"]
            for k, v in parsed["performance_specs"].items():
                if v and not (extract.get("performance_specs") or {}).get(k):
                    extract.setdefault("performance_specs", {})[k] = v
            extract["job_function"] = extract.get("job_function") or parsed["job_function"]
            extract["status"] = parsed["status"]
            key = robot_job_key(employer, parsed["job_title"], locality)
            if key in seen_keys:
                stats["duplicate_in_signals"] += 1
                continue
            seen_keys.add(key)
            exists = db.query(RobotJob.id).filter(RobotJob.job_key == key).first() is not None
            stats["already_present" if exists else "rebuildable"] += 1
            stats[f"tier_{extract.get('opportunity_tier')}"] += 1
            if len(samples) < 12 and not exists:
                samples.append(f"  {employer[:34]:34} | {parsed['job_title'][:44]:44} | {locality[:20]:20} | tier {extract.get('opportunity_tier')}")
            if not args.apply or exists:
                continue
            row = upsert_robot_job_from_extract(db, company_id=getattr(company, "id", None), extract=extract,
                                                source_url=sig.source_url)
            if row is None:
                stats["upsert_none"] += 1
                continue
            prov = dict(row.provenance or {})
            prov.update({"rebuilt_from": "signals", "signal_id": sig.id,
                         "signal_created_at": sig.created_at.isoformat() if sig.created_at else None})
            row.provenance = prov
            row.source_run = "rebuild_2026_10_11"
            if sig.created_at is not None:
                row.created_at = sig.created_at
            stats["written"] += 1
            if stats["written"] % 500 == 0:
                db.commit()
                print(f"  …{stats['written']:,} written ({i:,}/{total:,} read)")
        if args.apply:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print("\nsample of jobs that would be rebuilt:" if not args.apply else "\nsample:")
    print("\n".join(samples) or "  (none)")
    print("\nresult:")
    for k, v in sorted(stats.items()):
        print(f"  {k:22} {v:>8,}")
    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply.")
    return 0


# Tables copied from a restored backup, in FK order, with their conflict key.
BACKUP_TABLES = (
    ("work_claims", "claim_key"),
    ("robot_jobs", "job_key"),
    ("job_evidence", "id"),
    ("robot_job_matches", "id"),
)


def cmd_from_backup(args) -> int:
    from sqlalchemy import MetaData, create_engine, select, text
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.database import engine as target_engine

    url = args.source_url.strip()
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg2://" + url[len(prefix):]
    src = create_engine(url, pool_pre_ping=True)
    smeta, tmeta = MetaData(), MetaData()
    names = [t for t, _ in BACKUP_TABLES]
    smeta.reflect(bind=src, only=lambda n, _m: n in names)
    tmeta.reflect(bind=target_engine, only=lambda n, _m: n in names + ["companies", "robot_capability_profiles"])

    with target_engine.connect() as tc:
        company_ids = {r[0] for r in tc.execute(text("select id from companies"))}
        try:
            profile_ids = {r[0] for r in tc.execute(text("select id from robot_capability_profiles"))}
        except Exception:
            profile_ids = set()

    written: Counter = Counter()
    with src.connect() as sc, target_engine.connect() as tc:
        job_ids: set = set()
        claim_ids: set = {r[0] for r in tc.execute(text("select id from work_claims"))} if "work_claims" in tmeta.tables else set()
        for table, conflict in BACKUP_TABLES:
            if table not in smeta.tables or table not in tmeta.tables:
                print(f"skip {table}: missing on {'source' if table not in smeta.tables else 'target'}")
                continue
            s_tab, t_tab = smeta.tables[table], tmeta.tables[table]
            cols = [c.name for c in t_tab.columns if c.name in s_tab.columns]
            rows = [dict(r._mapping) for r in sc.execute(select(*[s_tab.c[c] for c in cols]))]
            keep = []
            for r in rows:
                if "company_id" in r and r["company_id"] not in company_ids:
                    r["company_id"] = None
                if table == "robot_jobs":
                    if r.get("work_claim_id") not in claim_ids:
                        r["work_claim_id"] = None
                    if r.get("discovery_profile_id") not in profile_ids:
                        r["discovery_profile_id"] = None
                    job_ids.add(r["id"])
                if table == "job_evidence":
                    if r.get("robot_job_id") and r["robot_job_id"] not in job_ids:
                        continue
                    if r.get("work_claim_id") and r["work_claim_id"] not in claim_ids:
                        r["work_claim_id"] = None
                if table == "robot_job_matches":
                    if r["robot_job_id"] not in job_ids or r["profile_id"] not in profile_ids:
                        continue
                if table == "work_claims":
                    claim_ids.add(r["id"])
                keep.append(r)
            print(f"{table:20} source rows {len(rows):>7,}  eligible {len(keep):>7,}")
            if not args.apply or not keep:
                continue
            for i in range(0, len(keep), 500):
                stmt = pg_insert(t_tab).values(keep[i:i + 500]).on_conflict_do_nothing(index_elements=[conflict])
                written[table] += tc.execute(stmt).rowcount or 0
        if args.apply:
            tc.commit()
        else:
            print("\nDRY RUN — nothing written. Re-run with --apply.")
            tc.rollback()
    for t, n in written.items():
        print(f"inserted {t:20} {n:>7,}")
    return 0


def cmd_from_archive(args) -> int:
    """Restore rows captured by the robot_jobs_deleted archive trigger."""
    from sqlalchemy import text

    from app.database import engine

    with engine.begin() as c:
        n = c.execute(text("select count(*) from rfr_deleted_rows where table_name = 'robot_jobs' "
                           "and restored_at is null")).scalar()
        print(f"archived, not yet restored: {n:,}")
        if not args.apply:
            print("DRY RUN — re-run with --apply.")
            return 0
        restored = c.execute(text("select restore_deleted_robot_jobs()")).scalar()
        print(f"restored: {restored:,}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("count")
    s = sub.add_parser("from-signals")
    s.add_argument("--apply", action="store_true")
    b = sub.add_parser("from-backup")
    b.add_argument("--source-url", default=os.environ.get("BACKUP_DATABASE_URL"), required=False)
    b.add_argument("--apply", action="store_true")
    a = sub.add_parser("from-archive")
    a.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.cmd == "from-backup" and not args.source_url:
        ap.error("--source-url (or BACKUP_DATABASE_URL) is required")
    return {"count": cmd_count, "from-signals": cmd_from_signals,
            "from-backup": cmd_from_backup, "from-archive": cmd_from_archive}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
