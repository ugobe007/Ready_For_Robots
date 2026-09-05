"""Humanoid benchmark cleanup tests."""
from app.services.humanoid_catalog_cleanup import (
    cleanup_humanoid_benchmarks,
    is_excluded_humanoid_slug,
    is_junk_humanoid_row,
    vendor_duplicate_rows,
)
from app.services.humanoid_vendor_catalog import catalog_count, catalog_entries


def test_deployment_pilot_slug_excluded():
    assert is_excluded_humanoid_slug("bmw-figure-pilot")
    assert is_excluded_humanoid_slug("amazon-digit")


def test_same_robot_duplicate_slug_excluded():
    assert is_excluded_humanoid_slug("zhiyuan-lingxi")
    assert not is_excluded_humanoid_slug("figure-01")
    assert not is_excluded_humanoid_slug("unitree-h1")


def test_news_junk_detected():
    assert is_junk_humanoid_row(
        "The 15 coolest things I saw Humanoid",
        "The 15 coolest things I saw",
        "the-15-coolest-things-i-saw",
    )


def test_ipo_headline_is_junk():
    assert is_junk_humanoid_row(
        "China's humanoid robotics startup Unitree fast-tracks Shanghai IPO with target US$6.2 billion valuation",
        "Unitree Robotics",
        "unitree-robotics-china-s-humanoid-robotics-startup",
    )


def test_is_news_headline_robot_name():
    from app.services.humanoid_catalog_cleanup import is_news_headline_robot_name

    assert is_news_headline_robot_name(
        "China's humanoid robotics startup Unitree fast-tracks Shanghai IPO with target US$6.2 billion valuation"
    )
    assert not is_news_headline_robot_name("Unitree G1")


def test_screenshot_headlines_are_junk():
    """RSS titles mistaken for robot SKUs (production index pollution)."""
    assert is_junk_humanoid_row(
        "China Assigns Digital Identity Codes to Thousands of Humanoid Robots",
        "CA",
        "china-assigns-digital-identity",
    )
    assert is_junk_humanoid_row(
        "BMW to deploy humanoid robots at Leipzig plant",
        "BM",
        "bmw-to-deploy-humanoid-robots",
    )
    assert is_junk_humanoid_row(
        "Apptronik Scores $935 Million, Hits Top 3 For Humanoid Robotics Funding",
        "Apptronik",
        "apptronik-scores-935-million",
    )

def test_vendor_placeholder_detected():
    assert is_junk_humanoid_row("Unitree Robotics Humanoid", "Unitree Robotics", "unitree-robotics")
    assert is_junk_humanoid_row("Figure Humanoid", "Figure AI", "figure-humanoid")
    assert is_junk_humanoid_row("Boston Dynamics Humanoid", "Boston Dynamics", "boston-dynamics")


def test_real_robot_kept():
    assert not is_junk_humanoid_row("Unitree G1", "Unitree Robotics", "unitree-g1")
    assert not is_junk_humanoid_row("Unitree H1", "Unitree Robotics", "unitree-h1")
    assert not is_junk_humanoid_row("Figure 01", "Figure AI", "figure-01")
    assert not is_junk_humanoid_row("Figure 02", "Figure AI", "figure-02")
    assert not is_junk_humanoid_row("Reflex Humanoid", "Reflex Robotics", "reflex-humanoid")


def test_catalog_filters_excluded_entries():
    assert catalog_count() >= 80


def test_catalog_allows_multiple_models_per_vendor():
    from collections import defaultdict

    from app.services.humanoid_catalog_cleanup import vendor_key

    by = defaultdict(list)
    for e in catalog_entries():
        by[vendor_key(e["vendor"])].append(e["model_slug"])
    figure = by["figure ai"]
    unitree = by["unitree"]
    assert "figure-01" in figure
    assert "figure-02" in figure
    assert "unitree-g1" in unitree
    assert "unitree-h1" in unitree


def test_vendor_duplicate_removal():
    rows = [
        {"id": 1, "model_slug": "figure-02", "name": "Figure 02", "vendor": "Figure AI", "heif_total": 2.5},
        {"id": 2, "model_slug": "figure-01", "name": "Figure 01", "vendor": "Figure AI", "heif_total": 2.0},
        {"id": 3, "model_slug": "figure-ai", "name": "Figure AI Humanoid", "vendor": "Figure AI", "heif_total": 1.0},
        {"id": 4, "model_slug": "boston-dynamics-atlas", "name": "Boston Dynamics Atlas", "vendor": "Boston Dynamics", "heif_total": 2.8},
        {"id": 5, "model_slug": "boston-dynamics", "name": "Boston Dynamics Humanoid", "vendor": "Boston Dynamics", "heif_total": 1.0},
    ]
    dupes = vendor_duplicate_rows(rows)
    slugs = {r["model_slug"] for r in dupes}
    assert slugs == {"figure-ai", "boston-dynamics"}
    assert "figure-01" not in slugs
    assert "figure-02" not in slugs


def test_cleanup_dry_run():
    class FakeDb:
        def execute(self, *args, **kwargs):
            class R:
                def mappings(self):
                    return self

                def all(self):
                    return [
                        {"id": 1, "model_slug": "unitree-g1", "name": "Unitree G1", "vendor": "Unitree Robotics", "heif_total": 2.3, "score_total": 58.0},
                        {"id": 2, "model_slug": "bmw-figure", "name": "BMW Figure Pilot", "vendor": "BMW", "heif_total": 1.0, "score_total": 25.0},
                    ]

            return R()

        def commit(self):
            pass

    result = cleanup_humanoid_benchmarks(FakeDb(), dry_run=True)
    assert result["removed"] == 1
    assert "bmw-figure" in result["removed_slugs"]
