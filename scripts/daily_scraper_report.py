#!/usr/bin/env python3
"""
Daily Scraper Performance Report
Tracks actual vs projected lead discovery metrics
"""

import sys
import os
from datetime import datetime, timedelta
from collections import Counter

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score


def get_daily_metrics():
    """Get lead discovery metrics for last 24 hours"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        # New companies discovered in last 24h
        new_companies_24h = db.query(Company).filter(
            Company.created_at >= yesterday
        ).all()
        
        # New signals in last 24h
        new_signals_24h = db.query(Signal).filter(
            Signal.created_at >= yesterday
        ).all()
        
        # Companies from last 7 days for trend analysis
        new_companies_7d = db.query(Company).filter(
            Company.created_at >= week_ago
        ).all()
        
        # Score distribution of new companies
        scores_24h = db.query(Score).join(Company).filter(
            Company.created_at >= yesterday
        ).all()
        
        # All companies for totals
        total_companies = db.query(Company).count()
        total_signals = db.query(Signal).count()
        
        return {
            'new_companies_24h': new_companies_24h,
            'new_signals_24h': new_signals_24h,
            'new_companies_7d': new_companies_7d,
            'scores_24h': scores_24h,
            'total_companies': total_companies,
            'total_signals': total_signals
        }
    finally:
        db.close()


def analyze_metrics(metrics):
    """Analyze metrics and compare to projections"""
    new_companies = metrics['new_companies_24h']
    new_signals = metrics['new_signals_24h']
    scores = metrics['scores_24h']
    
    # Count by data source
    sources = Counter([c.data_source for c in new_companies if c.data_source])
    
    # Count by signal type
    signal_types = Counter([s.signal_type for s in new_signals])
    
    # Count by tier
    hot_count = sum(1 for s in scores if s.final_score >= 70)
    warm_count = sum(1 for s in scores if 40 <= s.final_score < 70)
    cold_count = sum(1 for s in scores if s.final_score < 40)
    
    # Manufacturing signals (the big question)
    manufacturing_signals = [
        'quality_bottleneck', 'safety_incident', 'capacity_constraint',
        'throughput_issue', 'packaging_automation', 'material_handling'
    ]
    mfg_count = sum(1 for s in new_signals if s.signal_type in manufacturing_signals)
    
    # 7-day trend (daily average)
    days_7_count = len(metrics['new_companies_7d'])
    daily_avg_7d = days_7_count / 7.0
    
    # Automated vs seeded
    automated_sources = ['job_news', 'news_scraper', 'logistics_directory_scraper', 
                        'serp_scraper', 'job_board_scraper', 'rfp_marketplace_scraper',
                        'hotel_directory_scraper']
    automated_count = sum(1 for c in new_companies if c.data_source in automated_sources)
    seeded_count = len(new_companies) - automated_count
    
    return {
        'total_new': len(new_companies),
        'automated': automated_count,
        'seeded': seeded_count,
        'sources': sources,
        'signal_types': signal_types,
        'hot': hot_count,
        'warm': warm_count,
        'cold': cold_count,
        'manufacturing_signals': mfg_count,
        'daily_avg_7d': daily_avg_7d,
        'total_signals': len(new_signals)
    }


def generate_report(metrics, analysis):
    """Generate formatted daily report"""
    now = datetime.utcnow()
    
    report = []
    report.append("=" * 80)
    report.append(f"DAILY SCRAPER PERFORMANCE REPORT - {now.strftime('%B %d, %Y')}")
    report.append("=" * 80)
    report.append("")
    
    # Executive Summary
    report.append("📊 EXECUTIVE SUMMARY")
    report.append("-" * 80)
    report.append(f"New Leads (24h):        {analysis['total_new']}")
    report.append(f"  ├─ Automated:         {analysis['automated']} ({analysis['automated']/max(analysis['total_new'], 1)*100:.1f}%)")
    report.append(f"  └─ Seeded:            {analysis['seeded']} ({analysis['seeded']/max(analysis['total_new'], 1)*100:.1f}%)")
    report.append(f"New Signals:            {analysis['total_signals']}")
    report.append(f"7-Day Daily Avg:        {analysis['daily_avg_7d']:.1f} leads/day")
    report.append("")
    report.append(f"Total Database:         {metrics['total_companies']} companies, {metrics['total_signals']} signals")
    report.append("")
    
    # Projection Comparison
    report.append("🎯 ACTUAL vs PROJECTED")
    report.append("-" * 80)
    actual = analysis['total_new']
    report.append(f"Actual:                 {actual} leads/day")
    report.append(f"Conservative Target:    15-25 leads/day  {'✅ EXCEEDED' if actual > 25 else '✓ ON TRACK' if actual >= 15 else '⚠️ BELOW TARGET'}")
    report.append(f"Realistic Target:       30-50 leads/day  {'✅ EXCEEDED' if actual > 50 else '✓ ON TRACK' if actual >= 30 else '⚠️ BELOW TARGET'}")
    report.append(f"Optimistic Target:      60-80 leads/day  {'✅ EXCEEDED' if actual > 80 else '✓ ON TRACK' if actual >= 60 else '⚠️ BELOW TARGET'}")
    report.append("")
    
    # Quality Distribution
    report.append("🔥 QUALITY DISTRIBUTION")
    report.append("-" * 80)
    total_scored = analysis['hot'] + analysis['warm'] + analysis['cold']
    if total_scored > 0:
        report.append(f"HOT (70+):              {analysis['hot']} ({analysis['hot']/total_scored*100:.1f}%)")
        report.append(f"WARM (40-69):           {analysis['warm']} ({analysis['warm']/total_scored*100:.1f}%)")
        report.append(f"COLD (<40):             {analysis['cold']} ({analysis['cold']/total_scored*100:.1f}%)")
    else:
        report.append("No scored leads in last 24h")
    report.append("")
    
    # Manufacturing Signals (Critical Question)
    report.append("🏭 MANUFACTURING SIGNALS")
    report.append("-" * 80)
    mfg_count = analysis['manufacturing_signals']
    report.append(f"Detected (24h):         {mfg_count}")
    if mfg_count > 0:
        report.append("Status:                 ✅ LIVE - Manufacturing signals are being detected!")
    else:
        report.append("Status:                 ⏳ PENDING - Queries running but no matches yet")
        report.append("Action:                 Monitor for 48-72h, then adjust ontology if needed")
    report.append("")
    
    # Data Sources
    report.append("📡 DATA SOURCES")
    report.append("-" * 80)
    if analysis['sources']:
        for source, count in analysis['sources'].most_common():
            pct = count / max(analysis['total_new'], 1) * 100
            report.append(f"  {source:30} {count:3} leads ({pct:5.1f}%)")
    else:
        report.append("  No new leads from automated sources")
    report.append("")
    
    # Signal Types
    report.append("🎯 SIGNAL TYPES")
    report.append("-" * 80)
    if analysis['signal_types']:
        for signal_type, count in analysis['signal_types'].most_common(10):
            pct = count / max(analysis['total_signals'], 1) * 100
            report.append(f"  {signal_type:30} {count:3} signals ({pct:5.1f}%)")
    else:
        report.append("  No new signals detected")
    report.append("")
    
    # Trend Analysis
    report.append("📈 7-DAY TREND")
    report.append("-" * 80)
    if analysis['daily_avg_7d'] > 0:
        change = ((actual - analysis['daily_avg_7d']) / analysis['daily_avg_7d']) * 100
        trend = "↗️ UP" if change > 5 else "↘️ DOWN" if change < -5 else "→ FLAT"
        report.append(f"7-Day Average:          {analysis['daily_avg_7d']:.1f} leads/day")
        report.append(f"Today vs Avg:           {change:+.1f}% {trend}")
    else:
        report.append("Insufficient data for trend analysis")
    report.append("")
    
    # Recommendations
    report.append("💡 RECOMMENDATIONS")
    report.append("-" * 80)
    
    if mfg_count == 0:
        report.append("  ⚠️  Manufacturing signals: Monitor for 48h, consider ontology refinement")
    else:
        report.append("  ✅ Manufacturing signals: Performing well")
    
    if analysis['automated'] < analysis['total_new'] * 0.7:
        report.append(f"  ⚠️  Automated discovery: Only {analysis['automated']/max(analysis['total_new'],1)*100:.0f}%, target 70%+")
    else:
        report.append("  ✅ Automated discovery: Exceeding 70% target")
    
    if actual < 30:
        report.append("  📈 Scale up: Add more news sources or increase scraper frequency")
    
    if analysis['hot'] == 0 and total_scored > 0:
        report.append("  🎯 Lead quality: No HOT leads found - review scoring thresholds")
    
    report.append("")
    report.append("=" * 80)
    report.append(f"Report generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("=" * 80)
    
    return "\n".join(report)


def save_report(report_text):
    """Save report to file"""
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    filename = f"scraper_report_{datetime.utcnow().strftime('%Y%m%d')}.txt"
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, 'w') as f:
        f.write(report_text)
    
    # Also save as "latest.txt" for easy access
    latest_path = os.path.join(reports_dir, 'latest.txt')
    with open(latest_path, 'w') as f:
        f.write(report_text)
    
    return filepath


def main():
    """Main execution"""
    print("Generating daily scraper report...")
    
    metrics = get_daily_metrics()
    analysis = analyze_metrics(metrics)
    report = generate_report(metrics, analysis)
    
    # Print to console
    print(report)
    
    # Save to file
    filepath = save_report(report)
    print(f"\n✅ Report saved to: {filepath}")
    print(f"   Also available at: reports/latest.txt")


if __name__ == '__main__':
    main()
