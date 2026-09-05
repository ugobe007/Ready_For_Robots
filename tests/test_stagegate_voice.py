"""Tests for StageGate Cal outreach voice."""
from app.services.stagegate_voice import (
    STAGEGATE_OUTREACH_RULES,
    stagegate_outreach_email,
    stagegate_subject,
)


def test_stagegate_subject_names_show():
    subject = stagegate_subject("Yaskawa", "Automate 2026")
    assert "Yaskawa" in subject
    assert "Automate 2026" in subject
    assert "pre-floor" in subject.lower()


def test_stagegate_email_follows_training_format():
    draft = stagegate_outreach_email(
        "Yaskawa",
        trade_show="Automate 2026",
        contact_name="Jordan Lee",
    )
    body = draft["body"]

    assert draft["subject"] == stagegate_subject("Yaskawa", "Automate 2026")
    assert body.startswith("Hi Jordan Lee,")
    assert "StageGate" in body
    assert "Las Vegas" in body
    assert "Automate 2026" in body
    assert "onstage.bot" in body
    assert "loose connectors" in body
    assert "booth number" in body
    assert "calendar link" in body
    assert "Ready For Robots" not in body
    assert "ontology" not in body.lower()
    assert len(body.split()) <= 160


def test_stagegate_email_falls_back_to_company_greeting():
    draft = stagegate_outreach_email("Yaskawa", trade_show="Automate 2026")
    assert draft["body"].startswith("Hi Yaskawa team,")


def test_stagegate_training_rules_documented():
    assert len(STAGEGATE_OUTREACH_RULES) >= 6
    joined = " ".join(STAGEGATE_OUTREACH_RULES).lower()
    assert "onstage.bot" in joined
    assert "trade show" in joined
