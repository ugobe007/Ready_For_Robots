"""Robot opportunity ontology: operational work is the opportunity; only builders/desk work drop."""
import pytest

from app.services.automation_opportunity_classifier import OpportunityTier, classify_opportunity, should_reject
from app.services.workflow_ontology import FAMILIES, analyze_posting, search_terms


@pytest.mark.parametrize("title,desc,company,tier,family", [
    ("Order Picker - Nights", "$19-$22/hr, $1,000 sign-on bonus, lift 50 lbs, 150 units per hour", "Kroger", 2, "picking"),
    ("Line Cook", "", "Caesars Entertainment", 3, "food_prep"),
    ("Dishwasher", "", "Wynn Las Vegas", 3, "warewash"),
    ("EVS Tech", "terminal clean of isolation rooms", "HCA Healthcare", 2, "environmental_services"),
    ("Janitor", "", "ABM", 2, "cleaning"),
    ("CNC Machine Operator", "", "Parker Hannifin", 2, "machine_tending"),
    ("Production Associate", "Stack cases onto pallets at end of line, stretch-wrap", "Coca-Cola Bottling", 2, "palletizing"),
    ("Security Officer", "patrol parking structure", "Allied Universal", 3, "security_patrol"),
    ("Recycling Sorter", "", "Republic Services", 3, "waste_recycling"),
    ("Maintenance Technician", "maintain palletizing robots and conveyors", "PepsiCo", 1, "palletizing"),
    ("Automation Engineer", "support AMR deployment across our DCs", "Sysco", 1, None),
    ("Warehouse Associate", "work alongside autonomous mobile robots", "GEODIS", 1, "material_handling"),
])
def test_operational_work_is_an_opportunity(title, desc, company, tier, family):
    a = analyze_posting(title, desc, company)
    assert a.tier == tier, a.reason
    assert (a.primary.key if a.primary else None) == family


@pytest.mark.parametrize("title,company", [
    ("Robotics Software Engineer", "Locus Robotics"),
    ("Perception Engineer", "Agility Robotics"),
    ("Field Service Technician", "Locus Robotics"),
    ("Senior Accountant", "Marriott"),
    ("SQL Server Administrator", "Bank of America"),
])
def test_builders_and_desk_work_are_not_opportunities(title, company):
    tier, _ = classify_opportunity(title, "", company)
    assert should_reject(tier)


def test_human_job_language_never_rejects():
    """Regression for the 2026-10-11 purge: '$', 'hiring', 'full-time' are not disqualifiers."""
    tier, _ = classify_opportunity("Housekeeper - Hiring Now! $18/hr Full-Time w/ Benefits", "Apply now", "MGM Resorts")
    assert tier in (OpportunityTier.AUTOMATION_READY, OpportunityTier.AUTOMATABLE_WORK)


def test_every_family_has_vendors_and_search_terms():
    terms = search_terms()
    for fam in FAMILIES:
        assert fam.robot_categories and 0 < fam.automatability <= 1
        assert terms[fam.key], fam.key
