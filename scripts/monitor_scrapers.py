#!/usr/bin/env python3
"""
Scraper Monitoring Dashboard
============================
Real-time monitoring of scraper health and performance
Run: python3 scripts/monitor_scrapers.py
"""
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from sqlalchemy import func


def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')


def get_stats(db):
    """Get scraper statistics"""
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    stats = {}
    
    # Total counts
    stats['total_companies'] = db.query(func.count(Company.id)).scalar()
    stats['total_signals'] = db.query(func.count(Signal.id)).scalar()
    stats['hot_leads'] = db.query(func.count(Score.id)).filter(Score.tier == 'HOT').scalar()
    stats['warm_leads'] = db.query(func.count(Score.id)).filter(Score.tier == 'WARM').scalar()
    stats['cold_leads'] = db.query(func.count(Score.id)).filter(Score.tier == 'COLD').scalar()
    
    # Recent activity (last hour)
    stats['signals_last_hour'] = db.query(func.count(Signal.id)).filter(
        Signal.detected_at >= hour_ago
    ).scalar()
    
    stats['companies_last_hour'] = db.query(func.count(Company.id)).filter(
        Company.created_at >= hour_ago
    ).scalar()
    
    # Recent activity (last 24h)
    stats['signals_last_day'] = db.query(func.count(Signal.id)).filter(
        Signal.detected_at >= day_ago
    ).scalar()
    
    stats['companies_last_day'] = db.query(func.count(Company.id)).filter(
        Company.created_at >= day_ago
    ).scalar()
    
    # Signal type breakdown
    signal_types = db.query(
        Signal.signal_type,
        func.count(Signal.id).label('count')
    ).group_by(Signal.signal_type).order_by(func.count(Signal.id).desc()).limit(10).all()
    
    stats['top_signals'] = [(st, count) for st, count in signal_types]
    
    # Industry breakdown
    industries = db.query(
        Company.industry,
        func.count(Company.id).label('count')
    ).filter(Company.industry != None).group_by(Company.industry).order_by(
        func.count(Company.id).desc()
    ).limit(10).all()
    
    stats['top_industries'] = [(ind, count) for ind, count in industries]
    
    # Source breakdown
    sources = db.query(
        Company.source,
        func.count(Company.id).label('count')
    ).group_by(Company.source).order_by(func.count(Company.id).desc()).all()
    
    stats['sources'] = [(src, count) for src, count in sources]
    
    return stats


def display_dashboard(stats):
    """Display monitoring dashboard"""
    clear_screen()
    
    print("=" * 80)
    print(" READY FOR ROBOTS - Scraper Monitoring Dashboard".center(80))
    print(f" {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}".center(80))
    print("=" * 80)
    print()
    
    # Overall stats
    print("📊 OVERALL STATISTICS")
    print("-" * 80)
    print(f"  Total Companies:    {stats['total_companies']:>6,}")
    print(f"  Total Signals:      {stats['total_signals']:>6,}")
    print()
    print(f"  🔥 HOT Leads:       {stats['hot_leads']:>6,}")
    print(f"  🟡 WARM Leads:      {stats['warm_leads']:>6,}")
    print(f"  ❄️  COLD Leads:      {stats['cold_leads']:>6,}")
    print()
    
    # Recent activity
    print("⚡ RECENT ACTIVITY")
    print("-" * 80)
    print(f"  Last Hour:")
    print(f"    • Signals:        {stats['signals_last_hour']:>6,}")
    print(f"    • Companies:      {stats['companies_last_hour']:>6,}")
    print()
    print(f"  Last 24 Hours:")
    print(f"    • Signals:        {stats['signals_last_day']:>6,}")
    print(f"    • Companies:      {stats['companies_last_day']:>6,}")
    print()
    
    # Signal types
    print("🎯 TOP SIGNAL TYPES")
    print("-" * 80)
    for signal_type, count in stats['top_signals'][:5]:
        bar = "█" * min(40, count // 10)
        print(f"  {signal_type:.<30} {count:>5,} {bar}")
    print()
    
    # Industries
    print("🏭 TOP INDUSTRIES")
    print("-" * 80)
    for industry, count in stats['top_industries'][:5]:
        bar = "█" * min(40, count // 5)
        print(f"  {industry:.<30} {count:>5,} {bar}")
    print()
    
    # Sources
    print("📡 DATA SOURCES")
    print("-" * 80)
    for source, count in stats['sources']:
        print(f"  {source:.<30} {count:>5,}")
    print()
    
    print("=" * 80)
    print(" Press Ctrl+C to exit | Updates every 30 seconds")
    print("=" * 80)


def main():
    """Main monitoring loop"""
    print("Starting scraper monitoring...")
    print("Loading data...")
    
    try:
        while True:
            db = SessionLocal()
            
            try:
                stats = get_stats(db)
                display_dashboard(stats)
            finally:
                db.close()
            
            # Update every 30 seconds
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
