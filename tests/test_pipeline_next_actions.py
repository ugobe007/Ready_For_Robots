"""Pipeline next-actions ranking for home/pipeline right rails."""
from app.services.pipeline_next_actions import collect_pipeline_next_actions


def test_collect_pipeline_next_actions_ranks_hot_first():
    leads = [
        {
            "id": 1,
            "company_name": "Warm Co",
            "priority_tier": "WARM",
            "priority_score": 90,
            "pipeline_action": "Next: Review warm signals",
        },
        {
            "id": 2,
            "company_name": "Hot Co",
            "priority_tier": "HOT",
            "priority_score": 80,
            "pipeline_action": "Priority: Lead with AMR pilot",
        },
    ]
    actions = collect_pipeline_next_actions(leads, limit=3)
    assert len(actions) == 2
    assert actions[0]["companyName"] == "Hot Co"
    assert actions[0]["priority"] == "high"
    assert actions[0]["route"] == "/pipeline"
    assert actions[0]["entity_id"] == "2"


def test_collect_pipeline_next_actions_respects_limit():
    leads = [
        {"id": i, "company_name": f"Co {i}", "priority_tier": "HOT", "priority_score": 100 - i}
        for i in range(10)
    ]
    actions = collect_pipeline_next_actions(leads, limit=3)
    assert len(actions) == 3


def test_collect_pipeline_next_actions_skips_junk():
    leads = [
        {"id": 1, "company_name": "Good", "priority_tier": "HOT", "is_junk": True},
        {"id": 2, "company_name": "Also Good", "priority_tier": "WARM"},
    ]
    actions = collect_pipeline_next_actions(leads, limit=3)
    assert len(actions) == 1
    assert actions[0]["entity_id"] == "2"


def test_collect_pipeline_next_actions_prefers_humanoid_pilot():
    leads = [
        {
            "id": 1,
            "company_name": "Generic Hot",
            "priority_tier": "HOT",
            "priority_score": 95,
        },
        {
            "id": 2,
            "company_name": "Humanoid Buyer",
            "priority_tier": "WARM",
            "priority_score": 70,
            "humanoid_pilot_tier": "ACTIVE_PILOT",
            "humanoid_pilot_score": 90,
            "humanoid_pilot_action": "Lead with a narrow humanoid workcell pilot.",
        },
    ]
    actions = collect_pipeline_next_actions(leads, limit=2)
    assert actions[0]["companyName"] == "Humanoid Buyer"
    assert "Humanoid" in actions[0]["label"]


def test_collect_pipeline_next_actions_default_label():
    actions = collect_pipeline_next_actions(
        [{"id": 5, "company_name": "Mystery", "priority_tier": "COLD"}],
        limit=1,
    )
    assert actions[0]["label"] == "Monitor and qualify when timing improves"
    assert actions[0]["priority"] == "low"
