from app.services.plan_entitlements import (
    PLAN_ANONYMOUS,
    PLAN_FREE,
    PLAN_PAID,
    PIPELINE_LIMIT_ANONYMOUS,
    PIPELINE_LIMIT_FREE,
    PIPELINE_LIMIT_PAID,
    PIPELINE_LIMIT_PREVIEW,
    apply_pipeline_entitlements,
    pipeline_limit_for_plan,
    resolve_plan_tier,
    sanitize_lead_for_plan,
    saved_leads_limit_for_plan,
    trim_pipeline_leads_by_tier,
)


def test_resolve_plan_tier_anonymous():
    assert resolve_plan_tier(None) == PLAN_ANONYMOUS


def test_resolve_plan_tier_free_user():
    assert resolve_plan_tier({"email": "buyer@example.com"}) == PLAN_FREE


def test_resolve_plan_tier_paid_metadata():
    assert resolve_plan_tier({"email": "buyer@example.com", "plan_tier": "pro"}) == PLAN_PAID
    assert resolve_plan_tier({"email": "buyer@example.com", "plan_tier": "starter"}) == PLAN_FREE


def test_pipeline_limits():
    assert pipeline_limit_for_plan(PLAN_ANONYMOUS) == PIPELINE_LIMIT_ANONYMOUS
    assert pipeline_limit_for_plan(PLAN_FREE) == PIPELINE_LIMIT_FREE
    assert pipeline_limit_for_plan(PLAN_PAID) == PIPELINE_LIMIT_PAID
    assert PIPELINE_LIMIT_ANONYMOUS == 5
    assert PIPELINE_LIMIT_FREE == 15
    assert PIPELINE_LIMIT_PREVIEW == 15
    assert PIPELINE_LIMIT_PAID == 90


def test_trim_pipeline_leads_free_tier_caps_at_fifteen():
    leads = (
        [{"id": i, "priority_tier": "HOT"} for i in range(50)]
        + [{"id": 100 + i, "priority_tier": "WARM"} for i in range(40)]
        + [{"id": 200 + i, "priority_tier": "COLD"} for i in range(30)]
    )
    trimmed, mix = trim_pipeline_leads_by_tier(leads, PLAN_FREE)
    assert len(trimmed) == 15
    assert mix["hot"]["shown"] == 8
    assert mix["warm"]["shown"] == 5
    assert mix["monitoring"]["shown"] == 2
    assert mix["hot"]["cap"] == 8
    assert mix["warm"]["cap"] == 5
    assert mix["monitoring"]["cap"] == 2


def test_trim_pipeline_leads_by_tier_preserves_buckets():
    leads = (
        [{"id": i, "priority_tier": "HOT"} for i in range(50)]
        + [{"id": 100 + i, "priority_tier": "WARM"} for i in range(40)]
        + [{"id": 200 + i, "priority_tier": "COLD"} for i in range(30)]
    )
    trimmed, mix = trim_pipeline_leads_by_tier(leads, PLAN_PAID)
    assert len(trimmed) == 90
    assert mix["hot"]["shown"] == 40
    assert mix["warm"]["shown"] == 30
    assert mix["monitoring"]["shown"] == 20
    assert all(row["priority_tier"] == "HOT" for row in trimmed[:40])
    assert all(row["priority_tier"] == "WARM" for row in trimmed[40:70])
    assert all(row["priority_tier"] == "COLD" for row in trimmed[70:])


def test_trim_pipeline_anonymous_preview_includes_all_tiers():
    leads = (
        [{"id": i, "priority_tier": "HOT"} for i in range(50)]
        + [{"id": 100 + i, "priority_tier": "WARM"} for i in range(40)]
        + [{"id": 200 + i, "priority_tier": "COLD"} for i in range(30)]
    )
    trimmed, mix = trim_pipeline_leads_by_tier(leads, PLAN_ANONYMOUS)
    assert len(trimmed) == 5
    assert mix["hot"]["shown"] == 3
    assert mix["warm"]["shown"] == 2
    assert mix["monitoring"]["shown"] == 0


def test_trim_pipeline_anonymous_diversifies_hot_industries():
    leads = [
        {"id": i, "priority_tier": "HOT", "company_name": f"Hotel{i}", "industry": "Hospitality"}
        for i in range(40)
    ] + [
        {"id": 100, "priority_tier": "HOT", "company_name": "Warehouse Co", "industry": "Logistics"},
        {"id": 101, "priority_tier": "HOT", "company_name": "Clinic Co", "industry": "Healthcare"},
    ]
    trimmed, mix = trim_pipeline_leads_by_tier(leads, PLAN_ANONYMOUS)
    hot = [r for r in trimmed if r["priority_tier"] == "HOT"]
    industries = {r["industry"] for r in hot}
    assert "Logistics" in industries
    assert "Healthcare" in industries
    assert mix["hot"]["shown"] == 3


