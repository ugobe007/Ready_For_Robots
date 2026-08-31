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
    FIND_TILE_CLASSES,
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
    assert by.get("PuduBot 2") == "serving", by
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
    assert by.get("T8") == "serving" or by.get("Keenon T8") == "serving", by
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
    assert "Seer Humanoid" not in names
    assert "AMR scrubbers" not in names
    assert map_primary_class("Commercial", "Bipedal humanoid") == "humanoid"
    assert map_primary_class("Commercial", "Cleaning drone") == "cleaning_drone"


def test_lucidbots_is_cleaning_drone_not_floor_scrubber():
    sherpa = (
        "Sherpa Drone commercial cleaning drone for windows, facades and exteriors. "
        "Window washing drone. Exterior building washing. Not a floor scrubber."
    )
    assert classify_product_from_evidence(sherpa, "service_robot") == "cleaning_drone"
    assert classify_product_from_evidence(sherpa, "cleaning") == "cleaning_drone"
    assert prefer_work_language_class(sherpa, "avionics", name="Sherpa Drone") == "cleaning_drone"

    payload = listing_payload_for_url("https://www.lucidbots.com/")
    assert payload["matched"] is True
    by = {r["name"]: r.get("display_class") for r in payload["robots"]}
    assert by.get("Sherpa Drone") == "cleaning_drone", by
    assert "autonomous_scrubber" not in by.values()
    assert all(c != "avionics" for c in by.values()), by


def test_pudu_bellabot_serving_vs_cc1_cleaning():
    by = _by_class("https://www.pudurobotics.com/en")
    assert by["BellaBot"] == "serving"
    assert by["CC1"] == "cleaning"
    assert by["BellaBot"] != by["CC1"]


def test_keenon_waiter_vs_cleaner_live_names():
    by = _by_class("https://www.keenon.com/en")
    waiter = by.get("Dinerbot T10") or by.get("T11") or by.get("Dinerbot T5")
    cleaner = by.get("C55") or by.get("Keenon C30") or by.get("C40")
    assert waiter == "serving", by
    assert cleaner == "cleaning", by


def test_bear_servi_serving_and_servi_clean_cleaning():
    payload = listing_payload_for_url("https://www.bearrobotics.ai/")
    assert payload["matched"] is True
    by = {r["name"]: r.get("display_class") for r in payload["robots"]}
    assert by.get("Servi") == "serving", by
    assert by.get("Servi Plus") == "serving", by
    assert by.get("Servi Clean") == "cleaning", by
    rng = set(payload["product_range"])
    assert "serving" in rng and "cleaning" in rng
    assert payload["mixed_range"] is True


def test_gausium_avidbots_ecovacs_commercial_are_floor_cleaning():
    gau = _by_class("https://gausium.com/")
    assert gau.get("Phantas") in {"cleaning", "autonomous_scrubber"}, gau
    assert gau.get("Marvel") in {"cleaning", "autonomous_scrubber"} or "cleaning" in set(gau.values()), gau
    assert all(c not in {"cleaning_drone", "avionics"} for c in gau.values()), gau

    avid = _by_class("https://avidbots.com/")
    assert avid.get("Neo") in {"cleaning", "autonomous_scrubber"}, avid
    assert avid.get("Kas") in {"cleaning", "autonomous_scrubber"} or "cleaning" in set(avid.values()), avid
    assert all(c not in {"cleaning_drone", "avionics"} for c in avid.values()), avid

    eco = listing_payload_for_url("https://www.ecovacscommercial.com/")
    assert eco["matched"] is True
    eco_by = {r["name"]: r.get("display_class") for r in eco["robots"]}
    assert eco_by.get("DEEBOT PRO M1") == "cleaning", eco_by
    assert eco_by.get("DEEBOT PRO K1 VAC") == "cleaning", eco_by
    assert all(c != "cleaning_drone" for c in eco_by.values()), eco_by


def test_pringle_mixed_serving_and_cleaning_range():
    payload = listing_payload_for_url("https://pringlerobotics.ai/")
    assert payload["matched"] is True
    by = {r["name"]: r.get("display_class") for r in payload["robots"]}
    assert by.get("BellaBot") == "serving", by
    assert by.get("CC1") == "cleaning", by
    assert payload["mixed_range"] is True


def test_cleaning_drone_is_configuration_not_find_tile():
    assert "cleaning_drone" not in FIND_TILE_CLASSES
    assert "serving" in FIND_TILE_CLASSES and "cleaning" in FIND_TILE_CLASSES
    assert len(FIND_TILE_CLASSES) == 20


