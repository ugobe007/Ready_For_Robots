"""
Quick Data Recovery Script
==========================
Rebuilds lead pipeline by running seed scripts against LOCAL database.
Use this to quickly recover data while waiting for Supabase backup access.

Usage:
  python scripts/recover_data_local.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force LOCAL SQLite database (not Supabase)
os.environ['DATABASE_URL'] = 'sqlite:///./ready_for_robots.db'

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, engine
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.inference_engine import analyze_signals
import app.models

# Create tables
from app.database import Base
Base.metadata.create_all(bind=engine)

# Clear old internal test data
print("🗑️  Clearing old test data...")
db = SessionLocal()
try:
    deleted = db.query(Company).filter(Company.is_internal == True).delete()
    db.commit()
    print(f"   Deleted {deleted} old internal records")
except Exception as e:
    print(f"   Error clearing data: {e}")
    db.rollback()
finally:
    db.close()

# Import seed data from seed_leads_v2.py
print("\n📥 Loading seed data from seed_leads_v2.py...")
exec(open('scripts/seed_leads_v2.py').read())

print("\n✅ Recovery complete!")
print("\nNext steps:")
print("1. Check lead count: curl http://localhost:8000/api/leads | python3 -m json.tool | grep -c 'company_name'")
print("2. Open dashboard: http://localhost:3000")
print("3. Wait for Supabase Pro backup access for full recovery")
