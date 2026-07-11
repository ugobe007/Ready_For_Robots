"""Tests for demand-side buyer ingestion (DB-free: scoring + tier + rendering).

These pin the two guarantees the curated source depends on:
1. A strong sector-true signal set lands a high-fit operator at HOT/WARM (so Cal
   actually queues it), and
2. The curated dataset names all clear the junk gate (no real operator silently
   dropped) — the failure mode we hit and fixed during the build.
"""
from __future__ import annotations

import importlib.util
import os

from app.services.demand_side_ingest import _rendered_signals, preview_operator_tier

SIG = [
    (
        "labor_shortage",
        "{name}, a large {industry} operator, sits in a sector facing acute front-line "
        "labor shortages that are pushing operators to evaluate service and "
        "material-handling robots.",
        0.88,
    ),
    (
        "expansion",
        "As a high-volume {industry} operator, {name} runs the repetitive, hard-to-staff "
        "workflows where robots are being deployed to offset chronic staffing gaps.",
        0.82,
    ),
]


def _load_dataset():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "seed_demand_side_buyers.py")
    spec = importlib.util.spec_from_file_location("seed_demand_side_buyers", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_rendered_signals_interpolate_name_and_industry():
    out = _rendered_signals("Acme Logistics", "Logistics & Warehousing", SIG)
    assert len(out) == 2
    assert all("Acme Logistics" in text for _, text, _ in out)
    assert all("Logistics & Warehousing" in text for _, text, _ in out)
    # {placeholders} fully consumed
    assert not any("{name}" in text or "{industry}" in text for _, text, _ in out)


def test_high_fit_operator_lands_hot_or_warm():
    pred = preview_operator_tier(
        name="Ryder System", industry="Logistics & Supply Chain", signals=SIG,
        employee_estimate=40000,
    )
    assert pred["junk"] is False
    assert pred["tier"] in ("HOT", "WARM")
    assert pred["overall_intent_score"] >= 45


def test_headline_shaped_name_is_rejected_as_junk():
    # The junk gate must still catch headline-shaped / possessive names; we route
    # around it in the dataset with clean brand names, never by weakening the gate.
    pred = preview_operator_tier(
        name="Zaxby's", industry="Food Service (Restaurants)", signals=SIG,
    )
    assert pred["junk"] is True
    assert pred["tier"] == "JUNK"


def test_every_curated_operator_clears_the_junk_gate():
    mod = _load_dataset()
    dropped = []
    for op in mod.OPERATORS:
        pred = preview_operator_tier(
            name=op["name"], industry=op["industry"], signals=mod.SIGNALS,
            employee_estimate=op.get("employee_estimate"),
        )
        if pred["junk"] or pred["tier"] not in ("HOT", "WARM"):
            dropped.append((op["name"], pred["tier"], pred["reason"]))
    assert not dropped, f"curated operators not queueable: {dropped}"


def test_dataset_industries_are_high_fit():
    from app.services.lead_filter import _industry_fits

    mod = _load_dataset()
    off_fit = [op["name"] for op in mod.OPERATORS if not _industry_fits(op["industry"])]
    assert not off_fit, f"operators with non-high-fit industry: {off_fit}"
