#!/usr/bin/env python3
"""Delete human occupation postings from robot_jobs.

Cook, bartender, nurse, and warehouse associate are human hires. A row stays
only when the posting asks for a robot. Child match and evidence rows follow
the robot_jobs foreign keys (ON DELETE CASCADE).

  python3 scripts/clean_human_labor_from_robot_jobs.py
  python3 scripts/clean_human_labor_from_robot_jobs.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from app.services.robot_job_extract import asks_for_a_robot  # noqa: E402


def is_human_labor_posting(
    task: Optional[str],
    workflow: Optional[str] = None,
    why: Optional[str] = None,
    requirements: Any = None,
) -> bool:
    """True when this stored job is a human hire, not a robot request."""
    extra = [workflow or "", why or ""]
    if isinstance(requirements, dict):
        extra.append(str(requirements.get("job_description") or "")[:4000])
    return not asks_for_a_robot(task or "", *extra)


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove human labor rows from robot_jobs")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete the human-labor rows. Without this flag, only print the counts.",
    )
    args = parser.parse_args()

    from app.database import SessionLocal
    from app.models.robot_directed_discovery import RobotJob

    db = SessionLocal()
    try:
        rows = db.query(
            RobotJob.id,
            RobotJob.robot_compatible_task,
            RobotJob.observed_workflow,
            RobotJob.why_job,
            RobotJob.requirements,
        ).all()
        drop_ids = [
            row.id
            for row in rows
            if is_human_labor_posting(
                row.robot_compatible_task,
                row.observed_workflow,
                row.why_job,
                row.requirements,
            )
        ]
        total = len(rows)
        drop = len(drop_ids)
        keep = total - drop
        print(f"Total robot_jobs: {total}")
        print(f"Human labor to delete: {drop}")
        print(f"Robot requests to keep: {keep}")
        if not args.apply:
            print("Dry run. Re-run with --apply to delete.")
            return
        deleted = 0
        for start in range(0, drop, 400):
            chunk = drop_ids[start : start + 400]
            deleted += (
                db.query(RobotJob)
                .filter(RobotJob.id.in_(chunk))
                .delete(synchronize_session=False)
            )
            db.commit()
        left = db.query(RobotJob).count()
        print(f"Deleted: {deleted}")
        print(f"Remaining robot_jobs: {left}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
