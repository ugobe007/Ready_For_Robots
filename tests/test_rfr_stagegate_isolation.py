"""Ready For Robots admin must never surface StageGate show-ops voice."""
from types import SimpleNamespace

import pytest

from app.services.brand import is_stagegate_branded
from app.services.cal_draft_guard import draft_needs_regeneration
from app.services.cal_insights import pick_cal_insight
from app.services.stagegate_crm_bridge import _existing_company_is_rfr_buyer, _upsert_company


def test_is_stagegate_branded_from_metadata():
    company = SimpleNamespace(
        crm_metadata={"outreach_pipeline": "stagegate"},
        data_source="buyer_scrape",
    )
    assert is_stagegate_branded(company)


def test_rfr_buyer_not_stagegate_branded():
    company = SimpleNamespace(
        crm_metadata={"cal_variant_id": "what_survives"},
        data_source="rss",
    )
    assert not is_stagegate_branded(company)


def test_buyer_draft_with_stagegate_copy_needs_regeneration():
    stagegate_body = (
        "Subject: Acme — show logistics\n\n"
        "I'm Cal with StageGate — we're in Las Vegas and help robotics OEMs with show logistics: "
        "bonded warehousing, staging, unpack/test, and on-site tech support during demos. "
        "If it's useful, reply with your booth number and move-in dates and I'll send a calendar link. "
        "You can also register at onstage.bot if you prefer to self-serve.\n\n"
        "Thanks,\nCal\nStageGate · onstage.bot\nLas Vegas"
    )
    needs, reason = draft_needs_regeneration(stagegate_body, account_type="buyer")
    assert needs
    assert "stagegate" in reason.lower()


def test_vendor_insights_never_pick_stagegate_logistics_copy():
    for seed in ("a", "b", "c", "d", "e", "f", "g", "h"):
        text = pick_cal_insight(
            company_name=f"Vendor {seed}",
            industry="Robotics",
            seed=seed,
            audience="vendor",
        ).lower()
        assert "onstage.bot" not in text
        assert "stagegate" not in text
        assert "bonded warehous" not in text


def test_admin_cal_draft_rejects_stagegate_company():
    from app.api.admin_extended import _cal_draft_for_company

    company = SimpleNamespace(
        id=99,
        name="Robot OEM Inc",
        industry="Robotics OEM",
        website="https://robot-oem.example",
        crm_metadata={"outreach_pipeline": "stagegate"},
    )
    with pytest.raises(ValueError, match="StageGate accounts are isolated"):
        _cal_draft_for_company(company)


def test_existing_company_is_rfr_buyer():
    buyer = SimpleNamespace(
        crm_metadata={},
        source="rss",
    )
    assert _existing_company_is_rfr_buyer(buyer)

    stagegate = SimpleNamespace(
        crm_metadata={"outreach_pipeline": "stagegate"},
        source="stagegate_oem",
    )
    assert not _existing_company_is_rfr_buyer(stagegate)
