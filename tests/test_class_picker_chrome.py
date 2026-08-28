"""Class-picker chrome contract — source only, no app imports.

Agent-verify installs pytest only. Do not import robot_job_search here
(that pulls requests / Understanding). Compose coverage stays in
test_robot_class_qualify.py.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "readyforrobots-new" / "client" / "src" / "components" / "RobotJobsWorkspace.tsx"
WORKFLOW = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "jobsWorkflow.ts"


def test_class_picker_click_starts_search_not_crm():
    text = WORKSPACE.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    qualify = text[
        text.index("async function qualifyActive") : text.index("function revealJobs")
    ]
    go_activate = text[
        text.index("function goToActivate") : text.index("async function persistKeptJobs")
    ]
    assert "CLASS_PICKER_PROMPT" in text
    assert "What type of robot?" in workflow
    assert "What kind of robot is" not in text
    assert "kid of robot" not in text.lower()
    assert "fetchRobotJobSearch" in qualify
    assert "assertedClass: chosen" in qualify
    assert "qualifySearchLookupGrain" in qualify
    assert "needsClassChoice: false" in qualify
    assert "if (!a) return" not in qualify
    assert "fetchRobotJobMatch" not in qualify
    assert "shouldShowClassPicker(active)" in go_activate
    assert "classJobsEmptyCopy" in text
    assert "Finding jobs for that robot type" in text
    assert "classJobsEmptyCopy" in workflow
    assert "jobs for this robot yet" in workflow


def test_jobs_ui_never_renders_insufficient_evidence_copy():
    text = WORKSPACE.read_text(encoding="utf-8")
    banned = "we found _____, but we couldn't establish enough capability evidence to match it confidently"
    assert banned not in text.lower()
    assert "couldn't establish enough capability evidence" not in text.lower()
    assert "ClassPicker" in text
    assert "Name the robot class" in text
