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


def test_find_jobs_cta_is_checkout_copy_not_live_lag():
    from scripts.agent_verify import FIND_JOBS_CTA, jobs_chrome_hits, repo_find_jobs_cta_ok

    assert FIND_JOBS_CTA == "Find jobs →"
    assert repo_find_jobs_cta_ok()
    workflow = Path("readyforrobots-new/client/src/lib/jobsWorkflow.ts").read_text(
        encoding="utf-8"
    )
    assert 'JOBS_APPLY_HERO_CTA = "Apply to jobs →"' in workflow
    live_lag = (
        f"{FIND_HEADLINE} {JOBS_ACTIVATE} Show us your robot Available jobs "
        "Start jobs →"
    )
    hits = jobs_chrome_hits(live_lag)
    assert hits["find_jobs_live"] is True
    assert hits["find_jobs_source"] is True
    assert all(hits.values()), hits
    stale_src = 'export const FIND_JOBS_CTA = "Start jobs →";\n'
    stale = jobs_chrome_hits(live_lag, source=stale_src)
    assert stale["find_jobs_source"] is False


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
