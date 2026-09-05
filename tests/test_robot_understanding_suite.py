"""
Legacy parallel-understanding suite retired.

Production path is match-url understanding → jobs:
  tests/test_robot_ready_to_jobs.py
  tests/test_robot_job_capability_match.py
"""
from __future__ import annotations

from app.services.robot_job_capability_match import match_robot_url


def test_production_path_uses_robot_ready_caps_not_envelope():
    """Regression: arbitrary URL with ready profile must return jobs (not fixture gate)."""
    result = match_robot_url(
        "https://www.agilityrobotics.com/",
        robot_capabilities={
            "type": "Warehouse/Logistics",
            "use_case": "Warehouse Logistics",
            "capabilities": ["cloud connected"],
            "profile_score": 68,
        },
        page_text="Digit humanoid robot. Warehouses. 100,000 Totes.",
    )
    assert result["state"] != "could_not_understand"
    assert len(result["jobs"]) > 0
    assert result.get("robot_capabilities") is not None
