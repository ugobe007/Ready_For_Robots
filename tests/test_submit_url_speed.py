"""Submit-URL latency: parallel source fetches + deadline-capped timeouts."""
from __future__ import annotations

import threading
import time

from app.services.robot_profile_cache import (
    clear_profile_cache_memory,
    get_cached_profile,
    set_cached_profile,
)
from app.services.robot_understanding_v1.fetch import (
    DEFAULT_PAGE_TIMEOUT,
    FetchedPage,
    timeout_for_deadline,
)
from app.services.robot_understanding_v1.sources import collect_source_pack

_BODY = (
    "Acme Robotics builds the Hauler X1 autonomous mobile robot for warehouse "
    "totes, pallets, and factory transport. Payload 900 kg. Indoor navigation "
    "with lidar, tote handling, and pallet moves on factory floors. "
)


def _page(url: str, title: str = "Hauler X1") -> FetchedPage:
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=200,
        title=title,
        text=_BODY + title,
        html=f"<html><title>{title}</title><body>{_BODY}</body></html>",
        links=[],
    )


def _home_with_products(n: int = 6) -> FetchedPage:
    origin = "https://acme-robots.example"
    links = [(f"{origin}/products/hauler-{i}", f"Hauler {i}") for i in range(n)]
    return FetchedPage(
        url=f"{origin}/",
        final_url=f"{origin}/",
        status_code=200,
        title="Acme Robotics",
        text=_BODY,
        html="<html><title>Acme Robotics</title><body>Acme Robotics Hauler</body></html>",
        links=links,
    )


def test_timeout_for_deadline_caps_to_remaining_budget():
    deadline = time.monotonic() + 1.2
    t = timeout_for_deadline(deadline, default=(3.0, 12.0))
    assert t is not None
    assert sum(t) <= 1.25
    assert t[1] < 12.0


def test_timeout_for_deadline_none_when_budget_spent():
    assert timeout_for_deadline(time.monotonic() - 0.01, default=DEFAULT_PAGE_TIMEOUT) is None


def test_source_pack_fetches_candidate_pages_in_parallel(monkeypatch):
    lock = threading.Lock()
    active = {"n": 0, "max": 0}

    def fake_fetch(url, timeout=(2.5, 6.0), **kw):
        with lock:
            active["n"] += 1
            active["max"] = max(active["max"], active["n"])
        time.sleep(0.18)
        with lock:
            active["n"] -= 1
        return _page(url)

    monkeypatch.setattr(
        "app.services.robot_understanding_v1.sources.fetch_page", fake_fetch
    )
    home = _home_with_products(6)
    t0 = time.monotonic()
    pack = collect_source_pack(home, max_sources=4)
    elapsed = time.monotonic() - t0
    assert len(pack) >= 3
    assert active["max"] >= 3
    # Sequential 4×180ms would be ~0.72s; overlap should finish well under that.
    assert elapsed < 0.55


def test_source_pack_does_not_overrun_deadline_on_slow_pages(monkeypatch):
    def fake_fetch(url, timeout=(2.5, 6.0), **kw):
        # Honor the caller-capped timeout instead of the old 12s read default.
        time.sleep(min(0.05, timeout[1] if timeout else 0.05))
        return _page(url)

    monkeypatch.setattr(
        "app.services.robot_understanding_v1.sources.fetch_page", fake_fetch
    )
    home = _home_with_products(8)
    deadline = time.monotonic() + 0.35
    t0 = time.monotonic()
    collect_source_pack(home, max_sources=6, deadline_monotonic=deadline)
    elapsed = time.monotonic() - t0
    assert elapsed < 0.9


def test_cached_profile_aliases_selected_product():
    clear_profile_cache_memory()
    payload = {
        "company": {"name": "Agility Robotics"},
        "selected_product": {"name": "Digit"},
    }
    set_cached_profile("https://agilityrobotics.com/", None, payload)
    hit = get_cached_profile("https://www.agilityrobotics.com/", "Digit")
    assert hit is not None
    assert hit["selected_product"]["name"] == "Digit"
