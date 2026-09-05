"""Catalog includes requested OEM vendors with product URLs."""
from app.services.humanoid_vendor_catalog import catalog_entries

VENDOR_URLS = {
    "dexmate-vega": "https://www.dexmate.ai/product/vega",
    "eden-robotics": "https://edenrobotics.ai",
    "astribot-s1": "https://www.astribot.com/en",
    "limx-tron1": "https://www.limxdynamics.com/en",
    "limx-luna": "https://www.limxdynamics.com/en",
    "matrix-3": "https://matrixrobotics.ai",
    "kepler-k2": "https://www.gotokepler.com/home",
    "booster-t1": "https://booster.tech",
    "persona-ai-gen1": "https://persona.ai",
    "noble-machines": "https://www.noblemachines.ai",
    "fourier-gr1": "https://www.fftai.com/products-gr1",
    "fourier-gr2": "https://www.fftai.com/products-gr2",
    "fourier-gr3": "https://www.fftai.com/products-gr3series",
    "fourier-gr3c": "https://www.fftai.com/products-gr3series",
    "deep-robotics-dr02": "https://www.deeprobotics.cn/en/index/dr02.html",
    "robotera-star1": "https://www.robotera.com",
    "sanctuary-phoenix": "https://www.sanctuary.ai",
}


def test_requested_vendors_in_catalog():
    by_slug = {e["model_slug"]: e for e in catalog_entries()}
    for slug, url in VENDOR_URLS.items():
        assert slug in by_slug, f"missing {slug}"
        assert by_slug[slug]["product_url"] == url


def test_dexmate_and_eden_have_baseline_specs():
    by_slug = {e["model_slug"]: e for e in catalog_entries()}
    assert by_slug["dexmate-vega"]["specs"]["payload_kg"] == 7.0
    assert by_slug["eden-robotics"]["specs"]["has_sdk"] is True
    assert by_slug["noble-machines"]["specs"]["payload_kg"] == 23.0


def test_limx_multiple_models():
    slugs = {e["model_slug"] for e in catalog_entries() if e["vendor"] == "LimX Dynamics"}
    assert {"limx-tron1", "limx-luna", "limx-oli", "limx-tron2"}.issubset(slugs)


def test_fourier_gr3_baseline_specs():
    by_slug = {e["model_slug"]: e for e in catalog_entries()}
    gr3 = by_slug["fourier-gr3"]
    assert gr3["vendor"] == "Fourier Robotics"
    assert gr3["specs"]["height_cm"] == 165
    assert gr3["specs"]["hot_swap_battery"] is True
    assert gr3["specs"]["has_sdk"] is True


def test_fourier_gr3c_and_deep_dr02_in_catalog():
    by_slug = {e["model_slug"]: e for e in catalog_entries()}
    assert by_slug["fourier-gr3c"]["name"] == "Fourier GR-3C Cosmo"
    assert by_slug["deep-robotics-dr02"]["status"] == "pilot"
    assert by_slug["robotera-star2"]["product_url"] == "https://www.robotera.com"
