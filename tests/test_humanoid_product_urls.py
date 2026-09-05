"""Curated humanoid product URLs should point at live manufacturer pages."""
from app.services.humanoid_vendor_catalog import catalog_entries

CORRECTED_URLS = {
    "tesla-optimus-gen2": "https://www.tesla.com/AI",
    "agility-digit": "https://www.agilityrobotics.com/solutions",
    "ubtech-walker-x": "https://www.ubtrobot.com/en/",
    "ubtech-walker-s": "https://www.ubtrobot.com/en/",
    "mentee-bot": "https://www.menteebot.com",
}


def test_corrected_product_urls_in_catalog():
    by_slug = {e["model_slug"]: e for e in catalog_entries()}
    for slug, url in CORRECTED_URLS.items():
        assert by_slug[slug]["product_url"] == url
