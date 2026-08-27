"""Gates: scheduled Cal drafts/follow-ups stay off when autopilot is off."""
from app.services.cal_autonomy import (
    _draft_and_store,
    cal_scheduled_sales_work_enabled,
    get_cal_autonomy_status,
    run_cal_autonomy_cycle,
)
from app.services.sequence_runner import process_due_enrollments


def test_scheduled_sales_work_follows_autonomy_flag(monkeypatch):
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "0")
    monkeypatch.setenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "0")
    monkeypatch.setattr(
        "app.services.cal_autonomy.get_cal_autonomy_runtime_override",
        lambda: True,
    )
    assert cal_scheduled_sales_work_enabled() is False
    status = get_cal_autonomy_status()
    assert status["scheduled_drafts_paused"] is True
    assert status["followups_paused"] is True
    assert status["buyer_sales_enabled"] is False


def test_draft_and_store_noops_when_autopilot_off(monkeypatch):
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "0")
    drafted, refreshed = _draft_and_store(
        None,
        company=object(),
        acct=None,
        team=None,
        existing={},
        regenerate=True,
        stale_before=None,
    )
    assert drafted is False
    assert refreshed is False


def test_process_due_enrollments_held_when_autopilot_off(monkeypatch):
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "0")
    result = process_due_enrollments(None, limit=50)
    assert result["sent"] == 0
    assert result["status"] == "paused"
    assert "held" in result["reason"]


def test_scheduled_cycle_disabled_does_not_send(monkeypatch):
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "0")
    monkeypatch.setenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "0")
    result = run_cal_autonomy_cycle(None)
    assert result["status"] == "disabled"
    assert result["sent"] == 0
    assert result["drafted"] == 0
    assert result["followups"]["sent"] == 0
    assert result["followups"]["status"] == "paused"
