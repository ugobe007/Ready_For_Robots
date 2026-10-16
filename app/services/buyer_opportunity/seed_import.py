"""Import Bob's seed list (data/seed/rfr_seed_accounts.csv) into rfr_ tables.

Idempotent: a row is written only when a value differs, so importing the same
file twice leaves every row (including timestamps) unchanged. Only inserts or
updates rfr_ rows; never deletes. `companies` is read to link company_id and
is never written. A row with any invalid value is rejected whole.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from app.services.buyer_opportunity.tables import rfr_buyer_industries, rfr_buyers, rfr_workflows
from app.services.robot_understanding_v1.industries import NEVER_BUYER_INDUSTRIES
from app.services.robot_understanding_v1.taxonomy_extraction import load_taxonomy, taxonomy_values
from app.services.vendor_robot_lookup import lookup_vendor_by_url

SEED_SOURCE = "bob_seed"
# Buyers whose site also hosts something the vendor index treats as a robot
# product. The maker check must not flip these. DHL's Parcelcopter is a drone
# project, not a robot product line.
BUYER_ALLOWLIST_DOMAINS = frozenset({"dhl.com"})
BUYER_ALLOWLIST_NAMES = frozenset({"dhl"})
SEED_COLUMNS = (
    "company_name", "website", "industries", "hq_city", "hq_state", "priority",
    "workflows_of_interest", "known_deployments", "notes",
)
DEPLOYMENT_NOTE = "Known deployment per Bob's seed list (bob_seed)"
_LEGAL_SUFFIX = re.compile(r"(?:\s+(?:inc|llc|ltd|corp|corporation|co|company|plc|lp|llp))+$")


def normalize_domain(website: str | None) -> str | None:
    raw = (website or "").strip().lower()
    if not raw:
        return None
    host = urlsplit(raw if "://" in raw else f"//{raw}").hostname or ""
    host = host.removeprefix("www.").strip(".")
    return host or None


def normalize_name(name: str) -> str:
    tokens = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    return _LEGAL_SUFFIX.sub("", tokens).strip()


def _split(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split("|") if v.strip()]


@dataclass
class SeedRow:
    line: int
    name: str
    domain: str | None
    name_normalized: str
    hq_city: str | None
    hq_state: str | None
    priority: str | None
    industries: list[str]
    workflows: list[str]
    deployments: dict[str, str]


@dataclass
class ImportResult:
    rows_read: int = 0
    skipped_example: list[int] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    buyers: dict[str, int] = field(default_factory=lambda: {"inserted": 0, "updated": 0, "unchanged": 0})
    industries_inserted: int = 0
    workflows: dict[str, int] = field(default_factory=lambda: {"inserted": 0, "updated": 0, "unchanged": 0})
    robot_makers: list[str] = field(default_factory=list)
    company_links: dict[str, int] = field(default_factory=lambda: {"linked": 0, "none": 0, "ambiguous": 0})

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)

    @property
    def writes(self) -> int:
        return (self.buyers["inserted"] + self.buyers["updated"] + self.industries_inserted
                + self.workflows["inserted"] + self.workflows["updated"])


def parse_seed_rows(lines: Iterable[str], taxonomy: dict[str, Any] | None = None) -> tuple[list[SeedRow], ImportResult]:
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    industries_ok = set(taxonomy_values(taxonomy, "industries"))
    functions_ok = set(taxonomy_values(taxonomy, "functions"))
    result = ImportResult()
    rows: list[SeedRow] = []
    seen_names: dict[str, int] = {}
    seen_domains: dict[str, int] = {}

    reader = csv.DictReader(lines)
    missing = [c for c in SEED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"seed CSV is missing columns: {missing}")

    for line, raw in enumerate(reader, start=2):
        result.rows_read += 1
        name = (raw.get("company_name") or "").strip()
        if name.upper().startswith("EXAMPLE"):
            result.skipped_example.append(line)
            continue
        errors: list[str] = []
        if not name:
            errors.append("company_name is empty")
        industries = _split(raw.get("industries"))
        workflows = _split(raw.get("workflows_of_interest"))
        errors += [f"unknown industry {v!r}" for v in industries if v not in industries_ok]
        errors += [f"{v!r} is never a buyer industry" for v in industries if v in NEVER_BUYER_INDUSTRIES]
        errors += [f"unknown workflow {v!r}" for v in workflows if v not in functions_ok]
        deployments: dict[str, str] = {}
        for item in _split(raw.get("known_deployments")):
            workflow, sep, vendor = item.partition(":")
            workflow, vendor = workflow.strip(), vendor.strip()
            if not sep or not vendor:
                errors.append(f"known_deployments item {item!r} is not workflow:vendor")
            elif workflow not in functions_ok:
                errors.append(f"unknown deployment workflow {workflow!r}")
            elif workflow in deployments and deployments[workflow] != vendor:
                errors.append(f"two vendors for deployment workflow {workflow!r}")
            else:
                deployments[workflow] = vendor
        priority = (raw.get("priority") or "").strip().upper() or None
        if priority not in (None, "A", "B", "C"):
            errors.append(f"priority {priority!r} is not A, B, C or blank")
        domain = normalize_domain(raw.get("website"))
        name_key = normalize_name(name)
        if not errors and name_key and name_key in seen_names:
            errors.append(f"same buyer as line {seen_names[name_key]} (name {name_key!r})")
        elif not errors and domain and domain in seen_domains:
            errors.append(f"same buyer as line {seen_domains[domain]} (domain {domain!r})")
        if errors:
            result.rejected.append({"line": line, "company_name": name, "errors": errors})
            continue
        if name_key:
            seen_names[name_key] = line
        if domain:
            seen_domains[domain] = line
        rows.append(SeedRow(
            line=line, name=name, domain=domain, name_normalized=normalize_name(name),
            hq_city=(raw.get("hq_city") or "").strip() or None,
            hq_state=(raw.get("hq_state") or "").strip() or None,
            priority=priority,
            industries=list(dict.fromkeys(industries)),
            workflows=list(dict.fromkeys(workflows)),
            deployments=deployments,
        ))
    return rows, result


def _company_id(conn: Connection, row: SeedRow) -> tuple[int | None, str]:
    """Link only a public companies row. Tenant CRM copies are not buyers."""
    if row.domain:
        query = sa.text(
            "SELECT id FROM companies WHERE tenant_id IS NULL AND lower(website_domain) = :v "
            "ORDER BY id LIMIT 2"
        )
        ids = [r[0] for r in conn.execute(query, {"v": row.domain})]
    else:
        query = sa.text(
            "SELECT id FROM companies WHERE tenant_id IS NULL AND lower(name) = :v "
            "ORDER BY id LIMIT 2"
        )
        ids = [r[0] for r in conn.execute(query, {"v": row.name.lower()})]
    if len(ids) == 1:
        return ids[0], "linked"
    return None, "ambiguous" if ids else "none"


def _find_buyer(conn: Connection, row: SeedRow):
    """Domain finds a row that already has it. The normalized name still finds
    the row from before a website existed, or whose website changed."""
    b = rfr_buyers.c
    if row.domain:
        by_domain = conn.execute(
            sa.select(rfr_buyers).where(b.website_domain == row.domain)
        ).mappings().first()
        if by_domain is not None:
            return by_domain
    return conn.execute(
        sa.select(rfr_buyers).where(b.name_normalized == row.name_normalized).order_by(b.id)
    ).mappings().first()


def buyer_is_robot_maker(row: SeedRow) -> bool:
    """False for an explicit buyer, even when the vendor index hits the domain."""
    if row.domain in BUYER_ALLOWLIST_DOMAINS or row.name_normalized in BUYER_ALLOWLIST_NAMES:
        return False
    return bool(row.domain and lookup_vendor_by_url(row.domain))


def _upsert_buyer(conn: Connection, row: SeedRow, result: ImportResult) -> int:
    company_id, link = _company_id(conn, row)
    result.company_links[link] += 1
    is_robot_maker = buyer_is_robot_maker(row)
    if is_robot_maker:
        result.robot_makers.append(row.name)
    values = {
        "company_id": company_id, "name": row.name, "name_normalized": row.name_normalized,
        "website_domain": row.domain, "hq_city": row.hq_city, "hq_state": row.hq_state,
        "priority": row.priority, "source": SEED_SOURCE, "is_robot_maker": is_robot_maker,
    }
    existing = _find_buyer(conn, row)
    if existing is None:
        result.buyers["inserted"] += 1
        return conn.execute(rfr_buyers.insert().values(**values).returning(rfr_buyers.c.id)).scalar_one()
    if link != "linked":
        values.pop("company_id")
    changed = {k: v for k, v in values.items() if existing[k] != v}
    if not changed:
        result.buyers["unchanged"] += 1
        return existing["id"]
    result.buyers["updated"] += 1
    conn.execute(
        rfr_buyers.update().where(rfr_buyers.c.id == existing["id"])
        .values(**changed, updated_at=sa.func.current_timestamp())
    )
    return existing["id"]


def _ensure_industries(conn: Connection, buyer_id: int, row: SeedRow, result: ImportResult) -> None:
    t = rfr_buyer_industries.c
    have = set(conn.execute(
        sa.select(t.industry).where(t.buyer_id == buyer_id, t.source == SEED_SOURCE)
    ).scalars())
    for industry in row.industries:
        if industry not in have:
            conn.execute(rfr_buyer_industries.insert().values(
                buyer_id=buyer_id, industry=industry, confidence=1.0, source=SEED_SOURCE, source_url=None,
            ))
            result.industries_inserted += 1


def _ensure_workflows(conn: Connection, buyer_id: int, row: SeedRow, result: ImportResult) -> None:
    t = rfr_workflows.c
    existing = {
        r["workflow"]: r for r in conn.execute(
            sa.select(rfr_workflows).where(t.buyer_id == buyer_id)
        ).mappings()
    }
    seed_committed = {
        workflow for workflow, current in existing.items() if current["status_note"] == DEPLOYMENT_NOTE
    }
    cleared = {"status": "unknown", "committed_vendor": None, "status_note": None, "status_source_url": None}
    for workflow in dict.fromkeys(list(row.workflows) + list(row.deployments) + list(seed_committed)):
        vendor = row.deployments.get(workflow)
        if vendor:
            wanted = {
                "status": "committed", "committed_vendor": vendor,
                "status_note": DEPLOYMENT_NOTE, "status_source_url": None,
            }
        elif workflow in seed_committed:
            wanted = cleared
        else:
            wanted = None
        current = existing.get(workflow)
        if current is None:
            conn.execute(rfr_workflows.insert().values(
                buyer_id=buyer_id, workflow=workflow, **(wanted or {"status": "unknown"}),
            ))
            result.workflows["inserted"] += 1
            continue
        changed = {k: v for k, v in (wanted or {}).items() if current[k] != v}
        if not changed:
            result.workflows["unchanged"] += 1
            continue
        conn.execute(
            rfr_workflows.update().where(t.id == current["id"])
            .values(**changed, updated_at=sa.func.current_timestamp())
        )
        result.workflows["updated"] += 1


def import_seed(conn: Connection, csv_path: Path | str, taxonomy: dict[str, Any] | None = None) -> ImportResult:
    """Apply the seed file on `conn`. The caller owns the transaction (commit or roll back)."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows, result = parse_seed_rows(f, taxonomy)
    for row in rows:
        buyer_id = _upsert_buyer(conn, row, result)
        _ensure_industries(conn, buyer_id, row, result)
        _ensure_workflows(conn, buyer_id, row, result)
    return result
