"""Humanoid discovery and AI HEIF agent tests."""
from unittest.mock import patch

from app.services.humanoid_discovery import _merge_candidates
from app.services.humanoid_scraper import agent_assess_humanoid, compute_scores
from app.services.humanoid_vendor_catalog import catalog_count, catalog_entries, slugify


def test_catalog_has_real_oem_entries():
    assert catalog_count() >= 50


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


def test_rescore_existing_skips_after_agent_budget(monkeypatch):
    """rescore_existing should not rule-based rewrite entire catalog."""
    from app.services import humanoid_discovery as hd

    calls = {"agent": 0, "upsert": 0}

    def fake_agent(*args, **kwargs):
        calls["agent"] += 1
        return {
            "status": "research",
            "specs": {},
            "scores": {
                "heif_mobility": 1.0, "heif_manipulation": 1.0, "heif_cognition": 1.0,
                "heif_safety": 1.0, "heif_data_pipeline": 1.0, "heif_production": 1.0,
                "heif_total": 1.0, "score_total": 25.0,
                "score_mobility": 25.0, "score_manipulation": 25.0, "score_cognition": 25.0,
                "score_autonomy": 25.0, "score_safety": 25.0, "score_data_pipeline": 25.0,
                "score_endurance": 25.0, "score_production": 25.0, "score_market_readiness": 25.0,
            },
            "agent_scored": True,
            "evidence_summary": "test",
        }

    def fake_upsert(db, robot, **kwargs):
        calls["upsert"] += 1
        return "updated"

    monkeypatch.setattr(hd, "agent_assess_humanoid", fake_agent)
    monkeypatch.setattr(hd, "upsert_humanoid_robot", fake_upsert)
    monkeypatch.setattr(hd, "_catalog_candidates", lambda: [
        {"name": f"R{i}", "vendor": f"V{i}", "model_slug": f"r{i}", "status": "research", "specs": {}}
        for i in range(5)
    ])
    monkeypatch.setattr(hd, "_robot_company_candidates", lambda db: [])
    monkeypatch.setattr(hd, "_news_candidates", lambda max_queries=0: [])
    monkeypatch.setattr(hd, "_existing_slugs", lambda db: {f"r{i}" for i in range(5)})

    class FakeDb:
        def commit(self):
            pass

        def execute(self, *args, **kwargs):
            class R:
                def scalar(self):
                    return 5
            return R()

    stats = hd.run_humanoid_discovery(
        FakeDb(),
        use_catalog=True,
        use_robot_companies=False,
        news_queries=0,
        agent_limit=2,
        rescore_existing=True,
    )
    assert calls["agent"] == 2
    assert calls["upsert"] == 2
    assert stats["skipped"] == 3
