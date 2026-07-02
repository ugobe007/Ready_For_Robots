from app.services.cal_outreach_send import parse_cal_draft


def test_parse_cal_draft_with_subject_line():
    draft = "Subject: Hello there\n\nBody line one\nBody line two"
    subject, body = parse_cal_draft(draft, "Acme")
    assert subject == "Hello there"
    assert "Body line one" in body


def test_parse_cal_draft_fallback_subject():
    subject, body = parse_cal_draft("Just a body", "Acme Robotics")
    assert subject == "Robot automation partnership — Acme Robotics"
    assert body == "Just a body"
