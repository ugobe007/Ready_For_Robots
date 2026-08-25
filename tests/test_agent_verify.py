"""Agent verification helpers — feature map shape and doctor payload."""
from pathlib import Path

from scripts.agent_verify import feature_map_ok, FIND_HEADLINE, JOBS_ACTIVATE, STALE_JS


def test_feature_map_files_have_required_headings():
    errs = feature_map_ok()
    assert errs == [], errs


def test_docs_feature_map_names_chrome():
    text = Path("docs/feature_map.md").read_text(encoding="utf-8")
    for needle in (
        "Jobs header",
        "Process bar",
        "Job Card",
        "jobs_activate",
        "Pipeline",
        "FIND",
    ):
        assert needle in text


def test_canaries_are_jobs_not_signal():
    assert "Find jobs" in FIND_HEADLINE
    assert JOBS_ACTIVATE == "jobs_activate"
    assert STALE_JS.startswith("/assets/index-")
