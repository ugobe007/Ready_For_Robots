from app.api.robot_companies import _vendor_signup_email


class _RobotCompany:
    company_name = "DexMate Robotics"


def test_vendor_signup_email_only_mentions_three_matches():
    matches = [
        {"company_name": f"Buyer {i}", "industry": "Logistics", "why_match": "Matches AMR workflow."}
        for i in range(1, 6)
    ]

    email = _vendor_signup_email(_RobotCompany(), matches)

    assert "Buyer 1" in email["body"]
    assert "Buyer 2" in email["body"]
    assert "Buyer 3" in email["body"]
    assert "Buyer 4" not in email["body"]
    assert "Buyer 5" not in email["body"]
    assert "create a Ready For Robots account" in email["body"]
    assert "short call" in email["body"]
