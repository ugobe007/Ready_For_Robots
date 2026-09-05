"""Frozen V1 domain enums — load from ontology/enums.v1.json."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_ENUMS_PATH = _ROOT / "ontology" / "enums.v1.json"
_LOSS_PATH = _ROOT / "ontology" / "loss_reasons.v1.json"
_PRIM_PATH = _ROOT / "ontology" / "primitives.v1.json"


@lru_cache(maxsize=1)
def load_enums() -> dict:
    return json.loads(_ENUMS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_loss_ontology() -> dict:
    return json.loads(_LOSS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_primitives_ontology() -> dict:
    return json.loads(_PRIM_PATH.read_text(encoding="utf-8"))


def truth_states() -> frozenset[str]:
    return frozenset(load_enums()["truth_states"])


def opportunity_states() -> frozenset[str]:
    return frozenset(load_enums()["opportunity_states"])


def dispositions() -> frozenset[str]:
    return frozenset(load_enums()["dispositions"])


def call_priorities() -> frozenset[str]:
    return frozenset(load_enums()["call_priorities"])


def commercial_maturity_states() -> frozenset[str]:
    return frozenset(load_enums()["commercial_maturity"])


def vendor_roles() -> frozenset[str]:
    return frozenset(load_enums()["vendor_roles"])


def vendor_types() -> frozenset[str]:
    return frozenset(load_enums()["vendor_types"])


def loss_reason_codes() -> frozenset[str]:
    return frozenset(r["code"] for r in load_loss_ontology()["reasons"])


def normalize_enum_token(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def assert_truth_state(value: str) -> str:
    token = normalize_enum_token(value)
    if token not in truth_states():
        raise ValueError(f"Unknown truth_state: {value}")
    return token  # type: ignore[return-value]


def assert_call_priority(value: str) -> str:
    token = normalize_enum_token(value)
    # Accept product uppercase labels
    aliases = {"do_not_surface": "do_not_surface", "unresolvable": "do_not_surface"}
    token = aliases.get(token or "", token)
    if token not in call_priorities():
        raise ValueError(f"Unknown call_priority: {value}")
    return token  # type: ignore[return-value]


def assert_loss_reason(value: str) -> str:
    token = normalize_enum_token(value)
    if token not in loss_reason_codes():
        raise ValueError(f"Unknown loss reason: {value}")
    return token  # type: ignore[return-value]


def assert_commercial_maturity(value: str) -> str:
    token = normalize_enum_token(value)
    if token not in commercial_maturity_states():
        raise ValueError(f"Unknown commercial_maturity: {value}")
    return token  # type: ignore[return-value]


def prediction_wrong_code() -> str:
    return "rfr_prediction_wrong"
