#!/usr/bin/env python3
"""Run the Hermes qualify tick against Fly using Hermes/GitHub ADMIN_KEY.

Never prints the secret. Loads (first hit wins): env RFR_ADMIN_KEY / ADMIN_KEY /
RFR_ADMIN_KEY, then ~/.hermes/.env, then repo .env.

If the key is wrong, Fly returns 401/403 and this script exits 1 (the workflow
breaks). GitHub Actions injects secrets.ADMIN_KEY as RFR_ADMIN_KEY — same string
as Hermes ~/.hermes/.env RFR_ADMIN_KEY.

  python3 scripts/hermes_auth_smoke.py           # cal-status + infer-qualify dry_run
  python3 scripts/hermes_auth_smoke.py --apply   # persist overlays on public pipeline IDs

Mac:
  cd ~/Desktop/Ready_For_Robots && python3 scripts/hermes_auth_smoke.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

FLY = os.environ.get("RFR_API_BASE", "https://ready-2-robot.fly.dev").rstrip("/")
CAL = f"{FLY}/api/v1/market-graph/cal-status"
INFER = f"{FLY}/api/v1/market-graph/infer-qualify"
PIPELINE = f"{FLY}/api/leads/pipeline"
CACHE = f"{FLY}/api/admin/leads/refresh-pipeline-cache"
KEY_NAMES = ("RFR_ADMIN_KEY", "ADMIN_KEY", "RFR_ADMIN_KEY")


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
    for name in KEY_NAMES:
        val = (os.environ.get(name) or "").strip()
        if val:
            return val, f"env:{name}"
    home = Path.home() / ".hermes" / ".env"
    repo = Path(__file__).resolve().parents[1] / ".env"
    for path, names in (
        (home, KEY_NAMES),
        (repo, ("ADMIN_KEY", "RFR_ADMIN_KEY", "RFR_ADMIN_KEY")),
    ):
        data = _load_dotenv(path)
        for name in names:
            val = (data.get(name) or "").strip()
            if val:
                return val, f"{path}:{name}"
    return "", ""


def _request(url: str, key: str | None, payload: dict | None) -> tuple[int, dict | str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "rfr-hermes-auth-smoke",
    }
    if key:
        headers["X-Admin-Key"] = key
    data = None
    method = "GET"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read().decode()
            try:
                parsed: dict | str = json.loads(body)
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
        "hermes_run_id",
        "dry_run",
        "dry_run",
        "status",
        "message",
    )
    out = {k: body[k] for k in keep if k in body}
    results = body.get("results")
    if isinstance(results, list):
        out["result_count"] = len(results)
        ids: list[int] = []
        names: list[str] = []
        for row in results:
            if not isinstance(row, dict):
                continue
            cid = row.get("company_id")
            if cid is not None:
                ids.append(int(cid))
            name = row.get("company_name")
            if name:
                names.append(str(name)[:80])
        if ids:
            out["company_ids"] = ids
        if names:
            out["company_names"] = names[:12]
    return out


def _pipeline_snapshot() -> dict:
    code, body = _request(PIPELINE, None, None)
    if code != 200 or not isinstance(body, dict):
        return {"http": code, "leads": 0, "company_ids": [], "any_overlay": 0, "hermes_qualify": 0}
    leads = list(body.get("leads") or [])
    ids: list[int] = []
    filled = 0
    qualify = 0
    names: list[str] = []
    for row in leads:
        cid = row.get("id") or row.get("company_id")
        if cid is not None:
            ids.append(int(cid))
        nm = row.get("company_name") or row.get("name")
        if nm:
            names.append(str(nm)[:80])
        hq = row.get("hermes_qualify") or row.get("hermes_qualify")
        if hq:
            qualify += 1
            filled += 1
        elif row.get("hermes_job_titles") or row.get("hermes_decision_makers"):
            filled += 1
    return {
        "http": 200,
        "leads": len(leads),
        "company_ids": ids,
        "company_names": names,
        "any_overlay": filled,
        "hermes_qualify": qualify,
        "built_at": body.get("built_at"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes ↔ Fly ADMIN_KEY smoke")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="After a 200 dry_run, persist infer-qualify on the public pipeline company IDs.",
    )
    args = parser.parse_args()

    key, source = load_admin_key()
    if not key:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "no_key",
                    "hint": "Inject RFR_ADMIN_KEY (Hermes ~/.hermes/.env) or run on the Mac.",
                },
                indent=2,
            )
        )
        return 2
    kind = (
        "jwt"
        if key.startswith("eyJ")
        else "fingerprint"
        if len(key) == 16 and all(c in "0123456789abcdef" for c in key.lower())
        else "random"
    )
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

    pipe = _pipeline_snapshot()
    report["pipeline_before"] = pipe
    company_ids = list(pipe.get("company_ids") or [])
    infer_body_dry: dict = {
        # Fly production schema (OpenAPI): dry_run / hermes_run_id / company_ids
        "dry_run": True,
        "hermes_run_id": "hermes-pipeline-dry",
    }
    if company_ids:
        infer_body_dry["company_ids"] = company_ids
        infer_body_dry["limit"] = max(len(company_ids), 1)
    else:
        infer_body_dry["limit"] = 1

    cal_code, cal_body = _request(CAL, key, None)
    infer_code, infer_body = _request(INFER, key, infer_body_dry)
    report["cal_status"] = {"http": cal_code, **_safe_summary(cal_body)}
    report["infer_qualify_dry_run"] = {"http": infer_code, **_safe_summary(infer_body)}
    report["ok"] = cal_code == 200 and infer_code == 200
    if not report["ok"]:
        report["reason"] = "auth_or_contract_failed"
        print(json.dumps(report, indent=2, default=str))
        return 1

    if args.apply:
        live_payload: dict = {
            "dry_run": False,
            "hermes_run_id": "hermes-pipeline-apply",
        }
        if company_ids:
            live_payload["company_ids"] = company_ids
            live_payload["limit"] = max(len(company_ids), 1)
        else:
            live_payload["limit"] = 12
        live_code, live_body = _request(INFER, key, live_payload)
        report["infer_qualify_apply"] = {"http": live_code, **_safe_summary(live_body)}
        report["ok"] = live_code == 200 and (
            not isinstance(live_body, dict) or int(live_body.get("accepted") or 0) > 0
        )
        cache_code, cache_body = _request(CACHE, key, {})
        report["pipeline_cache_refresh"] = {"http": cache_code, **_safe_summary(cache_body)}
        after = _pipeline_snapshot()
        # Cache rebuild is async (~15 min). Poll briefly; apply success is the gate.
        for _ in range(6):
            if after.get("hermes_qualify"):
                break
            time.sleep(15)
            after = _pipeline_snapshot()
        report["pipeline_after"] = after
        if not report["ok"]:
            report["reason"] = "infer_qualify_apply_failed"
            print(json.dumps(report, indent=2, default=str))
            return 1
        if after.get("hermes_qualify"):
            report["overlays_visible"] = True
        else:
            report["overlays_visible"] = False
            report["note"] = (
                "infer-qualify wrote overlays on the public pipeline company IDs; "
                "public /api/leads/pipeline may lag until cache rebuild finishes."
            )
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
