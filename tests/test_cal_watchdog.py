"""Cal worker watchdog — heartbeat + stale-detection + alert/recovery."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from app.services import cal_watchdog


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, k):
        return self.store.get(k)

    def set(self, k, v, ex=None):
        self.store[k] = v

    def delete(self, *ks):
        for k in ks:
            self.store.pop(k, None)


@pytest.fixture()
def fake(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(cal_watchdog, "_redis_client", lambda: r)
    monkeypatch.setenv("CAL_WATCHDOG_ENABLED", "1")
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "1")
    monkeypatch.setenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "1")
    monkeypatch.setenv("CAL_WATCHDOG_STALE_MINUTES", "30")
    return r


@pytest.fixture()
def sent(monkeypatch):
    calls = []
    monkeypatch.setattr(cal_watchdog, "_send_alert_email", lambda s, b: calls.append((s, b)) or True)
    return calls


def _write_heartbeat(fake, *, minutes_ago=0.0, status="tick"):
    ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    fake.store[cal_watchdog._HEARTBEAT_KEY] = json.dumps({"ts": ts.isoformat(), "status": status})


def test_record_and_age(fake):
    assert cal_watchdog.record_cal_heartbeat("tick") is True
    age = cal_watchdog.cal_heartbeat_age_seconds()
    assert age is not None and age < 5


def test_status_fresh_not_stale(fake):
    _write_heartbeat(fake, minutes_ago=1)
    st = cal_watchdog.watchdog_status()
    assert st["stale"] is False
    assert st["age_seconds"] is not None


def test_status_missing_is_stale(fake):
    st = cal_watchdog.watchdog_status()
    assert st["stale"] is True
    assert st["age_seconds"] is None


def test_check_ok_when_fresh(fake, sent):
    _write_heartbeat(fake, minutes_ago=2)
    res = cal_watchdog.check_and_alert()
    assert res["action"] == "ok"
    assert sent == []


def test_check_alerts_when_stale_then_cooldown(fake, sent):
    _write_heartbeat(fake, minutes_ago=90)  # > 30 min threshold
    res = cal_watchdog.check_and_alert()
    assert res["action"] == "alert"
    assert len(sent) == 1
    # Second pass while still stale → suppressed by cooldown.
    res2 = cal_watchdog.check_and_alert()
    assert res2["action"] == "cooldown"
    assert len(sent) == 1


def test_check_alerts_when_no_heartbeat(fake, sent):
    res = cal_watchdog.check_and_alert()
    assert res["action"] == "alert"
    assert len(sent) == 1
    assert "never" in sent[0][1].lower()


def test_recovery_notice_after_alert(fake, sent):
    _write_heartbeat(fake, minutes_ago=90)
    cal_watchdog.check_and_alert()  # arms alert + cooldown
    assert len(sent) == 1
    # Worker recovers.
    _write_heartbeat(fake, minutes_ago=0)
    res = cal_watchdog.check_and_alert()
    assert res["action"] == "recovered"
    assert len(sent) == 2
    assert "recovered" in sent[1][0].lower()
    # State cleared → next healthy pass is a plain ok.
    res2 = cal_watchdog.check_and_alert()
    assert res2["action"] == "ok"


def test_skips_when_cal_disabled(fake, sent, monkeypatch):
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "0")
    _write_heartbeat(fake, minutes_ago=90)
    res = cal_watchdog.check_and_alert()
    assert res["checked"] is False
    assert res["reason"] == "cal_disabled"
    assert sent == []


def test_disabled_watchdog_noops(fake, sent, monkeypatch):
    monkeypatch.setenv("CAL_WATCHDOG_ENABLED", "0")
    res = cal_watchdog.check_and_alert()
    assert res["checked"] is False
    assert res["reason"] == "disabled"
    assert sent == []


def test_autostart_starts_stopped_worker(fake, sent, monkeypatch):
    monkeypatch.setenv("FLY_API_TOKEN", "tok")
    monkeypatch.setenv("FLY_APP_NAME", "ready-2-robot")
    calls = []

    def fake_api(method, path, timeout=10.0):
        calls.append((method, path))
        if method == "GET":
            return 200, [
                {"id": "web1", "state": "started",
                 "config": {"metadata": {"fly_process_group": "web"}}},
                {"id": "wk1", "state": "stopped",
                 "config": {"metadata": {"fly_process_group": "worker"}}},
            ]
        return 200, {"ok": True}

    monkeypatch.setattr(cal_watchdog, "_fly_machines_api", fake_api)
    _write_heartbeat(fake, minutes_ago=90)  # stale → triggers self-heal + alert

    res = cal_watchdog.check_and_alert()
    assert res["action"] == "alert"
    assert res["autostart"]["started"] == ["wk1"]
    # only the stopped worker is started — web is left alone
    assert ("POST", "/v1/apps/ready-2-robot/machines/wk1/start") in calls
    assert ("POST", "/v1/apps/ready-2-robot/machines/web1/start") not in calls
    # email reflects the auto-restart
    assert "auto-restart" in sent[0][0].lower()


def test_no_autostart_without_token(fake, sent, monkeypatch):
    monkeypatch.delenv("FLY_API_TOKEN", raising=False)
    monkeypatch.delenv("FLY_MACHINES_TOKEN", raising=False)
    _write_heartbeat(fake, minutes_ago=90)
    res = cal_watchdog.check_and_alert()
    assert res["action"] == "alert"
    assert res["autostart"] == {"attempted": False, "reason": "no_token"}
    # falls back to the manual-recovery alert
    assert "heartbeat stale" in sent[0][0].lower()
