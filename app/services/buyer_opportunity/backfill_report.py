"""Dry-run backfill report: how existing `companies` rows would map to rfr_buyers.

Writes nothing to the database. Free-text `companies.industry` maps to taxonomy
industries only through exact (normalized) rows in data/seed/industry_synonyms.csv;
anything else is listed as unmapped, never guessed.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from app.services.buyer_opportunity.seed_import import normalize_domain
from app.services.job_posting_ingest_pause import FEED_CLASSIFICATION, PEOPLE_POSTING
from app.services.robot_understanding_v1.industries import pilot_group
from app.services.robot_understanding_v1.taxonomy_extraction import load_taxonomy, taxonomy_values
from app.services.vendor_robot_lookup import lookup_vendor_by_url

REPO_ROOT = Path(__file__).resolve().parents[3]
SYNONYMS_PATH = REPO_ROOT / "data" / "seed" / "industry_synonyms.csv"
SYNONYM_STATUSES = ("mapped", "needs_bob", "ignore")
JOB_POSTING_SIGNAL_TYPES = frozenset({"job_posting"})
PEOPLE_POSTING_SOURCES = frozenset(k for k, v in FEED_CLASSIFICATION.items() if v == PEOPLE_POSTING)
NEEDS_BOB_EXAMPLES = 3


def normalize_industry_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def load_synonyms(path: Path | str = SYNONYMS_PATH, taxonomy: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    known = set(taxonomy_values(taxonomy, "industries"))
    out: dict[str, dict[str, Any]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for line, row in enumerate(csv.DictReader(f), start=2):
            key = normalize_industry_text(row["raw_value"])
            status = row["status"].strip()
            industries = [v.strip() for v in (row.get("industries") or "").split("|") if v.strip()]
            if not key:
                raise ValueError(f"line {line}: raw_value is empty")
            if key in out:
                raise ValueError(f"line {line}: duplicate raw_value {row['raw_value']!r}")
            if status not in SYNONYM_STATUSES:
                raise ValueError(f"line {line}: status {status!r} not in {SYNONYM_STATUSES}")
            if (status == "mapped") != bool(industries):
                raise ValueError(f"line {line}: only 'mapped' rows have industries")
            bad = [v for v in industries if v not in known]
            if bad:
                raise ValueError(f"line {line}: unknown industries {bad}")
            out[key] = {
                "raw_value": row["raw_value"].strip(),
                "status": status,
                "industries": industries,
                "notes": (row.get("notes") or "").strip(),
            }
    return out


def _read_only(conn: Connection) -> None:
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text("SET TRANSACTION READ ONLY"))


def build_backfill_report(
    conn: Connection,
    synonyms: dict[str, dict[str, Any]] | None = None,
    taxonomy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify every companies row; the caller should roll back afterwards."""
    _read_only(conn)
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    synonyms = synonyms if synonyms is not None else load_synonyms(taxonomy=taxonomy)

    signal_types: dict[int, set[str]] = {}
    for company_id, signal_type in conn.execute(
        sa.text("SELECT DISTINCT company_id, signal_type FROM signals WHERE company_id IS NOT NULL")
    ):
        signal_types.setdefault(company_id, set()).add(signal_type)

    buckets: Counter[str] = Counter()
    by_industry: Counter[str] = Counter()
    by_group: Counter[str] = Counter()
    needs_bob: Counter[str] = Counter()
    needs_bob_examples: dict[str, list[str]] = {}
    unmapped: Counter[str] = Counter()
    ignored: Counter[str] = Counter()
    robot_makers: list[str] = []

    rows = conn.execute(sa.text(
        "SELECT id, name, website, website_domain, industry, source, tenant_id FROM companies ORDER BY id"
    )).mappings()
    for c in rows:
        buckets["companies_read"] += 1
        if c["tenant_id"]:
            buckets["excluded_tenant_crm_rows"] += 1
            continue
        domain = normalize_domain(c["website_domain"] or c["website"])
        if domain and lookup_vendor_by_url(domain):
            buckets["excluded_robot_makers"] += 1
            robot_makers.append(c["name"])
            continue
        types = signal_types.get(c["id"], set())
        from_people_feed = (c["source"] or "").strip().lower() in PEOPLE_POSTING_SOURCES
        if from_people_feed or (types and types <= JOB_POSTING_SIGNAL_TYPES):
            buckets["skipped_job_posting_only"] += 1
            continue
        raw = c["industry"]
        key = normalize_industry_text(raw)
        entry = synonyms.get(key)
        if not key:
            buckets["unmapped_blank_industry"] += 1
        elif entry is None:
            buckets["unmapped"] += 1
            unmapped[raw.strip()] += 1
        elif entry["status"] == "ignore":
            buckets["unmapped_ignored_value"] += 1
            ignored[entry["raw_value"]] += 1
        elif entry["status"] == "needs_bob":
            buckets["needs_bob_decision"] += 1
            needs_bob[entry["raw_value"]] += 1
            examples = needs_bob_examples.setdefault(entry["raw_value"], [])
            if len(examples) < NEEDS_BOB_EXAMPLES:
                examples.append(c["name"])
        else:
            buckets["mapped"] += 1
            groups = set()
            for industry in entry["industries"]:
                by_industry[industry] += 1
                group = pilot_group(industry, taxonomy)
                groups.add(f"{group[0]}. {group[1]}" if group else "hidden (not a pilot industry)")
            for g in groups:
                by_group[g] += 1

    return {
        "writes": 0,
        "taxonomy_version": taxonomy.get("version"),
        "counts": dict(buckets),
        "mapped_by_industry": dict(by_industry.most_common()),
        "mapped_by_pilot_group": dict(sorted(by_group.items())),
        "needs_bob_by_raw_value": dict(needs_bob.most_common()),
        "needs_bob_examples": {k: needs_bob_examples[k] for k, _ in needs_bob.most_common()},
        "unmapped_by_raw_value": dict(unmapped.most_common()),
        "ignored_by_raw_value": dict(ignored.most_common()),
        "robot_makers_excluded": robot_makers,
        "rules": {
            "mapping": "exact match after lowercase and whitespace collapse, via data/seed/industry_synonyms.csv",
            "job_posting_only": "companies.source is a people-posting feed kind, or every signal is job_posting",
            "tenant_rows": "companies with tenant_id are customer CRM rows and are excluded",
            "robot_makers": "website domain is in the vendor index",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# rfr backfill report (dry run, nothing written)",
        "",
        f"Taxonomy {report['taxonomy_version']}. Writes: {report['writes']}.",
        "",
        "## Counts",
        "",
        *[f"- {k}: {v}" for k, v in report["counts"].items()],
    ]
    lines += ["", "## Needs Bob's decision, by raw value", ""]
    lines += [
        f"- {k}: {v} (e.g. {', '.join(report['needs_bob_examples'].get(k) or [])})"
        for k, v in report["needs_bob_by_raw_value"].items()
    ] or ["- none"]
    for title, key in (
        ("Mapped, by taxonomy industry", "mapped_by_industry"),
        ("Mapped, by pilot group", "mapped_by_pilot_group"),
        ("Unmapped, by raw value", "unmapped_by_raw_value"),
        ("Ignored values", "ignored_by_raw_value"),
    ):
        lines += ["", f"## {title}", ""]
        lines += [f"- {k}: {v}" for k, v in report[key].items()] or ["- none"]
    lines += ["", "## Robot makers excluded", ""]
    lines += [f"- {n}" for n in report["robot_makers_excluded"]] or ["- none"]
    lines += ["", "## Rules", "", *[f"- {k}: {v}" for k, v in report["rules"].items()], ""]
    return "\n".join(lines)
