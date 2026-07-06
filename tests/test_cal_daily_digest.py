"""Tests for Cal daily activity digest email."""
from datetime import datetime, timezone

from app.services.cal_daily_digest import (
    build_cal_daily_digest,
    get_cal_digest_recipients,
    next_digest_run_utc,
    render_cal_daily_digest_text,
    send_cal_daily_digest,
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
    )
    assert "Cal daily update — 2026-06-16" in text
    assert "Buyer intro emails sent: 3" in text
    assert "Autopilot: ON" in text
    assert "Drafts ready to send: 17" in text
    assert "Book meeting: Acme demo" in text


def test_next_digest_run_utc_is_in_future():
    target = next_digest_run_utc(hour=15, minute=0)
    assert target > datetime.now(timezone.utc)


def test_send_cal_daily_digest_skips_when_already_sent(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "ugobe07@gmail.com")
    monkeypatch.setattr(
        "app.services.cal_daily_digest._digest_already_sent",
        lambda day: True,
    )
    result = send_cal_daily_digest(None, force=False)
    assert result["sent"] is False
    assert result["reason"] == "Already sent today"


def test_build_cal_daily_digest_without_db_context(monkeypatch):
    """Smoke test: empty DB session still returns structured digest."""
    monkeypatch.setenv("ADMIN_EMAIL", "ugobe07@gmail.com")

    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
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

    digest = build_cal_daily_digest(FakeDB())
    assert digest["subject"].startswith("Cal daily update")
    assert "ugobe07@gmail.com" in digest["recipients"]
    assert "Buyer intro emails sent: 0" in digest["body_text"]
