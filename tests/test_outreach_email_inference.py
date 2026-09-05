"""Tests for industry-aware default outreach email inference."""
from app.services.outreach_email_inference import (
    infer_cc_outreach_emails,
    infer_outreach_emails,
    infer_primary_outreach_email,
    person_email_candidates,
)


def test_default_primary_is_operations():
    assert infer_primary_outreach_email("acme.com") == "operations@acme.com"


def test_logistics_primary_prefers_plant_manager():
    assert infer_primary_outreach_email("acme.com", "Logistics") == "plantmanager@acme.com"


def test_hospitality_primary_is_operations():
    assert infer_primary_outreach_email("mgm.com", "Hotels & Casinos") == "operations@mgm.com"


def test_cc_excludes_primary_and_caps_count():
    guess = infer_outreach_emails("acme.com", "Manufacturing")
    assert guess is not None
    assert guess.primary == "plantmanager@acme.com"
    assert guess.primary not in guess.cc
    assert len(guess.cc) <= 2
    assert all("@" in x for x in guess.cc)


def test_person_email_patterns():
    emails = person_email_candidates("John", "Smith", "tesla.com")
    assert ("john.smith@tesla.com", "first.last") in emails
    assert ("jsmith@tesla.com", "firstinitiallast") in emails


def test_infer_without_domain_returns_none():
    assert infer_outreach_emails(None) is None
    assert infer_cc_outreach_emails(None) == []


def test_should_reinfer_stored_contact():
    from app.services.outreach_email_inference import should_reinfer_stored_contact

    assert should_reinfer_stored_contact(None, "acme.com") is True
    assert should_reinfer_stored_contact("", "acme.com") is True
    assert should_reinfer_stored_contact("sales@acme.com", "acme.com") is True
    assert should_reinfer_stored_contact("john.smith@acme.com", "acme.com") is False
    assert should_reinfer_stored_contact("buyer@other.com", "acme.com") is False
    assert should_reinfer_stored_contact("operations@acme.com", "acme.com") is True


def test_looks_like_person_email():
    from app.services.outreach_email_inference import looks_like_person_email

    assert looks_like_person_email("john.smith@tesla.com") is True
    assert looks_like_person_email("sales@tesla.com") is False
    assert looks_like_person_email("operations@tesla.com") is False
