#!/usr/bin/env python3
"""Public probe: is Hermes research reaching ReadyForRobots?

Hermes (Nous agent on the Mac) curls Fly ingest with X-Admin-Key. This script
does not need that key. It reports overlay coverage on the public pipeline and
market-graph snapshot freshness.

  python3 scripts/hermes_health_probe.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from typing import Any

FLY = "https://ready-2-robot.fly.dev"
PIPELINE = f"{FLY}/api/leads/pipeline"
STATUS = f"{FLY}/api/v1/market-graph/status"


def _get(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "rfr-hermes-health"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def overlay_counts(leads: list[dict[str, Any]]) -> dict[str, int]:
    filled = 0
    qualify = 0
    jobs = 0
    dms = 0
    windows = 0
    videos = 0
    for row in leads:
        hq = row.get("hermes_qualify") or row.get("hermesQualify")
        hj = row.get("hermes_job_titles") or row.get("hermesJobTitles") or []
        hd = row.get("hermes_decision_makers") or row.get("hermesDecisionMakers") or []
        hb = row.get("hermes_buying_window") or row.get("hermesBuyingWindow")
        hv = row.get("hermes_video_evidence") or row.get("hermesVideoEvidence")
        if hq:
            qualify += 1
        if hj:
            jobs += 1
        if hd:
            dms += 1
        if hb:
            windows += 1
        if hv:
            videos += 1
        if hq or hj or hd or hb or hv:
            filled += 1
    return {
        "leads": len(leads),
        "any_overlay": filled,
        "hermes_qualify": qualify,
        "hermes_job_titles": jobs,
        "hermes_decision_makers": dms,
        "hermes_buying_window": windows,
        "hermes_video_evidence": videos,
    }


def main() -> int:
    pipe = _get(PIPELINE)
    leads = list(pipe.get("leads") or [])
    counts = overlay_counts(leads)
    status = _get(STATUS)
    snap = (status.get("snapshot") or {}) if isinstance(status, dict) else {}
    sched = (status.get("scheduler") or {}) if isinstance(status, dict) else {}

    report = {
        "pipeline_built_at": pipe.get("built_at"),
        "overlays": counts,
        "market_graph_generated_at": snap.get("generated_at"),
        "market_graph_status": snap.get("status"),
        "scheduler_running": sched.get("running"),
        "scheduler_last_run": sched.get("last_run"),
    }
    print(json.dumps(report, indent=2, default=str))

    if counts["leads"] and counts["any_overlay"] == 0:
        print(
            "\nHermes overlays are empty on the public pipeline. "
            "Mac crons are not reaching Fly ingest (gateway down, leftover "
            "--provider ai-gateway 402, or RFR_ADMIN_KEY ≠ Fly ADMIN_KEY).",
            file=sys.stderr,
        )
        print(
            "On the Mac: hermes doctor --fix && hermes gateway start && "
            "hermes cron list  # jobs must be terminal curl, not ai-gateway",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
