"""Mixed OEM product RANGE: named SKUs keep their own class.

PUDU / Keenon / UBTech / AgiBot / MagicLab / Deep Robotics ship humanoids,
serving robots, cleaning robots, and/or quadrupeds. FIND must not collapse
the company hub to one class (service_robot) or invent SKUs.
Does not import fetch/facts (agent-verify pytest-only venv has no requests).
"""
from __future__ import annotations

from app.services.jobs_oem_listing import (
    listing_from_catalog,
    listing_payload_for_url,
    product_range_classes,
)
from app.services.oem_sku_catalog import MIXED_OEM_CATALOG_PATH, map_primary_class
from app.services.robot_class_qualify import (
    classify_product_from_evidence,
    prefer_work_language_class,
)
from app.services.vendor_robot_lookup import (
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)


def setup_function():
    reload_vendor_robots_index()


def _by_class(url: str) -> dict[str, str]:
    vendor = lookup_vendor_by_url(url)
    assert vendor is not None, url
    return {
        r["name"]: r.get("display_class") for r in listing_from_catalog(vendor)
    }


def test_evidence_strings_split_serving_cleaning_humanoid():
    waiter = (
        "BellaBot tray delivery restaurant waiter. Table service and food running. "
        "Dining room bussing. Restaurants."
    )
    scrubber = (
        "CC1 vacuuming, scrubbing, mopping. Commercial floors. "
        "Floor cleaning janitor in public venues."
    )
    walker = (
        "Walker bipedal humanoid robot. Walking on two legs. Object manipulation."
    )
    kleen = (
        "KLEENBOT C55 sweeping and washing commercial floors. "
        "Scrubbing and mopping. Floor cleaner."
    )
    diner = (
        "DINERBOT T11 catering delivery. Narrow-aisle tray delivery. Restaurants."
    )
    agibot = "AGIBOT G1 universal embodied intelligent humanoid robot."
    magic = "MagicBot X1 humanoid robot. Bipedal patrol."
    dog = "MagicDog bionic quadruped robot dog. Patrol on four legs."
    assert prefer_work_language_class(waiter, "service_robot") == "serving"
    assert prefer_work_language_class(scrubber, "service_robot") == "cleaning"
    assert classify_product_from_evidence(walker, "service_robot") == "humanoid"
    assert classify_product_from_evidence(kleen, "service_robot") == "cleaning"
    assert classify_product_from_evidence(diner, "service_robot") == "serving"
    assert classify_product_from_evidence(agibot, "service_robot") == "humanoid"
    assert classify_product_from_evidence(magic, "service_robot") == "humanoid"
    assert classify_product_from_evidence(dog, "service_robot") == "quadruped"
    assert classify_product_from_evidence("Thin SKU with no work copy.", "service_robot") is None


def test_pudu_hub_range_is_serving_cleaning_and_humanoid():
    payload = listing_payload_for_url("https://www.pudurobotics.com/en")
    assert payload["matched"] is True
    by = {r["name"]: r.get("display_class") for r in payload["robots"]}
    assert by["BellaBot"] == "serving"
    assert by["CC1"] == "cleaning"
    assert by["D9"] == "humanoid"
    assert by["BellaBot"] != by["CC1"]
    assert "service_robot" not in {by["BellaBot"], by["CC1"], by["D9"]}
    rng = set(payload["product_range"])
    assert {"serving", "cleaning", "humanoid"} <= rng
    assert payload["mixed_range"] is True
    assert "en" not in {n.lower() for n in by}
    assert "About" not in by


def test_keenon_waiter_vs_cleaner():
    by = _by_class("https://www.keenon.com/")
    assert by.get("Dinerbot T5") == "serving", by
    assert by.get("T11") == "serving", by
    assert by.get("Keenon C30") == "cleaning", by
    assert by.get("C55") == "cleaning", by
    rng = set(product_range_classes(listing_from_catalog(lookup_vendor_by_url("https://www.keenon.com/"))))
    assert "serving" in rng and "cleaning" in rng


def test_ubtech_walker_is_humanoid_not_waiter():
    by = _by_class("https://www.ubtrobot.com/")
    walker = by.get("Walker") or by.get("UBTECH Walker")
    walker_x = by.get("Walker X") or by.get("UBTECH Walker X")
    assert walker == "humanoid", by
    assert walker_x == "humanoid", by
    assert walker != "serving"
    assert walker != "service_robot"


def test_agibot_and_magiclab_humanoid_not_waiter():
    agi = _by_class("https://www.agibot.com/")
    assert agi, agi
    assert all(c == "humanoid" for c in agi.values()), agi
    assert any("g1" in n.lower() or "x2" in n.lower() or "a2" in n.lower() for n in agi), agi

    magic = _by_class("https://www.magiclab.top/")
    assert magic, magic
    human = [n for n, c in magic.items() if c == "humanoid"]
    dogs = [n for n, c in magic.items() if c == "quadruped"]
    assert human, magic
    assert dogs, magic
    assert not any(c == "serving" for c in magic.values())


def test_deeprobotics_quadruped_and_humanoid_range():
    payload = listing_payload_for_url("https://www.deeprobotics.cn/")
    assert payload["matched"] is True
    by = {r["name"]: r.get("display_class") for r in payload["robots"]}
    quadruped = [n for n, c in by.items() if c == "quadruped"]
    humanoid = [n for n, c in by.items() if c == "humanoid"]
    assert any("x20" in n.lower() or "x30" in n.lower() for n in quadruped), by
    assert any("dr02" in n.lower() for n in humanoid), by
    assert payload["mixed_range"] is True
    assert {"quadruped", "humanoid"} <= set(payload["product_range"])


def test_mixed_overlay_file_does_not_invent_skus():
    import json

    data = json.loads(MIXED_OEM_CATALOG_PATH.read_text(encoding="utf-8"))
    names = [
        p["name"]
        for c in data["companies"]
        for p in c["products"]
    ]
    forbidden = {"About", "News", "en", "Imprint", "Product", "Farmers"}
    assert forbidden.isdisjoint(names)
    assert "PuduBot 3" not in names
    assert map_primary_class("Commercial", "Bipedal humanoid") == "humanoid"
