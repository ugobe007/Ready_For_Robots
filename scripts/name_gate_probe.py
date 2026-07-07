"""Probe every name-gate verdict for specific names to see which layer fires (or not)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

NAMES = [
    "Locus Robotics",
    "Locus Robotics Surpasses 5 Billion Pick Milestone",
    "Locus Robotics survey: 7",
    "Daifuku Co",
    "Daifuku",
    "Keenon Humanoid Robot Joins Ho",
    "PA logistics company",
    "Miami logistics company",
    "2021 Women",
    "Dynamic Warehouse AI-Powered AMRs",
    "Radisson Hotel Group",
]


def main() -> int:
    from app.services.company_name_validation import reject_as_non_company_name
    from app.services.known_brands import is_allowlisted_company_name
    from app.services.lead_filter import is_headline_fragment, is_junk
    from app.services.robot_vendor_names import is_known_robotics_vendor_name

    print("=" * 100)
    print(f"{'NAME':45} {'allow':6} {'vendor':7} {'frag':6} {'nonco':6} {'is_junk'}")
    print("=" * 100)
    for n in NAMES:
        allow = is_allowlisted_company_name(n)
        vend = is_known_robotics_vendor_name(n)
        frag = is_headline_fragment(n)[0]
        nonco = reject_as_non_company_name(n)[0]
        junk, reason = is_junk(n)
        print(f"{n[:45]:45} {str(allow):6} {str(vend):7} {str(frag):6} {str(nonco):6} {junk} :: {reason[:40]}")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
