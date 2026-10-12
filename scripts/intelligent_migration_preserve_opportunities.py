#!/usr/bin/env python3
"""
Intelligent Migration: Reclassify 14,288 robot_jobs without losing automation opportunities.

CRITICAL RULE: Do NOT classify automation opportunities as human labor.
- "Cook" job at a restaurant = automation opportunity (Class 3-5) → KEEP
- "Hiring Cook - $18/hr - Apply Now" = human requisition → REJECT

This script:
1. Classifies all existing jobs using the 3-tier system
2. Keeps Tier 1 (explicit robot requests) in robot_jobs → daily email
3. Keeps Tier 2 (sales opportunities) in robot_jobs → marked for pipeline
4. Keeps Tier 3 (automation opportunities) in robot_jobs → marked for archive
5. Only DELETES pure human hiring ads with salary/benefits/application language

Preserves 9 months of automation opportunity data while cleaning human spam.
"""
import sys
from datetime import datetime
from typing import Any

sys.path.insert(0, "/workspace")

from app.database import SessionLocal
from app.models.robot_directed_discovery import RobotJob
from app.services.automation_opportunity_classifier import (
    classify_opportunity,
    OpportunityTier,
    OpportunityClass,
)

def is_pure_human_hiring_spam(job: Any) -> bool:
    """
    True ONLY for pure human hiring ads with application/salary language.
    
    ✅ KEEP (automation opportunities):
    - "Cook" at restaurant (work that could be automated)
    - "Warehouse Worker" (labor shortage signal)
    - "Housekeeper" (cleaning automation opportunity)
    
    ❌ DELETE (human hiring spam):
    - "Cook - $18/hr - Apply Now - Benefits"
    - "Hiring 5 Cooks - Full Time - Resume Required"
    - "Bartender Needed - Interview Today - 401k"
    """
    title = (job.robot_compatible_task or "").lower()
    desc = (job.requirements or {}).get("job_description", "").lower()
    text = f"{title} {desc}"
    
    # Must have BOTH: human occupation title AND hiring language
    human_occupations = [
        "cook", "chef", "bartender", "server", "waiter", "busser", "dishwasher",
        "housekeeper", "janitor", "custodian", "cleaner",
        "warehouse worker", "warehouse associate", "material handler",
        "forklift operator", "picker", "packer",
        "bricklayer", "mason", "carpenter", "construction worker",
        "cashier", "sales associate", "receptionist",
        "farm worker", "farm laborer", "harvest worker",
        "driver", "security guard",
    ]
    
    hiring_spam = [
        "$", "per hour", "/hr", "hourly", "salary",
        "apply now", "apply today", "hiring", "needed",
        "full-time", "full time", "part-time", "part time",
        "benefits", "401k", "health insurance", "pto",
        "resume", "interview", "background check",
        "experience required", "must have", "years of experience",
    ]
    
    # Check if it's a human occupation
    has_human_title = any(occ in title for occ in human_occupations)
    
    # Check if it has hiring spam language
    has_hiring_spam = sum(1 for spam in hiring_spam if spam in text) >= 2
    
    # Only delete if it has BOTH
    return has_human_title and has_hiring_spam


def get_job_text(job: Any) -> tuple[str, str]:
    """Extract title and description from job."""
    title = job.robot_compatible_task or ""
    desc = (job.requirements or {}).get("job_description", "")
    return title, desc


