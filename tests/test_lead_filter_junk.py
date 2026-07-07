"""Junk company-name detection — generic sector phrases are not leads."""
from types import SimpleNamespace

import pytest

from app.services.lead_filter import (
    _company_name_not_corroborated_by_signals,
    classify_lead,
    is_junk,
)


@pytest.mark.parametrize(
    "name",
    [
        "Global Outlook.",
        "Global Outlook",
        "Retail Outlook",
        "Supply Chain",
        "supply chain",
        "Supply-Chain",
        "The Supply Chain",
        "Global Supply Chain",
        "Global supply chain firm",
        "Global Supply Chain Firm",
        "Global logistics firm",
        "Supply Chain Management",
        "VALUE CHAIN",
        "Logistics",
        "Digital Transformation",
        "Silicon Valley",
    ],
)
def test_sector_phrases_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True
    assert reason


@pytest.mark.parametrize(
    "name",
    [
        "Acme Logistics LLC",
        "Blue Supply Chain Partners Inc",
        "Target Corporation",
        "Faraday Future",
    ],
)
def test_real_company_names_not_junk(name):
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Japan Airlines puts humanoid robots",
        "White Castle Puts Its Restaurant",
        "White Castle Debuts Futuristic Restaurant",
        "United's mobile app",
        "United\u2019s mobile app",  # curly apostrophe from scraped titles
    ],
)
def test_verb_and_possessive_headline_fragments_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True
    assert reason


@pytest.mark.parametrize(
    "name",
    [
        "White Castle",
        "United Airlines",
        "Japan Airlines",
        "Domino\u2019s Pizza",
        "Trader Joe\u2019s",
    ],
)
def test_headline_fragment_patterns_spare_real_buyers(name):
    assert is_junk(name)[0] is False


def test_peak_season_exact_is_junk():
    assert is_junk("Peak Season")[0] is True


def test_ubs_ticker_headline_rejected_by_logic_engine_not_only_is_junk():
    from app.services.company_validator import is_valid_lead

    assert is_junk("UBS CGNX NASDAQ")[0] is False
    ok, reason = is_valid_lead("UBS CGNX NASDAQ", skip_junk_check=False)
    assert ok is False
    assert "structural" in reason.lower() or "inference" in reason.lower()


def test_scraped_article_title_too_long_is_junk():
    long_headline = (
        "Top robotics and automation companies ranked by financial performance in Q4"
    )
    assert is_junk(long_headline)[0] is True


def test_buyer_name_containing_robotics_vendor_token_not_auto_junk():
    """Prefix-only vendor match: do not block arbitrary names ending with a vendor phrase."""
    assert is_junk("Acme Bear Robotics Partnership")[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Serve Robotics and White Castle",
        "Serve Robotics and White Castle launch autonomous delivery via Uber Eats",
        "NVIDIA and SAP Partner on Enterprise AI",
        "Vegas Golden Knights and Richtech Robotics Partner",
        "BITO Lagertechnik and Locus Robotics",
    ],
)
def test_partnership_compound_names_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, reason
    assert "partnership compound" in reason.lower()


@pytest.mark.parametrize(
    "name",
    [
        "Johnson and Johnson",
        "Johnson & Johnson",
        "Marks and Spencer",
        "Procter and Gamble",
        "Ben and Jerry's",
    ],
)
def test_single_entity_and_names_not_partnership_junk(name):
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Why Automation Is",
        "Why Automation Is the Ally of Hotel Staff",
        "Five Success Factors",
        "Five Success Factors for Human–Robot Collaboration",
        "Florida Restaurant Implements Robot Workers",
        "East Coast Warehouse & Distribution",
    ],
)
def test_article_headlines_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, f"expected junk: {reason!r}"


@pytest.mark.parametrize(
    "name",
    [
        "Read More — Hotel Tech Weekly",
        "Acme Corp (Press Release)",
        "contact@acme.com",  # email scrape
        "Source: Hospitality Net",
        "NASDAQ: RBT",
        "Hotel Brand Stock Rises 12% on Earnings",
        "Yahoo Finance",
        "PR Newswire",
        "Research and Markets Report Title",
    ],
)
def test_extended_junk_patterns(name):
    junk, reason = is_junk(name)
    assert junk is True, reason


