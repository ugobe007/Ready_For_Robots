#!/usr/bin/env python3
"""Append a row to docs/cal_learning_log.md (Stage 1 Learn).

Example:
  python scripts/cal_log_learning.py \\
    --original 'Receiving. Replenishment. Returns.' \\
    --correction 'Explain how these create operational friction' \\
    --why 'Labels are not insights' \\
    --rule 'Cal connects observations; he does not stack labels.' \\
    --outcome 'template updated'
"""
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "cal_learning_log.md"


def _esc(cell: str) -> str:
    return (cell or "").replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a Cal Learning Log row.")
    parser.add_argument("--original", required=True, help="Broken behavior or copy")
    parser.add_argument("--correction", required=True, help="What worked instead")
    parser.add_argument("--why", required=True, help="One-sentence why")
    parser.add_argument("--rule", required=True, help="General Cal rule learned")
    parser.add_argument("--outcome", default="pending", help="Outcome if known")
    parser.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    args = parser.parse_args()

    if not LOG.exists():
        raise SystemExit(f"Missing learning log: {LOG}")

    row = (
        f"| {args.date} | {_esc(args.original)} | {_esc(args.correction)} | "
        f"{_esc(args.why)} | **{_esc(args.rule)}** | {_esc(args.outcome)} |"
    )

    text = LOG.read_text(encoding="utf-8")
    # Insert after header separator line (first table row block).
    # Table starts with | Date | ... then |------| then rows (newest first).
    match = re.search(
        r"(\| Date \| Original \| Correction \| Why \| New Cal Rule \| Outcome \|\n"
        r"\|------\|----------\|------------\|-----\|--------------\|---------\|\n)",
        text,
    )
    if not match:
        raise SystemExit("Could not find learning log table header")

    insert_at = match.end()
    new_text = text[:insert_at] + row + "\n" + text[insert_at:]

    if args.dry_run:
        print(row)
        return 0

    LOG.write_text(new_text, encoding="utf-8")
    print(f"Appended to {LOG.relative_to(ROOT)}")
    print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
