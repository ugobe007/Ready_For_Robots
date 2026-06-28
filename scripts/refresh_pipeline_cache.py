#!/usr/bin/env python3
"""Rebuild public pipeline/homepage caches (local CLI or prod DB via DATABASE_URL)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from urllib.parse import quote

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_loaded = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded):
    os.environ["DATABASE_URL"] = _shell_database_url


_HTTP_STATUS_MARKER = "__HTTP_STATUS__:"


def _auth_header_args(admin_key: str) -> list[str]:
    """Pick the correct auth header for the admin API.

    A JWT (Supabase access token, starts with ``eyJ``) must go in
    ``Authorization: Bearer``; the server rejects JWTs sent via ``X-Admin-Key``.
    The raw ADMIN_KEY secret goes in ``X-Admin-Key``.
    """
    key = (admin_key or "").strip()
    if key.startswith("eyJ"):
        return ["-H", f"Authorization: Bearer {key}"]
    return ["-H", f"X-Admin-Key: {key}"]


def resolve_remote_refresh_request(api_base: str) -> tuple[str, list[str]]:
    """Build refresh URL and curl header args for prod admin API."""
    base = api_base.rstrip("/")
    url = f"{base}/api/admin/leads/refresh-pipeline-cache"

    cron = (os.getenv("SCRAPER_CRON_TOKEN") or "").strip()
    if cron:
        return f"{url}?token={quote(cron, safe='')}", []

    bearer = (os.getenv("HARNESS_ADMIN_BEARER") or "").strip()
    if bearer.startswith("eyJ"):
        return url, ["-H", f"Authorization: Bearer {bearer}"]

    admin_key = (os.getenv("ADMIN_KEY") or "").strip()
    if not admin_key:
        raise ValueError(
            "Set ADMIN_KEY (raw secret), SCRAPER_CRON_TOKEN, or HARNESS_ADMIN_BEARER "
            "for remote pipeline cache refresh"
        )
    return url, _auth_header_args(admin_key)


def _should_wait_after_post(http_status: int) -> bool:
    """Only poll for a rebuilt cache when the trigger POST actually succeeded."""
    return 200 <= http_status < 300


def _post_remote_refresh(url: str, header_args: list[str]) -> tuple[int, str]:
    """POST the refresh trigger; return (http_status, response_body).

    Uses ``curl -w`` to capture the HTTP status even on 4xx/5xx (plain
    ``curl -sS`` exits 0 on an HTTP error, so the caller would otherwise
    treat a 401 as success and poll uselessly until timeout).
    """
    import subprocess

    proc = subprocess.run(
        [
            "curl",
            "-sS",
            "-X",
            "POST",
            url,
            *header_args,
            "-w",
            f"\n{_HTTP_STATUS_MARKER}%{{http_code}}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout
    status = 0
    body = out
    marker = out.rfind(_HTTP_STATUS_MARKER)
    if marker != -1:
        body = out[:marker].rstrip("\n")
        try:
            status = int(out[marker + len(_HTTP_STATUS_MARKER):].strip())
        except ValueError:
            status = 0
    return status, body


def _pipeline_cache_status(api_base: str) -> dict:
    import httpx

    url = f"{api_base.rstrip('/')}/api/leads/pipeline"
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        resp = client.get(url, headers={"Accept": "application/json"})
        resp.raise_for_status()
        payload = resp.json()
    return {
        "built_at": payload.get("built_at"),
        "cache_pending": payload.get("cache_pending"),
        "leads_count": len(payload.get("leads") or []),
    }


def _wait_for_remote_cache(*, api_base: str, timeout_sec: int, poll_sec: int) -> int:
    import time

    deadline = time.time() + timeout_sec
    last: dict | None = None
    print(
        f"Waiting for pipeline cache (poll every {poll_sec}s, timeout {timeout_sec}s)…",
        flush=True,
    )
    while time.time() < deadline:
        try:
            last = _pipeline_cache_status(api_base)
        except Exception as exc:
            print(f"Poll failed: {exc}", flush=True)
            time.sleep(poll_sec)
            continue

        pending = last.get("cache_pending")
        built_at = last.get("built_at")
        leads = last.get("leads_count") or 0
        print(
            f"  cache_pending={pending!r} built_at={built_at!r} leads={leads}",
            flush=True,
        )
        if pending is not True and built_at and leads > 0:
            print("Pipeline cache ready.", flush=True)
            return 0
        time.sleep(poll_sec)

    print(
        f"Timed out waiting for pipeline cache. Last status: {last}",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild pipeline/public surface caches")
    parser.add_argument(
        "--remote",
        action="store_true",
        help="POST to Fly admin API (needs ADMIN_KEY in .env)",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="After --remote, poll /api/leads/pipeline until built_at is set (15–20 min typical)",
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=1200,
        help="Max seconds to wait when using --wait (default 1200)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between pipeline status polls (default 30)",
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("API_BASE", "https://ready-2-robot.fly.dev"),
        help="API base when using --remote",
    )
    args = parser.parse_args()

    if args.remote:
        try:
            url, header_args = resolve_remote_refresh_request(args.api_base)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        import subprocess

        try:
            status, body = _post_remote_refresh(url, header_args)
        except subprocess.CalledProcessError as exc:
            print(f"Remote refresh failed: {exc.stderr or exc.stdout}", file=sys.stderr)
            return 1

        if not _should_wait_after_post(status):
            # curl exits 0 on HTTP errors, so without this guard --wait would
            # poll uselessly for the full timeout and report a misleading
            # "timed out" instead of the real auth/server failure.
            print(
                f"Remote refresh trigger returned HTTP {status}: {body}",
                file=sys.stderr,
            )
            if status in (401, 403):
                print(
                    "Auth rejected. Use one of:\n"
                    "  • ADMIN_KEY — raw server secret (fly secrets set ADMIN_KEY='…')\n"
                    "  • SCRAPER_CRON_TOKEN — query ?token= (same as scraper cron URLs)\n"
                    "  • HARNESS_ADMIN_BEARER — admin user Supabase access_token (Bearer)\n"
                    "Run: python3 scripts/harness_preflight.py --require-cache-auth",
                    file=sys.stderr,
                )
            return 1

        print(body or f"Refresh triggered (HTTP {status}).")

        if args.wait:
            return _wait_for_remote_cache(
                api_base=args.api_base.rstrip("/"),
                timeout_sec=args.wait_timeout,
                poll_sec=args.poll_interval,
            )
        print(
            "Refresh started in background. Re-run with --wait or check built_at in ~15–20 min.",
            flush=True,
        )
        return 0

    from app.database import SessionLocal
    from app.services.public_surface_cache import refresh_pipeline_surface_caches

    db = SessionLocal()
    try:
        print("Rebuilding pipeline surfaces (may take several minutes)…", flush=True)
        stats = refresh_pipeline_surface_caches(db)
        db.commit()
        print(json.dumps(stats, indent=2, default=str))
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Refresh failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
