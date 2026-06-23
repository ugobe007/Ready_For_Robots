"""Robotics OEM vendor name filter — buyer deployers vs manufacturer junk."""
import pytest

from app.services.lead_filter import is_junk
from app.services.robot_vendor_names import is_known_robotics_vendor_name, vendor_oem_junk_match


@pytest.mark.parametrize(
    "name",
    [
        "Physical Intelligence",
        "Skild AI",
        "Persona AI",
        "Keenon Robotics",
        "Milagrow",
        "ECOVACS Robotics",
        "Realman Robotics",
        "AgiBot",
        "Serve Robotics",
        "CloudMinds",
    ],
)
def test_new_oem_names_flagged_as_vendor(name):
    assert is_known_robotics_vendor_name(name) is True
    junk, reason = is_junk(name, mode="buyer")
    assert junk is True
    assert "vendor" in reason.lower() or "oem" in reason.lower()


@pytest.mark.parametrize(
    "name",
    [
        "Foxconn",
        "Siemens AG",
        "SoftBank Robotics",
        "Toyota Material Handling",
        "Samsung Electronics",
        "Mercedes-Benz",
        "GXO Logistics",
    ],
)
def test_catalog_buyer_deployers_not_flagged_as_vendor(name):
    assert is_known_robotics_vendor_name(name) is False


def test_tesla_allowlisted_in_buyer_pipeline():
    junk, _ = is_junk("Tesla", mode="buyer")
    assert junk is False
    assert is_known_robotics_vendor_name("Tesla") is False


def test_vendor_oem_junk_match_includes_pattern_vendors():
    ok, reason = vendor_oem_junk_match("RoboCorp Automation")
    assert ok
    assert "vendor" in reason.lower()
