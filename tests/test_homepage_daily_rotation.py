"""Homepage spotlight rotates once per Pacific edition day (6am rollover)."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.api.leads import _spotlight_rotation_seeds
from app.services.homepage_rotation import (
    homepage_rotation_day,
    homepage_rotation_slot,
    homepage_spotlight_seeds,
)


LA = ZoneInfo("America/Los_Angeles")


def _la(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=LA).astimezone(timezone.utc)


def test_edition_day_rolls_at_6am_pacific():
    # 5:59am June 14 → still June 13 edition
    assert homepage_rotation_day(_la(2026, 6, 14, 5, 59)).isoformat() == "2026-06-13"
    # 6:00am June 14 → June 14 edition
    assert homepage_rotation_day(_la(2026, 6, 14, 6, 0)).isoformat() == "2026-06-14"


def test_spotlight_seeds_stable_within_edition_day():
    morning = _la(2026, 6, 14, 8, 0)
    evening = _la(2026, 6, 14, 20, 30)
    assert homepage_spotlight_seeds(morning) == homepage_spotlight_seeds(evening)


def test_spotlight_seeds_change_on_edition_rollover():
    late_night = _la(2026, 6, 14, 5, 30)
    after_rollover = _la(2026, 6, 14, 6, 15)
    assert homepage_spotlight_seeds(late_night) != homepage_spotlight_seeds(after_rollover)


def test_spotlight_seeds_change_across_calendar_days():
    day_a = _la(2026, 6, 14, 12, 0)
    day_b = _la(2026, 6, 15, 12, 0)
    assert homepage_rotation_slot(day_a) != homepage_rotation_slot(day_b)
    assert _spotlight_rotation_seeds(day_a) != _spotlight_rotation_seeds(day_b)
