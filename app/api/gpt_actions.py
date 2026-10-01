"""
ChatGPT Actions / Custom GPT Integration Endpoint.
Exposes public OpenAPI schema and lightweight endpoints formatted for LLM function calling.
"""
from typing import Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.robot_job_capability_match import match_robot_url

router = APIRouter(prefix="/api/v1/gpt-actions", tags=["gpt-actions"])


class GptJobMatchIn(BaseModel):
    url: str = Field(description="URL of the robot product page or manufacturer website, e.g. https://alpharoboticsai.com")
    robot_name: Optional[str] = Field(default=None, description="Name of the robot model or brand, e.g. UR10e or Figure 02")
    location: Optional[str] = Field(default=None, description="Target geographic state or region, e.g. Ohio, Midwest, US")


class GptPaybackIn(BaseModel):
    robot_cost: float = Field(default=45000.0, description="Total robot purchase or deployment cost in USD")
    hourly_labor_rate: float = Field(default=28.50, description="Replaced human labor wage rate per hour in USD")
    shift_hours_per_day: float = Field(default=16.0, description="Daily operational hours (e.g. 16h for 2 shifts)")


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


@router.get("/openapi.json")
def gpt_openapi_schema():
    """Custom OpenAPI 3.0 specification for ChatGPT Actions."""
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "ReadyForRobots Placement & Payback API",
            "description": "API for matching physical robots to active commercial job openings and calculating labor ROI payback.",
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
            }
        }
    }
