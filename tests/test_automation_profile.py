"""Bench tests — automation profile engine (rules v1)."""
from types import SimpleNamespace

from app.services.automation_profile import (
    infer_automation_profile,
    profile_from_company_api_dict,
    get_automation_profile_for_response,
)


def test_nestle_like_food_beverage_packaging():
    p = infer_automation_profile(
        industry="Food & Beverage",
        company_name="Nestlé Example Division",
        signals=[
            {
                "signal_type": "packaging_automation",
                "raw_text": "End of line palletizing and case packing upgrade; evaluating Fanuc cells",
            },
            {"signal_type": "labor_shortage", "raw_text": "Pack out line staffing gaps"},
        ],
    )
    assert "end_of_line" in p.deployment_contexts or "factory_floor" in p.deployment_contexts
    assert "palletizing" in p.application_areas
    assert "packaging" in p.application_areas
    assert "articulated_industrial_arm" in p.robot_categories
    assert p.confidence in ("medium", "high")


def test_hotel_hospitality_mobile_service():
    p = infer_automation_profile(
        industry="Hospitality",
        company_name="Example Hotel Group",
        signals=[
            {"signal_type": "labor_shortage", "raw_text": "Room service and luggage delays; exploring service robots"},
            {"signal_type": "service_consistency", "raw_text": "Consistent delivery across shifts"},
        ],
    )
    assert "hospitality_guest_facing" in p.deployment_contexts
    assert "service_robot" in p.robot_categories
    assert "room_service_delivery" in p.application_areas or "food_delivery_mobile" in p.application_areas


def test_logistics_amr_signals():
    p = infer_automation_profile(
        industry="Logistics",
        company_name="3PL Partner",
        signals=[
            {"signal_type": "warehouse_throughput", "raw_text": "AMR fleet for sortation and pallet moves"},
        ],
    )
    assert "logistics_warehouse" in p.deployment_contexts
    assert "amr_amr_forklift" in p.robot_categories
    assert "sortation" in p.application_areas


def test_food_service_kiosk_prunes_logistics_defaults():
    p = infer_automation_profile(
        industry="Food Service",
        company_name="White Castle",
        signals=[
            {
                "signal_type": "expansion",
                "raw_text": "White Castle to set up 1,000 automated kiosks to sell sliders",
            },
        ],
    )
    assert "humanoid" in p.robot_categories
    assert "cobot" in p.robot_categories
    assert "food_prep_automation" in p.application_areas
    assert "amr_amr_forklift" not in p.robot_categories
    assert "agv" not in p.robot_categories


def test_aviation_humanoid_baggage_signal():
    p = infer_automation_profile(
        industry="Airports & Aviation",
        company_name="Japan Airlines",
        signals=[
            {
                "signal_type": "news",
                "raw_text": "Soon, humanoid robots will handle your baggage and clean aircraft at Tokyo Haneda Airport",
            },
        ],
    )
    assert "humanoid" in p.robot_categories
    assert "luggage_delivery" in p.application_areas
    assert "housekeeping_support" in p.application_areas


def test_cobot_keyword_sets_collaboration():
    p = infer_automation_profile(
        industry="Manufacturing",
        company_name="Small Parts Assembler",
        signals=[
            {"signal_type": "repetitive_process", "raw_text": "Deploying cobots alongside operators on line 3"},
        ],
    )
    assert "cobot" in p.robot_categories
    assert "cobot" in p.human_robot_collaboration.lower() or "collaborative" in p.human_robot_collaboration.lower()


def test_profile_from_api_dict_shape():
    lead = {
        "company_name": "Test Co",
        "industry": "Warehouse",
        "signals": [{"signal_type": "material_handling", "raw_text": ""}],
    }
    d = profile_from_company_api_dict(lead).to_dict()
    assert "deployment_contexts" in d
    assert "robot_categories" in d
    assert "application_areas" in d
    assert d["source"] == "rules_v1"


def test_get_automation_profile_for_response_uses_persisted_column():
    stored = {
        "source": "rules_v1",
        "deployment_contexts": ["factory_floor"],
        "robot_categories": ["cobot"],
        "application_areas": ["welding"],
        "human_robot_collaboration": "x",
        "sizing_notes": "y",
        "confidence": "high",
    }
    c = SimpleNamespace(
        automation_profile=stored,
        name="Other",
        industry="Other",
        signals=[],
    )
    assert get_automation_profile_for_response(c) is stored


def test_get_automation_profile_for_response_computes_when_missing():
    c = SimpleNamespace(
        automation_profile=None,
        name="Acme 3PL",
        industry="Logistics",
        signals=[],
    )
    d = get_automation_profile_for_response(c)
    assert d["source"] == "rules_v1"
    assert "logistics_warehouse" in d["deployment_contexts"] or "distribution_center" in d["deployment_contexts"]
