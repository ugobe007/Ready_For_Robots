"""Test that Moxi hospital robot matches ONLY healthcare jobs, not warehouse jobs.

Bug report: Moxi (https://www.diligentrobots.com/moxi/) is matching warehouse/
logistics jobs (Ryder, FedEx, CloudKitchens) instead of healthcare jobs.

Root cause: Moxi profile is missing healthcare_task capability or warehouse jobs
are not properly filtered.
"""
from __future__ import annotations

from app.api.robot_job_match import RobotJobMatchIn, post_robot_job_match


def test_moxi_matches_healthcare_not_warehouse():
    """Moxi hospital robot should match healthcare jobs, not warehouse AMR jobs."""
    
    # Submit Moxi URL
    result = post_robot_job_match(
        RobotJobMatchIn(url="https://www.diligentrobots.com/moxi/")
    )
    
    # Should have matches
    assert result["state"] == "matches", f"Expected matches, got {result['state']}"
    assert result["job_count"] > 0, "Expected jobs to be found"
    
    jobs = result["jobs"]
    assert len(jobs) > 0, "Expected at least one job"
    
    # Check capabilities - should have healthcare_task
    caps = {c["key"]: c for c in result["capabilities"]}
    assert "healthcare_task" in caps, (
        f"Moxi should have healthcare_task capability. Got: {list(caps.keys())}"
    )
    
    # Check job companies - should be healthcare, not logistics
    job_companies = [j.get("company_name", "") for j in jobs]
    
    # Should NOT match warehouse/logistics companies
    bad_companies = ["Ryder", "FedEx", "CloudKitchens"]
    for company in job_companies:
        for bad in bad_companies:
            assert bad not in company, (
                f"Moxi should not match warehouse/logistics job at {company}. "
                f"Moxi is a hospital robot and should only match healthcare jobs."
            )
    
    # Check job tape families and companies - should be healthcare
    tape_families = [j.get("tape_family", "") for j in jobs]
    
    for job, family in zip(jobs, tape_families):
        company = job.get("company_name", "") or ""
        title = job.get("title", "") or ""
        
        # Check if this is a healthcare context
        is_healthcare = any(
            kw in (company + " " + title).lower()
            for kw in ["hospital", "healthcare", "medical", "clinical", "patient", "nursing", "elder", "senior living"]
        )
        
        # Warehouse/logistics families are OK only in healthcare context
        warehouse_families = ["warehouse", "pick_pack", "logistics", "pallet"]
        for bad_family in warehouse_families:
            if bad_family in family and not is_healthcare:
                assert False, (
                    f"Moxi matched non-healthcare job '{title}' at {company} "
                    f"(family: {family}). Moxi is a hospital robot and should "
                    f"only match healthcare/clinical delivery jobs."
                )
    
    # At least one job should be healthcare-related
    healthcare_keywords = ["hospital", "healthcare", "clinical", "patient", "nursing", "medical"]
    healthcare_jobs = [
        j for j in jobs
        if any(
            kw in (j.get("title", "") + " " + j.get("company_name", "")).lower()
            for kw in healthcare_keywords
        )
    ]
    
    assert len(healthcare_jobs) > 0, (
        f"Moxi should match at least one healthcare job. "
        f"Got companies: {job_companies}"
    )


def test_moxi_has_healthcare_capability():
    """Moxi profile should explicitly derive healthcare_task capability."""
    
    result = post_robot_job_match(
        RobotJobMatchIn(url="https://www.diligentrobots.com/moxi/")
    )
    
    caps = {c["key"]: c for c in result["capabilities"]}
    
    # Must have healthcare_task
    assert "healthcare_task" in caps, (
        f"Moxi profile missing healthcare_task. Got capabilities: {list(caps.keys())}"
    )
    
    # Should also have transport for clinical delivery
    assert "transport" in caps or "mobile" in caps, (
        "Moxi should have transport/mobility capabilities for hospital delivery"
    )
