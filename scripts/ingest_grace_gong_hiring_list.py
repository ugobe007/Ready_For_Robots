#!/usr/bin/env python3
"""
Ingest Grace Gong's Physical AI Hiring List into RFR monitoring.

Grace Gong publishes weekly "On My Radar" lists of physical AI companies
actively hiring, ranked by % headcount growth in past 90 days. This is a
high-signal deployment and employment indicator.

This script:
1. Cross-references the list against our companies database
2. Adds new companies to our monitoring/scraping targets
3. Generates a market intelligence report for docs/market_thesis.md

Source: https://www.linkedin.com/posts/grace-gong_physical-ai-companies-hiring-list-week-98-activity-xxxxx

Usage:
  python3 scripts/ingest_grace_gong_hiring_list.py --dry-run
  python3 scripts/ingest_grace_gong_hiring_list.py --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

# Grace Gong's Physical AI Hiring List - Week 98 (October 2026)
# Ranked by % headcount growth in past 90 days
GRACE_GONG_WEEK_98 = [
    {
        "name": "Booster Robotics",
        "description": "humanoids for developers",
        "location": "Beijing",
        "career_page": "https://booster.tech/careers",
        "category": "humanoid_platform"
    },
    {
        "name": "Skild AI",
        "description": "one brain to control many kinds of robots",
        "location": "Pittsburgh",
        "career_page": "https://skild.ai/careers",
        "category": "foundation_model"
    },
    {
        "name": "X Square Robot",
        "description": "robots driven by an end-to-end large model",
        "location": "Shenzhen",
        "career_page": "https://x2robot.com/careers",
        "category": "foundation_model",
        "chinese_name": "自变量机器人"
    },
    {
        "name": "XDOF",
        "description": "foundation models for robots",
        "location": "San Mateo",
        "career_page": "https://xdof.com/careers",
        "category": "foundation_model"
    },
    {
        "name": "EngineAI",
        "description": "humanoid robots",
        "location": "Shenzhen",
        "career_page": "https://engineai.com.cn/careers",
        "category": "humanoid"
    },
    {
        "name": "ShengShu",
        "description": "world model for the digital and physical world",
        "location": "Beijing",
        "career_page": "https://shengshu-ai.com/careers",
        "category": "foundation_model"
    },
    {
        "name": "Sunday",
        "description": "home robot for household chores",
        "location": "Redwood City",
        "career_page": "https://sunday.ai/careers",
        "category": "home_robot"
    },
    {
        "name": "Maven Robotics",
        "description": "autonomous industrial robots",
        "location": "Santa Clara",
        "career_page": "https://mavenrobotics.ai/careers",
        "category": "industrial"
    },
    {
        "name": "Figure",
        "description": "general-purpose humanoid robot",
        "location": "Sunnyvale",
        "career_page": "https://figure.ai/careers",
        "category": "humanoid"
    },
    {
        "name": "Sharpa",
        "description": "human-like robot hands and humanoids",
        "location": "Singapore",
        "career_page": "https://sharpa.com/careers",
        "category": "humanoid"
    },
    {
        "name": "Physical Intelligence",
        "description": "foundation models for robots",
        "location": "San Francisco",
        "career_page": "https://physicalintelligence.company/careers",
        "category": "foundation_model"
    },
    {
        "name": "Scout AI",
        "description": "foundation model for defense robots",
        "location": "Sunnyvale",
        "career_page": "https://scoutai.com/careers",
        "category": "defense"
    },
    {
        "name": "Tutor",
        "description": "AI robots for warehouses and factories",
        "location": "Watertown",
        "career_page": "https://tutorintelligence.com/careers",
        "category": "industrial"
    },
    {
        "name": "LimX Dynamics",
        "description": "full-size general-purpose humanoids",
        "location": "Shenzhen",
        "career_page": "https://limxdynamics.com/careers",
        "category": "humanoid"
    },
    {
        "name": "Dyna Robotics",
        "description": "general-purpose robots on foundation models",
        "location": "Redwood City",
        "career_page": "https://dyna.co/careers",
        "category": "foundation_model"
    },
    {
        "name": "Rhoda AI",
        "description": "robots run on general-purpose foundation models",
        "location": "Palo Alto",
        "career_page": "https://rhoda.ai/careers",
        "category": "foundation_model"
    },
    {
        "name": "ROBOTERA",
        "description": "embodied AI robots",
        "location": "Beijing",
        "career_page": "https://robotera.com/careers",
        "category": "embodied_ai"
    },
    {
        "name": "Generalist",
        "description": "AI that trains robots to do many tasks",
        "location": "San Mateo",
        "career_page": "https://generalist.ai/careers",
        "category": "foundation_model"
    },
    {
        "name": "NEURA Robotics",
        "description": "robots that work alongside people",
        "location": "Metzingen",
        "career_page": "https://neura-robotics.com/careers",
        "category": "collaborative"
    },
    {
        "name": "RLWRLD",
        "description": "five-finger robot hands",
        "location": "Seoul",
        "career_page": "https://rlwrld.ai/careers",
        "category": "end_effector"
    },
    {
        "name": "Path Robotics",
        "description": "AI welding robots",
        "location": "Columbus",
        "career_page": "https://path-robotics.com/careers",
        "category": "industrial_welding"
    },
    {
        "name": "VinMotion",
        "description": "tools to deploy humanoids at scale",
        "location": "US",
        "career_page": "https://vinmotion.com/careers",
        "category": "deployment_tools"
    },
    {
        "name": "Apptronik",
        "description": "modular humanoid robots",
        "location": "Austin",
        "career_page": "https://apptronik.com/careers",
        "category": "humanoid"
    },
    {
        "name": "Humanoid",
        "description": "industrial humanoid robots",
        "location": "London",
        "career_page": "https://thehumanoid.ai/careers",
        "category": "humanoid"
    },
    {
        "name": "General Robotics",
        "description": "modular intelligence platform for robots",
        "location": "Redmond",
        "career_page": "https://generalrobotics.ai/careers",
        "category": "platform"
    },
    {
        "name": "Galbot",
        "description": "embodied AI robots",
        "location": "Beijing",
        "career_page": "https://galbot.com/careers",
        "category": "embodied_ai"
    },
    {
        "name": "Magiclab Robotics",
        "description": "general-purpose and humanoid robots",
        "location": "Beijing",
        "career_page": "https://magiclab.top/careers",
        "category": "humanoid"
    },
    {
        "name": "Generative Bionics",
        "description": "humanoid robots",
        "location": "Genoa",
        "career_page": "https://gbionics.ai/careers",
        "category": "humanoid"
    },
    {
        "name": "Standard Bots",
        "description": "AI-native industrial robots",
        "location": "Glen Cove",
        "career_page": "https://standardbots.com/careers",
        "category": "industrial"
    },
    {
        "name": "Waabi",
        "description": "physical AI for self-driving trucks",
        "location": "Toronto",
        "career_page": "https://waabi.ai/careers",
        "category": "autonomous_vehicles"
    },
    {
        "name": "Pudu Robotics",
        "description": "service robots for businesses",
        "location": "Shenzhen",
        "career_page": "https://pudurobotics.com/careers",
        "category": "service_robot"
    },
    {
        "name": "Agile Robots SE",
        "description": "humanoids and robot arms",
        "location": "Munich",
        "career_page": "https://agile-robots.com/careers",
        "category": "humanoid"
    },
    {
        "name": "Sereact",
        "description": "AI software that lets robots act on their own",
        "location": "Stuttgart",
        "career_page": "https://sereact.ai/careers",
        "category": "software"
    },
    {
        "name": "Flexion",
        "description": "autonomy software for humanoids",
        "location": "Zurich",
        "career_page": "https://flexion.ai/careers",
        "category": "software"
    },
    {
        "name": "Trener Robotics",
        "description": "intelligence layer for industrial robots",
        "location": "San Jose",
        "career_page": "https://trener.ai/careers",
        "category": "software"
    },
    {
        "name": "Unconventional AI",
        "description": "energy-efficient computers for AI",
        "location": "San Diego",
        "career_page": "https://unconv.ai/careers",
        "category": "compute_hardware"
    },
]


def cross_reference_with_db(companies_list: list[dict]) -> dict[str, Any]:
    """
    Cross-reference Grace Gong's list against our database.
    Returns coverage stats and new companies to add.
    """
    try:
        from app.database import SessionLocal
        from app.models.company import Company
        from sqlalchemy import select, or_
        
        db = SessionLocal()
        
        existing = set()
        new_companies = []
        
        for company in companies_list:
            name = company["name"]
            career_page = company["career_page"]
            
            # Check if company exists by name or career page domain
            domain = career_page.split("//")[1].split("/")[0] if "//" in career_page else career_page
            
            result = db.execute(
                select(Company).where(
                    or_(
                        Company.name.ilike(f"%{name}%"),
                        Company.website.ilike(f"%{domain}%")
                    )
                )
            ).first()
            
            if result:
                existing.add(name)
            else:
                new_companies.append(company)
        
        db.close()
        
        return {
            "total": len(companies_list),
            "existing": len(existing),
            "new": len(new_companies),
            "existing_companies": sorted(existing),
            "new_companies": new_companies,
            "coverage_pct": round(len(existing) / len(companies_list) * 100, 1)
        }
    
    except Exception as e:
        # Database not available - return structure for manual review
        return {
            "total": len(companies_list),
            "existing": "N/A - database not available",
            "new": "N/A - database not available",
            "existing_companies": [],
            "new_companies": companies_list,
            "coverage_pct": "N/A",
            "error": str(e)
        }


def generate_market_intelligence_report(cross_ref: dict) -> str:
    """Generate markdown report for market_thesis.md"""
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Category breakdown
    categories = {}
    for company in GRACE_GONG_WEEK_98:
        cat = company.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    # Geographic distribution
    locations = {}
    for company in GRACE_GONG_WEEK_98:
        loc = company.get("location", "Unknown")
        locations[loc] = locations.get(loc, 0) + 1
    
    report = f"""
