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
    "hospitality": (
        "kitchen", "restaurant", "cafe", "hotel", "dining", "espresso",
        "barista", "dishwasher", "hospitality", "cafeteria",
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


def _dest(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": row.get("kind") or "",
        "name": row.get("name") or "",
        "url": row.get("url"),
        "note": row.get("note") or "",
    }


def _merge_lookups(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in groups:
        for row in group:
            dest = _dest(row)
            key = dest["name"].lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(dest)
    return out


def _catalog(key: str) -> list[dict[str, Any]]:
    rows = load_task_model_ontology().get(key) or []
    return [r for r in rows if isinstance(r, dict)]


def _lookups(slot: dict[str, Any]) -> list[dict[str, Any]]:
    slot_rows = slot.get("where_to_look") or slot.get("where_to_look") or []
    return _merge_lookups(list(slot_rows), _catalog("shared_lookups"))


def _filter(row: dict[str, Any]) -> dict[str, Any]:
    label = row.get("label") or row.get("name") or ""
    return {
        "id": row.get("id") or "",
        "kind": row.get("kind") or row.get("id") or "",
        "name": label,
        "label": label,
        "url": row.get("url"),
        "note": row.get("note") or "",
    }


def _time_band(ont: dict[str, Any], band_id: str) -> dict[str, Any]:
    for row in ont.get("training_time_bands") or []:
        if row.get("id") == band_id:
            return {
                "id": row.get("id") or "",
                "label": row.get("label") or "",
                "meaning": row.get("meaning") or "",
            }
    return {"id": band_id or "", "label": band_id or "", "meaning": ""}


def _layer(ont: dict[str, Any], layer_id: str) -> dict[str, Any]:
    for row in ont.get("model_layers") or []:
        if row.get("id") == layer_id:
            return {
                "id": row.get("id") or "",
                "label": row.get("label") or "",
                "note": row.get("note") or "",
            }
    return {"id": layer_id or "", "label": layer_id or "", "note": ""}


def _contract(slot: dict[str, Any], ont: dict[str, Any]) -> dict[str, Any]:
    data = ont.get("data_contract") or {}
    pricing = ont.get("pricing_contract") or {}
    field = pricing.get("field_feedback") or {}
    you_provide = [
        {"id": row.get("id") or "", "label": row.get("label") or "", "examples": row.get("examples") or ""}
        for row in (data.get("you_provide") or [])
        if isinstance(row, dict)
    ]
    layer_id = slot.get("layer") or "site_adapted"
    band_id = slot.get("typical_time_band") or "2_to_8_weeks"
    return {
        "layer": _layer(ont, str(layer_id)),
        "who_trains": list(slot.get("who_trains") or []),
        "time_band": _time_band(ont, str(band_id)),
        "you_provide": you_provide,
        "field_feedback": {
            "automatic_rebate": bool(field.get("automatic_rebate")),
            "note": field.get("note") or "",
        },
    }


_LAYER_LIST_LABEL = {
    "foundation_vla": "Foundation VLA",
    "task_library": "Task library",
    "site_adapted": "Site-adapted",
}


def format_task_model_contract(slot_or_model: dict[str, Any]) -> dict[str, Any]:
    """Job Card copy: list burden + placement steps. No invented dollars."""
    contract = slot_or_model.get("contract") or {}
    layer = contract.get("layer") or {}
    time_band = contract.get("time_band") or {}
    who = [w.replace("_", " ") for w in (contract.get("who_trains") or []) if w]
    provide = [row.get("label") for row in (contract.get("you_provide") or []) if row.get("label")]
    who_s = " + ".join(who) if who else "OEM / integrator"
    layer_id = str(layer.get("id") or "")
    layer_short = _LAYER_LIST_LABEL.get(layer_id) or (layer.get("label") or "Task model").split("/")[0].strip()
    time_label = time_band.get("label") or "2–8 weeks"
    slot_label = (slot_or_model.get("label") or "").strip() or "this work"
    provide_s = ", ".join(provide).lower() if provide else "site map, object geometry, demo traces, SOP"
    rebate = "Field traces do not automatically reduce the model price unless the OEM contract says so."
    return {
        "headline": "To place this job",
        "layer": f"Layer: {(layer.get('label') or 'Task model').strip()}",
        "who_trains": f"Who trains: {who_s}",
        "time": f"Typical time: {time_label} after a map and demo traces exist",
        "you_provide": f"You provide: {provide_s}",
        "field_feedback": rebate,
        "list_line": f"{layer_short} · {time_label} · {who_s}",
        "steps": [
            {
                "n": 1,
                "label": "Name the slot",
                "body": slot_label,
            },
            {
                "n": 2,
                "label": "License a task-library pack",
                "body": "Ask the OEM which pack covers this SKU class. Do not train a foundation VLA.",
            },
            {
                "n": 3,
                "label": "Budget site adapt",
                "body": f"{who_s} · typical {time_label}",
            },
            {
                "n": 4,
                "label": "Bring workplace data",
                "body": provide_s,
            },
            {
                "n": 5,
                "label": "Qualify on this workplace",
                "body": "A checkpoint is not qualified until this site says so.",
            },
            {
                "n": 6,
                "label": "Write the field-data clause",
                "body": rebate,
            },
        ],
    }


def _serialize_slot(slot: dict[str, Any], *, presence: str = "unknown") -> dict[str, Any]:
    ont = load_task_model_ontology()
    contract = _contract(slot, ont)
    return {
        "id": slot.get("id") or "",
        "label": slot.get("label") or "",
        "physical_task": slot.get("physical_task") or slot.get("physical_task") or "",
        "vertical": slot.get("vertical") or "",
        "presence": presence,
        "hardware_not_enough": (
            slot.get("hardware_not_enough") or slot.get("hardware_not_enough") or ""
        ),
        "candidate_families": list(ont.get("candidate_families") or []),
        "where_to_look": _lookups(slot),
        "qualify_filters": [_filter(r) for r in _catalog("qualify_filters")],
        "pricing_lookups": [_dest(r) for r in _catalog("pricing_lookups")],
        "contract": contract,
        "card_contract": format_task_model_contract(
            {"label": slot.get("label") or "", "contract": contract}
        ),
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


_SHARED_OPEN_QUESTIONS = (
    "Is a candidate policy a robot VLA or OEM pack — not a chat LLM?",
    "Which task-library pack covers this work, and who trains the site-adapted layer?",
    "Does the license allow commercial placement on this robot?",
    "Will you provide a site map, object geometry, and demo traces? Field data does not automatically cut the model price.",
)


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
    if models:
        for question in _SHARED_OPEN_QUESTIONS:
            if question not in out:
                out.append(question)
    return out
