"""Tests for serialized secondary-pass runner."""
from app.services import secondary_pass_runner as runner


def test_global_lock_prevents_overlap():
    runner._GLOBAL_LOCK.acquire()
    try:
        result = runner.run_leads_secondary_pass_sync(limit=1)
        assert result["status"] == "skipped"
        assert result["reason"] == "already_running"
    finally:
        runner._GLOBAL_LOCK.release()


def test_status_tracks_running():
    runner._set_running("leads")
    try:
        status = runner.get_secondary_pass_status()
        assert status["running"] == "leads"
        assert status["running_since"]
    finally:
        runner._set_running(None)


def test_start_thread_skips_when_busy():
    runner._set_running("full")
    try:
        out = runner.start_secondary_job_in_thread(
            runner.run_leads_secondary_pass_sync,
            job_kind="leads",
            limit=1,
        )
        assert out["status"] == "skipped"
    finally:
        runner._set_running(None)
