#!/usr/bin/env python3
"""
Simple data export for whitepaper
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Company, Signal
from sqlalchemy import func
from datetime import datetime, timedelta
import json

db = SessionLocal()

# Basic stats
total_companies = db.query(Company).count()
total_signals = db.query(Signal).count()

# Industries
industries = db.query(
    Company.industry,
    func.count(Company.id).label('count')
).filter(Company.industry != None).group_by(Company.industry).all()

# Signal types
signal_types = db.query(
    Signal.signal_type,
    func.count(Signal.id).label('count')
).group_by(Signal.signal_type).all()

# Multi-signal companies
multi_signal = db.query(Company.id).join(Signal).group_by(Company.id).having(func.count(Signal.id) >= 3).count()

# Recent activity
thirty_days = datetime.utcnow() - timedelta(days=30)
recent = db.query(Company).filter(Company.created_at >= thirty_days).count()

# Sample companies
sample_companies = db.query(Company).limit(10).all()

print('━' * 80)
print('📊 AUTOMATION INTELLIGENCE REPORT - MARCH 2026')
print('━' * 80)
print()
print(f'📈 DATASET OVERVIEW:')
print(f'  Total Companies:  {total_companies}')
print(f'  Total Signals:    {total_signals}')
print(f'  Signals/Company:  {total_signals/total_companies:.1f}')
print()

print('🏭 TOP INDUSTRIES:')
for industry, count in sorted(industries, key=lambda x: x[1], reverse=True)[:8]:
    print(f'  {industry[:25]:.<30} {count:>3} companies')
print()

print('📡 TOP SIGNAL TYPES:')
for signal_type, count in sorted(signal_types, key=lambda x: x[1], reverse=True)[:10]:
    print(f'  {signal_type or "Unknown":.<35} {count:>4} signals')
print()

print(f'💎 STRONG BUYING INTENT:')
print(f'  Companies with 3+ signals: {multi_signal} ({multi_signal/total_companies*100:.1f}%)')
print()

print(f'⏰ RECENT DISCOVERIES (30 days): {recent} companies')
print()

print('🎯 SAMPLE COMPANIES:')
for i, company in enumerate(sample_companies[:5], 1):
    print(f'  {i}. {company.name} - {company.industry or "Unknown"}')
print()

print('━' * 80)

# Export data
whitepaper_data = {
    'generated_date': datetime.utcnow().isoformat(),
    'overview': {
        'total_companies': total_companies,
        'total_signals': total_signals,
        'avg_signals_per_company': round(total_signals/total_companies, 1),
        'companies_with_strong_intent': multi_signal,
        'strong_intent_percentage': round(multi_signal/total_companies*100, 1),
        'recent_discoveries_30_days': recent
    },
    'industries': [
        {'name': ind, 'count': cnt}
        for ind, cnt in sorted(industries, key=lambda x: x[1], reverse=True)[:10]
    ],
    'signal_types': [
        {'type': st or 'Unknown', 'count': cnt}
        for st, cnt in sorted(signal_types, key=lambda x: x[1], reverse=True)
    ],
    'sample_companies': [
        {'name': c.name, 'industry': c.industry, 'location': f'{c.location_city}, {c.location_state}' if c.location_city else None}
        for c in sample_companies[:10]
    ]
}

os.makedirs('reports', exist_ok=True)
with open('reports/whitepaper_data.json', 'w') as f:
    json.dump(whitepaper_data, f, indent=2)

print('✅ Data exported to reports/whitepaper_data.json')
