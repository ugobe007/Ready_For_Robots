"""Unit tests for JSON-LD trade show extraction (no network)."""

from app.services.trade_show_scraper import (
    extract_events_from_html,
    is_robot_focused_event,
    _source_key,
)


def test_extract_json_ld_event():
    html = """
    <html><head>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Event","name":"Automate 2030",
     "description":"Industrial robots and automation trade show floor",
     "startDate":"2030-05-05","endDate":"2030-05-08","url":"https://example.com/automate"}
    </script>
    </head><body></body></html>
    """
    evs = extract_events_from_html(html)
    assert len(evs) == 1
    assert is_robot_focused_event(evs[0])
    assert evs[0]["name"] == "Automate 2030"


def test_reject_non_robot_event():
    html = """
    <script type="application/ld+json">
    {"@type":"Event","name":"Annual Flower Festival","description":"Roses and tulips only"}
    </script>
    """
    evs = extract_events_from_html(html)
    assert len(evs) == 1
    assert not is_robot_focused_event(evs[0])


def test_source_key_stable():
    a = _source_key("the_robot_guild", "Foo Expo", None, "https://x")
    b = _source_key("the_robot_guild", "Foo Expo", None, "https://x")
    assert a == b
    assert a != _source_key("other", "Foo Expo", None, "https://x")
