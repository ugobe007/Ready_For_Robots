"""Exact synonyms from company.industry free text onto the 29 taxonomy industries.

A label is mapped only when the whole string is one entry in this table, or it
is already a taxonomy key. Combined or ambiguous labels are left unmapped.
Nothing here writes to the companies table.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_TAXONOMY_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "taxonomy.v1.json"

# Normalized phrase -> taxonomy industry key.
# Absent phrases stay unmapped. "logistics" and "hospitality" are absent on
# purpose: each name covers more than one taxonomy industry.
EXACT_SYNONYMS: dict[str, str] = {
    "food service": "restaurant",
    "food service (restaurants)": "restaurant",
    "food service and catering": "restaurant",
    "restaurant": "restaurant",
    "restaurants": "restaurant",
    "food service (fast casual)": "qsr_fast_food",
    "qsr": "qsr_fast_food",
    "fast food": "qsr_fast_food",
    "hospitality (hotel management)": "hotel",
    "hotel": "hotel",
    "hotels": "hotel",
    "casinos and gaming": "casino",
    "casino": "casino",
    "theme parks and entertainment": "stadium_venue",
    "airports and aviation": "airport",
    "airport": "airport",
    "healthcare": "hospital",
    "healthcare (hospital systems)": "hospital",
    "hospital": "hospital",
    "hospitals": "hospital",
    "healthcare (skilled nursing)": "senior_living",
    "senior living and assisted living": "senior_living",
    "senior living": "senior_living",
    "retail": "retail_store",
    "automotive and manufacturing": "manufacturing",
    "manufacturing": "manufacturing",
    "factory": "manufacturing",
    "food processing and manufacturing": "food_manufacturing",
    "food manufacturing (contract manufacturing)": "food_manufacturing",
    "datacenters": "data_center",
    "datacenter": "data_center",
    "data center": "data_center",
    "data centers": "data_center",
    "cold storage logistics": "warehouse_distribution",
    "logistics and warehousing (cold storage)": "warehouse_distribution",
    "food and beverage distribution": "warehouse_distribution",
    "warehouse": "warehouse_distribution",
    "warehousing": "warehouse_distribution",
    "logistics and warehousing (3pl)": "3pl",
    "logistics and supply chain (3pl)": "3pl",
    "3pl": "3pl",
    "construction": "construction",
    "construction and building": "construction",
    "mining": "energy_utilities",
    "defense": "defense",
    "cruise lines": "ships_maritime",
    "agriculture": "agriculture",
    "government": "government",
}


def normalize_industry_text(text: str | None) -> str:
    raw = (text or "").strip().lower().replace("&", " and ")
    raw = re.sub(r"[^a-z0-9()/ ]+", "", raw)
    return re.sub(r"\s+", " ", raw).strip()


@lru_cache(maxsize=1)
def taxonomy_industry_keys() -> frozenset[str]:
    data = json.loads(_TAXONOMY_PATH.read_text(encoding="utf-8"))
    return frozenset(key for key in data["industries"] if not key.startswith("_"))


@lru_cache(maxsize=1)
def taxonomy_function_keys() -> frozenset[str]:
    data = json.loads(_TAXONOMY_PATH.read_text(encoding="utf-8"))
    return frozenset(data["functions"])


def classify_industry(text: str | None) -> str | None:
    """Return one taxonomy industry key, or None when the label is not exact."""
    normalized = normalize_industry_text(text)
    if not normalized:
        return None
    if normalized in taxonomy_industry_keys():
        return normalized
    key = EXACT_SYNONYMS.get(normalized)
    if key in taxonomy_industry_keys():
        return key
    return None
