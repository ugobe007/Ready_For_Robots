"""Test sales-ready report integration with daily buyers report."""
from __future__ import annotations

from app.services.daily_buyers_report import render_sales_ready_report


def test_render_sales_ready_report():
    """Test full sales-ready report rendering from buyer data."""
    
    # Mock report data structure matching compose_daily_buyers_report output
    report = {
        "date": "2026-10-13",
        "stages": ["rfp_open", "exploring"],
        "counts": {"rfp_open": 2, "exploring": 1},
        "by_stage": {
            "rfp_open": [
                {
                    "rank": 1,
                    "company": "Disney Parks & Resorts",
                    "stage": "rfp_open",
                    "score": 95.0,
                    "industry": "Entertainment & Hospitality",
                    "city": "Orlando",
                    "state": "FL",
                    "open": [
                        {
                            "label": "Floor & surface cleaning",
                            "status": "rfp",
                            "score": 90.0,
                            "vendors": ["Locus"],
                            "evidence": [
                                {
                                    "text": "Disney seeking AMR vendors for hotel operations",
                                    "seen_at": "2026-09-11",
                                }
                            ],
                        },
                        {
                            "label": "Delivery / room service",
                            "status": "rfp",
                            "score": 85.0,
                            "vendors": [],
                            "evidence": [
                                {
                                    "text": "RFP issued for autonomous delivery robots",
                                    "seen_at": "2026-09-15",
                                }
                            ],
                        },
                    ],
                    "already_has": [
                        {"label": "Restroom / sanitizing", "vendors": ["Xenex"]},
                    ],
                    "predicted_next": ["Security / patrol", "Concierge / greeting"],
                    "evidence": [
                        {
                            "kind": "rfp",
                            "label": "RFP",
                            "text": "Disney seeking AMR vendors for hotel operations across 25+ properties, budget of $60.0M",
                            "url": "https://example.com/rfp",
                            "seen_at": "2026-09-11",
                        },
                        {
                            "kind": "rfp",
                            "label": "RFP",
                            "text": "RFP issued for autonomous delivery robots with incumbent: Savioke",
                            "url": "",
                            "seen_at": "2026-09-15",
                        },
                    ],
                },
                {
                    "rank": 2,
                    "company": "Walmart Logistics",
                    "stage": "rfp_open",
                    "score": 88.0,
                    "industry": "Retail & E-commerce",
                    "city": "Bentonville",
                    "state": "AR",
                    "open": [
                        {
                            "label": "Warehouse AMR / goods-to-person",
                            "status": "rfp",
                            "score": 92.0,
                            "vendors": ["Fetch Robotics"],
                            "evidence": [],
                        },
                    ],
                    "already_has": [],
                    "predicted_next": ["Palletizing", "Autonomous forklift"],
                    "evidence": [
                        {
                            "kind": "rfp",
                            "label": "RFP",
                            "text": "Walmart RFP for warehouse automation across 50 distribution centers",
                            "url": "",
                            "seen_at": "2026-10-01",
                        },
                    ],
                },
            ],
            "exploring": [
                {
                    "rank": 3,
                    "company": "Hilton Hotels",
                    "stage": "exploring",
                    "score": 75.0,
                    "industry": "Hospitality",
                    "city": "McLean",
                    "state": "VA",
                    "open": [
                        {
                            "label": "Delivery / room service",
                            "status": "exploring",
                            "score": 78.0,
                            "vendors": [],
                            "evidence": [],
                        },
                    ],
                    "already_has": [],
                    "predicted_next": ["Floor cleaning", "Concierge"],
                    "evidence": [
                        {
                            "kind": "exploring",
                            "label": "Exploring",
                            "text": "Hilton exploring robotic room service across portfolio in 2026",
                            "url": "",
                            "seen_at": "2026-08-20",
                        },
                    ],
                },
            ],
        },
    }
    
    text = render_sales_ready_report(report)
    
    # Check header
    assert "Robot Buyer Intelligence Report — 2026-10-13" in text
    
    # Check sections
    assert "RFP Open — Published RFP / Vendor Search, Budget Confirmed" in text
    assert "Exploring — Planning, Budgeting or Piloting, No Vendor Locked In" in text
    
    # Check Disney card
    assert "001  Disney Parks & Resorts" in text
    assert "Entertainment & Hospitality · Orlando, FL" in text
    assert "Job: Floor & surface cleaning; Delivery / room service" in text
    assert "Robot Types:" in text
    assert "Schedule: High-intent window (est. 45–120 days)" in text
    assert "Has Robots: Yes — Restroom / sanitizing" in text
    assert "Budget: $60.0M" in text
    assert "Status: RFP" in text
    assert "incumbent:" in text.lower()
    assert "Likely Next: Security / patrol, Concierge / greeting" in text
    
    # Check Walmart card
    assert "002  Walmart Logistics" in text
    assert "Retail & E-commerce · Bentonville, AR" in text
    
    # Check Hilton card
    assert "003  Hilton Hotels" in text
    assert "Hospitality · McLean, VA" in text
    assert "Schedule: Capital program phase (est. 90–210 days)" in text
    
    # Verify section grouping
    rfp_section_pos = text.index("RFP Open")
    exploring_section_pos = text.index("Exploring — Planning")
    disney_pos = text.index("001  Disney")
    walmart_pos = text.index("002  Walmart")
    hilton_pos = text.index("003  Hilton")
    
    # Disney and Walmart should be in RFP section
    assert rfp_section_pos < disney_pos < exploring_section_pos
    assert rfp_section_pos < walmart_pos < exploring_section_pos
    
    # Hilton should be in Exploring section
    assert exploring_section_pos < hilton_pos
