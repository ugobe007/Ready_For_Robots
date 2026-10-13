"""Test sales report formatting (budget, vendor, timeline extraction + card format)."""
from __future__ import annotations

from app.services.sales_report import (
    JobOpportunity,
    extract_budget,
    extract_date_from_evidence,
    extract_vendor,
    format_job_opportunity_text,
)


def test_extract_budget():
    """Test budget extraction from evidence text."""
    # USD with M suffix
    assert extract_budget("investing $60.0M in automation") == "$60.0M"
    assert extract_budget("budget of $1.9B for robotics") == "$1.9B"
    assert extract_budget("spending $5.5M on AMRs") == "$5.5M"
    
    # Word forms
    assert extract_budget("approved $50 million in capital") == "$50.0M"
    assert extract_budget("allocated approximately $2.3 billion") == "$2.3B"
    
    # EUR
    assert extract_budget("investing EUR 200M in warehouse automation") == "€200.0M"
    
    # No match
    assert extract_budget("exploring robotic solutions") is None
    assert extract_budget("automation ROI") is None


def test_extract_vendor():
    """Test vendor/incumbent extraction."""
    # Explicit incumbent
    assert extract_vendor("incumbent: Locus Robotics") == "Locus Robotics"
    assert extract_vendor("vendor: Fetch Robotics") == "Fetch Robotics"
    
    # Using/deploying
    assert extract_vendor("deploying with AutoStore") == "AutoStore"
    assert extract_vendor("using GreyOrange robots") == "GreyOrange"
    
    # No match
    assert extract_vendor("exploring automation options") is None
    assert extract_vendor("piloting robots") is None


def test_extract_date_from_evidence():
    """Test date extraction from URLs and text."""
    # URL patterns
    assert extract_date_from_evidence("https://example.com/2026/08/15/article", "") == "2026-08-15"
    assert extract_date_from_evidence("https://blog.com/2026-09-01-update", "") == "2026-09-01"
    
    # Text patterns
    assert extract_date_from_evidence("", "Published on August 15, 2026") == "2026-08-15"
    assert extract_date_from_evidence("", "RFP issued 2026-10-13") == "2026-10-13"
    
    # No match
    assert extract_date_from_evidence("", "Exploring automation") == ""


def test_format_job_opportunity_text():
    """Test card formatting matching PDF layout."""
    opp = JobOpportunity(
        rank=1,
        company_name="Disney Parks & Resorts",
        industry="Entertainment & Hospitality",
        city="Orlando",
        state_country="FL",
        job_workflows=["Floor & surface cleaning", "Delivery / room service"],
        robot_types=["Floor cleaning robots", "Delivery and serving robots"],
        timeline="Capital program phase (est. 90–210 days)",
        has_robots="Yes — Restroom / sanitizing",
        budget="$60.0M",
        status="RFP (incumbent: Locus)",
        evidence_quotes=[
            ("Disney seeking AMR vendors for hotel operations across 25+ properties", "2026-09-11"),
            ("RFP issued for autonomous delivery robots", "2026-09-15"),
        ],
        likely_next=["Security / patrol", "Concierge / greeting"],
        website="https://disney.com",
    )
    
    text = format_job_opportunity_text(opp)
    
    # Check header
    assert "001  Disney Parks & Resorts" in text
    assert "Entertainment & Hospitality · Orlando, FL" in text
    
    # Check job and robot types
    assert "Job: Floor & surface cleaning; Delivery / room service" in text
    assert "Robot Types: Floor cleaning robots; Delivery and serving robots" in text
    
    # Check intelligence line
    assert "Schedule: Capital program phase (est. 90–210 days)" in text
    assert "Has Robots: Yes — Restroom / sanitizing" in text
    assert "Budget: $60.0M" in text
    
    # Check status
    assert "Status: RFP (incumbent: Locus)" in text
    
    # Check evidence quotes
    assert '"Disney seeking AMR vendors for hotel operations across 25+ properties" (2026-09-11)' in text
    assert '"RFP issued for autonomous delivery robots" (2026-09-15)' in text
    
    # Check likely next
    assert "Likely Next: Security / patrol, Concierge / greeting" in text


def test_format_job_opportunity_no_budget():
    """Test card formatting when budget/vendor/timeline are missing."""
    opp = JobOpportunity(
        rank=10,
        company_name="Generic Warehouse Corp",
        industry="Logistics",
        city="",
        state_country="",
        job_workflows=["Warehouse AMR"],
        robot_types=["Warehouse AMRs"],
        timeline="Exploring",
        has_robots="No",
        budget=None,
        status="Exploring",
        evidence_quotes=[("Exploring warehouse automation", "")],
        likely_next=["Palletizing"],
    )
    
    text = format_job_opportunity_text(opp)
    
    # Should still have rank and company
    assert "010  Generic Warehouse Corp" in text
    assert "Logistics" in text
    
    # No city/state → just industry
    assert "Logistics · " not in text or text.count("·") == 0
    
    # Has robots: No
    assert "Has Robots: No" in text
    
    # No budget in output
    assert "Budget:" not in text
