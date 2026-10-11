#!/usr/bin/env python3
"""
Audit and clean the top 25 daily robot jobs to ensure no human labor positions slip through.

This script:
1. Queries the current top 25 robot jobs
2. Tests each against strict "asks for a robot" filters
3. Identifies any human labor positions that passed through
4. Recommends additional filter patterns if needed
5. Can optionally update job statuses to exclude human labor

The filter ensures jobs explicitly ask for robots, not human workers.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))


# Enhanced patterns to catch human labor postings
_HUMAN_LABOR_INDICATORS = [
    # Direct human role requests
    (r"\bhiring\s+(?:for|a|an)?\s*(?:warehouse\s+)?(?:worker|associate|staff|crew|team|member)", 
     "hiring human workers"),
    (r"\b(?:full-time|part-time|seasonal)\s+(?:position|role|employee|staff)", 
     "employment type for humans"),
    (r"\b(?:seeking|looking for|need|hiring)\s+(?:experienced|qualified)?\s*(?:operator|technician|engineer)", 
     "seeking human professionals"),
    
    # Benefits/scheduling that indicate human employment
    (r"\b(?:401k|health\s+insurance|dental|vision|pto|paid\s+time\s+off|benefits\s+package)", 
     "employee benefits"),
    (r"\b(?:hourly\s+wage|salary\s+range|competitive\s+pay|starting\s+at\s+\$\d+)", 
     "human compensation"),
    (r"\b(?:day\s+shift|night\s+shift|overnight|weekends?|monday.friday)", 
     "work schedule"),
    
    # Application/interview process
    (r"\b(?:apply\s+(?:now|today)|submit\s+(?:your\s+)?resume|send\s+(?:your\s+)?cv)", 
     "human application process"),
    (r"\b(?:interview|screening|background\s+check|drug\s+test|reference\s+check)", 
     "human hiring process"),
    (r"\b(?:must\s+be|should\s+be)\s+(?:\d+\s+)?(?:years?\s+(?:old|of\s+age)|eligible\s+to\s+work)", 
     "human eligibility requirements"),
    
    # Training/experience requirements
    (r"\b(?:experience\s+(?:in|with)|years?\s+of\s+experience|proven\s+track\s+record)", 
     "human experience requirements"),
    (r"\b(?:high\s+school|ged|bachelor|degree|certification|license)\s+(?:required|preferred)", 
     "human education requirements"),
    (r"\btraining\s+(?:will\s+be\s+)?provided", 
     "human training"),
    
    # Physical requirements (for human workers)
    (r"\b(?:ability\s+to\s+lift|must\s+be\s+able\s+to\s+(?:lift|stand|walk))\s+(?:up\s+to\s+)?\d+\s*lbs?", 
     "human physical requirements"),
    (r"\b(?:stand|walk|sit)\s+for\s+(?:extended\s+periods?|up\s+to\s+\d+\s+hours?)", 
     "human physical endurance"),
    
    # Work environment descriptions for humans
    (r"\bfast-paced\s+environment", "human work environment"),
    (r"\bteam\s+(?:player|oriented|environment|atmosphere)", "human team environment"),
    (r"\bgreat\s+(?:communication|people)\s+skills", "human soft skills"),
]


def check_for_human_labor(title: str, description: str, workflow: str, why_job: str) -> tuple[bool, list[str]]:
    """
    Check if this job posting is actually asking for human labor.
    
    Returns:
        (is_human_labor, list of reasons)
    """
    from app.services.robot_job_extract import asks_for_a_robot
    
    # First check: does it ask for a robot at all?
    if not asks_for_a_robot(title, description, workflow, why_job):
        return (True, ["does not explicitly ask for a robot"])
    
    # Second check: look for strong human labor indicators
    blob = " ".join([title, description, workflow, why_job]).lower()
    
    human_indicators = []
    for pattern, reason in _HUMAN_LABOR_INDICATORS:
        if re.search(pattern, blob, re.I):
            human_indicators.append(reason)
    
    # If we found multiple strong human indicators, it's likely human labor
    if len(human_indicators) >= 2:
        return (True, human_indicators)
    
    return (False, [])


def audit_top_25_jobs(db_session) -> dict:
    """Audit the current top 25 robot jobs for human labor contamination."""
    from app.services.daily_jobs_report import select_daily_report_rows
    
    print("="*80)
    print("AUDITING TOP 25 ROBOT JOBS FOR HUMAN LABOR")
    print("="*80)
    print()
    
    rows = select_daily_report_rows(db_session, limit=25)
    
    print(f"Retrieved {len(rows)} jobs from database")
    print()
    
    clean_jobs = []
    human_labor_jobs = []
    
    for i, row in enumerate(rows, 1):
        job_key = str(getattr(row, "job_key", ""))
        employer = str(getattr(row, "company_name", ""))
        title = str(getattr(row, "robot_compatible_task", ""))
        description = str(getattr(row, "observed_workflow", ""))
        workflow = str(getattr(row, "why_job", ""))
        action = str(getattr(row, "action", ""))
        
        is_human, reasons = check_for_human_labor(title, description, workflow, "")
        
        job_summary = {
            "rank": i,
            "job_key": job_key,
            "employer": employer[:50],
            "title": title[:80],
            "action": action,
            "is_human_labor": is_human,
            "reasons": reasons,
        }
        
        if is_human:
            human_labor_jobs.append(job_summary)
        else:
            clean_jobs.append(job_summary)
    
    # Print results
    print(f"✓ CLEAN ROBOT JOBS: {len(clean_jobs)}")
    print(f"✗ HUMAN LABOR CONTAMINATION: {len(human_labor_jobs)}")
    print()
    
    if human_labor_jobs:
        print("="*80)
        print("HUMAN LABOR JOBS FOUND (NEED REMOVAL)")
        print("="*80)
        print()
        
        for job in human_labor_jobs:
            print(f"Rank {job['rank']:2d}: {job['employer']}")
            print(f"  Title: {job['title']}")
            print(f"  Action: {job['action']}")
            print(f"  Reasons: {', '.join(job['reasons'])}")
            print(f"  Job Key: {job['job_key']}")
            print()
    else:
        print("✅ NO HUMAN LABOR CONTAMINATION FOUND")
        print("All 25 jobs explicitly ask for robots, not human workers.")
        print()
    
    if clean_jobs:
        print("="*80)
        print(f"CLEAN ROBOT JOBS ({len(clean_jobs)})")
        print("="*80)
        print()
        
        for job in clean_jobs[:10]:  # Show first 10
            print(f"Rank {job['rank']:2d}: {job['employer']} - {job['title'][:60]}")
        
        if len(clean_jobs) > 10:
            print(f"... and {len(clean_jobs) - 10} more")
        print()
    
    return {
        "total": len(rows),
        "clean": len(clean_jobs),
        "human_labor": len(human_labor_jobs),
        "clean_jobs": clean_jobs,
        "human_labor_jobs": human_labor_jobs,
    }


def mark_as_not_robot_job(db_session, job_key: str, reason: str) -> bool:
    """Mark a job as not a robot job (human labor contamination)."""
    from app.models.robot_directed_discovery import RobotJob
    
    try:
        job = db_session.query(RobotJob).filter(RobotJob.job_key == job_key).one_or_none()
        if not job:
            print(f"  ✗ Job {job_key} not found")
            return False
        
        # Update status to exclude from reports
        job.investigate_status = "not_robot_job"
        db_session.commit()
        print(f"  ✓ Marked {job_key} as not_robot_job: {reason}")
        return True
        
    except Exception as e:
        db_session.rollback()
        print(f"  ✗ Failed to update {job_key}: {e}")
        return False


def clean_human_labor_jobs(db_session, audit_results: dict, dry_run: bool = True):
    """Remove human labor jobs from the top 25 list."""
    human_jobs = audit_results.get("human_labor_jobs", [])
    
    if not human_jobs:
        print("✅ No human labor jobs to clean")
        return
    
    print()
    print("="*80)
    print(f"CLEANING {len(human_jobs)} HUMAN LABOR JOBS")
    print("="*80)
    print()
    
    if dry_run:
        print("[DRY RUN] Would mark the following jobs as not_robot_job:")
        print()
        for job in human_jobs:
            print(f"  - {job['employer']}: {job['title']}")
            print(f"    Reasons: {', '.join(job['reasons'])}")
        print()
        print("Run with --apply to actually update the database")
    else:
        print("Marking jobs as not_robot_job...")
        print()
        
        updated = 0
        for job in human_jobs:
            reason = "; ".join(job['reasons'])
            if mark_as_not_robot_job(db_session, job['job_key'], reason):
                updated += 1
        
        print()
        print(f"✓ Updated {updated} of {len(human_jobs)} jobs")


def main():
    parser = argparse.ArgumentParser(
        description="Audit and clean top 25 robot jobs to remove human labor"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (mark human labor jobs as not_robot_job)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be done without making changes (default)",
    )
    
    args = parser.parse_args()
    
    try:
        from app.database import SessionLocal
        
        db = SessionLocal()
        
        # Run audit
        audit_results = audit_top_25_jobs(db)
        
        # Clean if needed
        if audit_results["human_labor"] > 0:
            clean_human_labor_jobs(db, audit_results, dry_run=not args.apply)
        
        db.close()
        
        # Summary
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total jobs audited: {audit_results['total']}")
        print(f"Clean robot jobs: {audit_results['clean']}")
        print(f"Human labor contamination: {audit_results['human_labor']}")
        print()
        
        if audit_results['human_labor'] == 0:
            print("✅ All jobs explicitly ask for robots, not human workers")
            return 0
        else:
            contamination_pct = (audit_results['human_labor'] / audit_results['total']) * 100
            print(f"⚠️  {contamination_pct:.1f}% contamination rate")
            
            if not args.apply:
                print()
                print("Run with --apply to clean the contaminated jobs")
            
            return 1
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
