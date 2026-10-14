"""Form must fit the work (buyer_opportunity_spec v1.3 §6 step 5), current flow only.

Work that moves through a building needs a robot that moves. A SKU the vendor
index records as stationary (`has_mobile_base: false`) never gets those jobs.
Phase 2 replaces this with the config-driven compatibility table.
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


def is_stationary_sku(robot: dict[str, Any] | None) -> bool:
    for claim in (robot or {}).get("catalog_claims") or []:
        if isinstance(claim, dict) and claim.get("predicate") == "has_mobile_base":
            return claim.get("value") is False or claim.get("value") == "false"
    return False


def jobs_fit_form(jobs: Iterable[dict[str, Any]], *, stationary: bool) -> list[dict[str, Any]]:
    rows = list(jobs)
    if not stationary:
        return rows
    return [j for j in rows if (j.get("tape_family") or "") not in MOBILE_ONLY_TAPE_FAMILIES]
