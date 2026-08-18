"""Truthful zero-state classification (honesty layer over the frozen matcher)."""
from app.services.zero_state import (
    CORPUS_GAP,
    INSUFFICIENT_PROFILE_EVIDENCE,
    NO_COMPATIBLE_JOBS,
    classify_zero_state,
    corpus_family_set,
)

# The live corpus families (transport/scrub/cart/pallet/gripper/inspect).
CORPUS = corpus_family_set()


def test_no_capabilities_is_insufficient_profile_evidence():
    # 1X NEO shape: nothing grounded (only payload/IP were extracted upstream).
    assert classify_zero_state([], CORPUS) == INSUFFICIENT_PROFILE_EVIDENCE
    # Generic mobility alone is not work evidence.
    assert (
        classify_zero_state([{"key": "mobile"}], CORPUS)
        == INSUFFICIENT_PROFILE_EVIDENCE
    )


def test_grounded_caps_in_covered_domain_is_no_compatible_jobs():
    caps = [{"key": "manipulate"}, {"key": "reach"}]
    assert classify_zero_state(caps, CORPUS) == NO_COMPATIBLE_JOBS


def test_grounded_caps_outside_corpus_is_corpus_gap():
    # A grounded capability whose families are not represented in this corpus.
    empty_corpus: set[str] = set()
    assert classify_zero_state([{"key": "manipulate"}], empty_corpus) == CORPUS_GAP
    # Partial corpus that covers scrub only → a manipulation robot is a corpus gap.
    assert classify_zero_state([{"key": "manipulate"}], {"scrub"}) == CORPUS_GAP


def test_corpus_has_expected_families():
    assert {"transport", "scrub", "cart", "pallet", "gripper", "inspect"} <= CORPUS


def test_neo_real_profile_is_insufficient_when_available():
    # If the captured production NEO profile is present, confirm end-to-end that
    # the frozen matcher grounds no work capabilities → insufficient evidence.
    import json
    import os

    path = "/tmp/neo_profile.json"
    if not os.path.exists(path):
        return  # profile snapshot not present in this environment; unit cases cover logic
    from app.services.robot_requirement_match import match_jobs_from_profile

    profile = json.load(open(path))
    result = match_jobs_from_profile(profile)
    assert result["job_count"] == 0
    assert (
        classify_zero_state(result.get("capabilities") or [], CORPUS)
        == INSUFFICIENT_PROFILE_EVIDENCE
    )
