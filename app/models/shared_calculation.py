from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class SharedCalculation(Base):
    """Stores shareable ROI calculations"""
    __tablename__ = "shared_calculations"

    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(String(8), unique=True, index=True)  # Short unique ID
    robot_type = Column(String(100))
    robot_cost = Column(Float)
    industry = Column(String(50))
    payback_months = Column(Float)
    annual_savings = Column(Float)
    roi_1_year = Column(Float)
    roi_3_year = Column(Float)
    total_savings_3_year = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    views = Column(Integer, default=0)
    
class SharedCalculationCreate(BaseModel):
    robot_type: str
    robot_cost: float
    industry: str
    payback_months: float
    annual_savings: float
    roi_1_year: float
    roi_3_year: float
    total_savings_3_year: float
