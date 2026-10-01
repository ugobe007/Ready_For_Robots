"""
ChatGPT Actions / Custom GPT Integration Endpoint.
Exposes public OpenAPI schema and lightweight endpoints formatted for LLM function calling.
"""
from typing import Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.robot_job_capability_match import match_from_chip, match_robot_url

router = APIRouter(prefix="/api/v1/gpt-actions", tags=["gpt-actions"])


class GptJobMatchIn(BaseModel):
    url: str = Field(description="URL of the robot product page or manufacturer website, e.g. https://alpharoboticsai.com")
    robot_name: Optional[str] = Field(default=None, description="Name of the robot model or brand, e.g. UR10e or Figure 02")
    location: Optional[str] = Field(default=None, description="Target geographic state or region, e.g. Ohio, Midwest, US")


class GptPaybackIn(BaseModel):
    robot_cost: float = Field(default=45000.0, description="Total robot purchase or deployment cost in USD")
    hourly_labor_rate: float = Field(default=28.50, description="Replaced human labor wage rate per hour in USD")
    shift_hours_per_day: float = Field(default=16.0, description="Daily operational hours (e.g. 16h for 2 shifts)")


class GptOpportunitySearchIn(BaseModel):
    query: Optional[str] = Field(default=None, description="Search term, task, or concept, e.g. machine tending, floor cleaning, Ohio")
    industry: Optional[str] = Field(default=None, description="Industry sector filter, e.g. Manufacturing, Logistics, Healthcare")
    location: Optional[str] = Field(default=None, description="State or region filter, e.g. Ohio, CA, Midwest")


class GptRobotRecommendIn(BaseModel):
    task_description: str = Field(description="Description of the physical work task to automate, e.g. moving 500lb pallets in warehouse or picking 5kg parts for machine tending")
    payload_capacity_kg: Optional[float] = Field(default=None, description="Required payload capacity in kg")
    environment: Optional[str] = Field(default="indoor", description="Operating environment: indoor, warehouse, factory, outdoor, cleanroom")


@router.post("/match-jobs")
def gpt_match_jobs(payload: GptJobMatchIn):
    """Match a robot model or manufacturer URL to real available Robot Jobs."""
    res = match_robot_url(payload.url, robot_name=payload.robot_name)
    jobs = res.get("jobs", [])
    formatted_jobs = []
    for j in jobs[:5]:
        formatted_jobs.append({
            "title": j.get("title"),
            "company_name": j.get("company_name"),
            "location": j.get("location"),
            "industry": j.get("industry"),
            "hourly_wage": j.get("hourly_wage"),
            "task_model_required": j.get("task_model_required"),
            "crm_desk_url": f"https://readyforrobots.com/pipeline?src=chatgpt&url={payload.url}"
        })
    return {
        "status": "success",
        "robot_name": res.get("robot_name", payload.robot_name or "Robot"),
        "matched_job_count": len(jobs),
        "jobs": formatted_jobs,
        "summary": f"Found {len(jobs)} active job placements qualified for {res.get('robot_name', 'this robot')}.",
        "activation_url": f"https://readyforrobots.com/pipeline?src=chatgpt&url={payload.url}"
    }


@router.post("/calculate-payback")
def gpt_calculate_payback(payload: GptPaybackIn):
    """Calculate payback period (months) and annual ROI for replacing human labor with a robot."""
    daily_savings = payload.hourly_labor_rate * payload.shift_hours_per_day
    annual_savings = daily_savings * 250  # 250 work days/yr
    payback_months = round((payload.robot_cost / daily_savings) / 21.67, 1) if daily_savings > 0 else 0.0
    annual_roi_pct = round((annual_savings / payload.robot_cost) * 100, 1) if payload.robot_cost > 0 else 0.0

    return {
        "robot_cost_usd": payload.robot_cost,
        "hourly_labor_rate_usd": payload.hourly_labor_rate,
        "daily_savings_usd": round(daily_savings, 2),
        "annual_savings_usd": round(annual_savings, 2),
        "payback_period_months": payback_months,
        "annual_roi_percent": annual_roi_pct,
        "verdict": f"Fully pays back in {payback_months} months with an annual ROI of {annual_roi_pct}%.",
        "crm_desk_url": "https://readyforrobots.com/pipeline?src=chatgpt_payback"
    }


@router.post("/search-opportunities")
def gpt_search_opportunities(payload: GptOpportunitySearchIn):
    """Find active commercial companies and job opportunities needing robot automation (buyer intent radar)."""
    chip = "moves_materials"
    q = (payload.query or "").lower()
    if "clean" in q or "scrub" in q:
        chip = "cleans"
    elif "inspect" in q or "scan" in q:
        chip = "inspects"
    elif "tend" in q or "pick" in q or "weld" in q or "assembly" in q:
        chip = "manipulates"

    res = match_from_chip(chip)
    jobs = res.get("jobs", [])
    if payload.industry:
        jobs = [j for j in jobs if payload.industry.lower() in (j.get("industry") or "").lower()]
    if payload.location:
        jobs = [j for j in jobs if payload.location.lower() in (j.get("location") or "").lower()]

    formatted = []
    for j in jobs[:6]:
        formatted.append({
            "title": j.get("title"),
            "company_name": j.get("company_name"),
            "location": j.get("location"),
            "industry": j.get("industry"),
            "hourly_wage": j.get("hourly_wage"),
            "task_model_required": j.get("task_model_required"),
            "decision_maker_role": j.get("decision_maker_role") or "VP of Operations / Plant Manager",
            "crm_desk_url": "https://readyforrobots.com/pipeline?src=chatgpt_search"
        })

    return {
        "status": "success",
        "opportunity_count": len(formatted),
        "opportunities": formatted,
        "summary": f"Found {len(formatted)} commercial opportunities seeking robot automation for {payload.query or 'physical tasks'}.",
        "activation_url": "https://readyforrobots.com/pipeline?src=chatgpt_search"
    }


