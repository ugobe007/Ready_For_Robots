"""
Shared environment loading for harness scripts (snapshot, mission runner, notify).

Priority for DATABASE_URL:
  1. HARNESS_DATABASE_URL (optional read-only override)
  2. Repo-root `.env` (overrides frontend/nextjs/.env.local)
  3. Shell-exported DATABASE_URL when dotenv value is template/sqlite
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite


def load_harness_env(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    shell_url = (os.environ.get("DATABASE_URL") or "").strip()
    harness_url = (os.environ.get("HARNESS_DATABASE_URL") or "").strip()

    load_dotenv(root / "frontend" / "nextjs" / ".env.local")
    load_dotenv(root / ".env", override=True)

    source = "dotenv"
    if harness_url and not database_url_is_template_or_sqlite(harness_url):
        os.environ["DATABASE_URL"] = harness_url
        source = "HARNESS_DATABASE_URL"
    elif shell_url and database_url_is_template_or_sqlite(
        (os.environ.get("DATABASE_URL") or "").strip()
    ):
        os.environ["DATABASE_URL"] = shell_url
        source = "shell"

    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        return {"status": "unavailable", "reason": "no DATABASE_URL or HARNESS_DATABASE_URL", "source": None}
    if database_url_is_template_or_sqlite(url):
        return {
            "status": "unavailable",
            "reason": "DATABASE_URL looks like template or sqlite",
            "source": source,
        }
    return {"status": "configured", "source": source}


def database_telemetry(root: Path | None = None) -> dict[str, Any]:
    """Resolve URL config and optionally verify a live connection."""
    meta = load_harness_env(root)
    if meta.get("status") != "configured":
        return meta

    try:
        from sqlalchemy import text

        from app.database import SessionLocal
    except Exception as exc:
        return {**meta, "status": "unavailable", "reason": f"import failed: {exc}"}

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {**meta, "status": "connected"}
    except Exception as exc:
        return {**meta, "status": "unavailable", "reason": str(exc)[:240]}
    finally:
        db.close()
