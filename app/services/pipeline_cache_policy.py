"""
Pipeline / sales-lead public cache cadence.

Defaults: rebuild durable caches every 30 minutes. Pipeline list rotation uses
the refresh interval; homepage spotlight rotates once per Pacific edition day
(6am America/Los_Angeles). Override via env on Fly.
"""
from __future__ import annotations

import os

# How often the in-app loop (and recommended cron) rebuilds pipeline surfaces.
PUBLIC_CACHE_REFRESH_INTERVAL_SEC = int(
    os.getenv("PUBLIC_CACHE_REFRESH_INTERVAL_SEC", str(30 * 60))
)

# Pipeline feed / leads list rotation — defaults to the refresh interval.
PIPELINE_LEADS_ROTATION_SEC = int(
    os.getenv(
        "PIPELINE_LEADS_ROTATION_SEC",
        str(PUBLIC_CACHE_REFRESH_INTERVAL_SEC),
    )
)

# Homepage right-panel spotlight — one edition per day (rolls at 6am Pacific).
HOMEPAGE_SPOTLIGHT_ROTATION_SEC = int(
    os.getenv("HOMEPAGE_SPOTLIGHT_ROTATION_SEC", str(24 * 60 * 60))
)
HOMEPAGE_SPOTLIGHT_TZ = os.getenv("HOMEPAGE_SPOTLIGHT_TZ", "America/Los_Angeles")
HOMEPAGE_SPOTLIGHT_ROLLOVER_HOUR = int(
    os.getenv("HOMEPAGE_SPOTLIGHT_ROLLOVER_HOUR", "6")
)

# Durable row TTL (minutes). Slightly longer than refresh so stale data serves during rebuild.
PUBLIC_CACHE_TTL_MINUTES = int(
    os.getenv(
        "PUBLIC_CACHE_TTL_MINUTES",
        str(max(35, PUBLIC_CACHE_REFRESH_INTERVAL_SEC // 60 + 5)),
    )
)

# GET handlers schedule a background rebuild when L1 age exceeds this (seconds).
PUBLIC_CACHE_REVALIDATE_SEC = int(
    os.getenv(
        "PUBLIC_CACHE_REVALIDATE_SEC",
        str(PUBLIC_CACHE_REFRESH_INTERVAL_SEC),
    )
)
