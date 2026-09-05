#!/usr/bin/env python3
"""Print the M2 Novolex + four-physics truth matrix against frozen profiles."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.robot_requirement_match import match_job_spec, match_jobs_from_profile

FIX = ROOT / "tests" / "fixtures" / "m2_profiles"

JOBS = [
    ("manip_novolex_kinston_nc", "Novolex case palletizing"),
    ("origin_curascript_tempe", "CuraScript tote return"),
    ("neo_unifi_atl", "Airport hard-floor scrub"),
    ("plant_inspect", "Inspection route"),
]
ROBOTS = [
    ("vega", "Dexmate Vega"),
    ("digit", "Agility Digit"),
    ("origin", "Locus Origin"),
    ("neo", "Avidbots Neo"),
    ("spot", "Boston Dynamics Spot"),
    ("fixed_arm", "Fixed-cell cobot"),
]


def main() -> None:
    print("M2 requirement truth matrix (frozen profiles)\n")
    for job_key, job_label in JOBS:
        print(f"## {job_label}  ({job_key})")
        for fname, robot in ROBOTS:
            profile = json.loads((FIX / f"{fname}.json").read_text())
            card = match_job_spec(profile, job_key)
            print(f"  {card.verdict:16}  {robot}")
            if card.why:
                print(f"    why: {'; '.join(card.why)}")
            if card.still_unknown:
                print(f"    unknown: {'; '.join(card.still_unknown)}")
            if card.blockers:
                print(f"    blocker: {'; '.join(card.blockers)}")
        print()
    print("## Corpus top boards")
    for fname, robot in ROBOTS[:4]:
        profile = json.loads((FIX / f"{fname}.json").read_text())
        result = match_jobs_from_profile(profile)
        fams = sorted({j.get("tape_family") for j in result["jobs"]})
        print(f"  {robot}: {result['job_count']} possible  families={fams}")
        for j in result["jobs"][:5]:
            print(f"    - {j['title'][:60]}")


if __name__ == "__main__":
    main()
