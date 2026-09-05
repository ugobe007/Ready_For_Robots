#!/usr/bin/env python3
"""
Repair humanoid_benchmarks: remove headline junk, restore Unitree/flagships, backfill specs.

Usage (repo root, DATABASE_URL in .env):
  PYTHONPATH=. python3 scripts/repair_humanoid_index.py
  PYTHONPATH=. python3 scripts/repair_humanoid_index.py --dry-cleanup
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv

load_dotenv(_root / ".env")

from app.database import SessionLocal
from app.services.humanoid_benchmark_backfill import repair_humanoid_index
from app.services.humanoid_catalog_cleanup import cleanup_humanoid_benchmarks


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair humanoid index in Postgres")
    parser.add_argument(
        "--dry-cleanup",
        action="store_true",
        help="Preview junk removal only, then exit",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.dry_cleanup:
            preview = cleanup_humanoid_benchmarks(db, dry_run=True)
            print(preview)
            return
        result = repair_humanoid_index(db)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
