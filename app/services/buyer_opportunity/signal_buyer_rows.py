"""Buyer rows from Budget confirmed signals.

Behind ``RFR_FIND_SIGNAL_ROWS`` (default off). A row exists only when the
signal names the work: a closed taxonomy function and a closed taxonomy
industry, both taken from the signal text. A signal that names neither, or
that names a function but no industry, does not become a row.

This does not write the database. Expiry is null: the signals table has no
expiry column, and the text does not state one.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

BUDGET_CONFIRMED = "Budget confirmed"

_RFP_TYPES = frozenset({"rfp_posted", "vendor_selection", "government_contract"})
_RFP_TEXT = re.compile(
    r"\b(rfp|rfq|rfi|request for proposal|request for quote)\b",
    re.I,
)

# First match wins. Phrases are the work the signal names, not a nearby noun.
_WORK_RULES: tuple[tuple[re.Pattern[str], str, str, str], ...] = (
    (
        re.compile(r"grocery pickup", re.I),
        "picking_packing_palletizing",
        "pick_pack",
        "Grocery pickup",
    ),
    (
        re.compile(r"\bfood delivery\b", re.I),
        "delivery_transport",
        "transport",
        "Food delivery",
    ),
    (
        re.compile(r"\bfloor (?:scrub|clean)", re.I),
        "cleaning",
        "scrub",
        "Floor cleaning",
    ),
    (
        re.compile(r"\bsecurity patrol\b", re.I),
        "security_patrol",
        "inspect",
        "Security patrol",
    ),
    (
        re.compile(r"\bshelf scan\b", re.I),
        "inspection",
        "shelf_scan",
        "Shelf scan",
    ),
)

# First match wins. The industry has to be a taxonomy key the corpus join accepts.
_INDUSTRY_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bgrocery\b", re.I), "grocery"),
    (re.compile(r"\bairport\b", re.I), "airport"),
    (re.compile(r"\bhospital\b", re.I), "hospital"),
    (re.compile(r"\bhotel\b", re.I), "hotel"),
    (re.compile(r"\bwarehouse\b", re.I), "warehouse_distribution"),
    (re.compile(r"\brestaurant\b", re.I), "restaurant"),
    (re.compile(r"\b(?:farm|farming)\b", re.I), "agriculture"),
    (re.compile(r"\b(?:construction|jobsite)\b", re.I), "construction"),
)


def signal_rows_enabled() -> bool:
    return os.getenv("RFR_FIND_SIGNAL_ROWS", "").strip().lower() in ("1", "true", "yes")


def clean_signal_text(text: str | None) -> str:
    raw = re.sub(r"<[^>]+>", " ", text or "")
    raw = re.sub(r"https?://\S+", " ", raw)
    raw = raw.replace("&nbsp;", " ")
    raw = re.sub(r"\s+", " ", raw).strip()
    sentence = re.split(r"(?<=\.)\s+", raw, maxsplit=1)[0]
    return sentence[:280]


def is_budget_signal(signal_type: str | None, text: str | None) -> bool:
    kind = (signal_type or "").strip()
    if kind == "pilot_success" or kind in _RFP_TYPES:
        return True
    return bool(_RFP_TEXT.search(text or ""))


def named_work(text: str) -> tuple[str, str, str] | None:
    for pattern, function, family, title in _WORK_RULES:
        if pattern.search(text):
            return function, family, title
    return None


def named_industry(text: str) -> str | None:
    for pattern, industry in _INDUSTRY_RULES:
        if pattern.search(text):
            return industry
    return None


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def partition_budget_companies(companies: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Split Budget confirmed companies into rows and companies with no row.

    ``skipped`` is one entry per company that did not name both a workflow and
    an industry. ``rows`` is one card per company × workflow × industry.
    """
    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for company in companies:
        name = str(company.get("name") or "").strip()
        company_id = company.get("id")
        signals = [
            signal
            for signal in (company.get("signals") or [])
            if isinstance(signal, dict)
            and is_budget_signal(signal.get("type") or signal.get("signal_type"), signal.get("text"))
        ]
        chosen: dict[str, Any] | None = None
        named_function: str | None = None
        for signal in signals:
            text = clean_signal_text(signal.get("text"))
            work = named_work(text)
            industry = named_industry(text)
            if work and named_function is None:
                named_function = work[0]
            if work and industry:
                chosen = {
                    "text": text,
                    "work": work,
                    "industry": industry,
                    "source_url": signal.get("source_url"),
                    "created_at": signal.get("created_at"),
                }
                break
        if chosen is None:
            reason = "no_taxonomy_industry" if named_function else "no_named_workflow"
            skipped.append(
                {
                    "company_id": company_id,
                    "company_name": name,
                    "reason": reason,
                    "workflow": named_function,
                }
            )
            continue
        function, family, title = chosen["work"]
        source = chosen["source_url"] if isinstance(chosen["source_url"], str) else None
        rows.append(
            {
                "job_key": f"signal-{company_id}-{function}",
                "title": title,
                "industry": chosen["industry"],
                "path": title,
                "company_name": name,
                "locality": None,
                "tape_family": family,
                "source": "signal",
                "source_url": source,
                "readiness_label": BUDGET_CONFIRMED,
                "why_now": chosen["text"],
                "workflow": function,
                "signal_date": _iso(chosen["created_at"]),
                "signal_expiry": None,
                "text": chosen["text"],
                "unknowns": [],
            }
        )
    return {"rows": rows, "skipped": skipped}


def load_budget_confirmed_partition() -> dict[str, list[dict[str, Any]]]:
    """Read the latest-score cut. No writes."""
    from sqlalchemy import text

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        found = db.execute(
            text(
                """
                WITH latest AS (
                  SELECT DISTINCT ON (company_id) company_id, overall_intent_score
                  FROM scores
                  ORDER BY company_id, last_calculated_at DESC NULLS LAST, id DESC
                )
                SELECT c.id, c.name, g.signal_type, g.signal_text, g.source_url, g.created_at
                FROM companies c
                JOIN latest s ON s.company_id = c.id AND s.overall_intent_score >= 40
                JOIN signals g ON g.company_id = c.id
                WHERE g.signal_type = 'pilot_success'
                   OR g.signal_type IN ('rfp_posted', 'vendor_selection', 'government_contract')
                   OR g.signal_text ~* '\\y(rfp|rfq|rfi|request for proposal|request for quote)\\y'
                ORDER BY c.id, g.created_at DESC NULLS LAST, g.id DESC
                """
            )
        ).fetchall()
    finally:
        db.close()
    grouped: dict[int, dict[str, Any]] = {}
    for company_id, name, signal_type, signal_text, source_url, created_at in found:
        bucket = grouped.setdefault(
            company_id,
            {"id": company_id, "name": name, "signals": []},
        )
        bucket["signals"].append(
            {
                "type": signal_type,
                "text": signal_text,
                "source_url": source_url,
                "created_at": created_at,
            }
        )
    return partition_budget_companies(list(grouped.values()))