@pytest.mark.parametrize(
    "name",
    [
        "Warehouse Automation",
        "Warehouse Management Top",
        "warehouse management top",
        "WAREHOUSE AUTOMATION",
    ],
)
def test_warehouse_topic_titles_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, reason


@pytest.mark.parametrize(
    "name",
    [
        "Bear Robotics",
        "Unbox Robotics",
        "bear robotics inc",
    ],
)
def test_robot_oems_are_junk_not_buyers(name):
    junk, reason = is_junk(name)
    assert junk is True, reason
    assert "vendor" in reason.lower() or "oem" in reason.lower() or "buyer" in reason.lower()


@pytest.mark.parametrize(
    "name",
    [
        "Swedish sport airline?",
        "Swedish sports retailer...?",
        "Inside Alaska Airlines....",
        "Inside Delta Operations",
        "Norwegian sports carrier",
        "Why is this not a company???",
    ],
)
def test_editorial_headline_fragments_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, f"expected junk for {name!r}, got: {reason!r}"


@pytest.mark.parametrize(
    "name",
    [
        "Future Proofing. Power Couple ????",
        "Future Proofing and Your Supply Chain",
        "This Power Couple Is Betting on AMRs",
        "Will It Work????",
    ],
)
def test_magazine_style_headline_phrases_are_junk(name):
    assert is_junk(name)[0] is True


@pytest.mark.parametrize(
    "name",
    [
        "Meet Betty Bot",
        "Meet the Team Behind the Robot",
        "New MIT Mecalux",
        "New Stanford Robotics Lab Spinout",
    ],
)
def test_meet_and_new_university_deck_lines_are_junk(name):
    assert is_junk(name)[0] is True


def test_real_brand_without_meet_or_new_univ_prefix_not_junk():
    assert is_junk("Mecalux")[0] is False
    assert is_junk("Mecalux North America")[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Swedish sports retailer Stadium",
        "Swedish Sports Retailer Stadium AB",
    ],
)
def test_descriptor_plus_real_brand_not_junk(name):
    """Nationality + role + actual company name (e.g. Stadium) must not be junk."""
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Ideas Ahead....?",
        "DHL Warehouse Supply Chain Drive...?",
    ],
)
def test_truncated_listicle_logistics_headlines_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, f"expected junk for {name!r}, got: {reason!r}"


@pytest.mark.parametrize(
    "name",
    [
        "Unlock the ROI",
        "Airport",
        "Development",
        "Major DFW Hub in Industry First",
        "Chaos to Consistency: The 2026 Guide",
        "Three supply chain automation leaders",
    ],
)
def test_intelligence_scraper_headline_stubs_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, f"expected junk for {name!r}, got: {reason!r}"


@pytest.mark.parametrize(
    "name",
    [
        "Denver International Airport Authority",
        "Software Development Inc",
        "Airport Retail Group LLC",
    ],
)
def test_names_containing_airport_or_development_tokens_not_junk(name):
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Equipment",
        "EVERSANA Strengthens Position",
        "Acme Corp Strengthens Presence in APAC",
        "GlobalCo Strengthens Leadership Team",
    ],
)
def test_equipment_stub_and_strengthens_headline_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, reason


@pytest.mark.parametrize(
    "name",
    [
        "Eversana",
        "EVERSANA",
        "Medical Equipment Leasing LLC",
    ],
)
def test_real_brand_or_equipment_in_phrase_not_junk(name):
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Share Insights",
        "Using Flexible Robotics",
        "EBRD Grants RON",
    ],
)
def test_headline_fragments_user_reported_feb_2026(name):
    assert is_junk(name)[0] is True


@pytest.mark.parametrize(
    "name",
    [
        "s for",
        "port",
        "costs",
        "America",
        "Move}",
        "Fast Food",
        "Newsweek",
        "Use Cases",
        "Pee",
        "cloud-based",
        "Investor Day",
        "AI Adoption",
        "Hyperscale Data?",
        "USD 1",
        "Labor and Skilled Worker Shortage",
        "home",
        "Lego",
        "Top 10",
        "1 million & counting I Amazon",
        "Experiences",
        "The ROI",
        "Exosuit Study Demonstrates 62% Reduction",
        "to Incheon International Airport, with expansion",
        "Nexer Robotics to",
        "Research",
    ],
)
def test_headline_fragments_user_reported_may_2026(name):
    junk, reason = is_junk(name)
    assert junk is True, reason
    from app.services.company_validator import is_valid_lead

    ok, logic_reason = is_valid_lead(name, skip_junk_check=True)
    assert ok is False, logic_reason


