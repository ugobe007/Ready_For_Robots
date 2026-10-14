"""
Grace Gong Physical AI Hiring List - Career Page Monitoring Config

Source: Grace Gong "On My Radar" Week 98 (October 2026)
Signal: Companies with highest % headcount growth in past 90 days

These career pages should be scraped regularly for:
1. Job posting intelligence (what roles are they hiring for?)
2. Deployment signals (hiring indicates scaling/deploying)
3. Market movement (growth velocity in physical AI space)

Recommended scrape frequency: Weekly (aligns with Grace Gong's weekly posts)
"""

GRACE_GONG_WEEK_98_CAREER_PAGES = [
    # Foundation Model Companies (8) - Deployment multiplier potential
    {
        "company": "Skild AI",
        "url": "https://skild.ai/careers",
        "location": "Pittsburgh",
        "category": "foundation_model",
        "priority": "high",  # One brain → many robots = high placement multiplier
    },
    {
        "company": "X Square Robot",
        "url": "https://x2robot.com/careers",
        "location": "Shenzhen",
        "category": "foundation_model",
        "priority": "medium",
    },
    {
        "company": "XDOF",
        "url": "https://xdof.com/careers",
        "location": "San Mateo",
        "category": "foundation_model",
        "priority": "high",
    },
    {
        "company": "ShengShu",
        "url": "https://shengshu-ai.com/careers",
        "location": "Beijing",
        "category": "foundation_model",
        "priority": "medium",
    },
    {
        "company": "Physical Intelligence",
        "url": "https://physicalintelligence.company/careers",
        "location": "San Francisco",
        "category": "foundation_model",
        "priority": "high",  # Bay Area + foundation model = high visibility
    },
    {
        "company": "Dyna Robotics",
        "url": "https://dyna.co/careers",
        "location": "Redwood City",
        "category": "foundation_model",
        "priority": "high",
    },
    {
        "company": "Rhoda AI",
        "url": "https://rhoda.ai/careers",
        "location": "Palo Alto",
        "category": "foundation_model",
        "priority": "high",
    },
    {
        "company": "Generalist",
        "url": "https://generalist.ai/careers",
        "location": "San Mateo",
        "category": "foundation_model",
        "priority": "high",
    },
    
    # Humanoid Companies (9) - Direct ICP for Jobs product
    {
        "company": "Booster Robotics",
        "url": "https://booster.tech/careers",
        "location": "Beijing",
        "category": "humanoid",
        "priority": "high",  # Developer platform = multiple deployment targets
    },
    {
        "company": "EngineAI",
        "url": "https://engineai.com.cn/careers",
        "location": "Shenzhen",
        "category": "humanoid",
        "priority": "medium",
    },
    {
        "company": "Figure",
        "url": "https://figure.ai/careers",
        "location": "Sunnyvale",
        "category": "humanoid",
        "priority": "critical",  # High-profile, well-funded, active deployments
    },
    {
        "company": "Sharpa",
        "url": "https://sharpa.com/careers",
        "location": "Singapore",
        "category": "humanoid",
        "priority": "medium",
    },
    {
        "company": "LimX Dynamics",
        "url": "https://limxdynamics.com/careers",
        "location": "Shenzhen",
        "category": "humanoid",
        "priority": "high",
    },
    {
        "company": "Apptronik",
        "url": "https://apptronik.com/careers",
        "location": "Austin",
        "category": "humanoid",
        "priority": "critical",  # Apollo partnership with Mercedes = live deployments
    },
    {
        "company": "Humanoid",
        "url": "https://thehumanoid.ai/careers",
        "location": "London",
        "category": "humanoid",
        "priority": "medium",
    },
    {
        "company": "Magiclab Robotics",
        "url": "https://magiclab.top/careers",
        "location": "Beijing",
        "category": "humanoid",
        "priority": "medium",
    },
    {
        "company": "Generative Bionics",
        "url": "https://gbionics.ai/careers",
        "location": "Genoa",
        "category": "humanoid",
        "priority": "low",
    },
    
    # Industrial/Applied Robotics (4) - Direct job placement targets
    {
        "company": "Maven Robotics",
        "url": "https://mavenrobotics.ai/careers",
        "location": "Santa Clara",
        "category": "industrial",
        "priority": "high",
    },
    {
        "company": "Tutor",
        "url": "https://tutorintelligence.com/careers",
        "location": "Watertown",
        "category": "industrial",
        "priority": "high",  # Warehouse/factory focus = clear job categories
    },
    {
        "company": "Path Robotics",
        "url": "https://path-robotics.com/careers",
        "location": "Columbus",
        "category": "industrial_welding",
        "priority": "critical",  # Specific vertical (welding) = clear job matching
    },
    {
        "company": "Standard Bots",
        "url": "https://standardbots.com/careers",
        "location": "Glen Cove",
        "category": "industrial",
        "priority": "high",
    },
    
    # Software/Platform Companies (3) - Enablement layer
    {
        "company": "Sereact",
        "url": "https://sereact.ai/careers",
        "location": "Stuttgart",
        "category": "software",
        "priority": "medium",
    },
    {
        "company": "Flexion",
        "url": "https://flexion.ai/careers",
        "location": "Zurich",
        "category": "software",
        "priority": "medium",
    },
    {
        "company": "Trener Robotics",
        "url": "https://trener.ai/careers",
        "location": "San Jose",
        "category": "software",
        "priority": "medium",
    },
    
    # Other Categories
    {
        "company": "Sunday",
        "url": "https://sunday.ai/careers",
        "location": "Redwood City",
        "category": "home_robot",
        "priority": "medium",
    },
    {
        "company": "Scout AI",
        "url": "https://scoutai.com/careers",
        "location": "Sunnyvale",
        "category": "defense",
        "priority": "low",  # Defense = less public job data
    },
    {
        "company": "ROBOTERA",
        "url": "https://robotera.com/careers",
        "location": "Beijing",
        "category": "embodied_ai",
        "priority": "medium",
    },
    {
        "company": "NEURA Robotics",
        "url": "https://neura-robotics.com/careers",
        "location": "Metzingen",
        "category": "collaborative",
        "priority": "medium",
    },
    {
        "company": "RLWRLD",
        "url": "https://rlwrld.ai/careers",
        "location": "Seoul",
        "category": "end_effector",
        "priority": "low",
    },
    {
        "company": "VinMotion",
        "url": "https://vinmotion.com/careers",
        "location": "US",
        "category": "deployment_tools",
        "priority": "medium",
    },
    {
        "company": "General Robotics",
        "url": "https://generalrobotics.ai/careers",
        "location": "Redmond",
        "category": "platform",
        "priority": "medium",
    },
    {
        "company": "Galbot",
        "url": "https://galbot.com/careers",
        "location": "Beijing",
        "category": "embodied_ai",
        "priority": "medium",
    },
    {
        "company": "Waabi",
        "url": "https://waabi.ai/careers",
        "location": "Toronto",
        "category": "autonomous_vehicles",
        "priority": "medium",
    },
    {
        "company": "Pudu Robotics",
        "url": "https://pudurobotics.com/careers",
        "location": "Shenzhen",
        "category": "service_robot",
        "priority": "medium",
    },
    {
        "company": "Agile Robots SE",
        "url": "https://agile-robots.com/careers",
        "location": "Munich",
        "category": "humanoid",
        "priority": "high",
    },
    {
        "company": "Unconventional AI",
        "url": "https://unconv.ai/careers",
        "location": "San Diego",
        "category": "compute_hardware",
        "priority": "low",
    },
]


