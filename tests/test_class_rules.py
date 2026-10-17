"""The class table is deterministic and agrees with the frozen answer keys."""

from scripts.check_class_rules import DEFAULT_KEYS, check
from app.services.robot_understanding_v1.class_rules import assign_class


def test_frozen_keys_stay_73_of_73():
    ok, total, bad = check(list(DEFAULT_KEYS))
    assert (ok, total, bad) == (73, 73, [])


def test_model_guess_is_stored_and_rule_21_has_no_class():
    from app.services.robot_understanding_v1.taxonomy_extraction import _assign_product_class

    clinical = _assign_product_class(
        {
            "model_class_suggestion": "delivery",
            "primary_class": None,
            "primary_function": {"value": "delivery_transport"},
            "form": {"value": "mobile_manipulator"},
            "industries": [{"value": "hospital"}],
        }
    )
    assert clinical["model_class_suggestion"] == "delivery"
    assert clinical["primary_class"]["value"] == "healthcare"
    assert clinical["class_rule_id"] == "3"
    assert clinical["needs_review"] is False

    unmatched = _assign_product_class(
        {
            "primary_class": {"value": "service_robot"},
            "primary_function": {"value": "general_purpose"},
            "form": {"value": "amr_mobile_robot"},
            "industries": [{"value": "hotel"}],
        }
    )
    assert unmatched["primary_class"] is None
    assert unmatched["needs_review"] is True
    assert unmatched["class_rule_id"] == "21"
    assert unmatched["model_class_suggestion"] == "service_robot"
    assert unmatched["class_rule_reason"] == "Facts don't fit a rule"


def test_same_facts_always_assign_the_same_class():
    import json

    seen = []
    for path in DEFAULT_KEYS:
        data = json.loads(path.read_text())
        for row in (data.get("products") or []) + (data.get("robots") or []):
            functions = row.get("functions_required") or []
            if not functions:
                continue
            industries = (row.get("industries_required") or []) + (row.get("industries_any") or [])
            form = (row.get("form_ok") or [None])[0]
            first = assign_class(functions[0], industries, form)
            second = assign_class(functions[0], list(industries), form)
            assert first == second
            seen.append(first)
    assert seen
    assert assign_class(None, [], None) == (None, "21", "Facts don't fit a rule")
    assert assign_class("delivery_transport", ["hospital"], "mobile_manipulator")[0] == "healthcare"


def test_dealership_delivery_is_logistics_rule_17():
    klass, rule_id, reason = assign_class(
        "delivery_transport",
        ["automotive_dealership"],
        "amr_mobile_robot",
    )
    assert klass == "amr_logistics"
    assert rule_id == "17"
    assert "dealership" in reason


def test_dealership_does_not_change_other_functions():
    klass, rule_id, _reason = assign_class(
        "picking_packing_palletizing",
        ["automotive_dealership"],
        "amr_mobile_robot",
    )
    assert rule_id == "16"
    assert klass == "amr_logistics"

    klass, rule_id, _reason = assign_class(
        "general_purpose",
        ["automotive_dealership"],
        "amr_mobile_robot",
    )
    assert rule_id == "21"
    assert klass is None


def test_dealership_plus_hotel_stays_delivery():
    klass, rule_id, _reason = assign_class(
        "delivery_transport",
        ["automotive_dealership", "hotel"],
        "amr_mobile_robot",
    )
    assert rule_id == "18"
    assert klass == "delivery"
