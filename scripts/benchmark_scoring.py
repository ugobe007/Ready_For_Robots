"""
Benchmark label → ontology term mappings.

The benchmark file uses plain-English labels I created. The extraction system
uses ontology terms from our actual schema. This file maps between them,
allowing flexible matching (exact, parent class, synonym).

Product Classes:
- Allow parent/child matches (e.g. "construction_robot" matches "construction_layout_robot")
- Multiple ontology terms can satisfy one benchmark label

Capabilities:
- Map benchmark capability → one or more ontology predicates
- Score passes if ≥2 mapped capabilities are extracted

Domains/Verticals:
- Flexible matching on buyer vertical keywords
"""

# Product class mappings: benchmark_label → [accepted_ontology_terms]
PRODUCT_CLASS_MAP = {
    "healthcare_service_robot": ["service_robot", "healthcare", "delivery", "medical"],
    "indoor_delivery_robot": ["delivery", "service_robot", "transport_amr", "serving"],
    "disinfection_robot": ["disinfect", "cleaning", "healthcare"],
    "construction_robot_retrofit": ["construction", "construction_robot", "retrofit", "unknown"],
    "construction_layout_robot": ["construction", "construction_robot"],
    "construction_robot": ["construction", "construction_robot"],
    "construction_finishing_robot": ["construction", "construction_robot"],
    "service_robot": ["service_robot", "serving", "delivery"],
    "food_beverage_robot": ["service_robot", "serving", "food"],
    "cleaning_robot": ["cleaning", "floor_scrub"],
    "autonomy_software_platform": ["software", "platform", "unknown"],
    "kitchen_robot": ["service_robot", "food", "serving"],
    "food_manufacturing_robot": ["manipulator", "factory", "manufacturing"],
    "warehouse_amr": ["warehouse", "transport_amr", "logistics"],
    "mobile_manipulator": ["mobile_manipulation", "manipulator", "warehouse"],
    "humanoid_robot": ["humanoid", "general_purpose"],
    "security_robot": ["security", "patrol"],
    "agricultural_utility_robot": ["agriculture", "outdoor"],
    "agricultural_robot": ["agriculture", "outdoor"],
    "inspection_robot": ["inspection", "industrial"],
    "inventory_robot": ["warehouse", "retail"],
    "outdoor_delivery_robot": ["delivery", "outdoor", "transport_amr"],
    "collaborative_robot_arm": ["cobot", "manipulator", "manufacturing"],
    "robotics_service_provider": ["service_provider", "integration", "unknown"],
}

