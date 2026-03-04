"""
Robots API
==========
CRUD endpoints for managing the robot product library.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.robot import Robot

router = APIRouter()


# ── Pydantic Schemas ───────────────────────────────────────────────────────
class RobotCreate(BaseModel):
    name: str
    vendor: str
    model_number: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    robot_type: str  # delivery, disinfection, bartender, logistics, cleaning, service
    industries: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    payload_capacity_kg: Optional[float] = None
    battery_life_hours: Optional[float] = None
    speed_mps: Optional[float] = None
    dimensions: Optional[dict] = None
    weight_kg: Optional[float] = None
    features: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    price_usd: Optional[float] = None
    monthly_lease_usd: Optional[float] = None
    roi_stat: Optional[str] = None
    is_active: bool = True
    is_preferred: bool = True
    min_order_quantity: int = 1
    lead_time_weeks: Optional[int] = None
    notes: Optional[str] = None


class RobotUpdate(BaseModel):
    name: Optional[str] = None
    vendor: Optional[str] = None
    model_number: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    robot_type: Optional[str] = None
    industries: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    payload_capacity_kg: Optional[float] = None
    battery_life_hours: Optional[float] = None
    speed_mps: Optional[float] = None
    dimensions: Optional[dict] = None
    weight_kg: Optional[float] = None
    features: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    price_usd: Optional[float] = None
    monthly_lease_usd: Optional[float] = None
    roi_stat: Optional[str] = None
    is_active: Optional[bool] = None
    is_preferred: Optional[bool] = None
    min_order_quantity: Optional[int] = None
    lead_time_weeks: Optional[int] = None
    notes: Optional[str] = None


class RobotResponse(BaseModel):
    id: int
    name: str
    vendor: str
    model_number: Optional[str]
    tagline: Optional[str]
    description: Optional[str]
    product_url: Optional[str]
    image_url: Optional[str]
    robot_type: str
    industries: Optional[List[str]]
    use_cases: Optional[List[str]]
    payload_capacity_kg: Optional[float]
    battery_life_hours: Optional[float]
    speed_mps: Optional[float]
    dimensions: Optional[dict]
    weight_kg: Optional[float]
    features: Optional[List[str]]
    certifications: Optional[List[str]]
    price_usd: Optional[float]
    monthly_lease_usd: Optional[float]
    roi_stat: Optional[str]
    is_active: bool
    is_preferred: bool
    min_order_quantity: int
    lead_time_weeks: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/robots", response_model=List[RobotResponse])
def list_robots(
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    robot_type: Optional[str] = Query(None, description="Filter by robot type"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    active_only: bool = Query(True, description="Show only active robots"),
    db: Session = Depends(get_db)
):
    """
    List all robots in the library with optional filters.
    """
    query = db.query(Robot)
    
    if active_only:
        query = query.filter(Robot.is_active == True)
    
    if vendor:
        query = query.filter(Robot.vendor.ilike(f"%{vendor}%"))
    
    if robot_type:
        query = query.filter(Robot.robot_type == robot_type)
    
    robots = query.order_by(Robot.vendor, Robot.name).all()
    
    # Filter by industry in Python (SQLite JSON filtering has limitations)
    if industry:
        robots = [r for r in robots if r.industries and industry in r.industries]
    
    return robots


@router.get("/robots/{robot_id}", response_model=RobotResponse)
def get_robot(robot_id: int, db: Session = Depends(get_db)):
    """
    Get details of a specific robot by ID.
    """
    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return robot


@router.post("/robots", response_model=RobotResponse, status_code=201)
def create_robot(robot: RobotCreate, db: Session = Depends(get_db)):
    """
    Add a new robot to the library.
    """
    db_robot = Robot(**robot.model_dump())
    db.add(db_robot)
    db.commit()
    db.refresh(db_robot)
    return db_robot


@router.put("/robots/{robot_id}", response_model=RobotResponse)
def update_robot(robot_id: int, robot: RobotUpdate, db: Session = Depends(get_db)):
    """
    Update an existing robot's details.
    """
    db_robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if not db_robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    # Update only provided fields
    update_data = robot.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_robot, field, value)
    
    db.commit()
    db.refresh(db_robot)
    return db_robot


@router.delete("/robots/{robot_id}", status_code=204)
def delete_robot(robot_id: int, db: Session = Depends(get_db)):
    """
    Delete a robot from the library (or mark as inactive).
    """
    db_robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if not db_robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    # Soft delete - just mark as inactive
    db_robot.is_active = False
    db.commit()
    return None


@router.get("/robots/recommend/{industry}")
def recommend_robots(
    industry: str,
    robot_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(5, description="Max number of recommendations"),
    db: Session = Depends(get_db)
):
    """
    Get robot recommendations for a specific industry.
    Returns robots sorted by preference (preferred vendors first).
    """
    query = db.query(Robot).filter(Robot.is_active == True)
    
    if robot_type:
        query = query.filter(Robot.robot_type == robot_type)
    
    all_robots = query.all()
    
    # Filter by industry in Python for SQLite compatibility
    robots = [r for r in all_robots if r.industries and industry in r.industries]
    
    # Sort by preference: preferred robots first, then by vendor name
    robots.sort(key=lambda r: (not r.is_preferred, r.vendor, r.name))
    
    return {
        "industry": industry,
        "robot_type": robot_type,
        "count": len(robots[:limit]),
        "robots": [RobotResponse.model_validate(r) for r in robots[:limit]]
    }


@router.get("/robots/types/list")
def list_robot_types(db: Session = Depends(get_db)):
    """
    Get a list of all unique robot types in the library.
    """
    types = db.query(Robot.robot_type).filter(Robot.is_active == True).distinct().all()
    return {"robot_types": [t[0] for t in types if t[0]]}


@router.get("/robots/vendors/list")
def list_vendors(db: Session = Depends(get_db)):
    """
    Get a list of all unique vendors in the library.
    """
    vendors = db.query(Robot.vendor).filter(Robot.is_active == True).distinct().all()
    return {"vendors": [v[0] for v in vendors if v[0]]}
