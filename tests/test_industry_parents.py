import json
from pathlib import Path

import pytest

from app.services.robot_understanding_v1 import industries as ind
from app.services.robot_understanding_v1.taxonomy_extraction import load_taxonomy, taxonomy_values
from scripts.benchmark_scoring_v2 import score_industries

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ANSWER_KEYS = (
    "robot_benchmark_set.v2.json",
    "robot_holdout_set.v1.json",
    "robot_holdout_set.v2.json",
    "robot_oem_richtech_set.v1.json",
)
KEY_FIELDS = {
    "offering_type_ok": "offering_type",
    "form_ok": "form",
    "primary_class_ok": "primary_class",
    "functions_required": "functions",
    "functions_ok": "functions",
    "industries_required": "industries",
    "industries_any": "industries",
    "industries_must_not": "industries",
    "industries_ok_extra": "industries",
}


def test_taxonomy_is_v1_3_with_valid_parents():
    taxonomy = load_taxonomy()
    assert taxonomy["version"] == "v1.3"
    assert "_definition" not in taxonomy["primary_class"]
    assert "facility_services" in taxonomy_values(taxonomy, "industries")
    known = set(taxonomy_values(taxonomy, "industries"))
    parents = ind.industry_parents(taxonomy)
    assert parents == {"bar_nightclub": "restaurant", "surgery_center": "hospital", "k12_school": "college_university"}
    assert set(parents) <= known and set(parents.values()) <= known
    assert "surgical_assistance" in taxonomy_values(taxonomy, "functions")


@pytest.mark.parametrize("name", ANSWER_KEYS)
def test_answer_keys_use_only_taxonomy_values(name):
    taxonomy = load_taxonomy()
    data = json.loads((FIXTURES / name).read_text())
    entries = [e for g in ("robots", "products", "taxonomy_gap_probes", "negative_controls") for e in data.get(g) or []]
    assert entries
    bad = [
        (e.get("id"), key, value)
        for e in entries
        for key, section in KEY_FIELDS.items()
        for value in e.get(key) or []
        if value not in taxonomy_values(taxonomy, section)
    ]
    assert bad == []


def test_richtech_set_has_eight_products():
    data = json.loads((FIXTURES / "robot_oem_richtech_set.v1.json").read_text())
    assert sorted(p["target_product"] for p in data["products"]) == sorted([
        "ADAM", "Scorpion", "Matradee Plus", "Titan", "Pallet Jack", "DUST-E MX", "DUST-E S", "Dex",
    ])


def test_child_satisfies_parent_in_required_and_any():
    ok, _, details = score_industries(["bar_nightclub"], ["restaurant"], [], [], [])
    assert ok and details["counted_as_parent"] == ["restaurant"] and details["unexpected"] == []
    ok, _, _ = score_industries(["surgery_center"], [], ["hospital", "senior_living"], [], [])
    assert ok


def test_parent_does_not_satisfy_child():
    ok, reason, _ = score_industries(["restaurant"], ["bar_nightclub"], [], [], [])
    assert not ok and "bar_nightclub" in reason


def test_child_is_forbidden_where_parent_is():
    ok, reason, _ = score_industries(["surgery_center"], [], [], ["hospital"], [])
    assert not ok and "hospital" in reason


def test_unrelated_extra_is_still_unexpected():
    ok, _, details = score_industries(["bar_nightclub", "airport"], ["restaurant"], [], [], [])
    assert ok and details["unexpected"] == ["airport"]


def test_pilot_groups_use_taxonomy_values_and_spec_order():
    assert ind.invalid_pilot_values() == []
    assert [rank for rank, _, _ in ind.PILOT_INDUSTRY_GROUPS] == list(range(1, 10))


@pytest.mark.parametrize("industry,group", [
    ("bar_nightclub", (6, "Restaurants and bars")),
    ("surgery_center", (4, "Hospitals")),
    ("3pl", (1, "Warehouse, logistics, 3PL")),
    ("corporate_campus", (8, "Office buildings and facility services")),
    ("facility_services", (8, "Office buildings and facility services")),
    ("automotive_dealership", (9, "Auto dealerships")),
])
def test_pilot_group_membership(industry, group):
    assert ind.pilot_group(industry) == group


@pytest.mark.parametrize("industry", [
    "k12_school", "college_university", "transportation_transit",
    "residential_consumer", "construction",
])
def test_hidden_industries(industry):
    assert not ind.is_pilot_industry(industry)


def test_child_reaches_pilot_group_through_parent_only():
    taxonomy = {"industries": {}, "industry_parents": {"rooftop_bar": "bar_nightclub", "bar_nightclub": "restaurant"}}
    assert ind.with_parents(["rooftop_bar"], taxonomy) == {"rooftop_bar", "bar_nightclub", "restaurant"}
    assert ind.pilot_group("rooftop_bar", taxonomy) == (6, "Restaurants and bars")