def get_high_priority_targets():
    """Return career pages marked as high or critical priority."""
    return [
        entry for entry in GRACE_GONG_WEEK_98_CAREER_PAGES
        if entry.get("priority") in ["high", "critical"]
    ]


def get_by_category(category: str):
    """Return career pages filtered by category."""
    return [
        entry for entry in GRACE_GONG_WEEK_98_CAREER_PAGES
        if entry.get("category") == category
    ]


def get_by_location(location: str):
    """Return career pages filtered by location."""
    return [
        entry for entry in GRACE_GONG_WEEK_98_CAREER_PAGES
        if entry.get("location") == location
    ]


if __name__ == "__main__":
    print(f"Total career pages: {len(GRACE_GONG_WEEK_98_CAREER_PAGES)}")
    print(f"High priority targets: {len(get_high_priority_targets())}")
    print(f"\nHumanoid companies: {len(get_by_category('humanoid'))}")
    print(f"Foundation model companies: {len(get_by_category('foundation_model'))}")
    print(f"Industrial companies: {len([e for e in GRACE_GONG_WEEK_98_CAREER_PAGES if 'industrial' in e.get('category', '')])}")
    print(f"\nBay Area companies: {len([e for e in GRACE_GONG_WEEK_98_CAREER_PAGES if e.get('location') in ['San Francisco', 'Sunnyvale', 'Redwood City', 'Palo Alto', 'San Mateo', 'Santa Clara']])}")
    print(f"China companies: {len([e for e in GRACE_GONG_WEEK_98_CAREER_PAGES if e.get('location') in ['Beijing', 'Shenzhen']])}")
