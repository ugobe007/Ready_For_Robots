"""Post-deploy pipeline refresh must not rebuild inside the web process."""

from app.api.admin_lead_ops import refresh_pipeline_public_caches
from app.services.public_surface_cache import (
    consume_pipeline_refresh_request,
    schedule_public_cache_refresh,
)
from scripts.refresh_pipeline_cache import _pipeline_cache_status


def test_web_process_does_not_start_a_rebuild(monkeypatch):
    monkeypatch.setenv("RFR_PROCESS_ROLE", "web")
    assert schedule_public_cache_refresh(reason="deploy") is False


def test_admin_refresh_on_web_only_queues(monkeypatch):
    monkeypatch.setattr("app.runtime_role.is_web_process", lambda: True)
    seen = {}

    def _queue(db):
        seen["db"] = db
        return {"requested_at": "2026-10-17T00:00:00+00:00"}

    monkeypatch.setattr(
        "app.services.public_surface_cache.request_worker_pipeline_refresh",
        _queue,
    )
    db = object()
    out = refresh_pipeline_public_caches(db=db)
    assert out["status"] == "queued"
    assert out["runner"] == "worker"
    assert seen["db"] is db


def test_worker_runs_a_newer_request_once(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.services.public_surface_cache.read_public_cache",
        lambda key, **kwargs: {"requested_at": "t1"},
    )
    monkeypatch.setattr(
        "app.services.public_surface_cache.claim_pipeline_refresh_request",
        lambda requested_at: True,
    )

    def _start(**kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(
        "app.services.public_surface_cache.schedule_public_cache_refresh",
        _start,
    )
    assert consume_pipeline_refresh_request("") == "t1"
    assert consume_pipeline_refresh_request("t1") == "t1"
    assert calls == [{"pipeline_only": True, "reason": "worker_request"}]


def test_a_second_worker_does_not_start_another_rebuild(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.services.public_surface_cache.read_public_cache",
        lambda key, **kwargs: {"requested_at": "t1"},
    )
    monkeypatch.setattr(
        "app.services.public_surface_cache.claim_pipeline_refresh_request",
        lambda requested_at: False,
    )
    monkeypatch.setattr(
        "app.services.public_surface_cache.schedule_public_cache_refresh",
        lambda **kwargs: calls.append(kwargs) or True,
    )
    assert consume_pipeline_refresh_request("") == "t1"
    assert calls == []


def test_in_flight_rebuild_leaves_the_request_pending(monkeypatch):
    monkeypatch.setattr(
        "app.services.public_surface_cache._refresh_in_progress",
        True,
    )
    monkeypatch.setattr(
        "app.services.public_surface_cache.read_public_cache",
        lambda key, **kwargs: {"requested_at": "t2"},
    )
    monkeypatch.setattr(
        "app.services.public_surface_cache.schedule_public_cache_refresh",
        lambda **kwargs: False,
    )
    assert consume_pipeline_refresh_request("") == ""


def test_status_poll_reads_the_durable_row(monkeypatch):
    captured = {}

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"built_at": "2026-10-17T00:00:00Z", "leads": [{}], "cache_pending": False}

    class _Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, headers=None):
            captured["url"] = url
            return _Response()

    monkeypatch.setattr("httpx.Client", _Client)
    status = _pipeline_cache_status("https://ready-2-robot.fly.dev")
    assert captured["url"].endswith("/api/leads/pipeline?durable=1")
    assert status["built_at"] == "2026-10-17T00:00:00Z"
    assert status["leads_count"] == 1
