from app.services.form_spam import (
    field_looks_generated,
    report_download_spam_reason,
    token_looks_generated,
)


def test_operator_sample_is_spam():
    reason = report_download_spam_reason(
        email="info@alohaah.com",
        name="NLexdStETPSyhfSDp",
        company="Qpjgved LLC",
        robot_category="zTBxnhfiXkjdwRgHNyZeXY",
    )
    assert reason == "generated_fields"


def test_real_oem_request_is_not_spam():
    reason = report_download_spam_reason(
        email="sara@locusrobotics.com",
        name="Sara Chen",
        company="Locus Robotics",
        robot_category="warehouse AMR",
    )
    assert reason is None


def test_honeypot_is_spam():
    reason = report_download_spam_reason(
        email="sara@locusrobotics.com",
        name="Sara Chen",
        company="Locus Robotics",
        robot_category="humanoid",
        honeypot="https://spam.example",
    )
    assert reason == "honeypot"


def test_disposable_email_is_spam():
    reason = report_download_spam_reason(
        email="bot@mailinator.com",
        name="Sara Chen",
        company="Locus Robotics",
        robot_category="humanoid",
    )
    assert reason == "disposable_email"


def test_single_odd_field_is_not_enough():
    reason = report_download_spam_reason(
        email="ops@acmelogistics.com",
        name="Alex Rivera",
        company="Acme Logistics",
        robot_category="zTBxnhfiXkjdwRgHNyZeXY",
    )
    assert reason is None


def test_known_brands_are_not_generated():
    for token in (
        "Schmidt",
        "Stryker",
        "DeWalt",
        "NVIDIA",
        "McLaughlin",
        "Boston",
        "Dynamics",
        "humanoid",
        "warehouse",
    ):
        assert token_looks_generated(token) is False, token
    assert field_looks_generated("Boston Dynamics") is False
    assert field_looks_generated("Figure AI") is False
    assert field_looks_generated("Plus One Robotics") is False
