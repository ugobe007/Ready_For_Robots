"""HEIF / HEIR-aligned humanoid scoring tests."""
from app.services.humanoid_scraper import (
    SEED_ROBOTS,
    apply_heif_research,
    compute_scores,
    heif_total,
    infer_heif_scores,
)


def test_unitree_gets_heir_research_override():
    g1 = next(r for r in SEED_ROBOTS if r["model_slug"] == "unitree-g1")
    scores = compute_scores(g1["specs"], status=g1["status"], vendor=g1["vendor"])
    assert scores["heif_mobility"] == 3.5
    assert scores["heif_cognition"] == 1.5
    assert scores["heif_data_pipeline"] == 2.0
    assert scores["heif_production"] == 3.5
    assert scores["score_total"] == round(scores["heif_total"] * 25, 1)


def test_figure_ai_research_scores():
    fig = next(r for r in SEED_ROBOTS if r["model_slug"] == "figure-02")
    scores = compute_scores(fig["specs"], status=fig["status"], vendor=fig["vendor"])
    assert scores["heif_cognition"] == 3.5
    assert scores["heif_manipulation"] == 3.0


def test_unknown_vendor_uses_spec_inference():
    specs = {
        "top_speed_mps": 0.5,
        "payload_kg": 1.0,
        "finger_count": 0,
        "has_estop": False,
        "collision_force_n": 600,
        "autonomy_level": "research",
        "commercial_deployments": 0,
    }
    inferred = infer_heif_scores(specs, status="research")
    merged = apply_heif_research("Unknown Startup Inc", inferred)
    assert merged == inferred
    assert all(0 <= merged[d] <= 4 for d in merged)


def test_index_is_heif_times_25():
    digit = next(r for r in SEED_ROBOTS if r["model_slug"] == "agility-digit")
    scores = compute_scores(digit["specs"], status=digit["status"], vendor=digit["vendor"])
    assert scores["score_mobility"] == round(scores["heif_mobility"] * 25, 1)
    assert scores["score_autonomy"] == scores["score_cognition"]
    assert scores["score_endurance"] == scores["score_data_pipeline"]
    assert scores["score_market_readiness"] == scores["score_production"]
    assert scores["heif_total"] == heif_total(
        {
            "mobility": scores["heif_mobility"],
            "manipulation": scores["heif_manipulation"],
            "cognition": scores["heif_cognition"],
            "safety": scores["heif_safety"],
            "data_pipeline": scores["heif_data_pipeline"],
            "production": scores["heif_production"],
        }
    )
