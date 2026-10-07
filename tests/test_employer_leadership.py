"""Employer leadership/team URL discovery and name extract. No invented people."""
from app.services.employer_leadership import (
    discover_leadership_urls,
    fetch_leadership_pages,
    origin_for_domain,
    origins_for_domain,
    people_from_html,
    people_from_pages,
    ranked_leadership_urls,
)


def test_origin_skips_ats_and_junk():
    assert origin_for_domain("harrishealth.org") == "https://harrishealth.org"
    assert origins_for_domain("harrishealth.org") == [
        "https://www.harrishealth.org",
        "https://harrishealth.org",
    ]
    assert origin_for_domain("boards.greenhouse.io") is None
    assert origin_for_domain("") is None
    assert origin_for_domain("127.0.0.1") is None
    assert origin_for_domain("169.254.169.254") is None
    assert origin_for_domain("10.0.0.8") is None
    assert origin_for_domain("localhost") is None
    assert origin_for_domain("metadata.google.internal") is None


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
    assert all("careers" not in u for u in urls)
    assert all("other.org" not in u for u in urls)


def test_ranked_urls_prefer_nested_leadership_over_about_us():
    html = """
    <html><body>
      <a href="/about-us-hh/board/Pages/default.aspx">Board of Trustees</a>
      <a href="/about-us/harris-health">About Harris Health</a>
    </body></html>
    """
    urls = ranked_leadership_urls("https://harrishealth.org", html)
    nested = "https://harrishealth.org/about-us-hh/leadership"
    assert nested in urls
    assert urls[0] == nested
    generic = "https://harrishealth.org/leadership"
    if generic in urls:
        assert urls.index(nested) < urls.index(generic)


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


def test_people_from_html_reads_credentials_and_rejects_title_as_name():
    html = """
    <html><body>
      <p>Esmaeil Porsa, MD, MBA, MPH, CCHP-A</p>
      <p>President and Chief Executive Officer</p>
      <p>Louis G. Smith Jr., MHA</p>
      <p>Sr. Executive Vice President and Chief Operating Officer</p>
      <p>Chief Medical Executive</p>
    </body></html>
    """
    people = people_from_html(html, "https://harrishealth.org/about-us-hh/leadership")
    names = [p["name"] for p in people]
    assert "Esmaeil Porsa" in names
    assert "Louis Smith" in names
    assert "Chief Medical" not in names
    coo = next(p for p in people if p["name"] == "Louis Smith")
    assert "Operating" in coo["title"]


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


def test_fetch_skips_empty_shells_to_reach_nested_page():
    nested = (
        "<h2>Esmaeil Porsa, MD, MBA</h2>"
        "<p>President and Chief Executive Officer</p>"
        "<h2>Louis G. Smith Jr., MHA</h2>"
        "<p>Sr. Executive Vice President and Chief Operating Officer</p>"
    )
    shell = "<html><title>Leadership</title><body>" + ("nav " * 4000) + "</body></html>"
    pages_html = {
        "https://harrishealth.org": (
            '<a href="/about-us-hh/board/Pages/default.aspx">Board of Trustees</a>'
        ),
        "https://harrishealth.org/leadership": shell,
        "https://harrishealth.org/leadership-team": shell,
        "https://harrishealth.org/our-leadership": shell,
        "https://harrishealth.org/about-us-hh/leadership": nested,
    }

    def get_html(url):
        return pages_html.get(url.rstrip("/")) or pages_html.get(url)

    pages = fetch_leadership_pages(
        domain="harrishealth.org", employer="Harris Health", get_html=get_html
    )
    urls = [p["url"] for p in pages]
    assert "https://harrishealth.org/about-us-hh/leadership" in urls
    assert "https://harrishealth.org/leadership" not in urls
    names = [p["name"] for p in people_from_pages(pages)]
    assert "Esmaeil Porsa" in names
    assert "Louis Smith" in names


def test_fetch_uses_www_when_apex_drops_path():
    nested = (
        "<h2>Esmaeil Porsa, MD, MBA</h2>"
        "<p>President and Chief Executive Officer</p>"
    )
    home = '<a href="/about-us-hh/board">Board of Trustees</a>'

    def get_html(url):
        if url.startswith("https://harrishealth.org"):
            return None
        if url.rstrip("/") == "https://www.harrishealth.org":
            return home
        if url.rstrip("/") == "https://www.harrishealth.org/about-us-hh/leadership":
            return nested
        return None

    pages = fetch_leadership_pages(
        domain="harrishealth.org", employer="Harris Health", get_html=get_html
    )
    assert pages
    assert pages[0]["url"] == "https://www.harrishealth.org/about-us-hh/leadership"
    assert people_from_pages(pages)[0]["name"] == "Esmaeil Porsa"


def test_http_get_does_not_request_unsafe_urls(monkeypatch):
    from app.services import employer_leadership as el
    from app.services.robot_url_safety import UrlSafetyError

    def boom(url):
        raise UrlSafetyError("blocked")

    monkeypatch.setattr(el, "assert_public_http_url", boom)
    called = []
    monkeypatch.setattr(
        el.requests, "get", lambda *a, **k: called.append((a, k)) or None
    )
    assert el._http_get("https://127.0.0.1/leadership") is None
    assert called == []


def test_fetch_stops_after_first_named_page():
    calls: list[str] = []
    home = '<a href="/about-us-hh/board">Board</a>'
    nested = (
        "<h2>Esmaeil Porsa, MD</h2><p>President and Chief Executive Officer</p>"
    )

    def get_html(url):
        calls.append(url)
        if url.rstrip("/") == "https://www.harrishealth.org":
            return home
        if "leadership" in url:
            return nested
        return "<html><body>nav</body></html>"

    pages = fetch_leadership_pages(
        domain="harrishealth.org", employer="Harris Health", get_html=get_html
    )
    assert people_from_pages(pages)[0]["name"] == "Esmaeil Porsa"
    assert len(calls) <= 4
    assert sum(1 for u in calls if "leadership" in u) == 1
