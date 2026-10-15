"""Dry-run backfill report: how existing `companies` rows would map to rfr_buyers.

Writes nothing to the database. Free-text `companies.industry` maps to taxonomy
industries only through exact (normalized) rows in data/seed/industry_synonyms.csv;
anything else is listed as unmapped, never guessed.

Synonym rows (Bob's mapping):
- needs_company_check = no, default set: every default industry is assigned.
- needs_company_check = yes: each company is checked against its own website
  (industry_company_check.py). Only a decision with an evidence quote assigns
  industries; anything else goes to the review list with the default as a suggestion.
- no candidates and no default: the value is ignored.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from app.services.buyer_opportunity.seed_import import normalize_domain
from app.services.job_posting_ingest_pause import FEED_CLASSIFICATION, PEOPLE_POSTING
from app.services.robot_understanding_v1.industries import NEVER_BUYER_INDUSTRIES, pilot_group
from app.services.robot_understanding_v1.taxonomy_extraction import load_taxonomy, taxonomy_values
from app.services.vendor_robot_lookup import lookup_vendor_by_url

REPO_ROOT = Path(__file__).resolve().parents[3]
SYNONYMS_PATH = REPO_ROOT / "data" / "seed" / "industry_synonyms.csv"
SYNONYM_COLUMNS = ("source_value", "candidate_industries", "default_if_unclear", "needs_company_check", "notes")
JOB_POSTING_SIGNAL_TYPES = frozenset({"job_posting"})
PEOPLE_POSTING_SOURCES = frozenset(k for k, v in FEED_CLASSIFICATION.items() if v == PEOPLE_POSTING)
COMPANY_CHECK_EXAMPLES = 3


def normalize_industry_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _split(value: str | None) -> list[str]:
    return list(dict.fromkeys(v.strip() for v in (value or "").split("|") if v.strip()))


def load_synonyms(path: Path | str = SYNONYMS_PATH, taxonomy: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    known = set(taxonomy_values(taxonomy, "industries"))
    out: dict[str, dict[str, Any]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in SYNONYM_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"synonyms CSV is missing columns: {missing}")
        for line, row in enumerate(reader, start=2):
            raw = (row["source_value"] or "").strip()
            key = normalize_industry_text(raw)
            candidates = _split(row["candidate_industries"])
            default = _split(row["default_if_unclear"])
            check = (row["needs_company_check"] or "").strip().lower()
            if not key:
                raise ValueError(f"line {line}: source_value is empty")
            if key in out:
                raise ValueError(f"line {line}: duplicate source_value {raw!r}")
            if check not in ("yes", "no"):
                raise ValueError(f"line {line}: needs_company_check {check!r} is not yes or no")
            bad = [v for v in candidates + default if v not in known]
            if bad:
                raise ValueError(f"line {line}: unknown industries {bad}")
            never = [v for v in candidates + default if v in NEVER_BUYER_INDUSTRIES]
            if never:
                raise ValueError(f"line {line}: {never} is never a buyer industry")
            if candidates and not set(default) <= set(candidates):
                raise ValueError(f"line {line}: default_if_unclear is not among candidate_industries")
            if check == "yes":
                if not candidates:
                    raise ValueError(f"line {line}: a company check needs candidate_industries")
                status = "company_check"
            elif default:
                status = "mapped"
            elif candidates:
                raise ValueError(f"line {line}: candidates without a default need needs_company_check = yes")
            else:
                status = "ignore"
            out[key] = {
                "raw_value": raw,
                "status": status,
                "candidates": candidates or default,
                "default": default,
                "industries": default if status == "mapped" else [],
                "notes": (row.get("notes") or "").strip(),
            }
    return out


def _read_only(conn: Connection) -> None:
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text("SET TRANSACTION READ ONLY"))


def classify_companies(conn: Connection, synonyms: dict[str, dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Yield {company, domain, bucket, entry} for every companies row. Read-only."""
    _read_only(conn)
    signal_types: dict[int, set[str]] = {}
    for company_id, signal_type in conn.execute(
        sa.text("SELECT DISTINCT company_id, signal_type FROM signals WHERE company_id IS NOT NULL")
    ):
        signal_types.setdefault(company_id, set()).add(signal_type)

    rows = conn.execute(sa.text(
        "SELECT id, name, website, website_domain, industry, source, tenant_id FROM companies ORDER BY id"
    )).mappings().all()
    for c in rows:
        domain = normalize_domain(c["website_domain"] or c["website"])
        entry = synonyms.get(normalize_industry_text(c["industry"]))
        types = signal_types.get(c["id"], set())
        from_people_feed = (c["source"] or "").strip().lower() in PEOPLE_POSTING_SOURCES
        if c["tenant_id"]:
            bucket = "excluded_tenant_crm_rows"
        elif domain and lookup_vendor_by_url(domain):
            bucket = "excluded_robot_makers"
        elif from_people_feed or (types and types <= JOB_POSTING_SIGNAL_TYPES):
            bucket = "skipped_job_posting_only"
        elif not normalize_industry_text(c["industry"]):
            bucket = "unmapped_blank_industry"
        elif entry is None:
            bucket = "unmapped"
        elif entry["status"] == "ignore":
            bucket = "unmapped_ignored_value"
        elif entry["status"] == "company_check":
            bucket = "needs_company_check"
        else:
            bucket = "mapped"
        yield {"company": c, "domain": domain, "bucket": bucket, "entry": entry}


