"""Form must fit the work (buyer_opportunity_spec v1.3 §6 step 5), current flow only.

Work that moves through a building needs a robot that moves. A grounded
`has_mobile_base: false` never gets those jobs, unless the same claims also
say the robot navigates or name a mobility architecture. That is the same
exception capability derivation already uses. Phase 2 replaces this with the
config-driven compatibility table.
"""
from __future__ import annotations

from typing import Any, Iterable

# Bundled corpus tape families for delivery/transport, table-running and
# bussing, cleaning, and patrol/inspection rounds.
MOBILE_ONLY_TAPE_FAMILIES = frozenset(
    {
        "transport",
        "cart",
        "pallet_move",
        "clinical_delivery",
        "resident_services",
        "serve",
        "hospitality",
        "scrub",
        "restroom",
        "disinfection",
        "inspect",
        "shelf_scan",
    }
)


def indexed_sku(url: str | None, robot_name: str | None = None) -> dict[str, Any] | None:
    from app.services.vendor_robot_lookup import (
        index_robot_for_name,
        lookup_vendor_by_url,
        select_index_robot,
    )

    vendor = lookup_vendor_by_url(url)
    if not vendor:
        return None
    return select_index_robot(url, vendor) or (
        index_robot_for_name(vendor, robot_name) if robot_name else None
    )


def _claims(claims: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [c for c in claims or [] if isinstance(c, dict)]


def _false_mobile_base(claims: Iterable[dict[str, Any]] | None) -> bool:
    return any(
        c.get("predicate") == "has_mobile_base" and c.get("value") in (False, "false")
        for c in _claims(claims)
    )


def _explicit_mobility(claims: Iterable[dict[str, Any]] | None) -> bool:
    """True base, navigation, or a mobility architecture. Class guesses do not count."""
    for claim in _claims(claims):
        pred = claim.get("predicate")
        value = claim.get("value")
        if pred == "has_mobile_base" and value in (True, "true", 1):
            return True
        if pred == "autonomous_navigation" and value in (True, "true", 1):
            return True
        if pred == "mobility_architecture" and value not in (None, "", False, "false"):
            return True
    return False


def claims_are_stationary(claims: Iterable[dict[str, Any]] | None) -> bool:
    return _false_mobile_base(claims) and not _explicit_mobility(claims)


def is_stationary_sku(robot: dict[str, Any] | None) -> bool:
    return claims_are_stationary((robot or {}).get("catalog_claims"))


def is_stationary_for_jobs(
    profile: dict[str, Any] | None,
    indexed: dict[str, Any] | None = None,
) -> bool:
    """Stationary when a grounded false base is not contradicted by navigation.

    Profile facts use the same grounded filter as capability derivation.
    Vendor-index claims are already curated, so they count as written.
    """
    from app.services.robot_capability_derive import _grounded_facts

    claims = list(_grounded_facts(profile or {}))
    claims.extend((indexed or {}).get("catalog_claims") or [])
    return claims_are_stationary(claims)


def jobs_fit_form(jobs: Iterable[dict[str, Any]], *, stationary: bool) -> list[dict[str, Any]]:
    rows = list(jobs)
    if not stationary:
        return rows
    return [j for j in rows if (j.get("tape_family") or "") not in MOBILE_ONLY_TAPE_FAMILIES]
