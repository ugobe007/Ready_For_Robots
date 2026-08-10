"""Unit tests for market graph tension + match scoring (no DB)."""
from app.services.market_graph_loop import (
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
        }
    ]
    vendors = [
        {
            "manufacturer_id": "a",
            "name": "Hospitality Bot",
            "primary_industries": ["Hospitality", "Hotels"],
            "robot_categories": ["service"],
            "buckets": ["hospitality"],
        },
        {
            "manufacturer_id": "b",
            "name": "Mine Bot",
            "primary_industries": ["Mining"],
            "robot_categories": ["industrial"],
            "buckets": ["other"],
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
