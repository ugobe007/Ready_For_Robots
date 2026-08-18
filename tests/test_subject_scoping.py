"""Multi-product subject scoping: a selected product must not inherit a sibling
product's capabilities from a shared multi-product site.

Regression for Bear Robotics: researching "Servi" (a serving robot) used to
inherit scrubbing/cleaning from the company's "Servi Clean" floor-cleaner page,
because that page carries "Servi" in its nav/name (prefix collision).
"""
from __future__ import annotations

from types import SimpleNamespace

from app.services.robot_understanding_v1.facts import filter_facts_to_subject
from app.services.robot_understanding_v1.models import RobotFact


def _src(sid: str, url: str, text: str, title: str = ""):
    return SimpleNamespace(
        source=SimpleNamespace(id=sid, url=url, title=title),
        page=SimpleNamespace(final_url=url, title=title, text=text),
    )


def _fact(pred, value, sid, ev):
    return RobotFact.create("Servi", pred, value, source_id=sid, epistemic="explicit",
                            confidence=0.9, evidence_span=ev)


def _pack():
    servi = _src(
        "s_servi", "https://www.bearrobotics.ai/servi",
        "Servi is a restaurant robot server. Servi runs food and drinks to tables and "
        "delivers meals to guests across the dining room.",
        title="Servi: Hospitality's Best AI Robot Waiter",
    )
    clean = _src(
        "s_clean", "https://www.bearrobotics.ai/servi-clean",
        "Servi Clean and Servi Clean Max are commercial floor cleaning robots. This robot "
        "scrubber makes hard surfaces sparkle with floor scrubbing and mopping.",
        title="Commercial floor cleaning robots: Servi Clean",
    )
    return [servi, clean]


def _facts():
    return [
        _fact("claims_item_delivery", True, "s_servi", "runs food and drinks to tables"),
        _fact("supports_hard_floor_scrubbing", True, "s_clean", "floor scrubbing"),
        _fact("claims_surface_cleaning", True, "s_clean", "commercial floor cleaning robots"),
        _fact("product_class", "cleaning_robot", "s_clean", "floor cleaning robots"),
    ]


def test_multi_product_drops_sibling_capabilities():
    kept, dropped = filter_facts_to_subject(_facts(), _pack(), subject="Servi", multi_product=True)
    preds = {(f.predicate, str(f.value)) for f in kept}
    # Servi's own serving/delivery survives.
    assert ("claims_item_delivery", "True") in preds
    # The Servi Clean page's cleaning capabilities are NOT attributed to Servi.
    assert ("supports_hard_floor_scrubbing", "True") not in preds
    assert ("claims_surface_cleaning", "True") not in preds
    assert ("product_class", "cleaning_robot") not in preds
    assert dropped >= 3


def test_single_product_company_keeps_permissive_behaviour():
    # multi_product=False → no proximity/sibling-page gating (single-product sites
    # often state capabilities without repeating the product name).
    kept, dropped = filter_facts_to_subject(_facts(), _pack(), subject="Servi", multi_product=False)
    preds = {f.predicate for f in kept}
    assert "supports_hard_floor_scrubbing" in preds
    assert "claims_item_delivery" in preds