@pytest.mark.parametrize(
    "name",
    [
        "Exclusive EQT Bets",
        "Google Cloud Team Up",
        "Distribution Center Jobs While Increasing",
        "Blue Jay Takes Flight Amazon",
        "Kenco GreyOrange",
        "San Jos",
        "Domino Effect",
        "Warehouse DC Operations Survey Tech",
        "Your Warehouse",
        "Melonee Wise",
        "Flexkeeping Rollout Following",
        "Kentucky distribution center",
        "Container Stacking Machine Market",
        "Chinese humanoids",
        "Dutch hospitality operating system Mews",
        "California health workers helps patients",
        "SunRobi Becomes First Certified Operator",
        "Linde Forklifts Engineering Precision",
        "Tetra Pak Factory Os",
        "Beverage Co-Packer",
        "Eindhoven's MedTech startup Xyall",
    ],
)
def test_user_reported_scraper_headline_junk_apr_2026(name):
    junk, reason = is_junk(name)
    assert junk is True, reason


def test_classify_lead_treats_logic_engine_reject_as_junk():
    """API / spotlight use classify_lead — must hide non-company strings from HOT."""
    c = SimpleNamespace(name="Share Insights", industry="Retail", employee_estimate=None)
    junk, reason, pri = classify_lead(c, None, [])
    assert junk is True
    assert pri.tier == "COLD"
    assert any(
        tok in reason.lower()
        for tok in ("junk", "logic", "structural", "inference", "distinctive", "filter")
    )


def test_classify_lead_allows_real_company():
    c = SimpleNamespace(name="Acme Logistics LLC", industry="Logistics", employee_estimate=500)
    junk, reason, pri = classify_lead(c, None, [])
    assert junk is False
    assert reason == ""


@pytest.mark.parametrize(
    "name,signal_type,text",
    [
        (
            "Sponsor Oracle Hospitality Summit",
            "expansion",
            "RobosizeME to Sponsor Oracle Hospitality Summit 2026, Brings Time-Saving Workflow Automations to OHIP Users",
        ),
        (
            "First Fully Autonomous Telehealth AI",
            "labor_shortage",
            "First Fully Autonomous Telehealth AI Robot Enables Remote Clinicians to Navigate Hospitals Without Staff Assistance",
        ),
        (
            "NJ restaurants",
            "strategic_hire",
            "NJ restaurants say robot waiters are here to stay. Here's how dining out will change.",
        ),
        (
            "QSR Operators",
            "labor_shortage",
            "QSR Operators Report Staffing Shortages as 70% Cite Unfilled Positions Heading into Busiest Season",
        ),
        (
            "Brisbane Skytower - Hotel Technology News",
            "automation_interest",
            "Brisbane Skytower adopts hotel technology according to Hotel Technology News",
        ),
    ],
)
def test_classify_lead_blocks_headline_or_category_names_before_hot(name, signal_type, text):
    c = SimpleNamespace(name=name, industry="Hospitality", employee_estimate=None)
    sigs = [SimpleNamespace(signal_type=signal_type, signal_text=text)]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"
    assert (
        "junk" in reason.lower()
        or "logic" in reason.lower()
        or "buyer opportunity" in reason.lower()
    )


def test_classify_lead_blocks_seller_story_without_buyer_intent():
    c = SimpleNamespace(name="Morphle Labs", industry="Healthcare", employee_estimate=None)
    sigs = [
        SimpleNamespace(
            signal_type="funding_round",
            signal_text="Deeptech startup Morphle Labs raises $5M in Series A round for its healthtech automation platform.",
        )
    ]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"
    assert "buyer opportunity" in reason.lower()


def test_classify_lead_blocks_imos_pizza_store_opening():
    c = SimpleNamespace(name="Imo's Pizza", industry="Manufacturing", employee_estimate=None)
    sigs = [
        SimpleNamespace(
            signal_type="expansion",
            signal_text="Imo's Pizza Opens First Store in Nashville Area",
        )
    ]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"


