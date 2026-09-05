"""Regression: v1 facts extraction grounds autonomous item delivery/transport.

A hospitality/healthcare delivery robot (Relay, Keenon, Pudu) is a transport
robot. Its page describes delivering/transporting items point-to-point; the
extractor must ground `claims_item_delivery` so the matcher can serve it
transport/cart work instead of returning 0 jobs.
"""
from __future__ import annotations

from app.services.robot_understanding_v1.facts import _extract_from_page
from app.services.robot_understanding_v1.models import RobotSource


def _source() -> RobotSource:
    return RobotSource(
        id="s0",
        url="https://relayrobotics.com/",
        source_type="product",
        fetched_at="2026-08-18T00:00:00Z",
        title="Relay Delivery Robots",
        confidence=0.85,
    )


def _preds(text: str, subject: str = "Relay") -> set[str]:
    facts = _extract_from_page(_source(), text, subject=subject, page_url="https://relayrobotics.com/", page_title="Relay Delivery Robots")
    return {f.predicate for f in facts if f.epistemic != "unknown"}


def test_delivery_robot_grounds_item_delivery():
    text = (
        "Relay is a reliable, autonomous delivery robot. Relay robots safely and reliably "
        "transport items—medications, lab samples, and guest amenities. They "
        "autonomously navigate crowded hallways, security doors, and elevators and "
        "deliver room service items in hotels."
    )
    preds = _preds(text)
    assert "claims_item_delivery" in preds
    assert "product_class" in preds  # service_robot / delivery robot
    assert "autonomous_navigation" in preds


def test_item_delivery_not_grounded_by_generic_copy():
    # No item-delivery claim → must not ground it (avoid false positives).
    text = (
        "Our humanoid robot has two dexterous arms and can carry out complex assembly "
        "operations on the factory floor. It delivers results and value to customers."
    )
    # "delivers results/value" is not item delivery; "carry out operations" is not carrying items.
    assert "claims_item_delivery" not in _preds(text, subject="")


def test_warehouse_tote_transport_still_distinct():
    # Warehouse tote handling remains its own predicate (not item delivery).
    text = "Origin is a person-to-goods AMR for warehouse transport that handles totes."
    preds = _preds(text, subject="Origin")
    assert "claims_warehouse_transport" in preds or "supports_tote_handling" in preds
