#!/usr/bin/env python3
"""Verify DATABASE_URL (repo-root .env) and print companies row count."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.database import DATABASE_URL, engine


def main() -> None:
    masked = DATABASE_URL
    if "@" in masked and "://" in masked:
        pre, _, rest = masked.partition("@")
        if ":" in pre.split("://", 1)[-1]:
            scheme, _, tail = pre.partition("://")
            user, _, _ = tail.partition(":")
            masked = f"{scheme}://{user}:****@{rest}"

    print("DATABASE_URL:", masked)
    try:
        with engine.connect() as conn:
            n = conn.execute(text("select count(*) from companies")).scalar()
        print("OK — connected. companies count:", n)
    except Exception as e:
        print("FAILED:", e)
        print(
            "\nFix: set a single DATABASE_URL in repo-root .env from "
            "Supabase → Project Settings → Database (reset password if needed). "
            "Do not duplicate DATABASE_URL lines."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
