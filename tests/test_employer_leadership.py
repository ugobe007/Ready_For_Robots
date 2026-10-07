"""Employer leadership/team URL discovery and name extract. No invented people."""
from app.services.employer_leadership import (
    discover_leadership_urls,
    fetch_leadership_pages,
    origin_for_domain,
    people_from_html,
    people_from_pages,
)


def test_origin_skips_ats_and_junk():
    assert origin_for_domain("harrishealth.org") == "https://harrishealth.org"
    assert origin_for_domain("boards.greenhouse.io") is None
    assert origin_for_domain("") is None


def test_discover_leadership_urls_same_host_only():
    html = """
    <html><body>
      <a href="/leadership">Leadership</a>
      <a href="/careers">Careers</a>
      <a href="https://other.org/team">Other team</a>
      <a href="/about-us">About us</a>
    </body></html>
    """
    urls = discover_leadership_urls(html, "https://harrishealth.org")
    assert "https://harrishealth.org/leadership" in urls
    assert "https://harrishealth.org/about-us" in urls
    assert all("careers" not in u for u in urls)
    assert all("other.org" not in u for u in urls)


def test_people_from_html_reads_name_then_title():
    html = """
    <html><body>
      <h2>Priya Shah</h2>
      <p>Pharmacy Operations Manager</p>
      <p>About Us</p>
    </body></html>
    """
    people = people_from_html(html, "https://harrishealth.org/leadership")
    assert people[0]["name"] == "Priya Shah"
    assert "Pharmacy" in people[0]["title"]
    assert people[0]["source"] == "leadership_page"
    assert all(p["name"] != "About Us" for p in people)


def test_people_from_html_reads_json_ld_person():
    html = """
    <script type="application/ld+json">
    {"@type":"Person","name":"Maya Chen","jobTitle":"Director of Pharmacy"}
    </script>
    """
    people = people_from_html(html, "https://harrishealth.org/team")
    assert people[0]["name"] == "Maya Chen"
    assert people[0]["title"] == "Director of Pharmacy"


def test_fetch_leadership_pages_uses_injected_getter():
    pages_html = {
        "https://geodis.com": '<a href="/leadership">Leadership</a>',
        "https://geodis.com/leadership": "<h2>Alex Rivera</h2><p>Site Operations Manager</p>",
    }

    def get_html(url):
        return pages_html.get(url.rstrip("/")) or pages_html.get(url)

    pages = fetch_leadership_pages(domain="geodis.com", employer="GEODIS", get_html=get_html)
    urls = [p["url"] for p in pages]
    assert "https://geodis.com/leadership" in urls
    people = people_from_pages(pages)
    assert people[0]["name"] == "Alex Rivera"
    assert "Operations Manager" in people[0]["title"]


def test_http_get_rejects_ssrf_targets():
    """SSRF protection: _http_get must reject localhost and metadata endpoints."""
    from app.services.employer_leadership import _http_get

    assert _http_get("http://localhost/team") is None
    assert _http_get("http://127.0.0.1/leadership") is None
    assert _http_get("http://169.254.169.254/latest/meta-data") is None
    assert _http_get("http://metadata.google.internal/") is None


def test_fetch_leadership_pages_caps_failed_attempts():
    """Performance: failed/timeout requests count toward _MAX_ATTEMPTS to prevent stalls."""
    from app.services.employer_leadership import _MAX_ATTEMPTS

    call_count = 0

    def slow_getter(url):
        nonlocal call_count
        call_count += 1
        return None  # Always fail

    pages = fetch_leadership_pages(domain="example.com", get_html=slow_getter)
    assert pages == []
    assert call_count <= _MAX_ATTEMPTS  # Should stop at the attempts limit
