"""
Known robotics OEMs / vendors — not buyer opportunities for “who will deploy robots”.

These names are filtered in `lead_filter.is_junk` so the pipeline favors end-user accounts.
Conservative matching: normalized exact / starts-with / ends-with known vendor strings.
"""
from __future__ import annotations

import re
from typing import Optional, Set

# Normalized (lowercase, single spaces). Expand as you discover false positives in the wild.
KNOWN_ROBOTICS_VENDOR_NAMES: Set[str] = {
    # User-called out + common AMR / service robot OEMs
    "bear robotics",
    "unbox robotics",
    "brain corp",
    "brain corporation",
    "knightscope",
    "aethon",
    "savioke",
    "relay robotics",
    "relay robotics (savioke)",
    "pudu robotics",
    "otto motors",
    "fetch robotics",
    "diligent robotics",
    "greyorange",
    "geek+",
    "geekplus",
    "vecna robotics",
    "cognex",
    "universal robots",
    "mobile industrial robots",
    "mir",
    "mir (mobile industrial robots)",
    "agility robotics",
    "figure ai",
    "dexterity ai",
    "simbe robotics",
    "reflex robotics",
    "brightpick",
    "xenex",
    "uvd robots",
    "uvd robots (blue ocean robotics)",
    "blue ocean robotics",
    "keenon robotics",
    "richtech robotics",
    "fortna",
    "autostore",
    "abb robotics",
    "fanuc",
    "fanuc america",
    "kuka",
    "kuka robotics",
    "yaskawa",
    "comau",
    "epson robotics",
    "techman robot",
    "doosan robotics",
    "franka emika",
    "neura robotics",
    "bosch rexroth",
    # Often appear as “company” in funding / product headlines scraped as leads
    "symbiotic",
    "symbiotic systems",
    # Hospitality service robots (sell to hotels/restaurants, not buyers)
    "maidbot",
    "somatic",
    "somatic ai",
    "aethon",
    "aethon inc",
    "swisslog",
    "swisslog healthcare",
    # AMR / fulfillment robot vendors
    "6 river systems",
    "6river systems",
    "hai robotics",
    "quicktron",
    "mujin",
    "covariant",
    "covariant ai",
    "nuro",
    "apptronik",
    "sanctuary ai",
    "1x technologies",
    "fourier intelligence",
    "boston dynamics",
    "waymo",
    "gatik",
    "outrider",
    "seegrid",
    "badger technologies",
    "bossa nova robotics",
    "bossa nova",
    "autonomous solutions",
    "pal robotics",
    "clearpath robotics",
    "clearpath",
    "robotnik",
    "omron",
    "omron mobile robots",
    "zebra technologies",
    # Named explicitly from user-reported false positives
    "robosizeme",
    "robosize me",
}


_LEGAL_SUFFIX = re.compile(
    r"""
    \s*[\(,]?\s*
    (inc\.?|llc\.?|ltd\.?|corp\.?|corporation|company|co\.?|plc\.?|gmbh|s\.a\.|s\.p\.a\.?)
    \s*\)?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _normalize_key(name: str) -> str:
    s = " ".join(name.strip().lower().split())
    s = _LEGAL_SUFFIX.sub("", s).strip()
    s = re.sub(r"\s*\([^)]*\)\s*", " ", s)
    s = " ".join(s.split())
    return s


def is_known_robotics_vendor_name(name: Optional[str]) -> bool:
    """
    True when `name` is (or clearly starts with) a known robot manufacturer / OEM,
    not an end customer evaluating automation.
    """
    if not name or not str(name).strip():
        return False

    key = _normalize_key(str(name))
    if not key:
        return False

    if key in KNOWN_ROBOTICS_VENDOR_NAMES:
        return True

    # Prefix only (avoid "Acme … Bear Robotics" false positives on endswith)
    for v in KNOWN_ROBOTICS_VENDOR_NAMES:
        if key.startswith(v + " ") or key.startswith(v + ","):
            return True

    return False
