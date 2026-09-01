"""pstack How / Act / Critic release gate."""
from pathlib import Path

from app.services.pstack_protocol import critic_gate_ids
from scripts.pstack_release import (
    GREENFIELD,
    phase_act,
    phase_how,
    run_pstack_release,
)

ROOT = Path(__file__).resolve().parents[1]


def test_how_and_act_pass_on_this_tree():
    how = phase_how()
    act = phase_act()
    assert how["ok"], how
    assert act["ok"], act
    ids = {c["id"] for c in how["checks"]} | {c["id"] for c in act["checks"]}
    assert "chrome_not_gate" in ids
    assert "silent_abort" in ids
    assert "bind_url" in ids
    assert "cal_jobs_desk" in ids
    assert "crm_first_cta" in ids


def test_local_release_skips_fly_drive():
    result = run_pstack_release(local=True)
    assert result["ok"], result
    assert result["chrome_required"] is False
    assert result["authority"] == "release_gate"
    critic_ids = [c["id"] for c in result["critic"]["checks"]]
    assert "find_abort" in critic_ids
    assert "crm_leftover" in critic_ids
    assert "oem_extract" in critic_ids
    assert "class_picker" in critic_ids
    assert "healthcare_class" in critic_ids
    assert "healthcare_class:live" in critic_ids
    assert "ontology_industry_language" in critic_ids
    assert "url_workflow" in critic_ids
    assert "find_drive" in critic_ids


PR_194_FILES = [
    "app/scrapers/job_board_scraper_enhanced.py",
    "app/scrapers/scrape_targets.py",
    "app/services/robot_job_extract.py",
    "fly.toml",
    "scripts/pstack_release.py",
    "tests/test_job_board_scraper_pipeline.py",
    "tests/test_pstack_release.py",
    "tests/test_robot_job_extract.py",
]


def test_scrape_only_paths_skip_live_find():
    from scripts.pstack_release import path_is_scrape_only, paths_are_scrape_only

    assert path_is_scrape_only("app/scrapers/scrape_targets.py")
    assert path_is_scrape_only("fly.toml")
    assert path_is_scrape_only("app/services/robot_job_extract.py")
    assert not path_is_scrape_only("readyforrobots-new/client/src/lib/jobsWorkflow.ts")
    assert not path_is_scrape_only("ontology/industry_work_language.v1.json")
    assert paths_are_scrape_only(
        [
            "app/scrapers/scrape_targets.py",
            "app/scrapers/job_board_scraper_enhanced.py",
            "app/services/robot_job_extract.py",
            "tests/test_job_board_scraper_pipeline.py",
            "tests/test_robot_job_extract.py",
            "fly.toml",
        ]
    )
    assert not paths_are_scrape_only(
        ["app/scrapers/scrape_targets.py", "readyforrobots-new/client/src/lib/jobsWorkflow.ts"]
    )
    # Gate-script edits on a scrape PR are not scrape-only — that is why CI still
    # drove Dexmate after 149d2775.
    assert not paths_are_scrape_only(PR_194_FILES)


def test_scrape_plus_pstack_harness_skips_live_find():
    from scripts.pstack_release import skip_live_find_drives

    skip, reason = skip_live_find_drives(PR_194_FILES)
    assert skip, reason
    assert "FIND" in reason


def test_find_ui_diff_still_runs_live_find():
    from scripts.pstack_release import skip_live_find_drives

    skip, _reason = skip_live_find_drives(
        ["readyforrobots-new/client/src/lib/jobsWorkflow.ts", "scripts/pstack_release.py"]
    )
    assert not skip


def test_empty_ci_file_list_skips_live_find(monkeypatch):
    from scripts.pstack_release import skip_live_find_drives

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    skip, reason = skip_live_find_drives([])
    assert skip, reason


