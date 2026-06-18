"""Industry search lexicon — sector sub-ontologies."""
from app.services.industry_inference import infer_industry_scores
from app.services.industry_search_lexicon import (
    canonical_industries_for_query,
    expand_search_terms,
    industry_label_matches_query,
    lead_matches_search,
    sql_signal_terms_for_query,
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
    assert "food robotics" in terms
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


def test_datacenter_subject_inference():
    assert text_matches_subject_inference(
        "Hyperscale operator pilots maintenance robot inside new data center hall",
        "data center automation",
    )
    assert "Datacenters" in canonical_industries_for_query("datacenter automation")


def test_car_wash_and_laundry_subjects():
    assert text_matches_subject_inference(
        "National car wash chain deploys tunnel automation upgrade across 40 sites",
        "car wash automation",
    )
    assert text_matches_subject_inference(
        "Commercial laundry operator adds robotic flatwork handling line",
        "commercial laundry automation",
    )


def test_defense_logistics_and_grid():
    assert lead_matches_search(
        "defense logistics",
        industry="Defense",
        signal_text="Army base tests AMR fleet for defense logistics sustainment lanes",
    )
    assert text_matches_subject_inference(
        "Utility pilots substation inspection robot for grid modernization program",
        "grid automation",
    )


def test_quick_serve_and_dealership():
    assert text_matches_subject_inference(
        "QSR chain pilots kitchen robot across quick serve drive-thru locations",
        "quick serve automation",
    )
    assert "Automotive Dealerships" in canonical_industries_for_query("auto dealership automation")


def test_food_processing_and_truck_stop():
    assert text_matches_subject_inference(
        "Protein processor invests in food processing robot line for packaging hall",
        "food processing automation",
    )
    assert text_matches_subject_inference(
        "Highway travel center tests delivery robot for truck stop food court",
        "truck stop automation",
    )


def test_lab_does_not_match_collaboration_substring():
    assert not text_matches_industry_search(
        "Siemens partnership creates customisable collaborative manufacturing capability",
        "lab",
    )


def test_datacenter_query_not_every_hospitality_signal():
    assert not text_matches_industry_search(
        "Caesars F&B and housekeeping vacancy rate hits 34% during peak season",
        "data center automation",
    )


def test_grid_subject_requires_power_context():
    assert not text_matches_subject_inference(
        "Startup builds off-grid solar microgrid for remote communities",
        "grid automation",
    )
    assert text_matches_subject_inference(
        "Utility pilots substation inspection robot for grid modernization program",
        "grid automation",
    )


def test_patient_capital_not_healthcare_patient():
    assert not text_matches_subject_inference(
        "Private equity firm deploys patient capital into robotics portfolio",
        "patient automation",
    )


def test_hospital_robot_alone_not_lab_inference():
    assert not text_matches_subject_inference(
        "Siemens partnership creates customisable collaborative manufacturing capability",
        "lab automation",
    )


def test_vendor_integrator_story_filtered_from_buyer_signals():
    from app.services.signal_classifier import classify_signals_with_fallback

    text = "Acme Robotics, a leading system integrator, unveils new AMR software platform for partners."
    signals = classify_signals_with_fallback(text)
    assert signals == ["news"]


def test_row_matches_industry_search_uses_known_company_industry():
    from types import SimpleNamespace
    from app.api.leads import _row_matches_industry_search

    row = SimpleNamespace(name="White Castle", industry="Unknown")
    assert _row_matches_industry_search(row, "restaurant")
    row2 = SimpleNamespace(name="Lineage Logistics", industry="Logistics")
    assert not _row_matches_industry_search(row2, "restaurant")


def test_restaurant_still_matches_food_service_signal():
    assert text_matches_industry_search(
        "Regional QSR operator expands back of house kitchen automation pilot",
        "restaurant",
    )


def test_pack_out_still_matches_manufacturing_line():
    assert text_matches_industry_search(
        "CPG brand adds pack-out automation on new bottling line",
        "pack out",
    )


def test_lead_matches_search_known_restaurant_brand():
    assert lead_matches_search(
        "restaurant",
        industry="Unknown",
        company_name="Chipotle",
        signal_text="expands automation pilot",
    )


def test_lead_matches_search_mcdonalds_without_restaurant_in_signals():
    assert lead_matches_search(
        "restaurant",
        industry="New",
        company_name="McDonalds",
        signal_text="kitchen equipment upgrade",
    )


def test_sql_signal_terms_avoids_broad_logistics_phrases():
    terms = sql_signal_terms_for_query("restaurant")
    assert "restaurant" in terms
    assert "food delivery" not in terms


def test_robotics_channel_integrator_sector():
    assert "Manufacturing" in canonical_industries_for_query("system integrator")
    assert lead_matches_search(
        "robotics integrator",
        industry="Manufacturing",
        signal_text="Regional automation integrator expands AMR deployment services for warehouse clients",
    )


def test_humanoid_deployment_buyer_signal():
    from app.services.signal_classifier import classify_signals_with_fallback

    text = (
        "Automotive supplier pilots humanoid workforce deployment on assembly line "
        "to address skilled labor shortages"
    )
    signals = classify_signals_with_fallback(text)
    assert "robot_installation" in signals


def test_humanoid_oem_pr_filtered_to_news():
    from app.services.signal_classifier import classify_signals_with_fallback

    text = "Neura Robotics unveils NEURA 4NE1 humanoid robot platform at Hannover Messe"
    signals = classify_signals_with_fallback(text)
    assert signals == ["news"]


def test_magiclab_is_known_vendor():
    from app.services.robot_vendor_names import is_known_robotics_vendor_name

    assert is_known_robotics_vendor_name("MagicLab")
    assert is_known_robotics_vendor_name("Neura Robotics GmbH")


def test_catalog_humanoid_patterns_include_neura_and_magiclab():
    from app.services.humanoid_ontology_terms import catalog_humanoid_patterns

    patterns = catalog_humanoid_patterns()
    assert any("neura" in p for p in patterns)
    assert any("magiclab" in p for p in patterns)
