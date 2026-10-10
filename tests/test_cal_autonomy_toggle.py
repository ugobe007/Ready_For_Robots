import pytest
from app.services.cal_autonomy import (
    _cal_autonomy_env_default,
    cal_autonomy_enabled,
    get_cal_autonomy_runtime_override,
    set_cal_autonomy_runtime_override,
)
import app.services.cal_autonomy as cal_autonomy_mod


@pytest.fixture(autouse=True)
def reset_autonomy_override():
    cal_autonomy_mod._IN_MEMORY_AUTONOMY_OVERRIDE = None
    yield
    cal_autonomy_mod._IN_MEMORY_AUTONOMY_OVERRIDE = None


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


def test_cal_autonomy_in_memory_fallback_no_redis(monkeypatch):
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "0")
    monkeypatch.setattr("app.services.cal_autonomy._redis_client", lambda: None)

    # Initially off because env is 0 and override is None
    assert cal_autonomy_enabled() is False

    # Setting override to True succeeds even without Redis
    ok = set_cal_autonomy_runtime_override(True)
    assert ok is True
    assert get_cal_autonomy_runtime_override() is True
    assert cal_autonomy_enabled() is True


