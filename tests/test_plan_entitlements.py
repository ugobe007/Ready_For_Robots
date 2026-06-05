from app.services.plan_entitlements import (
    PLAN_ANONYMOUS,
    PLAN_FREE,
    PLAN_PAID,
    apply_pipeline_entitlements,
    pipeline_limit_for_plan,
    resolve_plan_tier,
    sanitize_lead_for_plan,
    saved_leads_limit_for_plan,
)


def test_resolve_plan_tier_anonymous():
    assert resolve_plan_tier(None) == PLAN_ANONYMOUS


def test_resolve_plan_tier_free_user():
    assert resolve_plan_tier({"email": "buyer@example.com"}) == PLAN_FREE


def test_resolve_plan_tier_paid_metadata():
    assert resolve_plan_tier({"email": "buyer@example.com", "plan_tier": "pro"}) == PLAN_PAID
    assert resolve_plan_tier({"email": "buyer@example.com", "plan_tier": "starter"}) == PLAN_FREE


def test_pipeline_limits():
    assert pipeline_limit_for_plan(PLAN_ANONYMOUS) == 12
    assert pipeline_limit_for_plan(PLAN_FREE) == 25
    assert pipeline_limit_for_plan(PLAN_PAID) == 50


def test_apply_pipeline_entitlements_trims_and_tags():
    feed = {
        "summary": {"hot": 40, "warm": 10, "total": 100},
        "leads": [{"id": i, "company_name": f"C{i}", "share_summary": "secret"} for i in range(30)],
    }
    out = apply_pipeline_entitlements(feed, PLAN_FREE)
    assert len(out["leads"]) == 25
    assert out["entitlements"]["plan"] == PLAN_FREE
    assert "share_summary" in out["leads"][0]


def test_sanitize_anonymous_keeps_scout_teaser():
    lead = {
        "company_name": "Acme",
        "share_summary": "x" * 300,
        "lead_highlights": {
            "specific_problem": "y" * 300,
            "why_lead": ["reason one", "reason two", "reason three"],
            "robot_categories": ["AMR", "cobot", "cleaning"],
        },
        "robot_types_needed": ["AMR", "arm", "drone"],
        "signals": [{"display_text": "z" * 250, "source_url": "https://example.com"}],
    }
    row = sanitize_lead_for_plan(lead, PLAN_ANONYMOUS)
    assert "share_summary" in row
    assert len(row["share_summary"]) <= 240
    assert row["lead_highlights"]["why_lead"] == ["reason one", "reason two"]
    assert row["robot_types_needed"] == ["AMR", "arm", "drone"]
    assert "source_url" not in row["signals"][0]
    assert len(row["signals"][0]["display_text"]) <= 200


def test_saved_limit_free():
    assert saved_leads_limit_for_plan(PLAN_FREE) == 5
    assert saved_leads_limit_for_plan(PLAN_PAID) is None
