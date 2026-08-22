from app.services.robot_job_extract import extract_robot_job, format_robot_job_signal
from app.services.robot_job_lifecycle import (
    should_close,
    status_from_evidence,
    status_from_posting_text,
)


def test_extracts_title_function_pay_and_specs():
    job = extract_robot_job(
        title="Warehouse Associate - Order Picker",
        description=(
            "Night shift order picker. $18–$22 an hour. Sign-on bonus $1,000. "
            "Lift 50 lbs. 45 cases per hour. 12 openings."
        ),
        company="Acme Fulfillment",
        locality="Memphis, TN",
    )
    assert job["job_function"] == "picking"
    assert job["compensation"]["wage_min"] == 18
    assert job["compensation"]["wage_max"] == 22
    assert job["compensation"]["signing_bonus"] == 1000
    assert job["performance_specs"]["throughput"]["count"] == 45
    assert job["performance_specs"]["payload"]["value"] == 50
    assert job["performance_specs"]["shift"] == "night shift"
    assert job["performance_specs"]["openings"] == 12
    assert "compensation" not in job["unknowns"]
    line = format_robot_job_signal(job)
    assert "ROBOT_JOB" in line
    assert "picking" in line


def test_unknown_when_pay_and_specs_absent():
    job = extract_robot_job(
        title="Warehouse Associate",
        description="Join our team in receiving.",
        company="Local DC",
    )
    assert job["compensation"]["wage_min"] is None
    assert "compensation" in job["unknowns"]
    assert "performance_specs" in job["unknowns"]


def test_closeout_filled_when_robot_does_this_work():
    ev = status_from_evidence(
        employer="GXO",
        job_title="Warehouse Associate - Tote Picker",
        job_function="picking",
        evidence_text=(
            "GXO deployed Digit humanoid robots that are now picking totes "
            "on the overnight shift."
        ),
    )
    assert ev["status"] == "filled_by_robot"
    assert should_close(ev["status"])


def test_closeout_withdrawn_without_inventing_a_robot():
    ev = status_from_posting_text("This job has expired. No longer accepting applications.")
    assert ev["status"] == "withdrawn"


def test_stays_open_without_robot_evidence():
    ev = status_from_evidence(
        employer="GXO",
        job_title="Order Picker",
        job_function="picking",
        evidence_text="GXO is hiring warehouse associates in Allentown this spring.",
    )
    assert ev["status"] == "open"
    assert not should_close(ev["status"])
