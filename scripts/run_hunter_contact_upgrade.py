#!/usr/bin/env python3
"""Upgrade role-inbox contacts to Hunter named emails when decision makers exist."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_dotenv_path = (os.getenv("DOTENV_PATH") or "").strip()
if _dotenv_path:
    load_dotenv(Path(_dotenv_path).expanduser(), override=True)
_loaded = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded):
    os.environ["DATABASE_URL"] = _shell_database_url

from app.database import SessionLocal
from app.services.hunter_contact_upgrade import run_hunter_upgrade_batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Hunter contact upgrade batch")
    parser.add_argument("--limit", type=int, default=25, help="Max leads to upgrade")
    parser.add_argument(
        "--tier",
        action="append",
        dest="tiers",
        default=["HOT", "WARM"],
        help="Priority tiers (repeatable)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        stats = run_hunter_upgrade_batch(
            db,
            limit=max(1, args.limit),
            tiers={t.strip().upper() for t in args.tiers if t.strip()},
        )
        print(json.dumps(stats, indent=2, default=str))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
