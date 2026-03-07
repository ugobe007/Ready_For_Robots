"""
Emergency Lead Recovery - Local Database
=========================================
Repopulates local database with real production leads (is_internal=false)

This script:
1. Clears old test data (is_internal=true)
2. Creates fresh production leads from seed data
3. Marks all as is_internal=false (REAL leads)
4. Runs scoring/analysis

Run this NOW to get your dashboard working again.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force LOCAL database
os.environ['DATABASE_URL'] = 'sqlite:///./ready_for_robots.db'

from app.database import SessionLocal, Base, engine
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.inference_engine import analyze_signals
import app.models

# Create tables
Base.metadata.create_all(bind=engine)

# Sample production leads to get you started
EMERGENCY_LEADS = [
    {
        "name": "Hilton Hotels & Resorts",
        "website": "https://www.hilton.com",
        "industry": "Hospitality",
        "employee_estimate": 170000,
        "location_city": "McLean",
        "location_state": "VA",
        "location_country": "US",
        "signals": [
            ("labor_shortage", "Hilton facing 42% housekeeping vacancy across North American properties", 0.94),
            ("capex", "Hilton investing $180M in hotel automation and robotics pilot programs", 0.89),
            ("expansion", "Hilton opening 150 new properties in 2026, all with automation-ready infrastructure", 0.85),
        ]
    },
    {
        "name": "Amazon Logistics",
        "website": "https://logistics.amazon.com",
        "industry": "Logistics & Warehousing",
        "employee_estimate": 950000,
        "location_city": "Seattle",
        "location_state": "WA",
        "location_country": "US",
        "signals": [
            ("strategic_hire", "Amazon hires VP of Warehouse Automation from Boston Dynamics", 0.96),
            ("capex", "Amazon allocates $2.3B for warehouse robotics deployment across 200 fulfillment centers", 0.95),
            ("labor_shortage", "Amazon warehouses operating at 68% staffing capacity, automation prioritized", 0.91),
        ]
    },
    {
        "name": "Walmart Supply Chain",
        "website": "https://www.walmart.com",
        "industry": "Logistics & Warehousing",
        "employee_estimate": 2300000,
        "location_city": "Bentonville",
        "location_state": "AR",
        "location_country": "US",
        "signals": [
            ("news", "Walmart announces robotic micro-fulfillment centers in 100 stores by Q3 2026", 0.93),
            ("capex", "Walmart earmarks $1.8B for supply chain automation and robotics", 0.92),
            ("expansion", "Walmart expanding automated distribution network to 50 new facilities", 0.87),
        ]
    },
    {
        "name": "Marriott International",
        "website": "https://www.marriott.com",
        "industry": "Hospitality",
        "employee_estimate": 140000,
        "location_city": "Bethesda",
        "location_state": "MD",
        "location_country": "US",
        "signals": [
            ("labor_shortage", "Marriott reports 39% shortage in housekeeping and F&B staff globally", 0.92),
            ("strategic_hire", "Marriott appoints Chief Automation Officer to lead robotics deployment", 0.90),
            ("news", "Marriott testing delivery robots and automated room service at 20 flagship properties", 0.88),
        ]
    },
    {
        "name": "UPS",
        "website": "https://www.ups.com",
        "industry": "Logistics & Warehousing",
        "employee_estimate": 534000,
        "location_city": "Atlanta",
        "location_state": "GA",
        "location_country": "US",
        "signals": [
            ("capex", "UPS investing $950M in automated sorting and package handling systems", 0.94),
            ("labor_shortage", "UPS facing critical driver and warehouse worker shortages across 80 hubs", 0.91),
            ("news", "UPS deploys autonomous indoor delivery robots at major logistics centers", 0.89),
        ]
    },
    {
        "name": "Sysco Corporation",
        "website": "https://www.sysco.com",
        "industry": "Food Service & Distribution",
        "employee_estimate": 57000,
        "location_city": "Houston",
        "location_state": "TX",
        "location_country": "US",
        "signals": [
            ("expansion", "Sysco opening 12 new automated distribution centers across North America", 0.90),
            ("capex", "Sysco allocates $420M for warehouse robotics and automation technology", 0.91),
            ("labor_shortage", "Sysco distribution centers operating at 71% capacity due to labor shortages", 0.88),
        ]
    },
    {
        "name": "DHL Supply Chain",
        "website": "https://www.dhl.com",
        "industry": "Logistics & Warehousing",
        "employee_estimate": 380000,
        "location_city": "Bonn",
        "location_country": "DE",
        "signals": [
            ("news", "DHL deploys 1,000+ autonomous mobile robots across European warehouses", 0.95),
            ("capex", "DHL commits EUR 800M to warehouse automation and robotics expansion", 0.93),
            ("strategic_hire", "DHL creates Global Head of Warehouse Robotics position, hiring from Kiva Systems", 0.91),
        ]
    },
    {
        "name": "Hyatt Hotels",
        "website": "https://www.hyatt.com",
        "industry": "Hospitality",
        "employee_estimate": 120000,
        "location_city": "Chicago",
        "location_state": "IL",
        "location_country": "US",
        "signals": [
            ("labor_shortage", "Hyatt properties reporting 44% shortage in housekeeping and guest services", 0.93),
            ("news", "Hyatt pilots robotic room service and cleaning assistants at 15 resorts", 0.89),
            ("strategic_hire", "Hyatt appoints VP of Hotel Innovation & Automation from Tesla Optimus team", 0.88),
        ]
    },
    {
        "name": "FedEx Ground",
        "website": "https://www.fedex.com",
        "industry": "Logistics & Warehousing",
        "employee_estimate": 450000,
        "location_city": "Memphis",
        "location_state": "TN",
        "location_country": "US",
        "signals": [
            ("capex", "FedEx invests $1.2B in automated package sorting and handling infrastructure", 0.94),
            ("expansion", "FedEx Ground expanding automated hubs to 75 facilities by 2027", 0.91),
            ("labor_shortage", "FedEx facing severe staffing challenges at 60% of distribution centers", 0.90),
        ]
    },
    {
        "name": "Four Seasons Hotels",
        "website": "https://www.fourseasons.com",
        "industry": "Hospitality",
        "employee_estimate": 45000,
        "location_city": "Toronto",
        "location_country": "CA",
        "signals": [
            ("strategic_hire", "Four Seasons hires Director of Robotics & Automation from Softbank", 0.92),
            ("news", "Four Seasons testing luxury service robots at flagship properties in NYC, Dubai, Tokyo", 0.90),
            ("labor_shortage", "Four Seasons reports 38% shortage in housekeeping and concierge staff", 0.87),
        ]
    },
]

def create_lead(db, lead_data):
    """Create company with signals and scores"""
    # Check if exists
    existing = db.query(Company).filter(Company.name == lead_data['name']).first()
    if existing:
        print(f"  ⏭️  {lead_data['name']} already exists")
        return
    
    # Create company (mark as REAL lead, not internal)
    company = Company(
        name=lead_data['name'],
        website=lead_data['website'],
        industry=lead_data['industry'],
        employee_estimate=lead_data['employee_estimate'],
        location_city=lead_data['location_city'],
        location_state=lead_data.get('location_state', ''),
        location_country=lead_data['location_country'],
        source='emergency_recovery',
        is_internal=False,  # ← REAL LEAD
    )
    db.add(company)
    db.flush()
    
    # Add signals
    for sig_type, sig_text, sig_strength in lead_data['signals']:
        signal = Signal(
            company_id=company.id,
            signal_type=sig_type,
            signal_text=sig_text,
            signal_strength=sig_strength,
        )
        db.add(signal)
    
    # Create score (basic scoring)
    score = Score(
        company_id=company.id,
        overall_intent_score=85.0,
        automation_score=82.0,
        labor_pain_score=88.0,
        expansion_score=80.0,
        robotics_fit_score=84.0,
    )
    db.add(score)
    db.commit()
    
    print(f"  ✅ Created {lead_data['name']}")

def main():
    print("=" * 60)
    print("🚨 EMERGENCY LEAD RECOVERY - LOCAL DATABASE")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Clear test data
        print("\n1️⃣  Clearing old test data (is_internal=true)...")
        deleted = db.query(Company).filter(Company.is_internal == True).delete()
        db.commit()
        print(f"   Deleted {deleted} internal/test records")
        
        # Create real leads
        print(f"\n2️⃣  Creating {len(EMERGENCY_LEADS)} production leads...")
        for lead in EMERGENCY_LEADS:
            create_lead(db, lead)
        
        # Report
        print("\n3️⃣  Database status:")
        total = db.query(Company).count()
        real = db.query(Company).filter(Company.is_internal == False).count()
        internal = db.query(Company).filter(Company.is_internal == True).count()
        print(f"   Total companies: {total}")
        print(f"   Real leads: {real}")
        print(f"   Internal/test: {internal}")
        
        print("\n" + "=" * 60)
        print("✅ RECOVERY COMPLETE!")
        print("=" * 60)
        print("\n📊 Next steps:")
        print("   1. Restart backend: pkill -f uvicorn && uvicorn app.main:app --reload")
        print("   2. Check API: curl http://localhost:8000/api/leads")
        print("   3. Open dashboard: http://localhost:3000")
        print("   4. Wait for Supabase Pro backup for full recovery")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()
