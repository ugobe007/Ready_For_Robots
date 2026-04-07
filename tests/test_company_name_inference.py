from app.services.company_name_inference import (
    best_name_from_signals,
    extract_company_name_from_headline,
    should_attempt_name_fix,
)


def test_faraday_future_headline():
    t = (
        "Faraday Future to Kick Off 2026 EAI Robotics Deliveries Beginning Feb. 27 "
        "by Delivering to an Airbnb Operator"
    )
    assert extract_company_name_from_headline(t) == "Faraday Future"


def test_best_name_from_signals():
    assert (
        best_name_from_signals(
            [
                "noise",
                "Acme Robotics announces Series B for warehouse arms",
            ]
        )
        == "Acme Robotics"
    )


def test_should_attempt_name_fix_long_headline():
    long = "Some Company announces something " * 5
    assert should_attempt_name_fix(long) is True


def test_should_not_fix_short_clean_name():
    assert should_attempt_name_fix("Target Corporation") is False
