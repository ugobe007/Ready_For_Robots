"""operating_environment must emit correct, ontology-known verticals.

Guards the healthcare/eldercare/hospitality mapping — in particular that
"hospitality" is not mislabeled "healthcare" (the word "hospital" is a substring
of "hospitality"), and that only known vertical keys are emitted.
"""
from __future__ import annotations

from app.services import robot_ontology as ont
from app.services.robot_understanding_v1 import facts as F
from app.services.robot_understanding_v1.models import RobotSource


def _envs(text: str) -> set[str]:
    src = RobotSource(id="s", url="https://x.ai/robot", source_type="product",
                      fetched_at="t", title="R", confidence=0.85)
    facts = F._extract_from_page(src, text, subject="", page_url="https://x.ai/robot", page_title="R")
    return {f.value for f in facts if f.predicate == "operating_environment"}


def test_hospitality_not_mislabeled_healthcare():
    envs = _envs("The robot serves guests in hotels and restaurants and hospitality venues nationwide.")
    assert "hospitality" in envs
    assert "restaurant" in envs
    assert "healthcare" not in envs  # 'hospitality' contains 'hospital' — must not leak


def test_healthcare_and_eldercare_distinct():
    assert _envs("Deployed across hospitals and clinics for medication delivery to patient units.") == {"healthcare"}
    assert "eldercare" in _envs("Delivers meals in nursing homes and assisted living senior communities daily.")


def test_all_emitted_environments_are_known_verticals():
    corpus = [
        "This autonomous robot runs in warehouses and factories across the country today.",
        "It works in hotels, restaurants, hospitals, clinics, retail stores and airports nationwide.",
        "Serves residents in nursing homes, senior living and assisted living facilities daily.",
        "Operates in indoor spaces and confined industrial environments for long shifts.",
        "Deployed on construction sites and jobsites for material transport tasks.",
    ]
    emitted: set[str] = set()
    for t in corpus:
        emitted |= _envs(t)
    assert emitted, "no environments emitted"
    assert emitted <= set(ont.verticals()), f"unknown verticals emitted: {emitted - set(ont.verticals())}"
