"""Employer MATCH: work language → named catalog robots.

Ontology MATCH on product class / work language. Never company → category → jobs.
Never invent SKUs. Empty is honest.
"""
from __future__ import annotations

import re
from typing import Any

from app.services.jobs_oem_listing import listing_from_catalog
from app.services.oem_sku_discover import is_junk_sku_name
from app.services.robot_class_qualify import (
    infer_class_from_work_language,
    lookup_class_id,
    normalize_class_id,
)
from app.services.oem_sku_catalog import name_key
from app.services.vendor_robot_lookup import load_vendor_robots_index

EMPTY_COPY = "No catalog robots for this work yet. Post the job so OEMs can find it."

# Work tile → robot classes that can do that work. MATCH, not a company dump.
WORK_TO_ROBOT_CLASSES: dict[str, frozenset[str]] = {
    "serving": frozenset({"serving"}),
    "cleaning": frozenset({"cleaning", "autonomous_scrubber", "cleaning_drone"}),
    "warehouse": frozenset({"warehouse", "amr", "logistics", "mobile_manipulator"}),
    "healthcare": frozenset({"healthcare"}),
    "food_prep": frozenset({"food_prep"}),
    "hospitality": frozenset({"hospitality", "serving"}),
    "logistics": frozenset({"logistics", "amr", "warehouse"}),
    "factory": frozenset({"factory", "cobot", "mobile_manipulator"}),
    "agriculture": frozenset({"agriculture", "agricultural_robot"}),
    "mining": frozenset({"mining"}),
    "construction": frozenset({"construction", "construction_robot"}),
    "marine": frozenset({"marine"}),
    "avionics": frozenset({"avionics", "drone", "evtol", "autonomous_aircraft"}),
    "aerospace": frozenset({"aerospace"}),
    "amr": frozenset({"amr", "warehouse", "logistics"}),
    "humanoid": frozenset({"humanoid"}),
    "cobot": frozenset({"cobot", "factory"}),
    "quadruped": frozenset({"quadruped"}),
    "mobile_manipulator": frozenset({"mobile_manipulator", "warehouse", "factory"}),
}

_TOKEN = re.compile(r"[a-z0-9]{3,}")


def _robot_class(row: dict[str, Any]) -> str | None:
    raw = (
        row.get("display_class")
        or row.get("primary_class")
        or row.get("listed_class")
        or ""
    )
    return lookup_class_id(str(raw)) or normalize_class_id(str(raw))


def _wanted_classes(work_class: str | None, description: str | None) -> set[str]:
    wanted: set[str] = set()
    cls = lookup_class_id(work_class) or normalize_class_id(work_class)
    if cls:
        wanted |= set(WORK_TO_ROBOT_CLASSES.get(cls, {cls}))
        wanted.add(cls)
    blob = (description or "").strip()
    if blob:
        inferred = infer_class_from_work_language(blob)
        if inferred:
            wanted |= set(WORK_TO_ROBOT_CLASSES.get(inferred, {inferred}))
            wanted.add(inferred)
    return {c for c in wanted if c}


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall((text or "").lower()))


def iter_catalog_robots() -> list[dict[str, Any]]:
    """Named catalog robots only. Deduped. Junk SKU names dropped."""
    index = load_vendor_robots_index()
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for vendor in index.get("vendors") or []:
        vendor_name = str(vendor.get("vendor_name") or "").strip()
        vendor_url = str(vendor.get("vendor_url") or "").strip() or None
        listed = listing_from_catalog(vendor)
        by_name = {
            name_key(str(r.get("name") or "")): r
            for r in (vendor.get("robots") or [])
            if r.get("name")
        }
        for row in listed:
            name = str(row.get("name") or "").strip()
            if not name or is_junk_sku_name(name):
                continue
            key = (name_key(vendor_name), name_key(name))
            if not key[1] or key in seen:
                continue
            seen.add(key)
            raw = by_name.get(name_key(name)) or {}
            product_url = str(raw.get("product_url") or "").strip() or vendor_url
            desc = str(row.get("description") or raw.get("description") or "").strip() or None
            cls = _robot_class({**raw, **row})
            out.append(
                {
                    "name": name,
                    "vendor_name": vendor_name or "Unknown OEM",
                    "vendor_url": vendor_url,
                    "robot_class": cls,
                    "description": desc,
                    "product_url": product_url,
                    "task": str(raw.get("task") or ""),
                    "setting": str(raw.get("setting") or ""),
                }
            )
    return out


def match_catalog_robots(
    *,
    work_class: str | None = None,
    description: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    wanted = _wanted_classes(work_class, description)
    if not wanted:
        return {
            "state": "empty",
            "robots": [],
            "robot_count": 0,
            "work_class": lookup_class_id(work_class),
            "empty_copy": EMPTY_COPY,
        }
    desc_tokens = _tokens(description or "")
    scored: list[tuple[float, dict[str, Any]]] = []
    for robot in iter_catalog_robots():
        cls = robot.get("robot_class")
        if cls not in wanted:
            continue
        score = 2.0
        blob = " ".join(
            x
            for x in (
                robot.get("description"),
                robot.get("task"),
                robot.get("setting"),
                robot.get("name"),
            )
            if x
        )
        if desc_tokens:
            overlap = desc_tokens & _tokens(blob)
            score += min(3.0, 0.4 * len(overlap))
        public = {
            "name": robot["name"],
            "vendor_name": robot["vendor_name"],
            "vendor_url": robot.get("vendor_url"),
            "robot_class": cls,
            "description": robot.get("description"),
            "product_url": robot.get("product_url"),
        }
        scored.append((score, public))
    scored.sort(key=lambda item: (-item[0], item[1]["name"].lower()))
    robots = [row for _, row in scored[: max(1, min(limit, 24))]]
    if not robots:
        return {
            "state": "empty",
            "robots": [],
            "robot_count": 0,
            "work_class": lookup_class_id(work_class),
            "empty_copy": EMPTY_COPY,
        }
    return {
        "state": "matches",
        "robots": robots,
        "robot_count": len(robots),
        "work_class": lookup_class_id(work_class),
        "empty_copy": None,
    }
