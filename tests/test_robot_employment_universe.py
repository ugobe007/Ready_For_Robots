"""Gates for the robot employment universe (placeable labor roster)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "docs" / "calibration" / "robot_employment_taxonomy_v1.json"
UNIVERSE = ROOT / "docs" / "calibration" / "robot_employment_universe_v1.json"
WORKFLOW = ROOT / "ontology" / "workflow_ontology.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_taxonomy_has_nineteen_employment_categories():
    data = _load(TAXONOMY)
    cats = data["employment_categories"]
    assert len(cats) == 19
    ids = [c["id"] for c in cats]
    assert len(ids) == len(set(ids))
    assert "humanoids" in ids
    assert "construction" in ids
    assert data["target_companies"] == 200


def test_core_names_include_dusty_and_figure():
    data = _load(TAXONOMY)
    names: list[str] = []
    for cat in data["employment_categories"]:
        for raw in cat["companies"]:
            names.append(raw["name"] if isinstance(raw, dict) else str(raw))
    assert "Dusty Robotics" in names
    assert "Figure AI" in names
    assert "Boston Dynamics" in names


def test_compiled_universe_is_a_roster_not_a_directory():
    data = _load(UNIVERSE)
    assert data["company_count"] == 200
    assert data["core_company_count"] >= 120
    assert data["named_robot_count"] >= 200
    companies = data["companies"]
    assert len(companies) == 200
    names = [c["company_name"] for c in companies]
    assert len(names) == len(set(names))


def test_boston_dynamics_lists_named_placeable_robots():
    data = _load(UNIVERSE)
    row = next(c for c in data["companies"] if c["company_name"] == "Boston Dynamics")
    names = {r["name"] for r in row["robots"]}
    assert "Stretch" in names
    assert "Spot" in names
    assert "warehouse_logistics" in row["employment_categories"]
    assert "inspection_maintenance" in row["employment_categories"]
    stretch = next(r for r in row["robots"] if r["name"] == "Stretch")
    assert "trailer_unload" in stretch["work_families"]


def test_dusty_fieldprinter_is_construction_layout():
    data = _load(UNIVERSE)
    row = next(c for c in data["companies"] if c["company_name"] == "Dusty Robotics")
    names = [r["name"] for r in row["robots"]]
    assert names[0] == "FieldPrinter"
    assert row["robots"][0]["work_families"] == ["construction"]
    assert "construction" in row["employment_categories"]


def test_robot_names_are_at_most_three_and_not_generic_agv():
    data = _load(UNIVERSE)
    families = set((_load(WORKFLOW).get("families") or {}).keys())
    for company in data["companies"]:
        robots = company["robots"]
        assert len(robots) <= 3
        for robot in robots:
            name = (robot.get("name") or "").strip()
            assert name
            assert name.upper() not in {"AGV", "AMR", "AGV/AMR", "ROBOTS"}
            for fam in robot.get("work_families") or []:
                assert fam in families
            assert robot["name_source"] in {"vendor_index", "vendor_seed"}


def test_empty_robots_are_core_catalog_gaps():
    data = _load(UNIVERSE)
    empty = [c for c in data["companies"] if not c["robots"]]
    assert empty, "some core OEMs should still be unnamed rather than hallucinated"
    assert all(c["priority"] == "core" for c in empty)
    filled = [c for c in data["companies"] if c["priority"] == "fill"]
    assert filled
    assert all(c["robots"] for c in filled)


OVERLAY = ROOT / "docs" / "calibration" / "robot_workforce_registry_overlay_v1.json"


def test_workforce_registry_overlay_is_researcher_claim_not_catalog():
    overlay = _load(OVERLAY)
    assert overlay["kind"] == "researcher_overlay"
    assert overlay["n"] == 200
    assert len(overlay["rows"]) == 200
    assert overlay["dashboard_claims"]["available_for_work_now"] == 172
    assert overlay["dashboard_claims"]["rfr_verdict"] == "too_optimistic_not_placement_ready"
    for row in overlay["rows"]:
        assert row["epistemic"] == "researcher_claim"
        assert row["do_not_treat_as_catalog"] is True
        assert row["company"]
        assert row["claimed_product"]

    universe = _load(UNIVERSE)
    catalog_names = {
        robot["name"]
        for company in universe["companies"]
        for robot in company["robots"]
    }
    assert "UR Series" not in catalog_names
    assert "Dexterity AI Robots" not in catalog_names
    assert "Shelf-to-Person / Tote-to-Person" not in catalog_names
    assert "Cat MineStar Command" not in catalog_names
    for company in universe["companies"]:
        for robot in company["robots"]:
            assert robot["name_source"] in {"vendor_index", "vendor_seed"}