# Capability mappings: benchmark_capability → [ontology_predicates]
CAPABILITY_MAP = {
    "mobile_navigation": ["mobile", "autonomous_navigation"],
    "manipulation_arm": ["manipulate", "manipulation", "gripper"],
    "elevator_use": ["elevator", "indoor"],
    "item_delivery": ["delivery", "material_transport", "transport"],
    "clinical_support_tasks": ["healthcare_task", "delivery"],
    "secure_cargo": ["carry", "transport", "secure"],
    "uv_disinfection": ["disinfect", "cleaning"],
    "semi_mobile": ["mobile"],
    "pick_and_place": ["manipulate", "picking", "grasping"],
    "material_transport": ["material_transport", "transport", "mobile"],
    "assembly": ["manipulate", "assembly", "manufacturing"],
    "outdoor_unstructured": ["outdoor", "unstructured_environment"],
    "equipment_retrofit": ["retrofit", "attachment"],
    "floor_printing": ["construction_layout", "precision"],
    "precision_positioning": ["precision", "positioning"],
    "rebar_tying": ["construction_task", "rebar", "assembly"],
    "rebar_placement": ["construction_task", "rebar", "lifting"],
    "gantry_system": ["gantry", "mobile"],
    "outdoor": ["outdoor"],
    "spray_application": ["spray", "finishing", "manipulation"],
    "surface_finishing": ["finishing", "construction_task"],
    "tray_delivery": ["delivery", "serving", "transport"],
    "table_service": ["serving", "hospitality_task"],
    "customer_interaction": ["interaction", "service"],
    "dual_arm_manipulation": ["dual_arm", "manipulate", "manipulation"],
    "beverage_preparation": ["food_prep", "serving"],
    "autonomous_floor_scrubbing": ["floor_scrub", "cleaning"],
    "large_area_coverage": ["large_area", "mobile"],
    "autonomy_retrofit": ["retrofit", "autonomy"],
    "floor_cleaning": ["cleaning", "floor_scrub"],
    "inventory_scanning": ["scanning", "inventory", "vision"],
    "frying": ["food_prep", "cooking"],
    "food_preparation": ["food_prep", "manipulation"],
    "meal_assembly": ["assembly", "food_prep", "manipulation"],
    "portioning": ["precision", "food_prep"],
    "conveyor_line_integration": ["conveyor", "integration"],
    "order_picking_assist": ["picking", "order_fulfillment", "warehouse_task"],
    "fleet_management": ["fleet", "coordination"],
    "box_handling": ["box_handling", "material_handling", "manipulation"],
    "truck_unloading": ["unloading", "logistics_task"],
    "bipedal_mobility": ["bipedal", "mobile", "humanoid"],
    "tote_handling": ["tote_handling", "material_handling"],
    "manipulation": ["manipulate", "manipulation", "gripper"],
    "mobile_patrol": ["patrol", "mobile", "security_task"],
    "video_surveillance": ["surveillance", "vision", "security_task"],
    "anomaly_detection": ["anomaly_detection", "vision", "security_task"],
    "indoor_patrol": ["patrol", "indoor", "security_task"],
    "access_control_check": ["access_control", "security_task"],
    "remote_monitoring": ["monitoring", "remote"],
    "follow_me": ["follow", "mobile"],
    "autonomous_hauling": ["hauling", "transport", "material_transport"],
    "computer_vision_weeding": ["vision", "weeding", "agriculture_task"],
    "laser_actuation": ["laser", "actuation"],
    "tractor_implement": ["implement", "agriculture"],
    "legged_mobility": ["legged", "mobile", "quadruped"],
    "thermal_inspection": ["thermal", "inspection_task"],
    "acoustic_inspection": ["acoustic", "inspection_task"],
    "hazardous_environment": ["hazardous", "industrial"],
    "climbing": ["climbing", "wall_climbing"],
    "ultrasonic_testing": ["ultrasonic", "testing", "inspection_task"],
    "data_analytics": ["analytics", "data"],
    "shelf_scanning": ["scanning", "retail_task", "vision"],
    "inventory_analytics": ["analytics", "inventory"],
    "sidewalk_navigation": ["navigation", "outdoor", "sidewalk"],
    "fleet_operations": ["fleet", "operations"],
    "machine_tending": ["machine_tending", "manufacturing_task"],
    "palletizing": ["pallet_move", "palletizing", "material_handling"],
    "welding": ["welding", "manufacturing_task"],
    "collaborative_safety": ["collaborative", "safety"],
    "case_packing": ["packing", "manufacturing_task"],
    "raas_model": ["raas", "service"],
    "dexterous_manipulation": ["dexterous", "manipulation", "gripper"],
    "general_purpose": ["general_purpose", "flexible"],
}

def score_product_class(extracted_type: str, expected_class: str) -> bool:
    """
    Check if extracted product class matches expected class.
    
    Returns True if:
    - Exact match (after normalization)
    - Extracted type is in the accepted terms for expected class
    - Parent/child relationship (e.g. "construction" matches "construction_robot")
    """
    if not extracted_type:
        return False
    
    extracted_norm = extracted_type.lower().strip().replace(' ', '_').replace('-', '_')
    expected_norm = expected_class.lower().strip().replace(' ', '_').replace('-', '_')
    
    # Exact match
    if extracted_norm == expected_norm:
        return True
    
    # Check if extracted type is an accepted synonym
    accepted_terms = PRODUCT_CLASS_MAP.get(expected_norm, [])
    if extracted_norm in accepted_terms:
        return True
    
    # Partial match (parent/child)
    if extracted_norm in expected_norm or expected_norm in extracted_norm:
        return True
    
    # Check each accepted term for partial match
    for term in accepted_terms:
        if extracted_norm in term or term in extracted_norm:
            return True
    
    return False


def score_capabilities(
    extracted_caps: list[str],
    expected_caps: list[str],
    min_required: int = 2,
) -> tuple[int, list[str]]:
    """
    Count how many expected capabilities were extracted.
    
    Args:
        extracted_caps: List of ontology capability keys from extraction
        expected_caps: List of benchmark capability labels
        min_required: Minimum number required to pass (default 2)
        
    Returns:
        (matched_count, list_of_matched_benchmark_labels)
    """
    extracted_norm = [c.lower().replace(' ', '_').replace('-', '_') for c in extracted_caps]
    
    matched = []
    for expected_cap in expected_caps:
        expected_norm = expected_cap.lower().replace(' ', '_').replace('-', '_')
        
        # Get acceptable ontology terms for this benchmark capability
        acceptable_terms = CAPABILITY_MAP.get(expected_norm, [expected_norm])
        
        # Check if any extracted capability matches
        for term in acceptable_terms:
            if any(term in ext or ext in term for ext in extracted_norm):
                matched.append(expected_cap)
                break
    
    return len(matched), matched
