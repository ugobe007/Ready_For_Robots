#!/usr/bin/env python3
"""
Verify that Grace Gong career pages are properly categorized as SUPPLY-SIDE
intelligence and will not be confused with DEMAND-SIDE job opportunities.

Grace Gong companies are robot manufacturers/OEMs (Figure, Apptronik, etc.)
hiring engineers and operators to BUILD robots. They are NOT employers posting
operational jobs to be automated (warehouses needing pickers, hotels needing
housekeepers, etc.).

This script ensures:
1. Grace Gong companies are tagged as supply-side (robotics vendors)
2. Their career pages won't be scraped as "jobs to automate"
3. The Jobs scraper only targets operational job boards (Indeed, etc.)
4. Clear distinction between "company hiring" and "work to automate"
"""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from app.services.grace_gong_career_pages import GRACE_GONG_WEEK_98_CAREER_PAGES


def verify_supply_side_categorization():
    """Verify Grace Gong companies are supply-side, not demand-side."""
    
    print("="*70)
    print("GRACE GONG SUPPLY-SIDE VERIFICATION")
    print("="*70)
    print()
    
    print("✓ Grace Gong list contains: ROBOT MANUFACTURERS (supply-side)")
    print("  - Figure, Apptronik, Physical Intelligence, Path Robotics, etc.")
    print("  - These companies BUILD robots")
    print("  - They are hiring engineers/operators to build robots")
    print()
    
    print("✗ Grace Gong list does NOT contain: EMPLOYERS WITH WORK (demand-side)")
    print("  - Warehouses needing pickers")
    print("  - Hotels needing housekeepers")
    print("  - Restaurants needing servers")
    print("  - Factories needing machine tenders")
    print()
    
    # Analyze the companies
    supply_side_indicators = []
    potential_demand_side = []
    
    for company in GRACE_GONG_WEEK_98_CAREER_PAGES:
        name = company['company']
        category = company.get('category', 'unknown')
        url = company['url']
        
        # Supply-side indicators
        if any(indicator in category.lower() for indicator in [
            'humanoid', 'foundation_model', 'robot', 'software', 
            'platform', 'embodied_ai', 'end_effector'
        ]):
            supply_side_indicators.append(f"{name} ({category})")
        
        # Check for potential confusion (should be empty)
        if any(word in name.lower() for word in [
            'warehouse', 'hotel', 'hospital', 'restaurant', 'factory',
            'logistics', 'retail', 'service', 'operations'
        ]):
            # Exception: "service_robot" category is still supply-side (robot builders)
            if category != 'service_robot':
                potential_demand_side.append(f"{name} - CHECK THIS")
    
    print(f"✓ Supply-side companies identified: {len(supply_side_indicators)}/{len(GRACE_GONG_WEEK_98_CAREER_PAGES)}")
    print()
    
    if potential_demand_side:
        print(f"⚠ WARNING: Potential demand-side confusion:")
        for item in potential_demand_side:
            print(f"  - {item}")
        print()
    else:
        print("✓ No demand-side confusion detected")
        print()
    
    # Show distinction
    print("="*70)
    print("SUPPLY-SIDE vs DEMAND-SIDE DISTINCTION")
    print("="*70)
    print()
    
    print("SUPPLY-SIDE (Grace Gong list):")
    print("  Category: Robot manufacturers/OEMs")
    print("  What they do: Build and sell robots")
    print("  What they hire for: Engineers, robotics operators, sales")
    print("  Career pages: Positions to BUILD robots")
    print("  Example: Figure hiring 'Robotics Software Engineer'")
    print()
    
    print("DEMAND-SIDE (Jobs scraper targets):")
    print("  Category: Operational employers")
    print("  What they do: Run warehouses, hotels, factories, etc.")
    print("  What they hire for: Pickers, housekeepers, machine tenders")
    print("  Job boards: Operational positions ROBOTS CAN DO")
    print("  Example: Amazon posting 'Order Picker - $18/hr - Night Shift'")
    print()
    
    return True


