"""Assign a robot class from extracted facts. The model does not choose the class."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

RULES_PATH = Path(__file__).resolve().parent / "class_rules.json"


@lru_cache(maxsize=1)
def load_class_rules() -> dict[str, Any]:
    return json.loads(RULES_PATH.read_text())


def _values(table: dict[str, Any], match: dict[str, Any]) -> set[str]:
    if "values" in match:
        return set(match["values"])
    return set(table["groups"][match["group"]])


def _group(table: dict[str, Any], name: str) -> set[str]:
    return set(table["groups"][name])


def _matches(table: dict[str, Any], match: dict[str, Any], function: str, industries: set[str], form: str) -> bool:
    if "form" in match and form != match["form"]:
        return False
    if "function" in match and function != match["function"]:
        return False
    if "function_in" in match and function not in match["function_in"]:
        return False
    if match.get("industries") == "nonempty_subset" and not (industries and industries <= _values(table, match)):
        return False
    for name in match.get("intersects") or []:
        if not industries & _group(table, name):
            return False
    if "intersects_any" in match and not any(industries & _group(table, name) for name in match["intersects_any"]):
        return False
    for name in match.get("intersects_none") or []:
        if industries & _group(table, name):
            return False
    return True


def assign_class(
    primary_function: str | None,
    industries: list[str] | None,
    form: str | None,
) -> tuple[str | None, str, str]:
    """Return (class, rule_id, reason). Rule 21 has no class and needs review.

    The same facts always return the same result. Secondary functions are ignored.
    """
    table = load_class_rules()
    function = (primary_function or "").strip()
    form_value = (form or "").strip()
    industry_set = {item.strip() for item in (industries or []) if item and str(item).strip()}
    for rule in table["rules"]:
        match = rule["match"]
        if match == "else" or _matches(table, match, function, industry_set, form_value):
            return rule["class"], str(rule["id"]), str(rule["reason"])
    return None, "21", "Facts don't fit a rule"
