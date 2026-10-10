"""Unit tests for ChatGPT Actions / Custom GPT Integration endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_gpt_openapi_schema():
    res = client.get("/api/v1/gpt-actions/openapi.json")
    assert res.status_code == 200
    data = res.json()
    assert data["openapi"] == "3.1.0"
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

    # Test robot_name only without url
    res_name_only = client.post(
        "/api/v1/gpt-actions/match-jobs",
        json={"robot_name": "UR10e"},
    )
    assert res_name_only.status_code == 200
    data_name_only = res_name_only.json()
    assert data_name_only["status"] == "success"
    assert data_name_only["matched_job_count"] == 1


def test_gpt_search_opportunities():
    res = client.post(
        "/api/v1/gpt-actions/search-opportunities",
        json={"query": "machine tending", "industry": "Manufacturing"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "opportunity_count" in data
    assert "activation_url" in data


def test_gpt_recommend_robots():
    res = client.post(
        "/api/v1/gpt-actions/recommend-robots",
        json={"task_description": "moving 500lb pallets in warehouse"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["recommended_robot_types"]) > 0
    assert "AMR" in data["recommended_robot_types"][0]["category"]

