from types import SimpleNamespace

from app.api.crm import _draft_buyer_body


def test_buyer_draft_is_human_and_not_template_slop():
    acct = SimpleNamespace(name="Americold Realty Trust", industry="Logistics")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "nice to meet you" in low
    assert "i am a robot coordinator" in low
    assert "at americold realty trust" in low
    assert "may i send them to you for review?" in low
    assert "i've been looking" not in low


def test_buyer_draft_strips_recommended_action_suffix_from_name():
    acct = SimpleNamespace(
        name="Americold Realty Trust -- contact new executive with ROI-focused pitch",
        industry="Logistics",
    )
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)

    assert "ROI-focused pitch" not in body
    assert "contact new executive" not in body
    assert "at Americold Realty Trust" in body


def test_hospitality_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="MGM Resorts International", industry="Hospitality")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i am a robot coordinator" in low
    assert "at mgm resorts international" in low
    assert "may i send them to you for review?" in low


def test_healthcare_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="LifePoint Health", industry="Healthcare")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i am a robot coordinator" in low
    assert "at lifepoint health" in low
    assert "may i send them to you for review?" in low


def test_food_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="Clemens Food Group", industry="Food Service")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i am a robot coordinator" in low
    assert "at clemens food group" in low
    assert "may i send them to you for review?" in low
