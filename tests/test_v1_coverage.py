"""V1 coverage constants."""
from app.domain.v1_coverage import (
    SUPPORTED_V1_CATEGORIES,
    V1_HUMANOID_INDUSTRIES,
    V1_TARGET_INDUSTRIES,
)


def test_humanoid_in_v1_categories():
    assert "humanoid" in SUPPORTED_V1_CATEGORIES


def test_target_industries_include_requested_verticals():
    needed = {
        "Hospitality",
        "Healthcare",
        "Manufacturing",
        "Food Service",
        "Casinos & Gaming",
        "Retail",
        "Defense",
    }
    assert needed <= set(V1_TARGET_INDUSTRIES)
    assert needed <= set(V1_HUMANOID_INDUSTRIES)


def test_commercial_maturity_constant_matches_ontology():
    from app.domain.enums import commercial_maturity_states
    from app.domain.v1_coverage import COMMERCIAL_MATURITY

    assert COMMERCIAL_MATURITY == commercial_maturity_states()
