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


def test_pstack_release_script_exists():
    from scripts.pstack_release import run_pstack_release

    result = run_pstack_release(local=True)
    assert result["ok"], result
    assert result["chrome_required"] is False


def test_automerge_dispatches_prod_deploys_after_github_token_squash():
    """GITHUB_TOKEN squash-merge does not fire push workflows. Dispatch must."""
    verify = Path(".github/workflows/agent-verify.yml").read_text(encoding="utf-8")
    deploy = Path(".github/workflows/deploy.yml").read_text(encoding="utf-8")
    frontend = Path(".github/workflows/deploy-frontend.yml").read_text(encoding="utf-8")
    assert "createWorkflowDispatch" in verify
    assert "actions: write" in verify
    assert "deploy.yml" in verify
    assert "deploy-frontend.yml" in verify
    assert "workflow_dispatch:" in deploy
    assert "ssh console" in deploy
    assert "jruc0a1b2c3d4" in deploy
    assert "workflow_dispatch:" in frontend
