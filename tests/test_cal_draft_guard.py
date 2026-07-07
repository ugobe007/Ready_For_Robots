from app.services.cal_autonomy import cal_buyer_outreach_body
from app.services.cal_draft_guard import draft_needs_regeneration, is_complete_cal_draft, parse_cal_draft_or_raise


class _FakeCompany:
    def __init__(self, name: str, industry: str = "Logistics"):
        self.name = name
        self.industry = industry


def test_truncated_preview_rejected():
    truncated = (
        "Subject: quick question about UPS Supply Chain Solutions's ops\n\n"
        "Hi — Cal from Ready For Robots.\n\n"
        "I help ops teams narrow the robotics vendor field. We monitor public signals — labor pressu"
    )
    ok, reason = is_complete_cal_draft(truncated)
    assert not ok
    assert "short" in reason.lower() or "mid-sentence" in reason.lower()


def test_complete_buyer_draft_accepted():
    body = cal_buyer_outreach_body(_FakeCompany("UPS Supply Chain Solutions", "Logistics"), fresh=True)
    full = f"Subject: robotics shortlist for UPS Supply Chain Solutions\n\n{body}"
    assert is_complete_cal_draft(full)[0]
    assert "vendor" in full.lower()
    # Value-first copy: leads with the buyer outcome (shortlist + payback), not surveillance.
    assert "shortlist" in full.lower()
    assert "payback" in full.lower()
    # The old surveillance framing must not creep back in.
    assert "we monitor" not in full.lower()
    assert "watchlist" not in full.lower()
    assert "generic vendor browse" not in full.lower()


def test_wrong_vendor_pitch_on_buyer_needs_regeneration():
    vendor_pitch = (
        "Hey,\n\nCal here — I run the automation research desk at Ready For Robots.\n\n"
        "We track robot companies by deployment type and industry fit. Based on Hawaiian Airlines's profile, "
        "I have a short list of vendors worth a look.\n\n"
        "Want me to send over the shortlist? Quick reply is all it takes.\n\n"
        "— Cal\nReady For Robots"
    )
    needs, reason = draft_needs_regeneration(vendor_pitch, account_type="buyer")
    assert needs
    assert "vendor-facing" in reason


def test_parse_cal_draft_or_raise_raises_on_truncated():
    truncated = "Subject: test\n\nHi — Cal from Ready For Robots.\n\nI help ops teams narrow the robotics vendor field. We monitor public signals — labor pressu"
    try:
        parse_cal_draft_or_raise(truncated, "Acme")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "short" in str(exc).lower() or "mid-sentence" in str(exc).lower()
