"""
Homepage spotlight lead rotation — one edition per Pacific day.

Edition day rolls at 6:00am America/Los_Angeles (aligned with newsletter publish).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from app.services.pipeline_cache_policy import (
    HOMEPAGE_SPOTLIGHT_ROLLOVER_HOUR,
    HOMEPAGE_SPOTLIGHT_ROTATION_SEC,
    HOMEPAGE_SPOTLIGHT_TZ,
)


def _spotlight_tz() -> ZoneInfo:
    return ZoneInfo(HOMEPAGE_SPOTLIGHT_TZ)


def homepage_rotation_day(now: Optional[datetime] = None) -> date:
    """Calendar edition day — before rollover hour counts as the previous day."""
    ts = (now or datetime.now(timezone.utc)).astimezone(_spotlight_tz())
    if ts.hour < HOMEPAGE_SPOTLIGHT_ROLLOVER_HOUR:
        ts = ts - timedelta(days=1)
    return ts.date()


def homepage_rotation_slot(now: Optional[datetime] = None) -> int:
    """Stable slot index for the current Pacific edition day."""
    return homepage_rotation_day(now).toordinal()


def homepage_spotlight_seeds(now: Optional[datetime] = None) -> tuple[int, int, int]:
    """
    Deterministic HOT/WARM circular-pick seeds for homepage spotlight.
    Changes once per edition day (6am Pacific rollover).
    """
    ts = now or datetime.now(timezone.utc)
    day_o = homepage_rotation_slot(ts)
    h_seed = day_o * 7919 + 203
    w_seed = day_o * 9283 + 411
    return h_seed, w_seed, day_o


def homepage_spotlight_mix_meta(now: Optional[datetime] = None) -> dict:
    """Metadata embedded in GET /api/leads/homepage spotlightMix."""
    ts = (now or datetime.now(timezone.utc)).astimezone(_spotlight_tz())
    day = homepage_rotation_day(ts)
    return {
        "rotation_period_sec": HOMEPAGE_SPOTLIGHT_ROTATION_SEC,
        "rotation_slot": homepage_rotation_slot(ts),
        "rotation_day": str(day),
        "rotation_timezone": HOMEPAGE_SPOTLIGHT_TZ,
        "rotation_rollover_hour": HOMEPAGE_SPOTLIGHT_ROLLOVER_HOUR,
        "rotation_hour_local": ts.hour,
        "rotation_minute_local": ts.minute,
    }
