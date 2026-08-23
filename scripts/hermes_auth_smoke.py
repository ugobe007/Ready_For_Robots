#!/usr/bin/env python3
"""Prove Hermes RFR_ADMIN_KEY matches Fly ADMIN_KEY. Never prints the secret.

Loads (first hit wins): env RFR_ADMIN_KEY / ADMIN_KEY, then ~/.hermes/.env, then repo .env.

  python3 scripts/hermes_auth_smoke.py

Mac:
  cd ~/Desktop/Ready_For_Robots && python3 scripts/hermes_auth_smoke.py

Cursor Cloud has no ~/.hermes/.env — this will exit 2 there.
"""
from __future__ import annotations

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
    )
    out = {k: body[k] for k in keep if k in body}
    cal = body.get("cal")
    if isinstance(cal, dict):
        out["cal_keys"] = sorted(cal.keys())[:12]
    return out


def main() -> int:
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
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
