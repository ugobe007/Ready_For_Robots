"""Unit tests for market graph tension + match scoring (no DB)."""
from app.services.market_graph_loop import (
    CORE_LOOP_STAGES,
    build_knowledge_truth_layers,
    build_loop_stages,
    detect_tensions,
    industry_bucket,
    match_edge_score,
    propose_matches,
    tension_score,
)


def test_industry_bucket_maps_common_verticals():
    assert industry_bucket("Logistics & Warehousing (3PL)") == "logistics"
    assert industry_bucket("Hospitality (Hotel Management)") == "hospitality"
    assert industry_bucket("Healthcare (Hospital Systems)") == "healthcare"
    assert industry_bucket("") == "unknown"


def test_tension_score_rises_when_supply_is_thin():
    thin = tension_score(demand_count=20, hot_count=10, vendor_count=1, signal_strength=0.8)
    covered = tension_score(demand_count=20, hot_count=10, vendor_count=20, signal_strength=0.8)
    assert thin > covered
    assert thin >= 50


def test_detect_tensions_surfaces_actionable_verticals():
    demand = [
        {
            "company_id": i,
            "company_name": f"Buyer {i}",
            "industry": "Logistics",
            "bucket": "logistics",
            "tier": "HOT" if i < 4 else "WARM",
            "score": 80,
            "signal_types": ["labor_shortage", "expansion"],
        }
        for i in range(8)
    ]
    vendors = [
        {
            "manufacturer_id": "v1",
            "name": "Sparse Vendor",
            "primary_industries": ["Logistics"],
            "robot_categories": ["amr"],
            "buckets": ["logistics"],
        }
    ]
    tensions = detect_tensions(demand, vendors)
    assert tensions
    assert tensions[0]["bucket"] == "logistics"
    assert tensions[0]["tension_score"] > 0
    assert "actionable" in tensions[0]


def test_propose_matches_prefers_aligned_vendor():
    demand = [
        {
            "company_id": 1,
            "company_name": "Hotel Co",
            "industry": "Hospitality",
            "bucket": "hospitality",
            "tier": "HOT",
            "score": 90,
            "signal_types": ["labor_shortage"],
            "required_primitives": [],
            "workflow_family": "unknown",
            "work": {},
        }
    ]
    vendors = [
        {
            "manufacturer_id": "a",
            "name": "Hospitality Bot",
            "primary_industries": ["Hospitality", "Hotels"],
            "robot_categories": ["service"],
            "buckets": ["hospitality"],
            "supported_primitives": [],
        },
        {
            "manufacturer_id": "b",
            "name": "Mine Bot",
            "primary_industries": ["Mining"],
            "robot_categories": ["industrial"],
            "buckets": ["other"],
            "supported_primitives": [],
        },
    ]
    matches = propose_matches(demand, vendors, limit=5)
    assert matches
    assert matches[0]["manufacturer_name"] == "Hospitality Bot"
    assert matches[0]["match_score"] >= match_edge_score(
        buyer_industry="Hospitality",
        buyer_tier="HOT",
        buyer_score=90,
        vendor_industries=["Mining"],
        vendor_categories=["industrial"],
    )
    assert matches[0]["predicate"] == "MATCHES"
    assert matches[0]["truth_state"] == "SIGNAL_INFERRED"
    assert matches[0]["layer"] == "knowledge"
    assert 0 < matches[0]["confidence"] <= 1


def test_propose_matches_uses_primitive_spine_when_present():
    demand = [
        {
            "company_id": 2,
            "company_name": "Food Plant",
            "industry": "Food manufacturing",
            "bucket": "food",
            "tier": "HOT",
            "score": 88,
            "signal_types": ["labor_shortage"],
            "workflow_family": "strong_transport",
            "required_primitives": [
                "eng.acquire_pallet_floor",
                "man.lift_vertical",
                "tr.point_to_point",
                "plc.floor_place",
                "mob.navigate_indoor",
            ],
            "work": {
                "work_unit_id": "work:strong_transport:test",
                "workflow_family": "strong_transport",
            },
        }
    ]
    vendors = [
        {
            "manufacturer_id": "fork",
            "name": "Fork OEM",
            "primary_industries": ["Food"],
            "robot_categories": ["autonomous_forklift"],
            "buckets": ["food"],
            "supported_primitives": [
                "eng.acquire_pallet_floor",
                "man.lift_vertical",
                "tr.point_to_point",
                "plc.floor_place",
                "mob.navigate_indoor",
                "per.detect_pallet",
            ],
        },
        {
            "manufacturer_id": "tug",
            "name": "Tug OEM",
            "primary_industries": ["Food"],
            "robot_categories": ["autonomous_tugger"],
            "buckets": ["food"],
            "supported_primitives": [
                "eng.tow_hitch",
                "tr.line_replenishment",
                "mob.navigate_indoor",
            ],
        },
    ]
    matches = propose_matches(demand, vendors, limit=5)
    assert matches
    assert matches[0]["manufacturer_name"] == "Fork OEM"
    assert matches[0]["match_mode"] == "primitive_spine"
    assert matches[0]["work_match"] is not None
    assert matches[0]["work_match"] >= 70


def test_loop_stages_cover_canonical_observe_to_learn():
    stages = build_loop_stages(
        demand_count=10,
        vendor_count=5,
        tension_count=2,
        match_count=3,
        refresh_queue_count=4,
        researched=0,
    )
    assert tuple(stages.keys()) == CORE_LOOP_STAGES
    assert stages["OBSERVE"]["status"] == "completed"
    assert stages["MATCH"]["status"] == "completed"
    assert stages["ACT"]["status"] == "deferred"
    assert stages["LEARN"]["status"] == "partial"


def test_knowledge_truth_layers_split_beliefs_from_outcomes():
    layers = build_knowledge_truth_layers(
        demand=[{"company_id": 1}],
        vendors=[{"manufacturer_id": "a"}],
        matches=[{"match_score": 80}],
        tensions=[{"bucket": "logistics"}],
    )
    assert layers["knowledge"]["center"] == "WORK"
    assert layers["knowledge"]["inferred_match_edges"] == 1
    assert layers["truth"]["edges"] == []
    assert layers["truth"]["deployments"] == []
