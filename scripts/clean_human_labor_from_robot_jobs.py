#!/usr/bin/env python3
"""RETIRED — do not resurrect.

On 2026-10-11 scripts/clean_human_labor_from_robot_jobs.py deleted ~14,500
Robot Jobs because it treated operational postings (cook, picker, "$/hr") as
"human labor contamination". Those postings ARE the product: human work a
robot could be hired to do.

Robot Jobs are never deleted to "clean" them. They are re-tiered:

    python3 scripts/reclassify_robot_jobs.py            # dry run
    python3 scripts/reclassify_robot_jobs.py --apply    # update tiers only

Recovery:  python3 scripts/rebuild_robot_jobs.py --help
"""
import sys

sys.exit(__doc__)
