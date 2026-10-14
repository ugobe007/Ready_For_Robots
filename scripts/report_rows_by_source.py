#!/usr/bin/env python3
"""Row counts in companies, signals and robot_jobs by source feed. Read-only.

The transaction is opened READ ONLY, so the database rejects any write.
Source per row:
  companies   companies.source (URL host, or the raw label when it is not a URL)
  signals     signals.source_url host
  robot_jobs  host of the earliest job_evidence.source_url, else apply_url host

Hosts map to the feed kinds in app/services/job_posting_ingest_pause.py.

    python3 scripts/report_rows_by_source.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.job_posting_ingest_pause import FEED_CLASSIFICATION  # noqa: E402
from scripts.harness_env import load_harness_env  # noqa: E402

HOST_TO_KIND = (
    ("indeed.com", "job_board"),
    ("simplyhired.com", "job_board"),
    ("amazon.jobs", "amazon_jobs"),
    ("greenhouse.io", "greenhouse"),
    ("lever.co", "lever"),
    ("ashbyhq.com", "ashby"),
    ("smartrecruiters.com", "smartrecruiters"),
    ("myworkdayjobs.com", "workday"),
    ("adzuna.", "adzuna"),
    ("jooble.org", "jooble"),
    ("usajobs.gov", "usajobs"),
    ("sam.gov", "sam_gov"),
)

HOST_SQL = "lower(substring({col} from '^[a-zA-Z]+://([^/?#]+)'))"

QUERIES = {
    "companies": f"""
        SELECT COALESCE({HOST_SQL.format(col='c.source')}, NULLIF(TRIM(c.source), ''), '(none)') AS src,
               COUNT(*) AS n
        FROM companies c GROUP BY 1
    """,
    "signals": f"""
        SELECT COALESCE({HOST_SQL.format(col='s.source_url')}, '(none)') AS src, s.signal_type, COUNT(*) AS n
        FROM signals s GROUP BY 1, 2
    """,
    "robot_jobs": f"""
        SELECT COALESCE({HOST_SQL.format(col='ev.source_url')}, {HOST_SQL.format(col='rj.apply_url')}, '(none)') AS src,
               COUNT(*) AS n
        FROM robot_jobs rj
        LEFT JOIN LATERAL (
            SELECT e.source_url FROM job_evidence e
            WHERE e.robot_job_id = rj.id AND e.source_url IS NOT NULL
            ORDER BY e.created_at ASC LIMIT 1
        ) ev ON TRUE
        GROUP BY 1
    """,
}


def feed_kind(src: str) -> str:
    for needle, kind in HOST_TO_KIND:
        if needle in src:
            return kind
    return "other"


def classification(kind: str) -> str:
    return FEED_CLASSIFICATION.get(kind, "not a posting feed") if kind != "other" else "not a posting feed"


def collect(conn) -> dict:
    from sqlalchemy import text

    conn.execute(text("SET TRANSACTION READ ONLY"))
    out: dict = {}
    for table, sql in QUERIES.items():
        by_kind: dict[str, int] = defaultdict(int)
        by_class: dict[str, int] = defaultdict(int)
        other_hosts: dict[str, int] = defaultdict(int)
        signal_types: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        total = 0
        for row in conn.execute(text(sql)).mappings():
            src = row["src"].removeprefix("www.")
            kind = feed_kind(src)
            n = int(row["n"])
            total += n
            by_kind[kind] += n
            by_class[classification(kind)] += n
            if kind == "other":
                other_hosts[src] += n
            if table == "signals":
                signal_types[kind][row["signal_type"]] += n
        out[table] = {
            "total": total,
            "by_classification": dict(by_class),
            "by_feed": dict(sorted(by_kind.items(), key=lambda kv: -kv[1])),
            "top_other_sources": dict(sorted(other_hosts.items(), key=lambda kv: -kv[1])[:15]),
        }
        if table == "signals":
            out[table]["signal_types_by_feed"] = {k: dict(v) for k, v in signal_types.items()}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    meta = load_harness_env(ROOT)
    if meta.get("status") != "configured":
        print(f"No database: {meta.get('reason')}", file=sys.stderr)
        return 2
    from app.database import engine

    with engine.connect() as conn, conn.begin() as tx:
        report = collect(conn)
        tx.rollback()

    for table, data in report.items():
        print(f"\n{table}: {data['total']:,} rows")
        for cls, n in data["by_classification"].items():
            print(f"  {cls:20s} {n:>8,}")
        print("  by feed:")
        for kind, n in data["by_feed"].items():
            print(f"    {kind:16s} {n:>8,}  ({classification(kind)})")
        if data["top_other_sources"]:
            print("  top other sources: " + ", ".join(f"{k} {v:,}" for k, v in data["top_other_sources"].items()))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
