"""What a Robot Job Card may claim about where it came from.

A card is sourced only when it links to evidence (posting, contact page, or a
recorded source URL). Everything else, including every row in the bundled
match corpus, is an Example. Robot makers are supply and never appear as the
employer on a card.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional


def job_source_url(row: dict[str, Any]) -> Optional[str]:
    for key in ("source_url", "apply_url", "contact_url"):
        value = row.get(key)
        if isinstance(value, str) and value.strip().lower().startswith(("http://", "https://")):
            return value.strip()
    return None


def is_example_job(row: dict[str, Any]) -> bool:
    return job_source_url(row) is None


def public_employer_email(email: Optional[str], employer: Optional[str]) -> Optional[str]:
    from app.services.daily_jobs_report import _is_invented_ops_email

    raw = (email or "").strip()
    if not raw or _is_invented_ops_email(raw, employer or ""):
        return None
    return raw


def is_robot_maker_employer(row: dict[str, Any]) -> bool:
    from app.services.workflow_ontology import is_robot_vendor

    return is_robot_vendor(str(row.get("company_name") or ""))


def buyer_rows(rows: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(row for row in rows if not is_robot_maker_employer(row))