## Grace Gong Physical AI Hiring List Intelligence ({timestamp})

**Source:** Grace Gong "On My Radar" Week 98 (LinkedIn)  
**Signal:** 36 physical AI companies actively hiring, ranked by % headcount growth (past 90 days)

### Strategic Value

This list represents **deployment-signal companies** — organizations scaling operations through active hiring. These are:
- **Potential employers** posting robot jobs (demand side)
- **Live deployment indicators** (companies hiring → companies deploying)
- **ICP alignment** (robot OEMs/integrators placing robots into work)

### Coverage Analysis

| Metric | Value |
|--------|-------|
| **Total companies** | {cross_ref["total"]} |
| **In RFR database** | {cross_ref["existing"]} |
| **New to monitor** | {cross_ref["new"]} |
| **Coverage %** | {cross_ref["coverage_pct"]}% |

### Category Breakdown

| Category | Count | % |
|----------|-------|---|
"""
    
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        pct = round(count / len(GRACE_GONG_WEEK_98) * 100, 1)
        report += f"| {cat.replace('_', ' ').title()} | {count} | {pct}% |\n"
    
    report += f"""
### Geographic Distribution

| Location | Count |
|----------|-------|
"""
    
    for loc, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]:
        report += f"| {loc} | {count} |\n"
    
    report += f"""
