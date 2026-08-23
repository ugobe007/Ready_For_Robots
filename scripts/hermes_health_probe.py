#!/usr/bin/env python3
"""Public probe: is Hermes research reaching ReadyForRobots?

Hermes (Nous agent on the Mac) curls Fly ingest with X-Admin-Key. This script
does not need that key. It reports overlay coverage on the public pipeline,
market-graph snapshot freshness, and the unauthenticated ingest contract.

  python3 scripts/hermes_health_probe.py
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

FLY = "https://ready-2-robot.fly.dev"
PIPELINE = f"{FLY}/api/leads/pipeline"
STATUS = f"{FLY}/api/v1/market-graph/status"
OPENAPI = f"{FLY}/openapi.json"
RECONSTRUCT = f"{FLY}/api/v1/market-graph/reconstruct"
INFER = f"{FLY}/api/v1/market-graph/infer-qualify"

HERMES_INGEST_PATHS = [
    "/api/v1/market-graph/job-signals/ingest",
    "/api/v1/market-graph/qualify-overlay",
    "/api/v1/market-graph/infer-qualify",
    "/api/v1/market-graph/contacts/ingest",
    "/api/v1/market-graph/vendor-news/ingest",
    "/api/v1/market-graph/deployment-evidence/ingest",
    "/api/v1/market-graph/buying-window-overlay",
    "/api/v1/market-graph/video-evidence/ingest",
    "/api/v1/market-graph/vendor-video-evidence/ingest",
    "/api/v1/market-graph/video-evidence/seed-targets",
    "/api/v1/market-graph/daily-digest-send",
]


def _get(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "rfr-hermes-health"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(url: str, body: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, Any]:
    data = json.dumps(body).encode()
    hdrs = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "rfr-hermes-health",
        **(headers or {}),
    }
    req = urllib.request.Request(url, data=data, method="POST", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            try:
                parsed: Any = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"raw": raw[:240]}
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw": raw[:240]}
        return exc.code, parsed


def overlay_counts(leads: list[dict[str, Any]]) -> dict[str, int]:
    filled = 0
    qualify = 0
    jobs = 0
    dms = 0
    windows = 0
    videos = 0
    for row in leads:
        hq = row.get("hermes_qualify") or row.get("hermes_qualify") or row.get("hermesQualify")
        hj = (
            row.get("hermes_job_titles")
            or row.get("hermes_job_titles")
            or row.get("hermesJobTitles")
            or []
        )
        hd = (
            row.get("hermes_decision_makers")
            or row.get("hermes_decision_makers")
            or row.get("hermesDecisionMakers")
            or []
        )
        hb = (
            row.get("hermes_buying_window")
            or row.get("hermes_buying_window")
            or row.get("hermesBuyingWindow")
        )
        hv = (
            row.get("hermes_video_evidence")
            or row.get("hermes_video_evidence")
            or row.get("hermesVideoEvidence")
        )
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


def ingest_contract() -> dict[str, Any]:
    unauth_code, unauth_body = _post(INFER, {"dry_run": True, "limit": 1})
    fp_code, fp_body = _post(
        INFER,
        {"dry_run": True, "limit": 1},
        {"X-Admin-Key": "0123456789abcdef"},
    )
    jwt_code, jwt_body = _post(
        INFER,
        {"dry_run": True, "limit": 1},
        {"X-Admin-Key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.sig"},
    )
    recon_code, recon_body = _post(
        RECONSTRUCT,
        {
            "text": (
                "Operate AMRs and unload totes from robots onto a conveyor "
                "for pack-out in a high-volume fulfillment center."
            ),
            "job_title": "AMR Operator",
        },
    )
    return {
        "unauth_infer_qualify": {
            "status": unauth_code,
            "ok": unauth_code == 403,
            "detail": (unauth_body.get("detail") if isinstance(unauth_body, dict) else None),
        },
        "fingerprint_infer_qualify": {
            "status": fp_code,
            "ok": fp_code == 401,
            "detail": (fp_body.get("detail") if isinstance(fp_body, dict) else None),
        },
        "jwt_infer_qualify": {
            "status": jwt_code,
            "ok": jwt_code == 401,
            "detail": (jwt_body.get("detail") if isinstance(jwt_body, dict) else None),
        },
        "reconstruct": {
            "status": recon_code,
            "ok": recon_code == 200,
            "work_id": (
                (recon_body.get("work") or {}).get("work_unit_id")
                if isinstance(recon_body, dict)
                else None
            ),
        },
    }


def documented_routes(openapi: dict[str, Any]) -> dict[str, Any]:
    paths = openapi.get("paths") or {}
    present = [p for p in HERMES_INGEST_PATHS if p in paths]
    missing = [p for p in HERMES_INGEST_PATHS if p not in paths]
    return {
        "present": present,
        "missing_on_fly": missing,
        "ok": len(missing) == 0,
    }


def main() -> int:
    pipe = _get(PIPELINE)
    leads = list(pipe.get("leads") or [])
    counts = overlay_counts(leads)
    status = _get(STATUS)
    snap = (status.get("snapshot") or {}) if isinstance(status, dict) else {}
    sched = (status.get("scheduler") or {}) if isinstance(status, dict) else {}
    try:
        spec = _get(OPENAPI)
        routes = documented_routes(spec)
    except Exception as exc:
        routes = {
            "ok": False,
            "error": str(exc)[:240],
            "present": [],
            "missing_on_fly": HERMES_INGEST_PATHS,
        }
    contract = ingest_contract()

    report = {
        "pipeline_built_at": pipe.get("built_at"),
        "overlays": counts,
        "market_graph_generated_at": snap.get("generated_at"),
        "market_graph_status": snap.get("status"),
        "scheduler_running": sched.get("running"),
        "scheduler_last_run": sched.get("last_run"),
        "ingest_contract": contract,
        "documented_routes": routes,
    }
    print(json.dumps(report, indent=2, default=str))

    exit_code = 0
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
        exit_code = 1
    if not contract["unauth_infer_qualify"]["ok"] or not contract["fingerprint_infer_qualify"]["ok"]:
        print("\nIngest auth contract failed on Fly.", file=sys.stderr)
        exit_code = 1
    if routes.get("missing_on_fly"):
        print(
            "\nDocumented Hermes tracks missing on Fly OpenAPI: "
            + ", ".join(routes["missing_on_fly"]),
            file=sys.stderr,
        )
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
