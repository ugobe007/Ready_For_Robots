"""A buyer row opens only from a quote that names the work."""
from __future__ import annotations

from app.services.buyer_opportunity.phase2_match import jobs_for_classification
from app.services.buyer_opportunity.source_facts import (
    load_source_quote_rows,
    named_workflow,
    publisher_from_batch_response,
    read_document,
)
from app.services.robot_understanding_v1.taxonomy_extraction import validate_evidence


def _fact(value: str) -> dict:
    return {"value": value, "confidence": 0.9, "evidence": value}


def _product(name: str, *, function: str, industries: list[str], form: str = "amr_mobile_robot") -> dict:
    return {
        "product_name": name,
        "offering_type": _fact("robot_product"),
        "form": _fact(form),
        "primary_class": _fact("amr_logistics"),
        "primary_function": _fact(function),
        "industries": [_fact(industry) for industry in industries],
    }


def test_food_delivery_without_restaurant_is_a_gap():
    page = "Wonder and Grubhub started a drone food delivery pilot across New Jersey this spring."
    result = read_document(page, company_name="Wonder Grubhub")
    assert result["rows"] == []
    gap = result["gaps"][0]
    assert gap["reason"] == "no_taxonomy_industry"
    assert gap["workflow"] == "delivery_transport"
    assert "not a taxonomy industry" in gap["note"]


def test_restaurant_in_the_quote_maps_food_delivery():
    page = "Wonder and Grubhub will expand drone delivery to other local restaurant partners."
    result = read_document(page, company_name="Wonder Grubhub", source_url="https://njbiz.com/wonder")
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert row["workflow"] == "delivery_transport"
    assert row["industry"] == "restaurant"
    assert validate_evidence(row["quotes"]["work"], page)
    assert validate_evidence(row["quotes"]["industry"], page)
    assert "restaurant" in row["quotes"]["industry"].lower()


def test_walmart_quote_names_grocery_pickup_and_does_not_invent_an_expiry():
    page = (
        "Walmart is piloting the use of storage and retrieval robotics, dubbed Alphabot, "
        "to increase the speed of online grocery order pickup. "
        "The system is being installed in a Salem, New Hampshire supercenter. "
        "Walmart said it will be operational by the end of this year."
    )
    result = read_document(page, company_name="Walmart")
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert row["workflow"] == "picking_packing_palletizing"
    assert row["industry"] == "grocery"
    assert row["signal_expiry"] is None
    assert "Alphabot" in row["quotes"]["work"]
    assert "Salem" in row["quotes"]["site"]
    assert "end of this year" in row["quotes"]["deadline"]


def test_a_robot_maker_does_not_become_a_buyer():
    page = (
        "Micropolis is a company specializing in the design, development, and manufacturing of unmanned ground vehicles. "
        "Micropolis completed a pilot of high-frequency patrol for the Ministry of Interior."
    )
    result = read_document(page, company_name="Micropolis")
    assert result["seller"] is True
    assert result["rows"] == []
    assert result["gaps"][0]["reason"] == "seller_not_buyer"


def test_a_passenger_shuttle_is_not_a_taxonomy_function():
    page = (
        "Metro Atlanta officials broke ground on autonomous shuttles near "
        "Hartsfield-Jackson Atlanta International Airport this week."
    )
    result = read_document(page, company_name="Metro Atlanta")
    assert result["rows"] == []
    assert result["gaps"][0]["work"] == "passenger shuttle"


def test_a_job_title_does_not_name_a_workflow():
    assert named_workflow("We are hiring a Robotics Engineer to lead the night shift at the plant.") is None
    stamped = (
        "ROBOT TASK SIGNAL | Machine Operator - 1st shift | Machine Tending | "
        "pay unknown | open | TreeHouse Foods"
    )
    assert named_workflow(stamped) is None
    assert named_workflow(
        "The warehouse is hiring for robotic palletizing on second shift at the fulfillment center."
    ) == "picking_packing_palletizing"


def test_google_news_batch_response_returns_the_publisher():
    body = '[["wrb.fr","Fbv4je","[\\"garturlres\\",\\"https://www.retaildive.com/news/walmart/529401/\\",1]"]]'
    assert publisher_from_batch_response(body) == "https://www.retaildive.com/news/walmart/529401/"
    assert publisher_from_batch_response('[["wrb.fr","Fbv4je",null]]') is None


def test_stored_source_rows_are_quote_backed_and_join_like_the_corpus():
    rows = load_source_quote_rows()
    assert [row["company_name"] for row in rows] == ["Walmart", "Chipotle", "Wonder Grubhub"]
    for row in rows:
        assert row["signal_expiry"] is None
        assert row["readiness_label"] == "Budget confirmed"
        page = " ".join(quote for quote in row["quotes"].values() if quote)
        again = read_document(page, company_name=row["company_name"], source_url=row["source_url"])
        matched = [item for item in again["rows"] if item["workflow"] == row["workflow"]]
        assert matched and matched[0]["industry"] == row["industry"]
        assert validate_evidence(row["quotes"]["work"], page)
        assert validate_evidence(row["quotes"]["industry"], page)

    grocery = _product("Aisle picker", function="picking_packing_palletizing", industries=["grocery"])
    jobs = jobs_for_classification(grocery, signal_rows=rows)
    assert jobs[0]["company_name"] == "Walmart"
    assert jobs[0]["is_example"] is False
    assert "Alphabot" in jobs[0]["quotes"]["work"]
    assert all(job["is_example"] for job in jobs[1:])

    delivery = _product("Sidewalk robot", function="delivery_transport", industries=["restaurant"])
    names = [job["company_name"] for job in jobs_for_classification(delivery, signal_rows=rows) if not job["is_example"]]
    assert names == ["Chipotle", "Wonder Grubhub"]

    diligent = _product("Moxi", function="delivery_transport", industries=["hospital"])
    matched = jobs_for_classification(diligent, signal_rows=rows)
    assert all(job["is_example"] for job in matched)


def test_flag_off_does_not_read_source_rows(monkeypatch):
    monkeypatch.delenv("RFR_FIND_SIGNAL_ROWS", raising=False)
    grocery = _product("Aisle picker", function="picking_packing_palletizing", industries=["grocery"])
    jobs = jobs_for_classification(grocery)
    assert all(job.get("readiness_label") is None for job in jobs)
