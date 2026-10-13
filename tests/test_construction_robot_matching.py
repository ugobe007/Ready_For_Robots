"""Test construction robot matching.

Validates that construction robots:
- Derive construction_task capability from construction keywords
- Match only construction jobs (drywall, framing, rebar, layout, etc.)
- Don't match warehouse or manufacturing jobs
"""
from __future__ import annotations

from app.api.robot_job_match import RobotJobMatchIn, post_robot_job_match


def test_construction_robots_match_construction_jobs():
    """Construction robots should derive construction_task and match construction jobs only."""
    construction_robots = [
        "https://www.gritt.ai/",  # Gritt - rebar tying
        "https://bedrockrobotics.com/",  # Bedrock - construction autonomy
        "https://botcrew.com/",  # Botcrew - solar construction
    ]
    
    for url in construction_robots:
        result = post_robot_job_match(RobotJobMatchIn(url=url))
        
        caps = {c["key"] for c in result["capabilities"]}
        
        # Should have construction_task capability
        assert "construction_task" in caps, f"Construction robot {url} should have construction_task capability"
        
        # Should detect as Construction Robot type
        robot_caps = result.get("robot_capabilities", {})
        assert robot_caps.get("type") == "Construction Robot", f"Should detect as Construction Robot, got {robot_caps.get('type')}"
        assert robot_caps.get("use_case") == "Construction Operations", f"Should have Construction Operations use case"
        
        # Should match construction jobs
        jobs = result["jobs"]
        assert len(jobs) >= 5, f"Construction robot should match construction jobs, got {len(jobs)}"
        
        # All jobs should be construction-related
        for job in jobs:
            company = job.get("company_name", "")
            title = job.get("title", "")
            tape_family = job.get("tape_family", "")
            
            is_construction = (
                tape_family == "construction"
                or any(kw in (company + " " + title).lower() for kw in ["construction", "jobsite", "drywall", "rebar", "framing", "grade", "lay block"])
            )
            assert is_construction, f"Construction robot matched non-construction job: {company} - {title}"


def test_construction_robots_no_warehouse_jobs():
    """Construction robots should NOT match warehouse or manufacturing jobs."""
    result = post_robot_job_match(
        RobotJobMatchIn(url="https://www.gritt.ai/")
    )
    
    jobs = result["jobs"]
    companies = [j.get("company_name", "").lower() for j in jobs]
    
    # Should NOT match warehouse companies
    warehouse_companies = ["sanmar", "ryder", "fedex", "cloudkitchens"]
    has_warehouse = any(any(wc in c for wc in warehouse_companies) for c in companies)
    assert not has_warehouse, f"Construction robot should not match warehouse jobs, got companies: {companies}"
    
    # Should NOT match manufacturing companies
    mfg_companies = ["novolex", "intuitive surgical"]
    has_mfg = any(any(mc in c for mc in mfg_companies) for c in companies)
    assert not has_mfg, f"Construction robot should not match manufacturing jobs"


def test_construction_job_examples():
    """Construction robots should match specific construction jobs."""
    result = post_robot_job_match(
        RobotJobMatchIn(url="https://bedrockrobotics.com/")
    )
    
    jobs = result["jobs"]
    job_titles = [j.get("title", "").lower() for j in jobs]
    
    # Should match common construction tasks
    construction_tasks = ["drywall", "frame", "rebar", "layout", "grade", "block"]
    
    has_construction_tasks = any(
        any(task in title for task in construction_tasks)
        for title in job_titles
    )
    
    assert has_construction_tasks, f"Construction robot should match drywall/framing/rebar jobs, got: {job_titles}"
