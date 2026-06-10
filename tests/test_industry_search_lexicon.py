"""Industry search lexicon — sector sub-ontologies."""
from app.services.industry_inference import infer_industry_scores
from app.services.industry_search_lexicon import (
    canonical_industries_for_query,
    expand_search_terms,
    industry_label_matches_query,
    lead_matches_search,
    text_matches_industry_search,
)
from app.services.industry_sector_ontology import (
    match_ontology_query,
    text_matches_subject_inference,
)


def test_restaurant_maps_to_food_service():
    assert "Food Service" in canonical_industries_for_query("restaurant")
    assert industry_label_matches_query("Food Service", "restaurant")
    assert not industry_label_matches_query("Logistics", "restaurant")


def test_food_robot_expansion():
    terms = expand_search_terms("food robot")
    assert "kitchen robot" in terms
    assert "serving robot" in terms


def test_food_prep_matches_signal_text():
    assert text_matches_industry_search(
        "Chain deploys kitchen automation for food prep during dinner rush",
        "food prep",
    )


def test_lead_matches_search_restaurant_name():
    assert lead_matches_search(
        "restaurant",
        industry="Hospitality",
        company_name="Regional QSR operator",
        signal_text="Fast casual expansion with back of house automation pilot",
    )


def test_food_delivery_alias():
    assert lead_matches_search(
        "food delivery",
        industry="Logistics",
        signal_text="Last-mile delivery robot pilot at airport concessions",
    )


def test_manufacturing_sub_ontology_pack_out():
    match = match_ontology_query("pack out")
    assert "Manufacturing" in match.canonical_industries or "CPG & Consumer Goods" in match.canonical_industries
    assert "pack in" in match.expansion_terms
    assert text_matches_industry_search(
        "CPG brand adds pack-out automation on new bottling line",
        "pack out",
    )


def test_logistics_intra_micro_light():
    terms = expand_search_terms("intra logistics")
    assert "micro logistics" in terms or "warehouse logistics" in terms
    assert lead_matches_search(
        "micro logistics",
        industry="Logistics",
        signal_text="3PL pilots light logistics AMRs between pick zones",
    )


def test_grocery_fulfillment_sub_ontology():
    assert "Retail" in canonical_industries_for_query("grocery pick and pack")
    assert text_matches_industry_search(
        "Supermarket chain scales grocery fulfillment automation in dark store",
        "grocery fulfillment automation",
    )


def test_hospitality_room_service_automation():
    assert lead_matches_search(
        "room service automation",
        industry="Hospitality",
        signal_text="Resort pilots in-room dining robot for guest room delivery",
    )


def test_facilities_janitorial_and_landscape():
    assert "Real Estate & Facilities" in canonical_industries_for_query("janitorial automation")
    assert text_matches_industry_search(
        "Property manager evaluates landscape automation for campus grounds",
        "landscape automation",
    )


def test_typo_manufacting_alias():
    assert "Manufacturing" in canonical_industries_for_query("manufacting")


def test_typo_package_handling():
    assert text_matches_industry_search(
        "Distribution hub upgrades package handling robotics",
        "package handing",
    )


def test_lab_subject_inference_without_exact_phrase():
    hay = "Regional health system pilots AMR for lab specimen runs between floors"
    assert text_matches_subject_inference(hay, "lab automation")
    assert lead_matches_search(
        "lab automation",
        industry="Healthcare",
        signal_text=hay,
    )


def test_patient_subject_inference():
    assert text_matches_subject_inference(
        "Hospital deploys patient transport robots to reduce nurse walking time",
        "patient automation",
    )


def test_airport_baggage_subject_inference():
    assert text_matches_subject_inference(
        "International terminal invests in baggage sortation robot pilot",
        "airport baggage handling automation",
    )
    assert "Airports & Aviation" in canonical_industries_for_query("baggage handling")


def test_automotive_parts_logistics():
    assert lead_matches_search(
        "parts logistics",
        industry="Automotive & Manufacturing",
        signal_text="OEM scales AMR fleet for spare parts logistics between plants",
    )


def test_infer_industry_scores_lab_robot_boost():
    scores = infer_industry_scores("Hospital pilots delivery robot for clinical lab workflow")
    assert scores.get("Healthcare", 0) >= 1 or scores.get("Medical Technology", 0) >= 1


def test_pharmacy_and_icu_subjects():
    assert text_matches_subject_inference(
        "ICU nursing unit tests autonomous supply cart during night shift",
        "icu automation",
    )
    assert text_matches_subject_inference(
        "Central pharmacy robot deployment reduces cart-fill labor",
        "pharmacy automation",
    )
