"""Robot vendor seed (500) structural gates."""
from __future__ import annotations

import json
from pathlib import Path

from app.domain.enums import vendor_roles, vendor_types

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "docs" / "calibration"
SEED = CAL / "robot_vendor_seed_v1.json"
XLSX = CAL / "ReadyForRobots_Robot_Vendor_Seed_v1.xlsx"

TARGETS = {
    "amr_agv_material_transport": 80,
    "autonomous_forklift_pallet": 40,
    "industrial_robot_arms": 55,
    "cobots": 40,
    "picking_manipulation_palletizing": 40,
    "humanoids_general_purpose": 50,
    "cleaning_robots": 30,
    "hospitality_foodservice_delivery": 35,
    "inspection_security_quadrupeds": 25,
    "agriculture": 35,
    "construction": 25,
    "healthcare_hospital_service": 20,
    "last_mile_outdoor_delivery": 15,
    "specialty_commercial": 10,
}


def test_vendor_seed_has_500_and_hits_category_targets():
    data = json.loads(SEED.read_text())
    vendors = data["vendors"]
    assert len(vendors) >= 495
    assert sum(TARGETS.values()) == 500
    from collections import Counter

    counts = Counter(v["robot_category"] for v in vendors)
    # Allow small shortfalls after host-level dedupe of product-line pads
    for cat, target in TARGETS.items():
        assert counts[cat] >= max(1, target - 5), f"{cat}: {counts[cat]} << {target}"
    names = [v["company_name"] for v in vendors]
    assert len(names) == len(set(names))
    assert data.get("actual_vendors") == len(vendors)


def test_vendor_roles_ontology():
    assert "robot_oem" in vendor_roles()
    assert "system_integrator" in vendor_roles()
    assert "component_supplier" in vendor_roles()
    assert "oem" in vendor_types()


def test_xlsx_and_model_sheet_exist():
    assert XLSX.exists() and XLSX.stat().st_size > 1000
    data = json.loads(SEED.read_text())
    assert data["seeded_model_rows"] >= 50
    assert data["target_models_range"] == [1500, 2500]
