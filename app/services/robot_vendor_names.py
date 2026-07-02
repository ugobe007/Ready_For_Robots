"""
Known robotics OEMs / vendors — not buyer opportunities for “who will deploy robots”.

These names are filtered in `lead_filter.is_junk` so the pipeline favors end-user accounts.
Conservative matching: normalized exact / starts-with / ends-with known vendor strings.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional, Set

from app.services.humanoid_ontology_terms import HUMANOID_CATALOG_BUYER_VENDORS

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
    "fourier robotics",
    "fftai",
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
    # ── Humanoid OEMs (added for XBOT / CES coverage) ────────────────────────
    "figure ai",
    "agility robotics",
    "apptronik",
    "sanctuary ai",
    "1x technologies",
    "fourier intelligence",
    "fourier robotics",
    "fftai",
    "ubtech robotics",
    "ubtech",
    "engineered arts",
    "deep robotics",
    "deeprobotics",
    "robotera",
    "unitree robotics",
    "unitree",
    "neura robotics",
    "generalist ai",
    "galaxea dynamics",
    "galaxea",
    "foundation future industries",
    "foundation.bot",
    "high torque robotics",
    "hightorque robotics",
    "andromeda robotics",
    "skl robotics",
    # ── Drone / UAV OEMs ─────────────────────────────────────────────────────
    "dji",
    "dji enterprise",
    "skydio",
    "parrot",
    "zipline",
    "wing aviation",
    "percepto",
    "autel robotics",
    "joby aviation",
    "archer aviation",
    "wisk aero",
    "lilium",
    "vertical aerospace",
    # ── 3D Printing / Additive OEMs ──────────────────────────────────────────
    "stratasys",
    "3d systems",
    "markforged",
    "carbon",
    "desktop metal",
    "eos",
    "formlabs",
    "bambu lab",
    # ── Surgical / Medical Robot OEMs ────────────────────────────────────────
    "intuitive surgical",
    "stryker mako",
    "cmr surgical",
    "avatera medical",
    "moon surgical",
    # ── Exoskeleton OEMs ─────────────────────────────────────────────────────
    "ekso bionics",
    "sarcos technology",
    "suitx",
    "cyberdyne",
    "rewalk robotics",
    # ── Additional industrial / cobot OEMs ───────────────────────────────────
    "techman robot",
    "tm robot",
    "dobot",
    "franka emika",
    "aubo robotics",
    "elite robots",
    "kassow robots",
    "vention",
    "rethink robotics",
    # Humanoid OEMs (also synced from humanoid_vendor_catalog)
    "magiclab",
    "magic lab",
    "hexagon robotics",
    "unitree robotics",
    "unitree",
    "fourier intelligence",
    "fftai",
    "engineered arts",
    "sanctuary ai",
    "apptronik",
    "1x technologies",
    "ubtech",
    "realman",
    "agibot",
    "agibot robotics",
    "limx dynamics",
    "limx",
    "milagrow",
    "ecovacs",
    "ecovacs robotics",
    "serve robotics",
    "skild ai",
    "physical intelligence",
    "persona ai",
    "cloudminds",
}


@lru_cache(maxsize=1)
def _all_vendor_names() -> frozenset[str]:
    from app.services.humanoid_ontology_terms import catalog_humanoid_vendor_names

    return frozenset(KNOWN_ROBOTICS_VENDOR_NAMES) | catalog_humanoid_vendor_names()


# Humanoid catalog lists deployment partners (e.g. GXO piloting Digit) — still buyer accounts.
_BUYER_DEPLOYMENT_PARTNERS = frozenset({
    "gxo logistics",
    "gxo",
}) | HUMANOID_CATALOG_BUYER_VENDORS


_LEGAL_SUFFIX = re.compile(
    r"""
    \s*[\(,]?\s*
    (inc\.?|llc\.?|ltd\.?|company|co\.?|plc\.?|gmbh|s\.a\.|s\.p\.a\.?)
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

    raw = " ".join(str(name).strip().lower().split())
    if raw in _BUYER_DEPLOYMENT_PARTNERS:
        return False
    for partner in _BUYER_DEPLOYMENT_PARTNERS:
        if raw.startswith(partner + " ") or raw.startswith(partner + ","):
            return False
    if raw in _all_vendor_names():
        return True

    key = _normalize_key(str(name))
    if not key:
        return False

    if key in _BUYER_DEPLOYMENT_PARTNERS:
        return False
    for partner in _BUYER_DEPLOYMENT_PARTNERS:
        if key.startswith(partner + " ") or key.startswith(partner + ","):
            return False

    if key in _all_vendor_names():
        return True

    # Prefix only (avoid "Acme … Bear Robotics" false positives on endswith)
    for v in _all_vendor_names():
        if key.startswith(v + " ") or key.startswith(v + ","):
            return True

    return False


def vendor_oem_junk_match(name: Optional[str], *, mode: str = "buyer") -> tuple[bool, str]:
    """
    True when ``is_junk`` rejects ``name`` as a robotics vendor/OEM (buyer pipeline).
    Covers blocklist hits and pattern-inferred automation vendors.
    """
    from app.services.lead_filter import is_junk

    junk, reason = is_junk(name, mode=mode)
    if not junk:
        return False, ""
    rl = (reason or "").lower()
    if "robotics vendor" in rl or "known robotics vendor" in rl:
        return True, reason
    if "automation/robotics vendor" in rl:
        return True, reason
    return False, ""
