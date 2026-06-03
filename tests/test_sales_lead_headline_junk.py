"""Sales lead names that are news sentences, not buyer companies."""
import pytest

from app.services.lead_filter import is_junk
from app.services.lead_name_gate import check_lead_name


@pytest.mark.parametrize(
    "name",
    [
        "Nabisco is looking to automate it's logistics pipeline...",
        "Nabisco is looking to automate its logistics pipeline",
        "Mondelez is looking to automate warehouse operations",
        "Sysco plans to automate distribution centers nationwide",
    ],
)
def test_sentence_leads_are_junk(name: str):
    junk, reason = is_junk(name)
    assert junk, reason
    ok, gate_reason = check_lead_name(name)
    assert not ok, gate_reason


@pytest.mark.parametrize(
    "name",
    [
        "Nabisco",
        "Mondelez International",
        "Sysco Corporation",
    ],
)
def test_real_buyer_names_kept(name: str):
    junk, _ = is_junk(name)
    assert not junk
    assert check_lead_name(name)[0]
