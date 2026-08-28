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
    assert "find_drive" in critic_ids


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
    assert "isAbortError(err)" in submit
    catch = submit[submit.rindex("} catch (err)") :]
    abort_at = catch.index("isAbortError(err)")
    error_at = catch.index("setError")
    assert abort_at < error_at


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
