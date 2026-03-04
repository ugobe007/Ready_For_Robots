from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, and_, or_, desc, text
from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()

# Track calculator usage
calculator_usage = []
robot_searches = []

@router.post("/track/roi-calculation")
async def track_roi_calculation(data: dict):
    """Track ROI calculator usage"""
    calculator_usage.append({
        **data,
        'timestamp': datetime.now().isoformat()
    })
    return {"status": "tracked"}

@router.post("/track/robot-search")
async def track_robot_search(data: dict):
    """Track robot search usage"""
    robot_searches.append({
        **data,
        'timestamp': datetime.now().isoformat()
    })
    return {"status": "tracked"}

@router.get("/analytics")
async def get_analytics(range: str = Query('7d', regex='^(7d|30d|90d|all)$')):
    """Get platform analytics"""
    
    # Calculate date cutoff
    now = datetime.now()
    if range == '7d':
        cutoff = now - timedelta(days=7)
    elif range == '30d':
        cutoff = now - timedelta(days=30)
    elif range == '90d':
        cutoff = now - timedelta(days=90)
    else:
        cutoff = datetime.min
    
    # Filter data by date range
    filtered_calcs = [c for c in calculator_usage if datetime.fromisoformat(c['timestamp']) >= cutoff]
    filtered_searches = [s for s in robot_searches if datetime.fromisoformat(s['timestamp']) >= cutoff]
    
    # Calculate metrics
    total_calculations = len(filtered_calcs)
    total_robot_searches = len(filtered_searches)
    
    # Previous period for growth calculation
    if range == '7d':
        prev_cutoff = now - timedelta(days=14)
        prev_end = cutoff
    elif range == '30d':
        prev_cutoff = now - timedelta(days=60)
        prev_end = cutoff
    elif range == '90d':
        prev_cutoff = now - timedelta(days=180)
        prev_end = cutoff
    else:
        prev_cutoff = datetime.min
        prev_end = now - timedelta(days=365)
    
    prev_calcs = [c for c in calculator_usage 
                  if prev_cutoff <= datetime.fromisoformat(c['timestamp']) < prev_end]
    
    calculation_growth = 0
    if len(prev_calcs) > 0:
        calculation_growth = round(((total_calculations - len(prev_calcs)) / len(prev_calcs)) * 100)
    elif total_calculations > 0:
        calculation_growth = 100
    
    # Average metrics
    avg_payback_months = 0
    avg_robot_cost = 0
    if filtered_calcs:
        paybacks = [c.get('payback_months', 0) for c in filtered_calcs if c.get('payback_months')]
        costs = [c.get('robot_cost', 0) for c in filtered_calcs if c.get('robot_cost')]
        avg_payback_months = round(sum(paybacks) / len(paybacks), 1) if paybacks else 0
        avg_robot_cost = round(sum(costs) / len(costs)) if costs else 0
    
    # Average matches per search
    avg_matches_per_search = 0
    if filtered_searches:
        matches = [s.get('matches_found', 0) for s in filtered_searches if s.get('matches_found')]
        avg_matches_per_search = round(sum(matches) / len(matches), 1) if matches else 0
    
    # Email captures (from benchmark downloads)
    email_captures = len([c for c in filtered_calcs if c.get('email')])
    conversion_rate = round((email_captures / total_calculations) * 100) if total_calculations > 0 else 0
    
    # Top robot types
    robot_type_counts = {}
    for calc in filtered_calcs:
        robot_type = calc.get('robot_type', 'Unknown')
        robot_type_counts[robot_type] = robot_type_counts.get(robot_type, 0) + 1
    
    top_robot_types = []
    if robot_type_counts:
        sorted_types = sorted(robot_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        max_count = sorted_types[0][1] if sorted_types else 1
        for robot_type, count in sorted_types:
            top_robot_types.append({
                'type': robot_type,
                'count': count,
                'percentage': round((count / max_count) * 100)
            })
    
    # Top industries
    industry_counts = {}
    for calc in filtered_calcs:
        industry = calc.get('industry', 'Other')
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
    
    for search in filtered_searches:
        industries = search.get('target_industries', [])
        for industry in industries:
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
    
    top_industries = []
    if industry_counts:
        sorted_industries = sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        max_count = sorted_industries[0][1] if sorted_industries else 1
        for industry, count in sorted_industries:
            top_industries.append({
                'name': industry,
                'count': count,
                'percentage': round((count / max_count) * 100)
            })
    
    # Top regions
    region_counts = {}
    for search in filtered_searches:
        regions = search.get('target_regions', [])
        for region in regions:
            region_counts[region] = region_counts.get(region, 0) + 1
    
    top_regions = []
    if region_counts:
        sorted_regions = sorted(region_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        max_count = sorted_regions[0][1] if sorted_regions else 1
        for region, count in sorted_regions:
            top_regions.append({
                'name': region,
                'searches': count,
                'percentage': round((count / max_count) * 100)
            })
    
    # Cost buckets
    cost_buckets = {
        'Under $20k': 0,
        '$20k - $30k': 0,
        '$30k - $40k': 0,
        '$40k - $50k': 0,
        'Over $50k': 0
    }
    
    for calc in filtered_calcs:
        cost = calc.get('robot_cost', 0)
        if cost < 20000:
            cost_buckets['Under $20k'] += 1
        elif cost < 30000:
            cost_buckets['$20k - $30k'] += 1
        elif cost < 40000:
            cost_buckets['$30k - $40k'] += 1
        elif cost < 50000:
            cost_buckets['$40k - $50k'] += 1
        else:
            cost_buckets['Over $50k'] += 1
    
    cost_bucket_list = []
    total_costs = sum(cost_buckets.values())
    if total_costs > 0:
        for bucket_range, count in cost_buckets.items():
            if count > 0:
                cost_bucket_list.append({
                    'range': bucket_range,
                    'count': count,
                    'percentage': round((count / total_costs) * 100)
                })
    
    # Generate insights
    insights = {
        'hottest_trend': 'Not enough data yet',
        'opportunity': 'Gather more data to reveal opportunities',
        'growth_area': 'Continue monitoring user behavior',
        'action_item': 'Build features users are requesting'
    }
    
    if top_robot_types:
        insights['hottest_trend'] = f"{top_robot_types[0]['type']} robots are trending with {top_robot_types[0]['count']} calculations"
    
    if top_industries:
        insights['opportunity'] = f"{top_industries[0]['name']} shows highest interest with {top_industries[0]['count']} interactions"
    
    if avg_payback_months > 0 and avg_payback_months < 9:
        insights['growth_area'] = f"Fast ROI potential ({avg_payback_months} mo avg payback) driving adoption"
    elif avg_payback_months >= 9:
        insights['growth_area'] = f"Education needed - {avg_payback_months} mo avg payback may slow adoption"
    
    if conversion_rate > 0:
        insights['action_item'] = f"Capitalize on {conversion_rate}% conversion rate with targeted email campaigns"
    else:
        insights['action_item'] = "Add more lead capture opportunities to convert visitors"
    
    return {
        'total_calculations': total_calculations,
        'calculation_growth': calculation_growth,
        'robot_searches': total_robot_searches,
        'avg_matches_per_search': avg_matches_per_search,
        'avg_payback_months': avg_payback_months,
        'avg_robot_cost': avg_robot_cost,
        'email_captures': email_captures,
        'conversion_rate': conversion_rate,
        'top_robot_types': top_robot_types,
        'top_industries': top_industries,
        'top_regions': top_regions,
        'cost_buckets': cost_bucket_list,
        'insights': insights
    }
