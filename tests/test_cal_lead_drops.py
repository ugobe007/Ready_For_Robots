"""Cal lead drops — preview cache builder."""
from app.services.cal_lead_drops import (
    _cal_personal_observation,
    _cal_prompt_for_tier,
    _recommended_action,
)


def test_cal_observation_hot():
    msg = _cal_personal_observation(
        "HOT",
        "Marriott",
        industry="Hospitality",
        signal_text="Labor pressure in recent OSHA filings",
    )
    assert "My read on Marriott" in msg
    assert "Marriott" in msg
    assert "prioritize" in msg.lower() or "reach out" in msg.lower()


def test_cal_prompt_hot():
    msg = _cal_prompt_for_tier("HOT", "Marriott")
    assert "send-ready draft" in msg.lower()
    assert "Marriott" in msg


def test_cal_prompt_warm():
    msg = _cal_prompt_for_tier("WARM", "White Castle")
    assert "brief" in msg.lower() or "talk track" in msg.lower()
    assert "White Castle" in msg


def test_recommended_action_hot():
    assert "48 hours" in _recommended_action("HOT")
