"""Tests for exact buyer-name display fixes."""
from app.services.company_name_fixes import canonical_display_name


def test_cheese_renames_to_santori_cheese():
    assert canonical_display_name("Cheese") == "Santori Cheese"
    assert canonical_display_name("cheese") == "Santori Cheese"
    assert canonical_display_name("  CHEESE  ") == "Santori Cheese"


def test_real_names_unchanged():
    assert canonical_display_name("Santori Cheese") == "Santori Cheese"
    assert canonical_display_name("Accor Hotels") == "Accor Hotels"
    assert canonical_display_name("") == ""
    assert canonical_display_name(None) is None
