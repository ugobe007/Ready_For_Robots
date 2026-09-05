#!/usr/bin/env python3
"""Verify DATABASE_URL and print `companies` row count.

Loads env the same way as other scripts: `frontend/nextjs/.env.local`, repo-root
`.env`, then optional ``DOTENV_PATH`` (see `cleanup_leads.py` for worktrees).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_dotenv_path = (os.getenv("DOTENV_PATH") or "").strip()
if _dotenv_path:
    load_dotenv(Path(_dotenv_path).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy import text

from app.database import DATABASE_URL, engine


def _masked_url(url: str) -> str:
    if "@" in url and "://" in url:
        pre, _, rest = url.partition("@")
        if ":" in pre.split("://", 1)[-1]:
            scheme, _, tail = pre.partition("://")
            user, _, _ = tail.partition(":")
            return f"{scheme}://{user}:****@{rest}"
    return url


def _diagnostics(url: str, err: Exception) -> None:
    """Hints for common Supabase + psycopg2 issues (not a substitute for dashboard URI)."""
    msg = str(err).lower()
    try:
        u = urlparse(url.replace("postgresql+psycopg2://", "postgresql://", 1))
    except Exception:
        return

    host = (u.hostname or "").lower()
    port = u.port
    user = u.username or ""

    print("\n── Parsed from DATABASE_URL (no password shown) ──")
    print(f"  host: {host!r}")
    print(f"  port: {port}")
    print(f"  user: {user!r}")

    # Transaction pooler (Supabase): port 6543, user postgres.<project_ref>
    if "pooler.supabase.com" in host:
        if port not in (5432, 6543):
            print("  note: pooler usually uses 5432 (session) or 6543 (transaction).")
        if user == "postgres" and port == 6543:
            print(
                "  hint: Transaction pooler often requires user "
                "'postgres.<your-project-ref>', not plain 'postgres'. "
                "Copy the full URI from Supabase (do not mix host from one mode "
                "with user from another)."
            )
        # Bare project ref as username → FATAL: Tenant or user not found
        if user and user != "postgres" and "." not in user:
            print(
                "\n  Likely mistake: username has no `postgres.` prefix "
                f"({user!r}). Supabase pooler expects `postgres.<project_ref>` "
                "as the user — copy the full URI from the dashboard, not only the ref."
            )
    if host.startswith("db.") and "supabase.co" in host:
        print(
            "  hint: Direct db.* host can fail with 'Connection refused' over IPv6 "
            "on some networks. Try the Session or Transaction pooler URI from the "
            "dashboard instead (same password; different host/port/user format)."
        )

    if "tenant or user not found" in msg:
        print(
            "\n  Supabase pooler: `Tenant or user not found` means the pooler could not "
            "map this host + user + password to a project (not just a “wrong password” "
            "message — that is usually “password authentication failed”)."
        )
        if user.startswith("postgres.") and "pooler.supabase.com" in host:
            print(
                "\n  Your username already looks like session-mode (`postgres.<ref>`). "
                "If it still fails, the usual causes are:\n"
                "  • **Host typo** — the segment `aws-0` vs `aws-1` (and region) must match "
                "the **Connect → Session pooler** string **exactly**. One digit wrong → "
                "this error.\n"
                "  • **Do not assemble the URI by hand** — in the dashboard click **Connect**, "
                "choose **Session pooler**, then **copy** the full URI once and paste into "
                "`.env` (compare host to yours character-for-character).\n"
                "  • **Try another official mode** from the same Connect panel:\n"
                "    – **Direct**: `postgres` @ `db.<ref>.supabase.co:5432` (IPv6 by default; "
                "good test from a Mac on many networks).\n"
                "    – **Transaction**: `postgres` @ `db.<ref>.supabase.co:6543` (different "
                "shape than session pooler; see docs — SQLAlchemy may need prepared "
                "statements disabled for PgBouncer transaction mode).\n"
                "  • If every copied string still fails, Supabase treats some cases as "
                "**project-specific** — open a ticket: "
                "https://supabase.com/dashboard/support/new"
            )
        else:
            print(
                "\n  Use the **exact** user for the mode you selected in **Connect**:\n"
                "  • Session pooler on `*.pooler.supabase.com:5432` → user is normally "
                "`postgres.<project_ref>`.\n"
                "  • Do not mix host from one tab with user from another."
            )
    if "password authentication failed" in msg or "authentication failed" in msg:
        print(
            "\n  Auth failed — almost always one of:\n"
            "  • Password not URL-encoded in the URI. If the password contains "
            "@ # % & + : / ? = or spaces, each must be encoded (e.g. @ → %40). "
            "Easiest fix: reset DB password to a long random string of letters and "
            "digits only, then paste the dashboard URI again.\n"
            "  • Wrong mode: use the username shown for that tab — session pooler uses "
            "`postgres.<ref>` on `*.pooler.supabase.com:5432`; transaction mode often uses "
            "user `postgres` on `db.<ref>.supabase.co:6543` (per dashboard)."
        )
    if "connection refused" in msg or "could not connect" in msg:
        print(
            "\n  Connection refused — not a password check yet; TCP did not reach "
            "Postgres. Check: Supabase project not paused; try pooler URI; try "
            "another network; corporate VPN/firewall blocking outbound 5432/6543."
        )
    if "circuit breaker" in msg or "retrieve database credentials" in msg:
        print(
            "\n  Supabase **session pooler** (Supavisor) refused the connection because its "
            "side could not load database credentials — this is usually **not** a typo in "
            "your `.env` string. It can be transient, or a delay/sync issue after a password "
            "change.\n"
            "  Try: wait a few minutes and retry; or switch `DATABASE_URL` to **Transaction** "
            "mode from **Connect** (`postgres` @ `db.<ref>.supabase.co:6543`), which often "
            "still works when `*.pooler.supabase.com:5432` fails.\n"
            "  If it persists: check https://status.supabase.com and open a support ticket from the dashboard."
        )


def _print_parsed_identity(url: str) -> None:
    try:
        u = urlparse(url.replace("postgresql+psycopg2://", "postgresql://", 1))
    except Exception:
        return
    print(
        "Effective connection (password hidden): "
        f"host={u.hostname!r} port={u.port} user={u.username!r}"
    )


def main() -> None:
    raw = DATABASE_URL
    print("DATABASE_URL:", _masked_url(raw))
    _print_parsed_identity(raw)
    try:
        with engine.connect() as conn:
            n = conn.execute(text("select count(*) from companies")).scalar()
        print("OK — connected. companies count:", n)
    except Exception as e:
        print("FAILED:", e)
        _diagnostics(raw, e)
        print(
            "\nFix: one DATABASE_URL in repo-root .env — paste from "
            "Supabase → Project Settings → Database → Connection string "
            "(pick one mode: Direct, Session pooler, or Transaction pooler; "
            "do not mix parts). "
            "Do not duplicate DATABASE_URL lines."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
