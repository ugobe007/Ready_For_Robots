"""Employer MATCH: named catalog robots only. Honest empty. No invented SKUs."""
from __future__ import annotations

from app.services.employer_robot_match import EMPTY_COPY, match_catalog_robots


def test_serving_work_returns_named_catalog_robots():
    result = match_catalog_robots(work_class="serving", limit=12)
    assert result["state"] == "matches"
    assert result["robot_count"] > 0
    names = [r["name"] for r in result["robots"]]
    vendors = [r["vendor_name"] for r in result["robots"]]
    assert any("BellaBot" in n for n in names)
    assert all(r["name"] and r["vendor_name"] for r in result["robots"])
    assert not any("Seer Humanoid" in n for n in names)
    assert any("Pudu" in v for v in vendors)


def test_healthcare_work_does_not_dump_humanoids():
    result = match_catalog_robots(work_class="healthcare", limit=12)
    classes = {r.get("robot_class") for r in result["robots"]}
    assert "humanoid" not in classes
    assert all(r["name"] and r["vendor_name"] for r in result["robots"])
    assert all(r.get("robot_class") in {None, "healthcare"} for r in result["robots"])


def test_unknown_work_class_is_honest_empty():
    result = match_catalog_robots(work_class="not_a_robot_class")
    assert result["state"] == "empty"
    assert result["robots"] == []
    assert result["empty_copy"] == EMPTY_COPY


def test_empty_work_class_is_honest():
    result = match_catalog_robots(work_class=None, description="")
    assert result["state"] == "empty"
    assert result["robots"] == []
    assert result["empty_copy"] == EMPTY_COPY


def test_empty_copy_tells_them_to_post():
    assert "Post the job so OEMs can find it" in EMPTY_COPY


def test_catalog_match_is_under_three_seconds():
    import time

    from app.services.employer_robot_match import match_catalog_robots

    match_catalog_robots(work_class="serving", limit=12)
    t0 = time.perf_counter()
    result = match_catalog_robots(work_class="warehouse", limit=12)
    elapsed = time.perf_counter() - t0
    assert elapsed < 3.0, elapsed
    assert result["catalog_only"] is True
    assert result["live_scrape"] is False


def test_match_module_does_not_scrape():
    from pathlib import Path

    src = Path("app/services/employer_robot_match.py").read_text(encoding="utf-8")
    assert "listing_from_catalog" not in src
    assert "build_robot_profile" not in src
    assert "scrape_robot_page" not in src
    assert "_catalog_robots_snapshot" in src


def test_matched_robots_carry_catalog_facts_for_examine():
    result = match_catalog_robots(work_class="serving", limit=12)
    assert result["state"] == "matches"
    assert result["robots"]
    for robot in result["robots"]:
        assert robot["name"]
        assert robot["vendor_name"]
        assert "product_url" in robot
        assert "match_percent" not in robot
        assert "roi" not in robot
        assert "fit_score" not in robot
    assert any(
        robot.get("product_url") or robot.get("vendor_url")
        for robot in result["robots"]
    )


def test_public_matched_robot_does_not_invent_specs():
    from app.services.employer_robot_match import public_matched_robot

    public = public_matched_robot(
        {
            "name": "BellaBot",
            "vendor_name": "Pudu Robotics",
            "vendor_url": "https://www.pudurobotics.com/",
            "robot_class": "serving",
            "description": "Restaurant serving.",
            "product_url": "https://www.pudurobotics.com/product/bellabot",
            "task": None,
            "setting": None,
        }
    )
    assert public["name"] == "BellaBot"
    assert public["product_url"].endswith("bellabot")
    assert "specs" not in public
    assert "image_url" not in public
    assert "match_percent" not in public
    with_photo = public_matched_robot(
        {
            "name": "BellaBot",
            "vendor_name": "Pudu Robotics",
            "description": "Restaurant serving.",
            "product_url": "https://www.pudurobotics.com/product/bellabot",
            "image_url": "https://cdn.example.com/bellabot.jpg",
            "specs": {"payload_kg": 10},
        }
    )
    assert with_photo["image_url"].endswith("bellabot.jpg")
    assert with_photo["specs"]["payload_kg"] == 10
    no_fake = public_matched_robot(
        {
            "name": "BellaBot",
            "vendor_name": "Pudu Robotics",
            "image_url": "javascript:alert(1)",
        }
    )
    assert "image_url" not in no_fake


def test_employer_can_shortlist_more_than_one_catalog_robot():
    from pathlib import Path

    from app.services.employer_robot_match import public_shortlisted_robots

    chosen = public_shortlisted_robots(
        [
            {"name": "BellaBot", "vendor_name": "Pudu Robotics", "robot_class": "serving"},
            {"name": "Dinerbot T10", "vendor_name": "Keenon Robotics", "robot_class": "serving"},
            {"name": "BellaBot", "vendor_name": "Pudu Robotics"},
            {"name": "", "vendor_name": "Ghost"},
        ]
    )
    assert [r["name"] for r in chosen] == ["BellaBot", "Dinerbot T10"]
    api = Path("app/api/employer_jobs.py").read_text(encoding="utf-8")
    life = Path("app/services/robot_job_lifecycle.py").read_text(encoding="utf-8")
    assert "employer_shortlisted_robots" in api
    assert "employer_shortlisted_robots" in life
    assert "public_shortlisted_robots" in api


def test_employer_draft_persists_jd_on_robot_jobs():
    from pathlib import Path

    api = Path("app/api/employer_jobs.py").read_text(encoding="utf-8")
    life = Path("app/services/robot_job_lifecycle.py").read_text(encoding="utf-8")
    assert "upsert_robot_job_from_extract" in api
    assert "jd_filename" in api
    assert "jd_text" in api
    assert "job_description_filename" in api
    assert "job_description" in life
    assert "job_description_filename" in life
    assert "contact_name" in api
    assert "contact_name" in life
    assert "Name the company, the job, and the contact" in api
    assert "indeed" not in api.lower()
    assert "hunter" not in api.lower()
    assert "apollo" not in api.lower()
