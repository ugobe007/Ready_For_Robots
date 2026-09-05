#!/usr/bin/env python3
"""Confirm readyforrobots.com is serving a fresh Jobs bundle after Vercel alias.

GitHub Actions #105 captured the *.vercel.app deployment URL correctly, then
`curl -f` of that host returned 404 (edge race / Deployment Protection). With
`set -e`, that aborted the job *before* polling the custom domain — which was
already aliased and serving the new hash.

Gate on https://readyforrobots.com only. A vercel.app 404 is logged, never fatal.

  python3 scripts/vercel_production_smoke.py
  python3 scripts/vercel_production_smoke.py --deploy-url https://….vercel.app
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

STALE_JS = "/assets/index-bxLpnQiT.js"
JS_PATH_RE = re.compile(r"/assets/index-[A-Za-z0-9_-]+\.js")
DEPLOY_URL_RE = re.compile(r"https://[A-Za-z0-9._-]+\.vercel\.app")
CANARY = "Jobs for"
# Signup Google/GitHub OAuth is dead if Vite omitted this host.
SUPABASE_HOST_CANARY = "lmoyydlhlgdyqbxkmkuz.supabase.co"
REQUIRED_JS_SUBSTRINGS = (CANARY, SUPABASE_HOST_CANARY)
MIN_JS_BYTES = 100_000
DEFAULT_DOMAIN = "https://readyforrobots.com"
DEFAULT_ATTEMPTS = 12
DEFAULT_SLEEP_S = 5.0

Getter = Callable[[str], tuple[int, bytes]]


def extract_deploy_url(log: str) -> str | None:
    matches = DEPLOY_URL_RE.findall(log or "")
    return matches[-1] if matches else None


def http_get(url: str, timeout: float = 30.0) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "text/html,application/javascript,*/*",
            "User-Agent": "rfr-vercel-production-smoke",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status), resp.read()
    except urllib.error.HTTPError as err:
        try:
            body = err.read()
        except Exception:
            body = b""
        return int(err.code), body
    except urllib.error.URLError:
        return 0, b""


def js_path_from_html(html: str) -> str | None:
    match = JS_PATH_RE.search(html or "")
    return match.group(0) if match else None


@dataclass
class BundleCheck:
    ok: bool
    origin: str
    status: int
    js_path: str | None
    js_bytes: int
    reason: str


def check_origin(origin: str, *, get: Getter | None = None, nonce: str = "n") -> BundleCheck:
    getter = get or http_get
    base = origin.rstrip("/")
    status, raw = getter(f"{base}/?n={nonce}")
    html = raw.decode("utf-8", errors="replace")
    js_path = js_path_from_html(html)
    if status != 200:
        return BundleCheck(False, base, status, js_path, 0, f"HTML HTTP {status}")
    if not js_path:
        return BundleCheck(False, base, status, None, 0, "no /assets/index-*.js in HTML")
    if js_path == STALE_JS:
        return BundleCheck(False, base, status, js_path, 0, "stale hash index-bxLpnQiT.js")
    js_status, js_body = getter(f"{base}{js_path}")
    if js_status != 200:
        return BundleCheck(False, base, js_status, js_path, 0, f"JS HTTP {js_status}")
    js_bytes = len(js_body)
    if js_bytes <= MIN_JS_BYTES:
        return BundleCheck(
            False, base, js_status, js_path, js_bytes, f"JS too small ({js_bytes} bytes)"
        )
    try:
        text = js_body.decode("utf-8", errors="replace")
    except Exception:
        text = ""
    missing = [needle for needle in REQUIRED_JS_SUBSTRINGS if needle not in text]
    if missing:
        return BundleCheck(
            False, base, js_status, js_path, js_bytes, f"missing canary {missing[0]!r}"
        )
    return BundleCheck(True, base, js_status, js_path, js_bytes, "ok")


def format_check(result: BundleCheck) -> str:
    path = result.js_path or "(none)"
    return (
        f"{result.origin} -> {path} status={result.status} "
        f"bytes={result.js_bytes} {result.reason}"
    )


def smoke_custom_domain(
    domain: str,
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    sleep_s: float = DEFAULT_SLEEP_S,
    get: Getter | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    nonce_factory: Callable[[], str] | None = None,
) -> BundleCheck:
    last = BundleCheck(False, domain.rstrip("/"), 0, None, 0, "no attempts")
    for i in range(max(1, attempts)):
        nonce = nonce_factory() if nonce_factory else str(int(time.time()) + i)
        last = check_origin(domain, get=get, nonce=nonce)
        print(format_check(last), flush=True)
        if last.ok:
            return last
        if i + 1 < attempts:
            sleeper(sleep_s)
    return last


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default=DEFAULT_DOMAIN)
    parser.add_argument(
        "--deploy-url",
        default="",
        help="Optional *.vercel.app URL from `vercel deploy`. Logged only; 404 is not a failure.",
    )
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS)
    parser.add_argument("--sleep", type=float, default=DEFAULT_SLEEP_S)
    args = parser.parse_args(argv)

    deploy = (args.deploy_url or "").strip()
    if deploy:
        preview = check_origin(deploy, nonce="deploy")
        print(f"deploy-url (advisory): {format_check(preview)}", flush=True)
        if not preview.ok:
            print(
                "deploy-url failed (404/protection/race is expected); "
                "gating on the custom domain.",
                flush=True,
            )

    result = smoke_custom_domain(
        args.domain,
        attempts=args.attempts,
        sleep_s=args.sleep,
    )
    if result.ok:
        print("Custom domain matches new bundle.", flush=True)
        return 0
    print(
        f"::error::{args.domain} still serving a stale or unreachable bundle after alias",
        flush=True,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
