"""Phelan OEM job intro — named work only, blanks for unknown pay/robot."""
from app.services.oem_job_intro import (
    BLANK,
    PAY_BLANK,
    TERM_BLANK,
    compose_employer_need_intro,
    compose_robot_company_intro,
    employer_intro_from_sales_card,
    intro_from_sales_card,
)


def test_intro_uses_operator_wording_and_named_job():
    text = compose_robot_company_intro(
        contact_name="Maya Chen",
        robot_name="Stretch",
        title="Pharmacy delivery",
        employer="Rochester Regional Health",
        locality="Rochester, NY",
        monthly_comp="4200",
        duration="12 months",
        requirements="Indoor hall delivery between units and central pharmacy",
        decision_maker_name="Priya Shah",
    )
    assert text.startswith("Hi Maya, nice to meet you.")
    assert "I am a Robot Coordinator for ReadyForRobots" in text
    assert "place robots into robot automation jobs" in text
    assert "your Stretch robot" in text
    assert (
        "The job is pharmacy delivery at Rochester Regional Health in Rochester, NY"
        in text
    )
    assert "comp level of $4200 per month for 12 months" in text
    assert "requirements of indoor hall delivery" in text
    assert "arrange a call with Priya at Rochester Regional Health" in text
    assert text.endswith("Phelan.")
    assert "SIGNAL" not in text
    assert "match%" not in text.lower()
    assert "ROI" not in text


def test_intro_leaves_blanks_instead_of_inventing():
    text = compose_robot_company_intro(
        title="Pallet move",
        employer="GEODIS",
        locality="Plainfield, IN",
        requirements="Unload inbound trailers and stage pallets at the dock.",
    )
    assert text.startswith(f"Hi {BLANK}, nice to meet you.")
    assert f"your {BLANK} robot" in text
    assert f"${PAY_BLANK} per month for {TERM_BLANK}" in text
    assert "arrange a call with GEODIS" in text
    assert "operations@" not in text
    assert "Operational Lead" not in text
    assert "$8,500" not in text


def test_intro_skips_invented_and_empty_people():
    text = compose_robot_company_intro(
        contact_name="Operational Lead (Vice President)",
        employer="Chipotle",
        title="Bowl assembly",
        decision_maker_name="Not named on the posting",
    )
    assert text.startswith(f"Hi {BLANK},")
    assert "arrange a call with Chipotle" in text
    assert "Operational Lead" not in text
    assert "Not named" not in text


def test_intro_from_sales_card_fills_job_not_pay():
    text = intro_from_sales_card(
        {
            "employer": "GEODIS",
            "title": "Pallet move",
            "locality": "Plainfield, IN",
            "description": "Unload inbound trailers and stage pallets at the dock.",
            "decision_maker_name": "Priya Shah",
            "timing": "First seen 2026-10-07 · new this week",
            "contact": "dock.ops@geodis.com",
        }
    )
    assert "pallet move at GEODIS in Plainfield, IN" in text
    assert "unload inbound trailers" in text
    assert "Priya at GEODIS" in text
    assert f"${PAY_BLANK}" in text
    assert TERM_BLANK in text
    assert "First seen" not in text
    assert "dock.ops@" not in text
    assert f"Hi {BLANK}," in text


def test_employer_intro_uses_operator_wording():
    text = compose_employer_need_intro(
        contact_name="Priya Shah",
        announced_need="Pallet move",
        automation_tasks="Unload inbound trailers and stage pallets at the dock.",
        skills="indoor navigation",
        capabilities="500 lb payload",
    )
    assert text.startswith("Hi Priya, nice to meet you.")
    assert "I am a Robot Coordinator for ReadyForRobots" in text
    assert "I help find robots for automation jobs" in text
    assert "need for pallet move" in text
    assert "help with unload inbound trailers and stage pallets at the dock automation tasks" in text
    assert "robots with indoor navigation skills" in text
    assert "capabilities of 500 lb payload" in text
    assert "May I send them to you for review?" in text
    assert text.endswith("Phelan.")
    assert "SIGNAL" not in text
    assert "RaaS" not in text
    assert "match%" not in text.lower()


def test_employer_intro_leaves_skills_blank():
    text = employer_intro_from_sales_card(
        {
            "employer": "GEODIS",
            "title": "Pallet move",
            "description": "Unload inbound trailers and stage pallets at the dock.",
            "decision_maker_name": "Priya Shah",
            "contact": "dock.ops@geodis.com",
        }
    )
    assert "Hi Priya," in text
    assert "need for pallet move" in text
    assert f"robots with {BLANK} skills" in text
    assert f"capabilities of {BLANK}" in text
    assert "dock.ops@" not in text
    assert "operations@" not in text


def test_employer_intro_keeps_allcaps_tokens():
    text = compose_employer_need_intro(
        contact_name="Priya Shah",
        announced_need="AMR Pallet Move",
        automation_tasks="Unload inbound trailers",
        skills="Indoor Navigation",
        capabilities="AMR 500 lb payload",
    )
    assert "need for AMR pallet move" in text
    assert "help with unload inbound trailers" in text
    assert "robots with indoor navigation skills" in text
    assert "capabilities of AMR 500 lb payload" in text
    assert "Hi Priya," in text


def test_employer_intro_skips_invented_people():
    text = compose_employer_need_intro(
        contact_name="Operational Lead (Vice President)",
        announced_need="Bowl assembly",
    )
    assert text.startswith(f"Hi {BLANK},")
    assert "Operational Lead" not in text
    assert f"help with {BLANK} automation tasks" in text
