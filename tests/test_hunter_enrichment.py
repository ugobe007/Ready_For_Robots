"""Hunter integration in lead enrichment waterfall."""
from unittest.mock import MagicMock, patch

from app.services.lead_enrichment import resolve_outreach_email


@patch("app.services.lead_enrichment.hunter_contact_email")
def test_resolve_outreach_email_uses_hunter_before_signal(mock_hunter):
    mock_hunter.return_value = {
        "email": "vp@acme.com",
        "title": "VP Operations",
        "source": "hunter_finder",
    }
    company = MagicMock()
    company.name = "Acme"
    company.website = "https://acme.com"
    company.industry = "Logistics"
    company.crm_metadata = {}
    acct = MagicMock()
    acct.contact_email = None
    acct.website = None
    acct.industry = None

    email, source, title = resolve_outreach_email(
        company,
        acct,
        use_apollo=False,
        signal_texts=["automation@acme.com"],
    )
    assert email == "vp@acme.com"
    assert source == "hunter"
    assert title == "VP Operations"
    mock_hunter.assert_called_once()
