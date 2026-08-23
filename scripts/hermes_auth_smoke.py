#!/usr/bin/env python3
"""Prove Hermes RFR_ADMIN_KEY matches Fly ADMIN_KEY, then run infer-qualify.

Never prints the secret. Loads (first hit wins): env RFR_ADMIN_KEY / ADMIN_KEY,
then ~/.hermes/.env, then repo .env.

  python3 scripts/hermes_auth_smoke.py           # cal-status + infer-qualify dry_run
  python3 scripts/hermes_auth_smoke.py --apply   # then persist infer-qualify (limit 12)

Mac:
  cd ~/Desktop/Ready_For_Robots && python3 scripts/hermes_auth_smoke.py --apply

Cursor Cloud has no ~/.hermes/.env unless RFR_ADMIN_KEY is injected (GitHub Actions).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

FLY = os.environ.get("RFR_API_BASE", "https://ready-2-robot.fly.dev").rstrip("/")
CAL = f"{FLY}/api/v1/market-graph/cal-status"
INFER = f"{FLY}/api/v1/market-graph/infer-qualify"


def _load_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key:
            out[key] = val
    return out


def load_admin_key() -> tuple[str, str]:
    for name in ("RFR_ADMIN_KEY", "ADMIN_KEY"):
        val = (os.environ.get(name) or "").strip()
        if val:
            return val, f"env:{name}"
    home = Path.home() / ".hermes" / ".env"
    repo = Path(__file__).resolve().parents[1] / ".env"
    for path, names in (
        (home, ("RFR_ADMIN_KEY", "ADMIN_KEY")),
        (repo, ("ADMIN_KEY", "RFR_ADMIN_KEY")),
    ):
        data = _load_dotenv(path)
        for name in names:
            val = (data.get(name) or "").strip()
            if val:
                return val, f"{path}:{name}"
    return "", ""


def _post_or_get(url: str, key: str, payload: dict | None) -> tuple[int, dict | str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "rfr-hermes-auth-smoke",
        "X-Admin-Key": key,
    }
    data = None
    method = "GET"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode()
            parsed: dict | str
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body[:400]
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body[:400]
        return exc.code, parsed


def _safe_summary(body: dict | str) -> dict:
    if not isinstance(body, dict):
        return {"raw": str(body)[:240]}
    keep = (
        "auth",
        "ok",
        "detail",
        "accepted",
        "failed",
        "skipped",
        "paid_llm",
        "engine",
        "error",
        "doc",
        "hermes_run_id",
        "dry_run",
    )
    out = {k: body[k] for k in keep if k in body}
    cal = body.get("cal")
    if isinstance(cal, dict):
        out["cal_keys"] = sorted(cal.keys())[:12]
    results = body.get("results")
    if isinstance(results, list):
        out["result_count"] = len(results)
    return out


def _overlay_counts() -> dict:
    url = f"{FLY}/api/leads/pipeline"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "rfr-hermes-auth-smoke"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        pipe = json.loads(resp.read().decode())
    leads = list(pipe.get("leads") or [])
    filled = 0
    qualify = 0
    for row in leads:
        hq = row.get("hermes_qualify") or row.get("hermes_qualify")
        if hq:
            qualify += 1
            filled += 1
        elif row.get("hermes_job_titles") or row.get("hermes_decision_makers"):
            filled += 1
    return {
        "leads": len(leads),
        "any_overlay": filled,
        "hermes_qualify": qualify,
        "built_at": pipe.get("built_at"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes ↔ Fly ADMIN_KEY smoke")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="After a 200 dry_run, POST infer-qualify with dry_run=false (writes overlays).",
    )
    args = parser.parse_args()

    key, source = load_admin_key()
    if not key:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "no_key",
                    "hint": "Run on the Mac: cd ~/Desktop/Ready_For_Robots && python3 scripts/hermes_auth_smoke.py",
                },
                indent=2,
            )
        )
        return 2
    kind = "jwt" if key.startswith("eyJ") else "fingerprint" if len(key) == 16 and all(
        c in "0123456789abcdef" for c in key.lower()
    ) else "random"
    report: dict = {
        "key_source": source,
        "key_len": len(key),
        "key_kind": kind,
        "api": FLY,
    }
    if kind != "random":
        report["ok"] = False
        report["reason"] = "wrong_kind_of_secret"
        print(json.dumps(report, indent=2))
        return 1

    cal_code, cal_body = _post_or_get(CAL, key, None)
    infer_code, infer_body = _post_or_get(
        INFER, key, {"dry_run": True, "limit": 1, "hermes_run_id": "auth-smoke"}
    )
    report["cal_status"] = {"http": cal_code, **_safe_summary(cal_body)}
    report["infer_qualify_dry_run"] = {"http": infer_code, **_safe_summary(infer_body)}
    report["ok"] = cal_code == 200 and infer_code == 200
    if report["ok"] and args.apply:
        live_code, live_body = _post_or_get(
            INFER,
            key,
            {
                "dry_run": False,
                "limit": 12,
                "hermes_run_id": "hermes-workflow-apply",
            },
        )
        report["infer_qualify_apply"] = {"http": live_code, **_safe_summary(live_body)}
        report["ok"] = live_code == 200
        try:
            report["pipeline_overlays_after"] = _overlay_counts()
        except Exception as exc:
            report["pipeline_overlays_after"] = {"error": str(exc)[:240]}
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