def test_trim_pipeline_anonymous_backfills_when_monitoring_sparse():
    leads = (
        [{"id": i, "priority_tier": "HOT"} for i in range(50)]
        + [{"id": 100 + i, "priority_tier": "WARM"} for i in range(40)]
    )
    trimmed, mix = trim_pipeline_leads_by_tier(leads, PLAN_ANONYMOUS)
    assert mix["monitoring"]["shown"] == 0
    assert len(trimmed) == 5


def test_trim_pipeline_drops_known_robot_vendors():
    leads = [
        {"id": 1, "priority_tier": "HOT", "company_name": "Boston Dynamics", "industry": "Robotics"},
        {"id": 2, "priority_tier": "HOT", "company_name": "Marriott Hotels", "industry": "Hospitality"},
        {"id": 3, "priority_tier": "WARM", "company_name": "Universal Robots", "industry": "Robotics"},
        {"id": 4, "priority_tier": "WARM", "company_name": "Hilton", "industry": "Hospitality"},
    ]
    trimmed, _ = trim_pipeline_leads_by_tier(leads, PLAN_ANONYMOUS)
    names = {r["company_name"] for r in trimmed}
    assert "Boston Dynamics" not in names
    assert "Universal Robots" not in names
    assert "Marriott Hotels" in names
    assert "Hilton" in names


def test_apply_pipeline_entitlements_trims_and_tags():
    feed = {
        "summary": {"hot": 40, "warm": 10, "total": 100},
        "leads": [
            {"id": i, "company_name": f"Hot Co {i}", "priority_tier": "HOT", "share_summary": "secret"}
            for i in range(20)
        ]
        + [
            {"id": 100 + i, "company_name": f"Warm Co {i}", "priority_tier": "WARM", "share_summary": "secret"}
            for i in range(20)
        ],
    }
    out = apply_pipeline_entitlements(feed, PLAN_FREE)
    # Free workspace shows 15 customer opportunities; Pro unlocks the full 90-lead feed.
    assert len(out["leads"]) == 15
    assert out["entitlements"]["plan"] == PLAN_FREE
    assert out["entitlements"]["pipeline_limit"] == 15
    assert out["entitlements"]["tier_mix"]["hot"]["shown"] == 8
    assert out["entitlements"]["tier_mix"]["warm"]["shown"] == 5
    assert out["entitlements"]["tier_mix"]["monitoring"]["shown"] == 0
    assert "share_summary" in out["leads"][0]


def test_apply_pipeline_entitlements_paid_keeps_full_feed():
    feed = {
        "summary": {"hot": 40, "warm": 30, "total": 100},
        "leads": (
            [{"id": i, "company_name": f"Hot Co {i}", "priority_tier": "HOT"} for i in range(40)]
            + [{"id": 100 + i, "company_name": f"Warm Co {i}", "priority_tier": "WARM"} for i in range(30)]
            + [{"id": 200 + i, "company_name": f"Cold Co {i}", "priority_tier": "COLD"} for i in range(20)]
        ),
    }
    out = apply_pipeline_entitlements(feed, PLAN_PAID)
    assert len(out["leads"]) == 90
    assert out["entitlements"]["pipeline_limit"] == 90
    assert out["entitlements"]["tier_mix"]["hot"]["shown"] == 40


def test_trim_pipeline_drops_headline_style_news_rows():
    leads = [
        {
            "id": 1,
            "priority_tier": "HOT",
            "company_name": "Los Gatos hotel seized through swift foreclosure as market wobbles - The Mercury News.",
            "industry": "Hospitality",
        },
        {
            "id": 2,
            "priority_tier": "HOT",
            "company_name": "Hilton",
            "industry": "Hospitality",
        },
    ]
    trimmed, _ = trim_pipeline_leads_by_tier(leads, PLAN_FREE)
    names = {r["company_name"] for r in trimmed}
    assert "Los Gatos hotel seized through swift foreclosure as market wobbles - The Mercury News." not in names
    assert "Hilton" in names


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


def test_plan_feature_flags():
    from app.services.plan_entitlements import plan_feature_flags, user_workspace_entitlements

    assert plan_feature_flags(PLAN_PAID)["research_updates"] is True
    assert plan_feature_flags(PLAN_FREE)["research_updates"] is False
    assert plan_feature_flags(PLAN_ANONYMOUS)["full_lead_intel"] is False

    anon = user_workspace_entitlements(None)
    assert anon["plan"] == PLAN_ANONYMOUS
    assert anon["saved_limit"] == 0

    free = user_workspace_entitlements({"email": "buyer@example.com", "uid": "00000000-0000-0000-0000-000000000001"})
    assert free["plan"] == PLAN_FREE
    assert free["display_name"] == "Free workspace"
    assert free["saved_limit"] == 5
