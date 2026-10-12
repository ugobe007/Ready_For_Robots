#!/usr/bin/env python3
"""
Clean robot_jobs table by removing human labor postings.

These are job postings hiring humans, not requesting robot automation.
"""
import sys
from sqlalchemy import func

sys.path.insert(0, "/workspace")

from app.database import SessionLocal
from app.models.robot_directed_discovery import RobotJob

# Human occupation titles that should NEVER be in robot_jobs
HUMAN_OCCUPATIONS = {
    # Healthcare workers
    "sterile processing technician",
    "processing tech",
    "pharmacy technician",
    "patient transporter",
    "patient transport",
    "medical assistant",
    "nursing assistant",
    "cna",
    "nurse",
    "phlebotomist",
    "lab tech",
    
    # Food service workers
    "cook",
    "line cook",
    "prep cook",
    "chef",
    "bartender",
    "mixologist",
    "server",
    "waiter",
    "waitress",
    "food runner",
    "busser",
    "dishwasher",
    "dietary aide",
    "banquet server",
    
    # Construction workers
    "bricklayer",
    "mason",
    "carpenter",
    "construction worker",
    "construction laborer",
    "framer",
    "drywaller",
    "electrician",
    "plumber",
    "roofer",
    "welder",
    
    # Warehouse/logistics workers  
    "warehouse worker",
    "warehouse associate",
    "material handler",
    "forklift operator",
    "order picker",
    "packer",
    "shipper",
    "receiver",
    "dock worker",
    
    # Cleaning/maintenance workers
    "housekeeper",
    "janitor",
    "custodian",
    "cleaner",
    "room attendant",
    "housekeeping",
    "floor tech",
    "maintenance worker",
    
    # Hospitality workers
    "front desk",
    "receptionist",
    "concierge",
    "bellhop",
    "valet",
    "hotel clerk",
    
    # Retail workers
    "cashier",
    "sales associate",
    "stock clerk",
    "stocker",
    "merchandiser",
    
    # Farm workers
    "farm worker",
    "farm laborer",
    "harvest worker",
    "field worker",
    "picker",
    
    # Manufacturing workers
    "machine operator",
    "cnc operator",
    "production worker",
    "assembly worker",
    "line worker",
    "machine tender",
    
    # Other workers
    "driver",
    "security guard",
    "groundskeeper",
    "landscaper",
}


def is_human_labor_job(task: str) -> bool:
    """Check if this is a human labor requisition."""
    task_lower = task.lower().strip()
    
    # Direct title match
    for occupation in HUMAN_OCCUPATIONS:
        if occupation in task_lower:
            return True
    
    # Common hiring patterns
    human_patterns = [
        "hiring",
        "seeking",
        "looking for",
        "needed",
        "wanted",
        "join our team",
        "apply now",
        "per hour",
        "/hr",
        "hourly",
        "full-time",
        "part-time",
        "full time",
        "part time",
        "$",
        "salary",
        "benefits",
        "401k",
        "health insurance",
        "experience required",
        "must have",
        "years of experience",
    ]
    
    for pattern in human_patterns:
        if pattern in task_lower:
            return True
    
    return False


def main():
    db = SessionLocal()
    
    try:
        print("🔍 Scanning robot_jobs table for human labor contamination...")
        print()
        
        total = db.query(RobotJob).count()
        print(f"Total jobs in table: {total:,}")
        
        # Find human labor jobs
        human_jobs = []
        for job in db.query(RobotJob).all():
            task = job.robot_compatible_task or ""
            if is_human_labor_job(task):
                human_jobs.append((job.id, job.company_name, task))
        
        print(f"Human labor jobs found: {len(human_jobs):,}")
        print()
        
        if not human_jobs:
            print("✅ No human labor contamination found!")
            return
        
        print("Sample human labor jobs:")
        for i, (job_id, company, task) in enumerate(human_jobs[:10], 1):
            print(f"{i:2d}. {company}")
            print(f"    {task[:100]}")
        print()
        
        response = input(f"Delete {len(human_jobs):,} human labor jobs? (yes/no): ").strip().lower()
        
        if response == "yes":
            print()
            print(f"🗑️  Deleting {len(human_jobs):,} jobs...")
            
            deleted = 0
            for job_id, _, _ in human_jobs:
                db.query(RobotJob).filter(RobotJob.id == job_id).delete()
                deleted += 1
                if deleted % 1000 == 0:
                    print(f"  Deleted {deleted:,}...")
                    db.commit()
            
            db.commit()
            
            remaining = db.query(RobotJob).count()
            print()
            print(f"✅ Deleted {deleted:,} human labor jobs")
            print(f"✅ Remaining robot jobs: {remaining:,}")
            print()
            print("Next: Send a new test email to verify clean results")
        else:
            print("Cancelled.")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
