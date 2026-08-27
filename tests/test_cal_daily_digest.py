"""Tests for Cal daily activity digest email."""
from datetime import datetime, timezone

from app.services.cal_daily_digest import (
    build_cal_daily_digest,
    digest_in_process_owner,
    get_cal_digest_recipients,
    next_digest_run_utc,
    render_cal_daily_digest_text,
    send_cal_daily_digest,
    _claim_digest_day,
)


def test_get_cal_digest_recipients_prefers_explicit(monkeypatch):
    monkeypatch.setenv("CAL_DAILY_DIGEST_EMAIL", "ops@example.com, backup@example.com")
    monkeypatch.setenv("ADMIN_EMAILS", "ugobe07@gmail.com")
    assert get_cal_digest_recipients() == ["ops@example.com", "backup@example.com"]


def test_get_cal_digest_recipients_falls_back_to_admin(monkeypatch):
    monkeypatch.delenv("CAL_DAILY_DIGEST_EMAIL", raising=False)
    monkeypatch.setenv("ADMIN_EMAIL", "ugobe07@gmail.com")
    assert get_cal_digest_recipients() == ["ugobe07@gmail.com"]


def test_render_cal_daily_digest_text_includes_sections():
    text = render_cal_daily_digest_text(
        day_label="2026-06-16",
        period_hours=24,
        autopilot_on=True,
        queue_summary={"hot": 12, "warm": 45, "sendable": 17},
        activity={
            "intro_sent": 3,
            "followup_sent": 2,
            "replies": 1,
            "drafts_touched": 5,
            "enroll_active": 4,
            "enroll_due": 1,
            "sendable": 17,
            "unsent_drafted": 20,
            "replied_total": 2,
        },
        intro_lines=["  • 14:00 UTC — Acme — Subject line"],
        reply_lines=["  • 16:30 UTC — buyer@acme.com — Re: robots"],
        needs_you=["  • Book meeting: Acme demo"],
        jobs_activity={"matcher_seen": 4, "jobs_kept": 2, "applications": 1},
    )
    assert "ReadyForRobots daily — 2026-06-16" in text
    assert "FIND / matcher submissions seen: 4" in text
    assert "Jobs kept in CRM: 2" in text
    assert "Applications stored: 1" in text
    assert "Robot-sales intros sent: 3" in text
    assert "Autopilot: ON" in text
    assert "Frozen sales drafts (not a send list): 17" in text
    assert "Book meeting: Acme demo" in text
    assert "/pipeline?src=jobs_activate" in text
    assert "opportunity signals" not in text
    assert "sales teams should prioritize" not in text


def test_render_frozen_when_autopilot_off():
    text = render_cal_daily_digest_text(
        day_label="2026-08-27",
        period_hours=24,
        autopilot_on=False,
        queue_summary={"hot": 300, "warm": 0, "sendable": 7},
        activity={
            "intro_sent": 0,
            "followup_sent": 0,
            "replies": 0,
            "drafts_touched": 16,
            "enroll_active": 27,
            "enroll_due": 22,
            "sendable": 7,
            "unsent_drafted": 9,
            "replied_total": 0,
        },
        intro_lines=[],
        reply_lines=[],
        needs_you=[],
        jobs_activity={"matcher_seen": 1, "jobs_kept": 3, "applications": 0},
    )
    assert "Cal sales outreach is frozen" in text
    assert "Scheduled drafts created or refreshed: 0 (paused)" in text
    assert "Drafts created or refreshed: 16" not in text
    assert "22 due now — held" in text
    assert "HOT buyer queue is not a send list" in text
    assert "Industry brief" not in text
    assert "/inbox" not in text
    assert "/calendar" not in text


def test_render_explains_zero_intros_when_drafts_ready():
    """0 intros next to N 'ready' drafts must not read as a broken pipeline."""
    text = render_cal_daily_digest_text(
        day_label="2026-07-10",
        period_hours=24,
        autopilot_on=True,
        queue_summary={"hot": 298, "warm": 2, "sendable": 3},
        activity={
            "intro_sent": 0,
            "followup_sent": 10,
            "replies": 0,
            "drafts_touched": 56,
            "enroll_active": 214,
            "enroll_due": 0,
            "sendable": 3,
            "unsent_drafted": 3,
            "replied_total": 0,
        },
        intro_lines=[],
        reply_lines=[],
        needs_you=[],
    )
    assert "Follow-up emails sent: 10" in text
    assert "Why 0 new intros" in text
    assert "Robot Jobs, not robot sales" in text
    assert "verified contacts" not in text


def test_render_no_zero_intro_note_when_intros_sent():
    text = render_cal_daily_digest_text(
        day_label="2026-07-10",
        period_hours=24,
        autopilot_on=True,
        queue_summary={"hot": 10, "warm": 5, "sendable": 4},
        activity={"intro_sent": 4, "followup_sent": 1, "sendable": 4},
        intro_lines=["  • 14:00 UTC — Acme — Subject"],
        reply_lines=[],
        needs_you=[],
    )
    assert "Why 0 new intros" not in text


