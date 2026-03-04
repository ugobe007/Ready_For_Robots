"""
Robot Model
===========
Database model for managing a library of robots from various vendors.
Stores robot specifications, capabilities, use cases, and pricing information.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Robot(Base):
    """
    Robot product catalog entry.
    
    Supports multiple vendors and robot types for matching with sales opportunities.
    """
    __tablename__ = "robots"
    
    # ── Core Identity ──────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # e.g., "MATRADEE", "Relay", "TUG"
    vendor = Column(String, nullable=False, index=True)  # e.g., "Bear Robotics", "Aethon"
    model_number = Column(String, nullable=True)  # Manufacturer model/SKU
    
    # ── Description & Marketing ────────────────────────────────────────────
    tagline = Column(String, nullable=True)  # Brief description
    description = Column(Text, nullable=True)  # Full product description
    product_url = Column(String, nullable=True)  # Link to vendor product page
    image_url = Column(String, nullable=True)  # Product image
    
    # ── Categorization ─────────────────────────────────────────────────────
    robot_type = Column(String, nullable=False, index=True)  
    # Types: "delivery", "disinfection", "bartender", "logistics", "cleaning", "service"
    
    industries = Column(JSON, nullable=True)  
    # Array: ["Hospitality", "Healthcare", "Food Service", "Logistics", "Retail"]
    
    use_cases = Column(JSON, nullable=True)  
    # Array: ["In-room dining delivery", "Medication delivery", "Floor cleaning"]
    
    # ── Specifications ─────────────────────────────────────────────────────
    payload_capacity_kg = Column(Float, nullable=True)  # Max payload in kg
    battery_life_hours = Column(Float, nullable=True)  # Operating hours per charge
    speed_mps = Column(Float, nullable=True)  # Maximum speed in meters/second
    dimensions = Column(JSON, nullable=True)  # {"height_cm": 120, "width_cm": 50, "depth_cm": 50}
    weight_kg = Column(Float, nullable=True)  # Robot weight
    
    # ── Features & Capabilities ────────────────────────────────────────────
    features = Column(JSON, nullable=True)  
    # Array: ["UV-C disinfection", "Elevator integration", "Voice interaction", "Touchscreen"]
    
    certifications = Column(JSON, nullable=True)  
    # Array: ["FDA approved", "CE certified", "UL listed"]
    
    # ── Pricing & ROI ──────────────────────────────────────────────────────
    price_usd = Column(Float, nullable=True)  # Purchase price
    monthly_lease_usd = Column(Float, nullable=True)  # Lease option
    roi_stat = Column(Text, nullable=True)  # ROI messaging for sales
    # e.g., "Handles 400+ daily deliveries, reducing delivery labor by 40%"
    
    # ── Availability ───────────────────────────────────────────────────────
    is_active = Column(Boolean, default=True, index=True)  # Available for recommendation
    is_preferred = Column(Boolean, default=True, index=True)  # Prioritize in recommendations
    min_order_quantity = Column(Integer, default=1)  # Minimum units per order
    lead_time_weeks = Column(Integer, nullable=True)  # Delivery time
    
    # ── Metadata ───────────────────────────────────────────────────────────
    notes = Column(Text, nullable=True)  # Internal notes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Robot {self.vendor} {self.name} ({self.robot_type})>"
