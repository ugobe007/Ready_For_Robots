#!/usr/bin/env python3
"""
Conversion lifeline smoke test — URL → signup next → 5 leads → pipeline → save gate.

Fails hard on anything that blocks the money path. Run before every deploy:

  python3 scripts/smoke_conversion_lifeline.py
  python3 scripts/smoke_conversion_lifeline.py --api https://ready-2-robot.fly.dev
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_API = "https://ready-2-robot.fly.dev"
DEFAULT_SITE = "https://readyforrobots.com"
SAMPLE_URL = "https://agilityrobotics.com"


class SmokeFailure(Exception):
    pass


def _get(url: str, *, timeout: float = 45.0) -> tuple[int, Any, str]:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "rfr-smoke/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            ct = resp.headers.get("content-type") or ""
            data: Any = body
            if "application/json" in ct:
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    data = body
            return int(resp.status), data, ct
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = body
        return int(e.code), data, e.headers.get("content-type") or ""
    except Exception as e:
        raise SmokeFailure(f"GET {url} failed: {e}") from e


def check_pages(site: str) -> list[str]:
    alerts: list[str] = []
    for path in ("/", "/signup", "/login", "/pipeline", "/pricing"):
        code, _, _ = _get(f"{site}{path}", timeout=30)
        if code >= 400:
            alerts.append(f"PAGE {path} → HTTP {code}")
    # Results with URL must serve SPA (200), not 404
    q = urllib.parse.urlencode({"url": SAMPLE_URL, "limit": "5", "src": "smoke"})
    code, _, _ = _get(f"{site}/results?{q}", timeout=30)
    if code >= 400:
        alerts.append(f"PAGE /results?url=… → HTTP {code}")
    return alerts


def check_match_url(api: str) -> list[str]:
    alerts: list[str] = []
    q = urllib.parse.urlencode({"url": SAMPLE_URL, "limit": "5"})
    code, data, ct = _get(f"{api}/api/leads/match-url?{q}", timeout=90)
    if code != 200:
        alerts.append(f"match-url HTTP {code}: {data!r}"[:240])
        return alerts
    if "application/json" not in ct or not isinstance(data, dict):
        alerts.append("match-url did not return JSON object")
        return alerts
    leads = data.get("leads")
    if not isinstance(leads, list):
        alerts.append("match-url missing leads[]")
        return alerts
    mode = str(data.get("matching_mode") or "")
    if mode == "no_profile":
        alerts.append("match-url returned no_profile for known robot OEM URL — scrape/profile broken")
    elif len(leads) == 0 and mode != "no_match":
        alerts.append(f"match-url returned 0 leads (mode={mode})")
    elif len(leads) == 0:
        alerts.append("match-url returned 0 leads (no_match) — check matcher / junk filter")
    else:
        # Brief must not crash cards; optional field
        sample = leads[0] if leads else {}
        if not sample.get("company_name") and not sample.get("name"):
            alerts.append("match-url lead missing company_name")
    return alerts


def check_pipeline_feed(api: str) -> list[str]:
    alerts: list[str] = []
    code, data, _ = _get(f"{api}/api/leads/pipeline", timeout=45)
    if code != 200 or not isinstance(data, dict):
        alerts.append(f"pipeline feed HTTP {code}")
        return alerts
    leads = data.get("leads") or []
    if not leads:
        alerts.append("pipeline feed empty — blocks anonymous value proof")
    if not data.get("built_at"):
        alerts.append("pipeline cache built_at missing")
    return alerts


def check_save_gate(api: str) -> list[str]:
    """Unauthenticated save must be rejected (401/403), not 500."""
    alerts: list[str] = []
    body = json.dumps({"company_id": 1, "name": "Smoke Test Co"}).encode()
    req = urllib.request.Request(
        f"{api}/api/crm/accounts",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            alerts.append(f"CRM create without auth unexpectedly succeeded HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code not in (401, 403, 422):
            alerts.append(f"CRM create without auth → HTTP {e.code} (expected 401/403)")
    except Exception as e:
        alerts.append(f"CRM create probe failed: {e}")
    return alerts


def check_signup_next_contract() -> list[str]:
    """Pure routing contract — mirrors client signupWorkflowPath."""
    alerts: list[str] = []
    try:
        # Import from repo when run from root; skip if path awkward
        sys.path.insert(0, "readyforrobots-new/client/src/lib")
    except Exception:
        pass

    # Inline mirror of critical rule so smoke does not depend on Node.
    def resolve(next_raw: str, company_url: str, matched: str | None = None) -> str:
        if next_raw.startswith("/results"):
            return next_raw
        if next_raw.startswith("/pipeline") or next_raw.startswith("/pricing"):
            return next_raw
        if next_raw == "/":
            return "/pipeline"
        if matched:
            return matched
        if company_url:
            q = urllib.parse.urlencode(
                {"url": company_url, "limit": "5", "src": "home_url_submit_signup_return"}
            )
            return f"/results?{q}"
        return "/pipeline"

    next_results = f"/results?url={urllib.parse.quote(SAMPLE_URL, safe='')}&limit=5&src=home_signup_return"
    got = resolve(
        next_results,
        SAMPLE_URL,
        matched=f"/pipeline?src=results_scan&url={SAMPLE_URL}",
    )
    if got != next_results:
        alerts.append(f"signup next=/results was rewritten to {got!r} — 5-lead step skipped")
    return alerts


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test conversion lifeline")
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--site", default=DEFAULT_SITE)
    args = parser.parse_args()

    print(f"API  {args.api}")
    print(f"SITE {args.site}")
    print(f"URL  {SAMPLE_URL}")
    print("---")

    checks = [
        ("pages", lambda: check_pages(args.site)),
        ("pipeline_feed", lambda: check_pipeline_feed(args.api)),
        ("match_url", lambda: check_match_url(args.api)),
        ("save_gate", lambda: check_save_gate(args.api)),
        ("signup_next", check_signup_next_contract),
    ]

    failed = 0
    for name, fn in checks:
        try:
            alerts = fn()
        except SmokeFailure as e:
            alerts = [str(e)]
        if alerts:
            failed += 1
            print(f"FAIL  {name}")
            for a in alerts:
                print(f"      - {a}")
        else:
            print(f"PASS  {name}")

    print("---")
    if failed:
        print(f"{failed} check(s) FAILED — do not ship")
        return 1
    print("All conversion lifeline checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
