"""Required task models for a Robot Job.

A task model is the trained policy / skill pack for a specific physical job.
Hardware capability is not enough. Presence starts as ``unknown`` — we never
invent that a candidate carries a named model.

Internal nickname only: "certificate". Product and API term: task model.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.services import robot_ontology

# Tape families that uniquely imply a slot even without vertical keywords.
_SPECIFIC_TAPES = frozenset({"scrub", "inspect", "pallet"})

_FALLBACK_ID = "site_task_policy"

# Extra tokens that confirm a vertical when tape is generic (transport/gripper/cart).
_VERTICAL_TOKENS: dict[str, tuple[str, ...]] = {
    "warehouse": (
        "warehouse", "fulfillment", "distribution", "logistics", "pallet",
        "tote", "carton", "case", "sku", "dock", "aisle", "asin",
    ),
    "manufacturing": (
        "cnc", "lathe", "mill", "fixture", "workpiece", "machine tend",
        "machine-tend", "tending", "machining",
    ),
    "healthcare": (
        "hospital", "clinic", "patient", "nursing", "linen", "or suite",
        "clinical", "pharmacy",
    ),
    "commercial": ("scrub", "janitorial", "custodial", "floor clean"),
    "utilities": ("inspect", "patrol", "thermal", "leak"),
}


@lru_cache(maxsize=1)
def load_task_model_ontology() -> dict[str, Any]:
    return robot_ontology.task_model_ontology()


def task_model_slots() -> list[dict[str, Any]]:
    data = load_task_model_ontology()
    slots = data.get("slots") or data.get("slots") or []
    return [s for s in slots if s.get("id")]


def _haystack(*parts: str) -> str:
    return " ".join(p for p in parts if p).lower()


def _keyword_hit(slot: dict[str, Any], hay: str) -> bool:
    return any((k or "").lower() in hay for k in slot.get("keywords") or [] if k)


def _tape_families(slot: dict[str, Any]) -> set[str]:
    return {str(x).lower() for x in (slot.get("tape_families") or slot.get("tape_families") or [])}


def _tape_hit(slot: dict[str, Any], tape: str) -> bool:
    t = (tape or "").lower().strip()
    if not t:
        return False
    return t in _tape_families(slot)


def _vertical_hit(slot: dict[str, Any], hay: str) -> bool:
    vertical = (slot.get("vertical") or "").lower()
    if vertical in {"", "any"}:
        return False
    tokens = _VERTICAL_TOKENS.get(vertical) or (vertical,)
    return any(tok in hay for tok in tokens)


def _slot_matches(slot: dict[str, Any], *, tape: str, hay: str) -> bool:
    sid = slot.get("id") or ""
    if sid == _FALLBACK_ID:
        return False
    if _keyword_hit(slot, hay):
        return True
    if not _tape_hit(slot, tape):
        return False
    tape_l = (tape or "").lower().strip()
    # Transport + warehouse is AMR nav, not pick-and-place, unless pick keywords hit.
    if sid == "warehouse_pick_place_policy" and tape_l == "transport":
        return False
    if tape_l in _SPECIFIC_TAPES:
        return True
    return _vertical_hit(slot, hay)


def _lookups(slot: dict[str, Any]) -> list[dict[str, Any]]:
    rows = slot.get("where_to_look") or slot.get("where_to_look") or []
    out: list[dict[str, Any]] = []
    for dest in rows:
        out.append(
            {
                "kind": dest.get("kind") or "",
                "name": dest.get("name") or "",
                "url": dest.get("url"),
                "note": dest.get("note") or "",
            }
        )
    return out


def _serialize_slot(slot: dict[str, Any], *, presence: str = "unknown") -> dict[str, Any]:
    return {
        "id": slot.get("id") or "",
        "label": slot.get("label") or "",
        "physical_task": slot.get("physical_task") or slot.get("physical_task") or "",
        "vertical": slot.get("vertical") or "",
        "presence": presence,
        "hardware_not_enough": (
            slot.get("hardware_not_enough") or slot.get("hardware_not_enough") or ""
        ),
        "where_to_look": _lookups(slot),
    }


def required_task_models_for_job(
    *,
    tape_family: str = "",
    industry: str = "",
    title: str = "",
    path: str = "",
    text: str = "",
) -> list[dict[str, Any]]:
    """Slots this job requires. Presence is always unknown until evidence exists."""
    hay = _haystack(title, industry, path, text, tape_family)
    tape = (tape_family or "").lower().strip()
    hospital = any(tok in hay for tok in _VERTICAL_TOKENS["healthcare"])
    selected: list[dict[str, Any]] = []
    for slot in task_model_slots():
        if not _slot_matches(slot, tape=tape, hay=hay):
            continue
        if hospital and (slot.get("vertical") or "") == "warehouse" and not _keyword_hit(slot, hay):
            continue
        selected.append(_serialize_slot(slot))
    if selected:
        return selected
    fallback = next((s for s in task_model_slots() if s.get("id") == _FALLBACK_ID), None)
    if fallback:
        return [_serialize_slot(fallback)]
    return []


def task_model_open_questions(models: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for model in models:
        label = (model.get("label") or "task model").strip()
        presence = (model.get("presence") or "unknown").lower()
        if presence == "absent":
            out.append(
                f"This robot does not carry a {label.lower()} required for this job."
            )
        elif presence != "present":
            out.append(
                f"Which {label.lower()} covers this work, and where is it published?"
            )
    return out
