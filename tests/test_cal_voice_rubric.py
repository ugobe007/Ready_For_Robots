"""Stage 1 Cal voice rubric — golden passes, label-stack fails."""
from app.services.agent_messaging import build_buyer_variant_body
from app.services.cal_voice_rubric import score_cal_draft


def test_pfg_golden_passes_rubric_gate():
    body = build_buyer_variant_body(
        "Performance Food Group",
        "Food Distribution / Wholesale",
        "bottleneck_first",
    )
    result = score_cal_draft(body, company_hint="Performance Food Group")
    assert result.approved, result.to_dict()
    assert result.voice_total >= 24
    assert result.accuracy_pass
    assert result.human >= 4
    assert result.reasoning >= 4


def test_label_stack_fails_reasoning_and_insight():
    bad = """Hi PFG team,

I've been looking at food distribution.

Receiving. Replenishment. Moving pallets around. Inventory exceptions. Returns.

I'm curious if that's true at PFG.
"""
    result = score_cal_draft(bad, company_hint="Performance Food Group")
    assert result.insight <= 3 or result.reasoning <= 3
    assert any("label" in i.lower() for i in result.issues)
    assert any("stack" in r.lower() or "connect" in r.lower() for r in result.suggested_rules)


def test_billboard_and_no_intro_flagged():
    bad = """Hi team,

In food distribution / wholesale, operational pressure often shows up first in receiving.

You should buy an AMR this quarter.
"""
    result = score_cal_draft(bad, company_hint="Performance Food Group")
    assert not result.voice_pass or result.human <= 3 or result.restraint <= 3
    assert result.issues
