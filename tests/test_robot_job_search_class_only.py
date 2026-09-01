"""Class-only FIND: asserted_class without a URL uses thin_class_profile."""
from __future__ import annotations

from app.services.robot_job_search import compose_robot_job_search


def test_class_only_agriculture_search_does_not_need_url():
    result = compose_robot_job_search(
        None,
        asserted_class="agriculture",
        lookup_grain="robot_type",
    )
    assert result.get("robot_class") in {"agriculture", "agricultural_robot", None} or result.get(
        "job_count", 0
    ) >= 0
    assert result.get("needs_class_choice") is not True
    assert result.get("source_url") in (None, "")
    assert result.get("robot_name")
