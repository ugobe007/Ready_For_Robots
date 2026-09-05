"""Test Robot Companies API"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.robot_company import RobotCompany

db = SessionLocal()

# Test stats
total = db.query(RobotCompany).count()
chinese = db.query(RobotCompany).filter(RobotCompany.country == "China").count()
hot_leads = db.query(RobotCompany).filter(RobotCompany.priority_tier == "hot").count()
needs_dist = db.query(RobotCompany).filter(RobotCompany.distributor_needed == "yes").count()
no_us = db.query(RobotCompany).filter(RobotCompany.us_presence == "none").count()

print(f"\n📊 ROBOT COMPANY DATABASE STATS")
print(f"{'='*50}")
print(f"Total Companies: {total}")
print(f"Chinese Companies: {chinese}")
print(f"Hot Leads (priority_tier='hot'): {hot_leads}")
print(f"Needs Distribution: {needs_dist}")
print(f"No U.S. Presence: {no_us}")

# Test hot leads
print(f"\n🔥 HOT LEADS (score >= 80)")
print(f"{'='*50}")
hot_companies = db.query(RobotCompany).filter(
    RobotCompany.priority_tier == "hot",
    RobotCompany.lead_score >= 80
).order_by(RobotCompany.lead_score.desc()).all()

for comp in hot_companies:
    print(f"{comp.lead_score:3d} - {comp.company_name:25s} ({comp.robot_type:10s}) - {comp.market_entry_wave}")

# Test Chinese companies without U.S. presence
print(f"\n🇨🇳 CHINESE COMPANIES NEEDING U.S. MARKET ENTRY")
print(f"{'='*50}")
no_presence = db.query(RobotCompany).filter(
    RobotCompany.country == "China",
    RobotCompany.us_presence == "none"
).order_by(RobotCompany.lead_score.desc()).all()

for comp in no_presence[:10]:
    urgency = comp.distributor_urgency or "unknown"
    print(f"{comp.lead_score:3d} - {comp.company_name:25s} - Urgency: {urgency:6s} - {comp.partnership_opportunity[:50]}")

# Test by robot type
print(f"\n🤖 COMPANIES BY ROBOT TYPE")
print(f"{'='*50}")
robot_types = db.query(RobotCompany.robot_type).distinct().all()
for (robot_type,) in robot_types:
    if robot_type:
        count = db.query(RobotCompany).filter(RobotCompany.robot_type == robot_type).count()
        print(f"{robot_type:15s}: {count:2d} companies")

# Test market entry waves
print(f"\n🌊 MARKET ENTRY WAVES")
print(f"{'='*50}")
wave_1 = db.query(RobotCompany).filter(RobotCompany.market_entry_wave == "wave_1").count()
wave_2 = db.query(RobotCompany).filter(RobotCompany.market_entry_wave == "wave_2").count()
wave_3 = db.query(RobotCompany).filter(RobotCompany.market_entry_wave == "wave_3").count()

print(f"Wave 1 (2020-2024 Established): {wave_1}")
print(f"Wave 2 (2024-2026 Expanding):  {wave_2} ⭐ HOTTEST")
print(f"Wave 3 (2025-2027 Emerging):   {wave_3}")

db.close()
print(f"\n✅ Database test complete!")