**Key observations:**
- **China concentration:** {sum(1 for c in GRACE_GONG_WEEK_98 if c['location'] in ['Beijing', 'Shenzhen'])} companies ({round(sum(1 for c in GRACE_GONG_WEEK_98 if c['location'] in ['Beijing', 'Shenzhen']) / len(GRACE_GONG_WEEK_98) * 100, 1)}%)
- **Bay Area cluster:** {sum(1 for c in GRACE_GONG_WEEK_98 if c['location'] in ['San Francisco', 'Sunnyvale', 'Redwood City', 'Palo Alto', 'San Mateo', 'Santa Clara'])} companies
- **Humanoid focus:** {categories.get('humanoid', 0)} pure-play humanoid companies + {sum(v for k, v in categories.items() if 'humanoid' in k.lower())} total humanoid-related

### Notable High-Growth Companies

**Foundation Models & AI Platform (deployment multiplier potential):**
"""
    
    foundation_companies = [c for c in GRACE_GONG_WEEK_98 if c.get("category") in ["foundation_model", "platform"]]
    for company in foundation_companies[:5]:
        report += f"- **{company['name']}** ({company['location']}) — {company['description']}\n"
    
    report += f"""
**Humanoid Platform Companies (ICP for Jobs product):**
"""
    
    humanoid_companies = [c for c in GRACE_GONG_WEEK_98 if "humanoid" in c.get("category", "")]
    for company in humanoid_companies[:5]:
        report += f"- **{company['name']}** ({company['location']}) — {company['description']}\n"
    
    report += f"""
