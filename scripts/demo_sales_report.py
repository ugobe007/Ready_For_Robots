#!/usr/bin/env python3
"""Demo: Generate sample sales-ready report output."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.sales_report import (  # noqa: E402
    JobOpportunity,
    format_sales_report_text,
)


def main() -> None:
    """Generate a sample report matching the PDF format."""
    
    # Create sample opportunities
    opportunities = [
        # RFP Open
        JobOpportunity(
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
        ),
        JobOpportunity(
            rank=2,
            company_name="Walmart Logistics",
            industry="Retail & E-commerce",
            city="Bentonville",
            state_country="AR",
            job_workflows=["Warehouse AMR / goods-to-person"],
            robot_types=["Warehouse AMRs"],
            timeline="High-intent window (est. 45–120 days)",
            has_robots="No",
            budget="$1.9B",
            status="RFP (incumbent: Fetch Robotics)",
            evidence_quotes=[
                ("Walmart RFP for warehouse automation across 50 distribution centers", "2026-10-01"),
                ("Seeking proposals for autonomous mobile robots with 3-year deployment timeline", "2026-10-05"),
            ],
            likely_next=["Palletizing / truck unloading", "Autonomous forklift"],
            website="https://corporate.walmart.com",
        ),
        # Exploring
        JobOpportunity(
            rank=3,
            company_name="Hilton Hotels",
            industry="Hospitality",
            city="McLean",
            state_country="VA",
            job_workflows=["Delivery / room service"],
            robot_types=["Delivery and serving robots"],
            timeline="Capital program phase (est. 90–210 days)",
            has_robots="No",
            budget=None,
            status="Exploring",
            evidence_quotes=[
                ("Hilton exploring robotic room service across portfolio in 2026", "2026-08-20"),
            ],
            likely_next=["Floor cleaning", "Concierge / greeting"],
            website="https://hilton.com",
        ),
        JobOpportunity(
            rank=4,
            company_name="Amazon Fulfillment",
            industry="E-commerce & Logistics",
            city="Seattle",
            state_country="WA",
            job_workflows=["Warehouse AMR / goods-to-person", "Palletizing / truck unloading"],
            robot_types=["Warehouse AMRs", "Palletizing robots"],
            timeline="Expansion window (est. 60–180 days)",
            has_robots="Yes — Warehouse AMR / goods-to-person; Autonomous forklift",
            budget=None,
            status="Expanding (incumbent: Kiva Systems)",
            evidence_quotes=[
                ("Amazon expanding robotics to 10 new fulfillment centers", "2026-09-25"),
            ],
            likely_next=["Autonomous forklift", "Inventory / shelf scanning"],
            website="https://amazon.com",
        ),
        JobOpportunity(
            rank=5,
            company_name="Target Corporation",
            industry="Retail",
            city="Minneapolis",
            state_country="MN",
            job_workflows=["Inventory / shelf scanning", "Warehouse AMR"],
            robot_types=["Inventory robots", "Warehouse AMRs"],
            timeline="Q1 2027",
            has_robots="No",
            budget="$150.0M",
            status="Exploring",
            evidence_quotes=[
                ("Target allocating approximately $150 million for store automation pilot", "2026-09-18"),
                ("Exploring shelf-scanning robots for inventory management in Q1 2027", "2026-09-22"),
            ],
            likely_next=["Floor cleaning", "Last-mile delivery"],
            website="https://target.com",
        ),
    ]
    
    # Generate report
    report_text = format_sales_report_text(opportunities)
    
    print(report_text)


if __name__ == "__main__":
    main()