@router.post("/recommend-robots")
def gpt_recommend_robots(payload: GptRobotRecommendIn):
    """Recommend qualified robot hardware classes and vendor SKUs for a specific task description."""
    desc = payload.task_description.lower()
    recommendations = []

    if "pallet" in desc or "move" in desc or "transport" in desc or "tug" in desc:
        recommendations.append({
            "category": "Autonomous Mobile Robot (AMR) / Heavy Pallet Transport",
            "suggested_models": ["MiR 1350", "OTTO 1500", "Fetch Robotics Heavy Pallet"],
            "key_capabilities": ["autonomous navigation", "slam", "1000kg+ payload"],
            "typical_task_model": "pallet_transport_v1"
        })
    if "clean" in desc or "scrub" in desc or "floor" in desc:
        recommendations.append({
            "category": "Autonomous Commercial Floor Scrubber",
            "suggested_models": ["Tennant T7AMR", "Avidbots Neo 2", "Brain Corp Scrub"],
            "key_capabilities": ["autonomous scrubbing", "water recycling", "obstacle avoidance"],
            "typical_task_model": "commercial_floor_clean_v1"
        })
    if "tend" in desc or "pick" in desc or "weld" in desc or "assembly" in desc or "cnc" in desc:
        recommendations.append({
            "category": "Collaborative Robot Arm (Cobot)",
            "suggested_models": ["Universal Robots UR10e / UR20", "FANUC CRX-25iA", "Doosan H2017"],
            "key_capabilities": ["force sensing", "precision trajectory", "flexible end-effector"],
            "typical_task_model": "machine_tending_v1"
        })
    if "tote" in desc or "humanoid" in desc or "general" in desc or not recommendations:
        recommendations.append({
            "category": "General Purpose Humanoid / Mobile Manipulator",
            "suggested_models": ["Unitree G1", "Figure 02", "Boston Dynamics Atlas / Stretch"],
            "key_capabilities": ["bipedal/wheeled mobility", "dual dexterous arms", "vla policy"],
            "typical_task_model": "open_world_tote_pick_v1"
        })

    return {
        "status": "success",
        "task_analyzed": payload.task_description,
        "recommended_robot_types": recommendations,
        "summary": f"Identified {len(recommendations)} optimal robot hardware classes for: '{payload.task_description}'.",
        "match_jobs_url": "https://readyforrobots.com/pipeline?src=chatgpt_recommend"
    }


@router.get("/openapi.json")
def gpt_openapi_schema():
    """Custom OpenAPI 3.0 specification for ChatGPT Actions."""
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "ReadyForRobots Placement & Payback API",
            "description": "API for matching physical robots to active commercial job openings, searching automation opportunities, recommending robot SKUs, and calculating labor ROI payback.",
            "version": "v1.0"
        },
        "servers": [{"url": "https://ready-2-robot.fly.dev"}],
        "paths": {
            "/api/v1/gpt-actions/match-jobs": {
                "post": {
                    "operationId": "matchRobotJobs",
                    "summary": "Match a robot URL or model to available commercial jobs",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "url": {"type": "string", "example": "https://alpharoboticsai.com"},
                                        "robot_name": {"type": "string", "example": "UR10e"}
                                    },
                                    "required": ["url"]
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Matched robot jobs"}}
                }
            },
            "/api/v1/gpt-actions/calculate-payback": {
                "post": {
                    "operationId": "calculatePayback",
                    "summary": "Calculate robot payback period and labor ROI",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "robot_cost": {"type": "number", "example": 45000},
                                        "hourly_labor_rate": {"type": "number", "example": 28.5}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Payback calculation result"}}
                }
            },
            "/api/v1/gpt-actions/search-opportunities": {
                "post": {
                    "operationId": "searchOpportunities",
                    "summary": "Find companies and opportunities seeking robot automation ('who needs robot automation')",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string", "example": "machine tending"},
                                        "industry": {"type": "string", "example": "Manufacturing"},
                                        "location": {"type": "string", "example": "Ohio"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Automation opportunity search results"}}
                }
            },
            "/api/v1/gpt-actions/recommend-robots": {
                "post": {
                    "operationId": "recommendRobots",
                    "summary": "Recommend robot hardware SKUs and categories for a task description ('what type of robot should I use')",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "task_description": {"type": "string", "example": "moving 500lb pallets in warehouse"},
                                        "payload_capacity_kg": {"type": "number", "example": 250}
                                    },
                                    "required": ["task_description"]
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Robot hardware recommendations"}}
                }
            }
        }
    }