def test_kaercher_overlay_is_robotic_kira_not_mop_skus():
    import json

    data = json.loads(MIXED_OEM_CATALOG_PATH.read_text(encoding="utf-8"))
    kaercher = next(c for c in data["companies"] if c["slug"] == "karcher")
    names = [p["name"] for p in kaercher["products"]]
    assert names == ["KIRA B 50", "KIRA B 200", "KIRA CV 50", "KIRA CV 60/1"]
    assert all(p["primary_class"] in {"cleaning", "cleaning_robot"} for p in kaercher["products"])
    blob = " ".join(names).lower()
    assert "fc 7" not in blob
    assert "sc 3" not in blob


def test_tennant_and_seer_named_robots_not_class_dumps():
    import json

    data = json.loads(MIXED_OEM_CATALOG_PATH.read_text(encoding="utf-8"))
    slugs = {c["slug"] for c in data["companies"]}
    assert "tennant" in slugs
    assert "seer-robotics" in slugs
    names = [p["name"] for c in data["companies"] for p in c["products"]]
    assert "AMR scrubbers" not in names
    assert "Seer Humanoid" not in names
    tennant = listing_payload_for_url("https://www.tennantco.com/en_us.html")
    tennant_names = [r["name"] for r in tennant.get("robots") or []]
    assert "AMR scrubbers" not in tennant_names
    assert "X6 ROVR" in tennant_names
    assert "T7AMR" in tennant_names
    assert all(r.get("display_class") == "cleaning" for r in tennant["robots"])
    seer = listing_payload_for_url("https://seer-robotics.ai/")
    seer_names = [r["name"] for r in seer.get("robots") or []]
    assert "Seer Humanoid" not in seer_names
    assert "AMB-300JZ" in seer_names
    assert "SFL-CBD15" in seer_names
    by = {r["name"]: r.get("display_class") for r in seer["robots"]}
    assert by["AMB-300JZ"] == "amr"
    assert by["SFL-CBD15"] == "amr"
    assert by.get("SRC-880") is None


def test_vinmotion_named_robots_from_page_evidence():
    import json

    data = json.loads(MIXED_OEM_CATALOG_PATH.read_text(encoding="utf-8"))
    vin = next(c for c in data["companies"] if c["slug"] == "vinmotion")
    names = [p["name"] for p in vin["products"]]
    assert names == ["Motion 1", "Motion 2"]
    assert "VinMotion Humanoid" not in names
    assert "Product" not in names
    payload = listing_payload_for_url("https://vinmotion.net/")
    assert payload["matched"] is True
    by = {r["name"]: r.get("display_class") for r in payload["robots"]}
    assert by["Motion 1"] == "humanoid"
    assert by.get("Motion 2") is None, by
    assert "Product" not in by
    assert "humanoid" in set(payload["product_range"])
    assert payload["mixed_range"] is False


def test_vinmotion_product_hrefs_and_next_f_menu():
    from app.services.oem_sku_discover import (
        classify_href_candidate,
        next_f_product_candidates,
    )

    m1 = "https://vinmotion.net/product/motion-1"
    m2 = "https://vinmotion.net/product/motion-2"
    assert classify_href_candidate(m1, "Motion 1") == "product"
    assert classify_href_candidate(m2, "Motion 2") == "product"
    assert classify_href_candidate("https://vinmotion.net/product", "Product") != "product"
    html = (
        'self.__next_f.push([1,"{\\"ProductMenu\\":{\\"ProductPageSlug\\":\\"/product\\",'
        '\\"ProductMenuItem\\":[{\\"Title\\":\\"Motion 1\\",\\"product_post\\":{\\"title\\":'
        '\\"Motion 1\\",\\"slug\\":\\"motion-1\\"}},{\\"Title\\":\\"Motion 2\\",'
        '\\"product_post\\":{\\"title\\":\\"Motion 2\\",\\"slug\\":\\"motion-2\\"}}]}}"])'
    )
    found = next_f_product_candidates(html, "https://vinmotion.net/")
    by = {row["name"]: row["url"] for row in found}
    assert by["Motion 1"] == m1
    assert by["Motion 2"] == m2
    assert "Product" not in by
    assert "VinMotion Humanoid" not in by