def build_backfill_report(
    conn: Connection,
    synonyms: dict[str, dict[str, Any]] | None = None,
    taxonomy: dict[str, Any] | None = None,
    company_checks: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Classify every companies row; the caller should roll back afterwards.

    `company_checks` maps company id to a decision from industry_company_check.
    """
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    synonyms = synonyms if synonyms is not None else load_synonyms(taxonomy=taxonomy)
    company_checks = company_checks or {}

    buckets: Counter[str] = Counter()
    by_industry: Counter[str] = Counter()
    by_group: Counter[str] = Counter()
    pending: Counter[str] = Counter()
    pending_examples: dict[str, list[str]] = {}
    unmapped: Counter[str] = Counter()
    ignored: Counter[str] = Counter()
    robot_makers: list[str] = []
    review: list[dict[str, Any]] = []

    def assign(industries: list[str]) -> None:
        groups = set()
        for industry in industries:
            by_industry[industry] += 1
            group = pilot_group(industry, taxonomy)
            groups.add(f"{group[0]}. {group[1]}" if group else "hidden (not a pilot industry)")
        for g in groups:
            by_group[g] += 1

    for item in classify_companies(conn, synonyms):
        c, bucket, entry = item["company"], item["bucket"], item["entry"]
        buckets["companies_read"] += 1
        if bucket == "excluded_robot_makers":
            robot_makers.append(c["name"])
        elif bucket == "unmapped":
            unmapped[c["industry"].strip()] += 1
        elif bucket == "unmapped_ignored_value":
            ignored[entry["raw_value"]] += 1
        elif bucket == "mapped":
            assign(entry["industries"])
        elif bucket == "needs_company_check":
            decision = company_checks.get(c["id"])
            if decision and decision.get("status") == "decided":
                bucket = "mapped_by_company_check"
                assign(decision["industries"])
            elif decision:
                bucket = "company_check_review"
                review.append({
                    "company_id": c["id"],
                    "name": c["name"],
                    "raw_value": entry["raw_value"],
                    "candidates": entry["candidates"],
                    "suggestion": entry["default"],
                    "reason": decision.get("reason") or "",
                })
            else:
                pending[entry["raw_value"]] += 1
                examples = pending_examples.setdefault(entry["raw_value"], [])
                if len(examples) < COMPANY_CHECK_EXAMPLES:
                    examples.append(c["name"])
        buckets[bucket] += 1

    return {
        "writes": 0,
        "taxonomy_version": taxonomy.get("version"),
        "counts": dict(buckets),
        "mapped_by_industry": dict(by_industry.most_common()),
        "mapped_by_pilot_group": dict(sorted(by_group.items())),
        "needs_company_check_by_raw_value": dict(pending.most_common()),
        "needs_company_check_examples": {k: pending_examples[k] for k, _ in pending.most_common()},
        "company_check_review": review,
        "unmapped_by_raw_value": dict(unmapped.most_common()),
        "ignored_by_raw_value": dict(ignored.most_common()),
        "robot_makers_excluded": robot_makers,
        "rules": {
            "mapping": "exact match after lowercase and whitespace collapse, via data/seed/industry_synonyms.csv",
            "needs_company_check_no": "every default_if_unclear industry is assigned",
            "needs_company_check_yes": "assigned only from a website decision with an evidence quote; otherwise review",
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
    lines += ["", "## Not yet checked against the company website, by raw value", ""]
    lines += [
        f"- {k}: {v} (e.g. {', '.join(report['needs_company_check_examples'].get(k) or [])})"
        for k, v in report["needs_company_check_by_raw_value"].items()
    ] or ["- none"]
    lines += ["", "## Review list (website check found no evidence)", ""]
    lines += [
        f"- {r['name']} ({r['raw_value']}): suggest {', '.join(r['suggestion']) or 'none'}; "
        f"candidates {', '.join(r['candidates'])}. {r['reason']}".rstrip()
        for r in report["company_check_review"]
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
