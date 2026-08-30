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
    assert job["employer_email"] is None


def test_jsonld_hiring_organization_email_is_persisted():
    from app.services.robot_job_extract import extract_job_contacts

    jsonld = {
        "@type": "JobPosting",
        "title": "Patient Transporter",
        "email": "ops@named-hospital.org",
        "hiringOrganization": {
            "@type": "Organization",
            "name": "Named Hospital",
            "email": "ops@named-hospital.org",
            "url": "https://named-hospital.org",
        },
        "url": "https://named-hospital.org/careers/transporter",
    }
    job = extract_robot_job(
        title="Patient Transporter",
        description="Hospital unit delivery. Immediate hire.",
        company="Named Hospital",
        locality="Portland, OR",
        jsonld=jsonld,
    )
    assert job["employer_email"] == "ops@named-hospital.org"
    assert job["contact_url"] == "https://named-hospital.org"
    assert job["apply_url"] == "https://named-hospital.org/careers/transporter"
    contacts = extract_job_contacts(jsonld=jsonld, employer="Named Hospital")
    assert contacts["employer_email"] == "ops@named-hospital.org"


def test_mailto_on_posting_html_is_kept():
    html = (
        '<a href="mailto:facilities@sunrise-orchards.com">Email hiring</a>'
        "<p>Harvest worker. Immediate hire.</p>"
    )
    job = extract_robot_job(
        title="Harvest Worker",
        description="Farm laborer harvest worker.",
        company="Sunrise Orchards",
        locality="Yakima, WA",
        html=html,
    )
    assert job["employer_email"] == "facilities@sunrise-orchards.com"


def test_indeed_board_mailbox_is_not_persisted():
    jsonld = {
        "@type": "JobPosting",
        "title": "Warehouse Associate",
        "hiringOrganization": {
            "name": "GXO Logistics",
            "email": "jobs@indeed.com",
        },
        "email": "noreply@indeed.com",
    }
    html = '<a href="mailto:noreply@indeed.com">Indeed</a>'
    job = extract_robot_job(
        title="Warehouse Associate",
        description="Night shift picker. Immediate hire.",
        company="GXO Logistics",
        locality="Allentown, PA",
        html=html,
        jsonld=jsonld,
    )
    assert job["employer_email"] is None
    assert job["job_title"] == "Warehouse Associate"
    assert job["employer"] == "GXO Logistics"


def test_does_not_invent_info_at_domain_from_employer_name():
    job = extract_robot_job(
        title="Order Picker",
        description="Night shift order picker. Immediate hire. Reach us at the warehouse.",
        company="Acme Fulfillment",
        locality="Memphis, TN",
    )
    assert job["employer_email"] is None
    assert job["contact_url"] is None
    assert "acme" not in str(job.get("employer_email") or "").lower()
    # Plain "info@acme.com" in copy is not mailto / JSON-LD — do not harvest a guess.
    guessed = extract_robot_job(
        title="Order Picker",
        description="Acme Fulfillment hiring. info@acme.com is not on this posting as mailto.",
        company="Acme Fulfillment",
        locality="Memphis, TN",
    )
    assert guessed["employer_email"] is None


def test_title_as_company_does_not_keep_a_mailbox():
    jsonld = {
        "@type": "JobPosting",
        "title": "Warehouse Associate",
        "hiringOrganization": {"name": "Warehouse Associate", "email": "hr@example.com"},
    }
    job = extract_robot_job(
        title="Warehouse Associate",
        description="Night shift. Immediate hire.",
        company="Warehouse Associate",
        jsonld=jsonld,
    )
    assert job["employer"] == "Warehouse Associate"
    assert job["employer_email"] is None


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


def test_harvest_and_cnc_titles_map_to_find_tape_families():
    from app.services.robot_job_extract import (
        is_job_employer_name,
        job_function_from_title,
        tape_family_for_job_function,
    )

    assert job_function_from_title("Harvest Worker - Orchard") == "harvest"
    assert tape_family_for_job_function("harvest") == "agriculture"
    assert job_function_from_title("CNC Machine Tender") == "machine_tending"
    assert tape_family_for_job_function("machine_tending") == "factory"
    assert job_function_from_title("Haul Truck Operator") == "haulage"
    assert tape_family_for_job_function("haulage") == "mining"
    assert is_job_employer_name("Sunrise Orchards") is True
    assert is_job_employer_name("Indeed") is False
    assert is_job_employer_name("Warehouse Associate", title="Warehouse Associate") is False
    assert is_job_employer_name("Confidential") is False


def test_janitor_custodian_are_cleaning_hospital_evs_stays_healthcare():
    from app.services.robot_job_extract import (
        job_function_from_title,
        tape_family_for_job_function,
    )

    assert job_function_from_title("Office Janitor") == "cleaning"
    assert tape_family_for_job_function("cleaning") == "scrub"
    assert job_function_from_title("Data Center Custodian") == "cleaning"
    assert job_function_from_title("Restroom Attendant") == "cleaning"
    assert job_function_from_title("Hospital EVS Technician") == "environmental_services"
    assert tape_family_for_job_function("environmental_services") == "disinfection"
    assert job_function_from_title("Hotel Housekeeper") == "housekeeping"
    assert tape_family_for_job_function("housekeeping") == "hospitality"
    assert job_function_from_title("Banquet Server") == "serving"
    assert tape_family_for_job_function("serving") == "serve"
    assert job_function_from_title("Food Runner / Busser") == "serving"
    assert job_function_from_title("Windows Server Administrator") != "serving"


def test_upsert_persists_email_when_contact_columns_exist(monkeypatch):
    from unittest.mock import MagicMock

    from app.services.robot_job_lifecycle import (
        reset_contact_column_cache,
        upsert_robot_job_from_extract,
    )

    reset_contact_column_cache()
    monkeypatch.setattr(
        "app.services.robot_job_lifecycle.robot_jobs_contact_columns_ready",
        lambda db: True,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.one_or_none.return_value = None
    extract = extract_robot_job(
        title="Patient Transporter",
        description="Hospital unit delivery.",
        company="Named Hospital",
        locality="Portland, OR",
        jsonld={
            "@type": "JobPosting",
            "title": "Patient Transporter",
            "hiringOrganization": {
                "name": "Named Hospital",
                "email": "ops@named-hospital.org",
            },
        },
    )
    row = upsert_robot_job_from_extract(db, company_id=None, extract=extract)
    assert row.employer_email == "ops@named-hospital.org"
    assert row.requirements["employer_email"] == "ops@named-hospital.org"


def test_upsert_keeps_job_when_email_missing(monkeypatch):
    from unittest.mock import MagicMock

    from app.services.robot_job_lifecycle import (
        reset_contact_column_cache,
        upsert_robot_job_from_extract,
    )

    reset_contact_column_cache()
    monkeypatch.setattr(
        "app.services.robot_job_lifecycle.robot_jobs_contact_columns_ready",
        lambda db: True,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.one_or_none.return_value = None
    extract = extract_robot_job(
        title="Harvest Worker",
        description="Farm laborer harvest worker. Immediate hire.",
        company="Sunrise Orchards",
        locality="Yakima, WA",
    )
    row = upsert_robot_job_from_extract(db, company_id=None, extract=extract)
    assert row is not None
    assert row.company_name == "Sunrise Orchards"
    assert row.employer_email is None
    assert not row.requirements.get("employer_email")
