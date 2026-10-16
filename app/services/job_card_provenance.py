"""What a Robot Job Card may claim about where it came from.

A card is sourced only when it links to evidence (posting, contact page, or a
recorded source URL). Everything else, including every row in the bundled
match corpus, is an Example. Robot makers are supply and never appear as the
employer on a card.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

# Example cards name the kind of organization. A real company name is shown
# only when the card has a source URL.
_EXAMPLE_EMPLOYER_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"memory care|assisted living|senior living|skilled nursing", re.I), "Senior living operator"),
    (re.compile(r"surgery", re.I), "Surgery center"),
    (re.compile(r"hospital|healthcare|\bhealth\b", re.I), "Hospital system"),
    (re.compile(r"\bmall\b", re.I), "Regional mall operator"),
    (re.compile(r"restroom|facilities|facility services", re.I), "Facilities services company"),
    (re.compile(r"airport|aviation|avionics|terminal floor", re.I), "Airport operator"),
    (re.compile(r"university|college|\bcampus\b", re.I), "University"),
    (re.compile(r"cafe|coffee|espresso", re.I), "Cafe operator"),
    (re.compile(r"hotel|marriott|hilton|hyatt|room-service|room service|guest rooms?", re.I), "Hotel operator"),
    (re.compile(r"\bbar\b|cocktail|nightclub", re.I), "Bar operator"),
    (re.compile(r"restaurant|dining|grill|quick-service|fast-casual|\bkitchen\b", re.I), "Restaurant operator"),
    (re.compile(r"pharma|pharmacy", re.I), "Pharmacy distribution operator"),
    (re.compile(r"grocery", re.I), "Grocery operator"),
    (re.compile(r"warehouse|\bdc\b|fulfillment|distribution|\b3pl\b|logistics|parcel|apparel|auto parts", re.I), "Warehouse or logistics operator"),
    (re.compile(r"factory|manufactur|machine shop|\bplant\b|industrial", re.I), "Manufacturer"),
    (re.compile(r"farm|agricultur|orchard|grower|\bgrain\b", re.I), "Farm operator"),
    (re.compile(r"mining", re.I), "Mining operator"),
    (re.compile(r"construction|builder|home improvement|home center", re.I), "Construction company"),
    (re.compile(r"marine|\bport\b|drydock", re.I), "Port or marine operator"),
    (re.compile(r"aerospace|\bnasa\b", re.I), "Aerospace operator"),
    (re.compile(r"utilities|utility", re.I), "Utility operator"),
    (re.compile(r"retail", re.I), "Retail operator"),
    (re.compile(r"\bcnc\b|med device", re.I), "Manufacturer"),
    (re.compile(r"pallet|cases|returns", re.I), "Warehouse or logistics operator"),
)


def job_source_url(row: dict[str, Any]) -> Optional[str]:
    for key in ("source_url", "apply_url", "contact_url"):
        value = row.get(key)
        if isinstance(value, str) and value.strip().lower().startswith(("http://", "https://")):
            return value.strip()
    return None


def is_example_job(row: dict[str, Any]) -> bool:
    return job_source_url(row) is None


def example_employer_label(*parts: str | None) -> str:
    """Kind of organization for an example card. Never a company name.

    Parts are tried in order, so pass organization fields before work text.
    """
    for part in parts:
        if not part:
            continue
        for pattern, label in _EXAMPLE_EMPLOYER_RULES:
            if pattern.search(part):
                return label
    return "Example employer"


def public_employer_name(row: dict[str, Any]) -> str:
    """Sourced cards keep the company. Example cards use a description."""
    name = str(row.get("company_name") or "").strip()
    if not is_example_job(row):
        return name
    return example_employer_label(
        row.get("industry"),
        name,
        row.get("title"),
        row.get("path"),
    )


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