def test_render_oem_rejections_are_fyi_not_needs_you():
    """OEM/vendor auto-skips are Cal working correctly — FYI, not an action item."""
    text = render_cal_daily_digest_text(
        day_label="2026-07-10",
        period_hours=24,
        autopilot_on=True,
        queue_summary={"hot": 298, "warm": 2, "sendable": 3},
        activity={"intro_sent": 0, "followup_sent": 10, "sendable": 3},
        intro_lines=[],
        reply_lines=[],
        needs_you=[],
        auto_filtered=["  • Dobot Robotics: Zebra is an OEM/vendor, not a buyer"],
    )
    needs_you_idx = text.index("Needs you")
    fyi_idx = text.index("Auto-filtered by Cal")
    assert "no action needed" in text.lower()
    assert "Dobot Robotics" in text
    assert fyi_idx > needs_you_idx
    assert "Fix blocked draft" not in text


def test_next_digest_run_utc_is_in_future():
    target = next_digest_run_utc(hour=15, minute=0)
    assert target > datetime.now(timezone.utc)


def test_send_cal_daily_digest_skips_when_already_sent(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "ugobe07@gmail.com")
    monkeypatch.setattr(
        "app.services.cal_daily_digest._claim_digest_day",
        lambda day: False,
    )
    result = send_cal_daily_digest(None, force=False)
    assert result["sent"] is False
    assert result["reason"] == "Already sent today"


def test_claim_digest_day_is_atomic(monkeypatch):
    store: dict[str, str] = {}

    class FakeRedis:
        def get(self, key):
            return store.get(key)

        def set(self, key, value, nx=False, ex=None):
            if nx and key in store:
                return False
            store[key] = value
            return True

        def delete(self, key):
            store.pop(key, None)

    monkeypatch.setattr("app.services.cal_daily_digest._redis_client", lambda: FakeRedis())
    assert _claim_digest_day("2026-08-27") is True
    assert _claim_digest_day("2026-08-27") is False


def test_digest_in_process_owner_worker_only(monkeypatch):
    monkeypatch.setenv("ENABLE_SCHEDULED_CAL_DAILY_DIGEST", "1")
    monkeypatch.delenv("CAL_DAILY_DIGEST_ENABLED", raising=False)
    monkeypatch.delenv("CAL_DAILY_DIGEST_WEB_BACKUP", raising=False)
    monkeypatch.setattr("app.runtime_role.is_worker_process", lambda: True)
    monkeypatch.setattr("app.runtime_role.is_web_process", lambda: False)
    assert digest_in_process_owner() == "worker"

    monkeypatch.setattr("app.runtime_role.is_worker_process", lambda: False)
    monkeypatch.setattr("app.runtime_role.is_web_process", lambda: True)
    assert digest_in_process_owner() is None

    monkeypatch.setenv("CAL_DAILY_DIGEST_WEB_BACKUP", "1")
    assert digest_in_process_owner() == "web-backup"


def test_build_cal_daily_digest_without_db_context(monkeypatch):
    """Smoke test: empty DB session still returns structured digest."""
    monkeypatch.setenv("ADMIN_EMAIL", "ugobe07@gmail.com")
    monkeypatch.setenv("CAL_AUTONOMY_ENABLED", "0")
    monkeypatch.setenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "0")

    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def group_by(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def scalar(self):
            return 0

        def all(self):
            return []

    class FakeDB:
        def query(self, *args, **kwargs):
            return FakeQuery()

    monkeypatch.setattr(
        "app.services.cal_autonomy.resolve_cal_admin_context",
        lambda db: None,
    )
    monkeypatch.setattr(
        "app.services.cal_ops_monitor.get_cal_ops_monitor",
        lambda db, limit=5: {"assembly_rejections": []},
    )
    monkeypatch.setattr(
        "app.services.industry_brief_service.build_industry_brief_payload",
        lambda *a, **k: {
            "executive_take": (
                "In the past 24 hours we discovered 1452 opportunity signals. "
                "Sales teams should prioritize accounts in logistics."
            ),
            "source": "heuristic",
        },
    )

    digest = build_cal_daily_digest(FakeDB())
    assert digest["subject"].startswith("ReadyForRobots daily")
    assert "ugobe07@gmail.com" in digest["recipients"]
    assert "Robot-sales intros sent: 0" in digest["body_text"]
    assert "not waiting on a robot-sales send" in digest["body_text"]
    assert "Cal sales outreach is frozen" in digest["body_text"]
    assert "opportunity signals" not in digest["body_text"]
    assert "Sales teams should prioritize" not in digest["body_text"]
    assert "Industry brief" not in digest["body_text"]
    assert "/pipeline?src=jobs_activate" in digest["body_text"]