def test_classify_lead_allows_real_buyer_deployment_signal():
    c = SimpleNamespace(name="Millennium Hotels & Resorts", industry="Hospitality", employee_estimate=1000)
    score = SimpleNamespace(overall_intent_score=62.0, last_calculated_at=None, id=1)
    sigs = [
        SimpleNamespace(
            signal_type="automation_interest",
            signal_text="Millennium Hotels & Resorts pilots autonomous service delivery robot to support room service operations.",
        )
    ]
    junk, reason, pri = classify_lead(c, [score], sigs)
    assert junk is False
    assert reason == ""
    assert pri.tier in {"HOT", "WARM", "COLD"}


@pytest.mark.parametrize("name", ["Six Flags", "Fresh Blends"])
def test_real_customer_names_are_not_fast_delete_junk(name):
    """Real accounts may fail current-opportunity gating, but are not name junk."""
    assert is_junk(name)[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "N.J. logistics park",
        "US hospitality",
        "Third Party Logistics",
        "Elderly Americans",
        "Philly-area hospitals",
        "MGM Springfield and the technology",
        "MGM Springfield and",
        "Scaling Restaurants",
        "Hospitality Robots Strategic Business",
    ],
)
def test_ontology_descriptor_names_fail_logic_engine(name):
    from app.services.company_validator import is_valid_lead

    ok, reason = is_valid_lead(name)
    assert ok is False
    assert (
        "text_classifier" in reason
        or "inference gate" in reason
        or "structural" in reason.lower()
        # "headline shape" is a newer reject path that fires before the
        # classifiers above for headline-fragment ontology stubs; the name is
        # still correctly junked (ok is False), so accept it here too.
        or "headline shape" in reason.lower()
    ), reason


def test_short_ticker_brands_not_junk_lg_bp():
    """Cleanup uses is_junk only; must match logic-engine allowlist (see known_brands)."""
    assert is_junk("LG")[0] is False
    assert is_junk("BP")[0] is False
    assert is_junk("3M")[0] is False


@pytest.mark.parametrize(
    "name",
    [
        "Technology Banking Coverage with Veteran Banker",
        "AI agents",
        "These Robotics Companies",
        "Amazon hopes robots can replace 600K future",
        "UF's RoboPI lab",
    ],
)
def test_quality_log_headline_fragments_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True, reason


def test_mis_attributed_company_name_not_in_signal_text():
    """Headline fragment as company.name with unrelated article bullets."""
    sigs = [
        SimpleNamespace(signal_text="Fetch Robotics raises funding."),
        SimpleNamespace(signal_text="Starship expands fleet."),
    ]
    assert _company_name_not_corroborated_by_signals("HeadlineFragmentXy", sigs) is True
    assert _company_name_not_corroborated_by_signals("Fetch Robotics", sigs) is False


def _rss_sig(text: str, signal_type: str = "expansion"):
    return SimpleNamespace(
        signal_type=signal_type,
        signal_text=(
            f"{text} <a href=\"https://news.google.com/rss/articles/ABC\" "
            'target="_blank">story</a>'
        ),
    )


def test_classify_lead_blocks_indefinite_article_restaurant_chain_headline():
    c = SimpleNamespace(
        name="A 1920s-Era Restaurant Chain",
        industry="Food Service",
        source="news_discovery",
        employee_estimate=None,
        is_internal=True,
    )
    sigs = [
        _rss_sig(
            "A 1920s-Era Restaurant Chain Is Expanding with a New Phoenix-Area Location."
        )
    ]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"
    assert "rss scrape noise" in reason.lower() or "headline shape" in reason.lower()


def test_classify_lead_blocks_how_to_labor_costs_headline():
    c = SimpleNamespace(
        name="Lower Restaurant Labor Costs",
        industry="Food Service",
        source="news_discovery",
        employee_estimate=None,
        is_internal=True,
    )
    sigs = [
        _rss_sig("How to Lower Restaurant Labor Costs in 2026 - Toast POS.")
    ]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"


