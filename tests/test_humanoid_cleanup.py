"""Humanoid benchmark cleanup tests."""
from app.services.humanoid_catalog_cleanup import (
    cleanup_humanoid_benchmarks,
    is_excluded_humanoid_slug,
    is_junk_humanoid_row,
)
from app.services.humanoid_vendor_catalog import catalog_count


def test_deployment_pilot_slug_excluded():
    assert is_excluded_humanoid_slug("bmw-figure-pilot")
    assert is_excluded_humanoid_slug("amazon-digit")


def test_duplicate_variant_excluded():
    assert is_excluded_humanoid_slug("figure-01")
    assert is_excluded_humanoid_slug("zhiyuan-lingxi")


def test_news_junk_detected():
    assert is_junk_humanoid_row(
        "The 15 coolest things I saw Humanoid",
        "The 15 coolest things I saw",
        "the-15-coolest-things-i-saw",
    )


def test_vendor_placeholder_detected():
    assert is_junk_humanoid_row("Unitree Robotics Humanoid", "Unitree Robotics", "unitree-robotics")


def test_real_robot_kept():
    assert not is_junk_humanoid_row("Unitree G1", "Unitree Robotics", "unitree-g1")
    assert not is_junk_humanoid_row("Figure 02", "Figure AI", "figure-02")


def test_catalog_filters_excluded_entries():
    assert catalog_count() < 187


def test_cleanup_dry_run():
    class FakeDb:
        def execute(self, *args, **kwargs):
            class R:
                def mappings(self):
                    return self

                def all(self):
                    return [
                        {"id": 1, "model_slug": "unitree-g1", "name": "Unitree G1", "vendor": "Unitree"},
                        {"id": 2, "model_slug": "bmw-figure", "name": "BMW Figure Pilot", "vendor": "BMW"},
                    ]

            return R()

        def commit(self):
            pass

    result = cleanup_humanoid_benchmarks(FakeDb(), dry_run=True)
    assert result["removed"] == 1
    assert "bmw-figure" in result["removed_slugs"]
