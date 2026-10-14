"""Spec v1.3 §6 step 5: a stationary robot never gets work that moves through a building."""
from __future__ import annotations

from app.services.form_fit import MOBILE_ONLY_TAPE_FAMILIES, jobs_fit_form
from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_job_capability_match import match_robot_url
from app.services.robot_job_search import compose_robot_job_search
from app.services.robot_profile_cache import clear_profile_cache_memory

ADAM = "https://www.richtechrobotics.com/adam"


def _fact(predicate, value):
    return {"predicate": predicate, "value": value, "evidence_span": "x", "epistemic": "explicit"}


def _profile(*facts):
    return {"company": {"name": "T"}, "selected_product": {"name": "T"}, "facts": list(facts)}


def test_grounded_stationary_beats_class_inference():
    caps = derive_capabilities(
        _profile(
            _fact("product_class", "service_robot"),
            _fact("operating_environment", "hospitality"),
            _fact("has_mobile_base", False),
        )
    )
    assert caps["mobile"].present is False


def test_explicit_navigation_still_counts_as_mobile():
    caps = derive_capabilities(
        _profile(_fact("has_mobile_base", False), _fact("autonomous_navigation", True))
    )
    assert caps["mobile"].present is True


def test_adam_site_search_returns_drink_station_work_only():
    clear_profile_cache_memory()
    out = compose_robot_job_search(ADAM, product="ADAM", lookup_grain="product")
    keys = {j["job_key"] for j in out["jobs"]}
    assert {"beverage_espresso_bar", "beverage_cocktail_bar"} <= keys
    assert {j.get("tape_family") for j in out["jobs"]} == {"beverage"}


def test_adam_legacy_match_returns_no_mobile_work():
    for name in ("ADAM", None):
        out = match_robot_url(ADAM, robot_name=name)
        families = {j.get("tape_family") for j in out["jobs"]}
        assert not families & MOBILE_ONLY_TAPE_FAMILIES
        assert out["job_count"] == len(out["jobs"])


def test_mobile_serving_robot_keeps_serving_jobs():
    clear_profile_cache_memory()
    out = compose_robot_job_search(
        "https://www.richtechrobotics.com/scotty", product="Scotty", lookup_grain="product"
    )
    assert {j.get("tape_family") for j in out["jobs"]} & {"serve"}


def test_jobs_fit_form_only_filters_stationary():
    jobs = [{"tape_family": "serve"}, {"tape_family": "beverage"}]
    assert jobs_fit_form(jobs, stationary=False) == jobs
    assert jobs_fit_form(jobs, stationary=True) == [{"tape_family": "beverage"}]
