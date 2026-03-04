from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.shared_calculation import SharedCalculation, SharedCalculationCreate
import random
import string

router = APIRouter()

def generate_share_id():
    """Generate a short unique ID for sharing"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

@router.post("/share-calculation")
async def create_shareable_calculation(data: SharedCalculationCreate):
    """Create a shareable link for an ROI calculation"""
    db = SessionLocal()
    try:
        # Generate unique share ID
        share_id = generate_share_id()
        while db.query(SharedCalculation).filter(SharedCalculation.share_id == share_id).first():
            share_id = generate_share_id()
        
        # Create shared calculation
        shared_calc = SharedCalculation(
            share_id=share_id,
            robot_type=data.robot_type,
            robot_cost=data.robot_cost,
            industry=data.industry,
            payback_months=data.payback_months,
            annual_savings=data.annual_savings,
            roi_1_year=data.roi_1_year,
            roi_3_year=data.roi_3_year,
            total_savings_3_year=data.total_savings_3_year,
            views=0
        )
        
        db.add(shared_calc)
        db.commit()
        db.refresh(shared_calc)
        
        return {
            "share_id": share_id,
            "share_url": f"/roi-calculator/{share_id}"
        }
    finally:
        db.close()

@router.get("/shared-calculation/{share_id}")
async def get_shared_calculation(share_id: str):
    """Get a shared calculation by ID"""
    db = SessionLocal()
    try:
        calc = db.query(SharedCalculation).filter(SharedCalculation.share_id == share_id).first()
        if not calc:
            raise HTTPException(status_code=404, detail="Shared calculation not found")
        
        # Increment view count
        calc.views += 1
        db.commit()
        
        return {
            "share_id": calc.share_id,
            "robot_type": calc.robot_type,
            "robot_cost": calc.robot_cost,
            "industry": calc.industry,
            "payback_months": calc.payback_months,
            "annual_savings": calc.annual_savings,
            "roi_1_year": calc.roi_1_year,
            "roi_3_year": calc.roi_3_year,
            "total_savings_3_year": calc.total_savings_3_year,
            "views": calc.views,
            "created_at": calc.created_at.isoformat()
        }
    finally:
        db.close()

@router.get("/share-card/{share_id}", response_class=HTMLResponse)
async def get_share_card(share_id: str):
    """Generate a social share card for a calculation"""
    db = SessionLocal()
    try:
        calc = db.query(SharedCalculation).filter(SharedCalculation.share_id == share_id).first()
        if not calc:
            raise HTTPException(status_code=404, detail="Shared calculation not found")
        
        # Generate beautiful HTML share card
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ROI: {calc.robot_type} - {calc.payback_months:.1f} month payback</title>
            <meta property="og:title" content="ROI: {calc.robot_type} - {calc.payback_months:.1f} month payback" />
            <meta property="og:description" content="${calc.annual_savings:,.0f}/year savings · {calc.roi_3_year:.0f}% 3-year ROI · {calc.industry}" />
            <meta property="og:type" content="website" />
            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:title" content="ROI: {calc.robot_type}" />
            <meta name="twitter:description" content="{calc.payback_months:.1f} mo payback · ${calc.annual_savings:,.0f}/yr savings" />
            <style>
                body {{
                    margin: 0;
                    padding: 40px;
                    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    color: white;
                }}
                .card {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #18181b;
                    border: 1px solid #27272a;
                    border-radius: 16px;
                    padding: 32px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    background: linear-gradient(to right, #10b981, #06b6d4);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 24px;
                }}
                h1 {{
                    font-size: 32px;
                    margin: 0 0 8px 0;
                    color: #fbbf24;
                }}
                .industry {{
                    color: #9ca3af;
                    font-size: 16px;
                    margin-bottom: 24px;
                }}
                .metric {{
                    background: #27272a;
                    border: 1px solid #3f3f46;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 16px;
                }}
                .metric-label {{
                    color: #9ca3af;
                    font-size: 14px;
                    margin-bottom: 8px;
                }}
                .metric-value {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #10b981;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                    margin-top: 16px;
                }}
                .small-metric {{
                    background: #27272a;
                    border: 1px solid #3f3f46;
                    border-radius: 8px;
                    padding: 16px;
                }}
                .small-metric-label {{
                    color: #9ca3af;
                    font-size: 12px;
                    margin-bottom: 6px;
                }}
                .small-metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: white;
                }}
                .cta {{
                    margin-top: 24px;
                    text-align: center;
                }}
                .cta a {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: transparent;
                    border: 2px solid #10b981;
                    color: #10b981;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    transition: all 0.2s;
                }}
                .cta a:hover {{
                    background: #10b981;
                    color: #0a0a0a;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="logo">🤖 Ready For Robots</div>
                <h1>{calc.robot_type}</h1>
                <div class="industry">{calc.industry}</div>
                
                <div class="metric">
                    <div class="metric-label">Payback Period</div>
                    <div class="metric-value">{calc.payback_months:.1f} months</div>
                </div>
                
                <div class="grid">
                    <div class="small-metric">
                        <div class="small-metric-label">Annual Savings</div>
                        <div class="small-metric-value">${calc.annual_savings:,.0f}</div>
                    </div>
                    <div class="small-metric">
                        <div class="small-metric-label">3-Year ROI</div>
                        <div class="small-metric-value">{calc.roi_3_year:.0f}%</div>
                    </div>
                </div>
                
                <div class="cta">
                    <a href="https://ready-2-robot.fly.dev/roi-calculator">Calculate Your ROI →</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html)
    finally:
        db.close()
