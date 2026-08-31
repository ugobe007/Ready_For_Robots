"""Scraper ontology params: range, named products, capabilities, task models."""
from types import SimpleNamespace

from app.services.oem_sku_discover import is_junk_sku_name, is_site_chrome_name
from app.services.robot_job_extract import (
    extract_robot_job,
    is_job_employer_name,
    job_function_from_title,
)
from app.services.robot_job_live_corpus import corpus_row_from_robot_job
from app.services.robot_job_scrape_params import (
    drone_cleaning_not_floor_scrub_only,
    infer_product_class,
    infer_required_capabilities,
    infer_task_model_requirement,
    is_chrome_name,
    is_class_dump_title,
    is_invented_sku_name,
    serving_caps_exclude_cleaner_sku,
    should_persist_robot_job,
)


def test_serving_posting_does_not_attach_to_cleaner_sku_class():
    job = extract_robot_job(
        title="Banquet Server",
        description=(
            "Food runner and busser in the dining room. Cocktail service "
            "and table delivery. Hotels and casinos."
        ),
        company="Named Casino",
        locality="Las Vegas, NV",
    )
    assert job["job_function"] == "serving"
    assert job["product_class"] == "serving"
    assert "serving_task" in job["required_capabilities"]
    assert "hard_floor_scrub" not in job["required_capabilities"]
    assert "dining_floor_service_policy" in job["task_model_ids"]
    assert serving_caps_exclude_cleaner_sku(
        job["required_capabilities"], job["product_class"]
    )
    row = SimpleNamespace(
        job_key="serve1",
        company_name="Named Casino",
        locality="Las Vegas, NV",
        action="serving",
        robot_compatible_task="Banquet Server",
        requirements={
            "job_function": "serving",
            "product_class": "serving",
            "required_capabilities": job["required_capabilities"],
            "task_model_ids": job["task_model_ids"],
            "work_task_model_kind": "unknown",
        },
        unknowns=[],
    )
    mapped = corpus_row_from_robot_job(row)
    assert mapped is not None
    assert mapped["product_class"] == "serving"
    assert mapped["tape_family"] == "serve"
    assert "floor_scrub" not in mapped["families"]


def test_drone_cleaning_posting_is_not_hard_floor_scrub_only():
    job = extract_robot_job(
        title="Window Washer",
        description=(
            "Window washing drone for facades and exteriors. "
            "Building washing from a cleaning drone. Not a floor scrubber."
        ),
        company="Named Facilities LLC",
        locality="Chicago, IL",
    )
    assert job["product_class"] == "cleaning_drone"
    assert "hard_floor_scrub" not in job["required_capabilities"]
    assert "drone_task" in job["required_capabilities"]
    assert drone_cleaning_not_floor_scrub_only(
        job["required_capabilities"], job["product_class"]
    )
    row = SimpleNamespace(
        job_key="drone1",
        company_name="Named Facilities LLC",
        locality="Chicago, IL",
        action="facade_cleaning",
        robot_compatible_task="Window Washer",
        requirements={
            "job_function": job["job_function"],
            "product_class": "cleaning_drone",
            "required_capabilities": job["required_capabilities"],
            "work_task_model_kind": "unknown",
        },
        unknowns=[],
    )
    mapped = corpus_row_from_robot_job(row)
    assert mapped is not None
    assert mapped["tape_family"] == "aerial_clean"
    assert "floor_scrub" not in mapped["families"]


def test_floor_janitor_still_grounds_floor_scrub():
    job = extract_robot_job(
        title="Office Janitor",
        description="Custodian for office floors and restrooms. Floor scrubbing and vacuuming.",
        company="Named Offices LLC",
        locality="Dallas, TX",
    )
    assert job["product_class"] == "cleaning"
    assert "hard_floor_scrub" in job["required_capabilities"]
    assert "surface_clean" in job["required_capabilities"]


def test_chrome_is_not_a_job_employer():
    for name in ("Impact", "Farmers", "Product", "About"):
        assert is_chrome_name(name)
        assert is_job_employer_name(name) is False
        assert should_persist_robot_job(title="Housekeeper", employer=name) is False
        job = extract_robot_job(
            title="Housekeeper",
            description="Room attendant. Immediate hire.",
            company=name,
            locality="Austin, TX",
        )
        assert job["persistable"] is False


def test_empty_and_invented_sku_names_are_rejected():
    for name in (
        "",
        "   ",
        "Seer Humanoid",
        "AMR scrubbers",
        "Galbot G2",
        "TWA Reach",
        "Scrubber",
    ):
        assert is_invented_sku_name(name)
        if (name or "").strip():
            assert is_junk_sku_name(name)
    assert is_class_dump_title("Seer Humanoid")
    assert is_class_dump_title("AMR scrubbers")
    assert should_persist_robot_job(
        title="Seer Humanoid", employer="Named Warehouse"
    ) is False
    assert should_persist_robot_job(
        title="Order Picker", employer="Galbot G2"
    ) is False
    assert is_site_chrome_name("Impact")
    assert is_junk_sku_name("Impact")
    assert is_junk_sku_name("Farmers")
    assert not is_invented_sku_name("BellaBot")
    assert not is_invented_sku_name("CC1")
    assert not is_invented_sku_name("MOS 2")


def test_task_model_unknown_unless_posting_names_a_source():
    unknown = infer_task_model_requirement(
        title="Banquet Server",
        description="Food runner. Dining room.",
        product_class="serving",
    )
    assert unknown["work_task_model_kind"] == "unknown"
    assert unknown["work_task_model_source"] is None
    named = infer_task_model_requirement(
        title="Order Picker",
        description="Site uses the GR00T policy pack already licensed for tote pick.",
        product_class="warehouse",
    )
    assert named["work_task_model_kind"] == "source"
    assert named["work_task_model_source"] == "GR00T"
    trained = infer_task_model_requirement(
        title="Order Picker",
        description="We will train the robot for this job on-site.",
        product_class="warehouse",
    )
    assert trained["work_task_model_kind"] == "self_train"
    assert trained["work_task_model_source"] is None
    # Do not invent a model from a robot SKU name in the listing.
    invented = infer_task_model_requirement(
        title="Server",
        description="BellaBot tray delivery. Galbot G2 is not a product on this page.",
        product_class="serving",
    )
    assert invented["work_task_model_kind"] == "unknown"
    assert invented["work_task_model_source"] is None


def test_product_class_comes_from_work_not_oem_dump():
    serving = infer_product_class(
        title="Banquet Server",
        description="Food runner and busser. Dining room cocktail service at a hotel.",
        job_function="serving",
    )
    cleaning = infer_product_class(
        title="Casino Janitor",
        description="Custodian for casino floors. Floor scrubbing and restroom cleaning.",
        job_function="environmental_services",
    )
    assert serving == "serving"
    assert cleaning == "cleaning"
    assert serving != cleaning
    assert infer_required_capabilities(serving, title="Banquet Server") == ["serving_task"]
    assert "hard_floor_scrub" in infer_required_capabilities(
        cleaning, title="Casino Janitor"
    )
    assert job_function_from_title("Window Washer - Facade") == "facade_cleaning"
