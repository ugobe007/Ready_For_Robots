"""URL submit match: score OEM profile against equally scored buyer opportunities."""

from app.api.robot_ready import (
    URL_MATCHED_ANONYMOUS_LIMIT,
    URL_MATCHED_PIPELINE_LIMIT,
    match_companies,
    url_matched_limit_for_plan,
)
from app.services.plan_entitlements import PLAN_ANONYMOUS, PLAN_FREE, PLAN_PAID


class _FakeSession:
    pass


def test_url_matched_pipeline_limit_is_fifteen():
    assert URL_MATCHED_PIPELINE_LIMIT == 15
    assert URL_MATCHED_ANONYMOUS_LIMIT == 5
    assert url_matched_limit_for_plan(PLAN_ANONYMOUS) == 5
    assert url_matched_limit_for_plan(PLAN_FREE) == 15
    assert url_matched_limit_for_plan(PLAN_PAID) == 15


def test_match_companies_prefers_score_parity(monkeypatch):
    robot_caps = {
        "type": "AMR",
        "use_case": "Warehouse Automation",
        "capabilities": ["payload", "navigation", "fleet"],
        "profile_score": 70,
    }
    candidates = [
        {
            "id": 1,
            "company_name": "Far Intent Co",
            "industry": "Logistics / Warehousing",
            "location_city": "Dallas",
            "location_state": "TX",
            "employee_estimate": 500,
            "priority_tier": "HOT",
            "priority_score": 90,
            "priority_reasons": ["expansion"],
            "overall_intent_score": 95,
            "signal_count": 2,
            "signals": [{"signal_type": "expansion", "display_text": "New warehouse expansion"}],
        },
        {
            "id": 2,
            "company_name": "Parity Fit Co",
            "industry": "Logistics / Warehousing",
            "location_city": "Austin",
            "location_state": "TX",
            "employee_estimate": 400,
            "priority_tier": "WARM",
            "priority_score": 72,
            "priority_reasons": ["labor"],
            "overall_intent_score": 68,
            "signal_count": 2,
            "signals": [{"signal_type": "labor_shortage", "display_text": "Warehouse labor shortage"}],
        },
        {
            "id": 3,
            "company_name": "Unrelated Low Fit",
            "industry": "Software",
            "location_city": "SF",
            "location_state": "CA",
            "employee_estimate": 100,
            "priority_tier": "COLD",
            "priority_score": 20,
            "priority_reasons": [],
            "overall_intent_score": 20,
            "signal_count": 0,
            "signals": [],
        },
    ]

    monkeypatch.setattr(
        "app.api.robot_ready._get_fresh_lead_candidate_index",
        lambda _db: candidates,
    )

    matches = match_companies(robot_caps, _FakeSession())
    assert len(matches) <= URL_MATCHED_PIPELINE_LIMIT
    assert matches, "expected at least one match"
    assert matches[0]["id"] == 2
    assert matches[0]["score_parity_gap"] <= abs(95 - 70)
    assert all(m.get("robot_profile_score") == 70 for m in matches)
