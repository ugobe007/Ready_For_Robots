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
    assert "indeed" not in api.lower()
    assert "hunter" not in api.lower()
    assert "apollo" not in api.lower()
