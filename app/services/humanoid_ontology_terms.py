"""
Humanoid vendor / product surface forms for ontology pattern expansion.

Pulls from ``humanoid_vendor_catalog.HUMANOID_CATALOG`` so signal and concept
matching stays aligned with the benchmark list (NEURA, MagicLab, Unitree, etc.).
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable, List, Set

from app.services.humanoid_vendor_catalog import HUMANOID_CATALOG

# Pilot catalog rows label deployers as vendor — exclude from OEM junk filter.
HUMANOID_CATALOG_BUYER_VENDORS = frozenset({
    "foxconn",
    "siemens",
    "softbank",
    "softbank robotics",
    "nvidia robotics",
    "toyota",
    "toyota industries",
    "toyota motor",
    "toyota material handling",
    "samsung",
    "samsung electronics",
    "samsung c&t",
    "mercedes-benz",
    "honda",
    "hyundai",
    "boeing",
    "airbus",
    "schaeffler",
    "mitsubishi electric",
    "mitsubishi electric automation",
    "lg electronics",
    "tesla",
})

_ALIAS_SPLIT = re.compile(r"[|,;/]")


def _norm_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


@lru_cache(maxsize=1)
def catalog_humanoid_patterns(*, max_terms: int = 96) -> tuple[str, ...]:
    """Distinct vendor/product phrases safe for case-insensitive substring match."""
    seen: Set[str] = set()
    out: List[str] = []

    def _add(raw: str) -> None:
        phrase = _norm_phrase(raw)
        if len(phrase) < 4 or phrase in seen:
            return
        seen.add(phrase)
        out.append(phrase)

    for entry in HUMANOID_CATALOG:
        for key in ("vendor", "name", "vendor_name_cn", "robot_name_cn"):
            _add(str(entry.get(key) or ""))
        for field in ("vendor_aliases", "robot_aliases"):
            blob = str(entry.get(field) or "")
            for part in _ALIAS_SPLIT.split(blob):
                _add(part)

    out.sort(key=len, reverse=True)
    return tuple(out[:max_terms])


@lru_cache(maxsize=1)
def catalog_humanoid_vendor_names() -> frozenset[str]:
    """Normalized vendor strings for OEM / non-buyer filtering."""
    names: Set[str] = set()
    for entry in HUMANOID_CATALOG:
        for key in ("vendor",):
            v = _norm_phrase(str(entry.get(key) or ""))
            if v and v not in HUMANOID_CATALOG_BUYER_VENDORS:
                names.add(v)
        for part in _ALIAS_SPLIT.split(str(entry.get("vendor_aliases") or "")):
            v = _norm_phrase(part)
            if len(v) >= 4 and v not in HUMANOID_CATALOG_BUYER_VENDORS:
                names.add(v)
    return frozenset(names)


def merge_catalog_patterns(existing: Iterable[str]) -> List[str]:
    """Deduped union of static patterns + catalog phrases."""
    seen = {_norm_phrase(p) for p in existing if _norm_phrase(p)}
    merged = list(existing)
    for phrase in catalog_humanoid_patterns():
        if phrase not in seen:
            seen.add(phrase)
            merged.append(phrase)
    return merged
