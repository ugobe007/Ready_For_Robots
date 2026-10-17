"""Phase 2 matches the submitted product. A sibling from the same maker is not a result."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.buyer_opportunity.phase2_match import (
    buyer_opportunities_enabled,
    classified_match_payload,
    corpus_industry_to_taxonomy,
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


def test_rule_21_search_shows_no_class_and_needs_review(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    product = _product(
        "Survey Bot",
        form="amr_mobile_robot",
        function="general_purpose",
        industries=["hotel"],
        primary_class="service_robot",
    )
    product["primary_class"] = None
    product["needs_review"] = True
    product["class_rule_id"] = "21"
    product["model_class_suggestion"] = "service_robot"
    page = SimpleNamespace(text="Survey Bot hotel", links=[])

    def extract(url, text, hint):
        return {
            "page": {"page_type": "manufacturer_product_page", "produces_records": True},
            "products": [product],
            "extraction_metadata": {"prompt_version": "v6", "taxonomy_version": "v1.3"},
        }

    out = try_phase2_search(
        "https://example.test/survey-bot",
        fetch=lambda url: page,
        extract=extract,
    )
    assert out["robot_class"] is None
    assert out["needs_review"] is True
    assert out["needs_class_choice"] is False
    assert out["products"][0]["display_class"] is None
    assert out["products"][0]["robot_class"] is None
    assert "model_class_suggestion" not in out["products"][0]
    assert out["profile"]["selected_product"]["display_class"] is None
    assert out["classified_product"]["product"]["model_class_suggestion"] == "service_robot"


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

    from app.services.vendor_robot_lookup import index_robot_names, lookup_vendor_by_url

    # The vendor index lists one robot for this domain, so the homepage classifies.
    assert index_robot_names(lookup_vendor_by_url("https://relayrobotics.com")) == ["Relay"]
    out = try_phase2_search("https://relayrobotics.com", fetch=lambda url: page, extract=extract)
    assert out is not None
    assert out["needs_class_choice"] is False
    assert out["needs_product_choice"] is False
    assert out["robot_name"] == "Relay"
    assert "clinical_delivery" in _families(out["jobs"])
    assert "resident_services" in _families(out["jobs"])


def _catalog_homepage(links: list[str]):
    return SimpleNamespace(text="Maker homepage with no product page linked.", links=links)


def _extract_one(product):
    def extract(url, text, hint):
        return {
            "page": {"produces_records": True},
            "products": [product],
            "extraction_metadata": {"prompt_version": "v6"},
        }

    return extract


def test_richtech_homepage_without_product_links_opens_the_picker(monkeypatch):
    """No /solutions/{product} links, and the index lists many robots. Not Titan."""
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    page = _catalog_homepage(
        [
            "https://richtechrobotics.com/solutions",
            "https://richtechrobotics.com/solutions?category=delivery",
        ]
    )
    missed = try_phase2_search(
        "https://richtechrobotics.com/",
        fetch=lambda url: page,
        extract=_extract_one(TITAN),
    )
    assert missed is None

    monkeypatch.setattr(
        "app.services.robot_understanding_v1.fetch.fetch_page",
        lambda url, **kwargs: page,
    )
    monkeypatch.setattr(
        "app.services.robot_understanding_v1.taxonomy_extraction.extract_robot_taxonomy",
        _extract_one(TITAN),
    )
    from app.services.robot_job_search import compose_robot_job_search

    out = compose_robot_job_search("https://richtechrobotics.com/")
    assert out["state"] == "select_product"
    assert out["needs_product_choice"] is True
    assert out["robot_name"] != "Titan"
    names = {row["name"] for row in out["products"]}
    assert "ADAM" in names
    assert "Titan" in names
    assert len(names) > 1


def test_keenon_homepage_without_product_links_opens_the_picker(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    page = _catalog_homepage(["https://www.keenon.com/solutions"])
    missed = try_phase2_search(
        "https://www.keenon.com/",
        fetch=lambda url: page,
        extract=_extract_one(TITAN),
    )
    assert missed is None

    monkeypatch.setattr(
        "app.services.robot_understanding_v1.fetch.fetch_page",
        lambda url, **kwargs: page,
    )
    from app.services.robot_job_search import compose_robot_job_search

    out = compose_robot_job_search("https://www.keenon.com/")
    assert out["state"] == "select_product"
    assert out["needs_product_choice"] is True
    assert len(out["products"]) > 1


def test_adam_product_url_still_classifies(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    page = SimpleNamespace(text="ADAM prepares drinks at the bar.", links=[])
    out = try_phase2_search(
        "https://richtechrobotics.com/solutions/adam",
        fetch=lambda url: page,
        extract=_extract_one(ADAM),
    )
    assert out is not None
    assert out["robot_name"] == "ADAM"
    assert out["needs_product_choice"] is False
    assert out["state"] != "select_product"


def test_unindexed_homepage_still_classifies_one_robot(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    solo = _product(
        "Acme Arm",
        form="robotic_arm_cobot",
        function="machine_tending",
        industries=["manufacturing"],
        primary_class="robotic_arm_cobot",
        company="Acme",
    )
    page = _catalog_homepage([])
    out = try_phase2_search(
        "https://unknown-oem.example/",
        fetch=lambda url: page,
        extract=_extract_one(solo),
    )
    assert out is not None
    assert out["robot_name"] == "Acme Arm"
    assert out["needs_product_choice"] is False


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
        lambda url, product_name=None, **_kwargs: sentinel,
    )
    from app.services.robot_job_search import compose_robot_job_search

    out = compose_robot_job_search("https://richtechrobotics.com/solutions/dust-e-s")
    assert out["robot_name"] == "DUST-E S"
    assert out["timings"]["total_ms"] >= 0


def test_jobs_for_classification_drops_mobile_work_for_a_fixed_arm():
    jobs = jobs_for_classification(ADAM)
    assert jobs
    assert {job["tape_family"] for job in jobs} == {"beverage"}


# The five robots from the live check. Each search calls the classifier once
# until a clean row exists for that URL at the current prompt and taxonomy versions.
FIVE_ROBOTS = (
    ("https://richtechrobotics.com/solutions/dust-e-s", "DUST-E S", DUST),
    ("https://www.richtechrobotics.com/adam", "ADAM", ADAM),
    ("https://www.richtechrobotics.com/titan", "Titan", TITAN),
    ("https://relayrobotics.com", "Relay", RELAY),
    ("https://locusrobotics.com/platform/locus-origin", "Locus Origin", LOCUS),
)


def _products_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool

    from app.services.buyer_opportunity.tables import rfr_robot_products

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    rfr_robot_products.metadata.create_all(engine, tables=[rfr_robot_products])
    return Session(engine)


def _search_and_save(db, url, name, product, calls):
    from app.services.buyer_opportunity.phase2_match import persist_classified_product
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    page = SimpleNamespace(text=f"{name} product page", links=[])

    def extract(page_url, text, hint):
        calls.append(page_url)
        return {
            "page": {"page_type": "manufacturer_product_page", "produces_records": True},
            "products": [product],
            "extraction_metadata": {
                "prompt_version": PROMPT_VERSION,
                "taxonomy_version": get_taxonomy_version(),
            },
        }

    out = try_phase2_search(url, name, fetch=lambda page_url: page, extract=extract, db=db)
    assert out is not None
    classified = out.pop("classified_product", None)
    if classified:
        persist_classified_product(db, classified)
    return out


def test_five_robots_reuse_saved_classifications(monkeypatch):
    """First pass classifies each URL. The second pass reads rfr_robot_products and does not call the model."""
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    db = _products_db()
    first: list[str] = []
    second: list[str] = []
    for url, name, product in FIVE_ROBOTS:
        out = _search_and_save(db, url, name, product, first)
        assert out["robot_name"] == name
        assert "classified_product" not in out
    for url, name, product in FIVE_ROBOTS:
        out = _search_and_save(db, url, name, product, second)
        assert out["robot_name"] == name
        assert out["zero_reason"] != "unrecognized_product"
        assert "classified_product" not in out
    assert len(first) == 5
    # Relay's homepage lists one indexed robot, and the saved name matches it,
    # so the second pass reuses that row too.
    assert second == []


def test_unclean_or_stale_row_still_calls_the_classifier(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from app.services.buyer_opportunity.phase2_match import persist_classified_product
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    db = _products_db()
    software = dict(DUST)
    software["offering_type"] = _fact("software")
    url = "https://richtechrobotics.com/solutions/dust-e-s"
    current = {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()}
    persist_classified_product(
        db,
        {"product": software, "metadata": current, "source_url": url},
    )
    calls: list[str] = []
    out = _search_and_save(db, url, "DUST-E S", DUST, calls)
    assert calls == [url]
    assert out["robot_name"] == "DUST-E S"

    stale = _products_db()
    persist_classified_product(
        stale,
        {
            "product": DUST,
            "metadata": {"prompt_version": "v0", "taxonomy_version": get_taxonomy_version()},
            "source_url": url,
        },
    )
    stale_calls: list[str] = []
    out = _search_and_save(stale, url, "DUST-E S", DUST, stale_calls)
    assert stale_calls == [url]
    assert out["robot_name"] == "DUST-E S"


def test_single_robot_homepage_reuses_a_saved_row_with_the_same_name(monkeypatch):
    """Diligent and Relay homepages list one indexed robot. A clean row whose name matches is reused."""
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from app.services.buyer_opportunity.phase2_match import persist_classified_product
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version
    from app.services.vendor_robot_lookup import index_robot_names, lookup_vendor_by_url

    assert index_robot_names(lookup_vendor_by_url("https://www.diligentrobots.com/")) == ["Moxi"]
    assert index_robot_names(lookup_vendor_by_url("https://relayrobotics.com")) == ["Relay"]
    moxi = _product(
        "Moxi",
        form="amr_mobile_robot",
        function="delivery_transport",
        industries=["hospital"],
        primary_class="healthcare",
        company="Diligent Robotics",
    )
    db = _products_db()
    home = "https://www.diligentrobots.com/"
    persist_classified_product(
        db,
        {
            "product": moxi,
            "metadata": {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()},
            "source_url": home,
        },
    )
    calls: list[str] = []
    out = try_phase2_search(
        home,
        fetch=lambda url: pytest.fail("saved single-robot homepage must not be fetched"),
        extract=lambda *args, **kwargs: calls.append("extract") or pytest.fail("extract"),
        db=db,
    )
    assert calls == []
    assert out["robot_name"] == "Moxi"
    assert out["robot_class"] == "healthcare"
    assert out["class_rule_id"] == "3"
    assert "classified_product" not in out


def test_reused_row_takes_the_rule_class_without_writing(monkeypatch):
    """A stored delivery class is not what reuse returns when the facts are clinical."""
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from sqlalchemy import insert, select

    from app.services.buyer_opportunity.tables import rfr_robot_products
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    home = "https://www.diligentrobots.com/"
    db = _products_db()
    version = {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()}
    db.execute(
        insert(rfr_robot_products).values(
            source_url=home,
            product_name="Moxi",
            company_name="Diligent Robotics",
            primary_class="delivery",
            primary_function="delivery_transport",
            form="mobile_manipulator",
            industries=["hospital"],
            evidence={
                "form": {"value": "mobile_manipulator"},
                "primary_class": {"value": "delivery"},
                "primary_function": {"value": "delivery_transport"},
                "industries": [{"value": "hospital"}],
            },
            **version,
        )
    )
    db.commit()
    out = try_phase2_search(
        home,
        fetch=lambda url: pytest.fail("saved Diligent homepage must not be fetched"),
        extract=lambda *args, **kwargs: pytest.fail("saved Diligent homepage must not be extracted"),
        db=db,
    )
    assert out["robot_class"] == "healthcare"
    assert out["class_rule_id"] == "3"
    stored = db.execute(select(rfr_robot_products.c.primary_class)).scalar_one()
    assert stored == "delivery"


def test_single_robot_homepage_does_not_reuse_a_different_name(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from app.services.buyer_opportunity.phase2_match import persist_classified_product
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    home = "https://www.diligentrobots.com/"
    other = _product(
        "Parcelcopter",
        form="amr_mobile_robot",
        function="delivery_transport",
        industries=["logistics_parcel"],
        primary_class="delivery",
        company="Diligent Robotics",
    )
    db = _products_db()
    persist_classified_product(
        db,
        {
            "product": other,
            "metadata": {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()},
            "source_url": home,
        },
    )
    page = SimpleNamespace(text="Moxi is a hospital robot.", links=[])
    calls: list[str] = []

    def extract(url, text, hint):
        calls.append(url)
        return {
            "page": {"produces_records": True},
            "products": [RELAY],
            "extraction_metadata": {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()},
        }

    out = try_phase2_search(home, fetch=lambda url: page, extract=extract, db=db)
    assert calls == [home]
    assert out["robot_name"] == "Relay"


def test_homepage_with_a_saved_row_still_returns_the_picker(monkeypatch):
    """A homepage whose vendor index lists more than one robot still returns the picker."""
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from app.services.buyer_opportunity.phase2_match import persist_classified_product
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    home = "https://richtechrobotics.com/"
    db = _products_db()
    persist_classified_product(
        db,
        {
            "product": ADAM,
            "metadata": {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()},
            "source_url": home,
        },
    )
    page = SimpleNamespace(
        text="catalog",
        links=[
            "https://richtechrobotics.com/solutions/adam",
            "https://richtechrobotics.com/solutions/scorpion",
        ],
    )
    calls: list[str] = []
    out = try_phase2_search(
        home,
        fetch=lambda url: page,
        extract=lambda *args, **kwargs: calls.append("extract") or pytest.fail("saved homepage row must not be classified"),
        db=db,
    )
    assert calls == []
    assert out["state"] == "select_product"
    assert out["needs_product_choice"] is True
    assert out["jobs"] == []
    assert out["robot_name"] != "ADAM"


def test_homepage_hint_does_not_reuse_a_different_saved_product(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from app.services.buyer_opportunity.phase2_match import persist_classified_product
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    home = "https://richtechrobotics.com/"
    scorpion_url = "https://richtechrobotics.com/solutions/scorpion"
    scorpion = _product(
        "Scorpion",
        form="robotic_arm_cobot",
        function="food_beverage_prep",
        industries=["restaurant", "bar_nightclub"],
        primary_class="food_robotics",
    )
    db = _products_db()
    persist_classified_product(
        db,
        {
            "product": ADAM,
            "metadata": {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()},
            "source_url": home,
        },
    )
    page = SimpleNamespace(
        text="catalog",
        links=[
            "https://richtechrobotics.com/solutions/adam",
            scorpion_url,
        ],
    )
    calls: list[str] = []

    def extract(url, text, hint):
        calls.append(url)
        return {
            "page": {"produces_records": True},
            "products": [scorpion],
            "extraction_metadata": {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()},
        }

    out = try_phase2_search(home, "Scorpion", fetch=lambda url: page, extract=extract, db=db)
    assert out["robot_name"] == "Scorpion"
    assert out["robot_name"] != "ADAM"
    assert calls == [scorpion_url]


def test_product_url_reuses_the_saved_row_for_the_same_product(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    url = "https://richtechrobotics.com/solutions/dust-e-s"
    db = _products_db()
    first: list[str] = []
    second: list[str] = []
    from sqlalchemy import func, select

    from app.services.buyer_opportunity.phase2_match import persist_classified_product
    from app.services.buyer_opportunity.tables import rfr_robot_products

    _search_and_save(db, url, "DUST-E S", DUST, first)
    saved_rows = db.execute(select(func.count()).select_from(rfr_robot_products)).scalar_one()
    page = SimpleNamespace(text="DUST-E S product page", links=[])
    out = try_phase2_search(
        url,
        "DUST-E S",
        fetch=lambda page_url: page,
        extract=lambda *args, **kwargs: second.append(url),
        db=db,
    )
    reused = out.pop("classified_product", None) if isinstance(out, dict) else None
    if reused:
        persist_classified_product(db, reused)
    again = db.execute(select(func.count()).select_from(rfr_robot_products)).scalar_one()
    assert first == [url]
    assert second == []
    assert out["robot_name"] == "DUST-E S"
    assert reused is None
    assert again == saved_rows


def test_saved_row_at_old_prompt_version_is_not_reused(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from app.services.buyer_opportunity.phase2_match import persist_classified_product
    from app.services.robot_understanding_v1.taxonomy_extraction import get_taxonomy_version

    url = "https://locusrobotics.com/platform/locus-origin"
    db = _products_db()
    persist_classified_product(
        db,
        {
            "product": LOCUS,
            "metadata": {"prompt_version": "v0", "taxonomy_version": get_taxonomy_version()},
            "source_url": url,
        },
    )
    calls: list[str] = []
    out = _search_and_save(db, url, "Locus Origin", LOCUS, calls)
    assert calls == [url]
    assert out["robot_name"] == "Locus Origin"


def test_saved_lookup_error_falls_through_to_the_classifier(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")

    class Broken:
        def execute(self, *args, **kwargs):
            raise RuntimeError("lookup failed")

        def rollback(self):
            self.rolled_back = True

    db = Broken()
    calls: list[str] = []
    url = "https://www.richtechrobotics.com/adam"
    page = SimpleNamespace(text="ADAM espresso", links=[])

    def extract(page_url, text, hint):
        calls.append(page_url)
        return {
            "page": {"produces_records": True},
            "products": [ADAM],
            "extraction_metadata": {"prompt_version": "v6"},
        }

    out = try_phase2_search(url, "ADAM", fetch=lambda page_url: page, extract=extract, db=db)
    assert calls == [url]
    assert out["robot_name"] == "ADAM"
    assert db.rolled_back is True


def test_industry_strings_for_unmapped_work():
    assert corpus_industry_to_taxonomy("Construction") == frozenset({"construction"})
    assert corpus_industry_to_taxonomy("Agriculture") == frozenset({"agriculture"})
    assert corpus_industry_to_taxonomy("Factory") == frozenset({"manufacturing"})
    assert corpus_industry_to_taxonomy("Surgery center") == frozenset({"surgery_center"})
    assert corpus_industry_to_taxonomy("Manufacturing") == frozenset({"manufacturing"})


def test_construction_agriculture_and_machine_tending_join():
    construction = jobs_for_classification(
        _product(
            "Exosystem",
            form="autonomous_vehicle_equipment",
            function="construction_task",
            industries=["construction"],
            primary_class="construction",
            company="Built Robotics",
        ),
        limit=20,
    )
    assert _families(construction) == {"construction"}
    assert len(construction) == 6

    agriculture = jobs_for_classification(
        _product(
            "BOT#25",
            form="amr_mobile_robot",
            function="agricultural_task",
            industries=["agriculture"],
            primary_class="agriculture",
            company="Greenfield Robotics",
        ),
        limit=20,
    )
    assert _families(agriculture) == {"agriculture"}
    assert len(agriculture) == 9

    tending = jobs_for_classification(
        _product(
            "Cell tender",
            form="robotic_arm_cobot",
            function="machine_tending_assembly",
            industries=["manufacturing"],
            primary_class="factory_industrial",
        ),
        limit=20,
    )
    assert _families(tending) == {"machine_tending"}
    assert len(tending) == 10
    assert all(job["industry"] != "Charlotte, NC" for job in tending)


def test_five_repeat_homepage_searches_add_at_most_one_row(monkeypatch):
    """An unindexed homepage (Greenfield) reuses the saved product. Five searches insert once."""
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from sqlalchemy import func, select

    from app.services.buyer_opportunity.tables import rfr_robot_products
    from app.services.vendor_robot_lookup import index_robot_names, lookup_vendor_by_url

    forms = [
        "https://www.greenfieldincorporated.com/",
        "https://greenfieldincorporated.com",
        "https://greenfieldincorporated.com/",
        "https://www.greenfieldincorporated.com",
        "https://www.greenfieldincorporated.com/",
    ]
    vendor = lookup_vendor_by_url(forms[0])
    assert vendor is None or index_robot_names(vendor) == []
    bot = _product(
        "BOT#25",
        form="amr_mobile_robot",
        function="agricultural_task",
        industries=["agriculture"],
        primary_class="agriculture",
        company="Greenfield Robotics",
    )
    db = _products_db()
    calls: list[str] = []
    for url in forms:
        _search_and_save(db, url, "BOT#25", bot, calls)
    saved = db.execute(select(func.count()).select_from(rfr_robot_products)).scalar_one()
    assert calls == [forms[0]]
    assert saved == 1


def test_match_uses_the_latest_row_for_a_url_and_product(monkeypatch):
    monkeypatch.setenv("RFR_BUYER_OPPORTUNITIES_V1", "1")
    from sqlalchemy import insert

    from app.services.buyer_opportunity.tables import rfr_robot_products
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    home = "https://www.greenfieldincorporated.com/"
    db = _products_db()
    version = {"prompt_version": PROMPT_VERSION, "taxonomy_version": get_taxonomy_version()}
    for primary_class in ("delivery", "agriculture"):
        db.execute(
            insert(rfr_robot_products).values(
                source_url=home,
                product_name="BOT#25",
                primary_class=primary_class,
                primary_function="agricultural_task",
                form="amr_mobile_robot",
                industries=["agriculture"],
                evidence={
                    "form": {"value": "amr_mobile_robot"},
                    "primary_class": {"value": primary_class},
                    "primary_function": {"value": "agricultural_task"},
                    "industries": [{"value": "agriculture"}],
                },
                **version,
            )
        )
    db.commit()
    out = try_phase2_search(
        home,
        fetch=lambda url: pytest.fail("latest saved homepage must not be fetched"),
        extract=lambda *args, **kwargs: pytest.fail("latest saved homepage must not be extracted"),
        db=db,
    )
    assert out["robot_class"] == "agriculture"
    assert out["robot_name"] == "BOT#25"
