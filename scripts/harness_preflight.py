#!/usr/bin/env python3
"""Validate harness / CI secrets before snapshot, cache refresh, or agent runs."""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from scripts.harness_env import load_harness_env

load_harness_env(_root)


def classify_admin_refresh_auth() -> dict:
    """Return whether remote pipeline cache refresh can authenticate."""
    admin_key = (os.getenv("ADMIN_KEY") or "").strip()
    cron = (os.getenv("SCRAPER_CRON_TOKEN") or "").strip()
    bearer = (os.getenv("HARNESS_ADMIN_BEARER") or "").strip()

    if cron:
        return {
            "ok": True,
            "method": "SCRAPER_CRON_TOKEN",
            "hint": "Remote refresh uses ?token= on /api/admin/leads/refresh-pipeline-cache",
        }
    if bearer.startswith("eyJ"):
        return {
            "ok": True,
            "method": "HARNESS_ADMIN_BEARER",
            "hint": "Remote refresh uses Authorization: Bearer (admin user JWT)",
        }
    if not admin_key:
        return {
            "ok": False,
            "method": None,
            "hint": (
                "Set GitHub secret ADMIN_KEY to the raw Fly secret "
                "(fly secrets set ADMIN_KEY='…' -a ready-2-robot), "
                "or set SCRAPER_CRON_TOKEN, or HARNESS_ADMIN_BEARER (admin session JWT)."
            ),
        }
    if admin_key.startswith("eyJ"):
        return {
            "ok": False,
            "method": None,
            "hint": (
                "ADMIN_KEY looks like a Supabase JWT — the server rejects JWTs on X-Admin-Key. "
                "Use the raw ADMIN_KEY secret, SCRAPER_CRON_TOKEN, or HARNESS_ADMIN_BEARER."
            ),
        }
    if re.fullmatch(r"[a-f0-9]{16}", admin_key):
        return {
            "ok": False,
            "method": None,
            "hint": (
                "ADMIN_KEY is the 16-char digest from `fly secrets list`, not the secret value. "
                "Run: fly secrets set ADMIN_KEY='your-secret' -a ready-2-robot"
            ),
        }
    return {
        "ok": True,
        "method": "ADMIN_KEY",
        "hint": "Remote refresh uses X-Admin-Key header",
    }


def classify_agent_auth(*, skip_agent: bool) -> dict:
    if skip_agent:
        return {"ok": True, "method": "skip_agent"}
    key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    if not key:
        return {
            "ok": False,
            "hint": "ANTHROPIC_API_KEY missing — use --skip-agent or add GitHub secret",
        }
    return {"ok": True, "method": "ANTHROPIC_API_KEY"}


def classify_notify_email() -> dict:
    to = (os.getenv("HARNESS_NOTIFY_EMAIL") or "").strip()
    if not to:
        admins = (os.getenv("ADMIN_EMAILS") or "").strip()
        if admins:
            to = admins.split(",")[0].strip()
    if not to:
        to = "ugobe07@gmail.com"
    resend = bool((os.getenv("RESEND_API_KEY") or "").strip())
    if not resend:
        return {
            "ok": False,
            "to": to,
            "hint": (
                "RESEND_API_KEY missing in GitHub Actions — copy from Fly: "
                "fly ssh console -a ready-2-robot -C 'printenv RESEND_API_KEY' "
                "then gh secret set RESEND_API_KEY"
            ),
        }
    return {"ok": True, "to": to, "method": "RESEND_API_KEY"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness / deploy secret preflight")
    parser.add_argument(
        "--require-cache-auth",
        action="store_true",
        help="Exit 1 when remote cache refresh cannot authenticate",
    )
    parser.add_argument(
        "--require-agent",
        action="store_true",
        help="Exit 1 when ANTHROPIC_API_KEY is missing",
    )
    parser.add_argument("--skip-agent", action="store_true")
    parser.add_argument(
        "--require-notify",
        action="store_true",
        help="Exit 1 when daily email cannot be sent (RESEND_API_KEY missing)",
    )
    args = parser.parse_args()

    cache = classify_admin_refresh_auth()
    agent = classify_agent_auth(skip_agent=args.skip_agent)
    notify = classify_notify_email()

    print("Harness preflight")
    print(f"  cache refresh: {'OK' if cache['ok'] else 'BLOCKED'} ({cache.get('method') or 'none'})")
    if cache.get("hint"):
        print(f"    → {cache['hint']}")
    print(f"  agent runner: {'OK' if agent['ok'] else 'BLOCKED'} ({agent.get('method', 'none')})")
    if agent.get("hint"):
        print(f"    → {agent['hint']}")
    print(f"  daily email: {'OK' if notify['ok'] else 'BLOCKED'} → {notify.get('to')}")
    if notify.get("hint"):
        print(f"    → {notify['hint']}")

    rc = 0
    if args.require_cache_auth and not cache["ok"]:
        rc = 1
    if args.require_agent and not agent["ok"]:
        rc = 1
    if args.require_notify and not notify["ok"]:
        rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