def test_classify_lead_blocks_quoted_company_headline_unicode_quotes():
    c = SimpleNamespace(
        name="\u2018Seafood Robotics\u2019 Company",
        industry="Food Service",
        source="news_discovery",
        employee_estimate=None,
        is_internal=True,
    )
    sigs = [
        _rss_sig(
            "\u2018Seafood Robotics\u2019 Company Buys Washington State Processing Plant."
        )
    ]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"


def test_classify_lead_blocks_generic_descriptor_rss_headline():
    c = SimpleNamespace(
        name="Efficient design",
        industry="Unknown",
        source="news_discovery",
        employee_estimate=None,
        is_internal=True,
    )
    sigs = [_rss_sig("Efficient design trends in warehouse automation.")]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"


def test_classify_lead_allows_seed_v2_buyer_with_rich_signals():
    c = SimpleNamespace(
        name="Accor Hotels",
        industry="Hospitality",
        source="seed_v2",
        employee_estimate=50000,
        is_internal=True,
    )
    score = SimpleNamespace(overall_intent_score=85.0, last_calculated_at=None, id=1)
    sigs = [
        SimpleNamespace(
            signal_type="labor_shortage",
            signal_text="Accor investing EUR 300M in hotel technology transformation including service robots.",
        )
    ]
    junk, reason, pri = classify_lead(c, [score], sigs)
    assert junk is False


def test_classify_lead_blocks_pipe_delimited_rss_headline():
    c = SimpleNamespace(
        name="AI-powered | WellSpan York Hospital",
        industry="Healthcare",
        source="news_discovery",
        employee_estimate=None,
        is_internal=True,
    )
    sigs = [
        _rss_sig(
            "AI-powered | WellSpan York Hospital unveils full-service robotic kitchen."
        )
    ]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"


def test_classify_lead_blocks_see_photos_of_headline():
    c = SimpleNamespace(
        name="See photos of WellSpan York Hospital",
        industry="Healthcare",
        source="news_discovery",
        employee_estimate=None,
        is_internal=True,
    )
    sigs = [_rss_sig("See photos of WellSpan York Hospital's new robotic kitchen unveiled.")]
    junk, reason, pri = classify_lead(c, None, sigs)
    assert junk is True
    assert pri.tier == "COLD"


# ── Pool-names mission: vendors (incl. allowlisted/headline forms) + descriptors ──


@pytest.mark.parametrize(
    "name",
    [
        # Vendor gate must win over the brand allowlist, incl. headline fragments.
        "Locus Robotics",
        "Locus Robotics Surpasses 5 Billion Pick Milestone",
        "Locus Robotics survey: 7",
        # Newly-added material-handling / service-robot OEMs.
        "Daifuku",
        "Daifuku Co",
        "Dematic",
        "Vanderlande",
        "Keenon",
        "Keenon Humanoid Robot Joins Hotel Chain",
        "Richtech Robotics",
        "Addverb Technologies",
        "Hikrobot",
        "Exotec",
    ],
)
def test_robot_vendors_are_junk_even_if_allowlisted(name):
    junk, reason = is_junk(name)
    assert junk is True
    assert "vendor" in reason.lower() or "oem" in reason.lower()


@pytest.mark.parametrize(
    "name",
    [
        "PA logistics company",
        "Miami logistics company",
        "2021 Women",
        "2023 Robotics Roundup",
        "Dynamic Warehouse AI-Powered AMRs",
    ],
)
def test_generic_descriptors_and_list_fragments_are_junk(name):
    junk, reason = is_junk(name)
    assert junk is True
    assert reason


@pytest.mark.parametrize(
    "name",
    [
        # Real buyers that must NOT be caught by the new descriptor/vendor rules.
        "Radisson Hotel Group",
        "Melia Hotel Group",
        "RJW Logistics Group",
        "Rebel Hotel Company",
        "PM Hotel Group",
    ],
)
def test_real_buyers_survive_pool_name_rules(name):
    assert is_junk(name)[0] is False


def test_vendor_allowed_in_oem_prospect_mode():
    # StageGate/XBOT pipeline sells TO vendors — they must pass in oem_prospect mode.
    assert is_junk("Daifuku Co", mode="oem_prospect")[0] is False
    assert is_junk("Locus Robotics", mode="oem_prospect")[0] is False
