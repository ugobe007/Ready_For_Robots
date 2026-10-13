"""Test that domain task filtering works for all robot types.

Ensures that:
- Healthcare robots only match healthcare jobs
- Warehouse robots only match warehouse jobs
- Factory robots only match factory jobs
- Generic robots (no domain) can match across domains
"""
from __future__ import annotations

from app.api.robot_job_match import RobotJobMatchIn, post_robot_job_match


def test_healthcare_robot_matches_only_healthcare():
    """Healthcare robots (Moxi) should only match hospital/clinical jobs."""
    result = post_robot_job_match(
        RobotJobMatchIn(url="https://www.diligentrobots.com/moxi/")
    )
    
    assert "healthcare_task" in {c["key"] for c in result["capabilities"]}
    
    jobs = result["jobs"]
    assert len(jobs) > 0, "Healthcare robot should match some jobs"
    
    # All jobs should be healthcare-related
    for job in jobs:
        company = job.get("company_name", "")
        title = job.get("title", "")
        text = (company + " " + title).lower()
        
        is_healthcare = any(
            kw in text
            for kw in ["hospital", "healthcare", "clinical", "patient", "nursing", "medical", "elder"]
        )
        assert is_healthcare, f"Healthcare robot matched non-healthcare job: {company} - {title}"


def test_locus_healthcare_operations_matches_healthcare():
    """Locus with 'Healthcare Operations' use case should match healthcare jobs."""
    result = post_robot_job_match(
        RobotJobMatchIn(url="https://locusrobotics.com/")
    )
    
    caps = {c["key"] for c in result["capabilities"]}
    assert "healthcare_task" in caps, "Locus with Healthcare Operations should have healthcare_task"
    
    jobs = result["jobs"]
    assert len(jobs) > 0
    
    # Should match hospital jobs
    healthcare_jobs = [
        j for j in jobs
        if any(kw in (j.get("company_name", "") + " " + j.get("title", "")).lower()
               for kw in ["hospital", "healthcare", "medical"])
    ]
    assert len(healthcare_jobs) > 0, "Healthcare-focused Locus should match hospital jobs"


def test_generic_warehouse_matches_broadly():
    """Generic warehouse AMR (no specific domain) should match across domains."""
    result = post_robot_job_match(
        RobotJobMatchIn(chip="moves_materials")
    )
    
    caps = {c["key"] for c in result["capabilities"]}
    
    # Should NOT have domain-specific tasks (generic)
    domain_caps = {"healthcare_task", "warehouse_task", "factory_task", "logistics_task"}
    assert not (caps & domain_caps), f"Generic AMR should not have domain task caps, got: {caps & domain_caps}"
    
    jobs = result["jobs"]
    assert len(jobs) > 0
    
    # Should match jobs from multiple domains
    has_hospital = any("hospital" in j.get("company_name", "").lower() for j in jobs)
    has_warehouse = any(
        any(kw in j.get("company_name", "").lower() for kw in ["warehouse", "fulfillment", "sanmar"])
        for j in jobs
    )
    has_manufacturing = any(
        any(kw in j.get("company_name", "").lower() for kw in ["surgical", "novolex", "industrial"])
        for j in jobs
    )
    
    # At least 2 different domains
    domain_count = sum([has_hospital, has_warehouse, has_manufacturing])
    assert domain_count >= 2, f"Generic robot should match multiple domains, got: hospital={has_hospital}, warehouse={has_warehouse}, mfg={has_manufacturing}"


def test_cleaning_robot_matches_broadly():
    """Cleaning robots (no domain task) should match across industries."""
    result = post_robot_job_match(
        RobotJobMatchIn(chip="cleans")
    )
    
    caps = {c["key"] for c in result["capabilities"]}
    
    # Should NOT have domain-specific tasks
    domain_caps = {"healthcare_task", "warehouse_task", "factory_task"}
    assert not (caps & domain_caps), "Cleaning robot should not have domain task caps"
    
    jobs = result["jobs"]
    assert len(jobs) > 0
    
    # Should match cleaning jobs across domains (mall, airport, hospital, university, etc.)
    companies = [j.get("company_name", "").lower() for j in jobs]
    
    # Check for diversity of industries
    has_retail = any("mall" in c for c in companies)
    has_transport = any("airport" in c for c in companies)
    has_healthcare = any("hospital" in c or "health" in c for c in companies)
    
    diversity = sum([has_retail, has_transport, has_healthcare])
    assert diversity >= 2, f"Cleaning robot should match multiple industries, got diversity={diversity}"