def test_more_oems_named_robots_from_page_evidence():
    payload_by = {
        "https://booster.tech": listing_payload_for_url("https://booster.tech"),
        "https://lumosbot.tech": listing_payload_for_url("https://lumosbot.tech"),
        "https://galbot.com": listing_payload_for_url("https://galbot.com"),
        "https://unix-group.ai": listing_payload_for_url("https://unix-group.ai"),
        "https://noetixrobotics.com/en": listing_payload_for_url("https://noetixrobotics.com/en"),
        "https://primebot.cn": listing_payload_for_url("https://primebot.cn"),
        "https://limxdynamics.com/en": listing_payload_for_url("https://limxdynamics.com/en"),
    }
    booster = {r["name"]: r.get("display_class") for r in payload_by["https://booster.tech"]["robots"]}
    assert booster["Booster K1"] == "humanoid"
    assert booster["Booster T1"] == "humanoid"
    assert booster["Booster T2"] == "humanoid"
    lumos = {r["name"]: r.get("display_class") for r in payload_by["https://lumosbot.tech"]["robots"]}
    assert lumos["Lumos LUS 2"] == "humanoid"
    assert lumos["Lumos NIX S3"] == "humanoid"
    assert lumos.get("Lumos MOS 2") is None, lumos
    assert lumos.get("Lumos LUD") is None, lumos
    assert "Lumos Motor" not in lumos
    galbot = {r["name"]: r.get("display_class") for r in payload_by["https://galbot.com"]["robots"]}
    assert "Galbot G1" in galbot
    assert "Galbot S1" in galbot
    assert "Galbot G2" not in galbot
    assert galbot.get("Galbot G1") is None, galbot
    assert galbot.get("Galbot S1") is None, galbot
    unix = {r["name"]: r.get("display_class") for r in payload_by["https://unix-group.ai"]["robots"]}
    assert unix["Wanda 2.0"] == "humanoid"
    assert unix["Panther"] == "humanoid"
    assert unix["Martian"] == "humanoid"
    assert "Wheeled" not in unix
    noetix = {r["name"]: r.get("display_class") for r in payload_by["https://noetixrobotics.com/en"]["robots"]}
    assert noetix["Bumi"] == "humanoid"
    assert noetix["N2"] == "humanoid"
    assert noetix["E1"] == "humanoid"
    prime = {r["name"]: r.get("display_class") for r in payload_by["https://primebot.cn"]["robots"]}
    assert prime["Q1"] == "humanoid"
    assert "Qiyuan T1" not in prime
    limx = {r["name"]: r.get("display_class") for r in payload_by["https://limxdynamics.com/en"]["robots"]}
    assert limx["Luna"] == "humanoid"
    assert limx["Oli"] == "humanoid"
    assert limx["TRON 1"] == "humanoid"
    assert limx.get("TRON 2") is None, limx
    empty = listing_payload_for_url("https://thirdwave.ai")
    names = [r["name"] for r in empty.get("robots") or []]
    assert "TWA Reach" not in names
    dexory = listing_payload_for_url("https://dexory.com")
    dnames = [r["name"] for r in dexory.get("robots") or []]
    assert "DexoryView" not in dnames
    assert "Powered by AI" not in dnames


def test_more_oem_product_hrefs():
    from app.services.oem_sku_discover import classify_href_candidate

    assert classify_href_candidate("https://www.booster.tech/booster-t2", "Booster T2") == "product"
    assert classify_href_candidate("https://www.lumosbot.tech/products/lus2", "Lumos LUS 2") == "product"
    assert classify_href_candidate("https://www.unix-group.ai/Wanda", "Wanda 2.0") == "product"
    assert classify_href_candidate("https://www.limxdynamics.com/en/products/tron1", "TRON 1") == "product"


def test_tennant_robotic_product_url_is_a_named_sku():
    from app.services.oem_sku_discover import (
        classify_href_candidate,
        tennant_robotic_sku_from_url,
    )
    from app.services.robot_understanding_v1.resolve import _sku_from_product_href

    x6 = "https://www.tennantco.com/en_us/1/machines/scrubbers/product.x6-rovr.autonomous-floor-scrubber.m-x6rovr.html"
    mop = "https://www.tennantco.com/en_us/1/machines/scrubbers/product.t7.ride-on-floor-scrubber.2000074.html"
    assert tennant_robotic_sku_from_url(x6) == "X6 ROVR"
    assert tennant_robotic_sku_from_url(mop) is None
    assert classify_href_candidate(x6, "X6 ROVR") == "product"
    assert _sku_from_product_href(x6) == "X6 ROVR"
    assert _sku_from_product_href(mop) is None


def test_discovered_sku_does_not_inherit_sibling_class():
    from app.services.oem_sku_discover import make_discovered_product

    company = {
        "slug": "pudu-robotics",
        "name": "Pudu Robotics",
        "domains": ["pudurobotics.com"],
        "products": [{"name": "BellaBot", "primary_class": "serving"}],
    }
    row = make_discovered_product(
        company, "PUDUA1", "https://www.pudurobotics.com/en/products/puduA1"
    )
    assert row["primary_class"] == "service_robot"
    assert row["primary_class"] != "serving"
    assert row["task"] is None
    assert row["listed_class"] is None


def test_pudu_thin_skus_are_not_dumped_to_serving():
    by = _by_class("https://www.pudurobotics.com/en")
    assert by["BellaBot"] == "serving"
    assert by["CC1"] == "cleaning"
    assert by["D9"] == "humanoid"
    assert by.get("PUDUA1") is None, by
    assert by.get("PUDUD1") is None, by
    assert by.get("PUDUSH1") is None, by
