"""Retail shelf/inventory scanning (Simbe Tally-class) + food-prep truth guard."""
from __future__ import annotations

from app.services.robot_capability_derive import derive_capabilities
from app.services.robot_requirement_match import match_jobs_from_profile
from app.services.robot_understanding_v1 import facts as F
from app.services.robot_understanding_v1.models import RobotSource


def _profile_from_facts(name, *preds):
    facts = [{"predicate": p, "value": True, "units": None, "epistemic": "explicit",
              "confidence": 0.9, "evidence_span": p, "source_id": "s0"} for p in preds]
    return {"selected_product": {"name": name}, "company": {"name": name}, "facts": facts}


def _fams(profile):
    return {j["tape_family"] for j in match_jobs_from_profile(profile, limit=60)["jobs"]}


def test_shelf_scanner_matches_shelf_scan_only():
    prof = _profile_from_facts("Tally", "claims_shelf_scan", "autonomous_navigation", "has_mobile_base")
    caps = derive_capabilities(prof)
    assert caps["shelf_scan"].present and caps["mobile"].present
    fams = _fams(prof)
    assert "shelf_scan" in fams
    # A shelf scanner is not a manipulator/cleaner/food robot.
    assert fams.isdisjoint({"pallet", "gripper", "scrub", "restroom", "food_prep", "beverage"})


def _extract(text: str) -> set[str]:
    src = RobotSource(id="s", url="https://x.ai/robot", source_type="product",
                      fetched_at="t", title="R", confidence=0.85)
    facts = F._extract_from_page(src, text, subject="", page_url="https://x.ai/robot", page_title="R")
    return {f.predicate for f in facts if f.epistemic != "unknown"}


def test_prepared_meals_category_is_not_food_prep():
    # "Prepared meals" is a grocery shelf category, not the robot cooking.
    preds = _extract("The inventory robot scans shelves including the prepared meals and deli aisles daily.")
    assert "claims_food_prep" not in preds
    assert "claims_shelf_scan" in preds


def test_active_food_prep_still_grounds():
    preds = _extract("This kitchen robot prepares fresh salads and assembles grain bowls to order each shift.")
    assert "claims_food_prep" in preds


def test_shelf_scan_navigation_grounds_mobility():
    # "navigates … stores/aisles" must ground autonomous_navigation (Tally case).
    preds = _extract("Tally is an autonomous inventory robot that navigates 150,000 square-foot stores daily.")
    assert "autonomous_navigation" in preds
    assert "claims_shelf_scan" in preds
