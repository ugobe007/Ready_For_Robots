#!/usr/bin/env python3
"""Quick seed - add 5 companies to database"""
import os
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:J5GW9sTXA0CHU1Mq@db.lmoyydlhlgdyqbxkmkuz.supabase.co:5432/postgres')

from app.database import SessionLocal, engine
from app.models.company import Company
from app.models.score import Score

# Create tables
Company.__table__.create(engine, checkfirst=True)
Score.__table__.create(engine, checkfirst=True)

db = SessionLocal()

companies_data = [
    {'name': 'Hilton Hotels', 'industry': 'Hospitality', 'location_city': 'McLean', 'location_state': 'VA', 'employee_estimate': 450000, 'source': 'Seed', 'website': 'hilton.com'},
    {'name': 'Amazon Logistics', 'industry': 'Logistics', 'location_city': 'Seattle', 'location_state': 'WA', 'employee_estimate': 950000, 'source': 'Seed', 'website': 'amazon.com'},
    {'name': 'Walmart Supply Chain', 'industry': 'Retail', 'location_city': 'Bentonville', 'location_state': 'AR', 'employee_estimate': 2300000, 'source': 'Seed', 'website': 'walmart.com'},
    {'name': 'Marriott Hotels', 'industry': 'Hospitality', 'location_city': 'Bethesda', 'location_state': 'MD', 'employee_estimate': 390000, 'source': 'Seed', 'website': 'marriott.com'},
    {'name': 'UPS', 'industry': 'Logistics', 'location_city': 'Atlanta', 'location_state': 'GA', 'employee_estimate': 534000, 'source': 'Seed', 'website': 'ups.com'},
]

for data in companies_data:
    existing = db.query(Company).filter(Company.name == data['name']).first()
    if not existing:
        company = Company(**data)
        db.add(company)
        print(f'✓ Added: {data["name"]}')
    else:
        print(f'⏭️  Skip: {data["name"]}')

db.commit()
total = db.query(Company).count()
print(f'\n✅ Total companies: {total}')
db.close()
