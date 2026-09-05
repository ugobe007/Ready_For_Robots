from app.services.cal_autonomy import (
    _cal_autonomy_env_default,
    cal_autonomy_enabled,
    get_cal_autonomy_runtime_override,
    set_cal_autonomy_runtime_override,
)


def test_cal_autonomy_runtime_override(monkeypatch):
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "1")
    store: dict[str, str] = {}

    class FakeRedis:
        def get(self, key):
            return store.get(key)

        def set(self, key, value):
            store[key] = value

    monkeypatch.setattr("app.services.cal_autonomy._redis_client", lambda: FakeRedis())

    assert _cal_autonomy_env_default() is True
    assert cal_autonomy_enabled() is True
    assert get_cal_autonomy_runtime_override() is None

    set_cal_autonomy_runtime_override(False)
    assert get_cal_autonomy_runtime_override() is False
    assert cal_autonomy_enabled() is False

    set_cal_autonomy_runtime_override(True)
    assert cal_autonomy_enabled() is True
