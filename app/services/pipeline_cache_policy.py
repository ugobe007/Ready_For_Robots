"""
Pipeline / sales-lead public cache cadence.

Defaults: rebuild durable caches every 30 minutes and rotate which leads
appear in each build (aligned to the same window). Override via env on Fly.
"""
from __future__ import annotations

import os

# How often the in-app loop (and recommended cron) rebuilds pipeline surfaces.
PUBLIC_CACHE_REFRESH_INTERVAL_SEC = int(
    os.getenv("PUBLIC_CACHE_REFRESH_INTERVAL_SEC", str(30 * 60))
)

# Lead rotation window — defaults to the refresh interval so each rebuild shows a new slice.
PIPELINE_LEADS_ROTATION_SEC = int(
    os.getenv(
        "PIPELINE_LEADS_ROTATION_SEC",
        str(PUBLIC_CACHE_REFRESH_INTERVAL_SEC),
    )
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