def main():
    db = SessionLocal()
    
    print("=" * 80)
    print("  INTELLIGENT MIGRATION: Reclassify 14,288 Jobs")
    print("=" * 80)
    print()
    print("RULE: Preserve ALL automation opportunities.")
    print("      Only delete pure human hiring spam.")
    print()
    
    try:
        # Get all jobs
        print("📊 Loading all robot_jobs...")
        all_jobs = db.query(RobotJob).all()
        total = len(all_jobs)
        print(f"   Total jobs: {total:,}")
        print()
        
        # Classify everything
        print("🔍 Classifying all jobs...")
        print()
        
        tier1_explicit_robot = []      # Class 11-12: "Need AMR"
        tier2_signals = []              # Class 21-24: Leadership, labor pain, cost
        tier3_automation_opp = []       # Work that COULD be automated (KEEP!)
        pure_spam = []                  # Human hiring ads with salary (DELETE)
        
        for i, job in enumerate(all_jobs, 1):
            if i % 1000 == 0:
                print(f"   Processed {i:,} / {total:,}...")
            
            title, desc = get_job_text(job)
            
            # First check: Is this pure hiring spam?
            if is_pure_human_hiring_spam(job):
                pure_spam.append((job, title))
                continue
            
            # Not spam - classify as opportunity
            tier, opp_class = classify_opportunity(title, desc)
            
            if tier == OpportunityTier.ROBOT_JOBS:
                # Explicit robot/automation request
                tier1_explicit_robot.append((job, opp_class, title))
            
            elif tier == OpportunityTier.SIGNALS:
                # Sales intelligence (leadership, labor pain, cost)
                tier2_signals.append((job, opp_class, title))
            
            else:
                # Unknown tier but NOT spam - treat as automation opportunity
                # This includes "Cook", "Warehouse Worker", etc. WITHOUT hiring spam
                tier3_automation_opp.append((job, title))
        
        print(f"   Done! Classified {total:,} jobs")
        print()
        
        # Show breakdown
        print("=" * 80)
        print("  CLASSIFICATION RESULTS")
        print("=" * 80)
        print()
        print(f"📊 Tier 1 (Explicit Robot Requests):      {len(tier1_explicit_robot):,} jobs")
        print(f"   → Keep in robot_jobs, show in daily email")
        print()
        print(f"📊 Tier 2 (Sales Opportunities):          {len(tier2_signals):,} jobs")
        print(f"   → Keep in robot_jobs, mark for pipeline follow-up")
        print()
        print(f"📊 Tier 3 (Automation Opportunities):     {len(tier3_automation_opp):,} jobs")
        print(f"   → Keep in robot_jobs, mark for future analysis")
        print()
        print(f"🗑️  Pure Human Hiring Spam:               {len(pure_spam):,} jobs")
        print(f"   → DELETE (salary, benefits, apply now)")
        print()
        
        # Show samples
        print("=" * 80)
        print("  SAMPLES (First 5 of each category)")
        print("=" * 80)
        print()
        
        if tier1_explicit_robot:
            print("✅ TIER 1 (Explicit Robot Requests) - Daily Email:")
            for job, cls, title in tier1_explicit_robot[:5]:
                print(f"   • {job.company_name}")
                print(f"     {title[:100]}")
                print(f"     Class: {cls}")
            print()
        
        if tier2_signals:
            print("📊 TIER 2 (Sales Opportunities) - Pipeline:")
            for job, cls, title in tier2_signals[:5]:
                print(f"   • {job.company_name}")
                print(f"     {title[:100]}")
                print(f"     Class: {cls}")
            print()
        
        if tier3_automation_opp:
            print("🤖 TIER 3 (Automation Opportunities) - Archive:")
            for job, title in tier3_automation_opp[:5]:
                print(f"   • {job.company_name}")
                print(f"     {title[:100]}")
            print()
        
        if pure_spam:
            print("🗑️  PURE SPAM (Will Delete):")
            for job, title in pure_spam[:5]:
                print(f"   • {job.company_name}")
                print(f"     {title[:100]}")
            print()
        
        # Confirmation
        print("=" * 80)
        print("  MIGRATION PLAN")
        print("=" * 80)
        print()
        print(f"✅ KEEP:   {len(tier1_explicit_robot) + len(tier2_signals) + len(tier3_automation_opp):,} jobs")
        print(f"           (All automation opportunities preserved!)")
        print()
        print(f"❌ DELETE: {len(pure_spam):,} jobs")
        print(f"           (Pure human hiring spam only)")
        print()
        
        if len(pure_spam) == 0:
            print("🎉 NO SPAM DETECTED!")
            print("   All jobs are automation opportunities. Applying classification...")
            print()
            should_proceed = "yes"
        else:
            response = input(f"Apply migration? Type 'yes' to proceed: ").strip().lower()
            should_proceed = response
        
        if should_proceed == "yes":
            print()
            print("🚀 Applying migration...")
            print()
            
            # Update Tier 1
            print(f"   Updating {len(tier1_explicit_robot):,} Tier 1 jobs...")
            for job, cls, _ in tier1_explicit_robot:
                job.opportunity_tier = 1
                job.opportunity_class = int(cls)
            
            # Update Tier 2
            print(f"   Updating {len(tier2_signals):,} Tier 2 jobs...")
            for job, cls, _ in tier2_signals:
                job.opportunity_tier = 2
                job.opportunity_class = int(cls)
            
            # Update Tier 3
            print(f"   Updating {len(tier3_automation_opp):,} Tier 3 jobs...")
            for job, _ in tier3_automation_opp:
                job.opportunity_tier = 3
                job.opportunity_class = 0  # Generic automation opportunity
            
            # Delete spam
            print(f"   Deleting {len(pure_spam):,} spam jobs...")
            for job, _ in pure_spam:
                db.delete(job)
            
            db.commit()
            
            # Final counts
            final_total = db.query(RobotJob).count()
            tier1_count = db.query(RobotJob).filter(RobotJob.opportunity_tier == 1).count()
            tier2_count = db.query(RobotJob).filter(RobotJob.opportunity_tier == 2).count()
            tier3_count = db.query(RobotJob).filter(RobotJob.opportunity_tier == 3).count()
            
            print()
            print("=" * 80)
            print("  ✅ MIGRATION COMPLETE!")
            print("=" * 80)
            print()
            print(f"📊 Final database state:")
            print(f"   Total jobs:        {final_total:,}")
            print(f"   Tier 1 (Email):    {tier1_count:,}")
            print(f"   Tier 2 (Pipeline): {tier2_count:,}")
            print(f"   Tier 3 (Archive):  {tier3_count:,}")
            print()
            print(f"✅ Preserved {final_total:,} automation opportunities")
            print(f"🗑️  Deleted {len(pure_spam):,} human hiring spam")
            print()
            print("Next: Send test email to see Tier 1 results!")
            
        else:
            print()
            print("❌ Migration cancelled. No changes made.")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