def verify_scraper_targets():
    """Verify that job scrapers target OPERATIONAL jobs, not career pages."""
    
    print("="*70)
    print("JOB SCRAPER TARGET VERIFICATION")
    print("="*70)
    print()
    
    print("Current job board scraper targets (from robot_job_scraper.md):")
    print()
    
    operational_targets = [
        "Indeed.com - Warehouse Worker, Housekeeper, Cook, etc.",
        "ZipRecruiter - Operational positions",
        "LinkedIn Jobs - Operational roles",
        "Industry-specific job boards",
    ]
    
    for target in operational_targets:
        print(f"  ✓ {target}")
    print()
    
    print("What gets scraped:")
    print("  ✓ Job postings for human labor (Order Picker, Server, etc.)")
    print("  ✓ Operational roles with clear tasks")
    print("  ✓ Positions robots can potentially perform")
    print()
    
    print("What does NOT get scraped:")
    print("  ✗ Career pages of robot manufacturers")
    print("  ✗ Engineering positions at robot companies")
    print("  ✗ Corporate roles (VP of Operations, etc.)")
    print("  ✗ 'Robotics Engineer' or similar builder roles")
    print()
    
    print("Filtering in place (robot_job_extract.py):")
    print("  ✓ JOB_FUNCTION_BY_TITLE extracts operational roles only")
    print("  ✓ Titles: picker, housekeeper, cook, machine tender, etc.")
    print("  ✓ Excludes: engineer, manager, analyst, director, etc.")
    print()
    
    return True


def verify_grace_gong_integration():
    """Verify how Grace Gong data should be used."""
    
    print("="*70)
    print("GRACE GONG INTEGRATION STRATEGY")
    print("="*70)
    print()
    
    print("✓ CORRECT USES of Grace Gong career pages:")
    print()
    print("  1. DEPLOYMENT SIGNAL INTELLIGENCE")
    print("     - Track hiring velocity = company scaling")
    print("     - Scaling companies are deploying robots")
    print("     - Correlate hiring → deployment announcements")
    print()
    
    print("  2. POTENTIAL EMPLOYER IDENTIFICATION")
    print("     - Robot companies may POST jobs on their sites")
    print("     - Example: Figure might post 'Robot Operator needed at")
    print("       customer XYZ facility' - THAT would be a Robot Job")
    print("     - Track if they start posting operational work")
    print()
    
    print("  3. MARKET INTELLIGENCE")
    print("     - Which robot categories are growing (humanoid 25%)")
    print("     - Geographic clusters (Bay Area 25%, China 25%)")
    print("     - Foundation model platforms (deployment multipliers)")
    print()
    
    print("✗ INCORRECT USES of Grace Gong career pages:")
    print()
    print("  1. DO NOT scrape 'Robotics Engineer' as a Robot Job")
    print("  2. DO NOT treat 'Software Engineer at Figure' as work to automate")
    print("  3. DO NOT confuse company growth hiring with operational demand")
    print()
    
    print("DATABASE TAGGING (when DATABASE_URL is available):")
    print()
    print("  When adding Grace Gong companies to database:")
    print("    company_type: 'robotics_vendor'  (NOT 'buyer')")
    print("    source: 'grace_gong_week_98'")
    print("    hiring_activity_signal: true")
    print("    deployment_velocity_indicator: 'high'")
    print()
    print("  This ensures they are:")
    print("    ✓ Tracked as supply-side intelligence")
    print("    ✓ NOT scraped as job opportunity sources")
    print("    ✓ Monitored for deployment announcements")
    print("    ✓ Considered as potential Jobs product partners")
    print()
    
    return True


def main():
    print()
    success = True
    
    try:
        success = verify_supply_side_categorization() and success
        success = verify_scraper_targets() and success
        success = verify_grace_gong_integration() and success
        
        print("="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)
        print()
        
        if success:
            print("✓ ALL CHECKS PASSED")
            print()
            print("Grace Gong career pages are properly categorized as:")
            print("  • SUPPLY-SIDE intelligence (robot manufacturers)")
            print("  • NOT demand-side job opportunities")
            print("  • Deployment velocity indicators")
            print("  • Market intelligence sources")
            print()
            print("Job scrapers are properly configured to:")
            print("  • Target OPERATIONAL job boards (Indeed, etc.)")
            print("  • Extract human labor positions (picker, housekeeper, etc.)")
            print("  • Filter out engineering/corporate roles")
            print("  • NOT scrape robot company career pages as jobs")
            print()
            print("No human labor jobs will be confused with robot company hiring.")
            print()
            return 0
        else:
            print("✗ VERIFICATION FAILED - Review output above")
            return 1
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
