"""Industry inference — avoid hospitality false positives for automotive OEMs (STR headlines)."""
from types import SimpleNamespace

from app.services.industry_inference import effective_industry_for_lead, infer_industry_from_text


def test_faraday_future_known_oem():
    assert infer_industry_from_text("Faraday Future robotics") == "Automotive & Manufacturing"


def test_vacation_rental_headline_not_hospitality_when_automotive():
    blob = (
        "Faraday Future to Kick Off 2026 EAI Robotics Deliveries Beginning Feb. 27 "
        "by Delivering to an Airbnb Operator; Establishes First U.S. "
        "EAI Robot & Vehicle + Vacation Rental Deploy"
    )
    assert infer_industry_from_text("Faraday Future " + blob) == "Automotive & Manufacturing"


def test_effective_industry_prefers_inference_over_stored_hospitality():
    sig = SimpleNamespace(signal_text="Airbnb vacation rental robot delivery pilot")
    eff = effective_industry_for_lead("Faraday Future", "Hospitality", [sig])
    assert eff == "Automotive & Manufacturing"


def test_effective_industry_falls_back_to_stored_when_inference_unknown():
    sig = SimpleNamespace(signal_text="generic news")
    eff = effective_industry_for_lead("Acme Corp", "Logistics", [sig])
    assert eff == "Logistics"
