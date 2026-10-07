"""Job-title decision-maker agent — correlate work with the right people."""
from app.services.job_decision_maker_agent import (
    pick_candidate,
    plan_for_job,
    score_candidate,
)


def test_pharmacy_cart_job_looks_for_pharmacy_titles():
    plan = plan_for_job(
        {
            "action": "delivery",
            "robot_compatible_task": "Deliver medication carts",
            "observed_workflow": "Move filled carts from pharmacy to nursing units",
            "locality": "Rochester, NY",
        }
    )
    assert plan.function == "pharmacy"
    assert "Director of Pharmacy" in plan.titles
    assert "Pharmacy Operations Manager" in plan.titles


def test_floor_scrub_looks_for_evs_not_security():
    plan = plan_for_job(
        {
            "action": "scrub",
            "robot_compatible_task": "Overnight scrub of mall common-area hard floors",
            "locality": "Bloomington, MN",
        }
    )
    assert plan.function == "environmental_services"
    assert any("EVS" in t or "Facilities" in t for t in plan.titles)


def test_agent_picks_pharmacy_ops_over_cdo():
    plan = plan_for_job(
        {
            "action": "delivery",
            "robot_compatible_task": "Pharmacy delivery",
            "observed_workflow": "Move filled carts from pharmacy to nursing units",
        }
    )
    picked = pick_candidate(
        plan,
        [
            {
                "email": "kelli@harrishealth.org",
                "name": "Kelli Fondren",
                "title": "Chief Development Officer",
                "confidence": 99,
            },
            {
                "email": "priya@harrishealth.org",
                "name": "Priya Shah",
                "title": "Pharmacy Operations Manager",
                "confidence": 80,
            },
        ],
        locality="Houston, TX",
    )
    assert picked is not None
    assert picked["email"] == "priya@harrishealth.org"
    assert "pharmacy" in (picked.get("match_why") or "").lower()


def test_agent_rejects_security_for_floor_scrub():
    plan = plan_for_job(
        {
            "action": "scrub",
            "robot_compatible_task": "Overnight terminal floor scrubbing",
        }
    )
    picked = pick_candidate(
        plan,
        [
            {
                "email": "rob@mallofamerica.com",
                "name": "Robert Swanson",
                "title": "Security Operations",
                "confidence": 95,
            }
        ],
        locality="Bloomington, MN",
    )
    assert picked is None
    assert score_candidate(
        plan,
        {"title": "Director of Environmental Services", "email": "evs@mall.com"},
    )


def test_same_employer_two_jobs_pick_different_people():
    people = [
        {
            "email": "evs@hospital.org",
            "name": "Dana Evens",
            "title": "Director of EVS",
            "confidence": 90,
        },
        {
            "email": "pharm@hospital.org",
            "name": "Maya Chen",
            "title": "Director of Pharmacy",
            "confidence": 90,
        },
        {
            "email": "cdo@hospital.org",
            "name": "Kelli Fondren",
            "title": "Chief Development Officer",
            "confidence": 99,
        },
    ]
    pharmacy = pick_candidate(
        plan_for_job(
            {
                "action": "delivery",
                "robot_compatible_task": "Pharmacy cart loop",
                "company_name": "Harris Health",
            }
        ),
        people,
    )
    evs = pick_candidate(
        plan_for_job(
            {
                "action": "scrub",
                "robot_compatible_task": "Night EVS hard-floor scrub routes",
                "company_name": "Harris Health",
            }
        ),
        people,
    )
    assert pharmacy["email"] == "pharm@hospital.org"
    assert evs["email"] == "evs@hospital.org"


def test_cnc_job_looks_for_plant_titles():
    plan = plan_for_job(
        {
            "action": "assembly",
            "robot_compatible_task": "Load parts into CNC",
            "locality": "Tualatin, OR",
        }
    )
    assert plan.function == "machine_tending"
    assert "Plant Manager" in plan.titles


def test_stored_lifecycle_function_is_the_plan_key():
    picking = plan_for_job(
        {
            "action": "picking",
            "robot_compatible_task": "Case pick to pallet",
        }
    )
    assert picking.function == "picking"
    assert "Fulfillment Operations Manager" in picking.titles

    housekeeping = plan_for_job(
        {
            "action": "housekeeping",
            "robot_compatible_task": "Guest room turnover",
        }
    )
    assert housekeeping.function == "housekeeping"
    assert "Director of Housekeeping" in housekeeping.titles

    tending = plan_for_job(
        {
            "action": "machine_tending",
            "robot_compatible_task": "Tend the production cell",
        }
    )
    assert tending.function == "machine_tending"
    assert "Plant Manager" in tending.titles


def test_agent_rejects_junior_titles_even_when_the_word_matches():
    plan = plan_for_job(
        {
            "action": "delivery",
            "robot_compatible_task": "Pharmacy cart loop",
            "observed_workflow": "Move filled carts from pharmacy to nursing units",
        }
    )
    assert (
        score_candidate(
            plan,
            {
                "email": "tech@harrishealth.org",
                "name": "Alex Tech",
                "title": "Pharmacy Technician",
                "confidence": 99,
            },
        )
        is None
    )
    evs = plan_for_job(
        {
            "action": "scrub",
            "robot_compatible_task": "Overnight terminal floor scrubbing",
        }
    )
    assert (
        score_candidate(
            evs,
            {
                "email": "asst@mallofamerica.com",
                "name": "Pat Asst",
                "title": "Facilities Assistant",
                "confidence": 99,
            },
        )
        is None
    )
    assert score_candidate(
        plan,
        {
            "email": "maya@harrishealth.org",
            "name": "Maya Chen",
            "title": "Director of Pharmacy",
            "confidence": 82,
        },
    )
