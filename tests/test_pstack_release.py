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
    assert "find_drive" in critic_ids


def test_post_json_retries_transient_503(monkeypatch):
    from scripts import pstack_release as ps

    calls = {"n": 0}

    def fake_once(url, payload, *, timeout):
        calls["n"] += 1
        if calls["n"] < 3:
            return 503, {"_raw": ""}
        return 200, {"state": "matches", "company_name": "Dexmate"}

    monkeypatch.setattr(ps, "_post_json_once", fake_once)
    monkeypatch.setenv("PSTACK_HTTP_RETRIES", "6")
    monkeypatch.setenv("PSTACK_HTTP_RETRY_SLEEP", "0")
    code, body = ps._post_json("https://example.test/api/robot-job-search", {"url": "https://www.dexmate.ai/"})
    assert code == 200
    assert body["state"] == "matches"
    assert calls["n"] == 3


def test_find_tile_pr_must_not_skip_live_critic():
    """Serving/Cleaning FIND tiles are not a scrape-only PR — live critic must run."""
    tile_files = (
        "readyforrobots-new/client/src/lib/robotClassOptions.ts",
        "readyforrobots-new/client/src/lib/jobsWorkflow.ts",
        "app/services/robot_class_qualify.py",
        "ontology/industry_work_language.v1.json",
        "scripts/pstack_release.py",
    )
    scrape_only = {
        "app/services/robot_job_extract.py",
        "app/services/job_board_scraper_runner.py",
        "tests/test_job_board_scraper_pipeline.py",
        "tests/test_robot_job_extract.py",
        "fly.toml",
    }
    assert not all(path in scrape_only or path.startswith("app/scrapers/") for path in tile_files)
    src = (ROOT / "scripts" / "pstack_release.py").read_text(encoding="utf-8")
    assert "wait_for_fly_health" in src
    assert "TRANSIENT_HTTP" in src
    assert 'if local:' in src
    assert "scrape-only PR" not in src


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
