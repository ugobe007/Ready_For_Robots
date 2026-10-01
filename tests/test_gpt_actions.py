"""Unit tests for ChatGPT Actions / Custom GPT Integration endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_gpt_openapi_schema():
    res = client.get("/api/v1/gpt-actions/openapi.json")
    assert res.status_code == 200
    data = res.json()
    assert data["openapi"] == "3.0.1"
    assert "/api/v1/gpt-actions/match-jobs" in data["paths"]
    assert "/api/v1/gpt-actions/calculate-payback" in data["paths"]


def test_gpt_calculate_payback():
    res = client.post(
        "/api/v1/gpt-actions/calculate-payback",
        json={"robot_cost": 50000.0, "hourly_labor_rate": 25.0, "shift_hours_per_day": 16.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["robot_cost_usd"] == 50000.0
    assert data["hourly_labor_rate_usd"] == 25.0
    assert data["daily_savings_usd"] == 400.0
    assert data["annual_savings_usd"] == 100000.0
    assert data["payback_period_months"] == 5.8
    assert data["annual_roi_percent"] == 200.0
    assert "crm_desk_url" in data


def test_gpt_match_jobs(monkeypatch):
    def mock_match(url, robot_name=None):
        return {
            "robot_name": robot_name or "UR10e",
            "jobs": [
                {
                    "title": "Machine Tending Operator",
                    "company_name": "Apex Mfg",
                    "location": "Columbus, OH",
                    "industry": "Manufacturing",
                    "hourly_wage": "$28.50/hr",
                    "task_model_required": "machine_tending_v1",
                }
            ],
        }

    monkeypatch.setattr("app.api.gpt_actions.match_robot_url", mock_match)

    res = client.post(
        "/api/v1/gpt-actions/match-jobs",
        json={"url": "https://alpharoboticsai.com", "robot_name": "UR10e"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["matched_job_count"] == 1
    assert data["jobs"][0]["company_name"] == "Apex Mfg"
    assert "https://readyforrobots.com/pipeline?src=chatgpt" in data["activation_url"]
