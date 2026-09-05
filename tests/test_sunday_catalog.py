"""Sunday Memo is catalog-first: URL list → index → named kitchen jobs, no scrape."""
from __future__ import annotations

from app.services.jobs_oem_listing import listing_payload_for_url
from app.services.robot_requirement_match import (
    is_named_robot_job,
    load_corpus,
    match_jobs_from_profile,
)
from app.services.vendor_robot_lookup import (
    index_robot_names,
    lookup_vendor_by_url,
    reload_vendor_robots_index,
)


SUNDAY = "https://www.sunday.ai/"


def test_unnamed_templates_are_not_robot_jobs():
    assert not is_named_robot_job(company_name=None, locality="Seattle, WA")
    assert not is_named_robot_job(company_name="Starbucks", locality=None)
    assert not is_named_robot_job(company_name="Unknown", locality="Seattle, WA")
    assert not is_named_robot_job(company_name="Starbucks", locality="[unknown]")
    assert is_named_robot_job(company_name="Starbucks", locality="Seattle, WA")


def test_sunday_url_hits_catalog_memo():
    reload_vendor_robots_index()
    load_corpus.cache_clear()
    hit = lookup_vendor_by_url(SUNDAY)
    assert hit is not None
    assert hit["vendor_name"] == "Sunday Robotics"
    assert index_robot_names(hit) == ["Memo"]
    payload = listing_payload_for_url(SUNDAY)
    assert payload["matched"] is True
    assert payload["robots"][0]["name"] == "Memo"
    assert payload["robots"][0]["display_class"] == "service_robot"
    blurb = (payload["robots"][0].get("description") or "").lower()
    assert "kitchen" in blurb or "espresso" in blurb or "home" in blurb


def test_sunday_homepage_skips_live_fetch(monkeypatch):
    reload_vendor_robots_index()
    import app.services.robot_understanding_v1.pipeline as P

    monkeypatch.setattr(
        P,
        "fetch_page",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("indexed Sunday URL must not wait on the live host")
        ),
    )
    monkeypatch.setattr(
        P,
        "collect_source_pack",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("indexed Sunday URL must not crawl SKUs")
        ),
    )
    timings: dict = {}
    profile = P.build_robot_profile(SUNDAY, product_name="Memo", timings=timings)
    assert timings.get("home_fetch") == "skipped"
    assert timings.get("source_strategy") == "catalog"
    assert profile.selected_product is not None
    assert profile.selected_product.name == "Memo"
    preds = {
        f.predicate: f.value
        for f in profile.facts
        if f.epistemic in {"explicit", "strongly_inferred"}
    }
    assert preds.get("product_class") == "service_robot"
    assert preds.get("claims_food_prep") is True
    assert preds.get("claims_beverage_prep") is True
    assert preds.get("product_class") != "humanoid"


def test_sunday_memo_matches_named_kitchen_jobs_not_cnc(monkeypatch):
    reload_vendor_robots_index()
    import app.services.robot_understanding_v1.pipeline as P

    monkeypatch.setattr(
        P,
        "fetch_page",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("indexed Sunday URL must not wait on the live host")
        ),
    )
    profile = P.build_robot_profile(SUNDAY, product_name="Memo")
    match = match_jobs_from_profile(profile.to_dict(), limit=12)
    jobs = match.get("jobs") or []
    assert jobs, match
    assert all(is_named_robot_job(row=j) for j in jobs)
    families = {j.get("tape_family") for j in jobs}
    assert families & {"food_prep", "beverage"}
    assert families.isdisjoint({"pallet", "gripper", "inspect"})
    titles = " ".join(j.get("title") or "" for j in jobs).lower()
    assert "cnc" not in titles
    employers = {j.get("company_name") for j in jobs}
    assert "Starbucks" in employers or "Compass Group" in employers or "White Castle" in employers


def test_richtech_adam_catalog_matches_named_beverage_jobs(monkeypatch):
    reload_vendor_robots_index()
    import app.services.robot_understanding_v1.pipeline as P

    monkeypatch.setattr(
        P,
        "fetch_page",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("indexed Richtech URL must not wait on the live host")
        ),
    )
    profile = P.build_robot_profile(
        "https://www.richtechrobotics.com/adam",
        product_name="ADAM",
    )
    match = match_jobs_from_profile(profile.to_dict(), limit=12)
    jobs = match.get("jobs") or []
    assert jobs
    assert all(is_named_robot_job(row=j) for j in jobs)
    families = {j.get("tape_family") for j in jobs}
    assert "beverage" in families
    assert all(j.get("company_name") and j.get("locality") for j in jobs)
