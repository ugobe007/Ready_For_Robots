"""Truthful zero-state classification for the Jobs workspace.

When a robot produces zero matched jobs, "zero" must be explainable. This is a
read-only honesty layer over the (frozen) matcher output — it changes no
matching decision, ranking, requirement logic, or Understanding. It only reads
the already-derived capabilities and the corpus's family coverage to say WHY
the result was zero.

Three distinct zero states:

- ``insufficient_profile_evidence`` — we could not establish enough grounded
  work capabilities to match confidently (e.g. product_class / mobility /
  manipulation all UNKNOWN). The robot was under-understood, not unmatchable.
- ``no_compatible_jobs`` — the robot's capabilities are grounded and the corpus
  represents that domain, but every candidate job fails a requirement.
- ``corpus_gap`` — the robot's capabilities are grounded, but the corpus has no
  work represented for that capability domain.
"""
from __future__ import annotations

from typing import Any, Optional

INSUFFICIENT_PROFILE_EVIDENCE = "insufficient_profile_evidence"
NO_COMPATIBLE_JOBS = "no_compatible_jobs"
CORPUS_GAP = "corpus_gap"

# Distinctive grounded work primitives. Generic locomotion ("mobile") alone is
# not evidence that we understood what work the robot performs.
_WORK_CAPABILITIES = frozenset(
    {
        "manipulate",
        "dual_arm",
        "tote_transport",
        "hard_floor_scrub",
        "inspect_route",
        "load_unload",
        "reach",
    }
)

# Capability → the corpus job families that capability can serve. Kept local to
# this honesty layer so it never perturbs the matcher.
_CAPABILITY_FAMILIES = {
    "manipulate": frozenset({"pallet", "gripper"}),
    "load_unload": frozenset({"pallet", "gripper"}),
    "dual_arm": frozenset({"pallet", "gripper"}),
    "reach": frozenset({"pallet", "gripper"}),
    "tote_transport": frozenset({"transport", "cart"}),
    "hard_floor_scrub": frozenset({"scrub"}),
    "inspect_route": frozenset({"inspect"}),
}


def _present_work_capabilities(capabilities: Optional[list[dict[str, Any]]]) -> set[str]:
    present: set[str] = set()
    for cap in capabilities or []:
        key = (cap.get("key") or "").strip()
        if key in _WORK_CAPABILITIES:
            present.add(key)
    return present


def classify_zero_state(
    capabilities: Optional[list[dict[str, Any]]],
    corpus_families: set[str],
) -> str:
    """Return the zero-state reason for a robot that matched zero jobs.

    ``capabilities`` is the matcher's derived-capability list (present primitives)
    for this robot; ``corpus_families`` is the set of ``tape_family`` values in
    the current job corpus.
    """
    present = _present_work_capabilities(capabilities)
    if not present:
        return INSUFFICIENT_PROFILE_EVIDENCE

    robot_families: set[str] = set()
    for key in present:
        robot_families |= set(_CAPABILITY_FAMILIES.get(key, frozenset()))

    if robot_families and robot_families.isdisjoint(corpus_families):
        return CORPUS_GAP
    return NO_COMPATIBLE_JOBS


def corpus_family_set() -> set[str]:
    """Families represented in the current job corpus (read-only)."""
    # Imported lazily so this honesty layer never affects matcher import cost.
    from app.services.robot_requirement_match import load_corpus

    return {
        (row.get("tape_family") or "").strip()
        for row in load_corpus()
        if row.get("tape_family")
    }
