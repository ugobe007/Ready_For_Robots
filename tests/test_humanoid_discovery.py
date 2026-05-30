"""Humanoid discovery and AI HEIF agent tests."""
from unittest.mock import patch

from app.services.humanoid_discovery import _merge_candidates
from app.services.humanoid_scraper import agent_assess_humanoid, compute_scores
from app.services.humanoid_vendor_catalog import catalog_count, catalog_entries, slugify


def test_catalog_has_100_plus_entries():
    assert catalog_count() >= 100


def test_slugify():
    assert slugify("Unitree G1") == "unitree-g1"
    assert slugify("Agibot (Zhiyuan)") == "agibot-zhiyuan"


def test_merge_candidates_dedupes_by_slug():
    a = [{"name": "G1", "vendor": "Unitree", "model_slug": "unitree-g1", "specs": {"payload_kg": 3}}]
    b = [{"name": "G1", "vendor": "Unitree", "model_slug": "unitree-g1", "specs": {"top_speed_mps": 2.0}}]
    merged = _merge_candidates(a, b)
    assert len(merged) == 1
    assert merged[0]["specs"]["payload_kg"] == 3
    assert merged[0]["specs"]["top_speed_mps"] == 2.0


def test_agent_assess_fallback_without_llm():
    with patch("app.services.llm_client.llm_json_completion", return_value=None):
        result = agent_assess_humanoid(
            "Test Humanoid",
            "Unknown Startup Inc",
            status="research",
            existing_specs={"top_speed_mps": 0.5, "payload_kg": 1.0},
        )
    assert result["agent_scored"] is False
    assert "scores" in result
    assert 0 <= result["scores"]["heif_total"] <= 4


def test_agent_assess_applies_heif_json():
    fake = """
    {
      "status": "pilot",
      "specs": {"top_speed_mps": 2.0, "payload_kg": 10, "has_sdk": true},
      "heif": {
        "mobility": 3.0, "manipulation": 2.5, "cognition": 2.0,
        "safety": 1.5, "data_pipeline": 2.0, "production": 2.5
      },
      "confidence": 0.8,
      "evidence_summary": "Public demo data"
    }
    """
    with patch("app.services.llm_client.llm_json_completion", return_value=fake):
        result = agent_assess_humanoid("PNDbotics Adam", "PNDbotics", status="research")
    assert result["agent_scored"] is True
    assert result["scores"]["heif_mobility"] == 3.0
    assert result["scores"]["score_total"] == round(result["scores"]["heif_total"] * 25, 1)


def test_heir_override_wins_over_agent():
    fake = """
    {
      "status": "available",
      "specs": {"top_speed_mps": 2.0},
      "heif": {
        "mobility": 1.0, "manipulation": 1.0, "cognition": 1.0,
        "safety": 1.0, "data_pipeline": 1.0, "production": 1.0
      },
      "confidence": 0.9,
      "evidence_summary": "ignored for unitree"
    }
    """
    with patch("app.services.llm_client.llm_json_completion", return_value=fake):
        result = agent_assess_humanoid("Unitree G1", "Unitree Robotics", status="available")
    # HEIR research override should keep mobility 3.5 not agent 1.0
    assert result["scores"]["heif_mobility"] == 3.5


def test_catalog_entries_have_slugs():
    for entry in catalog_entries()[:20]:
        assert entry.get("model_slug")
        assert entry.get("vendor")
        assert entry.get("name")
