"""Unknown /api paths must not look like an empty job board."""
from pathlib import Path

from app.spa_fallback import is_api_catchall_path

ROOT = Path(__file__).resolve().parents[1]


def test_preview_and_other_api_paths_are_catchall_api():
    assert is_api_catchall_path("api/robot-jobs/preview")
    assert is_api_catchall_path("/api/robot-jobs/preview?limit=3")
    assert is_api_catchall_path("api")
    assert is_api_catchall_path("/api/")


def test_jobs_pages_still_get_the_spa():
    assert not is_api_catchall_path("")
    assert not is_api_catchall_path("pipeline")
    assert not is_api_catchall_path("jobs/dexmate")
    assert not is_api_catchall_path("health")


def test_fly_spa_catchall_rejects_unknown_api():
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "from app.spa_fallback import is_api_catchall_path" in main
    assert "if is_api_catchall_path(full_path):" in main


def test_preview_endpoint_falls_back_to_named_employer_corpus():
    preview = (ROOT / "app" / "api" / "robot_jobs_preview.py").read_text(
        encoding="utf-8"
    )
    assert "def corpus_preview_jobs" in preview
    assert 'source = "corpus"' in preview
    assert "DECISION_MAKER_EMPTY" in preview
    assert "operations@" not in preview.split("def corpus_preview_jobs")[1][:800]