**Industrial/Applied Robotics (job placement targets):**
"""
    
    industrial_companies = [c for c in GRACE_GONG_WEEK_98 if c.get("category") in ["industrial", "industrial_welding"]]
    for company in industrial_companies:
        report += f"- **{company['name']}** ({company['location']}) — {company['description']}\n"
    
    report += f"""
### Integration Recommendations

1. **Career Page Monitoring:** Add all 36 career pages to scraping rotation for job posting intelligence
2. **Deployment Evidence:** Track these companies for deployment announcements (they're scaling → they're deploying)
3. **Weekly Refresh:** Grace Gong publishes weekly — automate ingestion of future lists
4. **Company Profiles:** Enrich our database with category, growth signal, and hiring activity metadata

### Action Items

- [ ] Add new companies ({cross_ref["new"]}) to `companies` table with source tag `grace_gong_week_98`
- [ ] Create scraper targets for all 36 career pages
- [ ] Tag existing companies ({cross_ref["existing"]}) with hiring activity signal
- [ ] Set up weekly monitoring for Grace Gong's LinkedIn posts
- [ ] Cross-reference with our Jobs matching engine for placement opportunities

### New Companies to Add
"""
    
    if isinstance(cross_ref["new_companies"], list) and len(cross_ref["new_companies"]) > 0:
        for company in cross_ref["new_companies"][:20]:  # Show first 20
            report += f"""
**{company['name']}** ({company['location']})
- Description: {company['description']}
- Career page: {company['career_page']}
- Category: {company['category']}
"""
    else:
        report += "\n*All companies already in database or database check unavailable*\n"
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Ingest Grace Gong Physical AI Hiring List")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--apply", action="store_true", help="Apply changes to database")
    parser.add_argument("--output", default="reports/grace_gong_week_98_intelligence.md", help="Output report path")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("Must specify --dry-run or --apply")
        sys.exit(1)
    
    print(f"Grace Gong Physical AI Hiring List - Week 98")
    print(f"Total companies: {len(GRACE_GONG_WEEK_98)}")
    print()
    
    # Cross-reference with database
    print("Cross-referencing with database...")
    cross_ref = cross_reference_with_db(GRACE_GONG_WEEK_98)
    
    print(f"\nCoverage Analysis:")
    print(f"  Total companies: {cross_ref['total']}")
    print(f"  Already in database: {cross_ref['existing']}")
    print(f"  New to add: {cross_ref['new']}")
    if isinstance(cross_ref['coverage_pct'], (int, float)):
        print(f"  Coverage: {cross_ref['coverage_pct']}%")
    
    # Generate intelligence report
    print("\nGenerating market intelligence report...")
    report = generate_market_intelligence_report(cross_ref)
    
    # Write report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if args.dry_run:
        print(f"\n[DRY RUN] Would write report to: {output_path}")
        print("\n--- REPORT PREVIEW ---")
        print(report[:1000] + "\n...\n")
    else:
        output_path.write_text(report)
        print(f"\n✓ Report written to: {output_path}")
    
    # Export structured data
    json_path = output_path.with_suffix(".json")
    structured_data = {
        "source": "grace_gong_on_my_radar",
        "week": 98,
        "published_date": "2026-10-11",
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "companies": GRACE_GONG_WEEK_98,
        "cross_reference": cross_ref,
    }
    
    if args.dry_run:
        print(f"[DRY RUN] Would write structured data to: {json_path}")
    else:
        json_path.write_text(json.dumps(structured_data, indent=2))
        print(f"✓ Structured data written to: {json_path}")
    
    if args.apply:
        print("\nApplying changes to database...")
        # TODO: Implement database insertion logic
        print("  Database insertion not yet implemented - manual review recommended")
    
    print("\n✓ Intelligence ingestion complete")
    print(f"\nNext steps:")
    print(f"  1. Review report: cat {output_path}")
    print(f"  2. Update docs/market_thesis.md with intelligence section")
    print(f"  3. Add new companies to monitoring/scraping targets")
    print(f"  4. Set up weekly Grace Gong LinkedIn monitoring")


if __name__ == "__main__":
    main()
