"""URL workflow critic: range / products / capabilities.

Does not import fetch/facts (agent-verify pytest-only venv has no requests).
"""
from __future__ import annotations

from app.services.url_workflow_critic import (
    BREAK_CHROME,
    BREAK_COMPANY_CLASS,
    BREAK_DRONE_SCRUB,
    BREAK_MIXED_FLAT,
    CORPUS_PATH,
    apply_heuristic_breaks,
    critique_url,
    load_corpus,
    run_fixture_suite,
    snapshot_from_rows,
)


def test_fixture_suite_detects_each_break_class_and_healthy_pass():
    suite = run_fixture_suite()
    by = {c["id"]: c for c in suite["cases"]}
    assert suite["ok"], suite
    assert BREAK_MIXED_FLAT in by[BREAK_MIXED_FLAT]["got_kinds"]
    assert BREAK_CHROME in by[BREAK_CHROME]["got_kinds"]
    assert BREAK_DRONE_SCRUB in by[BREAK_DRONE_SCRUB]["got_kinds"]
    assert BREAK_COMPANY_CLASS in by[BREAK_COMPANY_CLASS]["got_kinds"]
    assert by["healthy_mixed"]["ok"] is True
    assert by["healthy_drone"]["ok"] is True
    sherpa = next(
        p for p in by["healthy_drone"]["products"] if p["name"] == "Sherpa Drone"
    )
    assert sherpa["display_class"] == "cleaning_drone"
    assert "hard_floor_scrub" not in sherpa["capabilities_present"]


def test_mixed_range_flattened_break():
    raw = snapshot_from_rows(
        "https://example/flat",
        vendor_name="OEM",
        rows=[
            {"name": "BellaBot", "description": "waiter", "force_class": "service_robot"},
            {"name": "CC1", "description": "scrubber", "force_class": "service_robot"},
        ],
    )
    critique = apply_heuristic_breaks(raw)
    kinds = {b.kind for b in critique.breaks}
    assert BREAK_MIXED_FLAT in kinds or BREAK_COMPANY_CLASS in kinds


def test_chrome_as_sku_break():
    raw = snapshot_from_rows(
        "https://example/chrome",
        vendor_name="OEM",
        rows=[{"name": "About", "description": "About nav", "force_class": None}],
    )
    critique = apply_heuristic_breaks(raw)
    assert any(b.kind == BREAK_CHROME for b in critique.breaks)


def test_cleaning_drone_as_scrubber_break():
    raw = snapshot_from_rows(
        "https://example/drone",
        vendor_name="Lucid",
        rows=[
            {
                "name": "Sherpa Drone",
                "description": "Window washing drone for facades and exteriors.",
                "force_class": "autonomous_scrubber",
            }
        ],
    )
    critique = apply_heuristic_breaks(raw)
    assert any(b.kind == BREAK_DRONE_SCRUB for b in critique.breaks)


def test_company_class_not_product_class_break():
    from app.services.url_workflow_critic import apply_corpus_breaks

    raw = snapshot_from_rows(
        "https://example/company",
        vendor_name="Pudu",
        rows=[
            {
                "name": "BellaBot",
                "description": "Tray delivery waiter.",
                "force_class": "serving",
            },
            {
                "name": "CC1",
                "description": "Tray delivery waiter.",
                "force_class": "serving",
            },
        ],
    )
    critique = apply_corpus_breaks(
        apply_heuristic_breaks(raw),
        {"distinct_class_pairs": [["BellaBot", "CC1"]]},
    )
    assert any(b.kind == BREAK_COMPANY_CLASS for b in critique.breaks)


def test_corpus_file_lists_operator_urls():
    data = load_corpus()
    urls = [str(r["url"]) for r in data["urls"]]
    for host in (
        "pringlerobotics.ai",
        "keenon.com",
        "pudurobotics.com",
        "bearrobotics.ai",
        "lucidbots.com",
        "kaercher.com",
        "tennantco.com",
        "ubtrobot.com",
        "agibot.com",
        "magiclab.top",
        "deeprobotics.cn",
    ):
        assert any(host in u for u in urls), host
    assert CORPUS_PATH.is_file()


def test_critic_does_not_import_fetch():
    import app.services.url_workflow_critic as mod
    import inspect

    src = inspect.getsource(mod)
    assert "robot_understanding_v1.fetch" not in src
    assert "robot_understanding_v1.facts" not in src
    assert "import requests" not in src


def test_listing_path_keyed_to_submitted_url():
    a = critique_url("https://www.pudurobotics.com/en")
    b = critique_url("https://www.keenon.com/en")
    assert a.url != b.url
    if a.vendor_name and b.vendor_name:
        assert a.vendor_name != b.vendor_name
