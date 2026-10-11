from types import SimpleNamespace

from app.api.crm import _draft_buyer_body


def test_buyer_draft_is_human_and_not_template_slop():
    acct = SimpleNamespace(name="Americold Realty Trust", industry="Logistics")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert body.startswith("Hi Americold")
    assert "i research how companies are using robotics" in low
    assert "i've been looking" in low
    assert "i'd be interested in your perspective" in low
    assert "vendor-neutral" not in low
    assert "robot coordinator" in low


def test_buyer_draft_strips_recommended_action_suffix_from_name():
    acct = SimpleNamespace(
        name="Americold Realty Trust -- contact new executive with ROI-focused pitch",
        industry="Logistics",
    )
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)

    assert "ROI-focused pitch" not in body
    assert "contact new executive" not in body
    assert body.startswith("Hi Americold")


def test_hospitality_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="MGM Resorts International", industry="Hospitality")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i research how companies are using robotics" in low
    assert "housekeeping" in low
    assert "i'd be interested in your perspective" in low
    assert "vendor-neutral" not in low


def test_healthcare_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="LifePoint Health", industry="Healthcare")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i research how companies are using robotics" in low
    assert "between floors" in low
    assert "i'd be interested in your perspective" in low
    assert "vendor-neutral" not in low


def test_food_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="Clemens Food Group", industry="Food Service")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i research how companies are using robotics" in low
    assert "changeover" in low
    assert "i'd be interested in your perspective" in low
    assert "vendor-neutral" not in low
