"""Cal inline email demo GIF."""
from pathlib import Path

from app.services.cal_email_demo import (
    build_cal_demo_html,
    cal_demo_enabled,
    cal_demo_gif_bytes,
    enrich_cal_email_with_demo,
)


def test_cal_demo_gif_exists():
    gif = Path(__file__).resolve().parents[1] / "readyforrobots-new/client/public/marketing/cal-pipeline-demo.gif"
    assert gif.is_file(), "Run scripts/build_cal_demo_gif.py to generate the asset"
    assert len(cal_demo_gif_bytes()) > 1000


def test_enrich_cal_email_html_uses_hosted_gif_url():
    enriched = enrich_cal_email_with_demo("Hi,\n\nTest body.\n\n— Cal", use_cid=False)
    html = enriched.get("body_html") or ""
    assert "cal-pipeline-demo.gif" in html or "marketing/" in html
    assert "cid:cal-pipeline-demo" not in html
    assert "Cal · pipeline preview" in html
    assert 'width="280"' in html
    assert enriched.get("attachments") is None


def test_enrich_plaintext_demo_no_duplicate_url():
    enriched = enrich_cal_email_with_demo("Hi,\n\nTest body.\n\n— Cal")
    text = enriched.get("body_text") or ""
    assert "/preview" not in text
    assert text.strip().endswith("Cal") or "Test body" in text


def test_enrich_idempotent_strips_prior_demo_note():
    noisy = "Hi,\n\nBody.\n\n—\nCal pipeline preview (6-sec loop): https://readyforrobots.com/preview\n"
    enriched = enrich_cal_email_with_demo(noisy, use_cid=False)
    html = enriched.get("body_html") or ""
    assert html.count("cal-pipeline-demo") == 1
    assert html.count("<img") == 1


def test_enrich_html_demo_at_bottom():
    enriched = enrich_cal_email_with_demo("Hi,\n\nTest body.\n\n— Cal", use_cid=False)
    html = enriched.get("body_html") or ""
    # Letter content before demo table
    assert html.index("Test body") < html.index("Cal · pipeline preview")


def test_build_cal_demo_html_uses_https_url():
    block = build_cal_demo_html(img_src="https://readyforrobots.com/marketing/cal-pipeline-demo.gif")
    assert 'src="https://readyforrobots.com/marketing/cal-pipeline-demo.gif"' in block
    assert "View full preview" in block


def test_cal_demo_can_disable(monkeypatch):
    monkeypatch.setenv("CAL_EMAIL_DEMO_ENABLED", "0")
    enriched = enrich_cal_email_with_demo("Hi,\n\nBody")
    assert enriched.get("body_html") is None
