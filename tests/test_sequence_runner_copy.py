"""Cal follow-up cadence copy: personalization must never produce broken grammar.

These are pure-function tests (no DB) pinning the template rendering so a null or
junk industry can't ship "the your industry teams..." to a real buyer.
"""
from __future__ import annotations

from app.services.sequence_runner import (
    DEFAULT_BUYER_SEQUENCE,
    _clean_industry,
    _render_template,
)
from app.services.agent_messaging import build_ladder_touch_body


class _Acct:
    def __init__(self, name, industry):
        self.name = name
        self.industry = industry


def test_clean_industry_maps_junk_to_neutral_phrase():
    for junk in [None, "", "Unknown", "unknown", "General Robotics", "other", "N/A"]:
        assert _clean_industry(junk) == "your industry"
    # Real industries pass through unchanged.
    assert _clean_industry("Logistics") == "Logistics"
    assert _clean_industry("Food Service") == "Food Service"


def test_render_template_fills_company_and_industry():
    acct = _Acct("Acme Foods", "Hospitality")
    out = _render_template("Hi {company_name} in {industry}", acct)
    assert out == "Hi Acme Foods in Hospitality"


def test_render_never_emits_broken_industry_grammar():
    # Production follow-ups render via ladder builders; each touch should include
    # the reminder identity line and never leak junk industry placeholders.
    for industry in [None, "Unknown", "General Robotics"]:
        rendered = build_ladder_touch_body("teach", "Acme", industry)
        assert "Quick reminder: I'm Cal from Ready For Robots" in rendered
        assert "{industry}" not in rendered
        assert "Unknown" not in rendered
        assert "your industry teams" not in rendered  # the old broken construction


def test_cadence_has_four_touches_and_cal_signoff():
    steps = DEFAULT_BUYER_SEQUENCE["steps"]
    assert [s["step_number"] for s in steps] == [1, 2, 3, 4]
    # Every follow-up is signed by Cal and interpolates cleanly.
    for s in steps:
        body = _render_template(s["body_template"], _Acct("Acme Foods", "Logistics"))
        assert "Cal" in body
        assert "{company_name}" not in body and "{industry}" not in body
