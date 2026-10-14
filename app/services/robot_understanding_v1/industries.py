"""Industry parents and pilot-industry groups.

`industry_parents` in taxonomy.v1.json says which newer industries also count
as an older one (bar_nightclub -> restaurant). A child satisfies its parent in
answer-key scoring and in pilot-group membership; a parent never satisfies a
child. Pilot groups and their priority order come from
docs/buyer_opportunity_spec.md §1; industries outside them stay hidden.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable

from app.services.robot_understanding_v1.taxonomy_extraction import load_taxonomy, taxonomy_values

PILOT_INDUSTRY_GROUPS: tuple[tuple[int, str, tuple[str, ...]], ...] = (
    (1, "Warehouse, logistics, 3PL", ("warehouse_distribution", "3pl", "logistics_parcel")),
    (2, "Factories", ("manufacturing", "food_manufacturing")),
    (3, "Hotels and casinos", ("hotel", "casino")),
    (4, "Hospitals", ("hospital", "surgery_center")),
    (5, "Retail", ("retail_store", "grocery", "shopping_mall")),
    (6, "Restaurants and bars", ("restaurant", "qsr_fast_food", "bar_nightclub")),
    (7, "Airports", ("airport",)),
    (8, "Office buildings", ("office_building", "commercial_building", "corporate_campus")),
)

NEVER_BUYER_INDUSTRIES = frozenset({"residential_consumer"})


def industry_parents(taxonomy: dict[str, Any] | None = None) -> dict[str, str]:
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    return {k: v for k, v in (taxonomy.get("industry_parents") or {}).items() if not k.startswith("_")}


@lru_cache(maxsize=1)
def _default_parents() -> tuple[tuple[str, str], ...]:
    return tuple(industry_parents().items())


def with_parents(industries: Iterable[str], taxonomy: dict[str, Any] | None = None) -> set[str]:
    """The industries plus every ancestor they count as."""
    parents = industry_parents(taxonomy) if taxonomy is not None else dict(_default_parents())
    out: set[str] = set()
    for industry in industries:
        while industry and industry not in out:
            out.add(industry)
            industry = parents.get(industry)
    return out


def pilot_group(industry: str, taxonomy: dict[str, Any] | None = None) -> tuple[int, str] | None:
    """(priority, label) of the first pilot group the industry belongs to, or None if hidden."""
    if industry in NEVER_BUYER_INDUSTRIES:
        return None
    counts_as = with_parents([industry], taxonomy)
    for rank, label, members in PILOT_INDUSTRY_GROUPS:
        if counts_as & set(members):
            return rank, label
    return None


def is_pilot_industry(industry: str, taxonomy: dict[str, Any] | None = None) -> bool:
    return pilot_group(industry, taxonomy) is not None


def invalid_pilot_values(taxonomy: dict[str, Any] | None = None) -> list[str]:
    """Pilot-group values that are not taxonomy industries (should be empty)."""
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    known = set(taxonomy_values(taxonomy, "industries"))
    return [v for _, _, members in PILOT_INDUSTRY_GROUPS for v in members if v not in known]