def test_critic_skips_fly_on_scrape_pr_file_list(monkeypatch):
    from scripts import pstack_release as ps

    monkeypatch.setattr(ps, "pr_changed_files", lambda: list(PR_194_FILES))

    def boom(*_a, **_k):
        raise AssertionError("live FIND must not run on scrape + pstack-harness diffs")

    monkeypatch.setattr(ps, "drive_find_url", boom)
    monkeypatch.setattr(ps, "drive_diligent_healthcare", boom)
    critic = ps.phase_critic(api="https://ready-2-robot.fly.dev", local=False)
    assert critic["ok"], critic
    ids = {c["id"]: c for c in critic["checks"]}
    assert ids["find_drive"]["ok"]
    assert ids["healthcare_class:live"]["ok"]
    assert ids["ontology_industry_language"]["ok"]
    assert ids["url_workflow"]["ok"]


def test_critic_gates_include_abort_and_leftover():
    assert critic_gate_ids() == [
        "find",
        "find_abort",
        "find_identity",
        "crm_leftover",
        "job_cards",
        "wall",
        "matcher",
        "oem_extract",
        "class_picker",
        "healthcare_class",
        "ontology_industry_language",
        "url_workflow",
    ]


def test_173_abort_contract_is_in_identity_module():
    identity = (ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "robotUrlIdentity.ts").read_text()
    assert "export function isSilentFindError" in identity
    assert "failed to fetch" in identity.lower()
    assert "export function findUserFacingError" in identity
    workspace = (
        ROOT / "readyforrobots-new" / "client" / "src" / "components" / "RobotJobsWorkspace.tsx"
    ).read_text()
    submit = workspace[
        workspace.index("async function submitFind") : workspace.index(
            "async function confirmSelection"
        )
    ]
    assert "bindSubmittedRobot(submitUrl)" in submit
    assert "shouldIgnoreStaleFindError" in submit
    assert "isAbortError(err, ac.signal)" in submit
    catch = submit[submit.rindex("} catch (err)") :]
    abort_at = catch.index("isAbortError")
    fail_at = catch.index("lookupFailedMessage")
    error_at = catch.index("setError")
    assert abort_at < error_at
    assert abort_at < fail_at
    assert "FIND_RESEARCH_INTERRUPTED_MESSAGE" in catch


def test_172_strawberry_leftover_fixture_exists():
    release = (
        ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "pstackRelease.ts"
    ).read_text()
    assert "CRM_LEFTOVER_FIXTURE" in release
    assert "strawberry robot" in release
    assert GREENFIELD in release
    crm = (
        ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "jobsCrmAccount.test.ts"
    ).read_text()
    assert "does not keep strawberry identity after a Greenfield FIND" in crm


def test_crm_desk_has_no_protocol_chrome():
    desk = (
        ROOT / "readyforrobots-new" / "client" / "src" / "components" / "JobsCrmDesk.tsx"
    ).read_text()
    assert "JobsPstackProtocol" not in desk
    readme = (ROOT / "pstack" / "README.md").read_text()
    assert "release gate" in readme.lower()
    assert "JOBS AGENT PROTOCOL" in readme


def test_healthcare_class_fixture_fails_if_diligent_is_humanoid():
    from scripts.pstack_release import DILIGENT, healthcare_class_fixture

    ok, detail = healthcare_class_fixture()
    assert ok, detail
    seed = (ROOT / "app" / "data" / "vendor_robots_oem_sku_seed.json").read_text()
    assert "diligentrobots.com" in seed
    assert '"primary_class": "healthcare"' in seed
    assert DILIGENT in (ROOT / "pstack" / "release.yaml").read_text()


def test_rfr_release_meta_moves_with_git_not_frozen_handoff_id():
    html = (ROOT / "readyforrobots-new" / "client" / "index.html").read_text()
    assert 'name="rfr-release"' in html
    assert "jobs-handoff-42087c03" not in html
    vite = (ROOT / "readyforrobots-new" / "vite.config.ts").read_text()
    assert "injectRfrReleaseMeta" in vite
    assert "rfrReleaseId" in vite
