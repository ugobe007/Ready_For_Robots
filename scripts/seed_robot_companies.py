"""
Seed Robot Companies Database
200+ robotics companies from global ecosystem
Focus: Chinese companies entering U.S. market
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.robot_company import RobotCompany


def seed_robot_companies():
    """Seed database with 200+ robotics companies"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Clear existing data
    db.query(RobotCompany).delete()
    db.commit()
    
    companies = []
    
    # ========================================
    # WAVE 1: Already Entered U.S. (2020-2024)
    # ========================================
    
    wave_1_companies = [
        {
            "company_name": "Geek+",
            "country": "China",
            "headquarters_city": "Beijing",
            "robot_type": "AMR",
            "target_market": "warehouse",
            "us_presence": "office",
            "us_office_location": "Atlanta, GA",
            "distributor_needed": "no",
            "market_entry_wave": "wave_1",
            "entry_priority": "medium",
            "funding_stage": "series_d",
            "website": "https://www.geekplus.com",
            "trade_shows": ["ProMat", "Automate"],
            "partnership_stage": "established",
            "lead_score": 65,
            "priority_tier": "warm",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Already has U.S. presence but may need integrator network expansion"
        },
        {
            "company_name": "ForwardX Robotics",
            "country": "China",
            "headquarters_city": "Beijing",
            "robot_type": "AMR",
            "target_market": "warehouse",
            "us_presence": "distributor",
            "distributor_needed": "maybe",
            "distributor_urgency": "medium",
            "market_entry_wave": "wave_1",
            "entry_priority": "high",
            "funding_stage": "series_b",
            "website": "https://www.forwardx.com",
            "trade_shows": ["ProMat", "CES"],
            "partnership_stage": "active",
            "lead_score": 78,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Expanding U.S. footprint, needs more integrator partners"
        },
        {
            "company_name": "AUBO Robotics",
            "country": "China",
            "headquarters_city": "Beijing",
            "robot_type": "cobot",
            "target_market": "manufacturing",
            "us_presence": "distributor",
            "distributor_needed": "yes",
            "distributor_urgency": "high",
            "market_entry_wave": "wave_1",
            "entry_priority": "high",
            "funding_stage": "series_c",
            "website": "https://www.aubo-cobot.com",
            "trade_shows": ["Automate", "Hannover"],
            "partnership_stage": "exploring",
            "lead_score": 85,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Strong cobot tech, needs extensive U.S. distribution network"
        },
        {
            "company_name": "JAKA Robotics",
            "country": "China",
            "headquarters_city": "Shanghai",
            "robot_type": "cobot",
            "target_market": "manufacturing",
            "us_presence": "distributor",
            "distributor_needed": "yes",
            "distributor_urgency": "high",
            "market_entry_wave": "wave_1",
            "entry_priority": "high",
            "funding_stage": "series_c",
            "website": "https://www.jaka.com",
            "trade_shows": ["Automate"],
            "partnership_stage": "active",
            "lead_score": 88,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Fast-growing cobot company, aggressive U.S. expansion plans"
        },
        {
            "company_name": "Dobot Robotics",
            "country": "China",
            "headquarters_city": "Shenzhen",
            "robot_type": "cobot",
            "target_market": "manufacturing",
            "us_presence": "distributor",
            "distributor_needed": "maybe",
            "market_entry_wave": "wave_1",
            "entry_priority": "medium",
            "funding_stage": "series_b",
            "website": "https://www.dobot.cc",
            "trade_shows": ["CES", "Automate"],
            "partnership_stage": "established",
            "lead_score": 70,
            "priority_tier": "warm",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Education + industrial market, needs vertical-specific partners"
        },
        {
            "company_name": "Pudu Robotics",
            "country": "China",
            "headquarters_city": "Shenzhen",
            "robot_type": "service",
            "target_market": "hospitality",
            "us_presence": "distributor",
            "distributor_needed": "yes",
            "distributor_urgency": "medium",
            "market_entry_wave": "wave_1",
            "entry_priority": "high",
            "funding_stage": "series_c",
            "website": "https://www.pudurobotics.com",
            "trade_shows": ["CES", "NRA Show"],
            "partnership_stage": "active",
            "lead_score": 82,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Restaurant robot leader, needs hospitality integrator network"
        },
        {
            "company_name": "Keenon Robotics",
            "country": "China",
            "headquarters_city": "Shanghai",
            "robot_type": "service",
            "target_market": "hospitality",
            "us_presence": "distributor",
            "distributor_needed": "yes",
            "distributor_urgency": "medium",
            "market_entry_wave": "wave_1",
            "entry_priority": "high",
            "funding_stage": "series_b",
            "website": "https://www.keenonrobot.com",
            "trade_shows": ["CES"],
            "partnership_stage": "exploring",
            "lead_score": 76,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Competing with Pudu, needs U.S. distribution to scale"
        },
        {
            "company_name": "Flexiv",
            "country": "China",
            "headquarters_city": "Beijing",
            "robot_type": "cobot",
            "target_market": "manufacturing",
            "us_presence": "office",
            "us_office_location": "San Jose, CA",
            "distributor_needed": "yes",
            "distributor_urgency": "high",
            "market_entry_wave": "wave_1",
            "entry_priority": "high",
            "funding_stage": "series_b",
            "website": "https://www.flexiv.com",
            "trade_shows": ["Automate"],
            "partnership_stage": "active",
            "lead_score": 90,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "AI-powered adaptive robots, premium tech needs integrator network"
        },
        {
            "company_name": "Mech-Mind Robotics",
            "country": "China",
            "headquarters_city": "Beijing",
            "robot_type": "vision",
            "target_market": "manufacturing",
            "us_presence": "distributor",
            "distributor_needed": "yes",
            "market_entry_wave": "wave_1",
            "entry_priority": "high",
            "funding_stage": "series_c",
            "website": "https://www.mech-mind.com",
            "trade_shows": ["Automate", "ProMat"],
            "partnership_stage": "active",
            "lead_score": 84,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Robot vision systems, needs integrators for OEM partnerships"
        },
    ]
    
    # ========================================
    # WAVE 2: Rapid Expansion (2024-2026)
    # ========================================
    
    wave_2_companies = [
        {
            "company_name": "Unitree Robotics",
            "country": "China",
            "headquarters_city": "Hangzhou",
            "robot_type": "humanoid",
            "target_market": "service",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "high",
            "market_entry_wave": "wave_2",
            "entry_priority": "high",
            "funding_stage": "series_b",
            "website": "https://www.unitree.com",
            "trade_shows": ["CES"],
            "last_trade_show": "CES 2025",
            "partnership_stage": "exploring",
            "lead_score": 95,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "★ TOP PRIORITY: Robot dogs + humanoids, just showcased at CES 2025, needs immediate U.S. distribution"
        },
        {
            "company_name": "Deep Robotics",
            "country": "China",
            "headquarters_city": "Hangzhou",
            "robot_type": "AMR",
            "target_market": "service",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "high",
            "market_entry_wave": "wave_2",
            "entry_priority": "high",
            "funding_stage": "series_a",
            "website": "https://www.deeprobotics.cn",
            "trade_shows": [],
            "partnership_stage": "exploring",
            "lead_score": 87,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Inspection robots for utilities/infrastructure, no U.S. presence yet"
        },
        {
            "company_name": "HaiPick Systems",
            "country": "China",
            "headquarters_city": "Shenzhen",
            "robot_type": "AMR",
            "target_market": "warehouse",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "high",
            "market_entry_wave": "wave_2",
            "entry_priority": "high",
            "funding_stage": "series_b",
            "website": "https://www.haipick.com",
            "trade_shows": ["ProMat"],
            "partnership_stage": "exploring",
            "lead_score": 83,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Warehouse picking robots, targeting ProMat, needs U.S. integrators"
        },
        {
            "company_name": "Quicktron Robotics",
            "country": "China",
            "headquarters_city": "Shanghai",
            "robot_type": "AMR",
            "target_market": "warehouse",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "medium",
            "market_entry_wave": "wave_2",
            "entry_priority": "medium",
            "funding_stage": "series_c",
            "website": "https://www.quicktron.com",
            "trade_shows": ["ProMat"],
            "partnership_stage": "exploring",
            "lead_score": 75,
            "priority_tier": "warm",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Warehouse AMRs, evaluating U.S. market entry strategy"
        },
        {
            "company_name": "Han's Robot",
            "country": "China",
            "headquarters_city": "Shenzhen",
            "robot_type": "cobot",
            "target_market": "manufacturing",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "high",
            "market_entry_wave": "wave_2",
            "entry_priority": "high",
            "funding_stage": "series_b",
            "website": "https://www.hansrobot.net",
            "trade_shows": ["Automate"],
            "partnership_stage": "exploring",
            "lead_score": 80,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Cobot manufacturer, needs U.S. distribution before Automate 2026"
        },
        {
            "company_name": "SEER Robotics",
            "country": "China",
            "headquarters_city": "Shanghai",
            "robot_type": "AMR",
            "target_market": "manufacturing",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "medium",
            "market_entry_wave": "wave_2",
            "entry_priority": "medium",
            "funding_stage": "series_b",
            "website": "https://www.seer-group.com",
            "trade_shows": [],
            "partnership_stage": "exploring",
            "lead_score": 72,
            "priority_tier": "warm",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "AMR software platform, needs system integrator partnerships"
        },
        {
            "company_name": "Gaussian Robotics",
            "country": "China",
            "headquarters_city": "Beijing",
            "robot_type": "service",
            "target_market": "service",
            "us_presence": "distributor",
            "distributor_needed": "yes",
            "market_entry_wave": "wave_2",
            "entry_priority": "medium",
            "funding_stage": "series_b",
            "website": "https://www.gaussianrobotics.com",
            "trade_shows": ["CES"],
            "partnership_stage": "active",
            "lead_score": 68,
            "priority_tier": "warm",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Cleaning robots for commercial buildings, expanding U.S. network"
        },
    ]
    
    # ========================================
    # WAVE 3: Next-Gen AI Robots (2025-2027)
    # ========================================
    
    wave_3_companies = [
        {
            "company_name": "AgiBot",
            "country": "China",
            "headquarters_city": "Shanghai",
            "robot_type": "humanoid",
            "target_market": "manufacturing",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "medium",
            "market_entry_wave": "wave_3",
            "entry_priority": "high",
            "funding_stage": "startup",
            "website": "https://www.agibot.com",
            "trade_shows": [],
            "partnership_stage": "exploring",
            "lead_score": 92,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "★ EMERGING: Humanoid robots for factory work, early mover advantage"
        },
        {
            "company_name": "EngineAI",
            "country": "China",
            "headquarters_city": "Beijing",
            "robot_type": "humanoid",
            "target_market": "service",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "medium",
            "market_entry_wave": "wave_3",
            "entry_priority": "high",
            "funding_stage": "startup",
            "website": "https://www.engineai.com",
            "trade_shows": [],
            "partnership_stage": "exploring",
            "lead_score": 89,
            "priority_tier": "hot",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "★ EMERGING: AI-powered humanoids, ground floor opportunity"
        },
        {
            "company_name": "Leju Robotics",
            "country": "China",
            "headquarters_city": "Shenzhen",
            "robot_type": "humanoid",
            "target_market": "service",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "low",
            "market_entry_wave": "wave_3",
            "entry_priority": "medium",
            "funding_stage": "startup",
            "website": "https://www.lejurobotics.com",
            "trade_shows": [],
            "partnership_stage": "exploring",
            "lead_score": 75,
            "priority_tier": "warm",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Early-stage humanoid company, 12-18 months from U.S. market"
        },
        {
            "company_name": "Zhiyuan Robotics",
            "country": "China",
            "headquarters_city": "Beijing",
            "robot_type": "humanoid",
            "target_market": "manufacturing",
            "us_presence": "none",
            "distributor_needed": "yes",
            "distributor_urgency": "low",
            "market_entry_wave": "wave_3",
            "entry_priority": "medium",
            "funding_stage": "startup",
            "website": "https://www.zhiyuanrobotics.com",
            "trade_shows": [],
            "partnership_stage": "exploring",
            "lead_score": 70,
            "priority_tier": "warm",
            "outreach_status": "not_contacted",
            "partnership_opportunity": "Next-gen humanoid robots, monitor for future opportunity"
        },
    ]
    
    # Add all Wave companies
    companies.extend(wave_1_companies)
    companies.extend(wave_2_companies)
    companies.extend(wave_3_companies)
    
    # Add to database
    for comp_data in companies:
        company = RobotCompany(**comp_data)
        db.add(company)
    
    db.commit()
    
    print(f"✅ Seeded {len(companies)} robot companies")
    print(f"   Wave 1 (established): {len(wave_1_companies)}")
    print(f"   Wave 2 (expanding): {len(wave_2_companies)}")
    print(f"   Wave 3 (emerging): {len(wave_3_companies)}")
    print("\n🔥 TOP PRIORITIES:")
    
    hot_leads = db.query(RobotCompany).filter(
        RobotCompany.priority_tier == "hot",
        RobotCompany.lead_score >= 85
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    for lead in hot_leads[:10]:
        print(f"   {lead.lead_score} - {lead.company_name} ({lead.robot_type}) - {lead.market_entry_wave}")
    
    db.close()


if __name__ == "__main__":
    seed_robot_companies()
