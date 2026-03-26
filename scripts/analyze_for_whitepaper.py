#!/usr/bin/env python3
"""
Analyze automation intelligence data for whitepaper
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Company, Signal
from app.models.score import Score
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json

db = SessionLocal()

print('━' * 80)
print('📊 AUTOMATION INTELLIGENCE REPORT - MARCH 2026')
print('━' * 80)
print()

# Basic stats
total_companies = db.query(Company).count()
total_signals = db.query(Signal).count()

print(f'📈 DATASET OVERVIEW:')
print(f'  Total Companies:  {total_companies}')
print(f'  Total Signals:    {total_signals}')
print(f'  Signals/Company:  {total_signals/total_companies:.1f}')
print()

# Top companies
print('🎯 TOP 10 AUTOMATION-READY COMPANIES:')
top_companies = (
    db.query(Company, Score)
    .join(Score, Company.id == Score.company_id)
    .order_by(desc(Score.total_score))
    .limit(10)
    .all()
)
for i, (company, score) in enumerate(top_companies, 1):
    print(f'  {i:2}. {company.name[:35]:.<40} Score: {score.total_score:>3} | {company.industry or "N/A"}')
print()

# Industries
print('🏭 TOP INDUSTRIES:')
industries = db.query(
    Company.industry,
    func.count(Company.id).label('count'),
    func.avg(Score.total_score).label('avg_score')
).join(Score, Company.id == Score.company_id, isouter=True).filter(Company.industry != None).group_by(Company.industry).all()

for industry, count, avg_score in sorted(industries, key=lambda x: x[1], reverse=True)[:8]:
    score_text = f'{avg_score:.1f}' if avg_score else 'N/A'
    print(f'  {industry[:25]:.<30} {count:>3} companies (avg score: {score_text})')
print()

# Signal types
print('📡 SIGNAL TYPES:')
signal_types = db.query(
    Signal.signal_type,
    func.count(Signal.id).label('count')
).group_by(Signal.signal_type).all()

for signal_type, count in sorted(signal_types, key=lambda x: x[1], reverse=True):
    print(f'  {signal_type or "Unknown":.<35} {count:>4} signals')
print()

# Readiness levels
print('🚦 AUTOMATION READINESS:')
high = db.query(Company).join(Score).filter(Score.total_score >= 80).count()
medium = db.query(Company).join(Score).filter(Score.total_score >= 60, Score.total_score < 80).count()
low = db.query(Company).join(Score).filter(Score.total_score < 60).count()

scored_total = high + medium + low
print(f'  🔥 High (80+):     {high:>3} companies ({high/scored_total*100 if scored_total else 0:.1f}%)')
print(f'  🟡 Medium (60-79): {medium:>3} companies ({medium/scored_total*100 if scored_total else 0:.1f}%)')
print(f'  ⚪ Low (<60):      {low:>3} companies ({low/scored_total*100 if scored_total else 0:.1f}%)')
print()

# Multi-signal companies
multi_signal = db.query(Company.id).join(Signal).group_by(Company.id).having(func.count(Signal.id) >= 3).count()
print(f'💎 STRONG BUYING INTENT:')
print(f'  Companies with 3+ signals: {multi_signal} ({multi_signal/total_companies*100:.1f}%)')
print()

# Recent activity
thirty_days = datetime.utcnow() - timedelta(days=30)
recent = db.query(Company).filter(Company.created_at >= thirty_days).count()
print(f'⏰ RECENT DISCOVERIES (30 days):')
print(f'  New companies found: {recent}')
print()

print('━' * 80)

# Export data for whitepaper
whitepaper_data = {
    'total_companies': total_companies,
    'total_signals': total_signals,
    'avg_signals': round(total_signals/total_companies, 1),
    'high_readiness': high,
    'high_readiness_pct': round(high/scored_total*100 if scored_total else 0, 1),
    'multi_signal_companies': multi_signal,
    'multi_signal_pct': round(multi_signal/total_companies*100, 1),
    'top_industries': [
        {'name': ind, 'count': cnt, 'avg_score': round(score, 1) if score else None}
        for ind, cnt, score in sorted(industries, key=lambda x: x[1], reverse=True)[:5]
    ],
    'top_companies': [
        {'name': c.name, 'score': s.total_score, 'industry': c.industry}
        for c, s in top_companies[:5]
    ]
}

with open('reports/whitepaper_data.json', 'w') as f:
    json.dump(whitepaper_data, f, indent=2)
print('✅ Data exported to reports/whitepaper_data.json')
