from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

router = APIRouter()

class Company(BaseModel):
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    score: Optional[float] = None
    value_proposition: Optional[str] = None
    signals: Optional[List[str]] = []
    recommended_action: Optional[str] = None

class PlaybookRequest(BaseModel):
    robot_name: str
    matched_companies: List[Company]
    overall_strategy: Optional[str] = None
    target_industries: List[str]
    target_regions: List[str]

@router.post("/generate-playbook")
async def generate_sales_playbook(request: PlaybookRequest):
    """Generate a PDF sales playbook from Robot Ready results"""
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=inch, leftMargin=inch,
                           topMargin=inch, bottomMargin=inch)
    
    # Container for PDF elements
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#10b981'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#10b981'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#06b6d4'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    # Title Page
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph(f"Sales Playbook", title_style))
    story.append(Paragraph(f"{request.robot_name}", heading_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Executive Summary
    summary_text = f"""
    <b>Target Markets:</b> {', '.join(request.target_industries[:3])}...<br/>
    <b>Target Regions:</b> {', '.join(request.target_regions[:3])}...<br/>
    <b>Qualified Leads Found:</b> {len(request.matched_companies)}<br/>
    <b>Hot Prospects:</b> {len([c for c in request.matched_companies if (c.score or 0) >= 75])}
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(PageBreak())
    
    # Overall Strategy
    if request.overall_strategy:
        story.append(Paragraph("Recommended Sales Strategy", heading_style))
        for para in request.overall_strategy.split('\n'):
            if para.strip():
                story.append(Paragraph(para.strip(), styles['Normal']))
                story.append(Spacer(1, 12))
        story.append(PageBreak())
    
    # Top Prospects Section
    story.append(Paragraph("Top Prospect Companies", heading_style))
    story.append(Spacer(1, 12))
    
    # Sort companies by score
    sorted_companies = sorted(request.matched_companies, 
                              key=lambda x: x.score or 0, 
                              reverse=True)[:10]  # Top 10
    
    for idx, company in enumerate(sorted_companies, 1):
        # Company Header
        company_header = f"<b>{idx}. {company.name}</b>"
        if company.score:
            company_header += f" (Score: {int(company.score)})"
        story.append(Paragraph(company_header, subheading_style))
        
        # Company Details
        details = []
        if company.industry:
            details.append(f"<b>Industry:</b> {company.industry}")
        if company.location:
            details.append(f"<b>Location:</b> {company.location}")
        if details:
            story.append(Paragraph(" | ".join(details), styles['Normal']))
            story.append(Spacer(1, 6))
        
        # Value Proposition
        if company.value_proposition:
            story.append(Paragraph("<b>Your Value Proposition:</b>", styles['Normal']))
            story.append(Paragraph(company.value_proposition, styles['Italic']))
            story.append(Spacer(1, 8))
        
        # Signals
        if company.signals:
            story.append(Paragraph(f"<b>Buying Signals:</b> {', '.join(company.signals[:5])}", styles['Normal']))
            story.append(Spacer(1, 8))
        
        # Recommended Action
        if company.recommended_action:
            story.append(Paragraph(f"<b>→ Next Step:</b> {company.recommended_action}", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Page break after every 3 companies
        if idx % 3 == 0 and idx < len(sorted_companies):
            story.append(PageBreak())
    
    # Objection Handling Section
    story.append(PageBreak())
    story.append(Paragraph("Common Objections & Responses", heading_style))
    story.append(Spacer(1, 12))
    
    objections = [
        {
            'objection': '"The upfront cost is too high"',
            'response': 'Most customers see full payback within 6-12 months through labor savings. Would you like to see an ROI calculation specific to your operation?'
        },
        {
            'objection': '"We\'re not ready for automation"',
            'response': 'We can start with a small pilot program in one department. This de-risks the investment and proves value before scaling.'
        },
        {
            'objection': '"Our employees will lose their jobs"',
            'response': 'Leading companies redeploy staff to higher-value roles. Automation handles repetitive tasks, freeing your team for customer service and growth initiatives.'
        },
        {
            'objection': '"We need to see it working first"',
            'response': 'We offer on-site demos and can connect you with existing customers in your industry for reference calls.'
        }
    ]
    
    for obj in objections:
        story.append(Paragraph(f"<b>Objection:</b> {obj['objection']}", styles['Normal']))
        story.append(Paragraph(f"<b>Response:</b> {obj['response']}", styles['Italic']))
        story.append(Spacer(1, 15))
    
    # Demo Script
    story.append(PageBreak())
    story.append(Paragraph("Discovery Call Script", heading_style))
    story.append(Spacer(1, 12))
    
    demo_script = [
        ('Opening', 'Hi [Name], thanks for taking the time. I noticed [specific signal/trigger]. How are you currently handling [use case]?'),
        ('Pain Discovery', 'What challenges are you facing with labor costs, consistency, or 24/7 operations?'),
        ('Current State', 'Walk me through your current process. How many hours per day is this taking?'),
        ('Vision', 'If you could wave a magic wand, what would the ideal solution look like?'),
        ('Demo Transition', f'Let me show you how {request.robot_name} solves exactly this problem...'),
        ('ROI Focus', 'Based on what you\'ve shared, I calculate a [X] month payback. Does that align with your investment criteria?'),
        ('Next Steps', 'I\'d love to bring the robot on-site for a 2-week pilot. When would be a good time?'),
    ]
    
    for section, script in demo_script:
        story.append(Paragraph(f"<b>{section}:</b> {script}", styles['Normal']))
        story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{request.robot_name.replace(" ", "_")}_sales_playbook.pdf"'
        }
    )
