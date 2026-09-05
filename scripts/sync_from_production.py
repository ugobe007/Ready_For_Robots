"""
Sync lead data from production to local database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score

def sync_from_production():
    """Fetch leads from production API and sync to local database"""
    
    print("🔄 Syncing data from production...")
    
    # Fetch leads from production
    response = requests.get('https://ready-2-robot.fly.dev/api/leads')
    production_leads = response.json()
    
    print(f"📊 Found {len(production_leads)} leads in production")
    
    db = SessionLocal()
    
    try:
        # Get existing companies to avoid duplicates
        existing = {c.name.lower() for c in db.query(Company.name).all()}
        print(f"📦 Local database has {len(existing)} companies")
        
        added = 0
        skipped = 0
        
        for lead in production_leads:
            company_name = lead.get('company_name') or lead.get('name')
            if not company_name:
                continue
                
            # Skip if already exists
            if company_name.lower() in existing:
                skipped += 1
                continue
            
            # Create company
            company = Company(
                name=company_name,
                website=lead.get('website'),
                industry=lead.get('industry'),
                employee_estimate=lead.get('employee_estimate'),
                location_city=lead.get('location_city'),
                location_state=lead.get('location_state'),
                location_country=lead.get('location_country'),
                source=lead.get('source', 'production_sync')
            )
            db.add(company)
            db.flush()  # Get the company ID
            
            # Add signals if available
            if lead.get('signals'):
                for sig_data in lead['signals']:
                    signal = Signal(
                        company_id=company.id,
                        signal_type=sig_data.get('signal_type', 'unknown'),
                        signal_text=sig_data.get('description') or sig_data.get('signal_text', 'Signal detected'),
                        signal_strength=sig_data.get('strength') or sig_data.get('signal_strength', 0.5),
                        source_url=sig_data.get('source_url')
                    )
                    db.add(signal)
            
            # Add score if available
            if lead.get('score'):
                score_data = lead['score']
                if isinstance(score_data, dict):
                    score = Score(
                        company_id=company.id,
                        automation_score=score_data.get('automation_score', 0),
                        labor_pain_score=score_data.get('labor_pain_score', 0),
                        expansion_score=score_data.get('expansion_score', 0),
                        robotics_fit_score=score_data.get('robotics_fit_score') or score_data.get('market_fit_score', 0),
                        overall_intent_score=score_data.get('overall_intent_score') or score_data.get('overall_score', 0)
                    )
                    db.add(score)
            
            added += 1
            
            if added % 10 == 0:
                print(f"  ✓ Added {added} companies...")
        
        db.commit()
        
        print(f"\n✅ Sync complete!")
        print(f"  • Added: {added} new companies")
        print(f"  • Skipped: {skipped} existing companies")
        print(f"  • Total in local DB: {len(existing) + added}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    sync_from_production()
