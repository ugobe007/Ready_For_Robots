from scripts.harness_compile_memory import pick_next_mission
from scripts.harness_vercel_truth import (
    classify_frontend_deploy_run,
    vercel_production_is_a_lie,
)


def test_skip_green_under_30s():
    label = classify_frontend_deploy_run(conclusion="success", duration_seconds=7)
    assert label == "skipped_missing_secrets"
    assert vercel_production_is_a_lie(label)


def test_real_success_is_not_a_lie():
    label = classify_frontend_deploy_run(conclusion="success", duration_seconds=180)
    assert label == "shipped_or_long_enough"
    assert not vercel_production_is_a_lie(label)


def test_failed_run_keeps_conclusion():
    assert classify_frontend_deploy_run(conclusion="failure", duration_seconds=5) == "failure"


def test_next_mission_is_vercel_when_lie():
    nxt = pick_next_mission(
        vercel={"lie": True, "label": "skipped_missing_secrets"},
        followups=["header Pipeline leftover"],
    )
    assert nxt["slug"] == "vercel-production-cli-secrets"
    assert "VERCEL_TOKEN" in nxt["why"]


def test_next_mission_uses_followup_when_deploy_honest():
    nxt = pick_next_mission(
        vercel={"lie": False, "label": "shipped_or_long_enough"},
        followups=["Smoke FIND to CRM on production."],
    )
    assert nxt["slug"] == "jobs-path-followup"
    assert "FIND" in nxt["why"]
