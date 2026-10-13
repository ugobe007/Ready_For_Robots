"""Test multi-industry robots vs dedicated domain robots.

Validates that:
- Humanoid robots match across all domains (warehouse, factory, hospital, hotel, retail, etc.)
- General-purpose service robots match across all domains
- Multi-industry platform robots (Locus, BrightPick, Omron) match across domains
- Dedicated domain robots (Moxi) only match their specific domain
"""
from __future__ import annotations

from app.api.robot_job_match import RobotJobMatchIn, post_robot_job_match


def test_humanoid_robots_match_all_domains():
    """Humanoid robots should match warehouse, factory, hospital, hotel, retail, airport, etc."""
    humanoid_robots = [
        "https://www.reflexrobotics.com/",  # Reflex humanoid
        "https://www.dexmate.com/",  # Dexmate humanoid arms
    ]
    
    for url in humanoid_robots:
        result = post_robot_job_match(RobotJobMatchIn(url=url))
        
        caps = {c["key"] for c in result["capabilities"]}
        
        # Should NOT have domain-specific task capabilities
        domain_caps = {"healthcare_task", "warehouse_task", "factory_task", "logistics_task", "hospitality_task"}
        assert not (caps & domain_caps), f"Humanoid robot {url} should not have domain restrictions"
        
        # Should have "General Automation" use case
        robot_caps = result.get("robot_capabilities", {})
        assert robot_caps.get("use_case") == "General Automation"
        
        # Should match jobs from multiple domains
        jobs = result["jobs"]
        assert len(jobs) >= 10, f"Humanoid robot should match many jobs, got {len(jobs)}"
        
        companies = [j.get("company_name", "").lower() for j in jobs[:15]]
        
        # Check for diversity across domains
        has_hospital = any("hospital" in c or "health" in c for c in companies)
        has_warehouse = any(any(kw in c for kw in ["sanmar", "warehouse", "fulfillment"]) for c in companies)
        has_mfg = any(any(kw in c for kw in ["surgical", "industrial", "novolex", "intuitive"]) for c in companies)
        
        diversity = sum([has_hospital, has_warehouse, has_mfg])
        assert diversity >= 2, f"Humanoid should match multiple domains (got diversity={diversity})"


def test_multi_industry_platforms_match_broadly():
    """Multi-industry platforms (Locus, BrightPick, Omron) should match across all their target industries."""
    platforms = [
        "https://locusrobotics.com/",  # Serves: 3PL, Apparel, Beauty, E-Commerce, Grocery, Healthcare/Pharma, Industrial
        "https://brightpick.ai/",  # Serves: E-commerce, 3PL, E-Grocery, Medical, Industrial
        "https://robotics.omron.com/",  # Serves: Manufacturing, Warehouse, Logistics, Healthcare
    ]
    
    for url in platforms:
        result = post_robot_job_match(RobotJobMatchIn(url=url))
        
        caps = {c["key"] for c in result["capabilities"]}
        
        # Should NOT have domain-specific task capabilities (they serve 3+ industries)
        domain_caps = {"healthcare_task", "warehouse_task", "factory_task", "logistics_task"}
        assert not (caps & domain_caps), f"Multi-industry platform {url} should not have domain restrictions"
        
        # Should have "General Automation" use case
        robot_caps = result.get("robot_capabilities", {})
        assert robot_caps.get("use_case") == "General Automation", f"Expected General Automation, got {robot_caps.get('use_case')}"
        
        # Should match many jobs
        jobs = result["jobs"]
        assert len(jobs) >= 10, f"Multi-industry platform should match many jobs, got {len(jobs)}"
        
        # Should have domain diversity
        companies = [j.get("company_name", "").lower() for j in jobs[:15]]
        
        has_hospital = any("hospital" in c or "health" in c for c in companies)
        has_warehouse = any(any(kw in c for kw in ["sanmar", "warehouse", "fulfillment"]) for c in companies)
        has_mfg = any(any(kw in c for kw in ["surgical", "industrial", "novolex", "intuitive"]) for c in companies)
        
        diversity = sum([has_hospital, has_warehouse, has_mfg])
        assert diversity >= 2, f"Multi-industry platform {url} should match multiple domains (got {diversity})"


def test_dedicated_healthcare_robot_restricted():
    """Moxi (dedicated healthcare robot) should ONLY match hospital/clinical jobs."""
    result = post_robot_job_match(
        RobotJobMatchIn(url="https://www.diligentrobots.com/moxi/")
    )
    
    caps = {c["key"] for c in result["capabilities"]}
    
    # SHOULD have healthcare_task (dedicated healthcare robot)
    assert "healthcare_task" in caps, "Moxi should have healthcare_task capability"
    
    # Should have "Healthcare Operations" use case
    robot_caps = result.get("robot_capabilities", {})
    assert robot_caps.get("use_case") == "Healthcare Operations"
    
    # Should match only a few highly relevant hospital jobs
    jobs = result["jobs"]
    assert 1 <= len(jobs) <= 5, f"Dedicated healthcare robot should match only relevant hospital jobs, got {len(jobs)}"
    
    # All jobs should be healthcare-related
    for job in jobs:
        company = job.get("company_name", "").lower()
        title = job.get("title", "").lower()
        text = (company + " " + title).lower()
        
        is_healthcare = any(
            kw in text
            for kw in ["hospital", "healthcare", "clinical", "patient", "nursing", "medical", "elder"]
        )
        assert is_healthcare, f"Healthcare robot matched non-healthcare job: {job.get('company_name')} - {job.get('title')}"
    
    # Should NOT match warehouse or manufacturing jobs
    companies = [j.get("company_name", "").lower() for j in jobs]
    
    has_warehouse = any(any(kw in c for kw in ["ryder", "fedex", "sanmar", "warehouse"]) for c in companies)
    has_mfg = any(any(kw in c for kw in ["novolex", "cloudkitchens"]) for c in companies)
    
    assert not has_warehouse, "Healthcare robot should not match warehouse jobs"
    assert not has_mfg, "Healthcare robot should not match manufacturing jobs"


def test_service_robot_general_purpose():
    """General-purpose service robots (Reflex, Dexmate) should work like humanoids - match broadly."""
    # This is the same as test_humanoid_robots_match_all_domains
    # but explicitly tests the user's mentioned service robots
    service_robots = [
        "https://www.reflexrobotics.com/",
        "https://www.dexmate.com/",
    ]
    
    for url in service_robots:
        result = post_robot_job_match(RobotJobMatchIn(url=url))
        
        robot_caps = result.get("robot_capabilities", {})
        assert robot_caps.get("use_case") == "General Automation", f"Service robot {url} should have General Automation"
        
        caps = {c["key"] for c in result["capabilities"]}
        domain_caps = {"healthcare_task", "warehouse_task", "factory_task"}
        assert not (caps & domain_caps), f"Service robot {url} should not be domain-restricted"
        
        jobs = result["jobs"]
        assert len(jobs) >= 10, f"Service robot should match many jobs across domains"
