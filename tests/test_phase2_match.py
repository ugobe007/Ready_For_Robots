"""Phase 2 matches the submitted product. A sibling from the same maker is not a result."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.buyer_opportunity.phase2_match import (
    buyer_opportunities_enabled,
    classified_match_payload,
    discover_product_pages,
    jobs_for_classification,
    try_phase2_search,
    url_names_product,
)


def _fact(value: str) -> dict:
    return {"value": value, "confidence": 0.9, "evidence": value}


def _product(
    name: str,
    *,
    form: str,
    function: str,
    industries: list[str],
    primary_class: str,
    company: str = "Richtech Robotics",
) -> dict:
    return {
        "company": company,
        "product_name": name,
        "offering_type": _fact("robot_product"),
        "form": _fact(form),
        "primary_class": _fact(primary_class),
        "primary_function": _fact(function),
        "industries": [_fact(industry) for industry in industries],
    }


ADAM = _product(
    "ADAM",
    form="robotic_arm_cobot",
    function="food_beverage_prep",
    industries=["bar_nightclub", "restaurant", "hotel"],
    primary_class="food_robotics",
)
DUST = _product(
    "DUST-E S",
    form="amr_mobile_robot",
    function="cleaning",
    industries=["office_building", "hospital", "hotel", "retail_store"],
    primary_class="cleaning",
)
TITAN = _product(
    "Titan",
    form="amr_mobile_robot",
    function="delivery_transport",
    industries=["warehouse_distribution", "manufacturing", "automotive_dealership"],
    primary_class="amr_logistics",
)
LOCUS = _product(
    "Locus Origin",
    form="amr_mobile_robot",
    function="picking_packing_palletizing",
    industries=["warehouse_distribution", "3pl", "logistics_parcel"],
    primary_class="amr_logistics",
    company="Locus Robotics",
)
RELAY = _product(
    "Relay",
    form="amr_mobile_robot",
    function="delivery_transport",
    industries=["hospital", "senior_living"],
    primary_class="healthcare",
    company="Relay Robotics",
)


def _industries(jobs: list[dict]) -> set[str]:
    return {str(job.get("industry") or "").lower() for job in jobs}


def _families(jobs: list[dict]) -> set[str]:
    return {str(job.get("tape_family") or "") for job in jobs}


def test_url_names_the_product_not_a_sibling():
    dust = "https://richtechrobotics.com/solutions/dust-e-s"
    assert url_names_product(dust, "DUST-E S")
    assert not url_names_product(dust, "ADAM")
    assert not url_names_product(dust, "DUST-E MX")
    assert url_names_product("https://www.richtechrobotics.com/adam", "ADAM")
    assert url_names_product("https://www.richtechrobotics.com/titan", "Titan")
    assert url_names_product("https://www.locusrobotics.com/products/origin", "Locus Origin")
    assert not url_names_product("https://www.locusrobotics.com/", "Locus Origin")


def test_adam_is_drink_work_only():
    payload = classified_match_payload(ADAM, url="https://www.richtechrobotics.com/adam")
    assert payload["needs_class_choice"] is False
    assert payload["job_count"] >= 1
    assert _families(payload["jobs"]) == {"beverage"}
    industries = _industries(payload["jobs"])
    assert "airport" not in industries
    assert "hospital" not in industries
    assert any(job["company_name"] == "Cafe operator" for job in payload["jobs"])
    assert any(job["company_name"] == "Hotel operator" for job in payload["jobs"])
    assert all(job["company_name"] not in {"Starbucks", "Hyatt Hotels"} for job in payload["jobs"])


def test_dust_e_s_is_cleaning_not_adam():
    payload = classified_match_payload(
        DUST, url="https://richtechrobotics.com/solutions/dust-e-s"
    )
    assert payload["needs_class_choice"] is False
    assert payload["robot_name"] == "DUST-E S"
    assert payload["job_count"] >= 1
    assert _families(payload["jobs"]) <= {"scrub", "restroom"}
    assert "beverage" not in _families(payload["jobs"])
    assert not any("adam" in str(job.get("title") or "").lower() for job in payload["jobs"])


def test_titan_is_delivery_without_restaurant_work():
    payload = classified_match_payload(
        TITAN, url="https://www.richtechrobotics.com/titan"
    )
    assert payload["needs_class_choice"] is False
    assert payload["job_count"] >= 1
    assert _families(payload["jobs"]) <= {"transport", "cart", "pallet_move", "pallet"}
    blob = " ".join(_industries(payload["jobs"]))
    assert "restaurant" not in blob
    assert "hotel" not in blob


def test_pharma_warehouse_evidence_is_not_a_hospital():
    product = _product(
        "Locus Origin",
        form="amr_mobile_robot",
        function="picking_packing_palletizing",
        industries=["warehouse_distribution", "3pl", "logistics_parcel"],
        primary_class="amr_logistics",
        company="Locus Robotics",
    )
    product["industries"].append(
        {
            "value": "hospital",
            "confidence": 0.8,
            "evidence": "MSK Pharma Group · Healthcare / Pharma 63 Locus robots across two neighboring sites",
        }
    )
    payload = classified_match_payload(
        product, url="https://locusrobotics.com/platform/locus-origin"
    )
    industries = _industries(payload["jobs"])
    assert not industries & {"hospital", "healthcare", "airport", "hotel"}


LOCUS_ORIGIN_URL = "https://locusrobotics.com/platform/locus-origin"


def _locus_page_products(*, origin_offering: str | None):
    origin = _product(
        "Locus Origin",
        form="amr_mobile_robot",
        function="picking_packing_palletizing",
        industries=["3pl", "warehouse_distribution", "logistics_parcel"],
        primary_class="amr_logistics",
        company="Locus Robotics",
    )
    origin["offering_type"] = _fact(origin_offering) if origin_offering else None
    vector = _product(
        "Locus Vector",
        form="amr_mobile_robot",
        function="picking_packing_palletizing",
        industries=["3pl", "warehouse_distribution"],
        primary_class="amr_logistics",
        company="Locus Robotics",
    )
    array = _product(
        "Locus Array",
        form="fixed_gantry_system",
        function="picking_packing_palletizing",
        industries=["3pl", "warehouse_distribution"],
        primary_class="amr_logistics",
        company="Locus Robotics",
    )
    return origin, vector, array


def _search_locus_page(monkeypatch, products):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    page = SimpleNamespace(text="Locus Origin warehouse picking", links=[])

    def extract(url, text, hint):
        return {
            "page": {"page_type": "manufacturer_product_page", "produces_records": True},
            "products": products,
            "extraction_metadata": {"prompt_version": "v6", "taxonomy_version": "v1.3"},
        }

    return try_phase2_search(
        LOCUS_ORIGIN_URL,
        "Locus Origin",
        fetch=lambda url: page,
        extract=extract,
    )


def _not_a_sibling(payload) -> None:
    names = " ".join(
        [
            str(payload.get("robot_name") or ""),
            *(str(job.get("for_robot") or "") for job in payload.get("jobs") or []),
        ]
    ).lower()
    assert "vector" not in names
    assert "array" not in names


def test_locus_origin_page_missing_offering_type_is_not_unrecognized(monkeypatch):
    """The live Origin page was emptied when the matching record had no offering type.

    Clean siblings on the same page (Locus Vector, Locus Array) must not become the result.
    """
    origin, vector, array = _locus_page_products(origin_offering=None)
    out = _search_locus_page(monkeypatch, [origin, vector, array])
    assert out["zero_reason"] != "unrecognized_product"
    assert out["robot_name"] == "Locus Origin"
    assert out["company_name"] == "Locus Robotics"
    assert out["job_count"] >= 1
    assert "beverage" not in _families(out["jobs"])
    _not_a_sibling(out)


def test_locus_origin_non_robot_offering_stays_unrecognized(monkeypatch):
    origin, vector, array = _locus_page_products(origin_offering="software")
    out = _search_locus_page(monkeypatch, [origin, vector, array])
    assert out["zero_reason"] == "unrecognized_product"
    assert out["robot_name"] == "Locus Origin"
    assert out["robot_name"] != "LOCUS ORIGIN"
    assert out["job_count"] == 0
    _not_a_sibling(out)


def test_locus_origin_stays_in_warehouse_and_logistics():
    payload = classified_match_payload(
        LOCUS, url="https://www.locusrobotics.com/products/origin"
    )
    assert payload["needs_class_choice"] is False
    assert payload["job_count"] >= 1
    industries = _industries(payload["jobs"])
    assert not industries & {"airport", "hotel", "hospital", "healthcare"}
    makers = {str(job.get("company_name") or "").lower() for job in payload["jobs"]}
    assert not any("locus robotics" in name for name in makers)


def test_relay_is_hospital_and_senior_living_without_a_class_prompt():
    payload = classified_match_payload(RELAY, url="https://relayrobotics.com")
    assert payload["needs_class_choice"] is False
    assert payload["job_count"] >= 1
    families = _families(payload["jobs"])
    assert families <= {"clinical_delivery", "resident_services"}
    assert "clinical_delivery" in families
    assert "resident_services" in families


def test_relay_market_variants_stay_one_product_and_skip_senior_living_when_unsaid():
    hospital = _product(
        "Relay Hospital Delivery Robot",
        form="amr_mobile_robot",
        function="delivery_transport",
        industries=["hospital"],
        primary_class="delivery",
        company="Relay Robotics",
    )
    hotel = _product(
        "Relay Hotel Delivery Robot",
        form="amr_mobile_robot",
        function="delivery_transport",
        industries=["hotel"],
        primary_class="delivery",
        company="Relay Robotics",
    )
    from app.services.buyer_opportunity.phase2_match import pick_product_record

    picked = pick_product_record(
        {"products": [hospital, hotel]},
        "https://relayrobotics.com",
    )
    assert picked is not None
    assert picked["product_name"] == "Relay"
    payload = classified_match_payload(picked, url="https://relayrobotics.com", company_name="Relay Robotics")
    assert payload["needs_class_choice"] is False
    families = _families(payload["jobs"])
    assert "clinical_delivery" in families
    assert "resident_services" not in families
    blob = " ".join(_industries(payload["jobs"]))
    assert "warehouse" not in blob
    assert "airport" not in blob


def test_catalog_discovery_reads_platform_links_and_skips_theme_pages():
    links = [
        ("https://locusrobotics.com/platform/locus-origin", "Locus Origin™"),
        ("https://locusrobotics.com/platform/locus-vector", "Locus Vector™"),
        ("https://locusrobotics.com/solutions/labor-constraints", "Labor Constraints"),
        ("https://locusrobotics.com/platform/how-it-works", "How It Works"),
    ]
    found = discover_product_pages("https://locusrobotics.com/", links)
    assert [row["name"] for row in found] == ["Locus Origin", "Locus Vector"]


def test_catalog_discovery_lists_each_product_page():
    links = [
        "https://richtechrobotics.com/solutions/adam",
        "https://richtechrobotics.com/solutions/dust-e-s",
        "https://richtechrobotics.com/solutions/dust-e-s",
        "https://example.com/solutions/other",
    ]
    found = discover_product_pages("https://richtechrobotics.com/", links)
    names = [row["name"] for row in found]
    assert names == ["ADAM", "DUST-E S"]


def test_phase2_classifies_the_submitted_page_and_skips_siblings(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    assert buyer_opportunities_enabled()
    page = SimpleNamespace(text="DUST-E S sweeps and mops floors in offices and hotels.", links=[])

    def extract(url, text, hint):
        assert "dust-e-s" in url
        return {
            "page": {"produces_records": True},
            "products": [ADAM, DUST],
            "extraction_metadata": {"prompt_version": "v6", "taxonomy_version": "v1.3"},
        }

    out = try_phase2_search(
        "https://richtechrobotics.com/solutions/dust-e-s",
        fetch=lambda url: page,
        extract=extract,
    )
    assert out is not None
    assert out["robot_name"] == "DUST-E S"
    assert out["needs_class_choice"] is False
    assert _families(out["jobs"]) <= {"scrub", "restroom"}
    assert "beverage" not in _families(out["jobs"])


def test_unrecognized_page_stays_empty(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    page = SimpleNamespace(text="a page", links=[])

    def extract(url, text, hint):
        return {"page": {"produces_records": True}, "products": [], "extraction_metadata": {}}

    out = try_phase2_search(
        "https://richtechrobotics.com/solutions/dust-e-s",
        fetch=lambda url: page,
        extract=extract,
    )
    assert out["jobs"] == []
    assert out["needs_class_choice"] is False
    assert out["zero_reason"] == "unrecognized_product"
    assert out["robot_name"] != "ADAM"


def test_homepage_discovers_products_instead_of_matching_one(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    page = SimpleNamespace(
        text="catalog",
        links=["https://richtechrobotics.com/solutions/dust-e-s"],
    )
    out = try_phase2_search(
        "https://richtechrobotics.com/",
        fetch=lambda url: page,
        extract=lambda *args, **kwargs: pytest.fail("homepage must not classify one robot"),
    )
    assert out["state"] == "select_product"
    assert out["jobs"] == []
    assert out["products"][0]["name"] == "DUST-E S"


def test_single_product_homepage_classifies_without_a_class_prompt(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    page = SimpleNamespace(text="Relay delivers medications in hospitals and senior living.", links=[])

    def extract(url, text, hint):
        return {
            "page": {"produces_records": True},
            "products": [RELAY],
            "extraction_metadata": {"prompt_version": "v6"},
        }

    out = try_phase2_search("https://relayrobotics.com", fetch=lambda url: page, extract=extract)
    assert out is not None
    assert out["needs_class_choice"] is False
    assert out["robot_name"] == "Relay"
    assert "clinical_delivery" in _families(out["jobs"])
    assert "resident_services" in _families(out["jobs"])


def test_flag_off_leaves_the_old_flow(monkeypatch):
    monkeypatch.delenv("RFR_BUYER_OPPORTUNITIES_V1", raising=False)
    assert buyer_opportunities_enabled() is False
    assert (
        try_phase2_search(
            "https://richtechrobotics.com/solutions/dust-e-s",
            fetch=lambda url: pytest.fail("flag off must not fetch"),
            extract=lambda *a, **k: pytest.fail("flag off must not classify"),
        )
        is None
    )


def test_compose_returns_phase2_when_the_flag_is_on(monkeypatch):
    monkeypatch.setattr(
        "app.services.buyer_opportunity.phase2_match.buyer_opportunities_enabled",
        lambda: True,
    )
    sentinel = {"state": "matches", "jobs": [], "robot_name": "DUST-E S"}
    monkeypatch.setattr(
        "app.services.buyer_opportunity.phase2_match.try_phase2_search",
        lambda url, product_name=None: sentinel,
    )
    from app.services.robot_job_search import compose_robot_job_search

    out = compose_robot_job_search("https://richtechrobotics.com/solutions/dust-e-s")
    assert out["robot_name"] == "DUST-E S"
    assert out["timings"]["total_ms"] >= 0


def test_jobs_for_classification_drops_mobile_work_for_a_fixed_arm():
    jobs = jobs_for_classification(ADAM)
    assert jobs
    assert {job["tape_family"] for job in jobs} == {"beverage"}
