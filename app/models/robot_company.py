"""
Robot Company Model - Lead Generation Database
Tracks robotics vendors for distribution/partnership opportunities
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class RobotCompany(Base):
    """
    Robot company lead database for Ready For Robots
    Focus: Chinese robotics companies entering U.S. market
    """
    __tablename__ = "robot_companies"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    company_name = Column(String, nullable=False, index=True)
    country = Column(String, index=True)  # China, US, EU, Korea, Japan
    headquarters_city = Column(String)
    founded_year = Column(Integer)
    
    # Robot Classification
    robot_type = Column(String, index=True)  # industrial, AMR, cobot, humanoid, service, vision
    target_market = Column(String)  # manufacturing, warehouse, service, healthcare, hospitality
    product_category = Column(String)  # specific product line
    
    # U.S. Market Presence
    us_presence = Column(String, index=True)  # office, distributor, none
    us_office_location = Column(String)
    distributor_needed = Column(String)  # yes, maybe, no
    distributor_urgency = Column(String)  # high, medium, low
    
    # Partnership Readiness
    system_integrator_network = Column(JSON)  # list of current integrators
    has_us_partnerships = Column(Boolean, default=False)
    partnership_stage = Column(String)  # exploring, active, established
    
    # Market Entry Wave
    market_entry_wave = Column(String)  # wave_1 (2020-2024), wave_2 (2024-2026), wave_3 (2025-2027)
    entry_priority = Column(String)  # high, medium, low
    
    # Trade Shows & Events
    trade_shows = Column(JSON)  # [Automate, ProMat, CES, Hannover]
    last_trade_show = Column(String)
    next_trade_show = Column(String)
    
    # Funding & Company Stage
    funding_stage = Column(String)  # startup, series_a, series_b, public, private
    funding_amount = Column(String)
    investors = Column(JSON)
    is_publicly_traded = Column(Boolean, default=False)
    
    # Contact Information
    website = Column(String)
    contact_email = Column(String)
    sales_contact = Column(String)
    partnerships_contact = Column(String)
    linkedin_url = Column(String)
    
    # Business Intelligence
    annual_revenue_estimate = Column(String)
    employee_count = Column(Integer)
    production_scale = Column(String)  # units per year
    global_customers = Column(Integer)
    us_customers = Column(Integer)
    
    # Competitive Intelligence
    main_competitors = Column(JSON)
    unique_selling_points = Column(JSON)
    technology_advantages = Column(JSON)
    
    # Lead Scoring
    lead_score = Column(Integer, default=0)  # 0-100
    match_score = Column(Integer, default=0)  # fit for Ready For Robots
    priority_tier = Column(String)  # hot, warm, cold
    
    # Engagement Tracking
    outreach_status = Column(String)  # not_contacted, contacted, responded, meeting_scheduled, partnership
    last_contact_date = Column(DateTime)
    next_followup_date = Column(DateTime)
    outreach_notes = Column(Text)
    
    # Metadata
    data_source = Column(String)  # Crunchbase, trade show, manual research
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Notes & Intelligence
    notes = Column(Text)
    market_intelligence = Column(JSON)  # structured insights
    partnership_opportunity = Column(Text)  # why they need Ready For Robots
