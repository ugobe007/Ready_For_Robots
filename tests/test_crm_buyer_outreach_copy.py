from types import SimpleNamespace

from app.api.crm import _draft_buyer_body


def test_buyer_draft_is_human_and_not_template_slop():
    acct = SimpleNamespace(name="Americold Realty Trust", industry="Logistics")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert body.startswith("Hi Americold Realty Trust,")
    assert "i've been following" not in low
    assert "worth a quick reply if you're the right person to explore this" not in low
    assert "vendor-neutral" in low
    assert "could you point me to the right contact" in low


def test_buyer_draft_strips_recommended_action_suffix_from_name():
    acct = SimpleNamespace(
        name="Americold Realty Trust -- contact new executive with ROI-focused pitch",
        industry="Logistics",
    )
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)

    assert "ROI-focused pitch" not in body
    assert body.startswith("Hi Americold Realty Trust,")


def test_hospitality_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="MGM Resorts International", industry="Hospitality")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i work with hospitality teams on one thing" in low
    assert "real weekend occupancy" in low
    assert "housekeeping turnover" in low
    assert "housekeeping and turnover workflow recommendation" in low
    assert "i've been watching labor" not in low


def test_healthcare_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="LifePoint Health", industry="Healthcare")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i work with healthcare ops teams on one thing" in low
    assert "reduce staff miles" in low
    assert "evs" in low
    assert "elevator access" in low
    assert "evs and transport workflow recommendation" in low
    assert "i've had lifepoint health on my radar" not in low


def test_food_variant_matches_new_rewrite_style():
    acct = SimpleNamespace(name="Clemens Food Group", industry="Food Service")
    body = _draft_buyer_body(acct, settings=None, traits=[], collateral_policy="none", collateral_links=None)
    low = body.lower()

    assert "i work with food teams on one thing" in low
    assert "changeover headaches" in low
    assert "oee" in low
    assert "changeover and oee-focused workflow recommendation" in low
    assert "i noticed operational signals" not in low
